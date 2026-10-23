# Barangay user pages: reports, family profiles, deliveries, inventory, reports.

import csv
import io
import json
import os
import re
import shutil
import zipfile
from datetime import datetime, timedelta

from app.utils.timezone import ph_now, ph_today

from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, Response, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from app.extensions import db
from app.utils.decorators import role_required
from app.models.office import Office
from app.models.disaster_event import DisasterEvent
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
from app.models.food_pack_batch import BarangayFoodPackBatch, BarangayFoodPackBatchItem
from app.models.activity_log import ActivityLog
from app.models.user import User
from app.utils import weather as weather_service

from app.utils.filters import arg_date, date_range, in_range, iso
from app.routes.pswdo import (
    DISPATCH_STATUS_LABELS, NOTIFICATION_META, DEFAULT_NOTIFICATION_META,
    _shelf_status, NEAR_EXPIRY_DAYS, _lots_from_json, _take_from_batches, _batch_take_order, _refreshed_batch_items,
    _resolve_batch_item_specs, _plan_expiration,
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

DECIDED_REPORT_STATUSES = ("verified", "approved", "fulfilled", "declined")
ACCEPTED_REPORT_STATUSES = ("verified", "approved", "fulfilled")


# Rates how serious a barangay's situation is, using points for damaged houses and affected families.
# More points = higher level: Normal, Monitoring, Needs Assistance, or High Priority.
def _compute_severity(*, affected_families=0, affected_individuals=0,
                      totally_damaged_houses=0, partially_damaged_houses=0,
                      roofs_damaged=0):
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


# The logged-in user's barangay (shows an error if the account has no barangay).
def _own_barangay_or_404():
    barangay = current_user.barangay
    if not barangay:
        abort(404)
    return barangay


# The active disaster event that covers this barangay, if any.
def _active_event(barangay):
    event, applicable_barangay_ids = resolve_effective_event(barangay.city_municipality)
    if event and not event_covers_barangay(applicable_barangay_ids, barangay.barangay_id):
        return None
    return event


# Limits notifications to this barangay only.
def _own_activity_scope():
    barangay = current_user.barangay
    if not barangay:
        return None
    known_types = list(NOTIFICATION_META.keys())
    return db.and_(ActivityLog.barangay_id == barangay.barangay_id, ActivityLog.action_type.in_(known_types))


# Blocks opening a notification that belongs to another barangay.
def _assert_own_activity(log):
    barangay = current_user.barangay
    if not barangay or log.barangay_id != barangay.barangay_id:
        abort(403)


# Clicking a report notification opens the Barangay Report page.
def _damage_report_notification_link(log):
    return url_for("barangay.damage_report")


# Clicking a delivery notification opens the Relief Monitoring page.
def _relief_monitoring_notification_link(log):
    return url_for("barangay.relief_monitoring")


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


NOTIFICATION_CATEGORY_LABELS = {"distribution": "Relief Monitoring"}


# Gets one notification ready for display: icon, color, category and link.
def _notification_view(log):
    meta = NOTIFICATION_META.get(log.action_type, DEFAULT_NOTIFICATION_META)
    link_fn = NOTIFICATION_LINK_BUILDERS.get(log.action_type)
    return {
        "log": log, "icon": meta["icon"], "color": meta["color"],
        "category": meta["category"],
        "category_label": NOTIFICATION_CATEGORY_LABELS.get(meta["category"], meta["category_label"]),
        "link": link_fn(log) if link_fn else None,
    }


# All of this barangay's reports (including drafts), newest first.
def _own_reports_all(barangay_id):
    return BarangayReport.query.filter_by(barangay_id=barangay_id).order_by(
        BarangayReport.created_at.desc()
    ).all()


# This barangay's submitted reports (drafts not included), newest first.
def _own_submitted_reports(barangay_id):
    return BarangayReport.query.filter(
        BarangayReport.barangay_id == barangay_id,
        BarangayReport.status != "draft",
    ).order_by(BarangayReport.created_at.desc()).all()


# Finds a report, but only if it belongs to this barangay.
def _get_own_report_or_404(report_id):
    report = BarangayReport.query.get_or_404(report_id)
    barangay = current_user.barangay
    if not barangay or report.barangay_id != barangay.barangay_id:
        abort(403)
    return report


# Page: /barangay/dashboard - Barangay main dashboard: the active disaster event, report status,
# incoming deliveries, food packs on hand, notifications and weather.
@barangay_bp.route("/dashboard")
@login_required
@role_required("barangay_user")
def dashboard():
    now = ph_now()
    barangay = _own_barangay_or_404()

    primary_event = _active_event(barangay)
    province_event = None
    if primary_event and primary_event.scope == "municipality":
        province_event = blocking_event_for_province()
    elif not primary_event:
        province_event = blocking_event_for_province()

    counted_reports = BarangayReport.query.filter(
        BarangayReport.barangay_id == barangay.barangay_id,
        BarangayReport.status.notin_(("draft", "declined")),
    )

    today_start = datetime.combine(ph_today(), datetime.min.time())
    affected_families = sum(
        r.affected_families or 0 for r in counted_reports.filter(
            BarangayReport.submitted_at >= today_start,
            BarangayReport.submitted_at < today_start + timedelta(days=1),
        ).all()
    )

    event_totals = None
    if primary_event:
        event_reports = counted_reports.filter(
            BarangayReport.event_id == primary_event.event_id
        ).all()
        event_totals = {
            "reports": len(event_reports),
            "affected_families": sum(r.affected_families or 0 for r in event_reports),
            "affected_individuals": sum(r.affected_individuals or 0 for r in event_reports),
            "totally_damaged_houses": sum(r.totally_damaged_houses or 0 for r in event_reports),
            "partially_damaged_houses": sum(r.partially_damaged_houses or 0 for r in event_reports),
        }

    my_reports = _own_submitted_reports(barangay.barangay_id)
    pending_reports = [r for r in my_reports if r.status in ("pending", "returned")]
    returned_reports = [r for r in my_reports if r.status == "returned"]
    recent_reports = my_reports[:4]

    food_packs_allocated = 0
    if primary_event:
        food_packs_allocated = sum(
            a.allocated_quantity for a in AllocationRecord.query.filter_by(
                barangay_id=barangay.barangay_id, event_id=primary_event.event_id,
            ).all()
        )

    my_distributions = DistributionRecord.query.filter_by(barangay_id=barangay.barangay_id).order_by(
        DistributionRecord.distribution_date.desc()
    ).limit(5).all()
    in_transit_count = len([d for d in my_distributions if d.dispatch_status in ("dispatched", "in_transit")])
    awaiting_confirmation = [
        d for d in my_distributions
        if d.dispatch_status in ("dispatched", "in_transit", "delivered") and d.status != "confirmed"
    ]

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
        event_totals=event_totals,
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


# Page: /barangay/dashboard/weather - Sends the weather data for the barangay's dashboard widget (its municipality's weather).
@barangay_bp.route("/dashboard/weather")
@login_required
@role_required("barangay_user")
def dashboard_weather():
    barangay = _own_barangay_or_404()
    city = barangay.city_municipality
    return weather_service.get_dashboard_snapshot([city] if city else [])


# Saves the photos attached to a barangay report (only allowed image types).
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


# Applies the event and date filters to the report history list.
def _report_history_extra_filters(reports):
    event_filter = request.args.get("event_id", type=int)
    date_from, date_to = date_range(request.args)
    if event_filter:
        reports = [r for r in reports if r.event_id == event_filter]
    reports = [r for r in reports if in_range(r.submitted_at, date_from, date_to)]
    return reports, {"event_filter": event_filter, "date_from": iso(date_from), "date_to": iso(date_to)}


# Page: /barangay/damage-report - Barangay Report page: create situation reports for the CSWDO/MSWDO,
# see open drafts, and track past reports and their review status.
@barangay_bp.route("/damage-report")
@login_required
@role_required("barangay_user")
def damage_report():
    barangay = _own_barangay_or_404()
    primary_event = _active_event(barangay)
    tab = request.args.get("tab", "dashboard")

    all_reports = _own_reports_all(barangay.barangay_id)

    active_event_ids = (primary_event.event_id, None) if primary_event else (None,)

    # True if a report is for the current event and still open (draft, pending or returned).
    def _is_active_open(r):
        return r.event_id in active_event_ids and r.status in ("draft", "pending", "returned")

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
        all_history = [r for r in all_reports if not _is_active_open(r)]
        history_reports, extra = _report_history_extra_filters(history_reports)
        ctx.update({
            "decided_reports": history_reports,
            "history_statuses": history_statuses,
            "search_query": search_query,
            "status_filter": status_filter,
            "filter_events": sorted({r.event for r in all_history if r.event}, key=lambda e: e.start_date, reverse=True),
            **extra,
        })
    else:
        open_reports = [r for r in all_reports if _is_active_open(r)]
        returned_reports = [r for r in open_reports if r.status == "returned"]

        open_rows = [{"report": r} for r in open_reports]

        ctx.update({
            "open_rows": open_rows,
            "returned_reports": returned_reports,
        })

    return render_template("barangay/damage_report.html", **ctx)


# Download: /barangay/damage-report/export - Downloads the barangay's reviewed reports as a CSV (spreadsheet) file.
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
    decided_reports, _ = _report_history_extra_filters(decided_reports)

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


# Page: /barangay/damage-report/<int:report_id>/view - Shows one report and its review status.
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


# Gets everything the report form needs:
# the events to choose from, the family checklist, and any saved values.
def _report_form_context(barangay, report=None):
    event_options = events_covering_barangay(barangay.city_municipality, barangay.barangay_id)
    default_event = (report.event if report and report.event else None) or _active_event(barangay)
    if report and report.event and report.event not in event_options:
        event_options = [report.event] + event_options
    default_event_id = default_event.event_id if default_event else None

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
    manual_mode = bool(report and not report.affected_families_list and (report.affected_families or report.affected_individuals))

    captain = User.query.filter(
        User.barangay_id == barangay.barangay_id, User.is_active.is_(True),
        db.or_(User.designation.ilike("%captain%"), User.designation.ilike("%punong%"),
               User.designation.ilike("%kapitan%")),
    ).first()
    submitted_by_default = (report.submitted_by_name if report and report.submitted_by_name
                            else (captain.name if captain else current_user.name))

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
        "submitted_by_default": submitted_by_default,
    }


