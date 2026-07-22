import csv
import io
import secrets
from datetime import datetime

from flask import Blueprint, render_template, request, redirect, url_for, flash, Response
from flask_login import login_required, current_user

from app.extensions import db
from app.utils.decorators import role_required
from app.utils.activity import log_admin_activity, module_for_action, module_badge_class, AUDIT_ACTION_TYPES
from app.utils.settings import SETTINGS_SCHEMA, get_setting, set_setting
from app.utils.roles import ROLE_LABELS
from app.utils.mail import send_email
from app.models.user import User
from app.models.office import Office
from app.models.barangay import Barangay
from app.models.activity_log import ActivityLog
from app.routes.pswdo import TARGET_LGUS
from app.ml.train import historical_allocation_for

admin_bp = Blueprint("admin", __name__)

ROLE_CHOICES = ["system_admin", "pswdo_admin", "cswdo_admin", "barangay_user"]


# ---------------------------------------------------------------------------
# Small display helpers — everything here derives from real stored fields
# rather than adding columns for things that are really just presentation.
# ---------------------------------------------------------------------------

def _generate_temp_password():
    return secrets.token_urlsafe(9)


def _deliver_credentials(user, temp_password, subject, intro):
    """Emails a new/reset password when SMTP is configured; otherwise falls
    back to flashing it directly, mirroring auth.forgot_password's fallback
    so the admin flow works before any mail server is wired up."""
    body = f"{intro}\n\nEmail: {user.email}\nTemporary password: {temp_password}\n\nPlease log in and change it right away."
    sent = False
    try:
        sent = send_email(user.email, subject, body)
    except Exception:
        sent = False

    if sent:
        flash(f"{user.name}'s credentials were emailed to {user.email}.", "success")
    else:
        flash(
            f"Email delivery isn't configured, so here's the temporary password directly — "
            f"share it with {user.name} securely: {temp_password}",
            "success",
        )


def _office_type_label(office):
    if office.office_type == "pswdo":
        return "Provincial" if office.area_covered == "Province of Pangasinan" else "Warehouse"
    return "City" if office.area_covered == "Urdaneta City" else "Municipal"


def _office_code(office):
    if office.office_type == "pswdo":
        if office.area_covered == "Province of Pangasinan":
            return "PSWDO"
        initials = "".join(w[0] for w in office.office_name.split() if w[0].isalpha()).upper()
        return f"WH-{initials[:4]}"
    if office.area_covered == "Urdaneta City":
        return "CSWDO"
    words = office.area_covered.split()
    abbrev = "".join(w[0] for w in words).upper() if len(words) > 1 else office.area_covered[:3].upper()
    return f"MSWDO-{abbrev}"


def _risk_level(disaster_risk_index):
    value = float(disaster_risk_index or 0)
    if value >= 7.0:
        return "High"
    if value >= 5.0:
        return "Moderate"
    return "Low"


def _today_start():
    now = datetime.utcnow()
    return datetime(now.year, now.month, now.day)


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

@admin_bp.route("/dashboard")
@login_required
@role_required("system_admin")
def dashboard():
    total_users = User.query.count()
    active_sessions = User.query.filter(User.last_login >= _today_start()).count()
    inactive_accounts = User.query.filter_by(is_active=False).count()
    month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    audit_entries_this_month = ActivityLog.query.filter(ActivityLog.created_at >= month_start).count()

    recent_users = User.query.order_by(
        db.func.coalesce(User.last_login, User.created_at).desc()
    ).limit(5).all()

    return render_template(
        "admin/dashboard.html", now=datetime.now(),
        total_users=total_users, active_sessions=active_sessions,
        inactive_accounts=inactive_accounts, audit_entries_this_month=audit_entries_this_month,
        recent_users=recent_users,
    )


# ---------------------------------------------------------------------------
# User Management
# ---------------------------------------------------------------------------

@admin_bp.route("/users")
@login_required
@role_required("system_admin")
def users():
    search_query = request.args.get("q", "").strip()
    users_q = User.query
    if search_query:
        like = f"%{search_query}%"
        users_q = users_q.filter(db.or_(User.name.ilike(like), User.email.ilike(like)))

    user_list = users_q.order_by(User.name).all()
    offices = Office.query.order_by(Office.office_name).all()
    barangays = Barangay.query.order_by(Barangay.city_municipality, Barangay.barangay_name).all()

    return render_template(
        "admin/users.html", users=user_list, offices=offices, barangays=barangays,
        search_query=search_query, role_choices=ROLE_CHOICES,
    )


