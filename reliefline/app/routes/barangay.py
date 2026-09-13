import csv
import io
import json
import os
import shutil
import zipfile
from datetime import date, datetime

from app.utils.timezone import ph_now, ph_today

from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, Response, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from app.extensions import db
from app.utils.decorators import role_required
from app.models.office import Office
from app.models.disaster_event import DisasterEvent
from app.models.barangay_status import BarangayDisasterStatus
from app.utils.disaster_events import (
    resolve_effective_event, event_covers_barangay, relevant_active_events_query,
    blocking_event_for_province, events_covering_barangay,
)
from app.models.barangay_report import BarangayReport
from app.models.family import Family, ReportAffectedFamily
from app.models.barangay_inventory import BarangayInventory, BarangayStockLog
from app.models.allocation import AllocationRecord
from app.models.validation import DistributionRecord
from app.models.warehouse import WarehouseInventory, WarehouseStockLog
from app.models.activity_log import ActivityLog
from app.models.user import User
from app.utils import weather as weather_service

# Reused from the PSWDO route module so a status label, priority tier, or
# notification icon never drifts between the PSWDO/CSWDO screens and this
# barangay-facing one - see app/routes/pswdo.py for the source of truth.
from app.routes.pswdo import (
    DISPATCH_STATUS_LABELS, NOTIFICATION_META, DEFAULT_NOTIFICATION_META,
)

barangay_bp = Blueprint("barangay", __name__)

ALLOWED_UPLOAD_EXTENSIONS = {"pdf", "jpg", "jpeg", "png"}

REPORT_STATUS_LABELS = {
    "draft": "Draft",
    "pending": "Submitted",
    "returned": "Returned",
    "verified": "Verified",
    "approved": "Approved",
    "declined": "Declined",
    "fulfilled": "Fulfilled",
}

# Reports the barangay has nothing left to act on - MSWDO/CSWDO has decided
# them: "verified" (situation acknowledged, no allocation), "approved"
# (accepted, delivery scheduled), "fulfilled" (delivery confirmed received),
# "declined" (rejected). These fill the History tab. Open items the barangay
# still works on are draft / pending / returned.
DECIDED_REPORT_STATUSES = ("verified", "approved", "fulfilled", "declined")
# "Accepted" = the report was taken as valid, whether or not packs followed.
ACCEPTED_REPORT_STATUSES = ("verified", "approved", "fulfilled")

# The barangay's priority tier is COMPUTED server-side from the reported
# impact (see _compute_severity) - never graded by hand. It stays an internal
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


def _active_event(barangay):
    """This barangay's effective event - its own town's CSWDO-declared local
    event if active AND this barangay is one of the ones it covers, else
    PSWDO's province-wide event, else None (see app.utils.disaster_events).
    A barangay left unchecked out of its town's local event simply has no
    active event, even while that event is running for the rest of the town."""
    event, applicable_barangay_ids = resolve_effective_event(barangay.city_municipality)
    if event and not event_covers_barangay(applicable_barangay_ids, barangay.barangay_id):
        return None
    return event


def _own_activity_scope():
    """This barangay's own ActivityLog rows - the single source of truth the
    dashboard's Active Alerts panel, the full Notifications page, and its
    mark-as-read actions all read from, so all three always agree.

    Also restricted to NOTIFICATION_META's known operational action_types
    (same allowlist as app.routes.pswdo.notifications) - barangay_id is
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
    # No report_id FK on ActivityLog, so - same fallback pattern as PSWDO's
    # _relief_request_submitted_link when it can't resolve an exact record -
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
    "barangay_report_verified": _damage_report_notification_link,
    "cswdo_proactive_allocation": _relief_monitoring_notification_link,
    "distribution_status": _relief_monitoring_notification_link,
    "distribution_delivered": _relief_monitoring_notification_link,
    "distribution_receipt_confirmed": _relief_monitoring_notification_link,
}


# On the barangay side the "distribution" category is presented as
# "Relief Monitoring" (matches the sidebar page of the same name) - the
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
    """Every report this barangay has ever started, including drafts -
    what the Damage Report page's own Dashboard/History tabs read from."""
    return BarangayReport.query.filter_by(barangay_id=barangay_id).order_by(
        BarangayReport.created_at.desc()
    ).all()