# Page: /barangay/damage-report/new - Opens a blank report form.
@barangay_bp.route("/damage-report/new")
@login_required
@role_required("barangay_user")
def new_damage_report():
    barangay = _own_barangay_or_404()
    return render_template("barangay/damage_report_form.html", **_report_form_context(barangay))


# Page: /barangay/damage-report/<int:report_id>/edit - Opens a report for editing.
# Verified (reviewed) reports are locked and can't be edited.
@barangay_bp.route("/damage-report/<int:report_id>/edit")
@login_required
@role_required("barangay_user")
def edit_damage_report(report_id):
    report = _get_own_report_or_404(report_id)
    if report.status not in ("draft", "pending", "returned"):
        flash("Verified reports are locked and can no longer be edited.", "error")
        return redirect(url_for("barangay.view_damage_report", report_id=report.report_id))
    return render_template("barangay/damage_report_form.html", **_report_form_context(report.barangay, report))


# Action: /barangay/damage-report/<int:report_id>/delete - Deletes a draft report and its photos. Submitted reports stay on record.
@barangay_bp.route("/damage-report/<int:report_id>/delete", methods=["POST"])
@login_required
@role_required("barangay_user")
def delete_damage_report(report_id):
    if not db.session.get(BarangayReport, report_id):
        flash("That draft was already deleted.", "info")
        return redirect(url_for("barangay.damage_report"))
    report = _get_own_report_or_404(report_id)
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


# Saves the report's affected families: either ticked from the Family Profiles checklist,
# or typed in manually as totals.
def _apply_affected_families(report):
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


