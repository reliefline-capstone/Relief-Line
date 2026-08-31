import csv
import io
import json
import os
import shutil
import zipfile
from datetime import datetime, date

from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, Response, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from app.extensions import db
from app.utils.decorators import role_required
from app.models.barangay import Barangay
from app.models.warehouse import WarehouseInventory
from app.models.allocation import AllocationRecord
from app.models.validation import DistributionRecord
from app.models.disaster_event import DisasterEvent
from app.models.barangay_status import BarangayDisasterStatus
from app.utils import weather as weather_service
from app.models.barangay_report import BarangayReport
from app.models.relief_request_batch import ReliefRequestBatch
from app.models.activity_log import ActivityLog
from app.models.user import User
from app.ml import predict as ml_predict

# Reused from the PSWDO route module rather than redefined, so the two offices
# never drift apart on stock thresholds, priority labels, or status wording —
# see app/routes/pswdo.py for the source of truth.
from app.routes.pswdo import (
    _healthy_threshold, _moderate_threshold, DISPATCH_STATUS_LABELS,
    ROUTE_PROGRESS_BY_STATUS, DISPATCH_STEPS, STEP_LABELS,
    NOTIFICATION_META, DEFAULT_NOTIFICATION_META,
    _item_status, _priority_info, _lgu_burn_rate, _recent_stock_movements,
    _gis_scope_lgus, _gis_config,
    _parse_stock_source, _slugify, _full_stock_movements,
)
from app.models.warehouse import WarehouseStockLog

# CSWDO's own link targets for notification "View" buttons — deliberately NOT
# the pswdo.* links NOTIFICATION_LINK_BUILDERS (app/routes/pswdo.py) resolves
# to, since those point at pages role_required("pswdo_admin", "system_admin")
# would 403 a cswdo_admin out of. Both resolve down to the same destination —
# the Relief Requests Tracking tab for the specific batch a record belongs
# to — since that's the one CSWDO screen that shows an individual request's
# full status, distribution stepper, and history in one place. warehouse-
# category notifications (inter-warehouse transfers between PSWDO-managed
# offices) never reach a CSWDO office's own office_id/barangay_id scope in
# the first place, so no entry is needed for that category here.

def _cswdo_batch_tracking_link(batch_id):
    if not batch_id:
        return None
    return url_for("cswdo.relief_requests", tab="tracking", batch_id=batch_id)


def _cswdo_allocation_link(log):
    # PSWDO's stock-request decisions carry batch_id directly.
    if log.batch_id:
        return _cswdo_batch_tracking_link(log.batch_id)
    allocation = AllocationRecord.query.get(log.allocation_id) if log.allocation_id else None
    if allocation and allocation.batch_id:
        return _cswdo_batch_tracking_link(allocation.batch_id)
    if allocation and allocation.distribution_records:
        return url_for("cswdo.delivery_detail", distribution_id=allocation.distribution_records[0].distribution_id)
    return url_for("cswdo.relief_requests")


def _cswdo_distribution_link(log):
    distribution = DistributionRecord.query.get(log.distribution_id) if log.distribution_id else None
    if distribution and distribution.allocation and distribution.allocation.source == "barangay_request":
        return url_for("cswdo.delivery_detail", distribution_id=distribution.distribution_id)
    batch_id = distribution.allocation.batch_id if distribution and distribution.allocation else None
    return _cswdo_batch_tracking_link(batch_id) or url_for("cswdo.dashboard")


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
    "approved": "Approved",
    "declined": "Declined",
    "fulfilled": "Fulfilled",
    "no_report": "No Report",
}



def _own_lgu_barangays():
    office = current_user.office
    lgu = office.area_covered if office else None
    barangays = Barangay.query.filter_by(city_municipality=lgu).order_by(Barangay.barangay_name).all() if lgu else []
    return lgu, barangays


def _assert_own_lgu(report):
    """A cswdo_admin may only act on reports from their own LGU's barangays —
    role_required() only checks the role, not the office/LGU boundary."""
    office = current_user.office
    lgu = office.area_covered if office else None
    if not lgu or report.barangay.city_municipality != lgu:
        abort(403)


def _own_activity_filters():
    """Same office_id/barangay_id OR-scoping the dashboard already applies to
    ActivityLog — the single source of truth for "this CSWDO office's own
    activity," reused by the dashboard's notification preview, the full
    Notifications page, and its mark-as-read actions so all three always
    agree on the same scoped set."""
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


def _assert_own_activity(log):
    """A cswdo_admin may only act on notifications scoped to their own office
    or their own LGU's barangays — mirrors _assert_own_lgu's role/office
    boundary check for the notifications module."""
    office = current_user.office
    lgu = office.area_covered if office else None
    owns_by_office = office and log.office_id == office.office_id
    owns_by_barangay = log.barangay and lgu and log.barangay.city_municipality == lgu
    if not (owns_by_office or owns_by_barangay):
        abort(403)


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