def _apply_user_office_barangay(user, role):
    """Role dictates which assignment field is meaningful — clears the other
    so a role change doesn't leave a stale office/barangay pointer behind."""
    if role in ("pswdo_admin", "cswdo_admin"):
        office_id = request.form.get("office_id", type=int)
        user.office_id = office_id
        user.barangay_id = None
    elif role == "barangay_user":
        barangay_id = request.form.get("barangay_id", type=int)
        user.barangay_id = barangay_id
        user.office_id = None
    else:
        user.office_id = None
        user.barangay_id = None


@admin_bp.route("/users/add", methods=["POST"])
@login_required
@role_required("system_admin")
def add_user():
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip().lower()
    role = request.form.get("role", "")

    if not name or not email or role not in ROLE_CHOICES:
        flash("Enter a valid name, email, and role.", "error")
        return redirect(url_for("admin.users"))

    if User.query.filter_by(email=email).first():
        flash(f"{email} is already registered to another account.", "error")
        return redirect(url_for("admin.users"))

    temp_password = _generate_temp_password()
    user = User(name=name, email=email, role=role, is_active=True)
    user.set_password(temp_password)
    _apply_user_office_barangay(user, role)
    db.session.add(user)
    db.session.flush()

    log_admin_activity(
        current_user.user_id, "user_created",
        f"{current_user.name} created {ROLE_LABELS.get(role, role)} account for {name}",
        office_id=user.office_id, barangay_id=user.barangay_id,
    )
    db.session.commit()

    _deliver_credentials(
        user, temp_password, "ReliefLine — Your account was created",
        f"Hi {name}, a ReliefLine account was created for you as a {ROLE_LABELS.get(role, role)}.",
    )
    return redirect(url_for("admin.users"))


@admin_bp.route("/users/<int:user_id>/edit", methods=["POST"])
@login_required
@role_required("system_admin")
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip().lower()
    role = request.form.get("role", "")

    if not name or not email or role not in ROLE_CHOICES:
        flash("Enter a valid name, email, and role.", "error")
        return redirect(url_for("admin.users"))

    existing = User.query.filter_by(email=email).first()
    if existing and existing.user_id != user.user_id:
        flash(f"{email} is already registered to another account.", "error")
        return redirect(url_for("admin.users"))

    user.name = name
    user.email = email
    user.role = role
    _apply_user_office_barangay(user, role)

    log_admin_activity(
        current_user.user_id, "user_updated", f"{current_user.name} updated account for {name}",
        office_id=user.office_id, barangay_id=user.barangay_id,
    )
    db.session.commit()
    flash(f"{name}'s account was updated.", "success")
    return redirect(url_for("admin.users"))


@admin_bp.route("/users/<int:user_id>/reset-password", methods=["POST"])
@login_required
@role_required("system_admin")
def reset_user_password(user_id):
    user = User.query.get_or_404(user_id)
    temp_password = _generate_temp_password()
    user.set_password(temp_password)

    log_admin_activity(current_user.user_id, "user_password_reset", f"{current_user.name} reset the password for {user.name}")
    db.session.commit()

    _deliver_credentials(
        user, temp_password, "ReliefLine — Your password was reset",
        f"Hi {user.name}, your ReliefLine password was reset by a System Administrator.",
    )
    return redirect(url_for("admin.users"))


@admin_bp.route("/users/<int:user_id>/toggle-active", methods=["POST"])
@login_required
@role_required("system_admin")
def toggle_user_active(user_id):
    user = User.query.get_or_404(user_id)

    if user.user_id == current_user.user_id:
        flash("You can't deactivate your own account.", "error")
        return redirect(url_for("admin.users"))

    if user.is_active and user.role == "system_admin":
        other_active_admins = User.query.filter(
            User.role == "system_admin", User.user_id != user.user_id, User.is_active.is_(True)
        ).count()
        if other_active_admins == 0:
            flash("At least one active System Administrator account is required.", "error")
            return redirect(url_for("admin.users"))

    user.is_active = not user.is_active
    action = "user_activated" if user.is_active else "user_deactivated"
    verb = "Activated" if user.is_active else "Deactivated"
    log_admin_activity(current_user.user_id, action, f"{current_user.name} {verb.lower()} the account for {user.name}")
    db.session.commit()
    flash(f"{verb} {user.name}'s account.", "success")
    return redirect(url_for("admin.users"))


# ---------------------------------------------------------------------------
# Roles & Permissions — static, read-only. Mirrors the @role_required(...)
# checks actually enforced in app/routes/{pswdo,cswdo,barangay,prediction,
# reports,admin}.py, so this page never drifts from what the code enforces.
# ---------------------------------------------------------------------------