# Copies the report form (date, time, flood level, damage, people affected, notes) into the report.
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

    report.roofs_damaged = 0
    report.wind_signal = None

    _apply_affected_families(report)
    report.totally_damaged_houses = request.form.get("totally_damaged_houses", type=int) or 0
    report.partially_damaged_houses = request.form.get("partially_damaged_houses", type=int) or 0

    report.flood_level = _compute_severity(
        affected_families=report.affected_families,
        affected_individuals=report.affected_individuals,
        totally_damaged_houses=report.totally_damaged_houses,
        partially_damaged_houses=report.partially_damaged_houses,
        roofs_damaged=report.roofs_damaged,
    )

    report.requested_food_packs = request.form.get("requested_food_packs", type=int) or 0
    if report.requested_food_packs < 0:
        report.requested_food_packs = 0

    report.remarks = request.form.get("remarks", "").strip() or None
    report.submitted_by_name = request.form.get("submitted_by_name", "").strip() or current_user.name
    report.submitted_by_designation = request.form.get("submitted_by_designation", "").strip() or current_user.designation


# Picks which disaster event the report is for (the one chosen, if allowed).
def _resolve_submitted_event_id(barangay, report):
    submitted = request.form.get("event_id", type=int)
    options = events_covering_barangay(barangay.city_municipality, barangay.barangay_id)
    allowed_ids = {e.event_id for e in options}
    if report and report.event_id:
        allowed_ids.add(report.event_id)
    if submitted and submitted in allowed_ids:
        return submitted
    return options[0].event_id if options else None


# Loads the report being edited, or starts a new one.
def _get_or_create_report(barangay, report_id, event_id):
    if report_id:
        report = _get_own_report_or_404(report_id)
        if report.status not in ("draft", "pending", "returned"):
            abort(403)
        if event_id is not None and report.event_id != event_id:
            report.event_id = event_id
        return report, False
    report = BarangayReport(barangay_id=barangay.barangay_id, event_id=event_id)
    db.session.add(report)
    return report, True


# Action: /barangay/damage-report/save-draft - Saves a report as a draft (not yet sent to the CSWDO/MSWDO).
@barangay_bp.route("/damage-report/save-draft", methods=["POST"])
@login_required
@role_required("barangay_user")
def save_damage_report_draft():
    barangay = _own_barangay_or_404()
    report_id = request.form.get("report_id", type=int)
    existing = _get_own_report_or_404(report_id) if report_id else None
    event_id = _resolve_submitted_event_id(barangay, existing)

    report, is_new = _get_or_create_report(barangay, report_id, event_id)
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


# Action: /barangay/damage-report/submit - Submits a report to the CSWDO/MSWDO for review.
# The name of the person submitting is required.
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


# Action: /barangay/damage-report/<int:report_id>/unsubmit - Pulls a submitted report back to draft (only while it hasn't been reviewed yet).
@barangay_bp.route("/damage-report/<int:report_id>/unsubmit", methods=["POST"])
@login_required
@role_required("barangay_user")
def unsubmit_damage_report(report_id):
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


# Finds a family, but only if it belongs to this barangay.
def _get_own_family_or_404(family_id):
    barangay = _own_barangay_or_404()
    family = Family.query.filter_by(family_id=family_id, barangay_id=barangay.barangay_id).first()
    if not family:
        abort(404)
    return family


# Copies the family form (name, head, purok, contact, members, PWDs, seniors, children)
# into the family profile.
def _apply_family_form(family):
    family.family_name = request.form.get("family_name", "").strip()
    family.head_name = request.form.get("head_name", "").strip() or None
    family.purok = request.form.get("purok", "").strip() or None
    family.contact_number = request.form.get("contact_number", "").strip() or None
    family.member_count = max(1, request.form.get("member_count", type=int) or 1)
    family.pwd_count = max(0, request.form.get("pwd_count", type=int) or 0)
    family.senior_count = max(0, request.form.get("senior_count", type=int) or 0)
    family.children_count = max(0, request.form.get("children_count", type=int) or 0)


# Page: /barangay/family-profiles - Family Profiles page: the barangay's list of registered families (active or archived).
# Used as a checklist when filing reports and when giving out food packs.
@barangay_bp.route("/family-profiles")
@login_required
@role_required("barangay_user")
def family_profiles():
    barangay = _own_barangay_or_404()
    show_archived = request.args.get("archived") == "1"

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


# Action: /barangay/family-profiles/add - Adds a new family profile.
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


# Action: /barangay/family-profiles/<int:family_id>/edit - Saves changes to a family profile.
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


# Action: /barangay/family-profiles/<int:family_id>/archive - Archives a family (hides it from lists) or restores it.
@barangay_bp.route("/family-profiles/<int:family_id>/archive", methods=["POST"])
@login_required
@role_required("barangay_user")
def family_profile_archive(family_id):
    family = _get_own_family_or_404(family_id)
    family.is_active = not family.is_active
    db.session.commit()
    flash(f"{family.family_name} {'restored' if family.is_active else 'archived'}.", "success")
    return redirect(url_for("barangay.family_profiles", archived=request.args.get("archived")))


# Action: /barangay/family-profiles/<int:family_id>/delete - Deletes a family. Not allowed if it was already listed in a report (archive it instead).
@barangay_bp.route("/family-profiles/<int:family_id>/delete", methods=["POST"])
@login_required
@role_required("barangay_user")
def family_profile_delete(family_id):
    family = _get_own_family_or_404(family_id)
    if ReportAffectedFamily.query.filter_by(family_id=family.family_id).first():
        flash(f"{family.family_name} has been cited on a report and can't be deleted - archive it instead.", "error")
        return redirect(url_for("barangay.family_profiles"))
    name = family.family_name
    db.session.delete(family)
    db.session.commit()
    flash(f"{name} deleted.", "success")
    return redirect(url_for("barangay.family_profiles"))


# The official barangay letterhead for printed pages.
def _letterhead(user, barangay):
    from app.routes.report_data import build_letterhead
    return build_letterhead(user, barangay=barangay)

# One family's row on the Relief Distribution Sheet:
# last name, first name, number of dependents and food packs.
def _rds_row(family, packs):
    last = re.sub(r"\s+family$", "", (family.family_name or "").strip(), flags=re.I)
    first = (family.head_name or "").strip()
    if last and first.lower().endswith(" " + last.lower()):
        first = first[: -len(last)].strip()
    return {
        "last_name": last,
        "first_name": first,
        "dependents": max((family.member_count or 0) - 1, 0),
        "packs": packs,
    }


