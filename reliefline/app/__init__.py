# Sets up the whole app: settings, database, login, sidebar badges, and all pages.

import os

from flask import Flask
from app.config import Config
from app.extensions import db, login_manager
from app.utils.icons import ICONS
from app.utils.roles import ROLE_LABELS
from app.utils.timezone import ph_time, ph_now, ph_today

# Builds and starts the whole ReliefLine web app.
# It loads the settings, connects the database, turns on login, and registers every page of the system.
def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    if not app.config["SECRET_KEY"]:
        if not app.config["DEBUG"]:
            # On the server, the app refuses to start without a SECRET_KEY (it keeps logins secure).
            raise RuntimeError("SECRET_KEY is not set - add it to the environment / .env (see app/config.py).")
        app.config["SECRET_KEY"] = "dev-secret-key"

    if app.config["BEHIND_PROXY"]:
        from werkzeug.middleware.proxy_fix import ProxyFix
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

    db.init_app(app)
    login_manager.init_app(app)
    app.jinja_env.filters["ph_time"] = ph_time
    app.jinja_env.globals["ph_now"] = ph_now
    app.jinja_env.globals["ph_today"] = ph_today
    from app.utils.stock_labels import stock_log_label
    app.jinja_env.globals["stock_log_label"] = stock_log_label
    from app.models.disaster_event import EVENT_CATEGORIES
    app.jinja_env.globals["EVENT_CATEGORIES"] = EVENT_CATEGORIES

    # Adds a version number to each CSS/JS file link (based on when the file last changed).
    # This makes browsers download the newest file after an update instead of using an old saved copy.
    def asset_version(filename):
        try:
            path = os.path.join(app.static_folder, filename)
            return int(os.path.getmtime(path))
        except OSError:
            return 0

    app.jinja_env.globals["asset_version"] = asset_version

    # Lists the food pack batches a warehouse can choose from when sending out stock.
    # Used by the batch picker that appears on every 'send stock' form.
    def pickable_food_pack_batches(office_id):
        from app.routes.pswdo import _pickable_food_pack_batches
        return _pickable_food_pack_batches(office_id) if office_id else []
    app.jinja_env.globals["pickable_food_pack_batches"] = pickable_food_pack_batches

    from app import models
    from app.models.user import User
    from app.models.barangay import Barangay
    from app.models.barangay_report import BarangayReport
    from app.models.activity_log import ActivityLog

    # Looks up the logged-in user's account on every page visit,
    # so the app always knows who is using it.
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Saves the time a logged-in user was last active (at most once a minute).
    # This powers the green 'Online' badge the System Admin sees.
    @app.before_request
    def _track_last_activity():
        from datetime import timedelta
        from flask import request
        from flask_login import current_user

        if not request.endpoint or request.endpoint == "static":
            return
        if not current_user.is_authenticated:
            return

        now = ph_now()
        if not current_user.last_activity or now - current_user.last_activity > timedelta(seconds=60):
            current_user.last_activity = now
            db.session.commit()

    # If an admin reset this user's password, the user is sent back to the login page
    # until they choose a new password of their own. Only login and logout stay reachable.
    @app.before_request
    def _enforce_forced_password_change():
        from flask import request, redirect, url_for
        from flask_login import current_user

        allowed_endpoints = {
            "auth.login", "auth.force_change_password", "auth.logout", "static",
        }
        if not current_user.is_authenticated or request.endpoint in allowed_endpoints:
            return
        # This user's password was reset by an admin: send them to the login page to set a new one.
        if current_user.must_change_password:
            return redirect(url_for("auth.login"))

    # Makes the app's icon set available on every page.
    @app.context_processor
    def inject_icons():
        return dict(ICONS=ICONS)

    # Makes the readable role names (e.g. 'PSWDO Administrator') available on every page.
    @app.context_processor
    def inject_role_labels():
        return dict(ROLE_LABELS=ROLE_LABELS)

    # Counts the user's unread notifications for the number badge on the sidebar bell.
    # Each role only counts notifications meant for them (own municipality, own barangay, or province-wide).
    @app.context_processor
    def inject_unread_notifications():
        from flask_login import current_user
        if not current_user.is_authenticated:
            return dict(unread_notification_count=0)

        if current_user.role == "cswdo_admin":
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

        from app.routes.pswdo import PSWDO_NOTIFICATION_TYPES
        count = ActivityLog.query.filter(
            ActivityLog.action_type.in_(PSWDO_NOTIFICATION_TYPES), ActivityLog.is_read.is_(False)
        ).count()
        return dict(unread_notification_count=count)

    # Counts stock requests from CSWDO/MSWDO still waiting for a PSWDO decision.
    # Shown as a number badge on PSWDO's 'Stock Requests' sidebar link.
    @app.context_processor
    def inject_pending_stock_requests():
        from flask_login import current_user
        from app.models.relief_request_batch import ReliefRequestBatch
        if not current_user.is_authenticated or current_user.role not in ("pswdo_admin", "system_admin"):
            return dict(pending_stock_requests=0)
        count = ReliefRequestBatch.query.filter(
            ReliefRequestBatch.submitted_at.isnot(None),
            ReliefRequestBatch.status == "pending",
        ).count()
        return dict(pending_stock_requests=count)

    # Counts new barangay reports waiting for CSWDO/MSWDO review in the user's municipality.
    # Shown as a number badge on the 'Barangay Reports' sidebar link; clears once the event ends.
    @app.context_processor
    def inject_pending_barangay_reports():
        from flask_login import current_user
        from app.models.disaster_event import DisasterEvent
        if not current_user.is_authenticated or current_user.role not in ("cswdo_admin", "system_admin"):
            return dict(pending_barangay_reports=0)
        office = current_user.office
        lgu = office.area_covered if office else None
        if not lgu:
            return dict(pending_barangay_reports=0)
        barangay_ids = [b.barangay_id for b in Barangay.query.filter_by(city_municipality=lgu).all()]
        if not barangay_ids:
            return dict(pending_barangay_reports=0)
        count = BarangayReport.query.outerjoin(
            DisasterEvent, BarangayReport.event_id == DisasterEvent.event_id
        ).filter(
            BarangayReport.barangay_id.in_(barangay_ids),
            BarangayReport.status == "pending",
            db.or_(BarangayReport.event_id.is_(None), DisasterEvent.status != "ended"),
        ).count()
        return dict(pending_barangay_reports=count)

    # Counts new 'forgot password' requests the System Admin hasn't opened yet.
    # Shown as a number badge on the 'Password Reset Requests' sidebar link.
    @app.context_processor
    def inject_pending_password_resets():
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
    from app.routes.receipts import receipts_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(pswdo_bp, url_prefix="/pswdo")
    app.register_blueprint(cswdo_bp, url_prefix="/cswdo")
    app.register_blueprint(barangay_bp, url_prefix="/barangay")
    app.register_blueprint(prediction_bp, url_prefix="/prediction")
    app.register_blueprint(reports_bp, url_prefix="/pswdo/reports")
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(receipts_bp, url_prefix="/receipts")

    return app
