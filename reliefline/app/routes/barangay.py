import csv
import io
import json
import os
import shutil
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
from app.models.barangay_inventory import BarangayInventory, BarangayStockLog
from app.models.allocation import AllocationRecord
from app.models.validation import DistributionRecord
from app.models.activity_log import ActivityLog
from app.models.user import User
from app.utils import weather as weather_service
from app.ml import predict as ml_predict

# Reused from the PSWDO route module so a status label, priority tier, or
# notification icon never drifts between the PSWDO/CSWDO screens and this
# barangay-facing one — see app/routes/pswdo.py for the source of truth.
from app.routes.pswdo import (
    DISPATCH_STATUS_LABELS, NOTIFICATION_META, DEFAULT_NOTIFICATION_META,
)

barangay_bp = Blueprint("barangay", __name__)

ALLOWED_UPLOAD_EXTENSIONS = {"pdf", "jpg", "jpeg", "png"}

REPORT_STATUS_LABELS = {
    "draft": "Draft",
    "pending": "Submitted",
    "returned": "Returned",
    "approved": "Approved",
    "declined": "Declined",
    "fulfilled": "Fulfilled",
}

# Reports the barangay has nothing left to act on — MSWDO/CSWDO has decided
# them: "approved" (accepted, delivery scheduled), "fulfilled" (delivery
# confirmed received), "declined" (rejected). These fill the History tab.
# Open items the barangay still works on are draft / pending / returned.
# (There is no "verified" status — that wording predates the current enum.)
DECIDED_REPORT_STATUSES = ("approved", "fulfilled", "declined")
ACCEPTED_REPORT_STATUSES = ("approved", "fulfilled")

# The barangay's priority tier is COMPUTED server-side from the reported
# impact (see _compute_severity) — never graded by hand. It stays an internal
# signal only: it drives the GIS map colours, the CSWDO priority list, and the
# BarangayDisasterStatus row, but it is not shown on the report itself. The
# 4-tier vocabulary matches PRIORITY_BY_STATUS (app/routes/pswdo.py).


def _compute_severity(*, affected_families=0, affected_individuals=0,
                      totally_damaged_houses=0, partially_damaged_houses=0,
                      roofs_damaged=0):
    """Derive the priority tier from what was actually reported. Point-based,
    capped per factor:

      housing     totally-damaged houses (heavier) + partial + roofs damaged
      population  affected families reported

    Tiers: >=42 Critical · >=24 High · >=10 Moderate · else Low.
    """
    score = 0.0

    total_dmg = totally_damaged_houses or 0
    part_dmg = (partially_damaged_houses or 0) + (roofs_damaged or 0)
    if total_dmg >= 50:
        score += 30
    elif total_dmg >= 20:
        score += 20
    elif total_dmg >= 5:
        score += 10
    elif total_dmg >= 1:
        score += 4
    if part_dmg >= 100:
        score += 12
    elif part_dmg >= 30:
        score += 7
    elif part_dmg >= 1:
        score += 3

    fam = affected_families or 0
    if fam >= 300:
        score += 20
    elif fam >= 120:
        score += 13
    elif fam >= 40:
        score += 6

    if score >= 42:
        return "high_priority"
    if score >= 24:
        return "needs_assistance"
    if score >= 10:
        return "monitoring"
    return "normal"


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
    # this opens the Barangay Report page in general rather than one report.
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
    "damage_report_returned": _damage_report_notification_link,
    "allocation_approved": _relief_monitoring_notification_link,
    "allocation_rejected": _relief_monitoring_notification_link,
    "barangay_relief_approved": _relief_monitoring_notification_link,
    "barangay_relief_declined": _damage_report_notification_link,
    "cswdo_proactive_allocation": _relief_monitoring_notification_link,
    "distribution_status": _relief_monitoring_notification_link,
    "distribution_delivered": _relief_monitoring_notification_link,
    "distribution_receipt_confirmed": _relief_monitoring_notification_link,
}


# On the barangay side the "distribution" category is presented as
# "Relief Monitoring" (matches the sidebar page of the same name) — the
# shared NOTIFICATION_META label ("Deliveries") is CSWDO/PSWDO wording.
NOTIFICATION_CATEGORY_LABELS = {"distribution": "Relief Monitoring"}