@cswdo_bp.route("/dashboard")
@login_required
@role_required("cswdo_admin", "system_admin")
def dashboard():
    now = datetime.now()
    office = current_user.office
    lgu = office.area_covered if office else None

    active_events = DisasterEvent.query.filter_by(status="active").order_by(
        DisasterEvent.start_date.desc()
    ).all()
    primary_event = active_events[0] if active_events else None

    lgu_barangays = Barangay.query.filter_by(city_municipality=lgu).all() if lgu else []
    lgu_barangay_ids = [b.barangay_id for b in lgu_barangays]
    total_barangays = len(lgu_barangays)

    # Affected barangays + families — this LGU only, current active event
    affected_statuses = []
    if primary_event and lgu_barangay_ids:
        affected_statuses = BarangayDisasterStatus.query.filter(
            BarangayDisasterStatus.event_id == primary_event.event_id,
            BarangayDisasterStatus.barangay_id.in_(lgu_barangay_ids),
            BarangayDisasterStatus.status != "normal",
        ).all()
    affected_barangays_count = len(affected_statuses)
    total_affected_families = sum(s.affected_families for s in affected_statuses)

    # Municipal food-pack stock — own office only (province-wide warehouse
    # management stays a PSWDO responsibility; see Table 10 of the manuscript).
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
    if stock_pct >= _healthy_threshold() * 100:
        stock_health = "Healthy"
    elif stock_pct >= _moderate_threshold() * 100:
        stock_health = "Moderate"
    else:
        stock_health = "Low"

    # Pending relief requests — food packs this office has asked PSWDO to
    # approve/fulfill, not yet decided on.
    pending_requests_count = 0
    if lgu_barangay_ids:
        pending_requests_count = AllocationRecord.query.filter(
            AllocationRecord.barangay_id.in_(lgu_barangay_ids),
            AllocationRecord.status == "pending",
            AllocationRecord.rejection_reason.is_(None),
        ).count()

    # Incoming deliveries — approved allocations already dispatched toward this LGU
    incoming_distributions = []
    if lgu_barangay_ids:
        incoming_distributions = DistributionRecord.query.filter(
            DistributionRecord.barangay_id.in_(lgu_barangay_ids),
            DistributionRecord.dispatch_status.in_(["preparing", "loaded", "dispatched", "in_transit"]),
        ).order_by(DistributionRecord.distribution_date.desc()).all()
    incoming_deliveries_count = len(incoming_distributions)
    next_delivery = incoming_distributions[0] if incoming_distributions else None

    # Pending validations — delivered but awaiting the barangay's photo/signature
    # proof-of-delivery record (Table 10: CSWDO/MSWDO "validation monitoring").
    pending_validations_count = 0
    if lgu_barangay_ids:
        pending_validations_count = DistributionRecord.query.filter(
            DistributionRecord.barangay_id.in_(lgu_barangay_ids),
            DistributionRecord.status == "pending",
            DistributionRecord.dispatch_status == "delivered",
        ).count()

    # Barangay Relief Requests — Tier-1 requests from this LGU's barangays (a
    # BarangayReport carrying a food-pack ask). CSWDO/MSWDO reviews and fulfils
    # these from its own municipal warehouse; PSWDO is not involved. This is a
    # live status strip only — the full queue is the Barangay Reports page
    # (cswdo.damage_assessment), so this stays scoped exactly like that page
    # (all non-draft reports, newest first) rather than to the active event —
    # otherwise a request the user just acted on vanishes here if it belonged
    # to an event that has since ended.
    _STATUS_TAB = {
        "pending": "queue", "returned": "queue", "approved": "approved",
        "fulfilled": "fulfilled", "declined": "declined",
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
                "requested": rep.requested_food_packs,
                "active_distribution": active_distribution,
                "progress_pct": ROUTE_PROGRESS_BY_STATUS.get(active_distribution.dispatch_status, 0) if active_distribution else None,
            })

    # Barangay status reports — real priority tiers for this LGU (no "verified/
    # pending" concept exists in the data model, so this uses the same
    # normal/monitoring/needs_assistance/high_priority tiers the GIS map uses).
    barangay_reports = []
    if primary_event and lgu_barangays:
        status_by_barangay = {
            s.barangay_id: s for s in BarangayDisasterStatus.query.filter(
                BarangayDisasterStatus.event_id == primary_event.event_id,
                BarangayDisasterStatus.barangay_id.in_(lgu_barangay_ids),
            ).all()
        }
        for b in lgu_barangays:
            status_row = status_by_barangay.get(b.barangay_id)
            status_key = status_row.status if status_row else "normal"
            barangay_reports.append({
                "barangay": b,
                "affected_families": status_row.affected_families if status_row else 0,
                "priority": _priority_info(status_key),
            })
        barangay_reports.sort(key=lambda r: (r["priority"]["rank"], r["affected_families"]), reverse=True)
        barangay_reports = barangay_reports[:5]

    # Recent activity + notifications — scoped to this office and/or this LGU's
    # barangays, same scope the full Notifications page and mark-as-read
    # actions use (see _own_activity_filters).
    activity_filters = _own_activity_filters()

    recent_activities = []
    if activity_filters:
        # Also restricted to NOTIFICATION_META's known operational action_types
        # (see app.routes.pswdo.notifications) — the office/barangay OR-scope
        # above already excludes most System Administration rows since those
        # carry no office_id/barangay_id, but this makes that exclusion
        # explicit instead of incidental.
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
        active_events=active_events,
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
        pending_validations_count=pending_validations_count,
        relief_request_rows=relief_request_rows,
        barangay_reports=barangay_reports,
        recent_activities=recent_activities,
        status_labels=DAMAGE_STATUS_LABELS,
        dispatch_status_labels=DISPATCH_STATUS_LABELS,
        weather_cities=[lgu] if lgu else [],
    )


@cswdo_bp.route("/dashboard/weather")
@login_required
@role_required("cswdo_admin", "system_admin")
def dashboard_weather():
    """JSON feed for the dashboard's Weather & Typhoon Watch widget — this
    office's own LGU only (province-wide monitoring is a PSWDO concern, same
    scoping as the rest of this dashboard — see Table 10 of the manuscript)."""
    office = current_user.office
    lgu = office.area_covered if office else None
    return weather_service.get_dashboard_snapshot([lgu] if lgu else [])


@cswdo_bp.route("/gis-map")
@login_required
@role_required("cswdo_admin", "system_admin")
def gis_map():
    """Own-page shell so a CSWDO/MSWDO admin gets the CSWDO sidebar/nav (not
    PSWDO's) — same convention as every other page this office has its own
    template for. The actual map data comes from app.routes.pswdo's gis-map
    endpoints, which is fine to share: those are now scoped per-user via
    _gis_scope_lgus(), so a CSWDO admin hitting them only ever gets their own
    municipality back, same as if the logic were duplicated here."""
    active_events = DisasterEvent.query.filter_by(status="active").order_by(
        DisasterEvent.start_date.desc()
    ).all()
    return render_template(
        "cswdo/gis_map.html",
        active_events=active_events,
        target_lgus=_gis_scope_lgus(),
        gis_config=_gis_config(),
    )


# ---------------------------------------------------------------------------
# Relief Requests inbox — barangay Relief Requests come here. CSWDO/MSWDO
# reviews each, approves + fulfils from its OWN municipal warehouse (creates
# the AllocationRecord + the delivery), or declines / returns for correction.
# PSWDO is not involved in this tier. (Route name kept as `damage_assessment`
# for URL stability; the page is "Relief Requests".)
# ---------------------------------------------------------------------------

def _own_food_pack_inventory():
    office = current_user.office
    if not office:
        return None
    return WarehouseInventory.query.filter_by(
        office_id=office.office_id, item_type="food_pack"
    ).first()


