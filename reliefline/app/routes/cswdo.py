import csv
import io
import json
import os
import zipfile
from datetime import datetime, date

from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, Response, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from app.extensions import db
from app.utils.decorators import role_required
from app.models.barangay import Barangay
from app.models.office import Office
from app.models.warehouse import WarehouseInventory
from app.models.allocation import AllocationRecord
from app.models.validation import DistributionRecord
from app.models.disaster_event import DisasterEvent
from app.models.barangay_status import BarangayDisasterStatus
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
    ROUTE_PROGRESS_BY_STATUS, PRIORITY_BY_STATUS, DEFAULT_PRIORITY,
    NOTIFICATION_META, DEFAULT_NOTIFICATION_META,
    _item_status, _priority_info, _lgu_burn_rate, _recent_stock_movements,
)

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
    allocation = AllocationRecord.query.get(log.allocation_id) if log.allocation_id else None
    return (
        _cswdo_batch_tracking_link(allocation.batch_id) if allocation and allocation.batch_id
        else url_for("cswdo.relief_requests")
    )


def _cswdo_distribution_link(log):
    distribution = DistributionRecord.query.get(log.distribution_id) if log.distribution_id else None
    batch_id = distribution.allocation.batch_id if distribution and distribution.allocation else None
    return _cswdo_batch_tracking_link(batch_id) or url_for("cswdo.dashboard")


CSWDO_NOTIFICATION_LINK_BUILDERS = {
    "allocation_approved": _cswdo_allocation_link,
    "allocation_rejected": _cswdo_allocation_link,
    "relief_request_submitted": lambda log: _cswdo_batch_tracking_link(log.batch_id) or url_for("cswdo.relief_requests"),
    "distribution_status": _cswdo_distribution_link,
    "distribution_delivered": _cswdo_distribution_link,
    "distribution_receipt_confirmed": _cswdo_distribution_link,
}

CSWDO_NOTIFICATION_CATEGORIES = [
    {"value": "all", "label": "All"},
    {"value": "relief_requests", "label": "Relief Requests"},
    {"value": "distribution", "label": "Distribution"},
]

ALLOWED_UPLOAD_EXTENSIONS = {"pdf", "jpg", "jpeg", "png", "zip", "doc", "docx"}

RR_STATUS_LABELS = {
    "draft": "Draft",
    "pending": "Under Review",
    "approved": "Approved",
    "partially_approved": "Partially Approved",
    "rejected": "Rejected",
}

RR_PRIORITY_LABELS = {"high": "High", "medium": "Medium", "low": "Low"}
RR_TIER_TO_PRIORITY = {"high_priority": "high", "needs_assistance": "high", "monitoring": "medium", "normal": "low"}

cswdo_bp = Blueprint("cswdo", __name__)

