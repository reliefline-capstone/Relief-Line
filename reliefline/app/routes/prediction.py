# Predictive Analytics page (food pack forecast).

from flask import Blueprint, render_template, request, url_for
from flask_login import login_required, current_user
from sqlalchemy import text

from app.extensions import db

from app.utils.decorators import role_required
from app.models.barangay import Barangay
from app.models.barangay_status import BarangayDisasterStatus
from app.models.disaster_event import DisasterEvent
from app.models.prediction import ModelMetrics
from app.models.barangay_inventory import BarangayInventory, food_pack_on_hand
from app.models.barangay_report import BarangayReport
from app.ml import predict as ml_predict
from app.ml import charts as forecast_charts
from app.utils.disaster_events import (
    resolve_effective_event, blocking_event_for_province, relevant_active_events_query,
)

from app.routes.pswdo import (
    TARGET_LGUS,
    _load_warehouses, _stock_recommendations, _forecast_recommendations, _barangay_recommendations, _relief_summary,
    _stock_adequacy,
    _report_scope_filters,
)

prediction_bp = Blueprint("prediction", __name__)

MONTH_NAMES = ["January", "February", "March", "April", "May", "June", "July",
               "August", "September", "October", "November", "December"]


# Which municipalities the user may see (CSWDO/MSWDO: only their own; others: all 3).
def _scope_lgus():
    if current_user.role == "cswdo_admin":
        office = current_user.office
        if office and office.area_covered in TARGET_LGUS:
            return [office.area_covered]
        return []
    return list(TARGET_LGUS)


# True if the user is a CSWDO/MSWDO admin.
def _is_cswdo():
    return current_user.role == "cswdo_admin"


# Picks the disaster event to show for each municipality
# (the one the user chose, otherwise each municipality's active event).
def _resolve_event_map(explicit_event_id, lgus):
    if explicit_event_id:
        event = DisasterEvent.query.get(explicit_event_id)
        event_id = event.event_id if event else None
        return {lgu: event_id for lgu in lgus}, event

    lgu_events = {lgu: resolve_effective_event(lgu)[0] for lgu in lgus}
    lgu_event_ids = {lgu: (e.event_id if e else None) for lgu, e in lgu_events.items()}
    if len(lgus) == 1:
        page_event = lgu_events[lgus[0]]
    else:
        page_event = blocking_event_for_province()
    return lgu_event_ids, page_event


# Compares warehouse stock with the forecast: how many months the stock will last,
# the recommended stockpile, and how many packs are short.
def _stock_cover(stock, lgu_names, horizon_months):
    if not lgu_names:
        return None
    fh = [ml_predict.forecast_lgu(l, horizon_months) for l in lgu_names]
    f12 = [ml_predict.forecast_lgu(l, 12) for l in lgu_names]
    if any(f is None for f in fh + f12):
        return None
    stockpile = sum(f["horizon_p90"] for f in fh)
    expected = sum(f["horizon_total"] for f in fh)

    remaining, months = float(stock), 0.0
    exhausted = False
    for i in range(12):
        demand = sum(f["months"][i]["projected_packs"] for f in f12)
        if remaining >= demand:
            remaining -= demand
            months += 1
        else:
            months += remaining / demand
            exhausted = True
            break
    coverage = round(stock / stockpile * 100) if stockpile else None
    if coverage is None or coverage >= 100:
        tier = "healthy"
    elif coverage >= 50:
        tier = "warning"
    else:
        tier = "critical"
    return {
        "stockpile": stockpile,
        "expected": expected, "coverage_pct": coverage, "tier": tier,
        # 95% confidence interval of the need over the period (shown instead of the single expected figure).
        "ci_low": sum(f["horizon_ci_low"] for f in fh) if all(f["ci_level"] for f in fh) else None,
        "ci_high": sum(f["horizon_ci_high"] for f in fh) if all(f["ci_level"] for f in fh) else None,
        "shortfall": max(stockpile - stock, 0),
        "months_cover": round(months, 1), "covers_12_plus": not exhausted,
    }


