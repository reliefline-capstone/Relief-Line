from datetime import datetime, timedelta

from app.utils.timezone import ph_today

from flask import Blueprint, render_template, request, url_for
from flask_login import login_required, current_user

from app.utils.decorators import role_required
from app.models.barangay import Barangay
from app.models.barangay_status import BarangayDisasterStatus
from app.models.disaster_event import DisasterEvent
from app.models.validation import DistributionRecord
from app.models.prediction import ModelMetrics
from app.models.barangay_inventory import BarangayInventory, food_pack_on_hand
from app.models.barangay_report import BarangayReport
from app.ml import predict as ml_predict
from app.ml import charts as forecast_charts
from app.utils.disaster_events import (
    resolve_effective_event, blocking_event_for_province, relevant_active_events_query,
)

# Reused rather than re-implemented - this is the same TARGET_LGUS scope,
# warehouse loader, stock-transfer recommendation, and stock-adequacy tier
# logic the Dashboard/GIS Map/Relief Requests pages already use.
from app.routes.pswdo import (
    TARGET_LGUS,
    _load_warehouses, _stock_recommendations, _relief_summary,
    _stock_adequacy, _STOCK_TIER,
)

prediction_bp = Blueprint("prediction", __name__)

MONTH_NAMES = ["January", "February", "March", "April", "May", "June", "July",
               "August", "September", "October", "November", "December"]


def _scope_lgus():
    """LGUs this user's analytics view may cover.

    The time-forecasting model is a CSWDO/MSWDO decision-support tool (see the
    manuscript's Ch.1 Purpose and Ch.3 Project Design), so a cswdo_admin is
    pinned to their own municipality - same per-office boundary as
    app.routes.pswdo._gis_scope_lgus. PSWDO/system_admin still see all three
    target LGUs. A CSWDO admin with no office on record gets an empty scope
    rather than falling back to full access.
    """
    if current_user.role == "cswdo_admin":
        office = current_user.office
        if office and office.area_covered in TARGET_LGUS:
            return [office.area_covered]
        return []
    return list(TARGET_LGUS)


def _is_cswdo():
    return current_user.role == "cswdo_admin"


def _resolve_event_map(explicit_event_id, lgus):
    """Per-LGU event ids for this page, plus a single "page" event for the
    banner/burn-rate stat cards.

    An explicit event_id (viewing one specific past event from the dropdown)
    applies uniformly to every lgu, same as before. Otherwise each town
    resolves its own effective event - its own CSWDO-declared local one if
    active, else PSWDO's province-wide one (see app.utils.disaster_events) -
    so a system_admin's province-wide ranking doesn't force one town's event
    onto another's barangays.
    """
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


def _stock_cover(stock, lgu_names, horizon_months):
    """How well `stock` food packs covers what the forecaster says
    `lgu_names` will need. Returns None when there is no trained model.

    stockpile   - recommended stockpile for the horizon (the P90 total; for
                  several LGUs the SUM of their stockpiles, an upper bound
                  since storms rarely peak everywhere at once)
    expected    - expected demand over the same horizon
    coverage_pct- stock / stockpile
    months_cover- how many months of EXPECTED demand the stock lasts, walking
                  the next 12 monthly forecasts (capped at 12)"""
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
        "stockpile": stockpile, "expected": expected, "coverage_pct": coverage, "tier": tier,
        "shortfall": max(stockpile - stock, 0),
        "months_cover": round(months, 1), "covers_12_plus": not exhausted,
    }


def _barangay_snapshot(barangay, status_row, event_id):
    """One barangay's real profile + need figures. The priority tier here is
    STOCK ADEQUACY (see app.routes.pswdo._stock_adequacy) - reported caseload
    (affected families + individuals) vs the barangay's own food-pack stock -
    the same lens the GIS map uses, so this page and the map agree. 'Estimated
    Need' still uses the real submitted request/allocation when one exists,
    else the trained model's forecast."""
    status_key = status_row.status if status_row else "normal"

    relief = _relief_summary([barangay.barangay_id], event_id)
    has_request = relief["requested"] > 0
    predicted = ml_predict.predict_quantity(barangay)
    # P90 safety-stock level for this month (None without a trained model).
    safety_stock = ml_predict.predict_safety_stock(barangay)
    on_hand = food_pack_on_hand(barangay.barangay_id)

    report_row = None
    if event_id:
        report_row = BarangayReport.query.filter(
            BarangayReport.barangay_id == barangay.barangay_id,
            BarangayReport.event_id == event_id,
            BarangayReport.status != "draft",
        ).order_by(
            BarangayReport.submitted_at.desc(), BarangayReport.created_at.desc()
        ).first()
    stock_need = (report_row.affected_families or 0) if report_row else 0
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
        "safety_stock": safety_stock,
        # The barangay's own current food-pack stock - int, or None when the
        # barangay has never reported any. Shown read-only in the ranking and
        # used to prefill a proactive allocation (model estimate − on hand).
        "on_hand_stock": on_hand,
        "suggested_allocation": max((predicted or 0) - (on_hand or 0), 0),
    }