DAMAGE_STATUS_LABELS = {
    "pending": "Pending",
    "verified": "Verified",
    "returned": "Returned",
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

    # Relief Request Status — this office's own AllocationRecords, most recent first
    relief_request_rows = []
    if lgu_barangay_ids:
        requests_q = AllocationRecord.query.filter(
            AllocationRecord.barangay_id.in_(lgu_barangay_ids)
        ).order_by(AllocationRecord.allocation_date.desc()).limit(5).all()
        for r in requests_q:
            active_distribution = next(
                (d for d in r.distribution_records if d.dispatch_status != "delivered"), None
            )
            relief_request_rows.append({
                "record": r,
                "ref": f"RR-{r.allocation_date.year}-{r.allocation_id:03d}",
                "status": r.display_status,
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
    notifications = []
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
        notifications = scoped_query.filter(ActivityLog.is_read.is_(False)).order_by(
            ActivityLog.created_at.desc()
        ).limit(3).all()

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
        notifications=notifications,
        dispatch_status_labels=DISPATCH_STATUS_LABELS,
    )


def _damage_assessment_rows(lgu, barangays, primary_event):
    """One row per barangay in this LGU: its latest report for the active
    event (if any) plus a derived priority. Shared by the page view and the
    CSV export so both always agree."""
    reports_by_barangay = {}
    if primary_event and barangays:
        reports = BarangayReport.query.filter(
            BarangayReport.event_id == primary_event.event_id,
            BarangayReport.barangay_id.in_([b.barangay_id for b in barangays]),
            BarangayReport.status != "draft",  # a barangay's own in-progress draft isn't MSWDO's to see yet
        ).all()
        reports_by_barangay = {r.barangay_id: r for r in reports}

    rows = []
    for b in barangays:
        report = reports_by_barangay.get(b.barangay_id)
        status = report.status if report else "no_report"
        rows.append({
            "barangay": b,
            "report": report,
            "status": status,
            "priority": _priority_info(report.flood_level) if report else DEFAULT_PRIORITY,
        })
    return rows


@cswdo_bp.route("/damage-assessment")
@login_required
@role_required("cswdo_admin", "system_admin")
def damage_assessment():
    lgu, lgu_barangays = _own_lgu_barangays()
    tab = request.args.get("tab", "overview")

    active_events = DisasterEvent.query.filter_by(status="active").order_by(
        DisasterEvent.start_date.desc()
    ).all()
    primary_event = active_events[0] if active_events else None

    rows = _damage_assessment_rows(lgu, lgu_barangays, primary_event)

    submitted_rows = [r for r in rows if r["report"]]
    pending_rows = [r for r in rows if r["status"] == "pending"]
    verified_rows = [r for r in rows if r["status"] == "verified"]
    returned_rows = [r for r in rows if r["status"] == "returned"]

    verified_families = sum(r["report"].affected_families for r in verified_rows)
    verified_individuals = sum(r["report"].affected_individuals for r in verified_rows)
    verified_totally_damaged = sum(r["report"].totally_damaged_houses for r in verified_rows)
    verified_partially_damaged = sum(r["report"].partially_damaged_houses for r in verified_rows)
    verified_depths = [
        float(r["report"].flood_depth_m) for r in verified_rows if r["report"].flood_depth_m is not None
    ]
    avg_flood_depth = round(sum(verified_depths) / len(verified_depths), 2) if verified_depths else None

    flood_distribution = {key: 0 for key in PRIORITY_BY_STATUS}
    for r in verified_rows:
        flood_distribution[r["report"].flood_level] = flood_distribution.get(r["report"].flood_level, 0) + 1

    # Search + status filter for the "Barangay Reports" tab only
    search_query = request.args.get("q", "").strip().lower()
    status_filter = request.args.get("status", "all")
    filtered_rows = submitted_rows
    if search_query:
        filtered_rows = [
            r for r in filtered_rows
            if search_query in r["barangay"].barangay_name.lower() or search_query in r["report"].ref.lower()
        ]
    if status_filter != "all":
        filtered_rows = [r for r in filtered_rows if r["status"] == status_filter]

    return render_template(
        "cswdo/damage_assessment.html",
        tab=tab,
        now=datetime.now(),
        lgu=lgu,
        primary_event=primary_event,
        rows=rows,
        submitted_rows=submitted_rows,
        filtered_rows=filtered_rows,
        pending_rows=pending_rows,
        verified_rows=verified_rows,
        returned_rows=returned_rows,
        verified_families=verified_families,
        verified_individuals=verified_individuals,
        verified_totally_damaged=verified_totally_damaged,
        verified_partially_damaged=verified_partially_damaged,
        avg_flood_depth=avg_flood_depth,
        flood_distribution=flood_distribution,
        priority_by_status=PRIORITY_BY_STATUS,
        total_barangays=len(lgu_barangays),
        status_labels=DAMAGE_STATUS_LABELS,
        search_query=search_query,
        status_filter=status_filter,
    )


@cswdo_bp.route("/damage-assessment/<int:report_id>/verify", methods=["POST"])
@login_required
@role_required("cswdo_admin", "system_admin")
def verify_damage_report(report_id):
    report = BarangayReport.query.get_or_404(report_id)
    _assert_own_lgu(report)
    office = current_user.office

    report.status = "verified"
    report.review_remarks = request.form.get("review_remarks", "").strip() or None
    report.reviewed_by = current_user.user_id
    report.reviewed_at = datetime.utcnow()

    # Promote this report into the authoritative BarangayDisasterStatus row,
    # so the dashboard, GIS map, and this page all read the same verified
    # figures for this barangay+event from here on.
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
        actor_id=current_user.user_id, action_type="damage_report_verified",
        description=f"Damage report {report.ref} was verified by {office.office_name}",
        office_id=office.office_id, barangay_id=report.barangay_id,
    ))
    db.session.commit()
    flash(f"Report {report.ref} ({report.barangay.barangay_name}) verified successfully.", "success")
    return redirect(request.referrer or url_for("cswdo.damage_assessment"))


