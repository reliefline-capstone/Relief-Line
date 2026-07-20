from flask import Flask
from app.config import Config
from app.extensions import db, login_manager
from app.utils.icons import ICONS
from app.utils.roles import ROLE_LABELS

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)

    from app.models.user import User
    from app.models.office import Office
    from app.models.barangay import Barangay
    from app.models.warehouse import WarehouseInventory, WarehouseStockLog
    from app.models.allocation import AllocationRecord, PrepositionRecord
    from app.models.validation import DistributionRecord
    from app.models.prediction import PredictionLog, ModelMetrics
    from app.models.disaster_event import DisasterEvent
    from app.models.barangay_status import BarangayDisasterStatus
    from app.models.activity_log import ActivityLog, DailyOpsStat
    from app.models.logistics import Vehicle, Driver, WarehouseTransfer
    from app.models.report import ReportLog

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

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
        return dict(unread_notification_count=ActivityLog.query.filter(ActivityLog.is_read.is_(False)).count())

    from app.routes.auth import auth_bp
    from app.routes.pswdo import pswdo_bp
    from app.routes.cswdo import cswdo_bp
    from app.routes.barangay import barangay_bp
    from app.routes.prediction import prediction_bp
    from app.routes.reports import reports_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(pswdo_bp, url_prefix="/pswdo")
    app.register_blueprint(cswdo_bp, url_prefix="/cswdo")
    app.register_blueprint(barangay_bp, url_prefix="/barangay")
    app.register_blueprint(prediction_bp, url_prefix="/prediction")
    app.register_blueprint(reports_bp, url_prefix="/pswdo/reports")

    return app