PERMISSION_MATRIX = [
    {"label": "Dashboard", "pswdo": True, "cswdo": True, "barangay": True, "admin": True},
    {"label": "Demand Forecast / Prediction", "pswdo": True, "cswdo": False, "barangay": False, "admin": True},
    {"label": "Geospatial Map", "pswdo": True, "cswdo": False, "barangay": False, "admin": True},
    {"label": "Warehouse Inventory (View)", "pswdo": True, "cswdo": False, "barangay": False, "admin": True},
    {"label": "Warehouse Inventory (Edit)", "pswdo": True, "cswdo": False, "barangay": False, "admin": True},
    {"label": "Municipal Inventory (View)", "pswdo": False, "cswdo": True, "barangay": False, "admin": True},
    {"label": "Pre-positioning / Stock Transfer", "pswdo": True, "cswdo": False, "barangay": False, "admin": True},
    {"label": "Damage Assessment", "pswdo": False, "cswdo": True, "barangay": False, "admin": True},
    {"label": "Relief Requests (Submit)", "pswdo": False, "cswdo": True, "barangay": False, "admin": True},
    {"label": "Relief Requests (Review / Decide)", "pswdo": True, "cswdo": False, "barangay": False, "admin": True},
    {"label": "Distribution Tracking", "pswdo": True, "cswdo": False, "barangay": False, "admin": True},
    {"label": "Validation Records", "pswdo": False, "cswdo": False, "barangay": True, "admin": True},
    {"label": "Reports", "pswdo": True, "cswdo": True, "barangay": False, "admin": True},
    {"label": "Notifications", "pswdo": True, "cswdo": True, "barangay": False, "admin": True},
    {"label": "User Management", "pswdo": False, "cswdo": False, "barangay": False, "admin": True},
    {"label": "Office Management", "pswdo": False, "cswdo": False, "barangay": False, "admin": True},
    {"label": "Barangay Management", "pswdo": False, "cswdo": False, "barangay": False, "admin": True},
    {"label": "System Activity / Audit Logs", "pswdo": False, "cswdo": False, "barangay": False, "admin": True},
    {"label": "System Settings", "pswdo": False, "cswdo": False, "barangay": False, "admin": True},
]


@admin_bp.route("/roles-permissions")
@login_required
@role_required("system_admin")
def roles_permissions():
    return render_template("admin/roles_permissions.html", matrix=PERMISSION_MATRIX)


# ---------------------------------------------------------------------------
# Office Management
# ---------------------------------------------------------------------------

@admin_bp.route("/offices")
@login_required
@role_required("system_admin")
def offices():
    office_list = Office.query.order_by(Office.office_type, Office.office_name).all()
    user_counts = dict(
        db.session.query(User.office_id, db.func.count(User.user_id))
        .filter(User.office_id.isnot(None)).group_by(User.office_id).all()
    )
    rows = [{
        "office": o, "code": _office_code(o), "type_label": _office_type_label(o),
        "user_count": user_counts.get(o.office_id, 0),
    } for o in office_list]

    return render_template("admin/offices.html", rows=rows)


def _apply_office_form(office):
    office.office_name = request.form.get("office_name", "").strip()
    office.office_type = request.form.get("office_type", "cswdo")
    office.area_covered = request.form.get("area_covered", "").strip()
    capacity = request.form.get("capacity_food_pack", type=int)
    office.capacity_food_pack = capacity if capacity and capacity > 0 else office.capacity_food_pack or 20000
    office.full_address = request.form.get("full_address", "").strip() or None
    office.manager_name = request.form.get("manager_name", "").strip() or None
    office.contact_number = request.form.get("contact_number", "").strip() or None
    office.email = request.form.get("email", "").strip() or None


@admin_bp.route("/offices/add", methods=["POST"])
@login_required
@role_required("system_admin")
def add_office():
    office = Office(is_active=True)
    _apply_office_form(office)

    if not office.office_name or not office.area_covered:
        flash("Enter an office name and area covered.", "error")
        return redirect(url_for("admin.offices"))

    db.session.add(office)
    db.session.flush()
    log_admin_activity(current_user.user_id, "office_created", f"{current_user.name} added office {office.office_name}", office_id=office.office_id)
    db.session.commit()
    flash(f"{office.office_name} added.", "success")
    return redirect(url_for("admin.offices"))


