# CSWDO/MSWDO pages: barangay reports, deliveries, stock requests, municipal inventory.

import csv
import io
import json
import os
import shutil
import zipfile
from datetime import datetime

from app.utils.timezone import ph_now, ph_today

from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, Response, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from app.extensions import db
from app.utils.decorators import role_required
from app.models.barangay import Barangay
from app.models.warehouse import WarehouseInventory
from app.models.allocation import AllocationRecord
from app.models.validation import DistributionRecord
from app.utils.filters import date_range, in_range, iso
from app.models.disaster_event import DisasterEvent, event_categories_from_form
from app.models.event_barangay import EventBarangay
from app.models.barangay_status import BarangayDisasterStatus
from app.utils.disaster_events import (
    resolve_effective_event, event_covers_barangay,
    blocking_event_for_municipality, blocking_event_for_province,
    relevant_active_events_query,
)
from app.utils import weather as weather_service
from app.models.barangay_report import BarangayReport
from app.models.barangay_inventory import food_pack_on_hand
from app.models.relief_request_batch import ReliefRequestBatch
from app.models.activity_log import ActivityLog
from app.models.user import User
from app.ml import predict as ml_predict

from app.routes.pswdo import (
    DISPATCH_STATUS_LABELS,
    ROUTE_PROGRESS_BY_STATUS, DISPATCH_STEPS, STEP_LABELS,
    NOTIFICATION_META, DEFAULT_NOTIFICATION_META,
    _item_status, _food_pack_health,
    _lgu_burn_rate, _recent_stock_movements, _movement_filters, _inventory_row_filters,
    _gis_scope_lgus, _gis_config,
    _parse_stock_source, _slugify, _full_stock_movements,
    _shelf_status, _sync_food_pack_batches, NEAR_EXPIRY_DAYS,
    _create_food_pack_batch, _deduct_food_pack_batches, _batch_picks_from_form, _lots_from_json, _refreshed_batch_items,
    _parse_food_pack_contents, _parse_item_expiration, _parse_expiration_date, _plan_expiration,
)
from app.models.warehouse import WarehouseStockLog
from app.models.food_pack_batch import FoodPackBatch, FoodPackBatchItem, FoodPackComponent

CSWDO_STOCK_SOURCES = ("standard", "donation", "dswd", "municipal")


# Link to a stock request's 'Tracking' tab on the Stock Requests page.
def _cswdo_batch_tracking_link(batch_id):
    if not batch_id:
        return None
    return url_for("cswdo.relief_requests", tab="tracking", batch_id=batch_id)


# Where clicking an allocation notification goes
# (the stock request, the delivery, or the Stock Requests page).
def _cswdo_allocation_link(log):
    if log.batch_id:
        return _cswdo_batch_tracking_link(log.batch_id)
    allocation = AllocationRecord.query.get(log.allocation_id) if log.allocation_id else None
    if allocation and allocation.batch_id:
        return _cswdo_batch_tracking_link(allocation.batch_id)
    if allocation and allocation.distribution_records:
        return url_for("cswdo.delivery_detail", distribution_id=allocation.distribution_records[0].distribution_id)
    return url_for("cswdo.relief_requests")


# Where clicking a delivery notification goes (the delivery or its stock request).
def _cswdo_distribution_link(log):
    distribution = DistributionRecord.query.get(log.distribution_id) if log.distribution_id else None
    if distribution and distribution.allocation and distribution.allocation.source == "barangay_request":
        return url_for("cswdo.delivery_detail", distribution_id=distribution.distribution_id)
    batch_id = distribution.allocation.batch_id if distribution and distribution.allocation else None
    return _cswdo_batch_tracking_link(batch_id) or url_for("cswdo.dashboard")


# Where clicking an 'approved barangay relief' notification goes (the delivery, if scheduled).
def _cswdo_barangay_relief_link(log):
    alloc = AllocationRecord.query.get(log.allocation_id) if log.allocation_id else None
    if alloc and alloc.distribution_records:
        return url_for("cswdo.delivery_detail", distribution_id=alloc.distribution_records[0].distribution_id)
    return url_for("cswdo.damage_assessment")


CSWDO_NOTIFICATION_LINK_BUILDERS = {
    "allocation_approved": _cswdo_allocation_link,
    "allocation_rejected": _cswdo_allocation_link,
    "cswdo_proactive_allocation": _cswdo_allocation_link,
    "barangay_relief_approved": _cswdo_barangay_relief_link,
    "barangay_relief_declined": lambda log: url_for("cswdo.damage_assessment", tab="declined"),
    "relief_request_submitted": lambda log: _cswdo_batch_tracking_link(log.batch_id) or url_for("cswdo.relief_requests"),
    "distribution_status": _cswdo_distribution_link,
    "distribution_delivered": _cswdo_distribution_link,
    "distribution_receipt_confirmed": _cswdo_distribution_link,
}

CSWDO_NOTIFICATION_CATEGORIES = [
    {"value": "all", "label": "All"},
    {"value": "barangay_reports", "label": "Barangay Reports"},
    {"value": "relief_requests", "label": "Stock Requests"},
    {"value": "distribution", "label": "Deliveries"},
]

ALLOWED_UPLOAD_EXTENSIONS = {"pdf", "jpg", "jpeg", "png", "zip", "doc", "docx"}

RR_STATUS_LABELS = {
    "draft": "Draft",
    "pending": "Under Review",
    "approved": "Approved",
    "partially_approved": "Partially Approved",
    "declined": "Declined",
    "fulfilled": "Fulfilled",
}

RR_PRIORITY_LABELS = {"high": "High", "medium": "Medium", "low": "Low"}

cswdo_bp = Blueprint("cswdo", __name__)

DAMAGE_STATUS_LABELS = {
    "pending": "Pending Review",
    "returned": "Returned",
    "verified": "Verified",
    "approved": "Approved",
    "declined": "Declined",
    "fulfilled": "Fulfilled",
    "no_report": "No Report",
}


# The logged-in user's municipality and its list of barangays.
def _own_lgu_barangays():
    office = current_user.office
    lgu = office.area_covered if office else None
    barangays = Barangay.query.filter_by(city_municipality=lgu).order_by(Barangay.barangay_name).all() if lgu else []
    return lgu, barangays


# If the search box has an exact barangay name (e.g. 'Brgy. Anonas'),
# the page filters by that barangay instead of doing a text search.
def _search_as_barangay(lgu_barangays):
    q = request.args.get("q", "").strip().lower()
    if not q or request.args.get("barangay_id"):
        return None
    for prefix in ("brgy. ", "brgy ", "barangay "):
        if q.startswith(prefix):
            q = q[len(prefix):].strip()
    match = [b for b in lgu_barangays if b.barangay_name.lower() == q]
    if len(match) != 1:
        return None
    args = request.args.to_dict()
    args.pop("q")
    args["barangay_id"] = match[0].barangay_id
    return redirect(url_for(request.endpoint, **args))


# Blocks opening a barangay report from another municipality.
def _assert_own_lgu(report):
    office = current_user.office
    lgu = office.area_covered if office else None
    if not lgu or report.barangay.city_municipality != lgu:
        abort(403)


# Limits notifications to the user's own office and its barangays.
def _own_activity_filters():
    office = current_user.office
    lgu = office.area_covered if office else None
    filters = []
    if office:
        filters.append(ActivityLog.office_id == office.office_id)
    if lgu:
        barangay_ids = [b.barangay_id for b in Barangay.query.filter_by(city_municipality=lgu).all()]
        if barangay_ids:
            filters.append(ActivityLog.barangay_id.in_(barangay_ids))
    return filters


# Blocks opening a notification that belongs to another municipality.
def _assert_own_activity(log):
    office = current_user.office
    lgu = office.area_covered if office else None
    owns_by_office = office and log.office_id == office.office_id
    owns_by_barangay = log.barangay and lgu and log.barangay.city_municipality == lgu
    if not (owns_by_office or owns_by_barangay):
        abort(403)


# Gets one notification ready for display: icon, color, category and link.
def _cswdo_notification_view(log):
    meta = NOTIFICATION_META.get(log.action_type, DEFAULT_NOTIFICATION_META)
    link_fn = CSWDO_NOTIFICATION_LINK_BUILDERS.get(log.action_type)
    return {
        "log": log,
        "icon": meta["icon"],
        "color": meta["color"],
        "category": meta["category"],
        "category_label": meta["category_label"],
        "link": link_fn(log) if link_fn else None,
    }


# Action: /cswdo/disaster-events/declare - Declares a local disaster event for the municipality,
# covering all of its barangays or only the ones ticked. Blocked if an event is already active.
@cswdo_bp.route("/disaster-events/declare", methods=["POST"])
@login_required
@role_required("cswdo_admin", "system_admin")
def declare_disaster_event():
    office = current_user.office
    lgu, lgu_barangays = _own_lgu_barangays()
    if not lgu:
        flash("No office/municipality on file for this account.", "error")
        return redirect(url_for("cswdo.dashboard"))

    existing = blocking_event_for_municipality(lgu)
    if existing:
        flash(f"“{existing.event_name}” is already active for {lgu}. End it before declaring a new event.", "error")
        return redirect(url_for("cswdo.dashboard"))

    event_name = request.form.get("event_name", "").strip()
    if not event_name:
        flash("Event name is required to declare a disaster event.", "error")
        return redirect(url_for("cswdo.dashboard"))

    start_date_raw = request.form.get("start_date", "")
    try:
        start_date = datetime.strptime(start_date_raw, "%Y-%m-%d").date() if start_date_raw else ph_today()
    except ValueError:
        start_date = ph_today()

    weather_condition = event_categories_from_form(request.form)

    selected_ids = set(request.form.getlist("barangay_ids", type=int))
    own_barangay_ids = {b.barangay_id for b in lgu_barangays}
    covered_ids = selected_ids & own_barangay_ids

    event = DisasterEvent(
        event_name=event_name, event_type="typhoon", status="active",
        weather_condition=weather_condition, start_date=start_date,
        created_by=current_user.user_id,
        scope="municipality", city_municipality=lgu,
    )
    db.session.add(event)
    db.session.flush()
    for barangay_id in covered_ids:
        db.session.add(EventBarangay(event_id=event.event_id, barangay_id=barangay_id))
    db.session.add(ActivityLog(
        actor_id=current_user.user_id, office_id=office.office_id if office else None,
        action_type="disaster_event_declared",
        description=f"Declared {event_name} as {lgu}'s active local disaster event ({len(covered_ids)} of {len(own_barangay_ids)} barangays).",
    ))
    db.session.commit()

    flash(f"{event_name} has been declared as {lgu}'s active local disaster event.", "success")
    return redirect(url_for("cswdo.dashboard"))


# Action: /cswdo/disaster-events/<int:event_id>/end - Ends the municipality's own local disaster event and records the end date.
@cswdo_bp.route("/disaster-events/<int:event_id>/end", methods=["POST"])
@login_required
@role_required("cswdo_admin", "system_admin")
def end_disaster_event(event_id):
    office = current_user.office
    lgu = office.area_covered if office else None
    event = DisasterEvent.query.get_or_404(event_id)
    if event.scope != "municipality" or event.city_municipality != lgu:
        abort(403)
    if event.status != "active":
        flash(f"{event.event_name} is not currently active.", "error")
        return redirect(url_for("cswdo.dashboard"))

    event.status = "ended"
    event.end_date = ph_today()
    db.session.add(ActivityLog(
        actor_id=current_user.user_id, office_id=office.office_id if office else None,
        action_type="disaster_event_ended",
        description=f"Marked {event.event_name} as ended.",
    ))
    db.session.commit()

    flash(f"{event.event_name} has been marked as ended.", "success")
    return redirect(url_for("cswdo.dashboard"))


