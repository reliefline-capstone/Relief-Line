import csv
import io
import json
import os
import zipfile
from datetime import date, datetime

from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, Response, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from app.extensions import db
from app.utils.decorators import role_required
from app.models.office import Office
from app.models.disaster_event import DisasterEvent
from app.models.barangay_status import BarangayDisasterStatus
from app.models.barangay_report import BarangayReport
from app.models.allocation import AllocationRecord
from app.models.validation import DistributionRecord
from app.models.activity_log import ActivityLog
from app.models.user import User

# Reused from the PSWDO route module so a status label, priority tier, or
# notification icon never drifts between the PSWDO/CSWDO screens and this
# barangay-facing one — see app/routes/pswdo.py for the source of truth.
from app.routes.pswdo import (
    DISPATCH_STATUS_LABELS, ROUTE_PROGRESS_BY_STATUS, PRIORITY_BY_STATUS,
    DEFAULT_PRIORITY, NOTIFICATION_META, DEFAULT_NOTIFICATION_META, _priority_info,
)

barangay_bp = Blueprint("barangay", __name__)

ALLOWED_UPLOAD_EXTENSIONS = {"pdf", "jpg", "jpeg", "png"}

REPORT_STATUS_LABELS = {
    "draft": "Draft",
    "pending": "Submitted",
    "verified": "Verified",
    "returned": "Returned",
}

# Disaster Info step — sub-classification of the active typhoon event, per
# the manuscript's Scope and Limitations list of typhoon-related phenomena
# ("flash floods, storm surge, and strong winds that occur as direct
# consequences of a typhoon event").
DISASTER_TYPE_OPTIONS = ["Typhoon/Flood", "Flash Flood", "Storm Surge", "Strong Winds"]

# Severity Level cards on the Disaster Info step — same flood_level values as
# PRIORITY_BY_STATUS (app/routes/pswdo.py) so the tier driving this report's
# eventual priority is the exact same vocabulary used on the dashboard/GIS map,
# just with wording suited to a flood-depth picker instead of a status badge.
SEVERITY_CARDS = [
    {"value": "high_priority", "label": "Critical", "detail": ">2m · Extreme danger", "dot": "critical"},
    {"value": "needs_assistance", "label": "High", "detail": "1-2m · Dangerous", "dot": "high"},
    {"value": "monitoring", "label": "Moderate", "detail": "0.5-1m · Caution", "dot": "medium"},
    {"value": "normal", "label": "Low", "detail": "<0.5m · Minor", "dot": "low"},
]


def _own_barangay_or_404():
    barangay = current_user.barangay
    if not barangay:
        abort(404)
    return barangay


def _active_event():
    return DisasterEvent.query.filter_by(status="active").order_by(DisasterEvent.start_date.desc()).first()


def _own_activity_scope():
    """This barangay's own ActivityLog rows — the single source of truth the
    dashboard's Active Alerts panel, the full Notifications page, and its
    mark-as-read actions all read from, so all three always agree.

    Also restricted to NOTIFICATION_META's known operational action_types
    (same allowlist as app.routes.pswdo.notifications) — barangay_id is
    already None on every System Administration row (logins, user/office/
    barangay management), so this is belt-and-suspenders rather than fixing
    a live leak, but keeps the exclusion explicit instead of incidental."""
    barangay = current_user.barangay
    if not barangay:
        return None
    known_types = list(NOTIFICATION_META.keys())
    return db.and_(ActivityLog.barangay_id == barangay.barangay_id, ActivityLog.action_type.in_(known_types))


def _assert_own_activity(log):
    barangay = current_user.barangay
    if not barangay or log.barangay_id != barangay.barangay_id:
        abort(403)


def _damage_report_notification_link(log):
    # No report_id FK on ActivityLog, so — same fallback pattern as PSWDO's
    # _relief_request_submitted_link when it can't resolve an exact record —
    # this opens the Damage Report page in general rather than one report.
    return url_for("barangay.damage_report")


def _relief_monitoring_notification_link(log):
    # Allocation/distribution notifications all resolve to this barangay's
    # single Relief Monitoring list (no per-record detail route exists yet).
    return url_for("barangay.relief_monitoring")


# Mirrors app.routes.pswdo.NOTIFICATION_LINK_BUILDERS so every notification
# here is clickable the same way PSWDO/CSWDO notifications are, instead of
# only exposing a "Mark as Read" action.
NOTIFICATION_LINK_BUILDERS = {
    "damage_report_submitted": _damage_report_notification_link,
    "damage_report_verified": _damage_report_notification_link,
    "damage_report_returned": _damage_report_notification_link,
    "allocation_approved": _relief_monitoring_notification_link,
    "allocation_rejected": _relief_monitoring_notification_link,
    "distribution_status": _relief_monitoring_notification_link,
    "distribution_delivered": _relief_monitoring_notification_link,
    "distribution_receipt_confirmed": _relief_monitoring_notification_link,
}


def _notification_view(log):
    meta = NOTIFICATION_META.get(log.action_type, DEFAULT_NOTIFICATION_META)
    link_fn = NOTIFICATION_LINK_BUILDERS.get(log.action_type)
    return {
        "log": log, "icon": meta["icon"], "color": meta["color"],
        "category": meta["category"], "category_label": meta["category_label"],
        "link": link_fn(log) if link_fn else None,
    }


