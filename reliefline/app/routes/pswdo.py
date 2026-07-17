import csv
import io
import os

from flask import Blueprint, render_template, request, Response, redirect, url_for, flash, abort, current_app
from flask_login import login_required, current_user
from datetime import date, datetime, timedelta
from werkzeug.utils import secure_filename
from app.extensions import db
from app.utils.decorators import role_required
from app.models.office import Office
from app.models.barangay import Barangay
from app.models.warehouse import WarehouseInventory
from app.models.allocation import AllocationRecord
from app.models.validation import DistributionRecord
from app.models.disaster_event import DisasterEvent
from app.models.barangay_status import BarangayDisasterStatus
from app.models.activity_log import ActivityLog, DailyOpsStat
from app.models.logistics import Vehicle, Driver

pswdo_bp = Blueprint("pswdo", __name__)

TARGET_LGUS = ["Urdaneta City", "Santa Barbara", "Calasiao"]
LOW_STOCK_THRESHOLD = 0.30
MAX_CAPACITY_BY_TYPE = {"hygiene_kit": 5000, "kitchen_kit": 5000}

WAREHOUSE_HEALTHY = 0.70
WAREHOUSE_MODERATE = 0.30

# Priority is derived from BarangayDisasterStatus for the active event —
# there is no priority/urgency column in the schema, so this maps the
# existing 4-tier status enum onto the labels the UI shows.
PRIORITY_BY_STATUS = {
    "high_priority": {"label": "Critical", "tier": "critical", "detail": "Immediate action required", "rank": 4},
    "needs_assistance": {"label": "High", "tier": "high", "detail": "Needs attention", "rank": 3},
    "monitoring": {"label": "Medium", "tier": "medium", "detail": "Monitor", "rank": 2},
    "normal": {"label": "Low", "tier": "low", "detail": "Stable", "rank": 1},
}
DEFAULT_PRIORITY = {"label": "Unrated", "tier": "unrated", "detail": "No status on record", "rank": 0}

DISPATCH_STATUS_LABELS = {
    "preparing": "Preparing",
    "loaded": "Loaded",
    "dispatched": "Dispatched",
    "in_transit": "In Transit",
    "delivered": "Delivered",
    "delayed": "Delayed",
}

# Sequential happy-path stages for the detail-page stepper (delayed is a side-branch flag, not a step)
DISPATCH_STEPS = ["approved", "preparing", "loaded", "dispatched", "in_transit", "delivered"]
STEP_LABELS = {
    "approved": "Approved", "preparing": "Preparing", "loaded": "Loaded",
    "dispatched": "Dispatched", "in_transit": "In Transit", "delivered": "Delivered",
}

# Route-map placeholder progress, 0 = at warehouse, 100 = at destination
ROUTE_PROGRESS_BY_STATUS = {
    "preparing": 0, "loaded": 10, "dispatched": 35,
    "in_transit": 65, "delivered": 100, "delayed": 50,
}


def _priority_info(status_key):
    return PRIORITY_BY_STATUS.get(status_key, DEFAULT_PRIORITY)


def _load_warehouses():
    """ALL warehouses (province-wide infrastructure, PSWDO-managed) with current food-pack stock."""
    all_offices = Office.query.filter(
        db.or_(
            Office.office_type == "pswdo",
            db.and_(Office.office_type == "cswdo", Office.area_covered.in_(TARGET_LGUS))
        )
    ).all()

    warehouses = []
    total_food_packs = 0
    for office in all_offices:
        food_pack = WarehouseInventory.query.filter_by(
            office_id=office.office_id, item_type="food_pack"
        ).first()
        qty = food_pack.quantity_available if food_pack else 0
        capacity = office.capacity_food_pack or 20000
        pct = round((qty / capacity) * 100, 0) if capacity > 0 else 0

        if pct >= WAREHOUSE_HEALTHY * 100:
            health = "Healthy"
        elif pct >= WAREHOUSE_MODERATE * 100:
            health = "Moderate"
        else:
            health = "Low"

        warehouses.append({
            "office": office, "food_pack_qty": qty, "capacity": capacity,
            "pct": pct, "health": health
        })
        total_food_packs += qty

    return all_offices, warehouses, total_food_packs