# Page: /cswdo/dashboard - CSWDO/MSWDO main dashboard: the active event, barangay reports waiting for review,
# warehouse stock, deliveries, recent activity and weather for the municipality.
@cswdo_bp.route("/dashboard")
@login_required
@role_required("cswdo_admin", "system_admin")
def dashboard():
    now = ph_now()
    office = current_user.office
    lgu = office.area_covered if office else None

    primary_event, applicable_barangay_ids = resolve_effective_event(lgu)
    own_local_event = primary_event if primary_event and primary_event.scope == "municipality" else None
    province_event = blocking_event_for_province() if own_local_event else None

    lgu_barangays = Barangay.query.filter_by(city_municipality=lgu).all() if lgu else []
    lgu_barangay_ids = [b.barangay_id for b in lgu_barangays]
    total_barangays = len(lgu_barangays)
    event_barangay_ids = ([b for b in lgu_barangay_ids if event_covers_barangay(applicable_barangay_ids, b)]
                           if primary_event else lgu_barangay_ids)

    affected_barangays_count = 0
    total_affected_families = 0
    if primary_event and event_barangay_ids:
        event_reports = BarangayReport.query.filter(
            BarangayReport.event_id == primary_event.event_id,
            BarangayReport.barangay_id.in_(event_barangay_ids),
            BarangayReport.status.notin_(("draft", "declined")),
        ).all()
        affected_barangays_count = len({r.barangay_id for r in event_reports})
        total_affected_families = sum((r.affected_families or 0) for r in event_reports)

    food_pack_item = None
    other_items = []
    if office:
        food_pack_item = WarehouseInventory.query.filter_by(
            office_id=office.office_id, item_type="food_pack"
        ).first()
        raw_other_items = WarehouseInventory.query.filter(
            WarehouseInventory.office_id == office.office_id,
            WarehouseInventory.item_type != "food_pack",
        ).order_by(WarehouseInventory.item_name).all()
        other_items = [
            {
                "item": item,
                "pct": min(round((item.quantity_available / item.min_stock_level) * 100), 100) if item.min_stock_level else 100,
                "status": _item_status(item.quantity_available, item.min_stock_level),
            }
            for item in raw_other_items
        ]

    food_pack_qty = food_pack_item.quantity_available if food_pack_item else 0
    capacity = (office.capacity_food_pack or 20000) if office else 20000
    stock_pct = round((food_pack_qty / capacity) * 100, 0) if capacity > 0 else 0
    stock_health = _food_pack_health(food_pack_qty, capacity)

    pending_requests_count = 0
    if office:
        pending_requests_count = ReliefRequestBatch.query.filter(
            ReliefRequestBatch.office_id == office.office_id,
            ReliefRequestBatch.status == "pending",
        ).count()

    incoming_distributions = []
    if lgu_barangay_ids:
        incoming_distributions = DistributionRecord.query.filter(
            DistributionRecord.barangay_id.in_(lgu_barangay_ids),
            DistributionRecord.dispatch_status.in_(["preparing", "loaded", "dispatched", "in_transit"]),
        ).order_by(DistributionRecord.distribution_date.desc()).all()
    incoming_deliveries_count = len(incoming_distributions)
    next_delivery = incoming_distributions[0] if incoming_distributions else None

    pending_barangay_reports_count = 0
    if lgu_barangay_ids:
        pending_barangay_reports_count = BarangayReport.query.filter(
            BarangayReport.barangay_id.in_(lgu_barangay_ids),
            BarangayReport.status == "pending",
        ).count()

    _STATUS_TAB = {
        "pending": "queue", "returned": "queue", "verified": "verified",
        "approved": "approved", "fulfilled": "fulfilled", "declined": "declined",
    }
    relief_request_rows = []
    if lgu_barangay_ids:
        reports_q = BarangayReport.query.filter(
            BarangayReport.barangay_id.in_(lgu_barangay_ids),
            BarangayReport.status != "draft",
        ).order_by(BarangayReport.submitted_at.desc()).limit(3).all()
        for rep in reports_q:
            alloc = rep.allocation
            active_distribution = None
            if alloc:
                active_distribution = next(
                    (d for d in alloc.distribution_records if d.dispatch_status != "delivered"), None
                )
            relief_request_rows.append({
                "report": rep,
                "record": alloc,
                "ref": rep.ref,
                "status": rep.status,
                "tab": _STATUS_TAB.get(rep.status, "all"),
                "barangay": rep.barangay,
                "model_estimate": ml_predict.predict_quantity(rep.barangay) or 0,
                "active_distribution": active_distribution,
                "progress_pct": ROUTE_PROGRESS_BY_STATUS.get(active_distribution.dispatch_status, 0) if active_distribution else None,
            })

    activity_filters = _own_activity_filters()

    recent_activities = []
    if activity_filters:
        known_types = list(NOTIFICATION_META.keys())
        scoped_query = ActivityLog.query.filter(
            db.or_(*activity_filters), ActivityLog.action_type.in_(known_types)
        )
        recent_activities = scoped_query.order_by(ActivityLog.created_at.desc()).limit(4).all()

    return render_template(
        "cswdo/dashboard.html",
        now=now,
        office=office,
        lgu=lgu,
        primary_event=primary_event,
        own_local_event=own_local_event,
        province_event=province_event,
        lgu_barangays=lgu_barangays,
        total_barangays=total_barangays,
        affected_barangays_count=affected_barangays_count,
        total_affected_families=total_affected_families,
        food_pack_qty=food_pack_qty,
        capacity=capacity,
        stock_pct=stock_pct,
        stock_health=stock_health,
        other_items=other_items,
        pending_requests_count=pending_requests_count,
        incoming_deliveries_count=incoming_deliveries_count,
        next_delivery=next_delivery,
        pending_barangay_reports_count=pending_barangay_reports_count,
        relief_request_rows=relief_request_rows,
        recent_activities=recent_activities,
        status_labels=DAMAGE_STATUS_LABELS,
        dispatch_status_labels=DISPATCH_STATUS_LABELS,
        weather_cities=[lgu] if lgu else [],
    )


# Page: /cswdo/dashboard/weather - Sends the weather data for the municipality's dashboard widget.
@cswdo_bp.route("/dashboard/weather")
@login_required
@role_required("cswdo_admin", "system_admin")
def dashboard_weather():
    office = current_user.office
    lgu = office.area_covered if office else None
    return weather_service.get_dashboard_snapshot([lgu] if lgu else [])


# Page: /cswdo/gis-map - GIS Map page for the municipality's own barangays.
@cswdo_bp.route("/gis-map")
@login_required
@role_required("cswdo_admin", "system_admin")
def gis_map():
    scope_lgus = _gis_scope_lgus()
    active_events = relevant_active_events_query(scope_lgus).all()
    barangay_options = (
        Barangay.query.filter(Barangay.city_municipality.in_(scope_lgus))
        .order_by(Barangay.barangay_name).all()
        if scope_lgus else []
    )
    return render_template(
        "cswdo/gis_map.html",
        active_events=active_events,
        target_lgus=scope_lgus,
        barangay_options=barangay_options,
        gis_config=_gis_config(),
    )


# Page: /cswdo/barangay-distributions - Barangay Distributions page: what each barangay handed out to its families,
# with proof photos, filterable by barangay.
@cswdo_bp.route("/barangay-distributions")
@login_required
@role_required("cswdo_admin", "system_admin")
def barangay_distribution_history():
    from app.models.barangay_inventory import BarangayStockLog

    scope_lgus = _gis_scope_lgus()
    barangay_options = (
        Barangay.query.filter(Barangay.city_municipality.in_(scope_lgus))
        .order_by(Barangay.barangay_name).all()
        if scope_lgus else []
    )
    barangay_id = request.args.get("barangay_id", type=int)
    barangay = next((b for b in barangay_options if b.barangay_id == barangay_id), None)
    if barangay_id and not barangay:
        abort(404)

    proof_filter = request.args.get("proof", "all")
    date_from, date_to = date_range(request.args)
    logs = []
    if barangay:
        q = BarangayStockLog.query.filter_by(barangay_id=barangay.barangay_id, source_type="distribution")
        if proof_filter == "with":
            q = q.filter(BarangayStockLog.proof_photos.isnot(None))
        elif proof_filter == "without":
            q = q.filter(BarangayStockLog.proof_photos.is_(None))
        if date_from:
            q = q.filter(db.func.date(BarangayStockLog.created_at) >= date_from)
        if date_to:
            q = q.filter(db.func.date(BarangayStockLog.created_at) <= date_to)
        logs = q.order_by(BarangayStockLog.created_at.desc(), BarangayStockLog.log_id.desc()).all()

    return render_template(
        "cswdo/barangay_distributions.html",
        barangay=barangay, barangay_options=barangay_options, logs=logs,
        total_packs=sum(-l.delta for l in logs),
        with_proof=sum(1 for l in logs if l.proof_photo_list),
        families_reached=len({l.family_id for l in logs if l.family_id}),
        on_hand=food_pack_on_hand(barangay.barangay_id) if barangay else None,
        proof_filter=proof_filter, date_from=iso(date_from), date_to=iso(date_to),
    )


# The municipal warehouse's own food pack stock record.
def _own_food_pack_inventory():
    office = current_user.office
    if not office:
        return None
    return WarehouseInventory.query.filter_by(
        office_id=office.office_id, item_type="food_pack"
    ).first()


# Gets a barangay report ready for review: forecast estimate, the barangay's own stock,
# and a suggested number of food packs to allocate.
def _relief_request_row(report):
    model_estimate = ml_predict.predict_quantity(report.barangay) or 0
    on_hand = food_pack_on_hand(report.barangay_id)
    suggested = max(model_estimate - (on_hand or 0), 0)
    requested = report.requested_food_packs or 0
    return {
        "report": report,
        "barangay": report.barangay,
        "model_estimate": model_estimate,
        "barangay_on_hand": on_hand,
        "suggested_allocation": suggested,
        "requested": requested,
        "prefill_quantity": requested or suggested or model_estimate,
        "allocation": report.allocation,
    }


# Page: /cswdo/damage-assessment - Barangay Reports page: review situation reports from the municipality's barangays.
# For each one you can verify it, allocate food packs, return it for correction, or decline it.
@cswdo_bp.route("/damage-assessment")
@login_required
@role_required("cswdo_admin", "system_admin")
def damage_assessment():
    lgu, lgu_barangays = _own_lgu_barangays()
    as_barangay = _search_as_barangay(lgu_barangays)
    if as_barangay:
        return as_barangay
    office = current_user.office
    tab = request.args.get("tab", "queue")
    search_query = request.args.get("q", "").strip().lower()

    primary_event, _ = resolve_effective_event(lgu)

    barangay_ids = [b.barangay_id for b in lgu_barangays]
    reports = []
    if barangay_ids:
        reports = BarangayReport.query.filter(
            BarangayReport.barangay_id.in_(barangay_ids),
            BarangayReport.status != "draft",
        ).order_by(BarangayReport.submitted_at.desc()).all()

    rows = [_relief_request_row(r) for r in reports]
    if search_query:
        rows = [
            r for r in rows
            if search_query in r["barangay"].barangay_name.lower()
            or search_query in r["report"].ref.lower()
        ]
    barangay_filter = request.args.get("barangay_id", type=int)
    event_filter = request.args.get("event_id", type=int)
    date_from, date_to = date_range(request.args)
    if barangay_filter:
        rows = [r for r in rows if r["barangay"].barangay_id == barangay_filter]
    if event_filter:
        rows = [r for r in rows if r["report"].event_id == event_filter]
    rows = [r for r in rows if in_range(r["report"].submitted_at, date_from, date_to)]

    pending_rows = [r for r in rows if r["report"].status in ("pending", "returned")]
    verified_rows = [r for r in rows if r["report"].status == "verified"]
    approved_rows = [r for r in rows if r["report"].status == "approved"]
    fulfilled_rows = [r for r in rows if r["report"].status == "fulfilled"]
    declined_rows = [r for r in rows if r["report"].status == "declined"]

    fp = _own_food_pack_inventory()
    on_hand = fp.quantity_available if fp else 0

    suggested_pending = sum(r["suggested_allocation"] for r in pending_rows)
    approved_packs = sum(
        (r["allocation"].allocated_quantity if r["allocation"] else 0)
        for r in approved_rows + fulfilled_rows
    )

    return render_template(
        "cswdo/damage_assessment.html",
        tab=tab, now=ph_now(), lgu=lgu, office=office,
        primary_event=primary_event,
        rows=rows, pending_rows=pending_rows, verified_rows=verified_rows,
        approved_rows=approved_rows,
        fulfilled_rows=fulfilled_rows, declined_rows=declined_rows,
        on_hand=on_hand, suggested_pending=suggested_pending, approved_packs=approved_packs,
        total_barangays=len(lgu_barangays),
        status_labels=DAMAGE_STATUS_LABELS,
        dispatch_labels=DISPATCH_STATUS_LABELS,
        search_query=search_query,
        barangay_filter=barangay_filter, event_filter=event_filter,
        date_from=iso(date_from), date_to=iso(date_to), lgu_barangays=lgu_barangays,
        filter_events=sorted({r.event for r in reports if r.event}, key=lambda e: e.start_date, reverse=True),
        filtered_barangay=next((b for b in lgu_barangays if b.barangay_id == barangay_filter), None),
        reported_barangay_ids={r.barangay_id for r in reports},
    )