def _relief_request_row(report):
    return {
        "report": report,
        "barangay": report.barangay,
        "model_estimate": ml_predict.predict_quantity(report.barangay) or 0,
        "allocation": report.allocation,
    }


@cswdo_bp.route("/damage-assessment")
@login_required
@role_required("cswdo_admin", "system_admin")
def damage_assessment():
    lgu, lgu_barangays = _own_lgu_barangays()
    office = current_user.office
    tab = request.args.get("tab", "queue")
    search_query = request.args.get("q", "").strip().lower()

    active_events = DisasterEvent.query.filter_by(status="active").order_by(
        DisasterEvent.start_date.desc()
    ).all()
    primary_event = active_events[0] if active_events else None

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

    pending_rows = [r for r in rows if r["report"].status in ("pending", "returned")]
    approved_rows = [r for r in rows if r["report"].status == "approved"]
    fulfilled_rows = [r for r in rows if r["report"].status == "fulfilled"]
    declined_rows = [r for r in rows if r["report"].status == "declined"]

    fp = _own_food_pack_inventory()
    on_hand = fp.quantity_available if fp else 0

    requested_pending = sum(r["report"].requested_food_packs or 0 for r in pending_rows)
    approved_packs = sum(
        (r["allocation"].allocated_quantity if r["allocation"] else 0)
        for r in approved_rows + fulfilled_rows
    )

    return render_template(
        "cswdo/damage_assessment.html",
        tab=tab, now=datetime.now(), lgu=lgu, office=office,
        primary_event=primary_event,
        rows=rows, pending_rows=pending_rows, approved_rows=approved_rows,
        fulfilled_rows=fulfilled_rows, declined_rows=declined_rows,
        on_hand=on_hand, requested_pending=requested_pending, approved_packs=approved_packs,
        total_barangays=len(lgu_barangays),
        status_labels=DAMAGE_STATUS_LABELS,
        dispatch_labels=DISPATCH_STATUS_LABELS,
        search_query=search_query,
    )


def _fulfil_barangay_request(report, quantity, office):
    """Create the AllocationRecord + its DistributionRecord for an approved
    barangay Relief Request, and deduct the fulfilling CSWDO warehouse. The
    barangay's own inventory is bumped later, when it confirms receipt."""
    fp = _own_food_pack_inventory()
    available = fp.quantity_available if fp else 0
    if quantity > available:
        return None, (
            f"{office.office_name} only has {available:,} food packs on hand — "
            f"request a stock replenishment from PSWDO or approve a smaller quantity."
        )

    alloc = AllocationRecord(
        barangay_id=report.barangay_id, office_id=office.office_id,
        predicted_quantity=report.requested_food_packs or quantity,
        allocated_quantity=quantity,
        historical_allocation=ml_predict.historical_allocation_for(report.barangay_id),
        allocation_date=date.today(), event_id=report.event_id,
        status="approved", fulfilling_office_id=office.office_id,
        source="barangay_request", barangay_report_id=report.report_id,
        created_by=current_user.user_id, decided_by=current_user.user_id,
    )
    db.session.add(alloc)
    db.session.flush()

    dist = DistributionRecord(
        barangay_id=report.barangay_id, allocation_id=alloc.allocation_id,
        quantity_released=quantity, distribution_date=date.today(),
        dispatch_status="preparing", submitted_by=current_user.user_id,
    )
    db.session.add(dist)

    fp.quantity_available -= quantity
    fp.updated_by = current_user.user_id
    db.session.add(WarehouseStockLog(
        office_id=office.office_id, item_type="food_pack", item_name="Food Packs",
        delta=-quantity, reason=f"Released to Brgy. {report.barangay.barangay_name} ({report.ref})",
        source_type="standard", updated_by=current_user.user_id,
    ))
    db.session.flush()
    return alloc, None


def _push_proactive_allocation(barangay, quantity, office, event, remarks):
    """CSWDO/MSWDO pushing food packs to a barangay proactively — no
    BarangayReport behind it (source='cswdo_direct'). Same warehouse-check +
    AllocationRecord + DistributionRecord shape as _fulfil_barangay_request;
    only the provenance differs. predicted_quantity is recorded for
    reference/traceability, but allocated_quantity is always whatever the
    CSWDO admin actually entered on the form — the model never decides the
    number on its own (manuscript Ch.2: predicted output is decision support,
    not an automatic final allocation)."""
    fp = _own_food_pack_inventory()
    available = fp.quantity_available if fp else 0
    if quantity > available:
        return None, (
            f"{office.office_name} only has {available:,} food packs on hand — "
            f"request a stock replenishment from PSWDO or allocate a smaller quantity."
        )

    alloc = AllocationRecord(
        barangay_id=barangay.barangay_id, office_id=office.office_id,
        predicted_quantity=ml_predict.predict_quantity(barangay) or 0,
        allocated_quantity=quantity,
        historical_allocation=ml_predict.historical_allocation_for(barangay.barangay_id),
        allocation_date=date.today(), event_id=event.event_id,
        status="approved", fulfilling_office_id=office.office_id,
        source="cswdo_direct", barangay_report_id=None,
        created_by=current_user.user_id, decided_by=current_user.user_id,
        remarks=remarks or None,
    )
    db.session.add(alloc)
    db.session.flush()

    dist = DistributionRecord(
        barangay_id=barangay.barangay_id, allocation_id=alloc.allocation_id,
        quantity_released=quantity, distribution_date=date.today(),
        dispatch_status="preparing", submitted_by=current_user.user_id,
    )
    db.session.add(dist)

    fp.quantity_available -= quantity
    fp.updated_by = current_user.user_id
    db.session.add(WarehouseStockLog(
        office_id=office.office_id, item_type="food_pack", item_name="Food Packs",
        delta=-quantity,
        reason=f"Proactively allocated to Brgy. {barangay.barangay_name} ({event.event_name})",
        source_type="standard", updated_by=current_user.user_id,
    ))
    db.session.flush()
    return alloc, None