# The header of the Relief Distribution Sheet: region, province, municipality, barangay and disaster.
def _rds_header(barangay, event=None):
    disaster_type = occurred_on = ""
    if event is not None:
        disaster_type = f"{(event.event_type or 'other').title()} - {event.event_name}"
        occurred_on = event.start_date.strftime("%B %d, %Y") if event.start_date else ""
    return {
        "region": "Region I (Ilocos Region)",
        "province": "Pangasinan",
        "city": barangay.city_municipality,
        "barangay": barangay.barangay_name,
        "disaster_type": disaster_type,
        "occurred_on": occurred_on,
    }


# All family rows for the Relief Distribution Sheet.
def _family_print_rows(families):
    return [
        _rds_row(f, f.packs_given if f.received else f.suggested_packs)
        for f in families
    ]


# Page: /barangay/family-profiles/print - Prepares the print page for the families ticked on Family Profiles.
@barangay_bp.route("/family-profiles/print")
@login_required
@role_required("barangay_user")
def print_families_selected():
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


# Action: /barangay/family-profiles/print/generate - Builds the printable Relief Distribution Sheet for the selected families.
@barangay_bp.route("/family-profiles/print/generate", methods=["POST"])
@login_required
@role_required("barangay_user")
def print_families_generate():
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
        rows.append(_rds_row(f, packs if packs and packs > 0 else f.suggested_packs))

    return render_template(
        "barangay/print_family_list.html",
        barangay=barangay, title="Relief Distribution Sheet",
        rows=rows, rds=_rds_header(barangay),
        letterhead=_letterhead(current_user, barangay=barangay),
    )


# Page: /barangay/damage-report/<int:report_id>/print-families - Prints the Relief Distribution Sheet for the affected families listed in a report.
@barangay_bp.route("/damage-report/<int:report_id>/print-families")
@login_required
@role_required("barangay_user")
def print_report_families(report_id):
    report = _get_own_report_or_404(report_id)
    if not report.affected_families_list:
        flash("This report has no affected-families checklist to print.", "error")
        return redirect(url_for("barangay.view_damage_report", report_id=report.report_id))

    return render_template(
        "barangay/print_family_list.html",
        barangay=report.barangay, title="Relief Distribution Sheet",
        rows=_family_print_rows(report.affected_families_list),
        rds=_rds_header(report.barangay, report.event),
        letterhead=_letterhead(current_user, barangay=report.barangay),
    )


BARANGAY_DELIVERY_STEPS = ["requested", "approved", "preparing", "issued", "in_transit", "validated"]
BARANGAY_STEP_LABELS = {
    "requested": "Requested", "approved": "Approved", "preparing": "Preparing",
    "issued": "Issued (released)", "in_transit": "On the Way",
    "validated": "Received (you confirm)",
}


# Which step of the progress tracker a delivery is on.
def _delivery_step_index(dist):
    if dist.status == "confirmed":
        return 5
    if dist.dispatch_status == "in_transit":
        return 4
    if dist.dispatch_status == "dispatched" or dist.is_issued:
        return 3
    return 2


# Page: /barangay/relief-monitoring - Relief Monitoring page: track food pack deliveries coming to the barangay,
# and confirm receipt when they arrive.
@barangay_bp.route("/relief-monitoring")
@login_required
@role_required("barangay_user")
def relief_monitoring():
    barangay = _own_barangay_or_404()

    distributions = DistributionRecord.query.filter_by(barangay_id=barangay.barangay_id).order_by(
        DistributionRecord.distribution_date.desc(),
        DistributionRecord.distribution_id.desc(),
    ).all()

    _CONFIRMABLE = ("dispatched", "in_transit", "delivered")
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
        })

    search_query = (request.args.get("q") or "").strip()
    if search_query:
        ql = search_query.lower()

        # True if a delivery matches the search text.
        def _row_matches(row):
            office = row["fulfilling_office"].office_name if row["fulfilling_office"] else ""
            return any(ql in field.lower() for field in (
                row["label"], row["ref"], row["request_ref"], office,
            ))

        delivery_rows = [r for r in delivery_rows if _row_matches(r)]


    default_status = "all" if search_query else "transit"
    status_filter = request.args.get("status", default_status)
    if status_filter not in ("transit", "received", "all"):
        status_filter = default_status
    if status_filter == "transit":
        delivery_rows = [r for r in delivery_rows if r["distribution"].status != "confirmed"]
    elif status_filter == "received":
        delivery_rows = [r for r in delivery_rows if r["distribution"].status == "confirmed"]

    event_filter = request.args.get("event_id", type=int)
    date_from, date_to = date_range(request.args)
    if event_filter:
        delivery_rows = [r for r in delivery_rows if r["distribution"].allocation
                         and r["distribution"].allocation.event_id == event_filter]
    delivery_rows = [r for r in delivery_rows if in_range(r["distribution"].distribution_date, date_from, date_to)]

    return render_template(
        "barangay/relief_monitoring.html",
        barangay=barangay,
        delivery_rows=delivery_rows,
        search_query=search_query,
        status_filter=status_filter,
        event_filter=event_filter, date_from=iso(date_from), date_to=iso(date_to),
        filter_events=sorted({d.allocation.event for d in distributions if d.allocation and d.allocation.event},
                             key=lambda e: e.start_date, reverse=True),
        total_deliveries=len(distributions),
        in_transit_count=in_transit_count,
        received_count=received_count,
        total_packs=total_packs,
        dispatch_status_labels=DISPATCH_STATUS_LABELS,
        delivery_steps=BARANGAY_DELIVERY_STEPS,
        step_labels=BARANGAY_STEP_LABELS,
    )


# Finds a delivery, but only if it is for this barangay.
def _get_own_distribution_or_404(distribution_id):
    rec = DistributionRecord.query.get_or_404(distribution_id)
    barangay = current_user.barangay
    if not barangay or rec.barangay_id != barangay.barangay_id:
        abort(403)
    return rec


