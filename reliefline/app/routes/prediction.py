from datetime import datetime, timedelta

from flask import Blueprint, render_template, request, Response, url_for
from flask_login import login_required, current_user

from app.utils.decorators import role_required
from app.models.office import Office
from app.models.warehouse import WarehouseInventory
from app.models.barangay import Barangay
from app.models.barangay_status import BarangayDisasterStatus
from app.models.disaster_event import DisasterEvent
from app.models.validation import DistributionRecord
from app.models.prediction import ModelMetrics
from app.ml import predict as ml_predict

# Reused rather than re-implemented — this is the same TARGET_LGUS scope,
# priority-tier mapping, warehouse loader, and stock-transfer recommendation
# logic the Dashboard/GIS Map/Relief Requests pages already use.
from app.routes.pswdo import (
    TARGET_LGUS, PRIORITY_BY_STATUS, DEFAULT_PRIORITY,
    _priority_info, _load_warehouses, _stock_recommendations, _relief_summary,
)

prediction_bp = Blueprint("prediction", __name__)


def _scope_lgus():
    """LGUs this user's analytics view may cover.

    The Linear Regression model is a CSWDO/MSWDO decision-support tool (see the
    manuscript's Ch.1 Purpose and Ch.3 Project Design), so a cswdo_admin is
    pinned to their own municipality — same per-office boundary as
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


def _resolve_event(event_id):
    if event_id:
        return DisasterEvent.query.get(event_id)
    return DisasterEvent.query.filter_by(status="active").order_by(DisasterEvent.start_date.desc()).first()


def _barangay_snapshot(barangay, status_row, event_id):
    """One barangay's real profile + status + need figures. 'Estimated Need'
    uses the real submitted request when one exists; otherwise it falls back
    to the trained model's forecast (see app/ml — currently low-confidence,
    see the Model Performance panel)."""
    status_key = status_row.status if status_row else "normal"
    priority = _priority_info(status_key)

    relief = _relief_summary([barangay.barangay_id], event_id)
    has_request = relief["requested"] > 0
    predicted = ml_predict.predict_quantity(barangay)

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
        "priority_label": priority["label"],
        "priority_tier": priority["tier"],
        "priority_rank": priority["rank"],
        "affected_families": status_row.affected_families if status_row else 0,
        "packs_needed": packs_needed,
        "released": released,
        "undelivered": max(packs_needed - released, 0),
        "need_source": source,
        "predicted_quantity": predicted,
    }


@prediction_bp.route("/")
@login_required
@role_required("cswdo_admin", "system_admin")
def index():
    active_events = DisasterEvent.query.filter_by(status="active").order_by(
        DisasterEvent.start_date.desc()
    ).all()
    event_id = request.args.get("event_id", type=int)
    event = _resolve_event(event_id)
    event_id = event.event_id if event else None

    scope_lgus = _scope_lgus()
    is_cswdo = _is_cswdo()
    municipality_filter = request.args.get("municipality", "all")
    if municipality_filter != "all" and municipality_filter in scope_lgus:
        lgus = [municipality_filter]
    else:
        municipality_filter = "all"
        lgus = scope_lgus
    days_filter = request.args.get("days", 30, type=int)

    barangays = Barangay.query.filter(Barangay.city_municipality.in_(lgus)).order_by(
        Barangay.city_municipality, Barangay.barangay_name
    ).all()

    status_map = {}
    if event_id:
        rows = BarangayDisasterStatus.query.filter_by(event_id=event_id).all()
        status_map = {r.barangay_id: r for r in rows}

    # Snapshots below log a real PredictionLog row (deduped per barangay/day)
    # for every barangay whose estimate comes from the model rather than a
    # submitted request — see _barangay_snapshot / log_prediction_once_per_day.
    snapshots = []
    for b in barangays:
        snap = _barangay_snapshot(b, status_map.get(b.barangay_id), event_id)
        if snap["need_source"] == "model" and snap["predicted_quantity"] is not None:
            ml_predict.log_prediction_once_per_day(b, snap["predicted_quantity"])
        snapshots.append(snap)

    # ---- Stat cards ----
    estimated_need = sum(s["undelivered"] for s in snapshots)
    all_offices, all_warehouses, _ = _load_warehouses()
    # A CSWDO/MSWDO admin only ever sees their own municipal warehouse here —
    # province-wide depot visibility stays a PSWDO responsibility.
    if is_cswdo and current_user.office:
        warehouses = [w for w in all_warehouses if w["office"].office_id == current_user.office.office_id]
    else:
        warehouses = all_warehouses
    total_food_packs = sum(w["food_pack_qty"] for w in warehouses)
    fulfillable_warehouses = [w for w in warehouses if w["food_pack_qty"] > 0]
    # Burn rate is only meaningful during an active disaster event/operation —
    # one food pack sustains one family for three days (manuscript Scope), so
    # daily burn = affected_families / 3. No active event ⇒ no burn rate.
    total_affected_families = sum(s["affected_families"] for s in snapshots if s["status"] != "normal") if event else 0
    estimated_three_day_need = total_affected_families  # 1 pack per affected family
    burn_rate = round(total_affected_families / 3, 0) if total_affected_families > 0 else 0
    days_remaining = round(total_food_packs / burn_rate, 1) if burn_rate > 0 else None

    # ---- Demand forecast by municipality ----
    forecast_by_lgu = []
    for lgu in lgus:
        lgu_snaps = [s for s in snapshots if s["lgu"] == lgu]
        packs_needed = sum(s["packs_needed"] for s in lgu_snaps)
        delivered = sum(s["released"] for s in lgu_snaps)
        worst_rank = max((s["priority_rank"] for s in lgu_snaps), default=0)
        worst = next((v for v in PRIORITY_BY_STATUS.values() if v["rank"] == worst_rank), DEFAULT_PRIORITY)
        forecast_by_lgu.append({
            "lgu": lgu,
            "packs_needed": packs_needed,
            "delivered": delivered,
            "remaining": max(packs_needed - delivered, 0),
            "pct_done": round((delivered / packs_needed) * 100) if packs_needed else 0,
            "priority_label": worst["label"],
            "priority_tier": worst["tier"],
        })
    forecast_by_lgu.sort(key=lambda f: f["packs_needed"], reverse=True)

    # ---- Priority ranking (barangay-level; real status data ranks first,
    # model-only estimates fill remaining slots) ----
    ranking = sorted(
        snapshots,
        key=lambda s: (s["priority_rank"], s["affected_families"], s["packs_needed"]),
        reverse=True,
    )[:8]

    # ---- Warehouse stock forecast — the province-wide PSWDO warehouses only
    # (municipal CSWDO offices are covered on the GIS Map's per-municipality
    # "assigned warehouse" card instead) ----
    warehouse_cards = []
    for w in warehouses:
        # PSWDO sees the province-wide depots; a CSWDO admin sees their own
        # municipal warehouse (already the only entry in `warehouses` for them).
        if not is_cswdo and w["office"].office_type != "pswdo":
            continue
        days_left = round(w["food_pack_qty"] / burn_rate, 1) if burn_rate > 0 else None
        warehouse_cards.append({
            "name": w["office"].office_name,
            "food_pack_qty": w["food_pack_qty"],
            "capacity": w["capacity"],
            "pct": w["pct"],
            "health": w["health"],
            "days_left": days_left,
            "burn_rate": burn_rate,
        })

    # ---- Historical trend — real DistributionRecord history, whatever there
    # is of it (this deployment currently has activity on a single date) ----
    since = datetime.now().date() - timedelta(days=days_filter)
    history_rows = DistributionRecord.query.join(Barangay).filter(
        Barangay.city_municipality.in_(lgus),
        DistributionRecord.distribution_date >= since,
        DistributionRecord.dispatch_status == "delivered",
    ).all()
    by_date = {}
    for r in history_rows:
        by_date.setdefault(r.distribution_date, 0)
        by_date[r.distribution_date] += r.quantity_released
    historical_trend = [{"date": d.strftime("%b %d"), "packs": qty} for d, qty in sorted(by_date.items())]

    # ---- Model performance (real, honest — see app/ml/train.py) ----
    latest_metrics = ModelMetrics.query.order_by(ModelMetrics.trained_at.desc()).first()

    # ---- Recommendations: real stock-transfer rules + top-priority barangay ----
    # Link targets are role-aware — the PSWDO stock-transfer / relief-request
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
        scope_label=(scope_lgus[0] + " MSWDO/CSWDO") if is_cswdo and scope_lgus else "PSWDO",
        municipality_filter=municipality_filter,
        days_filter=days_filter,
        estimated_need=estimated_need,
        total_food_packs=total_food_packs,
        days_remaining=days_remaining,
        burn_rate=burn_rate,
        estimated_three_day_need=estimated_three_day_need,
        total_affected_families=total_affected_families,
        recommendations=recommendations,
        forecast_by_lgu=forecast_by_lgu,
        ranking=ranking,
        warehouse_cards=warehouse_cards,
        historical_trend=historical_trend,
        latest_metrics=latest_metrics,
        model_available=ml_predict.is_model_available(),
        fulfillable_warehouses=fulfillable_warehouses,
    )


@prediction_bp.route("/export.csv")
@login_required
@role_required("cswdo_admin", "system_admin")
def export_forecast():
    import csv
    import io

    event_id = request.args.get("event_id", type=int)
    event = _resolve_event(event_id)
    event_id = event.event_id if event else None
    scope_lgus = _scope_lgus()
    municipality_filter = request.args.get("municipality", "all")
    if municipality_filter != "all" and municipality_filter in scope_lgus:
        lgus = [municipality_filter]
    else:
        lgus = scope_lgus

    barangays = Barangay.query.filter(Barangay.city_municipality.in_(lgus)).order_by(
        Barangay.city_municipality, Barangay.barangay_name
    ).all()
    status_map = {}
    if event_id:
        rows = BarangayDisasterStatus.query.filter_by(event_id=event_id).all()
        status_map = {r.barangay_id: r for r in rows}

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow([
        "Municipality", "Barangay", "Status", "Affected Families",
        "Packs Needed", "Need Source", "Delivered", "Undelivered",
    ])
    for b in barangays:
        s = _barangay_snapshot(b, status_map.get(b.barangay_id), event_id)
        writer.writerow([
            s["lgu"], s["name"], s["priority_label"], s["affected_families"],
            s["packs_needed"], s["need_source"], s["released"], s["undelivered"],
        ])

    return Response(
        buffer.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=predictive_analytics.csv"},
    )