@admin_bp.route("/offices/<int:office_id>/edit", methods=["POST"])
@login_required
@role_required("system_admin")
def edit_office(office_id):
    office = Office.query.get_or_404(office_id)
    _apply_office_form(office)

    if not office.office_name or not office.area_covered:
        flash("Enter an office name and area covered.", "error")
        return redirect(url_for("admin.offices"))

    log_admin_activity(current_user.user_id, "office_updated", f"{current_user.name} updated office {office.office_name}", office_id=office.office_id)
    db.session.commit()
    flash(f"{office.office_name} updated.", "success")
    return redirect(url_for("admin.offices"))


@admin_bp.route("/offices/<int:office_id>/toggle-active", methods=["POST"])
@login_required
@role_required("system_admin")
def toggle_office_active(office_id):
    office = Office.query.get_or_404(office_id)
    office.is_active = not office.is_active
    action = "office_activated" if office.is_active else "office_deactivated"
    verb = "Activated" if office.is_active else "Deactivated"
    log_admin_activity(current_user.user_id, action, f"{current_user.name} {verb.lower()} office {office.office_name}", office_id=office.office_id)
    db.session.commit()
    flash(f"{verb} {office.office_name}.", "success")
    return redirect(url_for("admin.offices"))


# ---------------------------------------------------------------------------
# Barangay Management
# ---------------------------------------------------------------------------

@admin_bp.route("/barangays")
@login_required
@role_required("system_admin")
def barangays():
    search_query = request.args.get("q", "").strip()
    barangays_q = Barangay.query.filter(Barangay.city_municipality.in_(TARGET_LGUS))
    if search_query:
        barangays_q = barangays_q.filter(Barangay.barangay_name.ilike(f"%{search_query}%"))
    barangay_list = barangays_q.order_by(Barangay.city_municipality, Barangay.barangay_name).all()

    rows = [{
        "barangay": b, "risk_level": _risk_level(b.disaster_risk_index),
        "historical_allocation": historical_allocation_for(b.barangay_id),
    } for b in barangay_list]

    total_barangays = len(barangay_list)
    high_risk_count = sum(1 for r in rows if r["risk_level"] == "High")
    avg_poverty = (
        sum(float(b.poverty_incidence or 0) for b in barangay_list) / total_barangays
        if total_barangays else 0
    )

    return render_template(
        "admin/barangays.html", rows=rows, search_query=search_query,
        total_barangays=total_barangays, high_risk_count=high_risk_count,
        avg_poverty=avg_poverty, target_lgus=TARGET_LGUS,
    )


def _apply_barangay_form(barangay):
    barangay.barangay_name = request.form.get("barangay_name", "").strip()
    barangay.city_municipality = request.form.get("city_municipality", "")
    barangay.population = request.form.get("population", type=int) or 0
    barangay.num_households = request.form.get("num_households", type=int) or 0
    barangay.poverty_incidence = request.form.get("poverty_incidence", type=float) or 0
    barangay.disaster_risk_index = request.form.get("disaster_risk_index", type=float) or 0
    barangay.past_calamity_freq = request.form.get("past_calamity_freq", type=int) or 0


@admin_bp.route("/barangays/add", methods=["POST"])
@login_required
@role_required("system_admin")
def add_barangay():
    barangay = Barangay()
    _apply_barangay_form(barangay)

    if not barangay.barangay_name or barangay.city_municipality not in TARGET_LGUS:
        flash("Enter a barangay name and choose a valid municipality.", "error")
        return redirect(url_for("admin.barangays"))

    db.session.add(barangay)
    db.session.flush()
    log_admin_activity(current_user.user_id, "barangay_created", f"{current_user.name} added barangay {barangay.barangay_name}", barangay_id=barangay.barangay_id)
    db.session.commit()
    flash(f"{barangay.barangay_name} added.", "success")
    return redirect(url_for("admin.barangays"))


@admin_bp.route("/barangays/<int:barangay_id>/edit", methods=["POST"])
@login_required
@role_required("system_admin")
def edit_barangay(barangay_id):
    barangay = Barangay.query.get_or_404(barangay_id)
    _apply_barangay_form(barangay)

    if not barangay.barangay_name or barangay.city_municipality not in TARGET_LGUS:
        flash("Enter a barangay name and choose a valid municipality.", "error")
        return redirect(url_for("admin.barangays"))

    log_admin_activity(current_user.user_id, "barangay_updated", f"{current_user.name} updated barangay {barangay.barangay_name}", barangay_id=barangay.barangay_id)
    db.session.commit()
    flash(f"{barangay.barangay_name} updated.", "success")
    return redirect(url_for("admin.barangays"))