def _own_reports_all(barangay_id):
    """Every report this barangay has ever started, including drafts —
    what the Damage Report page's own Dashboard/History tabs read from."""
    return BarangayReport.query.filter_by(barangay_id=barangay_id).order_by(
        BarangayReport.created_at.desc()
    ).all()


def _own_submitted_reports(barangay_id):
    """Reports this barangay has actually sent to MSWDO/CSWDO (excludes
    drafts still being filled out) — used anywhere outside the Damage Report
    page itself, so an in-progress draft never shows up as if it were real,
    reviewable activity (main Dashboard, Reports, Affected Families, CSV export)."""
    return BarangayReport.query.filter(
        BarangayReport.barangay_id == barangay_id,
        BarangayReport.status != "draft",
    ).order_by(BarangayReport.created_at.desc()).all()


def _open_report_for_event(barangay_id, event_id):
    """The one report a barangay is still actively working on for this
    event — a draft in progress, freshly submitted (pending), or bounced
    back for correction (returned). Mirrors the one-active-report-per-
    barangay-per-event assumption the CSWDO Damage Assessment screen already
    relies on (app.routes.cswdo._damage_assessment_rows)."""
    if not event_id:
        return None
    return BarangayReport.query.filter(
        BarangayReport.barangay_id == barangay_id,
        BarangayReport.event_id == event_id,
        BarangayReport.status.in_(("draft", "pending", "returned")),
    ).order_by(BarangayReport.created_at.desc()).first()


def _get_own_report_or_404(report_id):
    report = BarangayReport.query.get_or_404(report_id)
    barangay = current_user.barangay
    if not barangay or report.barangay_id != barangay.barangay_id:
        abort(403)
    return report


@barangay_bp.route("/dashboard")
@login_required
@role_required("barangay_user")
def dashboard():
    now = datetime.now()
    barangay = _own_barangay_or_404()

    active_events = DisasterEvent.query.filter_by(status="active").order_by(
        DisasterEvent.start_date.desc()
    ).all()
    primary_event = active_events[0] if active_events else None

    # Affected families — this barangay's own current status for the active event
    status_row = None
    if primary_event:
        status_row = BarangayDisasterStatus.query.filter_by(
            barangay_id=barangay.barangay_id, event_id=primary_event.event_id
        ).first()
    affected_families = status_row.affected_families if status_row else 0
    priority = _priority_info(status_row.status if status_row else "normal")

    # My damage reports — needing attention (submitted/returned) vs. all-time count
    my_reports = _own_submitted_reports(barangay.barangay_id)
    pending_reports = [r for r in my_reports if r.status in ("pending", "returned")]
    returned_reports = [r for r in my_reports if r.status == "returned"]
    recent_reports = my_reports[:2]

    # Food packs allocated to this barangay for the active event
    food_packs_allocated = 0
    if primary_event:
        food_packs_allocated = sum(
            a.allocated_quantity for a in AllocationRecord.query.filter_by(
                barangay_id=barangay.barangay_id, event_id=primary_event.event_id,
            ).all()
        )

    # Relief deliveries — this barangay's own distributions, most recent first
    my_distributions = DistributionRecord.query.filter_by(barangay_id=barangay.barangay_id).order_by(
        DistributionRecord.distribution_date.desc()
    ).limit(5).all()
    in_transit_count = len([d for d in my_distributions if d.dispatch_status == "in_transit"])
    awaiting_confirmation = [
        d for d in my_distributions if d.dispatch_status == "in_transit" and d.status == "pending"
    ]

    # Active alerts — this barangay's own recent activity, read or unread
    recent_alerts = []
    scope = _own_activity_scope()
    if scope is not None:
        recent_alerts = ActivityLog.query.filter(scope).order_by(
            ActivityLog.created_at.desc()
        ).limit(4).all()

    return render_template(
        "barangay/dashboard.html",
        now=now,
        barangay=barangay,
        primary_event=primary_event,
        affected_families=affected_families,
        priority=priority,
        pending_reports_count=len(pending_reports),
        returned_reports_count=len(returned_reports),
        recent_reports=recent_reports,
        food_packs_allocated=food_packs_allocated,
        my_distributions=my_distributions[:2],
        in_transit_count=in_transit_count,
        awaiting_confirmation=awaiting_confirmation,
        recent_alerts=[_notification_view(log) for log in recent_alerts],
        dispatch_status_labels=DISPATCH_STATUS_LABELS,
        report_status_labels=REPORT_STATUS_LABELS,
    )


# ---------------------------------------------------------------------------
# Damage Report
# ---------------------------------------------------------------------------

def _save_report_upload(report):
    files = [f for f in request.files.getlist("photo_files") if f and f.filename]
    if not files:
        return
    upload_dir = os.path.join(current_app.root_path, "static", "uploads", "barangay_reports", str(report.report_id))
    os.makedirs(upload_dir, exist_ok=True)
    saved = []
    for f in files:
        ext = f.filename.rsplit(".", 1)[-1].lower() if "." in f.filename else ""
        if ext not in ALLOWED_UPLOAD_EXTENSIONS:
            continue
        safe_name = secure_filename(f.filename)
        f.save(os.path.join(upload_dir, safe_name))
        saved.append(safe_name)
    if saved:
        report.photo_paths = ",".join(saved)


