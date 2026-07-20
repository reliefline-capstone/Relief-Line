import io
import json
import zipfile
from datetime import datetime

from flask import Blueprint, render_template, request, Response, abort, url_for, redirect, flash
from flask_login import login_required, current_user

from app.extensions import db
from app.utils.decorators import role_required
from app.models.disaster_event import DisasterEvent
from app.models.report import ReportLog

from app.routes.pswdo import TARGET_LGUS
from app.routes.report_data import REPORT_TYPES, resolve_filters, build_report
from app.routes.report_files import generate_file

reports_bp = Blueprint("reports", __name__)

MIME_TYPES = {
    "pdf": "application/pdf",
    "excel": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}
EXTENSIONS = {"pdf": "pdf", "excel": "xlsx"}


class _StoredArgs(dict):
    """Makes a plain {event_id, municipality, days} dict quack like
    request.args for resolve_filters(), so a logged report's stored filters
    can be replayed exactly on re-download without touching the live query
    string."""

    def get(self, key, default=None, type=None):
        value = dict.get(self, key, default)
        if type is not None and value is not None:
            try:
                return type(value)
            except (TypeError, ValueError):
                return default
        return value


def _filters_snapshot(filters):
    """The resolved (not raw query-string) filter values, so a later
    re-download reproduces this exact event/municipality/range even if the
    'active' disaster event has since changed."""
    return {
        "event_id": filters["event_id"],
        "municipality": filters["municipality"],
        "days": filters["days"],
    }


def _regenerate_from_log(log):
    stored = json.loads(log.filters_json) if log.filters_json else {}
    filters = resolve_filters(_StoredArgs(stored))
    report = build_report(log.report_type, filters, log.generated_by_user)
    return generate_file(report, log.format)


@reports_bp.route("/<report_type>")
@login_required
@role_required("pswdo_admin", "system_admin")
def view(report_type):
    if report_type not in REPORT_TYPES:
        abort(404)
    filters = resolve_filters(request.args)
    report = build_report(report_type, filters, current_user)
    active_events = DisasterEvent.query.filter_by(status="active").order_by(
        DisasterEvent.start_date.desc()
    ).all()
    return render_template(
        "pswdo/report_view.html",
        report=report,
        filters=filters,
        active_events=active_events,
        target_lgus=TARGET_LGUS,
    )


def _export(report_type, fmt):
    if report_type not in REPORT_TYPES:
        abort(404)
    filters = resolve_filters(request.args)
    report = build_report(report_type, filters, current_user)
    content, pages = generate_file(report, fmt)

    db.session.add(ReportLog(
        report_type=report_type, format=fmt, pages=pages,
        filters_json=json.dumps(_filters_snapshot(filters)),
        generated_by=current_user.user_id,
    ))
    db.session.commit()

    filename = f"{report_type}_{datetime.now().strftime('%Y%m%d')}.{EXTENSIONS[fmt]}"
    return Response(
        content, mimetype=MIME_TYPES[fmt],
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@reports_bp.route("/<report_type>/pdf")
@login_required
@role_required("pswdo_admin", "system_admin")
def export_pdf(report_type):
    return _export(report_type, "pdf")


@reports_bp.route("/<report_type>/excel")
@login_required
@role_required("pswdo_admin", "system_admin")
def export_excel(report_type):
    return _export(report_type, "excel")


@reports_bp.route("/download/<int:report_id>")
@login_required
@role_required("pswdo_admin", "system_admin")
def download(report_id):
    """Re-download from Recent Reports — regenerates the same file from the
    log's stored filters rather than keeping binary blobs on disk/DB."""
    log = ReportLog.query.get_or_404(report_id)
    if log.report_type not in REPORT_TYPES:
        abort(404)

    content, _ = _regenerate_from_log(log)
    filename = f"{log.report_type}_{log.generated_at.strftime('%Y%m%d')}.{EXTENSIONS[log.format]}"
    return Response(
        content, mimetype=MIME_TYPES[log.format],
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@reports_bp.route("/download-all")
@login_required
@role_required("pswdo_admin", "system_admin")
def download_all():
    logs = ReportLog.query.order_by(ReportLog.generated_at.desc()).limit(10).all()
    if not logs:
        flash("No reports have been generated yet — export one first.", "error")
        return redirect(url_for("pswdo.warehouse_reports"))

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for i, log in enumerate(logs, start=1):
            if log.report_type not in REPORT_TYPES:
                continue
            content, _ = _regenerate_from_log(log)
            fname = f"{i:02d}_{log.report_type}_{log.generated_at.strftime('%Y%m%d')}.{EXTENSIONS[log.format]}"
            zf.writestr(fname, content)
    buffer.seek(0)

    return Response(
        buffer.getvalue(), mimetype="application/zip",
        headers={
            "Content-Disposition": f"attachment; filename=reliefline_reports_{datetime.now().strftime('%Y%m%d')}.zip"
        },
    )