def _own_submitted_reports(barangay_id):
    """Reports this barangay has actually sent to MSWDO/CSWDO (excludes
    drafts still being filled out) - used anywhere outside the Damage Report
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
    now = ph_now()
    barangay = _own_barangay_or_404()

    primary_event = _active_event(barangay)
    # Visibility only - PSWDO's province-wide event, if one is ALSO active
    # while this barangay's own town has a local event in effect (whether or
    # not this barangay is one it covers). primary_event above still drives
    # this dashboard's own figures; this is purely so the barangay isn't
    # unaware PSWDO has separately declared.
    province_event = None
    if primary_event and primary_event.scope == "municipality":
        province_event = blocking_event_for_province()
    elif not primary_event:
        # Also surface it when this barangay was left out of its town's local
        # event and so has no primary_event of its own at all.
        province_event = blocking_event_for_province()

    # Current Standing - this barangay's status for the active event. Prefer
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

    # My damage reports - needing attention (submitted/returned) vs. all-time count
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

    # Relief deliveries - this barangay's own distributions, most recent first
    my_distributions = DistributionRecord.query.filter_by(barangay_id=barangay.barangay_id).order_by(
        DistributionRecord.distribution_date.desc()
    ).limit(5).all()
    in_transit_count = len([d for d in my_distributions if d.dispatch_status in ("dispatched", "in_transit")])
    awaiting_confirmation = [
        d for d in my_distributions
        if d.dispatch_status in ("dispatched", "in_transit", "delayed", "delivered") and d.status != "confirmed"
    ]

    # Active alerts - this barangay's own recent activity, read or unread
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
        province_event=province_event,
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
    """JSON feed for the dashboard's Weather & Typhoon Watch widget - this
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
    primary_event = _active_event(barangay)
    tab = request.args.get("tab", "dashboard")

    all_reports = _own_reports_all(barangay.barangay_id)

    # The Active Event Report tab owns the open items (draft/pending/returned)
    # for the CURRENT event (or ones not yet tied to any event). Everything
    # else - decided reports and anything left open on an event that has since
    # ended - belongs in History, so a report the barangay can no longer act
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
            for s in ("pending", "returned", "verified", "approved", "declined", "fulfilled")
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
        # Active Event Report tab - open items (draft/submitted/returned) for
        # the active event, PLUS standing ones not yet tied to any event
        # (event_id IS NULL) - a draft started before PSWDO declared an event
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
    # Events this barangay may file under - normally just the one effective
    # event (see _active_event), but when a CSWDO-declared local event and
    # PSWDO's province-wide event are BOTH active at once, this barangay is
    # entitled to either (see app.utils.disaster_events) - let the filer
    # choose instead of silently picking one.
    event_options = events_covering_barangay(barangay.city_municipality, barangay.barangay_id)
    # A report already tied to an event that has since ended keeps that
    # event selectable (and as the default) so editing a draft never
    # silently reassigns it to whatever happens to be active now.
    default_event = (report.event if report and report.event else None) or _active_event(barangay)
    if report and report.event and report.event not in event_options:
        event_options = [report.event] + event_options
    default_event_id = default_event.event_id if default_event else None

    # Families available for the checklist. A report being edited may cite
    # a family that's since been archived - keep it selectable/visible on
    # THIS report's form so its checked state (and counts) aren't silently
    # dropped, even though it no longer shows up when starting a new report.
    families_q = Family.query.filter_by(barangay_id=barangay.barangay_id, is_active=True)
    if report:
        cited_ids = [rf.family_id for rf in report.affected_families_list if rf.family_id]
        if cited_ids:
            families_q = Family.query.filter(
                Family.barangay_id == barangay.barangay_id,
                db.or_(Family.is_active.is_(True), Family.family_id.in_(cited_ids)),
            )
    families = families_q.order_by(Family.purok, Family.family_name).all()
    selected_family_ids = {rf.family_id for rf in report.affected_families_list} if report else set()
    # A report filed before this feature (or saved via the manual fallback)
    # has affected_families/individuals but no checklist rows - default it
    # back into manual mode so its existing numbers aren't blanked out.
    manual_mode = bool(report and not report.affected_families_list and (report.affected_families or report.affected_individuals))
    return {
        "barangay": barangay,
        "report": report,
        "event_options": event_options,
        "default_event": default_event,
        "default_event_id": default_event_id,
        "today": ph_today(),
        "families": families,
        "selected_family_ids": selected_family_ids,
        "manual_mode": manual_mode,
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
    # Only drafts can be deleted - a submitted report stays on record so the
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


def _apply_affected_families(report):
    """Fills affected_families/affected_individuals (+ the PWD/senior/
    children breakdown) either from the Family Profiles checklist (the
    normal path - see app.models.family.Family) or, when the barangay has
    no registered profiles yet (or explicitly opts out via the "enter
    manually" toggle - see damage_report_form.html), from the legacy
    hand-typed number fields.

    entry_mode="checklist" replaces report.affected_families_list wholesale
    with a fresh snapshot of the checked families (see
    app.models.family.ReportAffectedFamily) so editing a family profile
    later never rewrites this report's already-submitted numbers.
    """
    entry_mode = request.form.get("entry_mode", "checklist")

    if entry_mode == "manual":
        report.affected_families_list = []
        report.affected_families = request.form.get("affected_families", type=int) or 0
        report.affected_individuals = request.form.get("affected_individuals", type=int) or 0
        report.affected_pwd = 0
        report.affected_seniors = 0
        report.affected_children = 0
        return

    family_ids = request.form.getlist("family_ids", type=int)
    families = []
    if family_ids:
        # no_autoflush - report may be a brand-new, not-yet-fully-populated
        # BarangayReport still pending in the session (required columns like
        # submitted_by_name are filled in later in _apply_report_form); this
        # query must not trigger an autoflush that tries to INSERT it early.
        with db.session.no_autoflush:
            families = Family.query.filter(
                Family.barangay_id == report.barangay_id,
                Family.family_id.in_(family_ids),
                Family.is_active.is_(True),
            ).all()

    report.affected_families_list = [
        ReportAffectedFamily(
            family_id=f.family_id, family_name=f.family_name, head_name=f.head_name, purok=f.purok,
            member_count=f.member_count, pwd_count=f.pwd_count,
            senior_count=f.senior_count, children_count=f.children_count,
        )
        for f in families
    ]
    report.affected_families = len(families)
    report.affected_individuals = sum(f.member_count for f in families)
    report.affected_pwd = sum(f.pwd_count for f in families)
    report.affected_seniors = sum(f.senior_count for f in families)
    report.affected_children = sum(f.children_count for f in families)


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

    # Roofs Damaged / Wind Signal are no longer collected - the form dropped
    # them. Left inert on new reports; old rows keep whatever they had.
    report.roofs_damaged = 0
    report.wind_signal = None

    _apply_affected_families(report)
    report.totally_damaged_houses = request.form.get("totally_damaged_houses", type=int) or 0
    report.partially_damaged_houses = request.form.get("partially_damaged_houses", type=int) or 0

    # Priority tier is derived, never hand-picked (see _compute_severity) - an
    # internal signal for the GIS map / CSWDO priority list, not shown on the
    # report.
    report.flood_level = _compute_severity(
        affected_families=report.affected_families,
        affected_individuals=report.affected_individuals,
        totally_damaged_houses=report.totally_damaged_houses,
        partially_damaged_houses=report.partially_damaged_houses,
        roofs_damaged=report.roofs_damaged,
    )

    # Optional barangay-stated food-pack request. Left at 0 when blank - it is
    # only decision support for CSWDO/MSWDO, never a binding figure (see
    # app.routes.cswdo._relief_request_row / approve_relief_request).
    report.requested_food_packs = request.form.get("requested_food_packs", type=int) or 0
    if report.requested_food_packs < 0:
        report.requested_food_packs = 0

    report.remarks = request.form.get("remarks", "").strip() or None
    report.submitted_by_name = request.form.get("submitted_by_name", "").strip() or current_user.name
    report.submitted_by_designation = request.form.get("submitted_by_designation", "").strip() or current_user.designation


def _resolve_submitted_event_id(barangay, report):
    """Validates the event_id the filer picked in damage_report_form.html's
    Step 1 dropdown (see _report_form_context) against what this barangay may
    actually file under - the province event, its own town's covered local
    event, or (if editing) whatever event this report is already tied to.
    Falls back to the auto-resolved default rather than trusting a tampered
    or stale form value outright."""
    submitted = request.form.get("event_id", type=int)
    options = events_covering_barangay(barangay.city_municipality, barangay.barangay_id)
    allowed_ids = {e.event_id for e in options}
    if report and report.event_id:
        allowed_ids.add(report.event_id)
    if submitted and submitted in allowed_ids:
        return submitted
    # Fall back to the most specific option (events_covering_barangay lists
    # the local event before the province one) rather than trusting a
    # tampered/stale value - NOT _active_event, which returns None for a
    # barangay excluded from its town's local event even when the province
    # event still applies to it.
    return options[0].event_id if options else None


def _get_or_create_report(barangay, report_id, event_id):
    if report_id:
        report = _get_own_report_or_404(report_id)
        if report.status not in ("draft", "pending", "returned"):
            abort(403)
        # Follows whatever event the filer has selected as of this save - a
        # report started before any event was active (or before PSWDO/CSWDO
        # declared) picks one up once available, and a filer who initially
        # chose one of two simultaneously-applicable events may switch to the
        # other while still editable (see _resolve_submitted_event_id).
        if event_id is not None and report.event_id != event_id:
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
    existing = _get_own_report_or_404(report_id) if report_id else None
    # Uses whichever event the filer picked in Step 1 (see
    # _resolve_submitted_event_id) - normally just the one event that
    # applies, but a barangay covered by both its town's local event and
    # PSWDO's province-wide one gets to choose. Leaves this report
    # standalone (event_id=None) if no event applies at all - filing no
    # longer requires PSWDO to have declared anything first.
    event_id = _resolve_submitted_event_id(barangay, existing)

    report, is_new = _get_or_create_report(barangay, report_id, event_id)
    # Once a report has left draft state (sent to MSWDO/CSWDO as "pending", or
    # bounced back as "returned"), editing it must not quietly demote it back
    # to "draft" - that would pull it out of the CSWDO review queue / drop its
    # place in the resubmission trail. Only a still-draft (or brand-new)
    # report can be saved as a draft.
    if not is_new and report.status != "draft":
        flash(f"{report.ref} has already been submitted and can't be saved as a draft again. Use Submit instead.", "error")
        return redirect(url_for("barangay.edit_damage_report", report_id=report.report_id))

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
    existing = _get_own_report_or_404(report_id) if report_id else None
    event_id = _resolve_submitted_event_id(barangay, existing)

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
    report.submitted_at = ph_now()
    # Resubmitting a returned report puts it back in the review queue -
    # review_remarks/reviewed_by/reviewed_at are left as history of the prior review.
    report.status = "pending"

    db.session.flush()
    _save_report_upload(report)

    cswdo_office = Office.query.filter_by(office_type="cswdo", area_covered=barangay.city_municipality).first()
    db.session.add(ActivityLog(
        actor_id=current_user.user_id, action_type="damage_report_submitted",
        description=f"{report.ref} {'resubmitted' if was_returned else 'submitted'} by Brgy. {barangay.barangay_name} - "
                     f"{report.affected_families:,} affected families",
        office_id=cswdo_office.office_id if cswdo_office else None, barangay_id=barangay.barangay_id,
    ))
    db.session.commit()

    flash(f"{report.ref} submitted to {barangay.city_municipality} MSWDO/CSWDO for review.", "success")
    return redirect(url_for("barangay.damage_report"))


@barangay_bp.route("/damage-report/<int:report_id>/unsubmit", methods=["POST"])
@login_required
@role_required("barangay_user")
def unsubmit_damage_report(report_id):
    """Pulls a report back out of the MSWDO/CSWDO review queue into draft, in
    case the barangay submitted too early and wants to fix something first.
    Only while it's still "pending" - once a reviewer has acted (verified/
    approved/declined/returned), the decision is on record and stands."""
    report = _get_own_report_or_404(report_id)
    if report.status != "pending":
        flash("Only a report that's still awaiting review can be unsubmitted.", "error")
        return redirect(url_for("barangay.view_damage_report", report_id=report.report_id))

    report.status = "draft"
    report.submitted_at = None

    db.session.add(ActivityLog(
        actor_id=current_user.user_id, action_type="damage_report_unsubmitted",
        description=f"{report.ref} unsubmitted by Brgy. {report.barangay.barangay_name} - pulled back to draft",
        barangay_id=report.barangay_id,
    ))
    db.session.commit()

    flash(f"{report.ref} pulled back to draft. Edit it and submit again when ready.", "success")
    return redirect(url_for("barangay.edit_damage_report", report_id=report.report_id))


# ---------------------------------------------------------------------------
# Family Profiles - the barangay's own resident registry (panelist-requested
# "profiling" addition). One row per household: member/PWD/senior/children
# counts. This registry is the checklist a Barangay Report is now built
# from - see app.models.family.Family / ReportAffectedFamily and
# _apply_affected_families above.
# ---------------------------------------------------------------------------

def _get_own_family_or_404(family_id):
    barangay = _own_barangay_or_404()
    family = Family.query.filter_by(family_id=family_id, barangay_id=barangay.barangay_id).first()
    if not family:
        abort(404)
    return family


def _apply_family_form(family):
    family.family_name = request.form.get("family_name", "").strip()
    family.head_name = request.form.get("head_name", "").strip() or None
    family.purok = request.form.get("purok", "").strip() or None
    family.contact_number = request.form.get("contact_number", "").strip() or None
    family.member_count = max(1, request.form.get("member_count", type=int) or 1)
    family.pwd_count = max(0, request.form.get("pwd_count", type=int) or 0)
    family.senior_count = max(0, request.form.get("senior_count", type=int) or 0)
    family.children_count = max(0, request.form.get("children_count", type=int) or 0)


@barangay_bp.route("/family-profiles")
@login_required
@role_required("barangay_user")
def family_profiles():
    barangay = _own_barangay_or_404()
    show_archived = request.args.get("archived") == "1"

    # Search/purok/category are all filtered client-side (see #fam-search
    # etc. in family_profiles.html, same pattern as the Barangay Report
    # wizard's family checklist) - the full list always renders so clearing
    # a filter doesn't need a round trip, and the stat cards below stay
    # fixed totals instead of fluctuating with whatever's currently searched.
    families = Family.query.filter_by(barangay_id=barangay.barangay_id, is_active=(not show_archived))
    families = families.order_by(Family.purok, Family.family_name).all()

    active_count = Family.query.filter_by(barangay_id=barangay.barangay_id, is_active=True).count()
    return render_template(
        "barangay/family_profiles.html",
        barangay=barangay, families=families,
        show_archived=show_archived, active_count=active_count,
        total_individuals=sum(f.member_count for f in families) if not show_archived else None,
        total_pwd=sum(f.pwd_count for f in families) if not show_archived else None,
        total_seniors=sum(f.senior_count for f in families) if not show_archived else None,
        total_children=sum(f.children_count for f in families) if not show_archived else None,
    )


@barangay_bp.route("/family-profiles/add", methods=["POST"])
@login_required
@role_required("barangay_user")
def family_profile_add():
    barangay = _own_barangay_or_404()
    family = Family(barangay_id=barangay.barangay_id)
    _apply_family_form(family)
    if not family.family_name:
        flash("Family / household head name is required.", "error")
        return redirect(url_for("barangay.family_profiles"))
    db.session.add(family)
    db.session.commit()
    flash(f"{family.family_name} added to your Family Profiles.", "success")
    return redirect(url_for("barangay.family_profiles"))


@barangay_bp.route("/family-profiles/<int:family_id>/edit", methods=["POST"])
@login_required
@role_required("barangay_user")
def family_profile_edit(family_id):
    family = _get_own_family_or_404(family_id)
    _apply_family_form(family)
    if not family.family_name:
        flash("Family / household head name is required.", "error")
        return redirect(url_for("barangay.family_profiles"))
    family.updated_at = ph_now()
    db.session.commit()
    flash(f"{family.family_name} updated.", "success")
    return redirect(url_for("barangay.family_profiles"))


@barangay_bp.route("/family-profiles/<int:family_id>/archive", methods=["POST"])
@login_required
@role_required("barangay_user")
def family_profile_archive(family_id):
    family = _get_own_family_or_404(family_id)
    family.is_active = not family.is_active
    db.session.commit()
    flash(f"{family.family_name} {'restored' if family.is_active else 'archived'}.", "success")
    return redirect(url_for("barangay.family_profiles", archived=request.args.get("archived")))


@barangay_bp.route("/family-profiles/<int:family_id>/delete", methods=["POST"])
@login_required
@role_required("barangay_user")
def family_profile_delete(family_id):
    family = _get_own_family_or_404(family_id)
    # A family already cited on a report can't be removed outright - the
    # report's snapshot (ReportAffectedFamily) survives either way, but
    # deleting the profile here would strand its "view profile" link.
    # Archiving is the safe removal path once a family has history.
    if ReportAffectedFamily.query.filter_by(family_id=family.family_id).first():
        flash(f"{family.family_name} has been cited on a report and can't be deleted - archive it instead.", "error")
        return redirect(url_for("barangay.family_profiles"))
    name = family.family_name
    db.session.delete(family)
    db.session.commit()
    flash(f"{name} deleted.", "success")
    return redirect(url_for("barangay.family_profiles"))


def _family_print_rows(families):
    """Normalizes either Family (manual selection) or ReportAffectedFamily
    (a report's checklist) rows into plain dicts for print_family_list.html
    - the two models don't share every column (Family has purok/contact,
    ReportAffectedFamily doesn't). Shows the actual packs_given once a
    report-linked family has already been marked received, else the
    suggested figure (1 + PWD + senior)."""
    return [{
        "family_name": f.family_name,
        "head_name": getattr(f, "head_name", None),
        "purok": getattr(f, "purok", None),
        "member_count": f.member_count,
        "pwd_count": f.pwd_count,
        "senior_count": f.senior_count,
        "children_count": f.children_count,
        "packs": f.packs_given if getattr(f, "received", False) else f.suggested_packs,
    } for f in families]


@barangay_bp.route("/family-profiles/print")
@login_required
@role_required("barangay_user")
def print_families_selected():
    """Step 1 of the "select a family" print path (see print_report_families
    for the "choose a report" half): shows the manually-picked families with
    an editable Packs field per family - defaulted to the suggested figure
    (1 + PWD + senior) but the barangay can override it here before
    generating the actual printable sheet (print_families_generate)."""
    barangay = _own_barangay_or_404()
    ids = request.args.getlist("family_ids", type=int)
    if not ids:
        flash("Select at least one family to print.", "error")
        return redirect(url_for("barangay.family_profiles"))
    families = Family.query.filter(
        Family.barangay_id == barangay.barangay_id, Family.family_id.in_(ids)
    ).order_by(Family.purok, Family.family_name).all()
    if not families:
        flash("Select at least one family to print.", "error")
        return redirect(url_for("barangay.family_profiles"))

    return render_template("barangay/print_family_prepare.html", barangay=barangay, families=families)


@barangay_bp.route("/family-profiles/print/generate", methods=["POST"])
@login_required
@role_required("barangay_user")
def print_families_generate():
    """Step 2 - renders the actual printable sheet using the pack quantities
    the barangay set on the prepare step above (falls back to a family's
    suggested figure for any left blank or invalid)."""
    barangay = _own_barangay_or_404()
    ids = request.form.getlist("family_ids", type=int)
    if not ids:
        flash("Select at least one family to print.", "error")
        return redirect(url_for("barangay.family_profiles"))
    families = Family.query.filter(
        Family.barangay_id == barangay.barangay_id, Family.family_id.in_(ids)
    ).order_by(Family.purok, Family.family_name).all()
    if not families:
        flash("Select at least one family to print.", "error")
        return redirect(url_for("barangay.family_profiles"))

    rows = []
    for f in families:
        packs = request.form.get(f"packs_{f.family_id}", type=int)
        rows.append({
            "family_name": f.family_name, "head_name": f.head_name, "purok": f.purok,
            "packs": packs if packs and packs > 0 else f.suggested_packs,
        })

    return render_template(
        "barangay/print_family_list.html",
        barangay=barangay, title="Distribution Announcement",
        subtitle=f"Manually selected - {len(families)} famil{'y' if len(families) == 1 else 'ies'}",
        rows=rows, generated_at=ph_now(),
    )


@barangay_bp.route("/damage-report/<int:report_id>/print-families")
@login_required
@role_required("barangay_user")
def print_report_families(report_id):
    """Printable distribution announcement for one Barangay Report's
    affected-families checklist - the "choose a report" half of this
    feature (see print_families_selected for the manual-pick half)."""
    report = _get_own_report_or_404(report_id)
    if not report.affected_families_list:
        flash("This report has no affected-families checklist to print.", "error")
        return redirect(url_for("barangay.view_damage_report", report_id=report.report_id))

    return render_template(
        "barangay/print_family_list.html",
        barangay=report.barangay, title="Distribution Announcement",
        subtitle=f"{report.ref}{' - ' + report.event.event_name if report.event else ''}",
        rows=_family_print_rows(report.affected_families_list), generated_at=ph_now(),
    )


# ---------------------------------------------------------------------------
# Relief Monitoring - read-only for the barangay: PSWDO/CSWDO own allocation
# and dispatch, this page only tracks incoming deliveries and lets the
# barangay confirm receipt (the manuscript's photo/signature validation
# record requirement). One card per DistributionRecord ("delivery"), not per
# AllocationRecord, since a single request can eventually produce a
# tracked physical delivery - the ID and progress the barangay actually
# cares about is the delivery's, not the original request's.
# ---------------------------------------------------------------------------

# Simplified 6-step barangay-facing view of a delivery's lifecycle. Coarser
# than pswdo.DISPATCH_STEPS (which also distinguishes Loaded/Dispatched) -
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

    # Most recent first - distribution_date is date-only, so distribution_id
    # breaks same-day ties to keep the newest delivery genuinely on top.
    distributions = DistributionRecord.query.filter_by(barangay_id=barangay.barangay_id).order_by(
        DistributionRecord.distribution_date.desc(),
        DistributionRecord.distribution_id.desc(),
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

    search_query = (request.args.get("q") or "").strip()
    if search_query:
        ql = search_query.lower()

        def _row_matches(row):
            office = row["fulfilling_office"].office_name if row["fulfilling_office"] else ""
            return any(ql in field.lower() for field in (
                row["label"], row["ref"], row["request_ref"], office,
            ))

        delivery_rows = [r for r in delivery_rows if _row_matches(r)]

    # delivery_rows stays in the query's newest-first order - no status
    # grouping, so "All statuses" reads strictly most-recent-first.

    # Default view shows only what still needs the barangay's attention.
    # Options: transit (default) · received · all. A bare search with no status
    # picked spans everything so a lookup for a received delivery still lands.
    default_status = "all" if search_query else "transit"
    status_filter = request.args.get("status", default_status)
    if status_filter not in ("transit", "received", "all"):
        status_filter = default_status
    if status_filter == "transit":
        delivery_rows = [r for r in delivery_rows if r["distribution"].status != "confirmed"]
    elif status_filter == "received":
        delivery_rows = [r for r in delivery_rows if r["distribution"].status == "confirmed"]

    return render_template(
        "barangay/relief_monitoring.html",
        barangay=barangay,
        delivery_rows=delivery_rows,
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

    # The barangay's VALIDATION RECORD (manuscript) - the only thing that
    # closes a Relief Request and moves stock into the barangay's inventory.
    # Available once CSWDO has confirmed issuance (dispatched) or the delivery
    # is on the road.
    if rec.dispatch_status not in ("dispatched", "in_transit", "delayed", "delivered") or rec.status == "confirmed":
        flash("This delivery isn't ready to be confirmed - it may have already been received.", "error")
        return redirect(url_for("barangay.relief_monitoring"))

    received_by = request.form.get("received_by", "").strip() or current_user.name
    condition = request.form.get("condition", "")

    if condition not in ("complete", "partial", "damaged"):
        flash("Select the condition the delivery arrived in.", "error")
        return redirect(url_for("barangay.relief_monitoring"))

    # Receipt breakdown - what actually arrived, per the barangay:
    #   complete → all released packs, none damaged
    #   partial  → the count the barangay entered, none damaged
    #   damaged  → good + damaged counts the barangay entered
    expected = rec.quantity_released or 0
    if condition == "complete":
        quantity_received, quantity_damaged = expected, 0
    elif condition == "partial":
        quantity_received = request.form.get("quantity_received", type=int) or 0
        quantity_damaged = 0
        if quantity_received <= 0:
            flash("Enter how many food packs the barangay actually received.", "error")
            return redirect(url_for("barangay.relief_monitoring"))
    else:  # damaged
        quantity_good = request.form.get("quantity_good", type=int) or 0
        quantity_damaged = request.form.get("quantity_damaged", type=int) or 0
        quantity_received = quantity_good + quantity_damaged
        if quantity_received <= 0:
            flash("Enter how many food packs arrived in good condition and how many were damaged.", "error")
            return redirect(url_for("barangay.relief_monitoring"))
        if quantity_damaged <= 0:
            flash("For a damaged delivery, enter how many packs were damaged (or pick a different condition).", "error")
            return redirect(url_for("barangay.relief_monitoring"))
    if quantity_received > expected:
        flash(f"The barangay can't receive more than the {expected:,} food packs that were released.", "error")
        return redirect(url_for("barangay.relief_monitoring"))

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

    # Photo proof: REQUIRED when the barangay reports a partial or damaged
    # delivery (CSWDO/MSWDO needs evidence before sending a replacement);
    # OPTIONAL when everything arrived complete.
    if condition in ("partial", "damaged") and not saved_names:
        flash("Attach a photo of the delivery - proof is required when packs are short or damaged.", "error")
        return redirect(url_for("barangay.relief_monitoring"))

    rec.received_by = received_by
    rec.condition = condition
    rec.quantity_received = quantity_received
    rec.quantity_damaged = quantity_damaged
    rec.time_received = ph_now().time()
    if saved_names:
        rec.validation_type = "photo"
        rec.validation_file = ",".join(saved_names)
    else:
        rec.validation_type = None
    rec.status = "confirmed"
    # The barangay's validation closes out the trip.
    rec.dispatch_status = "delivered"
    rec.submitted_by = current_user.user_id

    _record_barangay_receipt(rec)
    _return_damaged_packs(rec)

    db.session.add(ActivityLog(
        actor_id=current_user.user_id, action_type="distribution_receipt_confirmed",
        description=f"{rec.barangay.barangay_name} confirmed receipt of D-{rec.distribution_date.year}-{rec.distribution_id:03d} - "
                    f"{rec.received_count:,} of {rec.quantity_released or 0:,} food packs received"
                    + (f", {rec.damaged_count:,} damaged" if rec.damaged_count else "")
                    + f" ({condition}), received by {received_by}",
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
    # Only usable packs enter stock - what physically arrived, minus any the
    # barangay flagged as damaged (see DistributionRecord.good_count).
    usable = rec.good_count
    ref = f"D-{rec.distribution_date.year}-{rec.distribution_id:03d}"
    detail = ""
    if rec.received_count != (rec.quantity_released or 0):
        detail += f", {rec.received_count:,} of {rec.quantity_released or 0:,} released received"
    if rec.damaged_count:
        detail += f", {rec.damaged_count:,} damaged"
    inv.quantity_available = (inv.quantity_available or 0) + usable
    inv.updated_by = current_user.user_id
    db.session.add(BarangayStockLog(
        barangay_id=rec.barangay_id, item_type="food_pack", item_name="Food Packs",
        delta=usable, source_type="delivery",
        distribution_id=rec.distribution_id, updated_by=current_user.user_id,
        reason=f"Received delivery {ref}{detail}",
    ))
    alloc = rec.allocation
    if alloc and alloc.barangay_report_id:
        rep = BarangayReport.query.get(alloc.barangay_report_id)
        if rep and rep.status == "approved":
            rep.status = "fulfilled"


def _return_damaged_packs(rec):
    """Damaged packs never enter the barangay's usable stock (see
    _record_barangay_receipt's `good_count`-only bump) - they physically stay
    with/come back to whichever office fulfilled the delivery. Credit them
    back to that office's warehouse under a distinct "food_pack_damaged" item
    so they're visible for disposal/write-off decisions without ever being
    counted in the "food_pack" figure the allocation/prediction pipeline
    reads. Called once, right after confirm_receipt sets rec.quantity_damaged
    (the route's own "already confirmed" guard keeps this from double-firing)."""
    if not rec.damaged_count:
        return
    alloc = rec.allocation
    office_id = alloc.fulfilling_office_id if alloc else None
    if not office_id:
        return

    inv = WarehouseInventory.query.filter_by(
        office_id=office_id, item_type="food_pack_damaged"
    ).first()
    if inv is None:
        inv = WarehouseInventory(
            office_id=office_id, item_type="food_pack_damaged",
            item_name="Damaged Food Packs (Returned)", unit="packs", quantity_available=0,
        )
        db.session.add(inv)
    inv.quantity_available = (inv.quantity_available or 0) + rec.damaged_count
    inv.updated_by = current_user.user_id

    ref = f"D-{rec.distribution_date.year}-{rec.distribution_id:03d}"
    office_name = alloc.fulfilling_office.office_name if alloc.fulfilling_office else "the warehouse"
    db.session.add(WarehouseStockLog(
        office_id=office_id, item_type="food_pack_damaged", item_name="Damaged Food Packs (Returned)",
        delta=rec.damaged_count, source_type="returned_damaged",
        reason=f"Damaged on delivery {ref} to Brgy. {rec.barangay.barangay_name} - returned for disposal/write-off",
        updated_by=current_user.user_id,
    ))

    # Mirror the same event on the barangay's own ledger - delta 0 since the
    # damaged packs never entered BarangayInventory to begin with (see
    # _record_barangay_receipt); this row exists purely so the barangay's own
    # Movement History shows where the damaged packs went instead of them
    # just disappearing from the count.
    db.session.add(BarangayStockLog(
        barangay_id=rec.barangay_id, item_type="food_pack", item_name="Food Packs",
        delta=0, source_type="damaged_return", distribution_id=rec.distribution_id,
        updated_by=current_user.user_id,
        reason=f"{rec.damaged_count:,} damaged packs from {ref} returned to {office_name}",
    ))


# ---------------------------------------------------------------------------
# Inventory - the barangay's own food-pack stock. A plain +/- ledger for
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

    # Lifetime totals for the stat cards - unaffected by the Movement History
    # filters below, same convention as the CSWDO/PSWDO warehouse pages (the
    # filter narrows the list, not the running totals).
    all_logs = BarangayStockLog.query.filter_by(barangay_id=barangay.barangay_id).all()
    received = sum(l.delta for l in all_logs if l.delta > 0)
    given_out = sum(-l.delta for l in all_logs if l.delta < 0)

    type_filter = request.args.get("type", "all")
    date_filter = request.args.get("date", "")
    logs_q = BarangayStockLog.query.filter_by(barangay_id=barangay.barangay_id)
    if type_filter != "all":
        logs_q = logs_q.filter(BarangayStockLog.source_type == type_filter)
    if date_filter:
        try:
            day = datetime.strptime(date_filter, "%Y-%m-%d").date()
            logs_q = logs_q.filter(db.func.date(BarangayStockLog.created_at) == day)
        except ValueError:
            date_filter = ""
    logs = logs_q.order_by(BarangayStockLog.created_at.desc()).limit(30).all()

    # Delivery/damaged-return log rows link back to the DistributionRecord
    # they came from - fetched in one query so the Movement History can show
    # a released/good/short/damaged breakdown on click, without a query per row.
    distribution_ids = {
        l.distribution_id for l in logs
        if l.source_type in ("delivery", "damaged_return") and l.distribution_id
    }
    delivery_recs = {}
    if distribution_ids:
        for rec in DistributionRecord.query.filter(
            DistributionRecord.distribution_id.in_(distribution_ids)
        ).all():
            delivery_recs[rec.distribution_id] = rec

    families = Family.query.filter_by(
        barangay_id=barangay.barangay_id, is_active=True
    ).order_by(Family.purok, Family.family_name).all()

    return render_template(
        "barangay/inventory.html",
        barangay=barangay, on_hand=on_hand, logs=logs, families=families,
        received=received, given_out=given_out, delivery_recs=delivery_recs,
        type_filter=type_filter, date_filter=date_filter,
    )


def _record_barangay_distribution(barangay_id, amount, reason, family_id=None):
    """The one place barangay stock ever decreases (see inventory_record's
    docstring) - shared by the manual "Record Distribution" form on the
    Inventory page and the per-family "Mark Received" checklist on a
    fulfilled Barangay Report (mark_family_received below), so both write
    to the same BarangayInventory/BarangayStockLog ledger and can never
    disagree with each other or with the GIS map's stock-adequacy rating.

    `family_id` optionally tags the log with which registered Family this
    went to - set by either caller - so a family's distribution history is
    always the same one query (BarangayStockLog.family_id) regardless of
    whether the pack was tied to a report or handed out ad hoc.

    Returns an error message string when there isn't enough stock on hand
    (caller should flash it and bail without committing), or None on
    success (caller still owns the commit).
    """
    inv = BarangayInventory.query.filter_by(
        barangay_id=barangay_id, item_type="food_pack"
    ).first()
    on_hand = inv.quantity_available if inv else 0
    if inv is None or on_hand < amount:
        return f"You only have {on_hand:,} food packs on hand."

    inv.quantity_available = on_hand - amount
    inv.updated_by = current_user.user_id
    db.session.add(BarangayStockLog(
        barangay_id=barangay_id, item_type="food_pack", item_name="Food Packs",
        delta=-amount, source_type="distribution", reason=reason, family_id=family_id,
        updated_by=current_user.user_id,
    ))
    return None


@barangay_bp.route("/inventory/record", methods=["POST"])
@login_required
@role_required("barangay_user")
def inventory_record():
    """Barangay-side stock write - DISTRIBUTION ONLY. Stock only ever comes IN
    automatically, via a validated delivery (see _record_barangay_receipt,
    called from confirm_receipt) - a barangay account has no way to add stock
    by hand here, only record having handed packs out to residents. (A manual
    "Adjust Count" add/subtract used to live here too; removed on purpose.)

    This is the generic/manual path - it also doubles as the "Mark Received"
    checklist's more flexible sibling: an optional family picker lets the
    barangay name who this went to even when that family isn't tied to any
    report at all (a resident not on this event's affected list, an older
    profile, etc.) - see mark_family_received for the report-scoped version."""
    barangay = _own_barangay_or_404()
    amount = request.form.get("amount", type=int) or 0
    reason = request.form.get("reason", "").strip() or None

    if amount <= 0:
        flash("Enter a number greater than zero.", "error")
        return redirect(url_for("barangay.inventory"))

    family_id = request.form.get("family_id", type=int)
    family = None
    if family_id:
        family = Family.query.filter_by(family_id=family_id, barangay_id=barangay.barangay_id).first()
        if not family:
            flash("That family isn't in your Family Profiles.", "error")
            return redirect(url_for("barangay.inventory"))

    if not reason:
        reason = f"Distributed to {family.family_name}" if family else "Distributed to residents"

    err = _record_barangay_distribution(barangay.barangay_id, amount, reason, family_id=family.family_id if family else None)
    if err:
        flash(err, "error")
        return redirect(url_for("barangay.inventory"))

    db.session.commit()
    who = f"to {family.family_name}" if family else "to residents"
    flash(f"Recorded {amount:,} food packs distributed {who}.", "success")
    return redirect(url_for("barangay.inventory"))


@barangay_bp.route("/damage-report/<int:report_id>/distribute/<int:raf_id>", methods=["POST"])
@login_required
@role_required("barangay_user")
def mark_family_received(report_id, raf_id):
    """Marks one affected family (from the report's checklist) as having
    received its food pack(s) - the per-family counterpart to
    inventory_record. Only actionable once the report is "fulfilled" (the
    delivery itself has already been confirmed received, so the packs are
    actually on hand to give out - see confirm_receipt).

    Deducts `packs_given` from the same BarangayInventory/BarangayStockLog
    ledger inventory_record uses (via _record_barangay_distribution), so
    "who got a pack" and "how much stock is left" can never drift apart."""
    report = _get_own_report_or_404(report_id)
    if report.status != "fulfilled":
        flash("You can only record distribution once the delivery has been confirmed received.", "error")
        return redirect(url_for("barangay.view_damage_report", report_id=report.report_id))

    raf = next((rf for rf in report.affected_families_list if rf.id == raf_id), None)
    if not raf:
        abort(404)
    if raf.received:
        flash(f"{raf.family_name} is already marked as received.", "error")
        return redirect(url_for("barangay.view_damage_report", report_id=report.report_id))

    packs = request.form.get("packs_given", type=int)
    if packs is None:
        packs = raf.suggested_packs
    if packs <= 0:
        flash("Enter a number of packs greater than zero.", "error")
        return redirect(url_for("barangay.view_damage_report", report_id=report.report_id))

    err = _record_barangay_distribution(
        report.barangay_id, packs, f"{raf.family_name} - {report.ref}", family_id=raf.family_id
    )
    if err:
        flash(err, "error")
        return redirect(url_for("barangay.view_damage_report", report_id=report.report_id))

    raf.received = True
    raf.received_at = ph_now()
    raf.packs_given = packs
    raf.received_by = current_user.user_id
    db.session.commit()
    flash(f"Marked {raf.family_name} as received ({packs:,} food pack{'s' if packs != 1 else ''}).", "success")
    return redirect(url_for("barangay.view_damage_report", report_id=report.report_id))


@barangay_bp.route("/damage-report/<int:report_id>/distribute/<int:raf_id>/undo", methods=["POST"])
@login_required
@role_required("barangay_user")
def undo_family_received(report_id, raf_id):
    """Reverses a mark_family_received mistake - adds the packs back to
    on-hand stock (logged as an 'adjustment', not another 'distribution',
    since nothing actually went back out to anyone) and clears the
    family's received state so it can be marked again correctly."""
    report = _get_own_report_or_404(report_id)
    raf = next((rf for rf in report.affected_families_list if rf.id == raf_id), None)
    if not raf or not raf.received:
        abort(404)

    inv = BarangayInventory.query.filter_by(
        barangay_id=report.barangay_id, item_type="food_pack"
    ).first()
    if inv:
        inv.quantity_available += raf.packs_given
        inv.updated_by = current_user.user_id
        db.session.add(BarangayStockLog(
            barangay_id=report.barangay_id, item_type="food_pack", item_name="Food Packs",
            delta=raf.packs_given, source_type="adjustment",
            reason=f"Undo: {raf.family_name} - {report.ref}",
            updated_by=current_user.user_id,
        ))

    raf.received = False
    raf.received_at = None
    raf.packs_given = 0
    raf.received_by = None
    db.session.commit()
    flash(f"Undid the distribution record for {raf.family_name}.", "success")
    return redirect(url_for("barangay.view_damage_report", report_id=report.report_id))


# ---------------------------------------------------------------------------
# Reports - mirrors app.routes.cswdo's report-generation pattern (report
# cards -> report_view -> PDF/Excel export -> logged + re-downloadable),
# just scoped to this one barangay instead of a municipality. Only 2 of the
# 7 generic report types have a meaningful barangay-scoped equivalent (see
# app.routes.report_data.BARANGAY_REPORT_TYPES) - a barangay has no
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
    # Every event, not just the currently-active one - a report is almost
    # always generated *after* a typhoon has ended, so scoping this filter to
    # status="active" would make every past event unselectable.
    active_events = DisasterEvent.query.order_by(DisasterEvent.start_date.desc()).all()

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

    # "" not None - url_for() drops a None param outright, which would make
    # the generated link carry no event_id at all instead of an explicit
    # "no event filter", and resolve_barangay_filters() would then treat that
    # as "not chosen yet" and silently default back to the active event.
    query_params = {"event_id": filters["event_id"] or "", "days": filters["days"]}
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
        f"{filters['start_date'].strftime('%b %d')} - {ph_today().strftime('%b %d, %Y')}"
    )

    # Report History table - moved here from the now-removed standalone
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
    active_events = relevant_active_events_query([barangay.city_municipality]).all()

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

    filename = f"{report_type}_{ph_now().strftime('%Y%m%d')}.{REPORTS_EXTENSIONS[fmt]}"
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
        flash("No reports have been generated yet - export one first.", "error")
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
            "Content-Disposition": f"attachment; filename={barangay.barangay_name.replace(' ', '_')}_reports_{ph_now().strftime('%Y%m%d')}.zip"
        },
    )


@barangay_bp.route("/reports/export")
@login_required
@role_required("barangay_user")
def reports_export():
    """Lighter CSV export used by the Affected Families' Report History
    table - separate from the PDF/Excel report_export_pdf/excel above,
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

    # Opening the Notifications page is itself the "read" action - no per-item
    # or "Mark all as read" click needed. Unread rows still show highlighted on
    # this render (via was_unread) so the user sees what's new before it clears.
    if unread_count and scope is not None:
        ActivityLog.query.filter(scope, ActivityLog.is_read.is_(False)).update(
            {"is_read": True}, synchronize_session=False
        )
        db.session.commit()

    # Only the categories this barangay's own ActivityLog rows can actually
    # carry (see _own_activity_scope) - no "Warehouse" tab like PSWDO's, since
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