@barangay_bp.route("/damage-report")
@login_required
@role_required("barangay_user")
def damage_report():
    barangay = _own_barangay_or_404()
    primary_event = _active_event()
    tab = request.args.get("tab", "dashboard")

    all_reports = _own_reports_all(barangay.barangay_id)
    ctx = {
        "barangay": barangay, "primary_event": primary_event, "tab": tab,
        "status_labels": REPORT_STATUS_LABELS,
        "total_count": len(all_reports),
        "draft_count": len([r for r in all_reports if r.status == "draft"]),
    }

    if tab == "history":
        search_query = request.args.get("q", "").strip().lower()
        verified_reports = [r for r in all_reports if r.status == "verified"]
        if search_query:
            verified_reports = [
                r for r in verified_reports
                if search_query in r.ref.lower() or search_query in r.barangay.barangay_name.lower()
            ]
        ctx.update({
            "verified_reports": verified_reports,
            "search_query": search_query,
            "pending_count": len([r for r in all_reports if r.status == "pending"]),
            "verified_count": len(verified_reports),
            "returned_count": len([r for r in all_reports if r.status == "returned"]),
        })
    else:
        # Dashboard tab — this event's own open items (submitted/returned);
        # a verified report for this event has nothing left to act on, so it
        # moves to History instead of cluttering this table (see class docs).
        event_reports = [r for r in all_reports if primary_event and r.event_id == primary_event.event_id]
        # Drafts included here too — otherwise a saved draft would only ever
        # show up as a number on the stat card with no way to click back into it.
        open_reports = [r for r in event_reports if r.status in ("draft", "pending", "returned")]
        # Computed off the unfiltered set so the "returned" banner keeps showing
        # even while the table below is filtered down to a different status.
        returned_reports = [r for r in open_reports if r.status == "returned"]

        search_query = request.args.get("q", "").strip().lower()
        status_filter = request.args.get("status", "all")
        filtered_open_reports = open_reports
        if status_filter != "all":
            filtered_open_reports = [r for r in filtered_open_reports if r.status == status_filter]
        if search_query:
            filtered_open_reports = [r for r in filtered_open_reports if search_query in r.ref.lower()]

        open_rows = [{"report": r, "priority": _priority_info(r.flood_level)} for r in filtered_open_reports]

        ctx.update({
            "open_rows": open_rows,
            "pending_count": len([r for r in event_reports if r.status == "pending"]),
            "verified_count": len([r for r in event_reports if r.status == "verified"]),
            "returned_count": len([r for r in event_reports if r.status == "returned"]),
            "returned_reports": returned_reports,
            "search_query": search_query,
            "status_filter": status_filter,
        })

    return render_template("barangay/damage_report.html", **ctx)


@barangay_bp.route("/damage-report/export-open")
@login_required
@role_required("barangay_user")
def damage_report_export_open():
    """CSV export for the Dashboard tab's own toolbar — same idea as
    damage_report_export, but for this event's still-open (draft/pending/
    returned) reports instead of the History tab's verified ones."""
    barangay = _own_barangay_or_404()
    primary_event = _active_event()
    all_reports = _own_reports_all(barangay.barangay_id)
    event_reports = [r for r in all_reports if primary_event and r.event_id == primary_event.event_id]
    open_reports = [r for r in event_reports if r.status in ("draft", "pending", "returned")]

    search_query = request.args.get("q", "").strip().lower()
    status_filter = request.args.get("status", "all")
    if status_filter != "all":
        open_reports = [r for r in open_reports if r.status == status_filter]
    if search_query:
        open_reports = [r for r in open_reports if search_query in r.ref.lower()]

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["Report Ref", "Event", "Status", "Flood Level", "Submitted At"])
    for r in open_reports:
        writer.writerow([
            r.ref, r.event.event_name if r.event else "", REPORT_STATUS_LABELS.get(r.status, r.status),
            PRIORITY_BY_STATUS.get(r.flood_level, DEFAULT_PRIORITY)["label"],
            r.submitted_at.strftime("%Y-%m-%d %H:%M") if r.submitted_at else "",
        ])

    return Response(
        buffer.getvalue(), mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={barangay.barangay_name.replace(' ', '_')}_open_reports.csv"},
    )


@barangay_bp.route("/damage-report/export")
@login_required
@role_required("barangay_user")
def damage_report_export():
    barangay = _own_barangay_or_404()
    verified_reports = [r for r in _own_reports_all(barangay.barangay_id) if r.status == "verified"]

    search_query = request.args.get("q", "").strip().lower()
    if search_query:
        verified_reports = [
            r for r in verified_reports
            if search_query in r.ref.lower() or search_query in r.barangay.barangay_name.lower()
        ]

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["Report Ref", "Event", "Affected Families", "Affected Individuals",
                      "Flood Level", "Verified By", "Submitted At"])
    for r in verified_reports:
        writer.writerow([
            r.ref, r.event.event_name if r.event else "", r.affected_families, r.affected_individuals,
            PRIORITY_BY_STATUS.get(r.flood_level, DEFAULT_PRIORITY)["label"],
            r.reviewed_by_user.name if r.reviewed_by_user else "",
            r.submitted_at.strftime("%Y-%m-%d %H:%M") if r.submitted_at else "",
        ])

    return Response(
        buffer.getvalue(), mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={barangay.barangay_name.replace(' ', '_')}_report_history.csv"},
    )