# Allocates food packs to a barangay from its report:
# takes them out of the municipal warehouse and schedules the delivery.
def _fulfil_barangay_request(report, quantity, office, picks=None):
    fp = _own_food_pack_inventory()
    available = fp.quantity_available if fp else 0
    if quantity > available:
        return None, (
            f"{office.office_name} only has {available:,} food packs on hand - "
            f"request a stock replenishment from PSWDO or approve a smaller quantity."
        )

    alloc = AllocationRecord(
        barangay_id=report.barangay_id, office_id=office.office_id,
        predicted_quantity=quantity,
        allocated_quantity=quantity,
        historical_allocation=ml_predict.historical_allocation_for(report.barangay_id),
        allocation_date=ph_today(), event_id=report.event_id,
        status="approved", fulfilling_office_id=office.office_id,
        source="barangay_request", barangay_report_id=report.report_id,
        created_by=current_user.user_id, decided_by=current_user.user_id,
    )
    db.session.add(alloc)
    db.session.flush()

    dist = DistributionRecord(
        barangay_id=report.barangay_id, allocation_id=alloc.allocation_id,
        quantity_released=quantity, distribution_date=ph_today(),
        dispatch_status="preparing", submitted_by=current_user.user_id,
        batch_lots=_deduct_food_pack_batches(office.office_id, quantity, picks),
    )
    db.session.add(dist)

    # Take the allocated packs out of the municipal warehouse.
    fp.quantity_available -= quantity
    fp.updated_by = current_user.user_id
    db.session.add(WarehouseStockLog(
        office_id=office.office_id, item_type="food_pack", item_name="Food Packs",
        delta=-quantity, reason=f"Released to Brgy. {report.barangay.barangay_name} ({report.ref})",
        source_type="standard", updated_by=current_user.user_id,
    ))
    db.session.flush()
    return alloc, None


# Sends food packs to a barangay before it asks (pre-positioning):
# takes them out of the municipal warehouse and schedules the delivery.
def _push_proactive_allocation(barangay, quantity, office, event, remarks, picks=None):
    fp = _own_food_pack_inventory()
    available = fp.quantity_available if fp else 0
    if quantity > available:
        return None, (
            f"{office.office_name} only has {available:,} food packs on hand - "
            f"request a stock replenishment from PSWDO or allocate a smaller quantity."
        )

    alloc = AllocationRecord(
        barangay_id=barangay.barangay_id, office_id=office.office_id,
        predicted_quantity=ml_predict.predict_quantity(barangay) or 0,
        allocated_quantity=quantity,
        historical_allocation=ml_predict.historical_allocation_for(barangay.barangay_id),
        allocation_date=ph_today(), event_id=event.event_id if event else None,
        status="approved", fulfilling_office_id=office.office_id,
        source="cswdo_direct", barangay_report_id=None,
        created_by=current_user.user_id, decided_by=current_user.user_id,
        remarks=remarks or None,
    )
    db.session.add(alloc)
    db.session.flush()

    dist = DistributionRecord(
        barangay_id=barangay.barangay_id, allocation_id=alloc.allocation_id,
        quantity_released=quantity, distribution_date=ph_today(),
        dispatch_status="preparing", submitted_by=current_user.user_id,
        batch_lots=_deduct_food_pack_batches(office.office_id, quantity, picks),
    )
    db.session.add(dist)

    # Take the packs out of the municipal warehouse.
    fp.quantity_available -= quantity
    fp.updated_by = current_user.user_id
    event_note = f" ({event.event_name})" if event else ""
    db.session.add(WarehouseStockLog(
        office_id=office.office_id, item_type="food_pack", item_name="Food Packs",
        delta=-quantity,
        reason=f"Proactively allocated to Brgy. {barangay.barangay_name}{event_note}",
        source_type="standard", updated_by=current_user.user_id,
    ))
    db.session.flush()
    return alloc, None


# Action: /cswdo/proactive-allocate - Form action for pre-positioning food packs to a barangay
# (from the Predictive Analytics or Deliveries page).
@cswdo_bp.route("/proactive-allocate", methods=["POST"])
@login_required
@role_required("cswdo_admin", "system_admin")
def proactive_allocate():
    next_page = "cswdo.deliveries" if request.form.get("next") == "deliveries" else "prediction.index"

    # Goes back to the page the user came from.
    def _redirect(event_id=None):
        if next_page == "cswdo.deliveries":
            return redirect(url_for(next_page))
        return redirect(url_for(next_page, event_id=event_id))

    office = current_user.office
    if not office:
        flash("No office on file for this account.", "error")
        return _redirect()

    barangay_id = request.form.get("barangay_id", type=int)
    barangay = Barangay.query.get(barangay_id) if barangay_id else None
    if not barangay or barangay.city_municipality != office.area_covered:
        flash("Select a barangay in your own LGU.", "error")
        return _redirect()

    event_id = request.form.get("event_id", type=int)
    event = DisasterEvent.query.get(event_id) if event_id else None
    if event_id and (not event or event.status != "active"):
        flash("That disaster event is no longer active - reselect one or leave it blank to allocate without an event.", "error")
        return _redirect()

    quantity = request.form.get("quantity", type=int)
    if not quantity or quantity <= 0:
        flash("Enter the number of food packs to allocate.", "error")
        return _redirect(event_id)

    remarks = request.form.get("remarks", "").strip()
    if not remarks:
        flash("Add a short justification for this proactive allocation (no barangay request backs it, so this is the record of why).", "error")
        return _redirect(event_id)

    picks, error = _batch_picks_from_form(office.office_id, quantity)
    if error:
        flash(error, "error")
        return _redirect(event_id)

    alloc, error = _push_proactive_allocation(barangay, quantity, office, event, remarks, picks)
    if error:
        flash(error, "error")
        return _redirect(event_id)

    event_note = f" ({event.event_name})" if event else " (no event - routine restocking)"
    db.session.add(ActivityLog(
        actor_id=current_user.user_id, action_type="cswdo_proactive_allocation",
        description=f"{office.office_name} proactively allocated {quantity:,} food packs to "
                    f"Brgy. {barangay.barangay_name}{event_note} - model estimate was "
                    f"{alloc.predicted_quantity:,}",
        office_id=office.office_id, barangay_id=barangay.barangay_id,
        allocation_id=alloc.allocation_id,
    ))
    db.session.commit()
    flash(f"{quantity:,} food packs proactively allocated to Brgy. {barangay.barangay_name}.", "success")
    return _redirect(event_id)


# Updates the barangay's disaster status from its report
# (flood level and affected families), so the map shows the latest situation.
def _sync_barangay_disaster_status(report):
    if not report.event_id:
        return
    status_row = BarangayDisasterStatus.query.filter_by(
        barangay_id=report.barangay_id, event_id=report.event_id
    ).first()
    if status_row:
        status_row.status = report.flood_level
        status_row.affected_families = report.affected_families
        status_row.updated_by = current_user.user_id
    else:
        db.session.add(BarangayDisasterStatus(
            barangay_id=report.barangay_id, event_id=report.event_id,
            status=report.flood_level, affected_families=report.affected_families,
            updated_by=current_user.user_id,
        ))


# Action: /cswdo/damage-assessment/<int:report_id>/verify - Marks a barangay report as verified (checked and accepted) without sending food packs.
@cswdo_bp.route("/damage-assessment/<int:report_id>/verify", methods=["POST"])
@login_required
@role_required("cswdo_admin", "system_admin")
def verify_relief_request(report_id):
    report = BarangayReport.query.get_or_404(report_id)
    _assert_own_lgu(report)
    office = current_user.office

    if report.status not in ("pending", "returned"):
        flash("This report has already been decided.", "error")
        return redirect(url_for("cswdo.damage_assessment"))

    report.status = "verified"
    report.review_remarks = request.form.get("review_remarks", "").strip() or None
    report.reviewed_by = current_user.user_id
    report.reviewed_at = ph_now()
    _sync_barangay_disaster_status(report)

    on_hand = food_pack_on_hand(report.barangay_id)
    db.session.add(ActivityLog(
        actor_id=current_user.user_id, action_type="barangay_report_verified",
        description=f"{office.office_name if office else 'MSWDO'} verified {report.ref} "
                    f"(Brgy. {report.barangay.barangay_name}) - no allocation"
                    + (f", barangay stock {on_hand:,} packs on hand" if on_hand is not None else ""),
        office_id=office.office_id if office else None, barangay_id=report.barangay_id,
    ))
    db.session.commit()
    flash(f"{report.ref} verified - no allocation. The barangay has been notified.", "success")
    return redirect(url_for("cswdo.damage_assessment"))


# Action: /cswdo/damage-assessment/<int:report_id>/approve - Approves a barangay report and allocates food packs to that barangay.
# The municipal warehouse must have enough stock.
@cswdo_bp.route("/damage-assessment/<int:report_id>/approve", methods=["POST"])
@login_required
@role_required("cswdo_admin", "system_admin")
def approve_relief_request(report_id):
    report = BarangayReport.query.get_or_404(report_id)
    _assert_own_lgu(report)
    office = current_user.office

    if report.status not in ("pending", "returned"):
        flash("This relief request has already been decided.", "error")
        return redirect(url_for("cswdo.damage_assessment"))

    quantity = request.form.get("quantity", type=int)
    if not quantity or quantity <= 0:
        flash("Enter the number of food packs to allocate.", "error")
        return redirect(url_for("cswdo.damage_assessment"))

    picks, error = _batch_picks_from_form(office.office_id, quantity)
    if error:
        flash(error, "error")
        return redirect(url_for("cswdo.damage_assessment"))

    alloc, error = _fulfil_barangay_request(report, quantity, office, picks)
    if error:
        db.session.rollback()
        flash(error, "error")
        return redirect(url_for("cswdo.damage_assessment"))

    report.status = "approved"
    report.review_remarks = request.form.get("review_remarks", "").strip() or None
    report.reviewed_by = current_user.user_id
    report.reviewed_at = ph_now()
    _sync_barangay_disaster_status(report)

    db.session.add(ActivityLog(
        actor_id=current_user.user_id, action_type="barangay_relief_approved",
        description=f"{office.office_name} approved {quantity:,} food packs for Brgy. "
                    f"{report.barangay.barangay_name} ({report.ref}) - delivery scheduled",
        office_id=office.office_id, barangay_id=report.barangay_id,
        allocation_id=alloc.allocation_id,
    ))
    db.session.commit()
    flash(f"{report.ref} approved - {quantity:,} food packs, delivery to Brgy. "
          f"{report.barangay.barangay_name} is now preparing.", "success")
    return redirect(url_for("cswdo.delivery_detail", distribution_id=alloc.distribution_records[0].distribution_id))


# Action: /cswdo/damage-assessment/<int:report_id>/decline - Declines a barangay report. A remark is required so the barangay knows why.
@cswdo_bp.route("/damage-assessment/<int:report_id>/decline", methods=["POST"])
@login_required
@role_required("cswdo_admin", "system_admin")
def decline_relief_request(report_id):
    report = BarangayReport.query.get_or_404(report_id)
    _assert_own_lgu(report)
    if report.status not in ("pending", "returned"):
        flash("This relief request has already been decided.", "error")
        return redirect(url_for("cswdo.damage_assessment"))

    reason = (request.form.get("reason", "").strip()
              or request.form.get("review_remarks", "").strip())
    if not reason:
        flash("Add a remark explaining why this relief request is declined.", "error")
        return redirect(url_for("cswdo.damage_assessment"))

    report.status = "declined"
    report.review_remarks = reason
    report.reviewed_by = current_user.user_id
    report.reviewed_at = ph_now()
    office = current_user.office
    db.session.add(ActivityLog(
        actor_id=current_user.user_id, action_type="barangay_relief_declined",
        description=f"{office.office_name if office else 'MSWDO'} declined {report.ref} "
                    f"(Brgy. {report.barangay.barangay_name}) - {reason}",
        office_id=office.office_id if office else None, barangay_id=report.barangay_id,
    ))
    db.session.commit()
    flash(f"{report.ref} declined.", "success")
    return redirect(url_for("cswdo.damage_assessment"))


# Action: /cswdo/damage-assessment/<int:report_id>/return - Sends a report back to the barangay to correct, with a note on what to fix.
@cswdo_bp.route("/damage-assessment/<int:report_id>/return", methods=["POST"])
@login_required
@role_required("cswdo_admin", "system_admin")
def return_damage_report(report_id):
    report = BarangayReport.query.get_or_404(report_id)
    _assert_own_lgu(report)
    remarks = request.form.get("review_remarks", "").strip()
    if not remarks:
        flash("Enter a reason so the barangay knows what to correct.", "error")
        return redirect(url_for("cswdo.damage_assessment"))
    if report.status not in ("pending", "returned"):
        flash("Only a pending relief request can be returned.", "error")
        return redirect(url_for("cswdo.damage_assessment"))

    report.status = "returned"
    report.review_remarks = remarks
    report.reviewed_by = current_user.user_id
    report.reviewed_at = ph_now()
    office = current_user.office
    db.session.add(ActivityLog(
        actor_id=current_user.user_id, action_type="damage_report_returned",
        description=f"{report.ref} was returned by {office.office_name if office else 'MSWDO'} - {remarks}",
        office_id=office.office_id if office else None, barangay_id=report.barangay_id,
    ))
    db.session.commit()
    flash(f"{report.ref} ({report.barangay.barangay_name}) returned for correction.", "success")
    return redirect(url_for("cswdo.damage_assessment"))


