import os

from flask import Flask
from app.config import Config
from app.extensions import db, login_manager
from app.utils.icons import ICONS
from app.utils.roles import ROLE_LABELS
from app.utils.timezone import ph_time

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)
    app.jinja_env.filters["ph_time"] = ph_time

    def asset_version(filename):
        # File mtime as a cache-busting query string — browsers otherwise hold
        # onto a stale copy of a static JS/CSS file across edits (bit us with
        # gis_map.js: the fix was live on the server but the browser kept
        # serving the old cached script), so this forces a re-fetch whenever
        # the file on disk actually changes.
        try:
            path = os.path.join(app.static_folder, filename)
            return int(os.path.getmtime(path))
        except OSError:
            return 0

    app.jinja_env.globals["asset_version"] = asset_version

    from app.models.user import User
    from app.models.office import Office
    from app.models.barangay import Barangay
    from app.models.warehouse import WarehouseInventory, WarehouseStockLog
    from app.models.allocation import AllocationRecord, PrepositionRecord
    from app.models.validation import DistributionRecord
    from app.models.prediction import PredictionLog, ModelMetrics
    from app.models.disaster_event import DisasterEvent
    from app.models.barangay_status import BarangayDisasterStatus
    from app.models.barangay_report import BarangayReport
    from app.models.relief_request_batch import ReliefRequestBatch
    from app.models.activity_log import ActivityLog, DailyOpsStat
    from app.models.logistics import WarehouseTransfer
    from app.models.report import ReportLog
    from app.models.system_setting import SystemSetting
    from app.models.password_reset_request import PasswordResetRequest

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    @app.before_request
    def _track_last_activity():
        # Heartbeat for app.utils.presence.is_online() — throttled to once a
        # minute per user so normal browsing doesn't turn into a write on
        # every single request. Skips static assets (no endpoint / a
        # 'static' endpoint) since those aren't a meaningful "user is here".
        from datetime import datetime, timedelta
        from flask import request
        from flask_login import current_user

        if not request.endpoint or request.endpoint == "static":
            return
        if not current_user.is_authenticated:
            return

        now = datetime.utcnow()
        if not current_user.last_activity or now - current_user.last_activity > timedelta(seconds=60):
            current_user.last_activity = now
            db.session.commit()

    @app.before_request
    def _enforce_forced_password_change():
        # Set on User.must_change_password when a System Administrator
        # grants a PasswordResetRequest (see app.routes.admin) — the account
        # now holds the shared default password, so every page but the
        # change-password screen itself (and logout) redirects here until
        # the user replaces it with one of their own.
        from flask import request, redirect, url_for
        from flask_login import current_user

        allowed_endpoints = {"auth.force_change_password", "auth.logout", "static"}
        if not current_user.is_authenticated or request.endpoint in allowed_endpoints:
            return
        if current_user.must_change_password:
            return redirect(url_for("auth.force_change_password"))

    @app.context_processor
    def inject_icons():
        return dict(ICONS=ICONS)

    @app.context_processor
    def inject_role_labels():
        return dict(ROLE_LABELS=ROLE_LABELS)

    @app.context_processor
    def inject_unread_notifications():
        from flask_login import current_user
        if not current_user.is_authenticated:
            return dict(unread_notification_count=0)

        if current_user.role == "cswdo_admin":
            # Scoped to this office's own LGU — must match the count shown on
            # the CSWDO Notifications page and dashboard widget (see
            # app.routes.cswdo._own_activity_filters), otherwise the sidebar
            # badge would disagree with the page it links to.
            office = current_user.office
            lgu = office.area_covered if office else None
            filters = []
            if office:
                filters.append(ActivityLog.office_id == office.office_id)
            if lgu:
                barangay_ids = [b.barangay_id for b in Barangay.query.filter_by(city_municipality=lgu).all()]
                if barangay_ids:
                    filters.append(ActivityLog.barangay_id.in_(barangay_ids))
            if not filters:
                return dict(unread_notification_count=0)
            from app.routes.pswdo import NOTIFICATION_META
            known_types = list(NOTIFICATION_META.keys())
            count = ActivityLog.query.filter(
                db.or_(*filters), ActivityLog.action_type.in_(known_types), ActivityLog.is_read.is_(False)
            ).count()
            return dict(unread_notification_count=count)

        if current_user.role == "barangay_user":
            # Scoped to this barangay_id alone — must match the count shown on
            # the Barangay Notifications page and dashboard widget (see
            # app.routes.barangay._own_activity_filter).
            if not current_user.barangay_id:
                return dict(unread_notification_count=0)
            from app.routes.pswdo import NOTIFICATION_META
            known_types = list(NOTIFICATION_META.keys())
            count = ActivityLog.query.filter(
                ActivityLog.barangay_id == current_user.barangay_id,
                ActivityLog.action_type.in_(known_types),
                ActivityLog.is_read.is_(False),
            ).count()
            return dict(unread_notification_count=count)

        # pswdo_admin / system_admin see the province-wide count, matching the
        # PSWDO Notifications page (app.routes.pswdo.notifications) — same
        # PSWDO_NOTIFICATION_TYPES allowlist, so System Administration rows
        # (logins, user/office/barangay management) never count here either
        # (even though they're already is_read=True by design), and neither
        # do damage_report_* rows — reviewing those is entirely CSWDO/MSWDO's
        # job, and PSWDO has no page to click through to for them.
        from app.routes.pswdo import PSWDO_NOTIFICATION_TYPES
        count = ActivityLog.query.filter(
            ActivityLog.action_type.in_(PSWDO_NOTIFICATION_TYPES), ActivityLog.is_read.is_(False)
        ).count()
        return dict(unread_notification_count=count)

    @app.context_processor
    def inject_pending_password_resets():
        # Powers the badge on admin/_sidebar.html's "Password Reset
        # Requests" link, which is included on every admin/*.html page —
        # a context processor means each admin route doesn't need to
        # compute and pass this count itself. Scoped to is_seen=False (not
        # just status="pending") so opening the Password Reset Requests page
        # — which marks pending rows seen, see app.routes.admin — clears the
        # badge even though those requests are still awaiting a decision.
        from flask_login import current_user
        from app.models.password_reset_request import PasswordResetRequest
        if not current_user.is_authenticated or current_user.role != "system_admin":
            return dict(pending_password_resets=0)
        count = PasswordResetRequest.query.filter_by(status="pending", is_seen=False).count()
        return dict(pending_password_resets=count)

    from app.routes.auth import auth_bp
    from app.routes.pswdo import pswdo_bp
    from app.routes.cswdo import cswdo_bp
    from app.routes.barangay import barangay_bp
    from app.routes.prediction import prediction_bp
    from app.routes.reports import reports_bp
    from app.routes.admin import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(pswdo_bp, url_prefix="/pswdo")
    app.register_blueprint(cswdo_bp, url_prefix="/cswdo")
    app.register_blueprint(barangay_bp, url_prefix="/barangay")
    app.register_blueprint(prediction_bp, url_prefix="/prediction")
    app.register_blueprint(reports_bp, url_prefix="/pswdo/reports")
    app.register_blueprint(admin_bp, url_prefix="/admin")

    return app