# Action: /barangay/relief-monitoring/<int:distribution_id>/confirm-receipt - Confirms the barangay received a delivery: who received it,
# how many arrived, and the condition (complete, partial or damaged).
@barangay_bp.route("/relief-monitoring/<int:distribution_id>/confirm-receipt", methods=["POST"])
@login_required
@role_required("barangay_user")
def confirm_receipt(distribution_id):
    rec = _get_own_distribution_or_404(distribution_id)

    if rec.dispatch_status not in ("dispatched", "in_transit", "delivered") or rec.status == "confirmed":
        flash("This delivery isn't ready to be confirmed - it may have already been received.", "error")
        return redirect(url_for("barangay.relief_monitoring"))

    received_by = request.form.get("received_by", "").strip() or current_user.name
    condition = request.form.get("condition", "")

    if condition not in ("complete", "partial", "damaged"):
        flash("Select the condition the delivery arrived in.", "error")
        return redirect(url_for("barangay.relief_monitoring"))

    expected = rec.quantity_released or 0
    if condition == "complete":
        quantity_received, quantity_damaged = expected, 0
    elif condition == "partial":
        quantity_received = request.form.get("quantity_received", type=int) or 0
        quantity_damaged = 0
        if quantity_received <= 0:
            flash("Enter how many food packs the barangay actually received.", "error")
            return redirect(url_for("barangay.relief_monitoring"))
    else:
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


# Adds the good packs from a confirmed delivery to the barangay's stock
# (with the batch expiration dates that came with it).
def _record_barangay_receipt(rec):
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
    usable = rec.good_count
    ref = f"D-{rec.distribution_date.year}-{rec.distribution_id:03d}"
    detail = ""
    if rec.received_count != (rec.quantity_released or 0):
        detail += f", {rec.received_count:,} of {rec.quantity_released or 0:,} released received"
    if rec.damaged_count:
        detail += f", {rec.damaged_count:,} damaged"
    # Add the good packs to the barangay's stock.
    inv.quantity_available = (inv.quantity_available or 0) + usable
    inv.updated_by = current_user.user_id
    db.session.add(BarangayStockLog(
        barangay_id=rec.barangay_id, item_type="food_pack", item_name="Food Packs",
        delta=usable, source_type="delivery",
        distribution_id=rec.distribution_id, updated_by=current_user.user_id,
        reason=f"Received delivery {ref}{detail}",
    ))

    alloc = rec.allocation
    if usable:
        for received_date, qty, item_specs in _lots_from_json(rec.batch_lots, usable, ph_today()):
            _create_barangay_food_pack_batch(rec.barangay_id, qty, received_date, current_user.user_id, item_specs)

    if alloc and alloc.barangay_report_id:
        rep = BarangayReport.query.get(alloc.barangay_report_id)
        if rep and rep.status == "approved":
            rep.status = "fulfilled"


# Sends the damaged packs from a delivery back to the supplying warehouse's damaged stock.
def _return_damaged_packs(rec):
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

    db.session.add(BarangayStockLog(
        barangay_id=rec.barangay_id, item_type="food_pack", item_name="Food Packs",
        delta=0, source_type="damaged_return", distribution_id=rec.distribution_id,
        updated_by=current_user.user_id,
        reason=f"{rec.damaged_count:,} damaged packs from {ref} returned to {office_name}",
    ))


# Keeps the barangay's food pack batches matching its actual stock count,
# and moves expired batches out of usable stock.
def _sync_barangay_food_pack_batches(barangay_id):
    fp = BarangayInventory.query.filter_by(barangay_id=barangay_id, item_type="food_pack").first()
    on_hand = fp.quantity_available if fp else 0

    active_batches = _batch_take_order(
        BarangayFoodPackBatch.query.filter_by(barangay_id=barangay_id, status="active").all()
    )

    batch_total = sum(b.quantity_remaining for b in active_batches)
    excess = batch_total - on_hand
    if excess > 0:
        for b in active_batches:
            if excess <= 0:
                break
            trim = min(b.quantity_remaining, excess)
            b.quantity_remaining -= trim
            excess -= trim
        active_batches = [b for b in active_batches if b.quantity_remaining > 0]
    elif excess < 0:
        active_batches.append(_create_barangay_food_pack_batch(barangay_id, -excess, ph_today()))

    today = ph_today()
    expired_batches = [b for b in active_batches if b.expiration_date < today and b.quantity_remaining > 0]
    if not expired_batches:
        db.session.commit()
        return

    expired_qty = sum(b.quantity_remaining for b in expired_batches)
    if fp:
        fp.quantity_available = max((fp.quantity_available or 0) - expired_qty, 0)

    expired_item = BarangayInventory.query.filter_by(barangay_id=barangay_id, item_type="food_pack_expired").first()
    if expired_item is None:
        expired_item = BarangayInventory(
            barangay_id=barangay_id, item_type="food_pack_expired",
            item_name="Food Packs (Expired)", unit="packs", quantity_available=0,
        )
        db.session.add(expired_item)
    expired_item.quantity_available = (expired_item.quantity_available or 0) + expired_qty

    db.session.add(BarangayStockLog(
        barangay_id=barangay_id, item_type="food_pack", item_name="Food Packs",
        delta=-expired_qty, source_type="expired",
        reason=f"{expired_qty:,} food packs passed their expiration date",
    ))
    db.session.add(BarangayStockLog(
        barangay_id=barangay_id, item_type="food_pack_expired", item_name="Food Packs (Expired)",
        delta=expired_qty, source_type="expired",
        reason=f"{expired_qty:,} food packs moved to Expired after passing their expiration date",
    ))

    for b in expired_batches:
        b.status = "expired"
        b.expired_at = ph_now()

    db.session.commit()


# Creates a new barangay food pack batch with its items.
# The batch expires on the date of its earliest-expiring item.
def _create_barangay_food_pack_batch(barangay_id, quantity, received_date, updated_by=None, item_specs=None):
    from datetime import timedelta
    rows = _resolve_batch_item_specs(received_date, item_specs)
    batch = BarangayFoodPackBatch(
        barangay_id=barangay_id, quantity_remaining=quantity,
        received_date=received_date,
        expiration_date=min((d for _, _, d, _ in rows), default=received_date + timedelta(days=180)),
        updated_by=updated_by,
    )
    db.session.add(batch)
    db.session.flush()
    for component_id, custom_name, d, qty_label in rows:
        db.session.add(BarangayFoodPackBatchItem(
            batch_id=batch.batch_id, component_id=component_id,
            custom_name=custom_name, quantity_label=qty_label, expiration_date=d,
        ))
    return batch