@cswdo_bp.route("/damage-assessment/<int:report_id>/return", methods=["POST"])
@login_required
@role_required("cswdo_admin", "system_admin")
def return_damage_report(report_id):
    report = BarangayReport.query.get_or_404(report_id)
    _assert_own_lgu(report)
    remarks = request.form.get("review_remarks", "").strip()

    if not remarks:
        flash("Enter a reason so the barangay knows what to correct.", "error")
        return redirect(request.referrer or url_for("cswdo.damage_assessment"))

    report.status = "returned"
    report.review_remarks = remarks
    report.reviewed_by = current_user.user_id
    report.reviewed_at = datetime.utcnow()

    office = current_user.office
    db.session.add(ActivityLog(
        actor_id=current_user.user_id, action_type="damage_report_returned",
        description=f"Damage report {report.ref} was returned by {office.office_name if office else 'MSWDO'} — {remarks}",
        office_id=office.office_id if office else None, barangay_id=report.barangay_id,
    ))
    db.session.commit()
    flash(f"Report {report.ref} ({report.barangay.barangay_name}) returned for correction.", "success")
    return redirect(request.referrer or url_for("cswdo.damage_assessment"))


@cswdo_bp.route("/damage-assessment/export")
@login_required
@role_required("cswdo_admin", "system_admin")
def damage_assessment_export():
    lgu, lgu_barangays = _own_lgu_barangays()
    primary_event = DisasterEvent.query.filter_by(status="active").order_by(
        DisasterEvent.start_date.desc()
    ).first()
    rows = _damage_assessment_rows(lgu, lgu_barangays, primary_event)

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow([
        "Barangay", "Status", "Submitted By", "Designation", "Affected Families",
        "Affected Individuals", "Totally Damaged Houses", "Partially Damaged Houses",
        "Flood Level", "Flood Depth (m)", "Last Updated",
    ])
    for r in rows:
        report = r["report"]
        if not report:
            writer.writerow([r["barangay"].barangay_name, "No report submitted", "", "", "", "", "", "", "", "", ""])
            continue
        writer.writerow([
            r["barangay"].barangay_name, DAMAGE_STATUS_LABELS.get(report.status, report.status),
            report.submitted_by_name, report.submitted_by_designation or "",
            report.affected_families, report.affected_individuals,
            report.totally_damaged_houses, report.partially_damaged_houses,
            r["priority"]["label"], report.flood_depth_m if report.flood_depth_m is not None else "",
            (report.reviewed_at or report.submitted_at).strftime("%Y-%m-%d %H:%M"),
        ])

    return Response(
        buffer.getvalue(),
        mimetype="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={(lgu or 'damage_assessment').replace(' ', '_')}_damage_assessment.csv"
        },
    )


# ---------------------------------------------------------------------------
# Relief Requests
# ---------------------------------------------------------------------------

def _eligible_reports(office, event):
    """Verified BarangayReports for this office's LGU + event that don't
    already have an AllocationRecord for this event — i.e. newly verified
    barangays that haven't been requested yet. This is what a new/draft
    request covers; submitting locks it in via AllocationRecord.batch_id."""
    lgu = office.area_covered if office else None
    if not lgu or not event:
        return []
    barangay_ids = [b.barangay_id for b in Barangay.query.filter_by(city_municipality=lgu).all()]
    if not barangay_ids:
        return []

    already_requested = {
        r.barangay_id for r in AllocationRecord.query.filter(
            AllocationRecord.barangay_id.in_(barangay_ids),
            AllocationRecord.event_id == event.event_id,
        ).all()
    }
    reports = BarangayReport.query.filter(
        BarangayReport.barangay_id.in_(barangay_ids),
        BarangayReport.event_id == event.event_id,
        BarangayReport.status == "verified",
    ).all()
    return [r for r in reports if r.barangay_id not in already_requested]