@cswdo_bp.route("/proactive-allocate", methods=["POST"])
@login_required
@role_required("cswdo_admin", "system_admin")
def proactive_allocate():
    """Push food packs to a barangay ahead of any Relief Request — the
    manuscript's pre-positioning phase applied at the barangay tier, driven
    by the Predictive Analytics ranking (see prediction.index / _barangay_
    snapshot's 'model'-sourced rows). Scoped to an active disaster event on
    purpose, so this stays typhoon-related pre-positioning rather than an
    everyday bypass of the request workflow."""
    office = current_user.office
    if not office:
        flash("No office on file for this account.", "error")
        return redirect(url_for("prediction.index"))

    barangay_id = request.form.get("barangay_id", type=int)
    barangay = Barangay.query.get(barangay_id) if barangay_id else None
    if not barangay or barangay.city_municipality != office.area_covered:
        flash("Select a barangay in your own LGU.", "error")
        return redirect(url_for("prediction.index"))

    event_id = request.form.get("event_id", type=int)
    event = DisasterEvent.query.get(event_id) if event_id else None
    if not event or event.status != "active":
        flash("Select an active disaster event before allocating proactively.", "error")
        return redirect(url_for("prediction.index"))

    quantity = request.form.get("quantity", type=int)
    if not quantity or quantity <= 0:
        flash("Enter the number of food packs to allocate.", "error")
        return redirect(url_for("prediction.index", event_id=event_id))

    remarks = request.form.get("remarks", "").strip()
    if not remarks:
        flash("Add a short justification for this proactive allocation (no barangay request backs it, so this is the record of why).", "error")
        return redirect(url_for("prediction.index", event_id=event_id))

    alloc, error = _push_proactive_allocation(barangay, quantity, office, event, remarks)
    if error:
        flash(error, "error")
        return redirect(url_for("prediction.index", event_id=event_id))

    db.session.add(ActivityLog(
        actor_id=current_user.user_id, action_type="cswdo_proactive_allocation",
        description=f"{office.office_name} proactively allocated {quantity:,} food packs to "
                    f"Brgy. {barangay.barangay_name} ({event.event_name}) — model estimate was "
                    f"{alloc.predicted_quantity:,}",
        office_id=office.office_id, barangay_id=barangay.barangay_id,
        allocation_id=alloc.allocation_id,
    ))
    db.session.commit()
    flash(f"{quantity:,} food packs proactively allocated to Brgy. {barangay.barangay_name}.", "success")
    return redirect(url_for("prediction.index", event_id=event_id))


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

    alloc, error = _fulfil_barangay_request(report, quantity, office)
    if error:
        db.session.rollback()
        flash(error, "error")
        return redirect(url_for("cswdo.damage_assessment"))

    report.status = "approved"
    report.review_remarks = request.form.get("review_remarks", "").strip() or None
    report.reviewed_by = current_user.user_id
    report.reviewed_at = datetime.utcnow()

    # Keep BarangayDisasterStatus (dashboard / GIS priority) in sync — same as
    # the old verify flow. Event-scoped only.
    if report.event_id:
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

    db.session.add(ActivityLog(
        actor_id=current_user.user_id, action_type="barangay_relief_approved",
        description=f"{office.office_name} approved {quantity:,} food packs for Brgy. "
                    f"{report.barangay.barangay_name} ({report.ref}) — delivery scheduled",
        office_id=office.office_id, barangay_id=report.barangay_id,
        allocation_id=alloc.allocation_id,
    ))
    db.session.commit()
    flash(f"{report.ref} approved — {quantity:,} food packs, delivery to Brgy. "
          f"{report.barangay.barangay_name} is now preparing.", "success")
    return redirect(url_for("cswdo.delivery_detail", distribution_id=alloc.distribution_records[0].distribution_id))


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
    report.reviewed_at = datetime.utcnow()
    office = current_user.office
    db.session.add(ActivityLog(
        actor_id=current_user.user_id, action_type="barangay_relief_declined",
        description=f"{office.office_name if office else 'MSWDO'} declined {report.ref} "
                    f"(Brgy. {report.barangay.barangay_name}) — {reason}",
        office_id=office.office_id if office else None, barangay_id=report.barangay_id,
    ))
    db.session.commit()
    flash(f"{report.ref} declined.", "success")
    return redirect(url_for("cswdo.damage_assessment"))


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
    report.reviewed_at = datetime.utcnow()
    office = current_user.office
    db.session.add(ActivityLog(
        actor_id=current_user.user_id, action_type="damage_report_returned",
        description=f"{report.ref} was returned by {office.office_name if office else 'MSWDO'} — {remarks}",
        office_id=office.office_id if office else None, barangay_id=report.barangay_id,
    ))
    db.session.commit()
    flash(f"{report.ref} ({report.barangay.barangay_name}) returned for correction.", "success")
    return redirect(url_for("cswdo.damage_assessment"))


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
        "Request ID", "Barangay", "Typhoon Event", "Status", "Submitted By",
        "Affected Families", "Totally Damaged Houses",
        "Requested Packs", "Allocated Packs", "Last Updated",
    ])
    for rep in reports:
        alloc = rep.allocation
        writer.writerow([
            rep.ref, rep.barangay.barangay_name,
            rep.event.event_name if rep.event else "",
            DAMAGE_STATUS_LABELS.get(rep.status, rep.status),
            rep.submitted_by_name, rep.affected_families, rep.totally_damaged_houses,
            rep.requested_food_packs, alloc.allocated_quantity if alloc else "",
            (rep.reviewed_at or rep.submitted_at).strftime("%Y-%m-%d %H:%M") if (rep.reviewed_at or rep.submitted_at) else "",
        ])

    return Response(
        buffer.getvalue(), mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={(lgu or 'relief_requests').replace(' ', '_')}_relief_requests.csv"},
    )


# ---------------------------------------------------------------------------
# Deliveries — CSWDO/MSWDO dispatches food packs from its own warehouse to a
# barangay and monitors the trip. Two confirmations, kept separate:
#   * ISSUANCE  — CSWDO confirms the packs left the warehouse (this module).
#   * VALIDATION — the barangay confirms receipt with a photo/signature
#     (app.routes.barangay.confirm_receipt). ONLY the barangay's validation
#     closes the request and moves stock into the barangay's inventory.
# Lifecycle: preparing -> loaded -> [Confirm Issuance] dispatched -> in_transit
#            -> [barangay validation] delivered.
# ---------------------------------------------------------------------------

CSWDO_ADVANCE_TRANSITIONS = {"preparing": "loaded", "dispatched": "in_transit"}


def _own_delivery_or_404(distribution_id):
    rec = DistributionRecord.query.get_or_404(distribution_id)
    lgu = current_user.office.area_covered if current_user.office else None
    if not lgu or rec.barangay.city_municipality != lgu:
        abort(404)
    return rec