@admin_bp.route("/barangays/export")
@login_required
@role_required("system_admin")
def export_barangays():
    barangay_list = Barangay.query.filter(Barangay.city_municipality.in_(TARGET_LGUS)).order_by(
        Barangay.city_municipality, Barangay.barangay_name
    ).all()

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow([
        "Barangay", "Municipality", "Population", "Households", "Poverty Incidence (%)",
        "Disaster Risk Index", "Past Calamity Freq.", "Historical Allocation", "Risk Level",
    ])
    for b in barangay_list:
        writer.writerow([
            b.barangay_name, b.city_municipality, b.population, b.num_households,
            b.poverty_incidence, b.disaster_risk_index, b.past_calamity_freq,
            historical_allocation_for(b.barangay_id), _risk_level(b.disaster_risk_index),
        ])

    return Response(
        buffer.getvalue(), mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=barangays.csv"},
    )


# ---------------------------------------------------------------------------
# System Activity / Audit Logs — same table, different slice. Audit Logs
# narrows to AUDIT_ACTION_TYPES (account/security actions); System Activity
# shows everything so admins get one full operational feed.
# ---------------------------------------------------------------------------

def _activity_rows(query, search_query, limit=200):
    if search_query:
        query = query.join(User, ActivityLog.actor_id == User.user_id, isouter=True).filter(
            db.or_(ActivityLog.description.ilike(f"%{search_query}%"), User.name.ilike(f"%{search_query}%"))
        )
    logs = query.order_by(ActivityLog.created_at.desc()).limit(limit).all()
    return [
        {"log": log, "module": module_for_action(log.action_type), "badge_class": module_badge_class(log.action_type)}
        for log in logs
    ]


@admin_bp.route("/activity")
@login_required
@role_required("system_admin")
def activity():
    search_query = request.args.get("q", "").strip()
    rows = _activity_rows(ActivityLog.query, search_query)
    return render_template("admin/activity.html", rows=rows, search_query=search_query)


@admin_bp.route("/audit-logs")
@login_required
@role_required("system_admin")
def audit_logs():
    search_query = request.args.get("q", "").strip()
    rows = _activity_rows(ActivityLog.query.filter(ActivityLog.action_type.in_(AUDIT_ACTION_TYPES)), search_query)
    return render_template("admin/audit_logs.html", rows=rows, search_query=search_query)


def _export_activity(query, filename):
    logs = query.order_by(ActivityLog.created_at.desc()).limit(1000).all()
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["Timestamp", "User", "Action", "Module", "Description", "IP Address"])
    for log in logs:
        writer.writerow([
            log.created_at.strftime("%Y-%m-%d %H:%M:%S") if log.created_at else "",
            log.actor.name if log.actor else "System",
            log.action_type, module_for_action(log.action_type), log.description,
            log.ip_address or "",
        ])
    return Response(
        buffer.getvalue(), mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@admin_bp.route("/activity/export")
@login_required
@role_required("system_admin")
def export_activity():
    return _export_activity(ActivityLog.query, "system_activity.csv")


@admin_bp.route("/audit-logs/export")
@login_required
@role_required("system_admin")
def export_audit_logs():
    return _export_activity(ActivityLog.query.filter(ActivityLog.action_type.in_(AUDIT_ACTION_TYPES)), "audit_logs.csv")


# ---------------------------------------------------------------------------
# System Settings
# ---------------------------------------------------------------------------

@admin_bp.route("/settings", methods=["GET", "POST"])
@login_required
@role_required("system_admin")
def settings_page():
    if request.method == "POST":
        healthy = request.form.get("warehouse_healthy_threshold", type=float)
        moderate = request.form.get("warehouse_moderate_threshold", type=float)
        alerts_enabled = request.form.get("low_stock_alert_enabled") == "on"

        if healthy is None or moderate is None or not (0 < moderate < healthy <= 1):
            flash("Thresholds must be between 0 and 1, with Healthy greater than Moderate.", "error")
            return redirect(url_for("admin.settings_page"))

        set_setting("warehouse_healthy_threshold", healthy, user_id=current_user.user_id)
        set_setting("warehouse_moderate_threshold", moderate, user_id=current_user.user_id)
        set_setting("low_stock_alert_enabled", alerts_enabled, user_id=current_user.user_id)

        log_admin_activity(current_user.user_id, "settings_updated", f"{current_user.name} updated system settings")
        db.session.commit()
        flash("System settings updated.", "success")
        return redirect(url_for("admin.settings_page"))

    current_values = {
        key: get_setting(key, default, cast=cast) for key, (default, cast, _label) in SETTINGS_SCHEMA.items()
    }
    return render_template(
        "admin/settings.html", values=current_values, schema=SETTINGS_SCHEMA, target_lgus=TARGET_LGUS,
    )