def _model_predictions(reports):
    """{barangay_id: predicted_quantity} — 0 where the model has nothing to
    say (untrained model or missing profile fields), never fabricated."""
    return {r.barangay_id: (ml_predict.predict_quantity(r.barangay) or 0) for r in reports}


def _suggested_priority(reports):
    if not reports:
        return "medium"
    worst_rank = max(_priority_info(r.flood_level)["rank"] for r in reports)
    worst_tier_key = next((k for k, v in PRIORITY_BY_STATUS.items() if v["rank"] == worst_rank), "monitoring")
    return RR_TIER_TO_PRIORITY.get(worst_tier_key, "medium")


def _own_batch_or_404(batch_id):
    batch = ReliefRequestBatch.query.get_or_404(batch_id)
    office = current_user.office
    if not office or batch.office_id != office.office_id:
        abort(403)
    return batch


def _save_batch_uploads(batch):
    """Same upload convention as pswdo.confirm_delivery — validated extension,
    secure_filename, one folder per record. Skipped fields with no file
    selected are left untouched (so editing a draft doesn't wipe prior uploads)."""
    upload_dir = os.path.join(current_app.root_path, "static", "uploads", "relief_requests", str(batch.batch_id))

    def _save_one(field_name):
        f = request.files.get(field_name)
        if not f or not f.filename:
            return None
        ext = f.filename.rsplit(".", 1)[-1].lower() if "." in f.filename else ""
        if ext not in ALLOWED_UPLOAD_EXTENSIONS:
            return None
        os.makedirs(upload_dir, exist_ok=True)
        safe_name = secure_filename(f.filename)
        f.save(os.path.join(upload_dir, safe_name))
        return safe_name

    def _save_many(field_name):
        files = [f for f in request.files.getlist(field_name) if f and f.filename]
        if not files:
            return None
        os.makedirs(upload_dir, exist_ok=True)
        saved = []
        for f in files:
            ext = f.filename.rsplit(".", 1)[-1].lower() if "." in f.filename else ""
            if ext not in ALLOWED_UPLOAD_EXTENSIONS:
                continue
            safe_name = secure_filename(f.filename)
            f.save(os.path.join(upload_dir, safe_name))
            saved.append(safe_name)
        return ",".join(saved) if saved else None

    damage_report = _save_one("damage_report_file")
    if damage_report:
        batch.damage_report_file = damage_report
    photos = _save_many("photo_files")
    if photos:
        batch.photo_files = photos
    other = _save_many("other_files")
    if other:
        batch.other_files = other


def _apply_batch_form(batch):
    batch.requested_food_packs = request.form.get("food_packs", type=int) or 0
    priority = request.form.get("priority", "medium")
    batch.priority = priority if priority in RR_PRIORITY_LABELS else "medium"
    batch.reason = request.form.get("reason", "").strip() or None
    batch.remarks = request.form.get("remarks", "").strip() or None


RR_STEP_DEFS = [
    ("draft", "Draft"),
    ("submitted", "Submitted"),
    ("review", "Under Review"),
    ("approved", "Approved"),
    ("preparing", "Preparing Distribution"),
    ("in_transit", "In Transit"),
    ("delivered", "Delivered"),
]


def _fulfillment_stage(distributions):
    """None (no distribution scheduled yet) | 'preparing' | 'in_transit' | 'delivered'."""
    if not distributions:
        return None
    statuses = [d.dispatch_status for d in distributions]
    if all(s == "delivered" for s in statuses):
        return "delivered"
    if any(s == "in_transit" for s in statuses):
        return "in_transit"
    return "preparing"