# Page: /barangay/inventory - Inventory page: the barangay's food packs on hand, total received and given out,
# batches with expiration dates, and stock movement history.
@barangay_bp.route("/inventory")
@login_required
@role_required("barangay_user")
def inventory():
    barangay = _own_barangay_or_404()
    _sync_barangay_food_pack_batches(barangay.barangay_id)
    inv = BarangayInventory.query.filter_by(
        barangay_id=barangay.barangay_id, item_type="food_pack"
    ).first()
    on_hand = inv.quantity_available if inv else 0

    all_logs = BarangayStockLog.query.filter_by(barangay_id=barangay.barangay_id).all()
    received = sum(l.delta for l in all_logs if l.delta > 0)
    given_out = sum(-l.delta for l in all_logs if l.delta < 0)

    logs_q, type_filter, date_from, date_to = _inventory_movements_query(barangay)
    per_page = 20
    total_logs = logs_q.count()
    total_pages = max((total_logs + per_page - 1) // per_page, 1)
    page = min(max(request.args.get("page", 1, type=int), 1), total_pages)
    logs = (logs_q.order_by(BarangayStockLog.created_at.desc(), BarangayStockLog.log_id.desc())
            .offset((page - 1) * per_page).limit(per_page).all())

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

    batches = BarangayFoodPackBatch.query.filter(
        BarangayFoodPackBatch.barangay_id == barangay.barangay_id,
        BarangayFoodPackBatch.quantity_remaining > 0,
    ).order_by(BarangayFoodPackBatch.expiration_date).all()
    batch_rows = [{"batch": b, "shelf_status": _shelf_status(b.expiration_date)} for b in batches]

    return render_template(
        "barangay/inventory.html",
        barangay=barangay, on_hand=on_hand, logs=logs, families=families,
        received=received, given_out=given_out, delivery_recs=delivery_recs,
        type_filter=type_filter, date_from=iso(date_from), date_to=iso(date_to),
        batch_rows=batch_rows, near_expiry_days=NEAR_EXPIRY_DAYS, shelf_status_fn=_shelf_status,
        page=page, total_pages=total_pages, per_page=per_page, total_logs=total_logs,
    )


# Applies the movement type and date filters to the stock history.
def _inventory_movements_query(barangay):
    type_filter = request.args.get("type", "all")
    date_from, date_to = date_range(request.args)
    legacy = arg_date(request.args, "date")
    if legacy and not (date_from or date_to):
        date_from = date_to = legacy
    logs_q = BarangayStockLog.query.filter_by(barangay_id=barangay.barangay_id)
    if type_filter != "all":
        logs_q = logs_q.filter(BarangayStockLog.source_type == type_filter)
    if date_from:
        logs_q = logs_q.filter(db.func.date(BarangayStockLog.created_at) >= date_from)
    if date_to:
        logs_q = logs_q.filter(db.func.date(BarangayStockLog.created_at) <= date_to)
    return logs_q, type_filter, date_from, date_to


INVENTORY_MOVEMENT_TYPE_LABELS = {
    "delivery": "Received", "distribution": "Distributed",
    "damaged_return": "Damaged - Returned to Warehouse", "expired": "Expired Food Packs",
}


# Download: /barangay/inventory/movements/export - Downloads the stock movement history as an Excel file.
@barangay_bp.route("/inventory/movements/export")
@login_required
@role_required("barangay_user")
def inventory_movements_export():
    from app.routes.report_data import build_barangay_movement_export
    from app.routes.report_files import generate_file

    fmt = "excel"
    barangay = _own_barangay_or_404()
    logs_q, type_filter, date_from, date_to = _inventory_movements_query(barangay)
    logs = logs_q.order_by(BarangayStockLog.created_at.desc(), BarangayStockLog.log_id.desc()).all()
    type_label = "All Types" if type_filter == "all" else INVENTORY_MOVEMENT_TYPE_LABELS.get(type_filter, type_filter.title())
    report = build_barangay_movement_export(barangay, logs, type_label, date_from, date_to, current_user)
    content, _pages = generate_file(report, fmt)

    filename = f"stock_movements_{ph_now().strftime('%Y%m%d')}.{REPORTS_EXTENSIONS[fmt]}"
    return Response(
        content, mimetype=REPORTS_MIME_TYPES[fmt],
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


# Action: /barangay/inventory/expired-batch/<int:batch_id>/resolve - Handles an expired food pack batch:
# either dispose of the packs, or repack them with fresh items and put them back in stock.
@barangay_bp.route("/inventory/expired-batch/<int:batch_id>/resolve", methods=["POST"])
@login_required
@role_required("barangay_user")
def inventory_resolve_expired_batch(batch_id):
    barangay = _own_barangay_or_404()
    batch = BarangayFoodPackBatch.query.get_or_404(batch_id)
    if batch.barangay_id != barangay.barangay_id or batch.status != "expired":
        abort(403)

    quantity = request.form.get("quantity", type=int)
    resolution = request.form.get("resolution", "")
    if not quantity or quantity <= 0:
        flash("Enter how many expired packs this covers.", "error")
        return redirect(url_for("barangay.inventory"))
    if quantity > batch.quantity_remaining:
        flash(f"Only {batch.quantity_remaining:,} expired packs are on record for that batch.", "error")
        return redirect(url_for("barangay.inventory"))
    if resolution not in ("disposed", "fixed"):
        flash("Select Disposed or Fixed.", "error")
        return redirect(url_for("barangay.inventory"))

    expired_item = BarangayInventory.query.filter_by(
        barangay_id=barangay.barangay_id, item_type="food_pack_expired"
    ).first()
    if expired_item is None or expired_item.quantity_available < quantity:
        flash("Expired stock record is out of sync - reload and try again.", "error")
        return redirect(url_for("barangay.inventory"))

    plan, replaced_components = _refreshed_batch_items(batch, ph_today())

    batch.quantity_remaining -= quantity
    expired_item.quantity_available -= quantity
    expired_item.updated_by = current_user.user_id

    if resolution == "disposed":
        db.session.add(BarangayStockLog(
            barangay_id=barangay.barangay_id, item_type="food_pack_expired", item_name=expired_item.item_name,
            delta=-quantity, source_type="expired",
            reason=f"{quantity:,} expired packs disposed / written off",
            updated_by=current_user.user_id,
        ))
        flash(f"{quantity:,} expired packs marked disposed.", "success")
    else:
        replaced_names = ", ".join(c.name for c in replaced_components)
        db.session.add(BarangayStockLog(
            barangay_id=barangay.barangay_id, item_type="food_pack_expired", item_name=expired_item.item_name,
            delta=-quantity, source_type="expired",
            reason=f"{quantity:,} expired packs resolved - {replaced_names} replaced with fresh stock",
            updated_by=current_user.user_id,
        ))
        fp = BarangayInventory.query.filter_by(barangay_id=barangay.barangay_id, item_type="food_pack").first()
        if fp is None:
            fp = BarangayInventory(
                barangay_id=barangay.barangay_id, item_type="food_pack",
                item_name="Food Packs", unit="packs", quantity_available=0,
            )
            db.session.add(fp)
        fp.quantity_available = (fp.quantity_available or 0) + quantity
        fp.updated_by = current_user.user_id
        db.session.add(BarangayStockLog(
            barangay_id=barangay.barangay_id, item_type="food_pack", item_name="Food Packs",
            delta=quantity, source_type="expired",
            reason=f"{quantity:,} packs returned to usable stock after replacing {replaced_names}",
            updated_by=current_user.user_id,
        ))

        new_batch = BarangayFoodPackBatch(
            barangay_id=barangay.barangay_id, quantity_remaining=quantity,
            received_date=ph_today(),
            expiration_date=_plan_expiration(plan),
            status="active", updated_by=current_user.user_id,
        )
        db.session.add(new_batch)
        db.session.flush()
        for component_id, custom_name, exp, qty_label in plan:
            db.session.add(BarangayFoodPackBatchItem(
                batch_id=new_batch.batch_id, component_id=component_id,
                custom_name=custom_name, quantity_label=qty_label, expiration_date=exp,
            ))

        flash(f"{quantity:,} expired packs marked fixed - {replaced_names} replaced, "
              f"returned to Food Packs stock.", "success")

    db.session.commit()
    return redirect(url_for("barangay.inventory"))


DISTRIBUTION_PROOF_EXTENSIONS = {"jpg", "jpeg", "png"}


# Checks the proof photos for a distribution (JPG or PNG only).
def _distribution_proof_files():
    files = [f for f in request.files.getlist("proof_photos") if f and f.filename]
    for f in files:
        ext = f.filename.rsplit(".", 1)[-1].lower() if "." in f.filename else ""
        if ext not in DISTRIBUTION_PROOF_EXTENSIONS:
            return [], "Proof photos must be JPG or PNG images."
    return files, None


# Saves the proof photos for a distribution.
def _save_distribution_proof(log, files):
    if not files:
        return
    upload_dir = os.path.join(current_app.root_path, "static", "uploads", "barangay_distributions", str(log.log_id))
    os.makedirs(upload_dir, exist_ok=True)
    saved = []
    for f in files:
        safe_name = secure_filename(f.filename)
        if not safe_name or safe_name in saved:
            continue
        f.save(os.path.join(upload_dir, safe_name))
        saved.append(safe_name)
    log.proof_photos = ",".join(saved) or None


# Records food packs given out to families: removes them from stock (oldest batches first)
# and saves the record with any proof photos.
def _record_barangay_distribution(barangay_id, amount, reason, family_id=None, proof_files=None):
    inv = BarangayInventory.query.filter_by(
        barangay_id=barangay_id, item_type="food_pack"
    ).first()
    on_hand = inv.quantity_available if inv else 0
    if inv is None or on_hand < amount:
        return f"You only have {on_hand:,} food packs on hand."

    # Remove the given-out packs from the barangay's stock.
    inv.quantity_available = on_hand - amount
    inv.updated_by = current_user.user_id
    _take_from_batches(BarangayFoodPackBatch.query.filter_by(
        barangay_id=barangay_id, status="active").filter(BarangayFoodPackBatch.quantity_remaining > 0).all(), amount)
    log = BarangayStockLog(
        barangay_id=barangay_id, item_type="food_pack", item_name="Food Packs",
        delta=-amount, source_type="distribution", reason=reason, family_id=family_id,
        updated_by=current_user.user_id,
    )
    db.session.add(log)
    if proof_files:
        db.session.flush()
        _save_distribution_proof(log, proof_files)
    return None


# Action: /barangay/inventory/record - Form action 'Record Distribution': food packs given out, to whom, and proof photos.
@barangay_bp.route("/inventory/record", methods=["POST"])
@login_required
@role_required("barangay_user")
def inventory_record():
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

    proof_files, err = _distribution_proof_files()
    if err:
        flash(err, "error")
        return redirect(url_for("barangay.inventory"))
    if not proof_files:
        flash("Attach a photo of the hand-over to record this distribution.", "error")
        return redirect(url_for("barangay.inventory"))

    err = _record_barangay_distribution(
        barangay.barangay_id, amount, reason,
        family_id=family.family_id if family else None, proof_files=proof_files,
    )
    if err:
        flash(err, "error")
        return redirect(url_for("barangay.inventory"))

    db.session.commit()
    who = f"to {family.family_name}" if family else "to residents"
    flash(f"Recorded {amount:,} food packs distributed {who}.", "success")
    return redirect(url_for("barangay.inventory"))


# Action: /barangay/damage-report/<int:report_id>/distribute/<int:raf_id> - Marks a family listed in a report as having received its food packs
# (only after the delivery was confirmed), and removes the packs from stock.
@barangay_bp.route("/damage-report/<int:report_id>/distribute/<int:raf_id>", methods=["POST"])
@login_required
@role_required("barangay_user")
def mark_family_received(report_id, raf_id):
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

    proof_files, err = _distribution_proof_files()
    if err:
        flash(err, "error")
        return redirect(url_for("barangay.view_damage_report", report_id=report.report_id))
    if not proof_files:
        flash(f"Attach a photo of the hand-over to mark {raf.family_name} as received.", "error")
        return redirect(url_for("barangay.view_damage_report", report_id=report.report_id))

    err = _record_barangay_distribution(
        report.barangay_id, packs, f"{raf.family_name} - {report.ref}",
        family_id=raf.family_id, proof_files=proof_files,
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


# Action: /barangay/damage-report/<int:report_id>/distribute/<int:raf_id>/undo - Undoes a family's 'received' mark and puts its packs back into stock.
@barangay_bp.route("/damage-report/<int:report_id>/distribute/<int:raf_id>/undo", methods=["POST"])
@login_required
@role_required("barangay_user")
def undo_family_received(report_id, raf_id):
    report = _get_own_report_or_404(report_id)
    raf = next((rf for rf in report.affected_families_list if rf.id == raf_id), None)
    if not raf or not raf.received:
        abort(404)

    inv = BarangayInventory.query.filter_by(
        barangay_id=report.barangay_id, item_type="food_pack"
    ).first()
    if inv:
        # Put the family's packs back into stock.
        inv.quantity_available += raf.packs_given
        inv.updated_by = current_user.user_id
        _create_barangay_food_pack_batch(report.barangay_id, raf.packs_given, ph_today(), current_user.user_id)
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


REPORTS_MIME_TYPES = {
    "pdf": "application/pdf",
    "excel": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}
REPORTS_EXTENSIONS = {"pdf": "pdf", "excel": "xlsx"}


# The filters saved with a generated report (event and period).
def _reports_filters_snapshot(filters):
    return {"event_id": filters["event_id"], "days": filters["days"]}


# Rebuilds a past report file from its saved filters, so it can be downloaded again.
def _regenerate_barangay_report(log, barangay):
    from app.routes.reports import _StoredArgs
    from app.routes.report_data import resolve_barangay_filters, build_barangay_report
    from app.routes.report_files import generate_file

    stored = json.loads(log.filters_json) if log.filters_json else {}
    filters = resolve_barangay_filters(_StoredArgs(stored))
    report = build_barangay_report(log.report_type, barangay, filters, log.generated_by_user)
    return generate_file(report, log.format)


# Page: /barangay/reports - Reports page: summary numbers for the barangay and the PDF/Excel reports
# that can be generated, plus recently generated reports.
@barangay_bp.route("/reports")
@login_required
@role_required("barangay_user")
def reports():
    from app.models.report import ReportLog
    from app.routes.report_data import BARANGAY_REPORT_TYPES, resolve_barangay_filters

    barangay = _own_barangay_or_404()
    filters = resolve_barangay_filters(request.args)
    active_events = DisasterEvent.query.filter_by(is_reference=False).order_by(DisasterEvent.start_date.desc()).all()

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


# Page: /barangay/reports/<report_type> - Shows one report on screen before downloading it.
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


# Creates a report as PDF or Excel and saves it in the report history.
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
    inline = fmt == "pdf" and request.args.get("inline") == "1"

    if not inline:
        db.session.add(ReportLog(
            report_type=report_type, format=fmt, pages=pages,
            filters_json=json.dumps(_reports_filters_snapshot(filters)),
            generated_by=current_user.user_id,
        ))
        db.session.commit()

    filename = f"{report_type}_{ph_now().strftime('%Y%m%d')}.{REPORTS_EXTENSIONS[fmt]}"
    return Response(
        content, mimetype=REPORTS_MIME_TYPES[fmt],
        headers={"Content-Disposition": f"{'inline' if inline else 'attachment'}; filename={filename}"},
    )


# Download: /barangay/reports/<report_type>/pdf - Downloads a report as a PDF file.
@barangay_bp.route("/reports/<report_type>/pdf")
@login_required
@role_required("barangay_user")
def report_export_pdf(report_type):
    return _barangay_export_report(report_type, "pdf")


# Download: /barangay/reports/<report_type>/excel - Downloads a report as an Excel file.
@barangay_bp.route("/reports/<report_type>/excel")
@login_required
@role_required("barangay_user")
def report_export_excel(report_type):
    return _barangay_export_report(report_type, "excel")


# Download: /barangay/reports/download/<int:report_id> - Downloads a report from the history again (only the user's own reports).
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


# Download: /barangay/reports/download-all - Downloads the user's 10 latest reports together in one ZIP file.
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


# Page: /barangay/notifications - Barangay Notifications page: updates about the barangay's reports and deliveries,
# filterable by category.
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

    if unread_count and scope is not None:
        ActivityLog.query.filter(scope, ActivityLog.is_read.is_(False)).update(
            {"is_read": True}, synchronize_session=False
        )
        db.session.commit()

    categories = [
        {"value": "all", "label": "All"},
        {"value": "barangay_reports", "label": "Barangay Reports"},
        {"value": "distribution", "label": "Relief Monitoring"},
    ]

    return render_template(
        "barangay/notifications.html",
        items=page_items, unread_count=unread_count, total_count=total_count,
        total_filtered=total_filtered, category_filter=category_filter,
        categories=categories,
        page=page, total_pages=total_pages, per_page=per_page, barangay=barangay,
    )


# Page: /barangay/notifications/<int:log_id>/view - Marks a notification as read and opens the page it is about.
@barangay_bp.route("/notifications/<int:log_id>/view")
@login_required
@role_required("barangay_user")
def view_notification(log_id):
    log = ActivityLog.query.get_or_404(log_id)
    _assert_own_activity(log)
    log.is_read = True
    db.session.commit()
    destination = _notification_view(log)["link"]
    return redirect(destination or url_for("barangay.notifications"))


# Page: /barangay/settings/profile - Barangay user's Profile Settings page.
@barangay_bp.route("/settings/profile")
@login_required
@role_required("barangay_user")
def profile_settings():
    return render_template("barangay/profile_settings.html")


# Action: /barangay/settings/profile - Saves the user's own name, email and designation (position).
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


# Action: /barangay/settings/password - Changes the user's own password.
# The current password must be correct and the new one at least 8 characters.
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