# Download: /cswdo/damage-assessment/export - Downloads the barangay reports list as a CSV (spreadsheet) file.
@cswdo_bp.route("/damage-assessment/export")
@login_required
@role_required("cswdo_admin", "system_admin")
def damage_assessment_export():
    lgu, lgu_barangays = _own_lgu_barangays()
    barangay_ids = [b.barangay_id for b in lgu_barangays]
    reports = BarangayReport.query.filter(
        BarangayReport.barangay_id.in_(barangay_ids),
        BarangayReport.status != "draft",
    ).order_by(BarangayReport.submitted_at.desc()).all() if barangay_ids else []

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow([
        "Report ID", "Barangay", "Typhoon Event", "Status", "Submitted By",
        "Affected Families", "Totally Damaged Houses",
        "Allocated Packs", "Last Updated",
    ])
    for rep in reports:
        alloc = rep.allocation
        writer.writerow([
            rep.ref, rep.barangay.barangay_name,
            rep.event.event_name if rep.event else "",
            DAMAGE_STATUS_LABELS.get(rep.status, rep.status),
            rep.submitted_by_name, rep.affected_families, rep.totally_damaged_houses,
            alloc.allocated_quantity if alloc else "",
            (rep.reviewed_at or rep.submitted_at).strftime("%Y-%m-%d %H:%M") if (rep.reviewed_at or rep.submitted_at) else "",
        ])

    return Response(
        buffer.getvalue(), mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={(lgu or 'barangay_reports').replace(' ', '_')}_barangay_reports.csv"},
    )


CSWDO_ADVANCE_TRANSITIONS = {"preparing": "loaded", "dispatched": "in_transit"}


# Finds a delivery, but only if it is in the user's own municipality.
def _own_delivery_or_404(distribution_id):
    rec = DistributionRecord.query.get_or_404(distribution_id)
    lgu = current_user.office.area_covered if current_user.office else None
    if not lgu or rec.barangay.city_municipality != lgu:
        abort(404)
    return rec


# Page: /cswdo/deliveries - Deliveries page: food pack deliveries from the municipal warehouse to its barangays,
# grouped by status (preparing, in transit, awaiting confirmation, delivered).
@cswdo_bp.route("/deliveries")
@login_required
@role_required("cswdo_admin", "system_admin")
def deliveries():
    lgu, lgu_barangays = _own_lgu_barangays()
    as_barangay = _search_as_barangay(lgu_barangays)
    if as_barangay:
        return as_barangay
    status_filter = request.args.get("status", "preparing")
    search_query = request.args.get("q", "").strip().lower()
    barangay_ids = [b.barangay_id for b in lgu_barangays]

    q = DistributionRecord.query.filter(DistributionRecord.barangay_id.in_(barangay_ids)) if barangay_ids else DistributionRecord.query.filter(db.false())
    q = q.join(AllocationRecord).filter(AllocationRecord.source.in_(("barangay_request", "cswdo_direct")))
    all_recs = q.order_by(
        AllocationRecord.allocation_date.desc(),
        AllocationRecord.created_at.desc(),
        AllocationRecord.allocation_id.desc(),
        DistributionRecord.distribution_id.desc(),
    ).all()

    # Counts the deliveries in one status.
    def _counts(status):
        return sum(1 for r in all_recs if r.dispatch_status == status)

    # True if a delivery is on its way or delivered
    # but the barangay hasn't confirmed receiving it yet.
    def _awaiting_validation(r):
        return (r.dispatch_status in ("dispatched", "in_transit", "delivered")
                and r.status != "confirmed")

    barangay_filter = request.args.get("barangay_id", type=int)
    event_filter = request.args.get("event_id", type=int)
    source_filter = request.args.get("source", "all")
    date_from, date_to = date_range(request.args)

    recs = all_recs
    if status_filter != "all":
        recs = [r for r in recs if r.dispatch_status == status_filter]
    if barangay_filter:
        recs = [r for r in recs if r.barangay_id == barangay_filter]
    if event_filter:
        recs = [r for r in recs if r.allocation and r.allocation.event_id == event_filter]
    if source_filter != "all":
        recs = [r for r in recs if r.allocation and r.allocation.source == source_filter]
    recs = [r for r in recs if in_range(r.distribution_date, date_from, date_to)]
    if search_query:
        recs = [r for r in recs if search_query in r.barangay.barangay_name.lower()
                or search_query in f"d-{r.distribution_date.year}-{r.distribution_id:03d}"]

    rows = [{
        "rec": r,
        "ref": f"D-{r.distribution_date.year}-{r.distribution_id:03d}",
        "request_ref": (r.allocation.barangay_report.ref if r.allocation and r.allocation.barangay_report else None),
        "event": (r.allocation.event.event_name if r.allocation and r.allocation.event else None),
        "progress_pct": ROUTE_PROGRESS_BY_STATUS.get(r.dispatch_status, 0),
        "awaiting_validation": _awaiting_validation(r),
    } for r in recs]

    fp = _own_food_pack_inventory()
    active_events = relevant_active_events_query([lgu]).all()

    return render_template(
        "cswdo/deliveries.html",
        lgu=lgu, rows=rows, status_filter=status_filter, search_query=search_query,
        dispatch_labels=DISPATCH_STATUS_LABELS,
        total=len(all_recs), preparing_count=_counts("preparing"),
        in_transit_count=sum(1 for r in all_recs if r.dispatch_status in ("dispatched", "in_transit")),
        awaiting_validation_count=sum(1 for r in all_recs if _awaiting_validation(r)),
        validated_count=sum(1 for r in all_recs if r.status == "confirmed"),
        packs_in_transit=sum(r.quantity_released for r in all_recs if r.dispatch_status in ("dispatched", "in_transit")),
        can_allocate=bool(current_user.office),
        lgu_barangays=lgu_barangays,
        active_events=active_events,
        total_food_packs=fp.quantity_available if fp else 0,
        barangay_filter=barangay_filter, event_filter=event_filter, source_filter=source_filter,
        date_from=iso(date_from), date_to=iso(date_to),
        filter_events=sorted({r.allocation.event for r in all_recs if r.allocation and r.allocation.event},
                             key=lambda e: e.start_date, reverse=True),
    )


# Page: /cswdo/deliveries/<int:distribution_id> - One delivery's details and progress steps, plus the warehouse's stock.
@cswdo_bp.route("/deliveries/<int:distribution_id>")
@login_required
@role_required("cswdo_admin", "system_admin")
def delivery_detail(distribution_id):
    rec = _own_delivery_or_404(distribution_id)
    alloc = rec.allocation
    report = alloc.barangay_report if alloc else None
    office = current_user.office
    fp = _own_food_pack_inventory()
    on_hand = fp.quantity_available if fp else 0

    released_since = 0
    if office:
        released_since = db.session.query(
            db.func.coalesce(db.func.sum(DistributionRecord.quantity_released), 0)
        ).select_from(DistributionRecord).join(AllocationRecord).filter(
            AllocationRecord.fulfilling_office_id == office.office_id,
            AllocationRecord.source.in_(("barangay_request", "cswdo_direct")),
            DistributionRecord.distribution_id > rec.distribution_id,
        ).scalar() or 0
    stock_after_release = on_hand + released_since
    stock_before_release = stock_after_release + rec.quantity_released

    current_index = DISPATCH_STEPS.index(rec.dispatch_status) if rec.dispatch_status in DISPATCH_STEPS else 1
    attachments = rec.validation_file.split(",") if rec.validation_file else []
    return render_template(
        "cswdo/delivery_detail.html",
        rec=rec, alloc=alloc, report=report,
        ref=f"D-{rec.distribution_date.year}-{rec.distribution_id:03d}",
        on_hand=on_hand,
        stock_before_release=stock_before_release,
        stock_after_release=stock_after_release,
        dispatch_steps=DISPATCH_STEPS, step_labels=STEP_LABELS,
        current_index=current_index, dispatch_labels=DISPATCH_STATUS_LABELS,
        route_progress=ROUTE_PROGRESS_BY_STATUS.get(rec.dispatch_status, 0),
        next_status=CSWDO_ADVANCE_TRANSITIONS.get(rec.dispatch_status),
        can_issue=(rec.dispatch_status == "loaded" and not rec.is_issued),
        attachments=attachments,
    )


# Action: /cswdo/deliveries/<int:distribution_id>/advance - Moves a delivery to its next step (e.g. Preparing -> Loaded).
@cswdo_bp.route("/deliveries/<int:distribution_id>/advance", methods=["POST"])
@login_required
@role_required("cswdo_admin", "system_admin")
def advance_delivery(distribution_id):
    rec = _own_delivery_or_404(distribution_id)
    target = request.form.get("target")
    if target != CSWDO_ADVANCE_TRANSITIONS.get(rec.dispatch_status):
        flash("That status change is no longer valid.", "error")
        return redirect(url_for("cswdo.delivery_detail", distribution_id=distribution_id))

    rec.dispatch_status = target
    db.session.add(ActivityLog(
        actor_id=current_user.user_id, action_type="distribution_status",
        description=f"D-{rec.distribution_date.year}-{rec.distribution_id:03d} marked {DISPATCH_STATUS_LABELS[target]} "
                    f"(Brgy. {rec.barangay.barangay_name})",
        office_id=current_user.office.office_id if current_user.office else None,
        barangay_id=rec.barangay_id, distribution_id=rec.distribution_id,
    ))
    db.session.commit()
    flash(f"Delivery marked {DISPATCH_STATUS_LABELS[target]}.", "success")
    return redirect(url_for("cswdo.delivery_detail", distribution_id=distribution_id))


# Action: /cswdo/deliveries/<int:distribution_id>/issue - Confirms the loaded packs were released for delivery,
# with the expected arrival time.
@cswdo_bp.route("/deliveries/<int:distribution_id>/issue", methods=["POST"])
@login_required
@role_required("cswdo_admin", "system_admin")
def confirm_issuance(distribution_id):
    rec = _own_delivery_or_404(distribution_id)
    if rec.dispatch_status != "loaded" or rec.is_issued:
        flash("Issuance can only be confirmed once the delivery is loaded.", "error")
        return redirect(url_for("cswdo.delivery_detail", distribution_id=distribution_id))

    eta_raw = request.form.get("eta", "").strip()
    if eta_raw:
        try:
            rec.expected_arrival_time = datetime.strptime(eta_raw, "%H:%M").time()
        except ValueError:
            pass

    rec.issued_by = current_user.user_id
    rec.issued_at = ph_now()
    rec.dispatch_status = "dispatched"
    rec.departure_time = ph_now().time()

    db.session.add(ActivityLog(
        actor_id=current_user.user_id, action_type="distribution_status",
        description=f"D-{rec.distribution_date.year}-{rec.distribution_id:03d} - issuance confirmed, "
                    f"{rec.quantity_released:,} food packs released to Brgy. {rec.barangay.barangay_name}",
        office_id=current_user.office.office_id if current_user.office else None,
        barangay_id=rec.barangay_id, distribution_id=rec.distribution_id,
    ))
    db.session.commit()
    flash(f"Issuance confirmed - {rec.quantity_released:,} packs released. Awaiting barangay validation of receipt.", "success")
    return redirect(url_for("cswdo.delivery_detail", distribution_id=distribution_id))