@cswdo_bp.route("/deliveries")
@login_required
@role_required("cswdo_admin", "system_admin")
def deliveries():
    lgu, lgu_barangays = _own_lgu_barangays()
    status_filter = request.args.get("status", "all")
    search_query = request.args.get("q", "").strip().lower()
    barangay_ids = [b.barangay_id for b in lgu_barangays]

    q = DistributionRecord.query.filter(DistributionRecord.barangay_id.in_(barangay_ids)) if barangay_ids else DistributionRecord.query.filter(db.false())
    # Barangay-tier deliveries only (this office fulfilled them itself) —
    # covers both a barangay's own Relief Request and a proactive,
    # model-driven push with no request behind it.
    q = q.join(AllocationRecord).filter(AllocationRecord.source.in_(("barangay_request", "cswdo_direct")))
    all_recs = q.order_by(DistributionRecord.distribution_date.desc()).all()

    def _counts(status):
        return sum(1 for r in all_recs if r.dispatch_status == status)

    recs = all_recs
    if status_filter != "all":
        recs = [r for r in recs if r.dispatch_status == status_filter]
    if search_query:
        recs = [r for r in recs if search_query in r.barangay.barangay_name.lower()]

    rows = [{
        "rec": r,
        "ref": f"D-{r.distribution_date.year}-{r.distribution_id:03d}",
        "request_ref": (r.allocation.barangay_report.ref if r.allocation and r.allocation.barangay_report else None),
        "event": (r.allocation.event.event_name if r.allocation and r.allocation.event else None),
        "progress_pct": ROUTE_PROGRESS_BY_STATUS.get(r.dispatch_status, 0),
        "awaiting_validation": r.dispatch_status in ("in_transit", "delivered") and r.status != "confirmed",
    } for r in recs]

    return render_template(
        "cswdo/deliveries.html",
        lgu=lgu, rows=rows, status_filter=status_filter, search_query=search_query,
        dispatch_labels=DISPATCH_STATUS_LABELS,
        total=len(all_recs), preparing_count=_counts("preparing"),
        in_transit_count=sum(1 for r in all_recs if r.dispatch_status in ("dispatched", "in_transit")),
        awaiting_validation_count=sum(1 for r in all_recs if r.dispatch_status in ("in_transit", "delivered") and r.status != "confirmed"),
        validated_count=sum(1 for r in all_recs if r.status == "confirmed"),
        packs_in_transit=sum(r.quantity_released for r in all_recs if r.dispatch_status in ("dispatched", "in_transit")),
    )


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

    # This office deducts its warehouse the moment a request is approved (see
    # _fulfil_barangay_request), so `on_hand` above is the LIVE total after
    # every release. Reconstruct what the warehouse held right after THIS
    # release by adding back everything released for a barangay since — so the
    # figure is specific to this delivery instead of the same global number on
    # every page. (Ignores mid-stream replenishment transfers — close enough
    # for a review view.)
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


@cswdo_bp.route("/deliveries/<int:distribution_id>/issue", methods=["POST"])
@login_required
@role_required("cswdo_admin", "system_admin")
def confirm_issuance(distribution_id):
    """Issuance confirmation record — the packs have physically left the CSWDO/
    MSWDO warehouse. Moves the trip to 'dispatched'. This is NOT proof of
    delivery — the barangay still has to validate receipt."""
    rec = _own_delivery_or_404(distribution_id)
    if rec.dispatch_status != "loaded" or rec.is_issued:
        flash("Issuance can only be confirmed once the delivery is loaded.", "error")
        return redirect(url_for("cswdo.delivery_detail", distribution_id=distribution_id))

    rec.issued_by = current_user.user_id
    rec.issued_at = datetime.utcnow()
    rec.dispatch_status = "dispatched"
    rec.departure_time = datetime.now().time()

    db.session.add(ActivityLog(
        actor_id=current_user.user_id, action_type="distribution_status",
        description=f"D-{rec.distribution_date.year}-{rec.distribution_id:03d} — issuance confirmed, "
                    f"{rec.quantity_released:,} food packs released to Brgy. {rec.barangay.barangay_name}",
        office_id=current_user.office.office_id if current_user.office else None,
        barangay_id=rec.barangay_id, distribution_id=rec.distribution_id,
    ))
    db.session.commit()
    flash(f"Issuance confirmed — {rec.quantity_released:,} packs released. Awaiting barangay validation of receipt.", "success")
    return redirect(url_for("cswdo.delivery_detail", distribution_id=distribution_id))


# ---------------------------------------------------------------------------
# Stock Requests (CSWDO -> PSWDO) — municipal warehouse replenishment. The ONE
# request type PSWDO decides on. On approval PSWDO transfers stock from a
# provincial depot into this office's warehouse and both sides monitor the leg;
# CSWDO confirms receipt, which credits the stock and closes the request.
# ---------------------------------------------------------------------------

def _own_batch_or_404(batch_id):
    batch = ReliefRequestBatch.query.get_or_404(batch_id)
    office = current_user.office
    if not office or batch.office_id != office.office_id:
        abort(403)
    return batch


def _save_batch_uploads(batch):
    upload_dir = os.path.join(current_app.root_path, "static", "uploads", "relief_requests", str(batch.batch_id))

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


def municipal_demand_breakdown(office, event):
    """Per-barangay predicted food-pack demand for this office's LGU, so the
    municipal figure PSWDO sees is exactly the sum of the barangay-level model
    outputs (aggregation traceability). Uses the barangay's real active-event
    Relief Request where one exists, else the model estimate."""
    lgu = office.area_covered if office else None
    if not lgu:
        return [], 0
    barangays = Barangay.query.filter_by(city_municipality=lgu).order_by(Barangay.barangay_name).all()
    event_id = event.event_id if event else None
    rows = []
    for b in barangays:
        req = None
        if event_id:
            rep = BarangayReport.query.filter_by(
                barangay_id=b.barangay_id, event_id=event_id
            ).filter(BarangayReport.status.in_(("pending", "approved", "fulfilled"))).first()
            req = rep.requested_food_packs if rep else None
        model = ml_predict.predict_quantity(b) or 0
        demand = req if (req is not None and req > 0) else model
        rows.append({"barangay": b, "model": model, "requested": req, "demand": demand,
                     "source": "request" if (req is not None and req > 0) else "model"})
    return rows, sum(r["demand"] for r in rows)