@pswdo_bp.route("/dashboard")
@login_required
@role_required("pswdo_admin", "system_admin")
def dashboard():
    today = date.today()
    now = datetime.now()

    # Active typhoon/disaster events
    active_events = DisasterEvent.query.filter_by(status="active").order_by(
        DisasterEvent.start_date.desc()
    ).all()
    primary_event = active_events[0] if active_events else None

    all_offices, warehouses, total_food_packs = _load_warehouses()

    # CSWDO offices only — scope for relief operations (3 target LGUs)
    cswdo_offices = [o for o in all_offices if o.office_type == "cswdo"]
    office_ids = [o.office_id for o in cswdo_offices]

    # Pending allocation requests (a rejected request keeps status="pending" but
    # carries rejection_reason, so it must be excluded here — see AllocationRecord.display_status)
    pending_requests = AllocationRecord.query.join(Barangay).filter(
        Barangay.city_municipality.in_(TARGET_LGUS),
        AllocationRecord.status == "pending",
        AllocationRecord.rejection_reason.is_(None)
    ).order_by(AllocationRecord.allocation_date.desc()).limit(6).all()

    pending_requests_count = AllocationRecord.query.join(Barangay).filter(
        Barangay.city_municipality.in_(TARGET_LGUS),
        AllocationRecord.status == "pending",
        AllocationRecord.rejection_reason.is_(None)
    ).count()

    # Affected families + municipalities (3 target LGUs only)
    total_affected_families = 0
    affected_municipalities = set()
    if active_events:
        event_ids = [e.event_id for e in active_events]
        affected_statuses = BarangayDisasterStatus.query.filter(
            BarangayDisasterStatus.event_id.in_(event_ids),
            BarangayDisasterStatus.status != "normal"
        ).all()
        total_affected_families = sum(s.affected_families for s in affected_statuses)
        affected_municipalities = {s.barangay.city_municipality for s in affected_statuses}

    # Burn rate — based on affected families in the 3 target LGUs,
    # against TOTAL province-wide food pack stock (PSWDO can redistribute)
    burn_rate = round(total_affected_families / 3, 0) if total_affected_families > 0 else 0
    days_remaining = round(total_food_packs / burn_rate, 1) if burn_rate > 0 else None
    estimated_need = int(burn_rate * 3) if burn_rate > 0 else 0  # 3-day estimated need
    remaining_after_3days = max(total_food_packs - estimated_need, 0)

    # Low stock — item-level only, all warehouses
    all_inventory = WarehouseInventory.query.filter(
        WarehouseInventory.office_id.in_([o.office_id for o in all_offices])
    ).all()

    low_stock_items = []
    for item in all_inventory:
        if item.item_type == "food_pack":
            office = next((o for o in all_offices if o.office_id == item.office_id), None)
            max_capacity = office.capacity_food_pack if office else 20000
        else:
            max_capacity = MAX_CAPACITY_BY_TYPE.get(item.item_type, 5000)
        if item.quantity_available <= (max_capacity * LOW_STOCK_THRESHOLD):
            low_stock_items.append(item)

    # System Recommendations — simple threshold-based logic, food_pack only
    recommendations = []
    healthy_wh = [w for w in warehouses if w["health"] == "Healthy"]
    low_wh = [w for w in warehouses if w["health"] == "Low"]

    if low_wh and healthy_wh:
        source = max(healthy_wh, key=lambda w: w["food_pack_qty"])
        target = min(low_wh, key=lambda w: w["pct"])
        transfer_qty = min(2000, source["food_pack_qty"])
        recommendations.append({
            "type": "info",
            "title": f"Transfer {transfer_qty:,} packs → {target['office'].area_covered}",
            "detail": f"From {source['office'].office_name} · High Priority"
        })

    for w in warehouses:
        if w["pct"] < 15:
            recommendations.append({
                "type": "warning",
                "title": "Increase food pack procurement",
                "detail": f"{w['office'].office_name} stock: {w['pct']:.0f}% only"
            })

    for w in warehouses:
        if w["office"].office_type == "cswdo" and w["health"] == "Low":
            recommendations.append({
                "type": "critical",
                "title": f"Prioritize {w['office'].area_covered} next dispatch",
                "detail": "Critical stock level"
            })

    # Today's Distribution Progress (3 target LGUs, active event)
    today_allocations = []
    if primary_event:
        today_allocations = AllocationRecord.query.join(Barangay).filter(
            Barangay.city_municipality.in_(TARGET_LGUS),
            AllocationRecord.status.in_(["approved", "released"]),
            AllocationRecord.event_id == primary_event.event_id
        ).all()

    total_allocated_today = sum(a.allocated_quantity for a in today_allocations)

    today_distributions = DistributionRecord.query.filter_by(distribution_date=today).all()
    total_released_today = sum(d.quantity_released for d in today_distributions)
    packs_remaining = max(total_allocated_today - total_released_today, 0)
    completion_pct = round((total_released_today / total_allocated_today) * 100, 0) if total_allocated_today > 0 else 0

    municipalities_served = len(set(
        d.barangay.city_municipality for d in today_distributions if d.barangay
    ))

    vehicle_stats = DailyOpsStat.query.filter(
        DailyOpsStat.office_id.in_(office_ids),
        DailyOpsStat.stat_date == today
    ).all()
    vehicles_active = sum(v.vehicles_active for v in vehicle_stats)

    by_municipality = []
    for lgu in TARGET_LGUS:
        lgu_allocated = sum(a.allocated_quantity for a in today_allocations if a.barangay.city_municipality == lgu)
        lgu_released = sum(d.quantity_released for d in today_distributions if d.barangay and d.barangay.city_municipality == lgu)
        if lgu_allocated > 0:
            by_municipality.append({"lgu": lgu, "released": lgu_released, "allocated": lgu_allocated})

    # Recent activity feed
    recent_activities = ActivityLog.query.order_by(ActivityLog.created_at.desc()).limit(4).all()
    notifications = ActivityLog.query.order_by(ActivityLog.created_at.desc()).limit(3).all()

    return render_template(
        "pswdo/dashboard.html",
        active_events=active_events,
        primary_event=primary_event,
        warehouses=warehouses,
        total_food_packs=total_food_packs,
        pending_requests=pending_requests,
        pending_requests_count=pending_requests_count,
        total_affected_families=total_affected_families,
        affected_municipalities_count=len(affected_municipalities),
        total_target_lgus=len(TARGET_LGUS),
        low_stock_items=low_stock_items,
        burn_rate=burn_rate,
        days_remaining=days_remaining,
        estimated_need=estimated_need,
        remaining_after_3days=remaining_after_3days,
        recommendations=recommendations,
        completion_pct=completion_pct,
        municipalities_served=municipalities_served,
        total_released_today=total_released_today,
        packs_remaining=packs_remaining,
        vehicles_active=vehicles_active,
        by_municipality=by_municipality,
        recent_activities=recent_activities,
        notifications=notifications,
        now=now
    )