@barangay_bp.route("/damage-report/<int:report_id>/view")
@login_required
@role_required("barangay_user")
def view_damage_report(report_id):
    report = _get_own_report_or_404(report_id)
    return render_template(
        "barangay/damage_report_view.html",
        report=report, barangay=report.barangay,
        status_labels=REPORT_STATUS_LABELS, priority_by_status=PRIORITY_BY_STATUS,
    )


def _report_form_context(barangay, report=None):
    active_events = DisasterEvent.query.filter_by(status="active").order_by(
        DisasterEvent.start_date.desc()
    ).all()
    return {
        "barangay": barangay,
        "report": report,
        "active_events": active_events,
        "disaster_type_options": DISASTER_TYPE_OPTIONS,
        "severity_cards": SEVERITY_CARDS,
        "today": date.today(),
    }


@barangay_bp.route("/damage-report/new")
@login_required
@role_required("barangay_user")
def new_damage_report():
    barangay = _own_barangay_or_404()
    return render_template("barangay/damage_report_form.html", **_report_form_context(barangay))


@barangay_bp.route("/damage-report/<int:report_id>/edit")
@login_required
@role_required("barangay_user")
def edit_damage_report(report_id):
    report = _get_own_report_or_404(report_id)
    if report.status not in ("draft", "pending", "returned"):
        flash("Verified reports are locked and can no longer be edited.", "error")
        return redirect(url_for("barangay.view_damage_report", report_id=report.report_id))
    return render_template("barangay/damage_report_form.html", **_report_form_context(report.barangay, report))


def _apply_report_form(report):
    report.event_id = request.form.get("event_id", type=int) or report.event_id
    disaster_type = request.form.get("disaster_type", "")
    report.disaster_type = disaster_type if disaster_type in DISASTER_TYPE_OPTIONS else DISASTER_TYPE_OPTIONS[0]

    incident_date = request.form.get("incident_date", "")
    if incident_date:
        try:
            report.incident_date = datetime.strptime(incident_date, "%Y-%m-%d").date()
        except ValueError:
            pass
    incident_time = request.form.get("incident_time", "")
    if incident_time:
        try:
            report.incident_time = datetime.strptime(incident_time, "%H:%M").time()
        except ValueError:
            pass

    report.flood_depth_m = request.form.get("flood_depth_m", type=float)
    flood_level = request.form.get("flood_level", "normal")
    report.flood_level = flood_level if flood_level in PRIORITY_BY_STATUS else "normal"

    report.affected_families = request.form.get("affected_families", type=int) or 0
    report.affected_individuals = request.form.get("affected_individuals", type=int) or 0
    report.totally_damaged_houses = request.form.get("totally_damaged_houses", type=int) or 0
    report.partially_damaged_houses = request.form.get("partially_damaged_houses", type=int) or 0
    report.missing_persons = request.form.get("missing_persons", type=int) or 0
    report.casualties_deaths = request.form.get("casualties_deaths", type=int) or 0

    report.drinking_water_cases = request.form.get("drinking_water_cases", type=int) or 0
    report.hygiene_kits_est = request.form.get("hygiene_kits_est", type=int) or 0
    report.blankets_est = request.form.get("blankets_est", type=int) or 0

    report.remarks = request.form.get("remarks", "").strip() or None
    report.submitted_by_name = request.form.get("submitted_by_name", "").strip() or current_user.name
    report.submitted_by_designation = request.form.get("submitted_by_designation", "").strip() or current_user.designation


def _get_or_create_report(barangay, report_id, event_id):
    if report_id:
        report = _get_own_report_or_404(report_id)
        if report.status not in ("draft", "pending", "returned"):
            abort(403)
        return report, False
    report = BarangayReport(barangay_id=barangay.barangay_id, event_id=event_id)
    db.session.add(report)
    return report, True


@barangay_bp.route("/damage-report/save-draft", methods=["POST"])
@login_required
@role_required("barangay_user")
def save_damage_report_draft():
    barangay = _own_barangay_or_404()
    report_id = request.form.get("report_id", type=int)
    event_id = request.form.get("event_id", type=int) or (_active_event().event_id if _active_event() else None)
    if not event_id:
        flash("There is no active typhoon event to file a report against right now.", "error")
        return redirect(url_for("barangay.damage_report"))

    report, is_new = _get_or_create_report(barangay, report_id, event_id)
    _apply_report_form(report)
    report.status = "draft"

    db.session.flush()
    _save_report_upload(report)
    db.session.commit()

    flash(f"{report.ref} saved as draft.", "success")
    return redirect(url_for("barangay.edit_damage_report", report_id=report.report_id))