@cswdo_bp.route("/relief-requests")
@login_required
@role_required("cswdo_admin", "system_admin")
def relief_requests():
    office = current_user.office
    lgu = office.area_covered if office else None
    tab = request.args.get("tab", "overview")

    active_events = DisasterEvent.query.filter_by(status="active").order_by(
        DisasterEvent.start_date.desc()
    ).all()
    primary_event = active_events[0] if active_events else None

    batches = ReliefRequestBatch.query.filter_by(office_id=office.office_id).order_by(
        ReliefRequestBatch.created_at.desc()
    ).all() if office else []
    drafts = [b for b in batches if b.is_draft]
    submitted = [b for b in batches if not b.is_draft]

    fp = _own_food_pack_inventory()
    on_hand = fp.quantity_available if fp else 0
    breakdown, predicted_demand = municipal_demand_breakdown(office, primary_event)
    shortfall = max(predicted_demand - on_hand, 0)

    ctx = {
        "tab": tab, "lgu": lgu, "office": office, "primary_event": primary_event,
        "status_labels": RR_STATUS_LABELS, "priority_labels": RR_PRIORITY_LABELS,
        "on_hand": on_hand, "predicted_demand": predicted_demand, "shortfall": shortfall,
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
            "breakdown": breakdown,
            "food_packs_value": (editing.requested_food_packs if editing else (shortfall or predicted_demand)),
            "priority_value": (editing.priority if editing else ("high" if shortfall > on_hand else "medium")),
            "reason_value": editing.reason if editing else "",
            "remarks_value": editing.remarks if editing else "",
            "today": date.today(),
        })
    elif tab == "tracking":
        sel_id = request.args.get("batch_id", type=int)
        selected = next((b for b in submitted if b.batch_id == sel_id), None) or (submitted[0] if submitted else None)
        ctx.update({"trackable": submitted[:12], "selected": selected})
    else:  # overview
        search = request.args.get("q", "").strip().lower()
        rows = [b for b in batches if not search or search in b.ref.lower()]
        ctx.update({"rows": rows, "total": len(submitted), "search_query": search})

    return render_template("cswdo/relief_requests.html", **ctx)


def _apply_batch_form(batch):
    batch.requested_food_packs = max(request.form.get("food_packs", type=int) or 0, 0)
    pr = request.form.get("priority", "medium")
    batch.priority = pr if pr in RR_PRIORITY_LABELS else "medium"
    batch.reason = request.form.get("reason", "").strip() or None
    batch.remarks = request.form.get("remarks", "").strip() or None


@cswdo_bp.route("/relief-requests/save-draft", methods=["POST"])
@login_required
@role_required("cswdo_admin", "system_admin")
def relief_request_save_draft():
    office = current_user.office
    if not office:
        flash("No office on file for this account.", "error")
        return redirect(url_for("cswdo.relief_requests"))
    primary_event = DisasterEvent.query.filter_by(status="active").order_by(
        DisasterEvent.start_date.desc()
    ).first()
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


@cswdo_bp.route("/relief-requests/<int:batch_id>/delete", methods=["POST"])
@login_required
@role_required("cswdo_admin", "system_admin")
def relief_request_delete_draft(batch_id):
    batch = _own_batch_or_404(batch_id)
    # Only an unsubmitted draft can be deleted — a submitted stock request stays
    # on record so the PSWDO decision trail and any transfer tied to it are
    # never orphaned.
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


@cswdo_bp.route("/relief-requests/submit", methods=["POST"])
@login_required
@role_required("cswdo_admin", "system_admin")
def relief_request_submit():
    office = current_user.office
    if not office:
        flash("No office on file for this account.", "error")
        return redirect(url_for("cswdo.relief_requests"))
    primary_event = DisasterEvent.query.filter_by(status="active").order_by(
        DisasterEvent.start_date.desc()
    ).first()
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
    batch.submitted_at = datetime.utcnow()
    if primary_event and not batch.event_id:
        batch.event_id = primary_event.event_id

    db.session.add(ActivityLog(
        actor_id=current_user.user_id, action_type="relief_request_submitted",
        description=f"{office.office_name} submitted stock request {batch.ref} to PSWDO — "
                    f"{batch.requested_food_packs:,} food packs",
        office_id=office.office_id, batch_id=batch.batch_id,
    ))
    db.session.commit()
    flash(f"{batch.ref} submitted to PSWDO.", "success")
    return redirect(url_for("cswdo.relief_requests", tab="tracking", batch_id=batch.batch_id))


@cswdo_bp.route("/transfers/<int:transfer_id>/receive", methods=["POST"])
@login_required
@role_required("cswdo_admin", "system_admin")
def receive_transfer(transfer_id):
    """CSWDO confirms an incoming transfer (Stock-Request replenishment OR a
    PSWDO pre-positioning push) arrived — credits the warehouse and closes the
    Stock Request if there is one."""
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

    inv = WarehouseInventory.query.filter_by(office_id=office.office_id, item_type=transfer.item_type).first()
    if inv is None:
        inv = WarehouseInventory(office_id=office.office_id, item_type=transfer.item_type,
                                 item_name="Food Packs", unit="packs", quantity_available=0)
        db.session.add(inv)
    inv.quantity_available = (inv.quantity_available or 0) + transfer.quantity
    inv.updated_by = current_user.user_id

    transfer.status = "completed"
    transfer.dispatch_status = "delivered"
    transfer.received_by = request.form.get("received_by", "").strip() or current_user.name
    transfer.received_at = datetime.utcnow()
    transfer.completed_at = datetime.utcnow()
    ref = transfer.batch.ref if transfer.batch else transfer.ref
    if transfer.batch:
        transfer.batch.status = "fulfilled"

    db.session.add(WarehouseStockLog(
        office_id=office.office_id, item_type=transfer.item_type, item_name=inv.item_name,
        delta=transfer.quantity, reason=f"Received from {transfer.from_office.office_name} ({ref})",
        source_type="standard", updated_by=current_user.user_id,
    ))
    db.session.add(ActivityLog(
        actor_id=current_user.user_id, action_type="warehouse_transfer_completed",
        description=f"{office.office_name} received {transfer.quantity:,} food packs from "
                    f"{transfer.from_office.office_name} ({ref})",
        office_id=office.office_id, batch_id=transfer.batch_id,
    ))
    db.session.commit()
    flash(f"Received {transfer.quantity:,} food packs. Warehouse updated.", "success")
    # Same request.referrer-first pattern as the two early-exit branches above —
    # "Confirm Receipt" is submitted from both this page's Municipal Warehouse
    # view and the Relief Requests tracking tab, so send the admin back to
    # whichever one they actually clicked it from, instead of always bouncing
    # to Relief Requests.
    fallback = url_for("cswdo.relief_requests", tab="tracking", batch_id=transfer.batch_id) if transfer.batch_id \
        else url_for("cswdo.municipal_inventory")
    return redirect(request.referrer or fallback)


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