def _batch_stepper(batch, distributions):
    if batch.is_draft:
        return [{"key": "draft", "label": "Draft", "state": "current", "time": batch.created_at}]

    status = batch.display_status
    rejected = status == "rejected"
    stage_index = {"preparing": 4, "in_transit": 5, "delivered": 6}.get(_fulfillment_stage(distributions), 3)
    reached = 2 if status == "pending" else stage_index  # index of the furthest-reached step

    steps = []
    for i, (key, label) in enumerate(RR_STEP_DEFS):
        if rejected and i == 2:
            state = "rejected"
        elif rejected and i > 2:
            state = "upcoming"
        elif i < reached:
            state = "done"
        elif i == reached:
            state = "done" if key == "delivered" else "current"
        else:
            state = "upcoming"
        time_value = {"draft": batch.created_at, "submitted": batch.submitted_at}.get(key)
        steps.append({"key": key, "label": label, "state": state, "time": time_value})
    return steps


def _batch_view(batch):
    """Everything the Overview/History tables and the view modal need for one
    batch, computed fresh so it can never drift from the underlying records."""
    children = batch.allocation_records
    covered_barangays = [c.barangay for c in children]
    fulfilling_offices = {c.fulfilling_office.office_name for c in children if c.fulfilling_office}
    distributions = DistributionRecord.query.filter(
        DistributionRecord.allocation_id.in_([c.allocation_id for c in children])
    ).all() if children else []

    warehouse_label = "Not yet assigned"
    if len(fulfilling_offices) == 1:
        warehouse_label = next(iter(fulfilling_offices))
    elif len(fulfilling_offices) > 1:
        warehouse_label = "Multiple warehouses"

    dispatch_date = min((d.distribution_date for d in distributions), default=None)
    eta_times = [d.expected_arrival_time for d in distributions if d.expected_arrival_time]

    reports_by_barangay = {}
    if children:
        reports_by_barangay = {
            r.barangay_id: r for r in BarangayReport.query.filter(
                BarangayReport.barangay_id.in_([c.barangay_id for c in children]),
                BarangayReport.event_id == batch.event_id,
                BarangayReport.status == "verified",
            ).all()
        }

    status = batch.display_status
    rejection_reasons = [c.rejection_reason for c in children if c.rejection_reason]
    if status == "draft":
        current_handler, expected_review, latest_update = "—", "—", "Not yet submitted"
    elif status == "rejected":
        current_handler, expected_review = "PSWDO Office", "—"
        latest_update = rejection_reasons[0] if rejection_reasons else "Rejected by PSWDO"
    elif status == "pending":
        current_handler, expected_review, latest_update = "PSWDO Office", "Within 2 days", "Waiting for PSWDO approval"
    else:  # approved / partially_approved
        current_handler = "Warehouse / Logistics" if distributions else "PSWDO Office"
        expected_review = "Completed"
        latest_update = f"{warehouse_label} assigned" if warehouse_label != "Not yet assigned" else "Approved by PSWDO"

    return {
        "batch": batch,
        "status": status,
        "status_label": RR_STATUS_LABELS.get(status, status),
        "priority_label": RR_PRIORITY_LABELS.get(batch.priority, batch.priority),
        "children": children,
        "covered_barangays": covered_barangays,
        "affected_families": sum(r.affected_families for r in reports_by_barangay.values()),
        "affected_individuals": sum(r.affected_individuals for r in reports_by_barangay.values()),
        "warehouse_label": warehouse_label,
        "dispatch_date": dispatch_date,
        "eta_label": max(eta_times).strftime("%I:%M %p") if eta_times else None,
        "distributions": distributions,
        "rejection_reasons": rejection_reasons,
        "current_handler": current_handler,
        "expected_review": expected_review,
        "latest_update": latest_update,
        "stepper": _batch_stepper(batch, distributions),
    }


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

    office_batches = ReliefRequestBatch.query.filter_by(office_id=office.office_id).order_by(
        ReliefRequestBatch.created_at.desc()
    ).all() if office else []

    draft_batches = [b for b in office_batches if b.is_draft]
    submitted_batches = [b for b in office_batches if not b.is_draft]

    ctx = {
        "tab": tab, "lgu": lgu, "office": office, "primary_event": primary_event,
        "status_labels": RR_STATUS_LABELS, "priority_labels": RR_PRIORITY_LABELS,
        "draft_count": len(draft_batches),
    }

    if tab == "create":
        draft_id = request.args.get("draft_id", type=int)
        editing_draft = _own_batch_or_404(draft_id) if draft_id else None
        if editing_draft and not editing_draft.is_draft:
            abort(404)

        eligible = _eligible_reports(office, primary_event)
        predictions = _model_predictions(eligible)
        model_total = sum(predictions.values())

        ctx.update({
            "editing_draft": editing_draft,
            "eligible_reports": eligible,
            "verified_count": len(eligible),
            "affected_families": sum(r.affected_families for r in eligible),
            "affected_individuals": sum(r.affected_individuals for r in eligible),
            "model_total": model_total,
            "food_packs_value": editing_draft.requested_food_packs if editing_draft else model_total,
            "priority_value": editing_draft.priority if editing_draft else _suggested_priority(eligible),
            "reason_value": editing_draft.reason if editing_draft else "",
            "remarks_value": editing_draft.remarks if editing_draft else "",
            "today": date.today(),
        })

    elif tab == "tracking":
        selected_id = request.args.get("batch_id", type=int)
        selected = None
        if selected_id:
            selected = next((b for b in submitted_batches if b.batch_id == selected_id), None)
        if not selected and submitted_batches:
            selected = submitted_batches[0]
        ctx.update({
            "trackable_batches": submitted_batches[:12],
            "selected": _batch_view(selected) if selected else None,
        })

    elif tab == "history":
        search_query = request.args.get("q", "").strip().lower()
        event_filter = request.args.get("event_id", type=int)

        history_batches = [b for b in submitted_batches if b.event and b.event.status == "ended"]
        if event_filter:
            history_batches = [b for b in history_batches if b.event_id == event_filter]
        if search_query:
            history_batches = [
                b for b in history_batches
                if search_query in b.ref.lower() or (b.event and search_query in b.event.event_name.lower())
            ]
        ended_events = DisasterEvent.query.filter_by(status="ended").order_by(DisasterEvent.start_date.desc()).all()

        ctx.update({
            "history_rows": [_batch_view(b) for b in history_batches],
            "ended_events": ended_events,
            "event_filter": event_filter,
            "search_query": search_query,
        })

    else:  # overview
        search_query = request.args.get("q", "").strip().lower()
        status_filter = request.args.get("status", "all")

        rows = [_batch_view(b) for b in office_batches]
        if search_query:
            rows = [r for r in rows if search_query in r["batch"].ref.lower()]
        if status_filter != "all":
            rows = [r for r in rows if r["status"] == status_filter]

        per_page = 10
        total_filtered = len(rows)
        total_pages = max((total_filtered + per_page - 1) // per_page, 1)
        page = max(request.args.get("page", 1, type=int), 1)
        page = min(page, total_pages)
        page_rows = rows[(page - 1) * per_page: page * per_page]

        ctx.update({
            "rows": page_rows,
            "total_requests": len(submitted_batches),
            "pending_count": len([b for b in submitted_batches if b.display_status == "pending"]),
            "approved_count": len([b for b in submitted_batches if b.display_status in ("approved", "partially_approved")]),
            "rejected_count": len([b for b in submitted_batches if b.display_status == "rejected"]),
            "search_query": search_query,
            "status_filter": status_filter,
            "page": page,
            "total_pages": total_pages,
            "total_filtered": total_filtered,
        })

    return render_template("cswdo/relief_requests.html", **ctx)


@cswdo_bp.route("/relief-requests/save-draft", methods=["POST"])
@login_required
@role_required("cswdo_admin", "system_admin")
def relief_request_save_draft():
    office = current_user.office
    primary_event = DisasterEvent.query.filter_by(status="active").order_by(
        DisasterEvent.start_date.desc()
    ).first()
    if not office or not primary_event:
        flash("No active disaster event to file a request against.", "error")
        return redirect(url_for("cswdo.relief_requests"))

    draft_id = request.form.get("draft_id", type=int)
    batch = _own_batch_or_404(draft_id) if draft_id else None
    if batch and not batch.is_draft:
        abort(404)

    is_new = batch is None
    if is_new:
        batch = ReliefRequestBatch(office_id=office.office_id, event_id=primary_event.event_id,
                                    created_by=current_user.user_id)
        db.session.add(batch)

    _apply_batch_form(batch)
    db.session.flush()
    _save_batch_uploads(batch)
    db.session.commit()

    flash(f"Saved as draft ({batch.ref}).", "success")
    return redirect(url_for("cswdo.relief_requests", tab="create", draft_id=batch.batch_id))


@cswdo_bp.route("/relief-requests/submit", methods=["POST"])
@login_required
@role_required("cswdo_admin", "system_admin")
def relief_request_submit():
    office = current_user.office
    primary_event = DisasterEvent.query.filter_by(status="active").order_by(
        DisasterEvent.start_date.desc()
    ).first()
    if not office or not primary_event:
        flash("No active disaster event to file a request against.", "error")
        return redirect(url_for("cswdo.relief_requests"))

    draft_id = request.form.get("draft_id", type=int)
    batch = _own_batch_or_404(draft_id) if draft_id else None
    if batch and not batch.is_draft:
        abort(404)

    is_new = batch is None
    if is_new:
        batch = ReliefRequestBatch(office_id=office.office_id, event_id=primary_event.event_id,
                                    created_by=current_user.user_id)
        db.session.add(batch)

    _apply_batch_form(batch)

    if not batch.requested_food_packs or batch.requested_food_packs <= 0:
        flash("Enter the number of food packs to request.", "error")
        db.session.rollback()
        return redirect(url_for("cswdo.relief_requests", tab="create", draft_id=batch.batch_id if not is_new else None))
    if not batch.reason:
        flash("Explain why this relief request is needed.", "error")
        db.session.rollback()
        return redirect(url_for("cswdo.relief_requests", tab="create", draft_id=batch.batch_id if not is_new else None))

    eligible = _eligible_reports(office, primary_event)
    if not eligible:
        flash("No newly verified barangays are ready to request yet — verify barangay reports in Damage Assessment first.", "error")
        db.session.rollback()
        return redirect(url_for("cswdo.relief_requests", tab="create", draft_id=batch.batch_id if not is_new else None))

    db.session.flush()
    _save_batch_uploads(batch)

    predictions = _model_predictions(eligible)
    model_total = sum(predictions.values())
    today = date.today()

    for report in eligible:
        model_qty = predictions[report.barangay_id]
        if model_total > 0:
            scaled_qty = round(model_qty / model_total * batch.requested_food_packs)
        else:
            scaled_qty = round(batch.requested_food_packs / len(eligible))
        db.session.add(AllocationRecord(
            barangay_id=report.barangay_id, office_id=office.office_id,
            predicted_quantity=max(scaled_qty, 0), allocated_quantity=0,
            # Snapshot of the model's "Historical Allocation" predictor at request
            # time (see app.ml.train.historical_allocation_for) — kept on the row
            # itself as an audit trail, separate from how the model recomputes it
            # fresh from AllocationRecord history on every future training run.
            historical_allocation=ml_predict.historical_allocation_for(report.barangay_id),
            allocation_date=today, event_id=primary_event.event_id,
            status="pending", created_by=current_user.user_id, batch_id=batch.batch_id,
        ))

    batch.submitted_at = datetime.utcnow()
    db.session.add(ActivityLog(
        actor_id=current_user.user_id, action_type="relief_request_submitted",
        description=f"{office.office_name} submitted {batch.ref} to PSWDO — {batch.requested_food_packs:,} food packs across {len(eligible)} barangays",
        office_id=office.office_id, batch_id=batch.batch_id,
    ))
    db.session.commit()

    flash(f"{batch.ref} submitted to PSWDO.", "success")
    return redirect(url_for("cswdo.relief_requests", tab="tracking", batch_id=batch.batch_id))


@cswdo_bp.route("/relief-requests/export")
@login_required
@role_required("cswdo_admin", "system_admin")
def relief_request_export():
    office = current_user.office
    batches = []
    if office:
        batches = ReliefRequestBatch.query.filter(
            ReliefRequestBatch.office_id == office.office_id,
            ReliefRequestBatch.submitted_at.isnot(None),
        ).order_by(ReliefRequestBatch.submitted_at.desc()).all()

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["Request ID", "Typhoon Event", "Requested Packs", "Priority", "Barangays", "Status", "Date"])
    for b in batches:
        view = _batch_view(b)
        writer.writerow([
            b.ref, b.event.event_name if b.event else "", b.requested_food_packs,
            RR_PRIORITY_LABELS.get(b.priority, b.priority),
            ", ".join(bg.barangay_name for bg in view["covered_barangays"]),
            RR_STATUS_LABELS.get(view["status"], view["status"]),
            b.submitted_at.strftime("%Y-%m-%d"),
        ])

    return Response(
        buffer.getvalue(), mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={(office.area_covered if office else 'relief').replace(' ', '_')}_relief_requests.csv"},
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
    status_filter = request.args.get("status", "all")

    if not filters:
        return render_template(
            "cswdo/notifications.html", items=[], unread_count=0, total_count=0,
            total_filtered=0, category_filter=category_filter, status_filter=status_filter,
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
    if status_filter == "unread":
        query = query.filter(ActivityLog.is_read.is_(False))

    unread_count = ActivityLog.query.filter(scope, ActivityLog.is_read.is_(False)).count()
    total_count = ActivityLog.query.filter(scope).count()

    per_page = 15
    all_matching = query.order_by(ActivityLog.created_at.desc()).all()
    total_filtered = len(all_matching)
    total_pages = max((total_filtered + per_page - 1) // per_page, 1)
    page = max(request.args.get("page", 1, type=int), 1)
    page = min(page, total_pages)
    page_items = [_cswdo_notification_view(log) for log in all_matching[(page - 1) * per_page: page * per_page]]

    return render_template(
        "cswdo/notifications.html",
        items=page_items, unread_count=unread_count, total_count=total_count,
        total_filtered=total_filtered, category_filter=category_filter, status_filter=status_filter,
        categories=CSWDO_NOTIFICATION_CATEGORIES, page=page, total_pages=total_pages, lgu=lgu,
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


@cswdo_bp.route("/notifications/mark-all-read", methods=["POST"])
@login_required
@role_required("cswdo_admin", "system_admin")
def mark_all_notifications_read():
    filters = _own_activity_filters()
    if filters:
        known_types = list(NOTIFICATION_META.keys())
        ActivityLog.query.filter(
            db.or_(*filters), ActivityLog.action_type.in_(known_types), ActivityLog.is_read.is_(False)
        ).update({"is_read": True}, synchronize_session=False)
        db.session.commit()
    flash("All notifications marked as read.", "success")
    return redirect(request.referrer or url_for("cswdo.notifications"))


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
# Municipal Inventory (read-only) — per Table 10 the CSWDO/MSWDO role is
# "inventory monitoring," not management; every add/update/transfer action
# stays PSWDO-only (app/routes/pswdo.py). This page is the dashboard's
# Municipal Inventory panel's "View Details" destination, showing this
# office's own stock in more depth without exposing any write action.
# ---------------------------------------------------------------------------

@cswdo_bp.route("/municipal-inventory")
@login_required
@role_required("cswdo_admin", "system_admin")
def municipal_inventory():
    office = current_user.office
    if not office:
        abort(404)

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

    items = WarehouseInventory.query.filter_by(office_id=office.office_id).order_by(
        WarehouseInventory.item_name
    ).all()
    inventory_summary = [
        {"item": item, "status": _item_status(item.quantity_available, item.min_stock_level)}
        for item in items
    ]

    movements = _recent_stock_movements([office.office_id], limit=6)

    return render_template(
        "cswdo/municipal_inventory.html",
        office=office, food_pack_qty=food_pack_qty, capacity=capacity, pct=pct, health=health,
        burn=burn, days_remaining=days_remaining, inventory_summary=inventory_summary,
        movements=movements,
    )