@barangay_bp.route("/damage-report/submit", methods=["POST"])
@login_required
@role_required("barangay_user")
def submit_damage_report():
    barangay = _own_barangay_or_404()
    report_id = request.form.get("report_id", type=int)
    event_id = request.form.get("event_id", type=int) or (_active_event().event_id if _active_event() else None)
    if not event_id:
        flash("There is no active typhoon event to file a report against right now.", "error")
        return redirect(url_for("barangay.damage_report"))

    report, is_new = _get_or_create_report(barangay, report_id, event_id)
    _apply_report_form(report)

    if not report.submitted_by_name:
        flash("Enter the name of the person submitting this report.", "error")
        return redirect(url_for("barangay.edit_damage_report", report_id=report.report_id) if not is_new
                         else url_for("barangay.new_damage_report"))
    if report.affected_individuals < report.affected_families:
        flash("Affected Individuals must be greater than or equal to Affected Families.", "error")
        return redirect(url_for("barangay.edit_damage_report", report_id=report.report_id) if not is_new
                         else url_for("barangay.new_damage_report"))

    was_returned = report.status == "returned"
    report.submitted_at = datetime.utcnow()
    # Resubmitting a returned report puts it back in the review queue —
    # review_remarks/reviewed_by/reviewed_at are left as history of the prior review.
    report.status = "pending"

    db.session.flush()
    _save_report_upload(report)

    cswdo_office = Office.query.filter_by(office_type="cswdo", area_covered=barangay.city_municipality).first()
    db.session.add(ActivityLog(
        actor_id=current_user.user_id, action_type="damage_report_submitted",
        description=f"{report.ref} {'resubmitted' if was_returned else 'submitted'} by Brgy. {barangay.barangay_name} — "
                     f"{report.affected_families:,} affected families",
        office_id=cswdo_office.office_id if cswdo_office else None, barangay_id=barangay.barangay_id,
    ))
    db.session.commit()

    flash(f"{report.ref} submitted to {barangay.city_municipality} MSWDO/CSWDO for review.", "success")
    return redirect(url_for("barangay.damage_report"))


# ---------------------------------------------------------------------------
# Affected Families
# ---------------------------------------------------------------------------

@barangay_bp.route("/affected-families")
@login_required
@role_required("barangay_user")
def affected_families():
    barangay = _own_barangay_or_404()
    active_events = DisasterEvent.query.filter_by(status="active").order_by(
        DisasterEvent.start_date.desc()
    ).all()
    primary_event = active_events[0] if active_events else None

    status_row = None
    latest_report = None
    if primary_event:
        status_row = BarangayDisasterStatus.query.filter_by(
            barangay_id=barangay.barangay_id, event_id=primary_event.event_id
        ).first()
        latest_report = BarangayReport.query.filter(
            BarangayReport.barangay_id == barangay.barangay_id,
            BarangayReport.event_id == primary_event.event_id,
            BarangayReport.status != "draft",
        ).order_by(BarangayReport.created_at.desc()).first()

    priority = _priority_info(status_row.status if status_row else "normal")

    # History across past (ended) events, most recent first — same toolbar
    # (search + status + export) as the Damage Reports table on Reports.
    report_q = request.args.get("report_q", "").strip().lower()
    report_status = request.args.get("report_status", "all")
    history = _own_submitted_reports(barangay.barangay_id)
    if report_status != "all":
        history = [r for r in history if r.status == report_status]
    if report_q:
        history = [r for r in history if report_q in r.ref.lower()]
    history = history[:10]

    return render_template(
        "barangay/affected_families.html",
        barangay=barangay,
        primary_event=primary_event,
        status_row=status_row,
        latest_report=latest_report,
        priority=priority,
        history=history,
        status_labels=REPORT_STATUS_LABELS,
        report_q=report_q, report_status=report_status,
    )


# ---------------------------------------------------------------------------
# Relief Monitoring
# ---------------------------------------------------------------------------

@barangay_bp.route("/relief-monitoring")
@login_required
@role_required("barangay_user")
def relief_monitoring():
    barangay = _own_barangay_or_404()

    allocations = AllocationRecord.query.filter_by(barangay_id=barangay.barangay_id).order_by(
        AllocationRecord.allocation_date.desc()
    ).all()

    rows = []
    for a in allocations:
        distributions = sorted(a.distribution_records, key=lambda d: d.distribution_date, reverse=True)
        active_distribution = next((d for d in distributions if d.dispatch_status != "delivered"), None) \
            or (distributions[0] if distributions else None)
        rows.append({
            "allocation": a,
            "ref": f"RR-{a.allocation_date.year}-{a.allocation_id:03d}",
            "status": a.display_status,
            "distributions": distributions,
            "active_distribution": active_distribution,
            "progress_pct": ROUTE_PROGRESS_BY_STATUS.get(active_distribution.dispatch_status, 0) if active_distribution else None,
            "can_confirm": bool(active_distribution and active_distribution.dispatch_status == "in_transit"
                                 and active_distribution.status == "pending"),
        })

    return render_template(
        "barangay/relief_monitoring.html",
        barangay=barangay,
        rows=rows,
        dispatch_status_labels=DISPATCH_STATUS_LABELS,
    )


def _get_own_distribution_or_404(distribution_id):
    rec = DistributionRecord.query.get_or_404(distribution_id)
    barangay = current_user.barangay
    if not barangay or rec.barangay_id != barangay.barangay_id:
        abort(403)
    return rec