def _filtered_relief_requests():
    """Shared filter/sort logic for the relief requests page and its CSV export."""
    status_filter = request.args.get("status", "all")
    municipality_filter = request.args.get("municipality", "all")
    priority_filter = request.args.get("priority", "all")
    date_filter = request.args.get("date", "")
    search_query = request.args.get("q", "").strip()

    active_event = DisasterEvent.query.filter_by(status="active").order_by(
        DisasterEvent.start_date.desc()
    ).first()

    base_query = AllocationRecord.query.join(Barangay).filter(
        Barangay.city_municipality.in_(TARGET_LGUS)
    )

    total_count = base_query.count()
    pending_count = base_query.filter(
        AllocationRecord.status == "pending",
        AllocationRecord.rejection_reason.is_(None)
    ).count()
    approved_count = base_query.filter(AllocationRecord.status == "approved").count()
    released_count = base_query.filter(AllocationRecord.status == "released").count()

    query = base_query
    if status_filter != "all":
        query = query.filter(AllocationRecord.status == status_filter)
    if municipality_filter != "all":
        query = query.filter(Barangay.city_municipality == municipality_filter)
    if date_filter:
        try:
            parsed_date = datetime.strptime(date_filter, "%Y-%m-%d").date()
            query = query.filter(AllocationRecord.allocation_date == parsed_date)
        except ValueError:
            pass
    if search_query:
        like = f"%{search_query}%"
        query = query.filter(
            db.or_(
                Barangay.city_municipality.ilike(like),
                Barangay.barangay_name.ilike(like),
            )
        )

    matching_requests = query.order_by(AllocationRecord.allocation_date.desc()).all()

    # Priority lookup, scoped to the active event (falls back to "Unrated" otherwise)
    status_map = {}
    if active_event:
        statuses = BarangayDisasterStatus.query.filter_by(event_id=active_event.event_id).all()
        status_map = {s.barangay_id: s.status for s in statuses}

    enriched = []
    for req in matching_requests:
        priority = _priority_info(status_map.get(req.barangay_id))
        enriched.append((req, priority))

    if priority_filter != "all":
        enriched = [pair for pair in enriched if pair[1]["tier"] == priority_filter]

    enriched.sort(key=lambda pair: (pair[1]["rank"], pair[0].allocation_date), reverse=True)

    return {
        "enriched": enriched,
        "active_event": active_event,
        "pending_count": pending_count,
        "approved_count": approved_count,
        "released_count": released_count,
        "total_count": total_count,
        "status_filter": status_filter,
        "municipality_filter": municipality_filter,
        "priority_filter": priority_filter,
        "date_filter": date_filter,
        "search_query": search_query,
    }