def _notification_view(log):
    meta = NOTIFICATION_META.get(log.action_type, DEFAULT_NOTIFICATION_META)
    link_fn = NOTIFICATION_LINK_BUILDERS.get(log.action_type)
    return {
        "log": log, "icon": meta["icon"], "color": meta["color"],
        "category": meta["category"],
        "category_label": NOTIFICATION_CATEGORY_LABELS.get(meta["category"], meta["category_label"]),
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

    # Current Standing — this barangay's status for the active event. Prefer
    # the MSWDO-synced BarangayDisasterStatus (set once a report is approved);
    # before that, fall back to the barangay's own latest submitted report so
    # the panel reflects what was filed instead of showing 0 next to the
    # affected-individuals / damaged-houses figures pulled from that same
    # report.
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
    if status_row:
        affected_families = status_row.affected_families
        standing_verified = True
    elif latest_report:
        affected_families = latest_report.affected_families
        standing_verified = False
    else:
        affected_families = 0
        standing_verified = False

    # My damage reports — needing attention (submitted/returned) vs. all-time count
    my_reports = _own_submitted_reports(barangay.barangay_id)
    pending_reports = [r for r in my_reports if r.status in ("pending", "returned")]
    returned_reports = [r for r in my_reports if r.status == "returned"]
    recent_reports = my_reports[:4]

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
    in_transit_count = len([d for d in my_distributions if d.dispatch_status in ("dispatched", "in_transit")])
    awaiting_confirmation = [
        d for d in my_distributions
        if d.dispatch_status in ("dispatched", "in_transit", "delayed", "delivered") and d.status != "confirmed"
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
        status_row=status_row,
        latest_report=latest_report,
        standing_verified=standing_verified,
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
        weather_cities=[barangay.city_municipality] if barangay.city_municipality else [],
    )


@barangay_bp.route("/dashboard/weather")
@login_required
@role_required("barangay_user")
def dashboard_weather():
    """JSON feed for the dashboard's Weather & Typhoon Watch widget — this
    barangay's own city/municipality only."""
    barangay = _own_barangay_or_404()
    city = barangay.city_municipality
    return weather_service.get_dashboard_snapshot([city] if city else [])


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

    # The Active Event Report tab owns the open items (draft/pending/returned)
    # for the CURRENT event (or ones not yet tied to any event). Everything
    # else — decided reports and anything left open on an event that has since
    # ended — belongs in History, so a report the barangay can no longer act
    # on is still visible for the record instead of disappearing.
    active_event_ids = (primary_event.event_id, None) if primary_event else (None,)

    def _is_active_open(r):
        return r.event_id in active_event_ids and r.status in ("draft", "pending", "returned")

    # Stat cards are all-time and identical on both tabs.
    ctx = {
        "barangay": barangay, "primary_event": primary_event, "tab": tab,
        "status_labels": REPORT_STATUS_LABELS,
        "total_count": len(all_reports),
        "draft_count": len([r for r in all_reports if r.status == "draft"]),
        "pending_count": len([r for r in all_reports if r.status == "pending"]),
        "approved_count": len([r for r in all_reports if r.status in ACCEPTED_REPORT_STATUSES]),
        "returned_count": len([r for r in all_reports if r.status == "returned"]),
    }

    if tab == "history":
        search_query = request.args.get("q", "").strip().lower()
        status_filter = request.args.get("status", "all")
        history_reports = [r for r in all_reports if not _is_active_open(r)]
        # Only offer filter options for statuses that actually appear here.
        history_statuses = [
            (s, REPORT_STATUS_LABELS.get(s, s.title()))
            for s in ("pending", "returned", "approved", "declined", "fulfilled")
            if any(r.status == s for r in history_reports)
        ]
        if status_filter != "all":
            history_reports = [r for r in history_reports if r.status == status_filter]
        if search_query:
            history_reports = [
                r for r in history_reports
                if search_query in r.ref.lower() or search_query in r.barangay.barangay_name.lower()
            ]
        ctx.update({
            "decided_reports": history_reports,
            "history_statuses": history_statuses,
            "search_query": search_query,
            "status_filter": status_filter,
        })
    else:
        # Active Event Report tab — open items (draft/submitted/returned) for
        # the active event, PLUS standing ones not yet tied to any event
        # (event_id IS NULL) — a draft started before PSWDO declared an event
        # still needs a way back in.
        open_reports = [r for r in all_reports if _is_active_open(r)]
        returned_reports = [r for r in open_reports if r.status == "returned"]

        open_rows = [{"report": r} for r in open_reports]

        ctx.update({
            "open_rows": open_rows,
            "returned_reports": returned_reports,
        })

    return render_template("barangay/damage_report.html", **ctx)


@barangay_bp.route("/damage-report/export")
@login_required
@role_required("barangay_user")
def damage_report_export():
    barangay = _own_barangay_or_404()
    decided_reports = [r for r in _own_reports_all(barangay.barangay_id) if r.status in DECIDED_REPORT_STATUSES]

    status_filter = request.args.get("status", "all")
    if status_filter != "all":
        decided_reports = [r for r in decided_reports if r.status == status_filter]
    search_query = request.args.get("q", "").strip().lower()
    if search_query:
        decided_reports = [
            r for r in decided_reports
            if search_query in r.ref.lower() or search_query in r.barangay.barangay_name.lower()
        ]

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["Report Ref", "Event", "Affected Families", "Affected Individuals",
                      "Status", "Reviewed By", "Submitted At"])
    for r in decided_reports:
        writer.writerow([
            r.ref, r.event.event_name if r.event else "", r.affected_families, r.affected_individuals,
            REPORT_STATUS_LABELS.get(r.status, r.status),
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
        status_labels=REPORT_STATUS_LABELS,
    )


def _report_form_context(barangay, report=None):
    active_events = DisasterEvent.query.filter_by(status="active").order_by(
        DisasterEvent.start_date.desc()
    ).all()
    # Model estimate for THIS barangay — shown next to the "Food Packs
    # Requested" field as decision support only. None when no model is trained.
    model_estimate = ml_predict.predict_quantity(barangay)
    return {
        "barangay": barangay,
        "report": report,
        "active_events": active_events,
        "model_estimate": model_estimate,
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


@barangay_bp.route("/damage-report/<int:report_id>/delete", methods=["POST"])
@login_required
@role_required("barangay_user")
def delete_damage_report(report_id):
    report = _get_own_report_or_404(report_id)
    # Only drafts can be deleted — a submitted report stays on record so the
    # MSWDO review trail and any allocation tied to it are never orphaned.
    if report.status != "draft":
        flash("Only a draft can be deleted. Submitted reports stay on record.", "error")
        return redirect(url_for("barangay.damage_report"))
    ref = report.ref
    upload_dir = os.path.join(
        current_app.root_path, "static", "uploads", "barangay_reports", str(report.report_id)
    )
    db.session.delete(report)
    db.session.commit()
    shutil.rmtree(upload_dir, ignore_errors=True)
    flash(f"Draft {ref} deleted.", "success")
    return redirect(url_for("barangay.damage_report"))


def _apply_report_form(report):
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

    # Roofs Damaged / Wind Signal are no longer collected — the form dropped
    # them. Left inert on new reports; old rows keep whatever they had.
    report.roofs_damaged = 0
    report.wind_signal = None

    report.affected_families = request.form.get("affected_families", type=int) or 0
    report.affected_individuals = request.form.get("affected_individuals", type=int) or 0
    report.totally_damaged_houses = request.form.get("totally_damaged_houses", type=int) or 0
    report.partially_damaged_houses = request.form.get("partially_damaged_houses", type=int) or 0

    # Priority tier is derived, never hand-picked (see _compute_severity) — an
    # internal signal for the GIS map / CSWDO priority list, not shown on the
    # report.
    report.flood_level = _compute_severity(
        affected_families=report.affected_families,
        affected_individuals=report.affected_individuals,
        totally_damaged_houses=report.totally_damaged_houses,
        partially_damaged_houses=report.partially_damaged_houses,
        roofs_damaged=report.roofs_damaged,
    )

    # The barangay's own requested food-pack figure — decision support, not the
    # final allocation (CSWDO/MSWDO sets that when it acts on the request).
    report.requested_food_packs = max(request.form.get("requested_food_packs", type=int) or 0, 0)

    report.hygiene_kits_est = request.form.get("hygiene_kits_est", type=int) or 0
    report.kitchen_kits_est = request.form.get("kitchen_kits_est", type=int) or 0

    report.remarks = request.form.get("remarks", "").strip() or None
    report.submitted_by_name = request.form.get("submitted_by_name", "").strip() or current_user.name
    report.submitted_by_designation = request.form.get("submitted_by_designation", "").strip() or current_user.designation


def _get_or_create_report(barangay, report_id, event_id):
    if report_id:
        report = _get_own_report_or_404(report_id)
        if report.status not in ("draft", "pending", "returned"):
            abort(403)
        # A report started before PSWDO declared an event carries no event_id —
        # attach it to whatever event is active now that it's being saved or
        # submitted, so it stops being a standing/orphan record.
        if report.event_id is None and event_id is not None:
            report.event_id = event_id
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
    # Auto-links to whichever event PSWDO currently has declared, or leaves
    # this report standalone (event_id=None) — filing no longer requires
    # PSWDO to have declared anything first.
    active_event = _active_event()
    event_id = active_event.event_id if active_event else None

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
    active_event = _active_event()
    event_id = active_event.event_id if active_event else None

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
    if not report.requested_food_packs or report.requested_food_packs <= 0:
        flash("Enter the number of food packs your barangay is requesting.", "error")
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
# Relief Monitoring — read-only for the barangay: PSWDO/CSWDO own allocation
# and dispatch, this page only tracks incoming deliveries and lets the
# barangay confirm receipt (the manuscript's photo/signature validation
# record requirement). One card per DistributionRecord ("delivery"), not per
# AllocationRecord, since a single request can eventually produce a
# tracked physical delivery — the ID and progress the barangay actually
# cares about is the delivery's, not the original request's.
# ---------------------------------------------------------------------------

# Simplified 6-step barangay-facing view of a delivery's lifecycle. Coarser
# than pswdo.DISPATCH_STEPS (which also distinguishes Loaded/Dispatched) —
# those sub-stages are PSWDO/CSWDO's own logistics concern, not something a
# receiving barangay needs a separate step for. Ends in "Received" (this
# barangay's own confirmation), which pswdo.DISPATCH_STEPS has no equivalent
# of since that stepper is written from the dispatching side.
BARANGAY_DELIVERY_STEPS = ["requested", "approved", "preparing", "issued", "in_transit", "validated"]
BARANGAY_STEP_LABELS = {
    "requested": "Requested", "approved": "Approved", "preparing": "Preparing",
    "issued": "Issued (released)", "in_transit": "On the Way",
    "validated": "Received (you confirm)",
}


def _delivery_step_index(dist):
    if dist.status == "confirmed":
        return 5
    if dist.dispatch_status == "in_transit":
        return 4
    if dist.dispatch_status == "dispatched" or dist.is_issued:
        return 3
    # preparing / loaded read as one "Preparing" stage here.
    return 2


@barangay_bp.route("/relief-monitoring")
@login_required
@role_required("barangay_user")
def relief_monitoring():
    barangay = _own_barangay_or_404()

    distributions = DistributionRecord.query.filter_by(barangay_id=barangay.barangay_id).order_by(
        DistributionRecord.distribution_date.desc()
    ).all()

    _CONFIRMABLE = ("dispatched", "in_transit", "delayed", "delivered")
    total_packs = sum(d.quantity_released for d in distributions)
    in_transit_count = len([d for d in distributions if d.dispatch_status in _CONFIRMABLE and d.status != "confirmed"])
    received_count = len([d for d in distributions if d.status == "confirmed"])

    delivery_rows = []
    for i, d in enumerate(distributions, start=1):
        fulfilling = d.allocation.fulfilling_office or d.allocation.office
        report = d.allocation.barangay_report if d.allocation else None
        delivery_rows.append({
            "distribution": d,
            "label": f"DEL-{i:03d}",
            "ref": f"D-{d.distribution_date.year}-{d.distribution_id:03d}",
            "request_ref": (report.ref if report
                            else f"RR-{d.allocation.allocation_date.year}-{d.allocation.allocation_id:03d}"),
            "fulfilling_office": fulfilling,
            "step_index": _delivery_step_index(d),
            "can_confirm": d.dispatch_status in _CONFIRMABLE and d.status != "confirmed",
            "is_delayed": d.dispatch_status == "delayed",
        })

    # Requests still awaiting PSWDO/CSWDO approval or dispatch scheduling, or
    # rejected outright — no DistributionRecord exists yet for these, so they
    # never get a delivery card above; surfaced separately so a rejection or
    # a still-pending request doesn't just silently disappear from this page.
    dispatched_allocation_ids = {d.allocation_id for d in distributions}
    other_allocations = AllocationRecord.query.filter(
        AllocationRecord.barangay_id == barangay.barangay_id,
        ~AllocationRecord.allocation_id.in_(dispatched_allocation_ids),
    ).order_by(AllocationRecord.allocation_date.desc()).all()
    other_rows = [{
        "allocation": a,
        "ref": f"RR-{a.allocation_date.year}-{a.allocation_id:03d}",
        "status": a.display_status,
    } for a in other_allocations]

    search_query = (request.args.get("q") or "").strip()
    if search_query:
        ql = search_query.lower()

        def _row_matches(row):
            office = row["fulfilling_office"].office_name if row["fulfilling_office"] else ""
            return any(ql in field.lower() for field in (
                row["label"], row["ref"], row["request_ref"], office,
            ))

        delivery_rows = [r for r in delivery_rows if _row_matches(r)]
        other_rows = [r for r in other_rows if ql in r["ref"].lower()]

    status_filter = request.args.get("status", "all")
    if status_filter == "transit":
        delivery_rows = [r for r in delivery_rows if r["distribution"].status != "confirmed"]
    elif status_filter == "received":
        delivery_rows = [r for r in delivery_rows if r["distribution"].status == "confirmed"]

    return render_template(
        "barangay/relief_monitoring.html",
        barangay=barangay,
        delivery_rows=delivery_rows,
        other_rows=other_rows,
        search_query=search_query,
        status_filter=status_filter,
        total_deliveries=len(distributions),
        in_transit_count=in_transit_count,
        received_count=received_count,
        total_packs=total_packs,
        dispatch_status_labels=DISPATCH_STATUS_LABELS,
        delivery_steps=BARANGAY_DELIVERY_STEPS,
        step_labels=BARANGAY_STEP_LABELS,
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

    # The barangay's VALIDATION RECORD (manuscript) — the only thing that
    # closes a Relief Request and moves stock into the barangay's inventory.
    # Available once CSWDO has confirmed issuance (dispatched) or the delivery
    # is on the road.
    if rec.dispatch_status not in ("dispatched", "in_transit", "delayed", "delivered") or rec.status == "confirmed":
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
    # The barangay's validation closes out the trip.
    rec.dispatch_status = "delivered"
    rec.submitted_by = current_user.user_id

    _record_barangay_receipt(rec)

    db.session.add(ActivityLog(
        actor_id=current_user.user_id, action_type="distribution_receipt_confirmed",
        description=f"{rec.barangay.barangay_name} confirmed receipt of D-{rec.distribution_date.year}-{rec.distribution_id:03d} ({rec.quantity_released:,} food packs), received by {received_by}",
        barangay_id=rec.barangay_id, distribution_id=rec.distribution_id,
    ))
    db.session.commit()
    flash("Relief receipt confirmed. Thank you!", "success")
    return redirect(url_for("barangay.relief_monitoring"))


def _record_barangay_receipt(rec):
    """Validation closes the loop: bump the barangay's own food-pack inventory,
    write the +delta to its ledger, and mark the originating Relief Request
    fulfilled. Idempotent on distribution_id."""
    if BarangayStockLog.query.filter_by(
        distribution_id=rec.distribution_id, source_type="delivery"
    ).first():
        return
    inv = BarangayInventory.query.filter_by(
        barangay_id=rec.barangay_id, item_type="food_pack"
    ).first()
    if inv is None:
        inv = BarangayInventory(
            barangay_id=rec.barangay_id, item_type="food_pack",
            item_name="Food Packs", unit="packs", quantity_available=0,
        )
        db.session.add(inv)
    inv.quantity_available = (inv.quantity_available or 0) + (rec.quantity_released or 0)
    inv.updated_by = current_user.user_id
    db.session.add(BarangayStockLog(
        barangay_id=rec.barangay_id, item_type="food_pack", item_name="Food Packs",
        delta=rec.quantity_released or 0, source_type="delivery",
        distribution_id=rec.distribution_id, updated_by=current_user.user_id,
        reason=f"Received delivery D-{rec.distribution_date.year}-{rec.distribution_id:03d}",
    ))
    alloc = rec.allocation
    if alloc and alloc.barangay_report_id:
        rep = BarangayReport.query.get(alloc.barangay_report_id)
        if rep and rep.status == "approved":
            rep.status = "fulfilled"


# ---------------------------------------------------------------------------
# Inventory — the barangay's own food-pack stock. A plain +/- ledger for
# operational visibility (CSWDO/PSWDO can also see it). Goes UP automatically
# when the barangay validates a delivery; goes DOWN when barangay personnel
# record having handed packs out to residents. Not a model predictor.
# ---------------------------------------------------------------------------

@barangay_bp.route("/inventory")
@login_required
@role_required("barangay_user")
def inventory():
    barangay = _own_barangay_or_404()
    inv = BarangayInventory.query.filter_by(
        barangay_id=barangay.barangay_id, item_type="food_pack"
    ).first()
    on_hand = inv.quantity_available if inv else 0

    logs = BarangayStockLog.query.filter_by(barangay_id=barangay.barangay_id).order_by(
        BarangayStockLog.created_at.desc()
    ).all()
    received = sum(l.delta for l in logs if l.delta > 0)
    given_out = sum(-l.delta for l in logs if l.delta < 0)

    return render_template(
        "barangay/inventory.html",
        barangay=barangay, on_hand=on_hand, logs=logs[:30],
        received=received, given_out=given_out,
    )


@barangay_bp.route("/inventory/record", methods=["POST"])
@login_required
@role_required("barangay_user")
def inventory_record():
    """Barangay-side stock write — DISTRIBUTION ONLY. Stock only ever comes IN
    automatically, via a validated delivery (see _record_barangay_receipt,
    called from confirm_receipt) — a barangay account has no way to add stock
    by hand here, only record having handed packs out to residents. (A manual
    "Adjust Count" add/subtract used to live here too; removed on purpose.)"""
    barangay = _own_barangay_or_404()
    amount = request.form.get("amount", type=int) or 0
    reason = request.form.get("reason", "").strip() or None

    if amount <= 0:
        flash("Enter a number greater than zero.", "error")
        return redirect(url_for("barangay.inventory"))

    inv = BarangayInventory.query.filter_by(
        barangay_id=barangay.barangay_id, item_type="food_pack"
    ).first()
    on_hand = inv.quantity_available if inv else 0
    if inv is None or on_hand < amount:
        flash(f"You only have {on_hand:,} food packs on hand.", "error")
        return redirect(url_for("barangay.inventory"))

    inv.quantity_available = on_hand - amount
    inv.updated_by = current_user.user_id
    db.session.add(BarangayStockLog(
        barangay_id=barangay.barangay_id, item_type="food_pack", item_name="Food Packs",
        delta=-amount, source_type="distribution", reason=reason or "Distributed to residents",
        updated_by=current_user.user_id,
    ))
    db.session.commit()
    flash(f"Recorded {amount:,} food packs distributed to residents.", "success")
    return redirect(url_for("barangay.inventory"))


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
        if r.status in ACCEPTED_REPORT_STATUSES and r.submitted_at and r.submitted_at.date() >= filters["start_date"]
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

    # Report History table — moved here from the now-removed standalone
    # Affected Families page, same search + status + export toolbar.
    report_q = request.args.get("report_q", "").strip().lower()
    report_status = request.args.get("report_status", "all")
    history = my_reports
    if report_status != "all":
        history = [r for r in history if r.status == report_status]
    if report_q:
        history = [r for r in history if report_q in r.ref.lower()]
    history = history[:10]

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
        history=history,
        status_labels=REPORT_STATUS_LABELS,
        report_q=report_q, report_status=report_status,
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
                      "Submitted By", "Submitted At"])
    for r in my_reports:
        writer.writerow([
            r.ref, r.event.event_name if r.event else "", REPORT_STATUS_LABELS.get(r.status, r.status),
            r.affected_families, r.affected_individuals,
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

    scope = _own_activity_scope()
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
        view = _notification_view(log)
        view["was_unread"] = not log.is_read
        page_items.append(view)

    # Opening the Notifications page is itself the "read" action — no per-item
    # or "Mark all as read" click needed. Unread rows still show highlighted on
    # this render (via was_unread) so the user sees what's new before it clears.
    if unread_count and scope is not None:
        ActivityLog.query.filter(scope, ActivityLog.is_read.is_(False)).update(
            {"is_read": True}, synchronize_session=False
        )
        db.session.commit()

    # Only the categories this barangay's own ActivityLog rows can actually
    # carry (see _own_activity_scope) — no "Warehouse" tab like PSWDO's, since
    # warehouse-transfer notifications never carry a barangay_id, and no
    # "Relief Requests" tab since the barangay's relief request IS its
    # Barangay Report (Tier 1) and its whole lifecycle lives in that category.
    categories = [
        {"value": "all", "label": "All"},
        {"value": "barangay_reports", "label": "Barangay Reports"},
        {"value": "distribution", "label": "Relief Monitoring"},
    ]

    return render_template(
        "barangay/notifications.html",
        items=page_items, unread_count=unread_count, total_count=total_count,
        total_filtered=total_filtered, category_filter=category_filter,
        categories=categories, page=page, total_pages=total_pages, per_page=per_page, barangay=barangay,
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