@barangay_bp.route("/relief-monitoring/<int:distribution_id>/confirm-receipt", methods=["POST"])
@login_required
@role_required("barangay_user")
def confirm_receipt(distribution_id):
    rec = _get_own_distribution_or_404(distribution_id)

    if rec.dispatch_status != "in_transit" or rec.status != "pending":
        flash("This delivery isn't ready to be confirmed — it may have already been received.", "error")
        return redirect(url_for("barangay.relief_monitoring"))

    received_by = request.form.get("received_by", "").strip() or current_user.name
    condition = request.form.get("condition", "")
    validation_type = request.form.get("validation_type", "photo")

    if condition not in ("complete", "partial", "damaged"):
        flash("Select the condition the delivery arrived in.", "error")
        return redirect(url_for("barangay.relief_monitoring"))
    if validation_type not in ("photo", "signature"):
        validation_type = "photo"

    saved_names = []
    files = [f for f in request.files.getlist("proof_files") if f and f.filename]
    if files:
        upload_dir = os.path.join(current_app.root_path, "static", "uploads", "distributions", str(rec.distribution_id))
        os.makedirs(upload_dir, exist_ok=True)
        for f in files:
            ext = f.filename.rsplit(".", 1)[-1].lower() if "." in f.filename else ""
            if ext not in ALLOWED_UPLOAD_EXTENSIONS:
                continue
            safe_name = secure_filename(f.filename)
            f.save(os.path.join(upload_dir, safe_name))
            saved_names.append(safe_name)

    if not saved_names and validation_type == "photo":
        flash("Attach at least one photo, or switch to signature confirmation.", "error")
        return redirect(url_for("barangay.relief_monitoring"))

    rec.received_by = received_by
    rec.condition = condition
    rec.time_received = datetime.now().time()
    rec.validation_type = validation_type
    if saved_names:
        rec.validation_file = ",".join(saved_names)
    rec.status = "confirmed"
    # The barangay confirming receipt is what closes out the trip — mirrors
    # pswdo.confirm_delivery's own dispatch_status transition (app/routes/pswdo.py),
    # just triggered from the receiving end instead of the dispatching end.
    rec.dispatch_status = "delivered"
    rec.submitted_by = current_user.user_id

    db.session.add(ActivityLog(
        actor_id=current_user.user_id, action_type="distribution_receipt_confirmed",
        description=f"{rec.barangay.barangay_name} confirmed receipt of D-{rec.distribution_date.year}-{rec.distribution_id:03d} ({rec.quantity_released:,} food packs), received by {received_by}",
        barangay_id=rec.barangay_id, distribution_id=rec.distribution_id,
    ))
    db.session.commit()
    flash("Relief receipt confirmed. Thank you!", "success")
    return redirect(url_for("barangay.relief_monitoring"))


# ---------------------------------------------------------------------------
# Reports — mirrors app.routes.cswdo's report-generation pattern (report
# cards -> report_view -> PDF/Excel export -> logged + re-downloadable),
# just scoped to this one barangay instead of a municipality. Only 2 of the
# 7 generic report types have a meaningful barangay-scoped equivalent (see
# app.routes.report_data.BARANGAY_REPORT_TYPES) — a barangay has no
# warehouse of its own, so Warehouse Inventory/Stock Movement/Municipality
# Summary/Analytics don't have real data behind them at this scope.
# ---------------------------------------------------------------------------

REPORTS_MIME_TYPES = {
    "pdf": "application/pdf",
    "excel": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}
REPORTS_EXTENSIONS = {"pdf": "pdf", "excel": "xlsx"}


def _reports_filters_snapshot(filters):
    return {"event_id": filters["event_id"], "days": filters["days"]}


def _regenerate_barangay_report(log, barangay):
    from app.routes.reports import _StoredArgs
    from app.routes.report_data import resolve_barangay_filters, build_barangay_report
    from app.routes.report_files import generate_file

    stored = json.loads(log.filters_json) if log.filters_json else {}
    filters = resolve_barangay_filters(_StoredArgs(stored))
    report = build_barangay_report(log.report_type, barangay, filters, log.generated_by_user)
    return generate_file(report, log.format)