# ---------------------------------------------------------------------------
# Notifications
# ---------------------------------------------------------------------------

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

    # Same NOTIFICATION_META allowlist as pswdo.notifications — the office/
    # barangay OR-scope alone already excludes most System Administration
    # rows (no office_id/barangay_id), but this makes it explicit rather
    # than incidental.
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

    # Opening the Notifications page is itself the "read" action — no per-item
    # or "Mark all as read" click needed. Unread rows still show highlighted on
    # this render (via was_unread) so the user sees what's new before it clears.
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
        categories=CSWDO_NOTIFICATION_CATEGORIES, page=page, total_pages=total_pages, per_page=per_page, lgu=lgu,
    )


@cswdo_bp.route("/notifications/<int:log_id>/view")
@login_required
@role_required("cswdo_admin", "system_admin")
def view_notification(log_id):
    """The Notifications page's "View" link routes through here instead of
    linking to item.link directly, so opening a notification is what marks
    it read — no separate "Mark as read" click required."""
    log = ActivityLog.query.get_or_404(log_id)
    _assert_own_activity(log)
    log.is_read = True
    db.session.commit()
    destination = _cswdo_notification_view(log)["link"]
    return redirect(destination or url_for("cswdo.notifications"))


# ---------------------------------------------------------------------------
# Profile Settings
# ---------------------------------------------------------------------------

@cswdo_bp.route("/settings/profile")
@login_required
@role_required("cswdo_admin", "system_admin")
def profile_settings():
    return render_template("cswdo/profile_settings.html")


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


# ---------------------------------------------------------------------------
# Reports
# ---------------------------------------------------------------------------
# Reuses app.routes.report_data's report builders and app.routes.report_files'
# PDF/Excel generation as-is (both are pure data-in/file-out, no role
# dependency) — but NOT app.routes.reports' routes/templates, since those are
# pswdo_admin-only, live under /pswdo/reports, and let the caller pick "All
# Municipalities" or any of the 3 target LGUs via a municipality query param.
# A cswdo_admin must never see another LGU's data, so filters["municipality"]
# is always forced to this office's own LGU here, ignoring any query param —
# these routes exist entirely so that forcing can happen server-side rather
# than relying on a template to not offer the other choices.

REPORTS_MIME_TYPES = {
    "pdf": "application/pdf",
    "excel": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}
REPORTS_EXTENSIONS = {"pdf": "pdf", "excel": "xlsx"}


def _resolve_cswdo_report_filters(lgu):
    from app.routes.report_data import resolve_filters
    filters = resolve_filters(request.args)
    filters["municipality"] = lgu
    filters["lgus"] = [lgu]
    return filters


def _cswdo_report_filters_snapshot(filters):
    return {"event_id": filters["event_id"], "days": filters["days"]}


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
    active_events = DisasterEvent.query.filter_by(status="active").order_by(
        DisasterEvent.start_date.desc()
    ).all()

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

    # "This office's own reports" — ReportLog has no office_id column, so
    # generated_by is the scoping key (matches this office's single
    # cswdo_admin in current seed data; safe even with more than one, since
    # each admin then just sees their own generated history).
    reports_generated = ReportLog.query.filter(
        ReportLog.generated_by == current_user.user_id,
        ReportLog.generated_at >= filters["start_date"],
    ).count()
    approved_requests = approved_q.count()
    packs_distributed = sum(d.quantity_released for d in delivered_q.all())
    completed_deliveries = delivered_q.count()

    query_params = {"event_id": filters["event_id"], "days": filters["days"]}
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
        f"{filters['start_date'].strftime('%b %d')} - {date.today().strftime('%b %d, %Y')}"
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
    active_events = DisasterEvent.query.filter_by(status="active").order_by(
        DisasterEvent.start_date.desc()
    ).all()

    return render_template(
        "cswdo/report_view.html",
        report=report, filters=filters, active_events=active_events, lgu=lgu,
    )


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

    db.session.add(ReportLog(
        report_type=report_type, format=fmt, pages=pages,
        filters_json=json.dumps(_cswdo_report_filters_snapshot(filters)),
        generated_by=current_user.user_id,
    ))
    db.session.commit()

    filename = f"{report_type}_{datetime.now().strftime('%Y%m%d')}.{REPORTS_EXTENSIONS[fmt]}"
    return Response(
        content, mimetype=REPORTS_MIME_TYPES[fmt],
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@cswdo_bp.route("/reports/<report_type>/pdf")
@login_required
@role_required("cswdo_admin", "system_admin")
def report_export_pdf(report_type):
    return _cswdo_export_report(report_type, "pdf")


@cswdo_bp.route("/reports/<report_type>/excel")
@login_required
@role_required("cswdo_admin", "system_admin")
def report_export_excel(report_type):
    return _cswdo_export_report(report_type, "excel")


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
        flash("No reports have been generated yet — export one first.", "error")
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
            "Content-Disposition": f"attachment; filename={lgu.replace(' ', '_')}_reports_{datetime.now().strftime('%Y%m%d')}.zip"
        },
    )


# ---------------------------------------------------------------------------
# Municipal Warehouse — the CSWDO/MSWDO office manages its own municipal stock
# here (Table 10: "allocation management"; Scope: CSWDO/MSWDO "confirm and
# record the release of food packs from warehouses to target barangays").
# Add/update/adjust stock for food and non-food items, scoped strictly to
# this office's own warehouse. Province-wide depot management + inter-warehouse
# pre-positioning transfers stay a PSWDO responsibility (app/routes/pswdo.py).
# Route bodies mirror the PSWDO equivalents; only the office scope differs.
# ---------------------------------------------------------------------------