# Action: /cswdo/deliveries/<int:distribution_id>/replace - Sends replacement packs for ones that arrived missing or damaged.
# Only possible after the barangay confirmed the delivery.
@cswdo_bp.route("/deliveries/<int:distribution_id>/replace", methods=["POST"])
@login_required
@role_required("cswdo_admin", "system_admin")
def replace_delivery(distribution_id):
    rec = _own_delivery_or_404(distribution_id)
    if not rec.is_validated:
        flash("A replacement can only be sent once the barangay has validated the original delivery.", "error")
        return redirect(url_for("cswdo.delivery_detail", distribution_id=distribution_id))

    owed = rec.outstanding_deficit
    if owed <= 0:
        flash("Nothing outstanding on this delivery - no replacement needed.", "error")
        return redirect(url_for("cswdo.delivery_detail", distribution_id=distribution_id))

    quantity = request.form.get("quantity", type=int) or owed
    if quantity <= 0 or quantity > owed:
        flash(f"Enter a replacement quantity between 1 and {owed:,} (packs still owed).", "error")
        return redirect(url_for("cswdo.delivery_detail", distribution_id=distribution_id))

    office = current_user.office
    fp = _own_food_pack_inventory()
    available = fp.quantity_available if fp else 0
    if quantity > available:
        flash(f"{office.office_name if office else 'This office'} only has {available:,} food packs on hand - "
              f"request a stock replenishment from PSWDO or send a smaller replacement.", "error")
        return redirect(url_for("cswdo.delivery_detail", distribution_id=distribution_id))

    replacement = DistributionRecord(
        barangay_id=rec.barangay_id, allocation_id=rec.allocation_id,
        quantity_released=quantity, distribution_date=ph_today(),
        dispatch_status="preparing", submitted_by=current_user.user_id,
        replacement_of_id=rec.distribution_id,
        batch_lots=_deduct_food_pack_batches(office.office_id, quantity),
    )
    db.session.add(replacement)

    # Take the replacement packs out of the municipal warehouse.
    fp.quantity_available -= quantity
    fp.updated_by = current_user.user_id
    db.session.add(WarehouseStockLog(
        office_id=office.office_id, item_type="food_pack", item_name="Food Packs",
        delta=-quantity,
        reason=f"Replacement for D-{rec.distribution_date.year}-{rec.distribution_id:03d} "
               f"(Brgy. {rec.barangay.barangay_name}) - "
               + (f"{rec.shortage_count:,} short" if rec.shortage_count else "")
               + (", " if rec.shortage_count and rec.damaged_count else "")
               + (f"{rec.damaged_count:,} damaged" if rec.damaged_count else ""),
        source_type="standard", updated_by=current_user.user_id,
    ))
    db.session.flush()

    db.session.add(ActivityLog(
        actor_id=current_user.user_id, action_type="distribution_replacement",
        description=f"{office.office_name if office else 'MSWDO'} dispatched a {quantity:,}-pack replacement "
                    f"(D-{replacement.distribution_date.year}-{replacement.distribution_id:03d}) for "
                    f"D-{rec.distribution_date.year}-{rec.distribution_id:03d} - Brgy. {rec.barangay.barangay_name}",
        office_id=office.office_id if office else None,
        barangay_id=rec.barangay_id, distribution_id=replacement.distribution_id,
    ))
    db.session.commit()
    flash(f"Replacement delivery created - {quantity:,} food packs for Brgy. {rec.barangay.barangay_name}, now preparing.", "success")
    return redirect(url_for("cswdo.delivery_detail", distribution_id=replacement.distribution_id))


# Finds a stock request, but only if it belongs to the user's office.
def _own_batch_or_404(batch_id):
    batch = ReliefRequestBatch.query.get_or_404(batch_id)
    office = current_user.office
    if not office or batch.office_id != office.office_id:
        abort(403)
    return batch


# Saves the files attached to a stock request (damage report, photos, other files).
def _save_batch_uploads(batch):
    upload_dir = os.path.join(current_app.root_path, "static", "uploads", "relief_requests", str(batch.batch_id))

    # Saves one attached file (only allowed file types).
    def _save_one(field):
        f = request.files.get(field)
        if not f or not f.filename:
            return None
        ext = f.filename.rsplit(".", 1)[-1].lower() if "." in f.filename else ""
        if ext not in ALLOWED_UPLOAD_EXTENSIONS:
            return None
        os.makedirs(upload_dir, exist_ok=True)
        name = secure_filename(f.filename)
        f.save(os.path.join(upload_dir, name))
        return name

    # Saves several attached files (only allowed file types).
    def _save_many(field):
        files = [f for f in request.files.getlist(field) if f and f.filename]
        if not files:
            return None
        os.makedirs(upload_dir, exist_ok=True)
        saved = []
        for f in files:
            ext = f.filename.rsplit(".", 1)[-1].lower() if "." in f.filename else ""
            if ext in ALLOWED_UPLOAD_EXTENSIONS:
                name = secure_filename(f.filename)
                f.save(os.path.join(upload_dir, name))
                saved.append(name)
        return ",".join(saved) if saved else None

    dr = _save_one("damage_report_file")
    if dr:
        batch.damage_report_file = dr
    ph = _save_many("photo_files")
    if ph:
        batch.photo_files = ph
    ot = _save_many("other_files")
    if ot:
        batch.other_files = ot


# Page: /cswdo/relief-requests - Stock Requests page: request food packs from PSWDO, save drafts,
# and track sent requests until the stock arrives.
@cswdo_bp.route("/relief-requests")
@login_required
@role_required("cswdo_admin", "system_admin")
def relief_requests():
    office = current_user.office
    lgu = office.area_covered if office else None
    tab = request.args.get("tab", "overview")

    primary_event, _ = resolve_effective_event(lgu)

    batches = ReliefRequestBatch.query.filter_by(office_id=office.office_id).order_by(
        ReliefRequestBatch.created_at.desc()
    ).all() if office else []
    drafts = [b for b in batches if b.is_draft]
    submitted = [b for b in batches if not b.is_draft]

    fp = _own_food_pack_inventory()
    on_hand = fp.quantity_available if fp else 0

    ctx = {
        "tab": tab, "lgu": lgu, "office": office, "primary_event": primary_event,
        "status_labels": RR_STATUS_LABELS, "priority_labels": RR_PRIORITY_LABELS,
        "on_hand": on_hand,
        "draft_count": len(drafts),
        "pending_count": len([b for b in submitted if b.status == "pending"]),
        "approved_count": len([b for b in submitted if b.status in ("approved", "partially_approved")]),
        "fulfilled_count": len([b for b in submitted if b.status == "fulfilled"]),
    }

    if tab == "create":
        draft_id = request.args.get("draft_id", type=int)
        editing = _own_batch_or_404(draft_id) if draft_id else None
        if editing and not editing.is_draft:
            abort(404)
        ctx.update({
            "editing_draft": editing,
            "food_packs_value": editing.requested_food_packs if editing else "",
            "priority_value": editing.priority if editing else "medium",
            "reason_value": editing.reason if editing else "",
            "remarks_value": editing.remarks if editing else "",
            "today": ph_today(),
        })
    elif tab == "tracking":
        sel_id = request.args.get("batch_id", type=int)
        selected = next((b for b in submitted if b.batch_id == sel_id), None) or (submitted[0] if submitted else None)
        ctx.update({"trackable": submitted[:12], "selected": selected})
    else:
        search = request.args.get("q", "").strip().lower()
        status_filter = request.args.get("status", "all")
        priority_filter = request.args.get("priority", "all")
        event_filter = request.args.get("event_id", type=int)
        date_from, date_to = date_range(request.args)
        rows = [b for b in batches if not search or search in b.ref.lower()]
        if status_filter == "approved":
            rows = [b for b in rows if b.display_status in ("approved", "partially_approved")]
        elif status_filter != "all":
            rows = [b for b in rows if b.display_status == status_filter]
        if priority_filter != "all":
            rows = [b for b in rows if b.priority == priority_filter]
        if event_filter:
            rows = [b for b in rows if b.event_id == event_filter]
        rows = [b for b in rows if in_range(b.submitted_at or b.created_at, date_from, date_to)]
        ctx.update({
            "rows": rows, "total": len(submitted), "search_query": search,
            "status_filter": status_filter, "priority_filter": priority_filter, "event_filter": event_filter,
            "date_from": iso(date_from), "date_to": iso(date_to),
            "filter_events": sorted({b.event for b in batches if b.event}, key=lambda e: e.start_date, reverse=True),
        })

    return render_template("cswdo/relief_requests.html", **ctx)


# Copies the stock request form (number of packs, priority, reason, remarks) into the request.
def _apply_batch_form(batch):
    batch.requested_food_packs = max(request.form.get("food_packs", type=int) or 0, 0)
    pr = request.form.get("priority", "medium")
    batch.priority = pr if pr in RR_PRIORITY_LABELS else "medium"
    batch.reason = request.form.get("reason", "").strip() or None
    batch.remarks = request.form.get("remarks", "").strip() or None


# Action: /cswdo/relief-requests/save-draft - Saves a stock request as a draft (not yet sent to PSWDO).
@cswdo_bp.route("/relief-requests/save-draft", methods=["POST"])
@login_required
@role_required("cswdo_admin", "system_admin")
def relief_request_save_draft():
    office = current_user.office
    if not office:
        flash("No office on file for this account.", "error")
        return redirect(url_for("cswdo.relief_requests"))
    primary_event, _ = resolve_effective_event(office.area_covered)
    draft_id = request.form.get("draft_id", type=int)
    batch = _own_batch_or_404(draft_id) if draft_id else None
    if batch and not batch.is_draft:
        abort(404)
    if batch is None:
        batch = ReliefRequestBatch(office_id=office.office_id,
                                   event_id=primary_event.event_id if primary_event else None,
                                   created_by=current_user.user_id, status="draft")
        db.session.add(batch)
    _apply_batch_form(batch)
    batch.status = "draft"
    db.session.flush()
    _save_batch_uploads(batch)
    db.session.commit()
    flash(f"Saved as draft ({batch.ref}).", "success")
    return redirect(url_for("cswdo.relief_requests", tab="create", draft_id=batch.batch_id))


# Action: /cswdo/relief-requests/<int:batch_id>/delete - Deletes a draft stock request and its attached files.
# Requests already sent can't be deleted.
@cswdo_bp.route("/relief-requests/<int:batch_id>/delete", methods=["POST"])
@login_required
@role_required("cswdo_admin", "system_admin")
def relief_request_delete_draft(batch_id):
    batch = _own_batch_or_404(batch_id)
    if not batch.is_draft:
        flash("Only a draft can be deleted. Submitted stock requests stay on record.", "error")
        return redirect(url_for("cswdo.relief_requests"))
    ref = batch.ref
    upload_dir = os.path.join(
        current_app.root_path, "static", "uploads", "relief_requests", str(batch.batch_id)
    )
    db.session.delete(batch)
    db.session.commit()
    shutil.rmtree(upload_dir, ignore_errors=True)
    flash(f"Draft {ref} deleted.", "success")
    return redirect(url_for("cswdo.relief_requests"))


# Action: /cswdo/relief-requests/submit - Sends a stock request to PSWDO for approval.
@cswdo_bp.route("/relief-requests/submit", methods=["POST"])
@login_required
@role_required("cswdo_admin", "system_admin")
def relief_request_submit():
    office = current_user.office
    if not office:
        flash("No office on file for this account.", "error")
        return redirect(url_for("cswdo.relief_requests"))
    primary_event, _ = resolve_effective_event(office.area_covered)
    draft_id = request.form.get("draft_id", type=int)
    batch = _own_batch_or_404(draft_id) if draft_id else None
    if batch and not batch.is_draft:
        abort(404)
    if batch is None:
        batch = ReliefRequestBatch(office_id=office.office_id,
                                   event_id=primary_event.event_id if primary_event else None,
                                   created_by=current_user.user_id, status="draft")
        db.session.add(batch)
    _apply_batch_form(batch)

    if not batch.requested_food_packs or batch.requested_food_packs <= 0:
        flash("Enter the number of food packs to request.", "error")
        db.session.rollback()
        return redirect(url_for("cswdo.relief_requests", tab="create", draft_id=batch.batch_id if batch.batch_id else None))
    if not batch.reason:
        flash("Explain why the replenishment is needed.", "error")
        db.session.rollback()
        return redirect(url_for("cswdo.relief_requests", tab="create", draft_id=batch.batch_id if batch.batch_id else None))

    db.session.flush()
    _save_batch_uploads(batch)
    batch.status = "pending"
    batch.submitted_at = ph_now()
    if primary_event and not batch.event_id:
        batch.event_id = primary_event.event_id

    db.session.add(ActivityLog(
        actor_id=current_user.user_id, action_type="relief_request_submitted",
        description=f"{office.office_name} submitted stock request {batch.ref} to PSWDO - "
                    f"{batch.requested_food_packs:,} food packs",
        office_id=office.office_id, batch_id=batch.batch_id,
    ))
    db.session.commit()
    flash(f"{batch.ref} submitted to PSWDO.", "success")
    return redirect(url_for("cswdo.relief_requests", tab="tracking", batch_id=batch.batch_id))