@barangay_bp.route("/reports")
@login_required
@role_required("barangay_user")
def reports():
    from app.models.report import ReportLog
    from app.routes.report_data import BARANGAY_REPORT_TYPES, resolve_barangay_filters

    barangay = _own_barangay_or_404()
    filters = resolve_barangay_filters(request.args)
    active_events = DisasterEvent.query.filter_by(status="active").order_by(
        DisasterEvent.start_date.desc()
    ).all()

    my_reports = _own_submitted_reports(barangay.barangay_id)
    delivered = DistributionRecord.query.filter(
        DistributionRecord.barangay_id == barangay.barangay_id,
        DistributionRecord.dispatch_status == "delivered",
        DistributionRecord.distribution_date >= filters["start_date"],
    ).all()

    reports_generated = ReportLog.query.filter(
        ReportLog.generated_by == current_user.user_id,
        ReportLog.generated_at >= filters["start_date"],
    ).count()
    verified_count = len([
        r for r in my_reports
        if r.status == "verified" and r.submitted_at and r.submitted_at.date() >= filters["start_date"]
    ])
    packs_received = sum(d.quantity_released for d in delivered)
    completed_deliveries = len(delivered)

    query_params = {"event_id": filters["event_id"], "days": filters["days"]}
    report_cards = [
        {"slug": slug, **info, "generate_url": url_for("barangay.report_view", report_type=slug, **query_params)}
        for slug, info in BARANGAY_REPORT_TYPES.items()
    ]

    recent_logs = ReportLog.query.filter_by(generated_by=current_user.user_id).order_by(
        ReportLog.generated_at.desc()
    ).limit(10).all()
    recent_reports = []
    for log in recent_logs:
        if log.report_type not in BARANGAY_REPORT_TYPES:
            continue
        stored = json.loads(log.filters_json) if log.filters_json else {}
        recent_reports.append({
            "log": log,
            "title": BARANGAY_REPORT_TYPES.get(log.report_type, {}).get("title", log.report_type),
            "view_url": url_for("barangay.report_view", report_type=log.report_type, **stored),
            "download_url": url_for("barangay.report_download", report_id=log.report_id),
        })

    coverage_range = "All Time" if filters["days"] == "all" else (
        f"{filters['start_date'].strftime('%b %d')} - {date.today().strftime('%b %d, %Y')}"
    )

    return render_template(
        "barangay/reports.html",
        barangay=barangay,
        active_events=active_events,
        filters=filters,
        coverage_range=coverage_range,
        reports_generated=reports_generated,
        verified_count=verified_count,
        packs_received=packs_received,
        completed_deliveries=completed_deliveries,
        report_cards=report_cards,
        recent_reports=recent_reports,
        download_all_url=url_for("barangay.report_download_all"),
    )


@barangay_bp.route("/reports/<report_type>")
@login_required
@role_required("barangay_user")
def report_view(report_type):
    from app.routes.report_data import BARANGAY_REPORT_TYPES, resolve_barangay_filters, build_barangay_report

    if report_type not in BARANGAY_REPORT_TYPES:
        abort(404)
    barangay = _own_barangay_or_404()
    filters = resolve_barangay_filters(request.args)
    report = build_barangay_report(report_type, barangay, filters, current_user)
    active_events = DisasterEvent.query.filter_by(status="active").order_by(
        DisasterEvent.start_date.desc()
    ).all()

    return render_template(
        "barangay/report_view.html",
        report=report, filters=filters, active_events=active_events, barangay=barangay,
    )