def _own_office_or_404():
    office = current_user.office
    if not office:
        abort(404)
    return office


def _own_inventory_item_or_403(inventory_id):
    """A cswdo_admin may only touch line items in their own office's warehouse."""
    item = WarehouseInventory.query.get_or_404(inventory_id)
    office = current_user.office
    if not office or item.office_id != office.office_id:
        abort(403)
    return item


@cswdo_bp.route("/municipal-inventory")
@login_required
@role_required("cswdo_admin", "system_admin")
def municipal_inventory():
    office = _own_office_or_404()
    search_query = request.args.get("q", "").strip()

    active_events = DisasterEvent.query.filter_by(status="active").order_by(
        DisasterEvent.start_date.desc()
    ).all()

    food_pack_item = WarehouseInventory.query.filter_by(office_id=office.office_id, item_type="food_pack").first()
    food_pack_qty = food_pack_item.quantity_available if food_pack_item else 0
    capacity = office.capacity_food_pack or 20000
    pct = round((food_pack_qty / capacity) * 100, 0) if capacity > 0 else 0

    if pct >= _healthy_threshold() * 100:
        health = "Healthy"
    elif pct >= _moderate_threshold() * 100:
        health = "Moderate"
    else:
        health = "Low"

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

    movements = _recent_stock_movements([office.office_id], limit=3)
    all_movements = _full_stock_movements([office.office_id])
    stock_in = sum(m["qty"] for m in all_movements if m["qty"] > 0)
    stock_out = sum(-m["qty"] for m in all_movements if m["qty"] < 0)

    # Incoming transfers from PSWDO awaiting this warehouse's receipt confirmation
    from app.models.logistics import WarehouseTransfer
    incoming = WarehouseTransfer.query.filter(
        WarehouseTransfer.to_office_id == office.office_id,
        WarehouseTransfer.status != "completed",
        WarehouseTransfer.dispatch_status.in_(("in_transit", "delivered")),
    ).order_by(WarehouseTransfer.requested_at.desc()).all()

    return render_template(
        "cswdo/municipal_inventory.html",
        office=office, food_pack_qty=food_pack_qty, capacity=capacity, pct=pct, health=health,
        burn=burn, days_remaining=days_remaining, inventory_summary=rows, rows=rows,
        movements=movements, search_query=search_query, incoming_transfers=incoming,
        stock_in=stock_in, stock_out=stock_out, has_active_event=bool(active_events),
    )


@cswdo_bp.route("/municipal-inventory/add", methods=["POST"])
@login_required
@role_required("cswdo_admin", "system_admin")
def municipal_inventory_add():
    office = _own_office_or_404()
    item_name = request.form.get("item_name", "").strip()
    unit = request.form.get("unit", "").strip() or "units"
    quantity = request.form.get("quantity", type=int)
    min_stock_level = request.form.get("min_stock_level", type=int) or 0

    if not item_name or quantity is None or quantity < 0:
        flash("Enter a valid item name and quantity.", "error")
        return redirect(url_for("cswdo.municipal_inventory"))

    source_type, donor_name, source_error = _parse_stock_source(request.form)
    if source_error:
        flash(source_error, "error")
        return redirect(url_for("cswdo.municipal_inventory"))

    item_type = _slugify(item_name)
    if WarehouseInventory.query.filter_by(office_id=office.office_id, item_type=item_type).first():
        flash(f"{item_name} already exists in this warehouse — use Update instead.", "error")
        return redirect(url_for("cswdo.municipal_inventory"))

    db.session.add(WarehouseInventory(
        office_id=office.office_id, item_type=item_type, item_name=item_name, unit=unit,
        quantity_available=quantity, min_stock_level=min_stock_level,
        updated_by=current_user.user_id,
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


@cswdo_bp.route("/municipal-inventory/<int:inventory_id>/update", methods=["POST"])
@login_required
@role_required("cswdo_admin", "system_admin")
def municipal_inventory_update(inventory_id):
    item = _own_inventory_item_or_403(inventory_id)
    new_quantity = request.form.get("quantity", type=int)
    unit = request.form.get("unit", "").strip()
    reason = request.form.get("reason", "").strip() or None

    if new_quantity is None or new_quantity < 0:
        flash("Enter a valid quantity.", "error")
        return redirect(url_for("cswdo.municipal_inventory"))

    # Same rule as the PSWDO side — a source tag only applies to a net increase
    # (incoming stock); a decrease is a manual correction (recount, spoilage).
    delta = new_quantity - item.quantity_available
    source_type, donor_name = "standard", None
    if delta > 0:
        source_type, donor_name, source_error = _parse_stock_source(request.form)
        if source_error:
            flash(source_error, "error")
            return redirect(url_for("cswdo.municipal_inventory"))

    item.quantity_available = new_quantity
    if unit:
        item.unit = unit
    item.updated_by = current_user.user_id

    if delta != 0:
        db.session.add(WarehouseStockLog(
            office_id=item.office_id, item_type=item.item_type, item_name=item.item_name,
            delta=delta, reason=reason, source_type=source_type, donor_name=donor_name,
            updated_by=current_user.user_id,
        ))
    db.session.commit()
    flash(f"Updated {item.item_name} stock.", "success")
    return redirect(url_for("cswdo.municipal_inventory"))


@cswdo_bp.route("/municipal-inventory/<int:inventory_id>/delete", methods=["POST"])
@login_required
@role_required("cswdo_admin", "system_admin")
def municipal_inventory_delete(inventory_id):
    item = _own_inventory_item_or_403(inventory_id)
    if item.item_type == "food_pack":
        flash("Food Packs can't be removed — it's required for allocation and prediction.", "error")
        return redirect(url_for("cswdo.municipal_inventory"))
    name = item.item_name
    db.session.delete(item)
    db.session.commit()
    flash(f"{name} removed.", "success")
    return redirect(url_for("cswdo.municipal_inventory"))


@cswdo_bp.route("/municipal-inventory/movements")
@login_required
@role_required("cswdo_admin", "system_admin")
def municipal_inventory_movements():
    office = _own_office_or_404()
    type_filter = request.args.get("type", "all")
    date_filter = request.args.get("date", "")
    movements = _full_stock_movements([office.office_id], type_filter, date_filter)
    return render_template(
        "cswdo/municipal_inventory_movements.html",
        office=office, movements=movements, type_filter=type_filter, date_filter=date_filter,
    )


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