# One barangay's numbers for the Predictive Analytics page:
# need (request or forecast), stock on hand, stock adequacy and priority.
def _barangay_snapshot(barangay, status_row, event_id):
    status_key = status_row.status if status_row else "normal"

    relief = _relief_summary([barangay.barangay_id], event_id)
    has_request = relief["requested"] > 0
    predicted = ml_predict.predict_quantity(barangay)
    on_hand = food_pack_on_hand(barangay.barangay_id)

    report_row = BarangayReport.query.filter(
        BarangayReport.barangay_id == barangay.barangay_id,
        *_report_scope_filters(event_id),
    ).order_by(
        BarangayReport.submitted_at.desc(), BarangayReport.created_at.desc()
    ).first()
    stock_need = (report_row.requested_food_packs or 0) if report_row else 0
    adeq, ratio_pct = _stock_adequacy(stock_need, on_hand)

    if has_request:
        packs_needed = relief["requested"]
        released = relief["released"]
        source = "request"
    else:
        packs_needed = predicted or 0
        released = 0
        source = "model"

    return {
        "barangay_id": barangay.barangay_id,
        "name": barangay.barangay_name,
        "lgu": barangay.city_municipality,
        "status": status_key,
        "priority_label": adeq["label"],
        "priority_tier": adeq["tier"],
        "priority_rank": adeq["rank"],
        "stock_need": stock_need,
        "stock_ratio_pct": ratio_pct,
        "affected_families": (report_row.affected_families if report_row
                              else (status_row.affected_families if status_row else 0)),
        "packs_needed": packs_needed,
        "released": released,
        "undelivered": max(packs_needed - released, 0),
        "need_source": source,
        "predicted_quantity": predicted,
        "on_hand_stock": on_hand,
        "suggested_allocation": max((predicted or 0) - (on_hand or 0), 0),
    }


# Past food pack distribution from the real typhoon relief records (the model's dataset),
# grouped by municipality -> year -> month, each month with its barangay breakdown.
def _distribution_history(lgus):
    if not lgus:
        return {}
    events = db.session.execute(text(
        "SELECT relief_event_id, city_municipality, report_date FROM relief_events "
        "WHERE report_date IS NOT NULL")).fetchall()
    events = {eid: (lgu, d) for eid, lgu, d in events if lgu in lgus}
    if not events:
        return {}

    names_by_event = {}
    storm_date = {}
    for eid, name, start in db.session.execute(text(
            "SELECT t.relief_event_id, c.typhoon_name, c.start_date FROM relief_event_typhoons t "
            "JOIN typhoon_calendar c ON c.typhoon_key = t.typhoon_key ORDER BY c.start_date")).fetchall():
        names_by_event.setdefault(eid, []).append(name)
        storm_date.setdefault(eid, start)
    # File each report under the month its (first) typhoon started, not the report's date,
    # so a late report (e.g. Urdaneta's Oct 2026 report for the Aug 2026 storms) lands in the right month.
    events = {eid: (lgu, storm_date.get(eid) or d) for eid, (lgu, d) in events.items()}

    brgy_names = dict(Barangay.query.with_entities(Barangay.barangay_id, Barangay.barangay_name)
                      .filter(Barangay.city_municipality.in_(lgus)).all())

    history = {}
    rows = db.session.execute(text(
        "SELECT relief_event_id, barangay_id, food_packs_given, affected_families "
        "FROM barangay_relief_records")).fetchall()
    for eid, bid, packs, fam in rows:
        if eid not in events:
            continue
        lgu, d = events[eid]
        month = history.setdefault(lgu, {}).setdefault(str(d.year), {}).setdefault(d.month, {
            "packs": 0, "families": 0, "typhoons": [], "brgys": {},
        })
        for n in names_by_event.get(eid, []):
            if n not in month["typhoons"]:
                month["typhoons"].append(n)
        b = month["brgys"].setdefault(bid, {"name": brgy_names.get(bid, f"Barangay #{bid}"),
                                            "packs": None, "families": 0})
        if packs is not None:
            b["packs"] = (b["packs"] or 0) + int(packs)
            month["packs"] += int(packs)
        b["families"] += int(fam or 0)
        month["families"] += int(fam or 0)

    # Turn each month's barangay map into a list sorted by packs given (largest first).
    for years in history.values():
        for months in years.values():
            for m in months.values():
                m["rows"] = sorted(m.pop("brgys").values(), key=lambda r: (r["packs"] or 0, r["families"]),
                                   reverse=True)
    return history