@prediction_bp.route("/")
@login_required
@role_required("cswdo_admin", "system_admin")
def index():
    explicit_event_id = request.args.get("event_id", type=int)

    scope_lgus = _scope_lgus()
    is_cswdo = _is_cswdo()
    # Proactive allocation is a CSWDO/MSWDO action (this page's route is
    # already cswdo_admin/system_admin-only) - just needs an office on file
    # to know which warehouse to deduct from and which barangay it may act on.
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

    # Snapshots below log a real PredictionLog row (deduped per barangay/day)
    # for every barangay whose estimate comes from the model rather than a
    # submitted request - see _barangay_snapshot / log_prediction_once_per_day.
    snapshots = []
    for b in barangays:
        b_event_id = lgu_event_ids.get(b.city_municipality)
        snap = _barangay_snapshot(b, status_map.get(b.barangay_id), b_event_id)
        if snap["need_source"] == "model" and snap["predicted_quantity"] is not None:
            ml_predict.log_prediction_once_per_day(b, snap["predicted_quantity"])
        snapshots.append(snap)

    # ---- Stat cards ----
    estimated_need = sum(s["undelivered"] for s in snapshots)
    all_offices, all_warehouses, _ = _load_warehouses()
    # A CSWDO/MSWDO admin only ever sees their own municipal warehouse here -
    # province-wide depot visibility stays a PSWDO responsibility.
    if is_cswdo and current_user.office:
        warehouses = [w for w in all_warehouses if w["office"].office_id == current_user.office.office_id]
    else:
        warehouses = all_warehouses
    total_food_packs = sum(w["food_pack_qty"] for w in warehouses)
    fulfillable_warehouses = [w for w in warehouses if w["food_pack_qty"] > 0]
    # Burn rate is only meaningful during an active disaster event/operation -
    # one food pack sustains one family for three days (manuscript Scope), so
    # daily burn = affected_families / 3. No active event ⇒ no burn rate.
    total_affected_families = sum(s["affected_families"] for s in snapshots if s["status"] != "normal") if event else 0
    estimated_three_day_need = total_affected_families  # 1 pack per affected family
    burn_rate = round(total_affected_families / 3, 0) if total_affected_families > 0 else 0
    days_remaining = round(total_food_packs / burn_rate, 1) if burn_rate > 0 else None

    # ---- Demand forecast by municipality --------------------------------
    # SUPERSEDED by the time-forecasting model (app.ml.predict.forecast_lgu) -
    # this was a current-moment snapshot (sum of submitted requests / model
    # estimates vs delivered-so-far), not an actual multi-month forecast,
    # and its "Demand Forecast by Municipality" panel is commented out in
    # prediction/index.html in favor of the model-driven per-LGU summary
    # built below (see "Time forecasting - projected demand per LGU").
    # Left here commented out, not deleted, in case the snapshot view is
    # wanted back later.
    # forecast_by_lgu = []
    # for lgu in lgus:
    #     lgu_snaps = [s for s in snapshots if s["lgu"] == lgu]
    #     packs_needed = sum(s["packs_needed"] for s in lgu_snaps)
    #     delivered = sum(s["released"] for s in lgu_snaps)
    #     worst_rank = max((s["priority_rank"] for s in lgu_snaps), default=0)
    #     worst = next((v for v in _STOCK_TIER.values() if v["rank"] == worst_rank), _STOCK_TIER["unrated"])
    #     forecast_by_lgu.append({
    #         "lgu": lgu,
    #         "packs_needed": packs_needed,
    #         "delivered": delivered,
    #         "remaining": max(packs_needed - delivered, 0),
    #         "pct_done": round((delivered / packs_needed) * 100) if packs_needed else 0,
    #         "priority_label": worst["label"],
    #         "priority_tier": worst["tier"],
    #     })
    # forecast_by_lgu.sort(key=lambda f: f["packs_needed"], reverse=True)

    # ---- Priority ranking (barangay-level) - by STOCK SHORTFALL: the
    # barangays least able to cover their own reported caseload from their own
    # food-pack stock float to the top (same lens as the GIS map). Within a
    # tier, the higher need-vs-stock ratio ranks first, then the larger
    # estimated need. ----
    ranking = sorted(
        snapshots,
        key=lambda s: (s["priority_rank"], s["stock_ratio_pct"] or 0, s["packs_needed"]),
        reverse=True,
    )[:8]

    # ---- Warehouse stock vs forecast - each warehouse's stock against the
    # recommended stockpile (see _stock_cover). A CSWDO admin sees their
    # own municipal warehouse vs their LGU's forecast; PSWDO/admin see the
    # province-wide depots vs the whole province's (sum of municipal
    # stockpiles), plus all warehouses combined. The health badge stays the
    # capacity-fill rating (_food_pack_health) - a separate, deliberate lens. ----
    cover_horizon = request.args.get("forecast_months", 6, type=int)
    if cover_horizon not in (3, 6, 9, 12):
        cover_horizon = 6
    warehouse_cards = []
    for w in warehouses:
        # PSWDO sees the province-wide depots; a CSWDO admin sees their own
        # municipal warehouse (already the only entry in `warehouses` for them).
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

    # ---- Model performance (real, honest - see app/ml/train.py) ----
    latest_metrics = ModelMetrics.query.order_by(ModelMetrics.trained_at.desc()).first()

    # ---- Time forecasting - projected demand per LGU over a future horizon
    # (see app.ml.predict.forecast_lgu). Query-param driven, same pattern as
    # municipality_filter/days_filter above - stays on this page rather than
    # a separate route. ----
    forecast_months = request.args.get("forecast_months", 6, type=int)
    if forecast_months not in (3, 6, 9, 12):
        forecast_months = 6
    forecast_lgu_choice = request.args.get("forecast_lgu", "")
    if forecast_lgu_choice not in scope_lgus:
        forecast_lgu_choice = scope_lgus[0] if scope_lgus else None
    lgu_forecast = ml_predict.forecast_lgu(forecast_lgu_choice, forecast_months) if forecast_lgu_choice else None

    # Two line charts built from the forecast (geometry in app.ml.charts):
    #  - "Will the stock last?": cumulative expected / P90 demand vs the
    #    municipal warehouse's stock on hand for the LGU being viewed.
    #  - "How did the model do?": actual vs forecast for the latest backtest
    #    year, for the same LGU.
    cover_chart = backtest_chart = cover_wh = None
    if lgu_forecast:
        wh = next((w for w in all_warehouses
                   if w["office"].office_type == "cswdo"
                   and w["office"].area_covered == forecast_lgu_choice), None)
        if wh is not None:
            cover_chart = forecast_charts.cover_chart(lgu_forecast["months"], wh["food_pack_qty"])
            # Capacity fill and the gap to the recommended stockpile, shown in
            # the same panel (formerly only in "Warehouse Stock vs Forecast",
            # which now shows only for the multi-warehouse admin view).
            cover_wh = {"pct": wh["pct"],
                        "cover": _stock_cover(wh["food_pack_qty"], [forecast_lgu_choice], forecast_months)}
        bt = ml_predict.backtest_series(forecast_lgu_choice)
        if bt:
            backtest_chart = forecast_charts.backtest_chart(bt)

    # Compact per-LGU comparison strip shown above the detailed chart -
    # replaces the old "Demand Forecast by Municipality" snapshot panel
    # (commented out above) with the model's actual current-month + horizon
    # projections for every LGU in scope, not just the one currently picked.
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
        })
    forecast_summary_by_lgu.sort(key=lambda f: f["horizon_total"], reverse=True)

    # Barangay breakdown of the chosen LGU's forecast - each barangay's share
    # and the pieces it is built from (app.ml.predict.share_breakdown), with
    # the packs taken from forecast_barangay so they match the CSV and map.
    # Only built (and shown) when the user clicks "View barangay breakdown"
    # on the Projected Demand by Municipality panel (?show_breakdown=1).
    show_breakdown = request.args.get("show_breakdown") == "1"
    barangay_breakdown = []
    if lgu_forecast and show_breakdown:
        by_id = {b.barangay_id: b for b in Barangay.query.filter_by(city_municipality=forecast_lgu_choice).all()}
        for row in sorted(ml_predict.share_breakdown(forecast_lgu_choice), key=lambda r: r["share"], reverse=True):
            fb = ml_predict.forecast_barangay(by_id[row["barangay_id"]], forecast_months)
            barangay_breakdown.append({
                **row,
                "expected": fb["horizon_total"] if fb else 0,
                "stockpile": fb["horizon_p90"] if fb else 0,
            })

    # Per-month barangay split for the Projected Demand chart: click a month
    # to see only that month's packs per barangay. Same top-down maths as
    # forecast_barangay (barangay share x the LGU's month figure), done
    # straight from lgu_forecast so the forecast isn't recomputed per barangay.
    # The chart also draws the current month (months[0] below), in addition
    # to the next `forecast_months`; tiles/totals still use lgu_forecast.
    chart_forecast = (ml_predict.forecast_lgu(forecast_lgu_choice, forecast_months + 1, include_current=True)
                      if lgu_forecast else None)
    chart_months = chart_forecast["months"] if chart_forecast else []
    # Y axis for that chart: a round top value + evenly spaced ticks.
    peak = max((m["p90_packs"] for m in chart_months), default=0)
    step = min((c * mag for mag in (1, 10, 100, 1000, 10000, 100000) for c in (1, 2, 2.5, 5)
                if c * mag * 4 >= peak), default=1)
    step = max(int(-(-step // 1)), 1)
    chart_axis_max = step * 4
    chart_axis_ticks = [step * i for i in range(5)]
    month_breakdown = {}
    if lgu_forecast:
        shares = sorted(ml_predict.share_breakdown(forecast_lgu_choice), key=lambda r: r["share"], reverse=True)
        # Each barangay's current food-pack stock, read once for the whole
        # LGU (same source as food_pack_on_hand). None = no inventory row on
        # record at all, shown as "No record" - not the same as a real 0.
        on_hand = dict(BarangayInventory.query.with_entities(
            BarangayInventory.barangay_id, BarangayInventory.quantity_available
        ).filter(
            BarangayInventory.barangay_id.in_([r["barangay_id"] for r in shares]),
            BarangayInventory.item_type == "food_pack",
        ).all())
        stock_total = sum(v for v in on_hand.values() if v is not None)
        for m in chart_months:
            month_breakdown[m["date"]] = {
                "label": f"{MONTH_NAMES[m['month'] - 1]} {m['year']}",
                "expected": m["projected_packs"],
                "stockpile": m["p90_packs"],
                "on_hand_total": stock_total,
                "rows": [{
                    "name": r["name"],
                    "share": round(r["share"] * 100, 1),
                    "expected": max(int(round(m["projected_packs"] * r["share"])), 0),
                    "stockpile": max(int(round(m["p90_packs"] * r["share"])), 0),
                    "on_hand": on_hand.get(r["barangay_id"]),
                } for r in shares],
            }

    # ---- Recommendations: real stock-transfer rules + top-priority barangay ----
    # Link targets are role-aware - the PSWDO stock-transfer / relief-request
    # pages are role_required("pswdo_admin", ...) and would 403 a cswdo_admin.
    relief_link = url_for("cswdo.relief_requests") if is_cswdo else "/pswdo/relief-requests"
    transfer_link = url_for("cswdo.municipal_inventory") if is_cswdo else "/pswdo/warehouse-inventory/transfer"
    stock_word = "Municipal" if is_cswdo else "Provincial"

    recommendations = []
    top = ranking[0] if ranking else None
    if top and top["priority_rank"] >= 3:
        local_office = next((o for o in all_offices if o.office_type == "cswdo" and o.area_covered == top["lgu"]), None)
        local_stock = next((w["food_pack_qty"] for w in warehouses if local_office and w["office"].office_id == local_office.office_id), 0)
        recommendations.append({
            "type": "critical" if top["priority_rank"] == 4 else "warning",
            "title": f"Prioritize {top['name']}",
            "tag": top["priority_label"],
            "detail": f"{top['affected_families']:,} affected families and {top['packs_needed']:,} packs needed"
                       f" ({'submitted request' if top['need_source'] == 'request' else 'model estimate'})."
                       f" Current local stock: {local_stock:,} packs only.",
            "link_label": "View Relief Request",
            "link": relief_link + ("?municipality=" + top["lgu"] if not is_cswdo else ""),
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
        # forecast_by_lgu=forecast_by_lgu,  # superseded - see comment above where it's built
        ranking=ranking,
        warehouse_cards=warehouse_cards,
        latest_metrics=latest_metrics,
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
        backtest_chart=backtest_chart,
        show_breakdown=show_breakdown,
        loto_cv=ml_predict.loto_cv_summary(),
        loto_packs_cv=ml_predict.loto_packs_cv_summary(),
        loto_p90=ml_predict.p90_coverage_summary(),
    )