# Action: /cswdo/transfers/<int:transfer_id>/receive - Confirms the municipal warehouse received a transfer from PSWDO.
# Good packs are added to stock; damaged ones go to damaged stock.
@cswdo_bp.route("/transfers/<int:transfer_id>/receive", methods=["POST"])
@login_required
@role_required("cswdo_admin", "system_admin")
def receive_transfer(transfer_id):
    from app.models.logistics import WarehouseTransfer
    office = current_user.office
    transfer = WarehouseTransfer.query.get_or_404(transfer_id)
    if not office or transfer.to_office_id != office.office_id:
        abort(403)
    if transfer.status == "completed":
        flash("This transfer has already been received.", "error")
        return redirect(request.referrer or url_for("cswdo.municipal_inventory"))
    if transfer.dispatch_status not in ("in_transit", "delivered"):
        flash("PSWDO has not dispatched this transfer yet.", "error")
        return redirect(request.referrer or url_for("cswdo.municipal_inventory"))

    condition = request.form.get("condition", "complete")
    total = transfer.quantity or 0
    if condition == "partial":
        received = request.form.get("quantity_received", type=int)
        damaged = 0
        if received is None or received < 0 or received >= total:
            flash(f"For a partial delivery, enter how many packs arrived (fewer than {total:,}).", "error")
            return redirect(request.referrer or url_for("cswdo.municipal_inventory"))
    elif condition == "damaged":
        good = request.form.get("quantity_good", type=int) or 0
        damaged = request.form.get("quantity_damaged", type=int) or 0
        received = good + damaged
        if good < 0 or damaged < 1 or received > total:
            flash(f"Enter the good and damaged packs (at least 1 damaged, no more than {total:,} in all).", "error")
            return redirect(request.referrer or url_for("cswdo.municipal_inventory"))
    else:
        condition, received, damaged = "complete", total, 0
    receipt_note = request.form.get("receipt_note", "").strip()[:255] or None
    if condition != "complete" and not receipt_note:
        flash("Add a short note explaining what was short or damaged.", "error")
        return redirect(request.referrer or url_for("cswdo.municipal_inventory"))
    usable = received - damaged

    inv = WarehouseInventory.query.filter_by(office_id=office.office_id, item_type=transfer.item_type).first()
    if inv is None:
        inv = WarehouseInventory(office_id=office.office_id, item_type=transfer.item_type,
                                 item_name="Food Packs", unit="packs", quantity_available=0)
        db.session.add(inv)
    # Add the good packs to the municipal warehouse.
    inv.quantity_available = (inv.quantity_available or 0) + usable
    inv.updated_by = current_user.user_id

    transfer.status = "completed"
    transfer.dispatch_status = "delivered"
    transfer.received_by = request.form.get("received_by", "").strip() or current_user.name
    transfer.received_at = ph_now()
    transfer.completed_at = ph_now()
    transfer.receipt_condition = condition
    transfer.quantity_received = received
    transfer.quantity_damaged = damaged
    transfer.receipt_note = receipt_note
    ref = transfer.batch.ref if transfer.batch else transfer.ref
    if transfer.batch:
        transfer.batch.status = "fulfilled"

    if transfer.item_type == "food_pack" and usable:
        for received_date, qty, item_specs in _lots_from_json(transfer.batch_lots, usable, ph_today()):
            _create_food_pack_batch(office.office_id, qty, received_date, current_user.user_id, item_specs)

    detail = ""
    if received != total:
        detail += f", {received:,} of {total:,} dispatched received"
    if damaged:
        detail += f", {damaged:,} damaged"
    db.session.add(WarehouseStockLog(
        office_id=office.office_id, item_type=transfer.item_type, item_name=inv.item_name,
        delta=usable, reason=f"Received from {transfer.from_office.office_name} ({ref}){detail}",
        source_type="standard", updated_by=current_user.user_id,
    ))
    if damaged:
        dmg = WarehouseInventory.query.filter_by(office_id=office.office_id, item_type="food_pack_damaged").first()
        if dmg is None:
            dmg = WarehouseInventory(
                office_id=office.office_id, item_type="food_pack_damaged",
                item_name="Damaged Food Packs (Returned)", unit="packs", quantity_available=0,
            )
            db.session.add(dmg)
        dmg.quantity_available = (dmg.quantity_available or 0) + damaged
        dmg.updated_by = current_user.user_id
        db.session.add(WarehouseStockLog(
            office_id=office.office_id, item_type="food_pack_damaged", item_name="Damaged Food Packs (Returned)",
            delta=damaged, source_type="returned_damaged",
            reason=f"{damaged:,} packs arrived damaged in {ref} from {transfer.from_office.office_name} - for disposal/write-off",
            updated_by=current_user.user_id,
        ))
    db.session.add(ActivityLog(
        actor_id=current_user.user_id, action_type="warehouse_transfer_completed",
        description=f"{office.office_name} received {usable:,} usable food packs from "
                    f"{transfer.from_office.office_name} ({ref}) - {condition}{detail}"
                    + (f" - {receipt_note}" if receipt_note else ""),
        office_id=office.office_id, batch_id=transfer.batch_id,
    ))
    db.session.commit()
    if condition == "complete":
        flash(f"Received {usable:,} food packs. Warehouse updated.", "success")
    else:
        flash(f"Recorded as {condition}: {usable:,} usable food packs added to the warehouse.", "success")
    fallback = url_for("cswdo.relief_requests", tab="tracking", batch_id=transfer.batch_id) if transfer.batch_id \
        else url_for("cswdo.municipal_inventory")
    return redirect(request.referrer or fallback)


# Download: /cswdo/relief-requests/export - Downloads the office's stock requests as a CSV (spreadsheet) file.
@cswdo_bp.route("/relief-requests/export")
@login_required
@role_required("cswdo_admin", "system_admin")
def relief_request_export():
    office = current_user.office
    batches = ReliefRequestBatch.query.filter(
        ReliefRequestBatch.office_id == office.office_id,
        ReliefRequestBatch.submitted_at.isnot(None),
    ).order_by(ReliefRequestBatch.submitted_at.desc()).all() if office else []
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["Request ID", "Event", "Requested", "Approved", "Priority", "Status", "Date"])
    for b in batches:
        writer.writerow([
            b.ref, b.event.event_name if b.event else "", b.requested_food_packs,
            b.approved_food_packs, RR_PRIORITY_LABELS.get(b.priority, b.priority),
            RR_STATUS_LABELS.get(b.display_status, b.display_status),
            b.submitted_at.strftime("%Y-%m-%d"),
        ])
    return Response(
        buffer.getvalue(), mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={(office.area_covered if office else 'stock').replace(' ', '_')}_stock_requests.csv"},
    )