def _barangay_export_report(report_type, fmt):
    from app.models.report import ReportLog
    from app.routes.report_data import BARANGAY_REPORT_TYPES, resolve_barangay_filters, build_barangay_report
    from app.routes.report_files import generate_file

    if report_type not in BARANGAY_REPORT_TYPES:
        abort(404)
    barangay = _own_barangay_or_404()
    filters = resolve_barangay_filters(request.args)
    report = build_barangay_report(report_type, barangay, filters, current_user)
    content, pages = generate_file(report, fmt)

    db.session.add(ReportLog(
        report_type=report_type, format=fmt, pages=pages,
        filters_json=json.dumps(_reports_filters_snapshot(filters)),
        generated_by=current_user.user_id,
    ))
    db.session.commit()

    filename = f"{report_type}_{datetime.now().strftime('%Y%m%d')}.{REPORTS_EXTENSIONS[fmt]}"
    return Response(
        content, mimetype=REPORTS_MIME_TYPES[fmt],
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@barangay_bp.route("/reports/<report_type>/pdf")
@login_required
@role_required("barangay_user")
def report_export_pdf(report_type):
    return _barangay_export_report(report_type, "pdf")


@barangay_bp.route("/reports/<report_type>/excel")
@login_required
@role_required("barangay_user")
def report_export_excel(report_type):
    return _barangay_export_report(report_type, "excel")


@barangay_bp.route("/reports/download/<int:report_id>")
@login_required
@role_required("barangay_user")
def report_download(report_id):
    from app.models.report import ReportLog
    from app.routes.report_data import BARANGAY_REPORT_TYPES

    barangay = _own_barangay_or_404()
    log = ReportLog.query.get_or_404(report_id)
    if log.generated_by != current_user.user_id:
        abort(403)
    if log.report_type not in BARANGAY_REPORT_TYPES:
        abort(404)

    content, _ = _regenerate_barangay_report(log, barangay)
    filename = f"{log.report_type}_{log.generated_at.strftime('%Y%m%d')}.{REPORTS_EXTENSIONS[log.format]}"
    return Response(
        content, mimetype=REPORTS_MIME_TYPES[log.format],
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@barangay_bp.route("/reports/download-all")
@login_required
@role_required("barangay_user")
def report_download_all():
    from app.models.report import ReportLog
    from app.routes.report_data import BARANGAY_REPORT_TYPES

    barangay = _own_barangay_or_404()
    logs = ReportLog.query.filter_by(generated_by=current_user.user_id).order_by(
        ReportLog.generated_at.desc()
    ).limit(10).all()
    if not logs:
        flash("No reports have been generated yet — export one first.", "error")
        return redirect(url_for("barangay.reports"))

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for i, log in enumerate(logs, start=1):
            if log.report_type not in BARANGAY_REPORT_TYPES:
                continue
            content, _ = _regenerate_barangay_report(log, barangay)
            fname = f"{i:02d}_{log.report_type}_{log.generated_at.strftime('%Y%m%d')}.{REPORTS_EXTENSIONS[log.format]}"
            zf.writestr(fname, content)
    buffer.seek(0)

    return Response(
        buffer.getvalue(), mimetype="application/zip",
        headers={
            "Content-Disposition": f"attachment; filename={barangay.barangay_name.replace(' ', '_')}_reports_{datetime.now().strftime('%Y%m%d')}.zip"
        },
    )


@barangay_bp.route("/reports/export")
@login_required
@role_required("barangay_user")
def reports_export():
    """Lighter CSV export used by the Affected Families' Report History
    table — separate from the PDF/Excel report_export_pdf/excel above,
    which log to ReportLog and appear in this page's own Recent Reports."""
    barangay = _own_barangay_or_404()
    my_reports = _own_submitted_reports(barangay.barangay_id)

    report_q = request.args.get("report_q", "").strip().lower()
    report_status = request.args.get("report_status", "all")
    if report_status != "all":
        my_reports = [r for r in my_reports if r.status == report_status]
    if report_q:
        my_reports = [r for r in my_reports if report_q in r.ref.lower()]

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["Report Ref", "Event", "Status", "Affected Families", "Affected Individuals",
                      "Flood Level", "Submitted By", "Submitted At"])
    for r in my_reports:
        writer.writerow([
            r.ref, r.event.event_name if r.event else "", REPORT_STATUS_LABELS.get(r.status, r.status),
            r.affected_families, r.affected_individuals, PRIORITY_BY_STATUS.get(r.flood_level, DEFAULT_PRIORITY)["label"],
            r.submitted_by_name, r.submitted_at.strftime("%Y-%m-%d %H:%M") if r.submitted_at else "",
        ])

    return Response(
        buffer.getvalue(), mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={barangay.barangay_name.replace(' ', '_')}_reports.csv"},
    )


# ---------------------------------------------------------------------------
# Notifications
# ---------------------------------------------------------------------------

@barangay_bp.route("/notifications")
@login_required
@role_required("barangay_user")
def notifications():
    barangay = _own_barangay_or_404()
    category_filter = request.args.get("category", "all")
    status_filter = request.args.get("status", "all")

    scope = _own_activity_scope()
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
    page_items = [_notification_view(log) for log in all_matching[(page - 1) * per_page: page * per_page]]

    # Only the categories this barangay's own ActivityLog rows can actually
    # carry (see _own_activity_scope) — no "Warehouse" tab like PSWDO's,
    # since warehouse-transfer notifications never carry a barangay_id.
    categories = [
        {"value": "all", "label": "All"},
        {"value": "damage_reports", "label": "Damage Reports"},
        {"value": "relief_requests", "label": "Relief Requests"},
        {"value": "distribution", "label": "Distribution"},
    ]

    return render_template(
        "barangay/notifications.html",
        items=page_items, unread_count=unread_count, total_count=total_count,
        total_filtered=total_filtered, category_filter=category_filter, status_filter=status_filter,
        categories=categories, page=page, total_pages=total_pages, barangay=barangay,
    )


@barangay_bp.route("/notifications/<int:log_id>/view")
@login_required
@role_required("barangay_user")
def view_notification(log_id):
    """Same as pswdo.view_notification: opening a notification is what marks
    it read, then routes to whatever page that notification is about."""
    log = ActivityLog.query.get_or_404(log_id)
    _assert_own_activity(log)
    log.is_read = True
    db.session.commit()
    destination = _notification_view(log)["link"]
    return redirect(destination or url_for("barangay.notifications"))


@barangay_bp.route("/notifications/mark-all-read", methods=["POST"])
@login_required
@role_required("barangay_user")
def mark_all_notifications_read():
    scope = _own_activity_scope()
    if scope is not None:
        ActivityLog.query.filter(scope, ActivityLog.is_read.is_(False)).update(
            {"is_read": True}, synchronize_session=False
        )
        db.session.commit()
    flash("All notifications marked as read.", "success")
    return redirect(request.referrer or url_for("barangay.notifications"))


# ---------------------------------------------------------------------------
# Profile Settings
# ---------------------------------------------------------------------------

@barangay_bp.route("/settings/profile")
@login_required
@role_required("barangay_user")
def profile_settings():
    return render_template("barangay/profile_settings.html")


@barangay_bp.route("/settings/profile", methods=["POST"])
@login_required
@role_required("barangay_user")
def update_profile_info():
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip().lower()
    designation = request.form.get("designation", "").strip()

    if not name or not email:
        flash("Name and email are required.", "error")
        return redirect(url_for("barangay.profile_settings"))

    email_taken = User.query.filter(
        User.email == email, User.user_id != current_user.user_id
    ).first()
    if email_taken:
        flash(f"{email} is already in use by another account.", "error")
        return redirect(url_for("barangay.profile_settings"))

    current_user.name = name
    current_user.email = email
    current_user.designation = designation or None
    db.session.commit()
    flash("Profile information updated.", "success")
    return redirect(url_for("barangay.profile_settings"))


@barangay_bp.route("/settings/password", methods=["POST"])
@login_required
@role_required("barangay_user")
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
    return redirect(url_for("barangay.profile_settings"))