@pswdo_bp.route("/relief-requests")
@login_required
@role_required("pswdo_admin", "system_admin")
def relief_requests():
    ctx = _filtered_relief_requests()
    enriched = ctx["enriched"]

    per_page = 10
    total_filtered = len(enriched)
    total_pages = max((total_filtered + per_page - 1) // per_page, 1)
    page = max(request.args.get("page", 1, type=int), 1)
    page = min(page, total_pages)
    start = (page - 1) * per_page
    page_items = enriched[start:start + per_page]

    return render_template(
        "pswdo/relief_requests.html",
        active_event=ctx["active_event"],
        pending_count=ctx["pending_count"],
        approved_count=ctx["approved_count"],
        released_count=ctx["released_count"],
        total_count=ctx["total_count"],
        total_filtered=total_filtered,
        status_filter=ctx["status_filter"],
        municipality_filter=ctx["municipality_filter"],
        priority_filter=ctx["priority_filter"],
        date_filter=ctx["date_filter"],
        search_query=ctx["search_query"],
        target_lgus=TARGET_LGUS,
        requests=page_items,
        page=page,
        total_pages=total_pages,
    )


@pswdo_bp.route("/relief-requests/export")
@login_required
@role_required("pswdo_admin", "system_admin")
def export_relief_requests():
    ctx = _filtered_relief_requests()

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow([
        "Municipality", "Barangay", "Request ID", "Typhoon Event",
        "Requested Packs", "Priority", "Date", "Status"
    ])
    for req, priority in ctx["enriched"]:
        writer.writerow([
            req.barangay.city_municipality,
            req.barangay.barangay_name,
            f"RR-{req.allocation_date.year}-{req.allocation_id:03d}",
            req.event.event_name if req.event else (req.disaster_event or ""),
            req.predicted_quantity,
            priority["label"],
            req.allocation_date.isoformat(),
            req.status,
        ])

    return Response(
        buffer.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=relief_requests.csv"},
    )


def _urgency_score(barangay, status_key, predicted_quantity, municipal_available):
    """
    0-100 score, weighted from real fields since there's no urgency column in the
    schema: disaster status tier (40%), barangay disaster_risk_index (20%),
    poverty_incidence (15%), past_calamity_freq (10%), and the requested-vs-available
    stock gap at the municipal office (15%).
    """
    rank = _priority_info(status_key)["rank"]  # 0-4
    status_component = (rank / 4) * 40
    risk_component = min(float(barangay.disaster_risk_index or 0) / 10, 1) * 20
    poverty_component = min(float(barangay.poverty_incidence or 0) / 100, 1) * 15
    calamity_component = min((barangay.past_calamity_freq or 0) / 10, 1) * 10

    if predicted_quantity > 0:
        gap = max(0, (predicted_quantity - municipal_available) / predicted_quantity)
    else:
        gap = 0
    stock_component = gap * 15

    return round(status_component + risk_component + poverty_component + calamity_component + stock_component)


def _get_target_scoped_request(allocation_id):
    req = AllocationRecord.query.get_or_404(allocation_id)
    if req.barangay.city_municipality not in TARGET_LGUS:
        abort(404)
    return req


@pswdo_bp.route("/relief-requests/<int:allocation_id>")
@login_required
@role_required("pswdo_admin", "system_admin")
def relief_request_detail(allocation_id):
    req = _get_target_scoped_request(allocation_id)

    status_key = None
    affected_families = 0
    if req.event_id:
        bs = BarangayDisasterStatus.query.filter_by(
            barangay_id=req.barangay_id, event_id=req.event_id
        ).first()
        if bs:
            status_key = bs.status
            affected_families = bs.affected_families

    priority = _priority_info(status_key)

    affected_barangays_count = 0
    if req.event_id:
        affected_barangays_count = BarangayDisasterStatus.query.join(Barangay).filter(
            BarangayDisasterStatus.event_id == req.event_id,
            BarangayDisasterStatus.status != "normal",
            Barangay.city_municipality == req.barangay.city_municipality,
        ).count()

    # The requesting municipality's own office stock, for the inventory-gap comparison
    municipal_office = req.office
    municipal_inventory = None
    if municipal_office:
        municipal_inventory = WarehouseInventory.query.filter_by(
            office_id=municipal_office.office_id, item_type="food_pack"
        ).first()
    municipal_available = municipal_inventory.quantity_available if municipal_inventory else 0
    municipal_capacity = municipal_office.capacity_food_pack if municipal_office else 20000

    _, warehouses, total_food_packs = _load_warehouses()

    urgency_score = _urgency_score(req.barangay, status_key, req.predicted_quantity, municipal_available)
    suggested_allocation = min(req.predicted_quantity, total_food_packs)
    enough_stock = total_food_packs >= req.predicted_quantity

    # Fixed 2-day SLA heuristic off the real allocation_date, purely for the deadline hint
    deadline_label, deadline_state = None, None
    if req.display_status == "pending":
        days_left = (req.allocation_date + timedelta(days=2) - date.today()).days
        if days_left < 0:
            deadline_label, deadline_state = "Overdue", "overdue"
        elif days_left == 0:
            deadline_label, deadline_state = "Today", "today"
        else:
            deadline_label, deadline_state = f"In {days_left} day{'s' if days_left != 1 else ''}", "upcoming"

    fulfillable_warehouses = [w for w in warehouses if w["food_pack_qty"] > 0]

    return render_template(
        "pswdo/relief_request_detail.html",
        req=req,
        priority=priority,
        affected_families=affected_families,
        affected_barangays_count=affected_barangays_count,
        municipal_office=municipal_office,
        municipal_available=municipal_available,
        municipal_capacity=municipal_capacity,
        total_food_packs=total_food_packs,
        urgency_score=urgency_score,
        suggested_allocation=suggested_allocation,
        enough_stock=enough_stock,
        deadline_label=deadline_label,
        deadline_state=deadline_state,
        fulfillable_warehouses=fulfillable_warehouses,
    )


@pswdo_bp.route("/relief-requests/<int:allocation_id>/approve", methods=["POST"])
@login_required
@role_required("pswdo_admin", "system_admin")
def approve_relief_request(allocation_id):
    req = _get_target_scoped_request(allocation_id)

    if req.display_status != "pending":
        flash("This request has already been decided.", "error")
        return redirect(url_for("pswdo.relief_request_detail", allocation_id=allocation_id))

    office_id = request.form.get("fulfilling_office_id", type=int)
    quantity = request.form.get("quantity", type=int)
    expected_delivery = request.form.get("expected_delivery_date", "")
    remarks = request.form.get("remarks", "").strip()

    office = Office.query.get(office_id) if office_id else None
    if not office:
        flash("Select a warehouse to fulfill this request.", "error")
        return redirect(url_for("pswdo.relief_request_detail", allocation_id=allocation_id))

    if not quantity or quantity <= 0 or quantity > req.predicted_quantity:
        flash(f"Quantity must be between 1 and {req.predicted_quantity:,}.", "error")
        return redirect(url_for("pswdo.relief_request_detail", allocation_id=allocation_id))

    inventory = WarehouseInventory.query.filter_by(office_id=office.office_id, item_type="food_pack").first()
    available = inventory.quantity_available if inventory else 0
    if quantity > available:
        flash(f"{office.office_name} only has {available:,} food packs available.", "error")
        return redirect(url_for("pswdo.relief_request_detail", allocation_id=allocation_id))

    req.status = "approved"
    req.allocated_quantity = quantity
    req.fulfilling_office_id = office.office_id
    req.remarks = remarks or None
    req.rejection_reason = None
    req.decided_by = current_user.user_id
    if expected_delivery:
        try:
            req.expected_delivery_date = datetime.strptime(expected_delivery, "%Y-%m-%d").date()
        except ValueError:
            pass

    inventory.quantity_available -= quantity

    label = "Partially approved" if quantity < req.predicted_quantity else "Approved"
    db.session.add(ActivityLog(
        actor_id=current_user.user_id,
        action_type="allocation_approved",
        description=f"{label} {quantity:,} food packs for {req.barangay.city_municipality} from {office.office_name}",
        office_id=office.office_id,
        barangay_id=req.barangay_id,
    ))

    db.session.commit()
    flash(f"{label}: {quantity:,} food packs allocated to {req.barangay.city_municipality}.", "success")
    return redirect(url_for("pswdo.relief_request_detail", allocation_id=allocation_id))


@pswdo_bp.route("/relief-requests/<int:allocation_id>/reject", methods=["POST"])
@login_required
@role_required("pswdo_admin", "system_admin")
def reject_relief_request(allocation_id):
    req = _get_target_scoped_request(allocation_id)

    if req.display_status != "pending":
        flash("This request has already been decided.", "error")
        return redirect(url_for("pswdo.relief_request_detail", allocation_id=allocation_id))

    reason = request.form.get("reason", "").strip()
    if not reason:
        flash("A reason is required to reject a request.", "error")
        return redirect(url_for("pswdo.relief_request_detail", allocation_id=allocation_id))

    req.rejection_reason = reason
    req.decided_by = current_user.user_id
    db.session.add(ActivityLog(
        actor_id=current_user.user_id,
        action_type="allocation_rejected",
        description=f"Rejected relief request from {req.barangay.city_municipality}: {reason}",
        office_id=req.office_id,
        barangay_id=req.barangay_id,
    ))
    db.session.commit()
    flash(f"Request from {req.barangay.city_municipality} has been rejected.", "success")
    return redirect(url_for("pswdo.relief_request_detail", allocation_id=allocation_id))


def _filtered_distributions():
    """Shared filter logic for the distribution page and its CSV export."""
    today = date.today()
    status_filter = request.args.get("status", "all")
    search_query = request.args.get("q", "").strip()

    primary_event = DisasterEvent.query.filter_by(status="active").order_by(
        DisasterEvent.start_date.desc()
    ).first()

    base_query = DistributionRecord.query.join(Barangay).filter(
        Barangay.city_municipality.in_(TARGET_LGUS)
    )
    today_query = base_query.filter(DistributionRecord.distribution_date == today)

    total_today = today_query.count()
    preparing_count = today_query.filter(DistributionRecord.dispatch_status == "preparing").count()
    in_transit_count = today_query.filter(DistributionRecord.dispatch_status == "in_transit").count()
    delivered_today = today_query.filter(DistributionRecord.dispatch_status == "delivered").all()
    delivered_count = len(delivered_today)
    delayed_count = today_query.filter(DistributionRecord.dispatch_status == "delayed").count()
    packs_released = sum(d.quantity_released for d in delivered_today)

    query = base_query
    if status_filter != "all":
        query = query.filter(DistributionRecord.dispatch_status == status_filter)
    if search_query:
        like = f"%{search_query}%"
        query = query.filter(Barangay.city_municipality.ilike(like))

    records = query.order_by(DistributionRecord.distribution_date.desc()).all()

    return {
        "primary_event": primary_event,
        "today": today,
        "total_today": total_today,
        "preparing_count": preparing_count,
        "in_transit_count": in_transit_count,
        "delivered_count": delivered_count,
        "delayed_count": delayed_count,
        "packs_released": packs_released,
        "status_filter": status_filter,
        "search_query": search_query,
        "records": records,
    }


@pswdo_bp.route("/distribution")
@login_required
@role_required("pswdo_admin", "system_admin")
def distribution():
    ctx = _filtered_distributions()
    return render_template(
        "pswdo/distribution.html",
        dispatch_labels=DISPATCH_STATUS_LABELS,
        **ctx,
    )


@pswdo_bp.route("/distribution/export")
@login_required
@role_required("pswdo_admin", "system_admin")
def export_distribution():
    ctx = _filtered_distributions()

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow([
        "Distribution ID", "Request ID", "Municipality", "Warehouse",
        "Packs", "Vehicle", "Driver", "Date", "Status"
    ])
    for rec in ctx["records"]:
        fulfilling = rec.allocation.fulfilling_office or rec.allocation.office
        writer.writerow([
            f"D-{rec.distribution_date.year}-{rec.distribution_id:03d}",
            f"RR-{rec.allocation.allocation_date.year}-{rec.allocation.allocation_id:03d}",
            rec.barangay.city_municipality,
            fulfilling.office_name if fulfilling else "",
            rec.quantity_released,
            rec.vehicle.vehicle_name if rec.vehicle else "Unassigned",
            rec.driver.name if rec.driver else "",
            rec.distribution_date.isoformat(),
            DISPATCH_STATUS_LABELS.get(rec.dispatch_status, rec.dispatch_status),
        ])

    return Response(
        buffer.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=distribution.csv"},
    )


OFFICE_TYPE_PREFIX = {"cswdo": "MSWDO", "pswdo": "PSWDO"}


def _person_label(user, office):
    if not user:
        return "—"
    prefix = OFFICE_TYPE_PREFIX.get(office.office_type) if office else None
    return f"{prefix} - {user.name}" if prefix else user.name


def _get_target_scoped_distribution(distribution_id):
    rec = DistributionRecord.query.get_or_404(distribution_id)
    if rec.barangay.city_municipality not in TARGET_LGUS:
        abort(404)
    return rec


@pswdo_bp.route("/distribution/<int:distribution_id>")
@login_required
@role_required("pswdo_admin", "system_admin")
def distribution_detail(distribution_id):
    rec = _get_target_scoped_distribution(distribution_id)
    alloc = rec.allocation

    status_key = None
    if alloc.event_id:
        bs = BarangayDisasterStatus.query.filter_by(
            barangay_id=alloc.barangay_id, event_id=alloc.event_id
        ).first()
        if bs:
            status_key = bs.status
    priority = _priority_info(status_key)

    fulfilling_office = alloc.fulfilling_office or alloc.office
    inventory = None
    if fulfilling_office:
        inventory = WarehouseInventory.query.filter_by(
            office_id=fulfilling_office.office_id, item_type="food_pack"
        ).first()
    available_stock = inventory.quantity_available if inventory else 0
    stock_after_release = max(available_stock - rec.quantity_released, 0) if rec.dispatch_status not in ("delivered",) else available_stock

    vehicles = Vehicle.query.order_by(Vehicle.vehicle_name).all()
    drivers = Driver.query.order_by(Driver.name).all()

    current_index = DISPATCH_STEPS.index(rec.dispatch_status) if rec.dispatch_status in DISPATCH_STEPS else 1
    route_progress = ROUTE_PROGRESS_BY_STATUS.get(rec.dispatch_status, 0)

    attachments = rec.validation_file.split(",") if rec.validation_file else []

    return render_template(
        "pswdo/distribution_detail.html",
        rec=rec,
        alloc=alloc,
        priority=priority,
        fulfilling_office=fulfilling_office,
        available_stock=available_stock,
        stock_after_release=stock_after_release,
        vehicles=vehicles,
        drivers=drivers,
        dispatch_steps=DISPATCH_STEPS,
        step_labels=STEP_LABELS,
        current_index=current_index,
        route_progress=route_progress,
        dispatch_labels=DISPATCH_STATUS_LABELS,
        requested_by_label=_person_label(alloc.submitted_by, alloc.office),
        approved_by_label=_person_label(alloc.decided_by_user, alloc.fulfilling_office or alloc.office),
        attachments=attachments,
    )


@pswdo_bp.route("/distribution/<int:distribution_id>/assign-vehicle", methods=["POST"])
@login_required
@role_required("pswdo_admin", "system_admin")
def assign_distribution_vehicle(distribution_id):
    rec = _get_target_scoped_distribution(distribution_id)

    vehicle_id = request.form.get("vehicle_id", type=int)
    driver_id = request.form.get("driver_id", type=int)
    plate_number = request.form.get("plate_number", "").strip()
    capacity = request.form.get("capacity_packs", type=int)

    vehicle = Vehicle.query.get(vehicle_id) if vehicle_id else None
    driver = Driver.query.get(driver_id) if driver_id else None
    if not vehicle or not driver:
        flash("Select a vehicle and a driver.", "error")
        return redirect(url_for("pswdo.distribution_detail", distribution_id=distribution_id))

    if plate_number:
        vehicle.plate_number = plate_number
    if capacity:
        vehicle.capacity_packs = capacity

    rec.vehicle_id = vehicle.vehicle_id
    rec.driver_id = driver.driver_id
    db.session.commit()
    flash(f"Assigned {vehicle.vehicle_name} with driver {driver.name}.", "success")
    return redirect(url_for("pswdo.distribution_detail", distribution_id=distribution_id))


@pswdo_bp.route("/distribution/<int:distribution_id>/advance", methods=["POST"])
@login_required
@role_required("pswdo_admin", "system_admin")
def advance_distribution(distribution_id):
    """Handles the simple one-click transitions: preparing -> loaded -> dispatched -> in_transit."""
    rec = _get_target_scoped_distribution(distribution_id)
    target = request.form.get("target")

    valid_transitions = {
        "preparing": "loaded",
        "loaded": "dispatched",
        "dispatched": "in_transit",
    }
    expected_next = valid_transitions.get(rec.dispatch_status)
    if target != expected_next:
        flash("That status change is no longer valid.", "error")
        return redirect(url_for("pswdo.distribution_detail", distribution_id=distribution_id))

    if target == "dispatched" and not (rec.vehicle_id and rec.driver_id):
        flash("Assign a vehicle and driver before dispatching.", "error")
        return redirect(url_for("pswdo.distribution_detail", distribution_id=distribution_id))

    rec.dispatch_status = target
    if target == "dispatched" and not rec.departure_time:
        rec.departure_time = datetime.now().time()

    db.session.add(ActivityLog(
        actor_id=current_user.user_id,
        action_type="distribution_status",
        description=f"D-{rec.distribution_date.year}-{rec.distribution_id:03d} marked {DISPATCH_STATUS_LABELS[target]}",
        office_id=rec.allocation.fulfilling_office_id,
        barangay_id=rec.barangay_id,
    ))
    db.session.commit()
    flash(f"Status updated to {DISPATCH_STATUS_LABELS[target]}.", "success")
    return redirect(url_for("pswdo.distribution_detail", distribution_id=distribution_id))


ALLOWED_PROOF_EXTENSIONS = {"pdf", "jpg", "jpeg", "png", "zip"}


@pswdo_bp.route("/distribution/<int:distribution_id>/confirm-delivery", methods=["POST"])
@login_required
@role_required("pswdo_admin", "system_admin")
def confirm_delivery(distribution_id):
    rec = _get_target_scoped_distribution(distribution_id)

    if rec.dispatch_status != "in_transit":
        flash("Delivery can only be confirmed once a distribution is In Transit.", "error")
        return redirect(url_for("pswdo.distribution_detail", distribution_id=distribution_id))

    received_by = request.form.get("received_by", "").strip()
    condition = request.form.get("condition", "")
    time_received = request.form.get("time_received", "").strip()
    travel_time = request.form.get("travel_time", "").strip()

    if not received_by or condition not in ("complete", "partial", "damaged"):
        flash("Received By and Condition are required.", "error")
        return redirect(url_for("pswdo.distribution_detail", distribution_id=distribution_id))

    rec.received_by = received_by
    rec.condition = condition
    rec.travel_time = travel_time or None
    if time_received:
        for fmt in ("%H:%M", "%I:%M %p"):
            try:
                rec.time_received = datetime.strptime(time_received, fmt).time()
                break
            except ValueError:
                continue

    saved_names = []
    files = request.files.getlist("proof_files")
    if files and any(f.filename for f in files):
        upload_dir = os.path.join(current_app.root_path, "static", "uploads", "distributions", str(rec.distribution_id))
        os.makedirs(upload_dir, exist_ok=True)
        for f in files:
            if not f.filename:
                continue
            ext = f.filename.rsplit(".", 1)[-1].lower() if "." in f.filename else ""
            if ext not in ALLOWED_PROOF_EXTENSIONS:
                continue
            safe_name = secure_filename(f.filename)
            f.save(os.path.join(upload_dir, safe_name))
            saved_names.append(safe_name)

    if saved_names:
        rec.validation_file = ",".join(saved_names)
        rec.validation_type = "photo"

    rec.dispatch_status = "delivered"
    rec.status = "confirmed"
    rec.submitted_by = current_user.user_id

    db.session.add(ActivityLog(
        actor_id=current_user.user_id,
        action_type="distribution_delivered",
        description=f"D-{rec.distribution_date.year}-{rec.distribution_id:03d} delivered to {rec.barangay.city_municipality}, received by {received_by}",
        office_id=rec.allocation.fulfilling_office_id,
        barangay_id=rec.barangay_id,
    ))
    db.session.commit()
    flash("Delivery confirmed.", "success")
    return redirect(url_for("pswdo.distribution_detail", distribution_id=distribution_id))


@pswdo_bp.route("/distribution/completed")
@login_required
@role_required("pswdo_admin", "system_admin")
def completed_deliveries():
    primary_event = DisasterEvent.query.filter_by(status="active").order_by(
        DisasterEvent.start_date.desc()
    ).first()

    delivered = DistributionRecord.query.join(Barangay).filter(
        Barangay.city_municipality.in_(TARGET_LGUS),
        DistributionRecord.dispatch_status == "delivered"
    ).order_by(DistributionRecord.distribution_date.desc()).all()

    total_delivered = len(delivered)
    packs_delivered = sum(d.quantity_released for d in delivered)
    municipalities_served = len({d.barangay.city_municipality for d in delivered})

    return render_template(
        "pswdo/completed_deliveries.html",
        primary_event=primary_event,
        delivered=delivered,
        total_delivered=total_delivered,
        packs_delivered=packs_delivered,
        municipalities_served=municipalities_served,
    )