# Page: /cswdo/notifications - CSWDO/MSWDO Notifications page: updates about the municipality's barangays and requests,
# filterable by category.
@cswdo_bp.route("/notifications")
@login_required
@role_required("cswdo_admin", "system_admin")
def notifications():
    office = current_user.office
    lgu = office.area_covered if office else None
    filters = _own_activity_filters()
    category_filter = request.args.get("category", "all")

    if not filters:
        return render_template(
            "cswdo/notifications.html", items=[], unread_count=0, total_count=0,
            total_filtered=0, category_filter=category_filter,
            categories=CSWDO_NOTIFICATION_CATEGORIES, page=1, total_pages=1, lgu=lgu,
        )

    known_types = list(NOTIFICATION_META.keys())
    scope = db.and_(db.or_(*filters), ActivityLog.action_type.in_(known_types))
    query = ActivityLog.query.filter(scope)
    if category_filter != "all":
        action_types = [k for k, v in NOTIFICATION_META.items() if v["category"] == category_filter]
        query = query.filter(ActivityLog.action_type.in_(action_types))

    unread_count = ActivityLog.query.filter(scope, ActivityLog.is_read.is_(False)).count()
    total_count = ActivityLog.query.filter(scope).count()

    per_page = 10
    all_matching = query.order_by(ActivityLog.created_at.desc()).all()
    total_filtered = len(all_matching)
    total_pages = max((total_filtered + per_page - 1) // per_page, 1)
    page = max(request.args.get("page", 1, type=int), 1)
    page = min(page, total_pages)
    page_items = []
    for log in all_matching[(page - 1) * per_page: page * per_page]:
        view = _cswdo_notification_view(log)
        view["was_unread"] = not log.is_read
        page_items.append(view)

    if unread_count:
        ActivityLog.query.filter(
            db.or_(*filters),
            ActivityLog.action_type.in_(known_types),
            ActivityLog.is_read.is_(False),
        ).update({"is_read": True}, synchronize_session=False)
        db.session.commit()

    return render_template(
        "cswdo/notifications.html",
        items=page_items, unread_count=unread_count, total_count=total_count,
        total_filtered=total_filtered, category_filter=category_filter,
        categories=CSWDO_NOTIFICATION_CATEGORIES,
        page=page, total_pages=total_pages, per_page=per_page, lgu=lgu,
    )


# Page: /cswdo/notifications/<int:log_id>/view - Marks a notification as read and opens the page it is about.
@cswdo_bp.route("/notifications/<int:log_id>/view")
@login_required
@role_required("cswdo_admin", "system_admin")
def view_notification(log_id):
    log = ActivityLog.query.get_or_404(log_id)
    _assert_own_activity(log)
    log.is_read = True
    db.session.commit()
    destination = _cswdo_notification_view(log)["link"]
    return redirect(destination or url_for("cswdo.notifications"))


# Page: /cswdo/settings/profile - CSWDO/MSWDO user's Profile Settings page.
@cswdo_bp.route("/settings/profile")
@login_required
@role_required("cswdo_admin", "system_admin")
def profile_settings():
    return render_template("cswdo/profile_settings.html")


# Action: /cswdo/settings/profile - Saves the user's own name and email (the email must not be used by another account).
@cswdo_bp.route("/settings/profile", methods=["POST"])
@login_required
@role_required("cswdo_admin", "system_admin")
def update_profile_info():
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip().lower()

    if not name or not email:
        flash("Name and email are required.", "error")
        return redirect(url_for("cswdo.profile_settings"))

    email_taken = User.query.filter(
        User.email == email, User.user_id != current_user.user_id
    ).first()
    if email_taken:
        flash(f"{email} is already in use by another account.", "error")
        return redirect(url_for("cswdo.profile_settings"))

    current_user.name = name
    current_user.email = email
    db.session.commit()
    flash("Profile information updated.", "success")
    return redirect(url_for("cswdo.profile_settings"))


# Action: /cswdo/settings/password - Changes the user's own password.
# The current password must be correct and the new one at least 8 characters.
@cswdo_bp.route("/settings/password", methods=["POST"])
@login_required
@role_required("cswdo_admin", "system_admin")
def change_password():
    current_password = request.form.get("current_password", "")
    new_password = request.form.get("new_password", "")
    confirm_password = request.form.get("confirm_password", "")

    if not current_user.check_password(current_password):
        flash("Current password is incorrect.", "error")
    elif len(new_password) < 8:
        flash("New password must be at least 8 characters long.", "error")
    elif new_password != confirm_password:
        flash("New password and confirmation do not match.", "error")
    else:
        current_user.set_password(new_password)
        db.session.commit()
        flash("Password updated successfully.", "success")
    return redirect(url_for("cswdo.profile_settings"))


REPORTS_MIME_TYPES = {
    "pdf": "application/pdf",
    "excel": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}
REPORTS_EXTENSIONS = {"pdf": "pdf", "excel": "xlsx"}


# Reads the report filters, always locked to the user's own municipality.
def _resolve_cswdo_report_filters(lgu):
    from app.routes.report_data import resolve_filters
    filters = resolve_filters(request.args)
    filters["municipality"] = lgu
    filters["lgus"] = [lgu]
    return filters


# The filters saved with a generated report (event and period).
def _cswdo_report_filters_snapshot(filters):
    return {"event_id": filters["event_id"], "days": filters["days"]}


# Rebuilds a past report file from its saved filters, so it can be downloaded again.
def _regenerate_cswdo_report(log, lgu):
    from app.routes.reports import _StoredArgs
    from app.routes.report_data import resolve_filters, build_report
    from app.routes.report_files import generate_file

    stored = json.loads(log.filters_json) if log.filters_json else {}
    filters = resolve_filters(_StoredArgs(stored))
    filters["municipality"] = lgu
    filters["lgus"] = [lgu]
    report = build_report(log.report_type, filters, log.generated_by_user)
    return generate_file(report, log.format)


# Page: /cswdo/reports - Reports page: summary numbers for the municipality and the PDF/Excel reports
# that can be generated, plus recently generated reports.
@cswdo_bp.route("/reports")
@login_required
@role_required("cswdo_admin", "system_admin")
def reports():
    from app.models.report import ReportLog
    from app.routes.report_data import REPORT_TYPES

    office = current_user.office
    lgu = office.area_covered if office else None
    if not lgu:
        abort(404)

    filters = _resolve_cswdo_report_filters(lgu)
    active_events = DisasterEvent.query.filter_by(is_reference=False).order_by(DisasterEvent.start_date.desc()).all()

    barangay_ids = [b.barangay_id for b in Barangay.query.filter_by(city_municipality=lgu).all()]

    approved_q = AllocationRecord.query.filter(
        AllocationRecord.status.in_(("approved", "released")),
        AllocationRecord.allocation_date >= filters["start_date"],
        AllocationRecord.barangay_id.in_(barangay_ids),
    )
    delivered_q = DistributionRecord.query.filter(
        DistributionRecord.dispatch_status == "delivered",
        DistributionRecord.distribution_date >= filters["start_date"],
        DistributionRecord.barangay_id.in_(barangay_ids),
    )
    if filters["event_id"]:
        approved_q = approved_q.filter(AllocationRecord.event_id == filters["event_id"])
        delivered_q = delivered_q.join(AllocationRecord).filter(AllocationRecord.event_id == filters["event_id"])

    reports_generated = ReportLog.query.filter(
        ReportLog.generated_by == current_user.user_id,
        ReportLog.generated_at >= filters["start_date"],
    ).count()
    approved_requests = approved_q.count()
    packs_distributed = sum(d.quantity_released for d in delivered_q.all())
    completed_deliveries = delivered_q.count()

    query_params = {"event_id": filters["event_id"] or "", "days": filters["days"]}
    report_cards = [
        {"slug": slug, **info, "generate_url": url_for("cswdo.report_view", report_type=slug, **query_params)}
        for slug, info in REPORT_TYPES.items()
    ]

    recent_logs = ReportLog.query.filter_by(generated_by=current_user.user_id).order_by(
        ReportLog.generated_at.desc()
    ).limit(10).all()
    recent_reports = []
    for log in recent_logs:
        stored = json.loads(log.filters_json) if log.filters_json else {}
        recent_reports.append({
            "log": log,
            "title": REPORT_TYPES.get(log.report_type, {}).get("title", log.report_type),
            "view_url": url_for("cswdo.report_view", report_type=log.report_type, **stored),
            "download_url": url_for("cswdo.report_download", report_id=log.report_id),
        })

    coverage_range = "All Time" if filters["days"] == "all" else (
        f"{filters['start_date'].strftime('%b %d')} - {ph_today().strftime('%b %d, %Y')}"
    )

    return render_template(
        "cswdo/reports.html",
        active_events=active_events,
        lgu=lgu,
        filters=filters,
        coverage_range=coverage_range,
        reports_generated=reports_generated,
        approved_requests=approved_requests,
        packs_distributed=packs_distributed,
        completed_deliveries=completed_deliveries,
        report_cards=report_cards,
        recent_reports=recent_reports,
        download_all_url=url_for("cswdo.report_download_all"),
    )


# Page: /cswdo/reports/<report_type> - Shows one report on screen before downloading it.
@cswdo_bp.route("/reports/<report_type>")
@login_required
@role_required("cswdo_admin", "system_admin")
def report_view(report_type):
    from app.routes.report_data import REPORT_TYPES, build_report

    if report_type not in REPORT_TYPES:
        abort(404)
    office = current_user.office
    lgu = office.area_covered if office else None
    if not lgu:
        abort(404)

    filters = _resolve_cswdo_report_filters(lgu)
    report = build_report(report_type, filters, current_user)
    active_events = relevant_active_events_query([lgu]).all()

    return render_template(
        "cswdo/report_view.html",
        report=report, filters=filters, active_events=active_events, lgu=lgu,
    )


# Creates a report as PDF or Excel and saves it in the report history.
def _cswdo_export_report(report_type, fmt):
    from app.models.report import ReportLog
    from app.routes.report_data import REPORT_TYPES, build_report
    from app.routes.report_files import generate_file

    if report_type not in REPORT_TYPES:
        abort(404)
    office = current_user.office
    lgu = office.area_covered if office else None
    if not lgu:
        abort(404)

    filters = _resolve_cswdo_report_filters(lgu)
    report = build_report(report_type, filters, current_user)
    content, pages = generate_file(report, fmt)
    inline = fmt == "pdf" and request.args.get("inline") == "1"

    if not inline:
        db.session.add(ReportLog(
            report_type=report_type, format=fmt, pages=pages,
            filters_json=json.dumps(_cswdo_report_filters_snapshot(filters)),
            generated_by=current_user.user_id,
        ))
        db.session.commit()

    filename = f"{report_type}_{ph_now().strftime('%Y%m%d')}.{REPORTS_EXTENSIONS[fmt]}"
    return Response(
        content, mimetype=REPORTS_MIME_TYPES[fmt],
        headers={"Content-Disposition": f"{'inline' if inline else 'attachment'}; filename={filename}"},
    )


# Download: /cswdo/reports/<report_type>/pdf - Downloads a report as a PDF file.
@cswdo_bp.route("/reports/<report_type>/pdf")
@login_required
@role_required("cswdo_admin", "system_admin")
def report_export_pdf(report_type):
    return _cswdo_export_report(report_type, "pdf")


# Download: /cswdo/reports/<report_type>/excel - Downloads a report as an Excel file.
@cswdo_bp.route("/reports/<report_type>/excel")
@login_required
@role_required("cswdo_admin", "system_admin")
def report_export_excel(report_type):
    return _cswdo_export_report(report_type, "excel")


# Download: /cswdo/reports/download/<int:report_id> - Downloads a report from the history again (only the user's own reports).
@cswdo_bp.route("/reports/download/<int:report_id>")
@login_required
@role_required("cswdo_admin", "system_admin")
def report_download(report_id):
    from app.models.report import ReportLog
    from app.routes.report_data import REPORT_TYPES

    log = ReportLog.query.get_or_404(report_id)
    if log.generated_by != current_user.user_id:
        abort(403)
    if log.report_type not in REPORT_TYPES:
        abort(404)

    office = current_user.office
    lgu = office.area_covered if office else None
    content, _ = _regenerate_cswdo_report(log, lgu)
    filename = f"{log.report_type}_{log.generated_at.strftime('%Y%m%d')}.{REPORTS_EXTENSIONS[log.format]}"
    return Response(
        content, mimetype=REPORTS_MIME_TYPES[log.format],
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


# Download: /cswdo/reports/download-all - Downloads the user's 10 latest reports together in one ZIP file.
@cswdo_bp.route("/reports/download-all")
@login_required
@role_required("cswdo_admin", "system_admin")
def report_download_all():
    from app.models.report import ReportLog
    from app.routes.report_data import REPORT_TYPES

    office = current_user.office
    lgu = office.area_covered if office else None
    logs = ReportLog.query.filter_by(generated_by=current_user.user_id).order_by(
        ReportLog.generated_at.desc()
    ).limit(10).all()
    if not logs:
        flash("No reports have been generated yet - export one first.", "error")
        return redirect(url_for("cswdo.reports"))

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for i, log in enumerate(logs, start=1):
            if log.report_type not in REPORT_TYPES:
                continue
            content, _ = _regenerate_cswdo_report(log, lgu)
            fname = f"{i:02d}_{log.report_type}_{log.generated_at.strftime('%Y%m%d')}.{REPORTS_EXTENSIONS[log.format]}"
            zf.writestr(fname, content)
    buffer.seek(0)

    return Response(
        buffer.getvalue(), mimetype="application/zip",
        headers={
            "Content-Disposition": f"attachment; filename={lgu.replace(' ', '_')}_reports_{ph_now().strftime('%Y%m%d')}.zip"
        },
    )


# The user's own office (shows an error if the account has no office).
def _own_office_or_404():
    office = current_user.office
    if not office:
        abort(404)
    return office


# Finds a stock item, but only if it belongs to the user's own office.
def _own_inventory_item_or_403(inventory_id):
    item = WarehouseInventory.query.get_or_404(inventory_id)
    office = current_user.office
    if not office or item.office_id != office.office_id:
        abort(403)
    return item


# Page: /cswdo/municipal-inventory - Municipal Inventory page: the municipal warehouse's stock, food pack batches with expiration dates,
# incoming transfers from PSWDO, and stock health.
@cswdo_bp.route("/municipal-inventory")
@login_required
@role_required("cswdo_admin", "system_admin")
def municipal_inventory():
    office = _own_office_or_404()
    _sync_food_pack_batches(office.office_id)
    search_query = request.args.get("q", "").strip()

    active_events = relevant_active_events_query([office.area_covered]).all()

    food_pack_item = WarehouseInventory.query.filter_by(office_id=office.office_id, item_type="food_pack").first()
    food_pack_qty = food_pack_item.quantity_available if food_pack_item else 0
    capacity = office.capacity_food_pack or 20000
    pct = round((food_pack_qty / capacity) * 100, 0) if capacity > 0 else 0
    health = _food_pack_health(food_pack_qty, capacity)

    burn = _lgu_burn_rate(office, active_events)
    days_remaining = round(food_pack_qty / burn, 0) if burn else None

    items_q = WarehouseInventory.query.filter_by(office_id=office.office_id)
    if search_query:
        items_q = items_q.filter(WarehouseInventory.item_name.ilike(f"%{search_query}%"))
    items = items_q.order_by(WarehouseInventory.item_name).all()
    rows = [
        {"item": item, "status": _item_status(item.quantity_available, item.min_stock_level)}
        for item in items
    ]
    all_rows = rows
    rows, item_filters = _inventory_row_filters(rows, office.office_id)

    movements = _recent_stock_movements([office.office_id], limit=3)
    all_movements = _full_stock_movements([office.office_id])
    stock_in = sum(m["qty"] for m in all_movements if m["qty"] > 0)
    stock_out = sum(-m["qty"] for m in all_movements if m["qty"] < 0)

    from app.models.logistics import WarehouseTransfer
    incoming = WarehouseTransfer.query.filter(
        WarehouseTransfer.to_office_id == office.office_id,
        WarehouseTransfer.status != "completed",
        WarehouseTransfer.dispatch_status.in_(("in_transit", "delivered")),
    ).order_by(WarehouseTransfer.requested_at.desc()).all()

    batches = FoodPackBatch.query.filter(
        FoodPackBatch.office_id == office.office_id, FoodPackBatch.quantity_remaining > 0
    ).order_by(FoodPackBatch.expiration_date).all()
    batch_rows = [{"batch": b, "shelf_status": _shelf_status(b.expiration_date)} for b in batches]

    return render_template(
        "cswdo/municipal_inventory.html",
        office=office, food_pack_qty=food_pack_qty, capacity=capacity, pct=pct, health=health,
        burn=burn, days_remaining=days_remaining, inventory_summary=all_rows, rows=rows, **item_filters,
        movements=movements, search_query=search_query, incoming_transfers=incoming,
        stock_in=stock_in, stock_out=stock_out, has_active_event=bool(active_events),
        batch_rows=batch_rows, near_expiry_days=NEAR_EXPIRY_DAYS, shelf_status_fn=_shelf_status,
        food_pack_components=FoodPackComponent.query.order_by(FoodPackComponent.sort_order).all(),
    )


# Action: /cswdo/municipal-inventory/add - Adds a new stock item to the municipal warehouse, with its source
# and, for food packs, the contents and expiration dates.
@cswdo_bp.route("/municipal-inventory/add", methods=["POST"])
@login_required
@role_required("cswdo_admin", "system_admin")
def municipal_inventory_add():
    office = _own_office_or_404()
    item_name = request.form.get("item_name", "").strip()
    unit = "packs"
    quantity = request.form.get("quantity", type=int)
    min_stock_level = request.form.get("min_stock_level", type=int) or 0

    if not item_name or quantity is None or quantity < 0:
        flash("Enter a valid item name and quantity.", "error")
        return redirect(url_for("cswdo.municipal_inventory"))

    source_type, donor_name, source_error = _parse_stock_source(request.form, CSWDO_STOCK_SOURCES)
    if source_error:
        flash(source_error, "error")
        return redirect(url_for("cswdo.municipal_inventory"))

    expiration_date, expiry_error = _parse_item_expiration(request.form, item_name)
    if expiry_error:
        flash(expiry_error, "error")
        return redirect(url_for("cswdo.municipal_inventory"))

    item_type = _slugify(item_name)
    if WarehouseInventory.query.filter_by(office_id=office.office_id, item_type=item_type).first():
        flash(f"{item_name} already exists in this warehouse - use Update instead.", "error")
        return redirect(url_for("cswdo.municipal_inventory"))

    db.session.add(WarehouseInventory(
        office_id=office.office_id, item_type=item_type, item_name=item_name, unit=unit,
        quantity_available=quantity, min_stock_level=min_stock_level,
        expiration_date=expiration_date, updated_by=current_user.user_id,
    ))
    if quantity > 0:
        db.session.add(WarehouseStockLog(
            office_id=office.office_id, item_type=item_type, item_name=item_name,
            delta=quantity, reason="Initial stock", source_type=source_type, donor_name=donor_name,
            updated_by=current_user.user_id,
        ))
    db.session.commit()
    flash(f"Added {item_name} to {office.office_name}.", "success")
    return redirect(url_for("cswdo.municipal_inventory"))


# Action: /cswdo/municipal-inventory/<int:inventory_id>/update - Adds or removes stock for an item, with a reason and source.
# The change is saved in the stock history; stock can't go below zero.
@cswdo_bp.route("/municipal-inventory/<int:inventory_id>/update", methods=["POST"])
@login_required
@role_required("cswdo_admin", "system_admin")
def municipal_inventory_update(inventory_id):
    item = _own_inventory_item_or_403(inventory_id)
    delta = request.form.get("delta", type=int)
    unit = request.form.get("unit", "").strip()
    reason = request.form.get("reason", "").strip() or None
    min_stock_level = request.form.get("min_stock_level", type=int)

    if delta is None:
        flash("Enter a quantity to add or remove.", "error")
        return redirect(url_for("cswdo.municipal_inventory"))
    new_quantity = item.quantity_available + delta
    if new_quantity < 0:
        flash(
            f"That would take {item.item_name} below zero - current stock is "
            f"{item.quantity_available:,}.", "error"
        )
        return redirect(url_for("cswdo.municipal_inventory"))
    if min_stock_level is not None and min_stock_level < 0:
        flash("Min stock level can't be negative.", "error")
        return redirect(url_for("cswdo.municipal_inventory"))

    source_type, donor_name = "standard", None
    if delta > 0:
        source_type, donor_name, source_error = _parse_stock_source(request.form, CSWDO_STOCK_SOURCES)
        if source_error:
            flash(source_error, "error")
            return redirect(url_for("cswdo.municipal_inventory"))
    elif request.form.get("source_type", "").strip() == "donation":
        flash("A donation adds stock - enter a positive quantity to record it.", "error")
        return redirect(url_for("cswdo.municipal_inventory"))

    expiry_specs = None
    new_expiration = None
    if item.item_type == "food_pack" and delta > 0:
        expiry_specs, expiry_error = _parse_food_pack_contents(request.form)
        if expiry_error:
            flash(expiry_error, "error")
            return redirect(url_for("cswdo.municipal_inventory"))
    elif item.expiration_date and delta > 0 and request.form.get("expiration_date", "").strip():
        new_expiration, expiry_error = _parse_expiration_date(request.form.get("expiration_date"), item.item_name)
        if expiry_error:
            flash(expiry_error, "error")
            return redirect(url_for("cswdo.municipal_inventory"))

    # Save the new stock quantity.
    item.quantity_available = new_quantity
    if unit:
        item.unit = unit
    if min_stock_level is not None:
        item.min_stock_level = min_stock_level
    if new_expiration:
        item.expiration_date = new_expiration
    item.updated_by = current_user.user_id

    if item.item_type == "food_pack" and delta > 0:
        _create_food_pack_batch(item.office_id, delta, ph_today(), current_user.user_id, expiry_specs)

    if delta != 0:
        db.session.add(WarehouseStockLog(
            office_id=item.office_id, item_type=item.item_type, item_name=item.item_name,
            delta=delta, reason=reason, source_type=source_type, donor_name=donor_name,
            updated_by=current_user.user_id,
        ))
    db.session.commit()
    flash(f"Updated {item.item_name} stock.", "success")
    return redirect(url_for("cswdo.municipal_inventory"))


# Action: /cswdo/municipal-inventory/<int:inventory_id>/resolve-damaged - Handles damaged packs:
# either dispose of them, or return the usable ones to regular stock.
@cswdo_bp.route("/municipal-inventory/<int:inventory_id>/resolve-damaged", methods=["POST"])
@login_required
@role_required("cswdo_admin", "system_admin")
def municipal_inventory_resolve_damaged(inventory_id):
    item = _own_inventory_item_or_403(inventory_id)
    if item.item_type != "food_pack_damaged":
        flash("That item isn't a damaged-stock entry.", "error")
        return redirect(url_for("cswdo.municipal_inventory"))

    quantity = request.form.get("quantity", type=int)
    resolution = request.form.get("resolution", "")
    if not quantity or quantity <= 0:
        flash("Enter how many damaged packs this covers.", "error")
        return redirect(url_for("cswdo.municipal_inventory"))
    if quantity > item.quantity_available:
        flash(f"Only {item.quantity_available:,} damaged packs are on record.", "error")
        return redirect(url_for("cswdo.municipal_inventory"))
    if resolution not in ("disposed", "fixed"):
        flash("Select Disposed or Fixed.", "error")
        return redirect(url_for("cswdo.municipal_inventory"))

    item.quantity_available -= quantity
    item.updated_by = current_user.user_id

    if resolution == "disposed":
        db.session.add(WarehouseStockLog(
            office_id=item.office_id, item_type="food_pack_damaged", item_name=item.item_name,
            delta=-quantity, source_type="standard",
            reason=f"{quantity:,} damaged packs disposed / written off",
            updated_by=current_user.user_id,
        ))
        flash(f"{quantity:,} damaged packs marked disposed.", "success")
    else:
        db.session.add(WarehouseStockLog(
            office_id=item.office_id, item_type="food_pack_damaged", item_name=item.item_name,
            delta=-quantity, source_type="standard",
            reason=f"{quantity:,} damaged packs repaired - moved back to usable Food Packs stock",
            updated_by=current_user.user_id,
        ))
        fp = WarehouseInventory.query.filter_by(office_id=item.office_id, item_type="food_pack").first()
        if fp is None:
            fp = WarehouseInventory(
                office_id=item.office_id, item_type="food_pack",
                item_name="Food Packs", unit="packs", quantity_available=0,
            )
            db.session.add(fp)
        fp.quantity_available = (fp.quantity_available or 0) + quantity
        fp.updated_by = current_user.user_id
        db.session.add(WarehouseStockLog(
            office_id=item.office_id, item_type="food_pack", item_name="Food Packs",
            delta=quantity, source_type="standard",
            reason=f"{quantity:,} previously-damaged packs repaired and returned to usable stock",
            updated_by=current_user.user_id,
        ))
        flash(f"{quantity:,} damaged packs marked fixed and returned to Food Packs stock.", "success")

    db.session.commit()
    return redirect(url_for("cswdo.municipal_inventory"))


# Action: /cswdo/municipal-inventory/expired-batch/<int:batch_id>/resolve - Handles an expired food pack batch:
# either dispose of the packs, or repack them with fresh items and put them back in stock.
@cswdo_bp.route("/municipal-inventory/expired-batch/<int:batch_id>/resolve", methods=["POST"])
@login_required
@role_required("cswdo_admin", "system_admin")
def municipal_inventory_resolve_expired_batch(batch_id):
    office = _own_office_or_404()
    batch = FoodPackBatch.query.get_or_404(batch_id)
    if batch.office_id != office.office_id or batch.status != "expired":
        abort(403)

    quantity = request.form.get("quantity", type=int)
    resolution = request.form.get("resolution", "")
    if not quantity or quantity <= 0:
        flash("Enter how many expired packs this covers.", "error")
        return redirect(url_for("cswdo.municipal_inventory"))
    if quantity > batch.quantity_remaining:
        flash(f"Only {batch.quantity_remaining:,} expired packs are on record for that batch.", "error")
        return redirect(url_for("cswdo.municipal_inventory"))
    if resolution not in ("disposed", "fixed"):
        flash("Select Disposed or Fixed.", "error")
        return redirect(url_for("cswdo.municipal_inventory"))

    expired_item = WarehouseInventory.query.filter_by(
        office_id=office.office_id, item_type="food_pack_expired"
    ).first()
    if expired_item is None or expired_item.quantity_available < quantity:
        flash("Expired stock record is out of sync - reload and try again.", "error")
        return redirect(url_for("cswdo.municipal_inventory"))

    plan, replaced_components = _refreshed_batch_items(batch, ph_today())

    batch.quantity_remaining -= quantity
    expired_item.quantity_available -= quantity
    expired_item.updated_by = current_user.user_id

    if resolution == "disposed":
        db.session.add(WarehouseStockLog(
            office_id=office.office_id, item_type="food_pack_expired", item_name=expired_item.item_name,
            delta=-quantity, source_type="expired",
            reason=f"{quantity:,} expired packs disposed / written off",
            updated_by=current_user.user_id,
        ))
        flash(f"{quantity:,} expired packs marked disposed.", "success")
    else:
        replaced_names = ", ".join(c.name for c in replaced_components)
        db.session.add(WarehouseStockLog(
            office_id=office.office_id, item_type="food_pack_expired", item_name=expired_item.item_name,
            delta=-quantity, source_type="expired",
            reason=f"{quantity:,} expired packs resolved - {replaced_names} replaced with fresh stock",
            updated_by=current_user.user_id,
        ))
        fp = WarehouseInventory.query.filter_by(office_id=office.office_id, item_type="food_pack").first()
        if fp is None:
            fp = WarehouseInventory(
                office_id=office.office_id, item_type="food_pack",
                item_name="Food Packs", unit="packs", quantity_available=0,
            )
            db.session.add(fp)
        fp.quantity_available = (fp.quantity_available or 0) + quantity
        fp.updated_by = current_user.user_id
        db.session.add(WarehouseStockLog(
            office_id=office.office_id, item_type="food_pack", item_name="Food Packs",
            delta=quantity, source_type="expired",
            reason=f"{quantity:,} packs returned to usable stock after replacing {replaced_names}",
            updated_by=current_user.user_id,
        ))

        new_batch = FoodPackBatch(
            office_id=office.office_id, quantity_remaining=quantity,
            received_date=ph_today(),
            expiration_date=_plan_expiration(plan),
            status="active", updated_by=current_user.user_id,
        )
        db.session.add(new_batch)
        db.session.flush()
        for component_id, custom_name, exp, qty_label in plan:
            db.session.add(FoodPackBatchItem(
                batch_id=new_batch.batch_id, component_id=component_id,
                custom_name=custom_name, quantity_label=qty_label, expiration_date=exp,
            ))

        flash(f"{quantity:,} expired packs marked fixed - {replaced_names} replaced, "
              f"returned to Food Packs stock.", "success")

    db.session.commit()
    return redirect(url_for("cswdo.municipal_inventory"))


# Action: /cswdo/municipal-inventory/<int:inventory_id>/delete - Removes a stock item.
# Food Packs can't be removed because forecasts and allocations depend on them.
@cswdo_bp.route("/municipal-inventory/<int:inventory_id>/delete", methods=["POST"])
@login_required
@role_required("cswdo_admin", "system_admin")
def municipal_inventory_delete(inventory_id):
    item = _own_inventory_item_or_403(inventory_id)
    if item.item_type == "food_pack":
        flash("Food Packs can't be removed - it's required for allocation and prediction.", "error")
        return redirect(url_for("cswdo.municipal_inventory"))
    name = item.item_name
    db.session.delete(item)
    db.session.commit()
    flash(f"{name} removed.", "success")
    return redirect(url_for("cswdo.municipal_inventory"))


# Page: /cswdo/municipal-inventory/movements - Stock Movement History page for the municipal warehouse, with filters.
@cswdo_bp.route("/municipal-inventory/movements")
@login_required
@role_required("cswdo_admin", "system_admin")
def municipal_inventory_movements():
    office = _own_office_or_404()
    movements, filters = _movement_filters([office.office_id])
    return render_template(
        "cswdo/municipal_inventory_movements.html",
        office=office, movements=movements, **filters,
    )


# Download: /cswdo/municipal-inventory/movements/export - Downloads the municipal warehouse's stock movement history as a CSV (spreadsheet) file.
@cswdo_bp.route("/municipal-inventory/movements/export")
@login_required
@role_required("cswdo_admin", "system_admin")
def municipal_inventory_movements_export():
    office = _own_office_or_404()
    movements, _ = _movement_filters([office.office_id])
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["Date", "Time", "Activity", "Details", "Quantity"])
    for m in movements:
        writer.writerow([
            m["when"].isoformat() if m["when"] else "",
            m["sort_at"].strftime("%I:%M %p") if m.get("sort_at") else "",
            m["direction"], m["context"], m["qty"],
        ])
    return Response(
        buffer.getvalue(), mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={office.office_name.replace(' ', '_')}_stock_movements.csv"},
    )


# Download: /cswdo/municipal-inventory/export - Downloads the municipal inventory as a CSV (spreadsheet) file.
@cswdo_bp.route("/municipal-inventory/export")
@login_required
@role_required("cswdo_admin", "system_admin")
def municipal_inventory_export():
    office = _own_office_or_404()
    items = WarehouseInventory.query.filter_by(office_id=office.office_id).order_by(
        WarehouseInventory.item_name
    ).all()
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["Item", "Current Qty", "Unit", "Min Level", "Status"])
    for item in items:
        writer.writerow([
            item.item_name, item.quantity_available, item.unit, item.min_stock_level,
            _item_status(item.quantity_available, item.min_stock_level),
        ])
    return Response(
        buffer.getvalue(), mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={office.office_name.replace(' ', '_')}_inventory.csv"},
    )