# Page: /prediction/ - Predictive Analytics page: food pack forecast per municipality, how long the stock will last,
# priority barangays, monthly breakdown charts and the model's accuracy.
@prediction_bp.route("/")
@login_required
@role_required("cswdo_admin", "system_admin")
def index():
    explicit_event_id = request.args.get("event_id", type=int)

    scope_lgus = _scope_lgus()
    is_cswdo = _is_cswdo()
    can_allocate = bool(current_user.office)
    municipality_filter = request.args.get("municipality", "all")
    if municipality_filter != "all" and municipality_filter in scope_lgus:
        lgus = [municipality_filter]
    else:
        municipality_filter = "all"
        lgus = scope_lgus
    days_filter = request.args.get("days", 30, type=int)

    active_events = relevant_active_events_query(scope_lgus).all()
    lgu_event_ids, event = _resolve_event_map(explicit_event_id, lgus)
    event_id = event.event_id if event else None

    barangays = Barangay.query.filter(Barangay.city_municipality.in_(lgus)).order_by(
        Barangay.city_municipality, Barangay.barangay_name
    ).all()

    relevant_event_ids = {eid for eid in lgu_event_ids.values() if eid}
    status_map = {}
    if relevant_event_ids:
        rows = BarangayDisasterStatus.query.filter(BarangayDisasterStatus.event_id.in_(relevant_event_ids)).all()
        status_map = {r.barangay_id: r for r in rows}

    snapshots = []
    for b in barangays:
        b_event_id = lgu_event_ids.get(b.city_municipality)
        snap = _barangay_snapshot(b, status_map.get(b.barangay_id), b_event_id)
        if snap["need_source"] == "model" and snap["predicted_quantity"] is not None:
            ml_predict.log_prediction_once_per_day(b, snap["predicted_quantity"])
        snapshots.append(snap)

    estimated_need = sum(s["undelivered"] for s in snapshots)
    all_offices, all_warehouses, _ = _load_warehouses()
    if is_cswdo and current_user.office:
        warehouses = [w for w in all_warehouses if w["office"].office_id == current_user.office.office_id]
    else:
        warehouses = all_warehouses
    total_food_packs = sum(w["food_pack_qty"] for w in warehouses)
    fulfillable_warehouses = [w for w in warehouses if w["food_pack_qty"] > 0]
    total_affected_families = sum(s["affected_families"] for s in snapshots if s["status"] != "normal") if event else 0
    estimated_three_day_need = total_affected_families
    burn_rate = round(total_affected_families / 3, 0) if total_affected_families > 0 else 0
    days_remaining = round(total_food_packs / burn_rate, 1) if burn_rate > 0 else None

    ranking = sorted(
        snapshots,
        key=lambda s: (s["priority_rank"], s["stock_ratio_pct"] or 0, s["packs_needed"]),
        reverse=True,
    )[:8]

    cover_horizon = request.args.get("forecast_months", 12, type=int)
    if cover_horizon not in (3, 6, 9, 12):
        cover_horizon = 12
    warehouse_cards = []
    for w in warehouses:
        if not is_cswdo and w["office"].office_type != "pswdo":
            continue
        scope = [w["office"].area_covered] if is_cswdo else list(scope_lgus)
        warehouse_cards.append({
            "name": w["office"].office_name,
            "food_pack_qty": w["food_pack_qty"],
            "capacity": w["capacity"],
            "pct": w["pct"],
            "health": w["health"],
            "scope_label": scope[0] if is_cswdo else "the whole province",
            "cover": _stock_cover(w["food_pack_qty"], scope, cover_horizon),
        })
    combined_cover = None if is_cswdo else _stock_cover(total_food_packs, list(scope_lgus), cover_horizon)

    forecast_months = request.args.get("forecast_months", 12, type=int)
    if forecast_months not in (3, 6, 9, 12):
        forecast_months = 12
    forecast_lgu_choice = request.args.get("forecast_lgu", "")
    if forecast_lgu_choice not in scope_lgus:
        forecast_lgu_choice = scope_lgus[0] if scope_lgus else None
    lgu_forecast = ml_predict.forecast_lgu(forecast_lgu_choice, forecast_months) if forecast_lgu_choice else None

    cover_chart = cover_wh = None
    if lgu_forecast:
        wh = next((w for w in all_warehouses
                   if w["office"].office_type == "cswdo"
                   and w["office"].area_covered == forecast_lgu_choice), None)
        if wh is not None:
            cover_chart = forecast_charts.cover_chart(lgu_forecast["months"], wh["food_pack_qty"])
            cover_wh = {"pct": wh["pct"],
                        "cover": _stock_cover(wh["food_pack_qty"], [forecast_lgu_choice], forecast_months)}

    forecast_summary_by_lgu = []
    for lgu in lgus:
        lf = ml_predict.forecast_lgu(lgu, forecast_months)
        if lf is None:
            continue
        forecast_summary_by_lgu.append({
            "lgu": lgu,
            "this_month": lf["months"][0]["projected_packs"] if lf["months"] else 0,
            "horizon_total": lf["horizon_total"],
            "horizon_p90": lf["horizon_p90"],
            "ci_level": lf["ci_level"],
            "ci_low": lf["horizon_ci_low"], "ci_high": lf["horizon_ci_high"],
            "this_month_low": lf["months"][0]["ci_low"] if lf["months"] else None,
            "this_month_high": lf["months"][0]["ci_high"] if lf["months"] else None,
        })
    forecast_summary_by_lgu.sort(key=lambda f: f["horizon_total"], reverse=True)

    show_breakdown = request.args.get("show_breakdown") == "1"
    barangay_breakdown = []
    if lgu_forecast and show_breakdown:
        by_id = {b.barangay_id: b for b in Barangay.query.filter_by(city_municipality=forecast_lgu_choice).all()}
        breakdown_on_hand = dict(BarangayInventory.query.with_entities(
            BarangayInventory.barangay_id, BarangayInventory.quantity_available
        ).filter(
            BarangayInventory.barangay_id.in_(list(by_id)),
            BarangayInventory.item_type == "food_pack",
        ).all())
        for row in sorted(ml_predict.share_breakdown(forecast_lgu_choice), key=lambda r: r["share"], reverse=True):
            fb = ml_predict.forecast_barangay(by_id[row["barangay_id"]], forecast_months)
            barangay_breakdown.append({
                **row,
                "on_hand": breakdown_on_hand.get(row["barangay_id"]),
                "expected": fb["horizon_total"] if fb else 0,
                "stockpile": fb["horizon_p90"] if fb else 0,
                "ci_low": fb["horizon_ci_low"] if fb else None,
                "ci_high": fb["horizon_ci_high"] if fb else None,
            })

    chart_forecast = (ml_predict.forecast_lgu(forecast_lgu_choice, forecast_months + 1, include_current=True)
                      if lgu_forecast else None)
    chart_months = chart_forecast["months"] if chart_forecast else []
    # Buffer (stockpile) bars are hidden unless the user turns them on; the axis fits whatever is shown.
    show_buffer = request.args.get("show_buffer") == "1"
    # The axis fits the top of each month's 95% confidence interval (and the stockpile marker when shown),
    # plus 8% headroom so the range labels above the bars never touch the top of the chart.
    peak = max([max(m["projected_packs"], m["ci_high"] or 0,
                    (m["p90_packs"] if show_buffer else 0))
                for m in chart_months], default=0) * 1.08
    step = min((c * mag for mag in (1, 10, 100, 1000, 10000, 100000) for c in (1, 2, 2.5, 5)
                if c * mag * 4 >= peak), default=1)
    step = max(int(-(-step // 1)), 1)
    chart_axis_max = step * 4
    chart_axis_ticks = [step * i for i in range(5)]
    month_breakdown = {}
    if lgu_forecast:
        shares = sorted(ml_predict.share_breakdown(forecast_lgu_choice), key=lambda r: r["share"], reverse=True)
        on_hand = dict(BarangayInventory.query.with_entities(
            BarangayInventory.barangay_id, BarangayInventory.quantity_available
        ).filter(
            BarangayInventory.barangay_id.in_([r["barangay_id"] for r in shares]),
            BarangayInventory.item_type == "food_pack",
        ).all())
        stock_total = sum(v for v in on_hand.values() if v is not None)
        for m in chart_months:
            month_stockpile = m["p90_packs"]
            month_breakdown[m["date"]] = {
                "label": f"{MONTH_NAMES[m['month'] - 1]} {m['year']}",
                "expected": m["projected_packs"],
                "ci_low": m["ci_low"], "ci_high": m["ci_high"],
                "stockpile": month_stockpile,
                "on_hand_total": stock_total,
                "rows": [{
                    "name": r["name"],
                    "share": round(r["share"] * 100, 1),
                    "expected": max(int(round(m["projected_packs"] * r["share"])), 0),
                    "ci_low": max(int(round(m["ci_low"] * r["share"])), 0) if m["ci_low"] is not None else None,
                    "ci_high": max(int(round(m["ci_high"] * r["share"])), 0) if m["ci_high"] is not None else None,
                    "stockpile": max(int(round(month_stockpile * r["share"])), 0),
                    "on_hand": on_hand.get(r["barangay_id"]),
                } for r in shares],
            }

    relief_link = url_for("cswdo.relief_requests") if is_cswdo else "/pswdo/relief-requests"
    transfer_link = url_for("cswdo.municipal_inventory") if is_cswdo else "/pswdo/warehouse-inventory/transfer"
    stock_word = "Municipal" if is_cswdo else "Provincial"

    recommendations = []
    top = ranking[0] if ranking else None
    if top and top["priority_rank"] >= 3:
        brgy_stock = top["on_hand_stock"]
        stock_txt = ("no stock on record" if brgy_stock is None
                     else f"Brgy. {top['name']} has {brgy_stock:,} packs on hand")
        recommendations.append({
            "type": "critical" if top["priority_rank"] == 4 else "warning",
            "title": f"Prioritize {top['name']}",
            "tag": top["priority_label"],
            "detail": f"{top['affected_families']:,} affected families and {top['packs_needed']:,} packs needed"
                       f" ({'submitted request' if top['need_source'] == 'request' else 'model estimate'})."
                       f" Current stock: {stock_txt}.",
            "link_label": "View Barangay Reports" if is_cswdo else "View Relief Request",
            "link": (url_for("cswdo.damage_assessment", tab="all", barangay_id=top["barangay_id"])
                     if is_cswdo else relief_link + "?municipality=" + top["lgu"]),
        })
    for rec in _forecast_recommendations(warehouses, forecast_months, "cswdo" if is_cswdo else "pswdo"):
        if rec["lgu"] not in scope_lgus:
            continue
        recommendations.append({
            "type": rec["type"], "title": rec["title"],
            "tag": "Forecast", "detail": rec["detail"],
            "link_label": "Request Stock" if is_cswdo else "View Stock Transfer",
            "link": relief_link if is_cswdo else transfer_link,
        })
    for rec in _barangay_recommendations(all_warehouses, scope_lgus, forecast_months,
                                         "cswdo" if is_cswdo else "pswdo"):
        recommendations.append({
            "type": rec["type"], "title": rec["title"], "tag": "Barangays", "detail": rec["detail"],
            "link_label": "Allocate to Barangays" if is_cswdo else "View Relief Requests",
            "link": url_for("cswdo.deliveries") if is_cswdo else relief_link,
            "barangays": rec["barangays"], "lgu": rec["lgu"],
            "total_short": rec["total_short"], "horizon_months": rec["horizon_months"],
        })
    for rec in _stock_recommendations(warehouses):
        recommendations.append({
            "type": rec["type"], "title": rec["title"], "tag": None, "detail": rec["detail"],
            "link_label": "View Stock Transfer" if not is_cswdo else "View Warehouse", "link": transfer_link,
        })
    if days_remaining is not None:
        recommendations.append({
            "type": "info" if days_remaining >= 8 else "warning",
            "title": f"Current inventory sufficient for {int(days_remaining)} days" if days_remaining >= 8 else f"{stock_word} stock running low",
            "tag": None,
            "detail": f"{stock_word} stock of {total_food_packs:,} packs covers estimated needs for "
                      f"approximately {int(days_remaining)} days at the current combined burn rate of "
                      f"{burn_rate:,.0f} packs/day.",
            "link_label": None, "link": None,
        })

    return render_template(
        "prediction/index.html",
        active_events=active_events,
        event=event,
        event_id=event_id,
        target_lgus=scope_lgus,
        is_cswdo=is_cswdo,
        can_allocate=can_allocate,
        scope_label=(scope_lgus[0] + " MSWDO/CSWDO") if is_cswdo and scope_lgus else "PSWDO",
        municipality_filter=municipality_filter,
        days_filter=days_filter,
        estimated_need=estimated_need,
        total_food_packs=total_food_packs,
        days_remaining=days_remaining,
        combined_cover=combined_cover,
        cover_horizon=cover_horizon,
        burn_rate=burn_rate,
        estimated_three_day_need=estimated_three_day_need,
        total_affected_families=total_affected_families,
        recommendations=recommendations,
        ranking=ranking,
        warehouse_cards=warehouse_cards,
        model_available=ml_predict.is_model_available(),
        fulfillable_warehouses=fulfillable_warehouses,
        forecast_months=forecast_months,
        forecast_lgu_choice=forecast_lgu_choice,
        lgu_forecast=lgu_forecast,
        forecast_summary_by_lgu=forecast_summary_by_lgu,
        barangay_breakdown=barangay_breakdown,
        month_breakdown=month_breakdown,
        chart_months=chart_months,
        chart_axis_max=chart_axis_max,
        chart_axis_ticks=chart_axis_ticks,
        cover_chart=cover_chart,
        cover_wh=cover_wh,
        distribution_history=_distribution_history(scope_lgus),
        show_breakdown=show_breakdown,
        show_buffer=show_buffer,
    )


# Page: /prediction/model-performance - Model Performance: how reliable the forecast is.
# System admin only, and deliberately not linked anywhere: open it by typing the address.
# 12-month uncertainty ranges, how the safety buffer was worked out, weighted R² per predictor,
# and the leave-one-typhoon-out accuracy tables with the 'actual vs predicted' chart for one municipality.
@prediction_bp.route("/model-performance")
@login_required
@role_required("system_admin")
def model_performance():
    lgu_choice = request.args.get("lgu", "")
    if lgu_choice not in TARGET_LGUS:
        lgu_choice = TARGET_LGUS[0]

    uncertainty = [f for f in (ml_predict.forecast_lgu(lgu, 12) for lgu in TARGET_LGUS) if f]
    bt = ml_predict.backtest_series(lgu_choice)
    artifact_pi = uncertainty[0]["pi_level"] if uncertainty and uncertainty[0]["pi_level"] else None

    return render_template(
        "prediction/model_performance.html",
        target_lgus=list(TARGET_LGUS),
        lgu_choice=lgu_choice,
        latest_metrics=ModelMetrics.query.order_by(ModelMetrics.trained_at.desc()).first(),
        model_available=ml_predict.is_model_available(),
        uncertainty=uncertainty,
        pi_pct=round(artifact_pi * 100) if artifact_pi else None,
        n_simulations=ml_predict.n_simulations(),
        buffer_cal=ml_predict.buffer_calibration_summary(),
        weighted_r2=ml_predict.weighted_r2_summary(),
        backtest_chart=forecast_charts.backtest_chart(bt) if bt else None,
        loto_cv=ml_predict.loto_cv_summary(),
        loto_packs_cv=ml_predict.loto_packs_cv_summary(),
        loto_p90=ml_predict.p90_coverage_summary(),
    )
