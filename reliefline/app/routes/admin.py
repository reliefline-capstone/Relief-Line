# System Admin pages: users, warehouses, barangays, activity log, settings.

import csv
import io

from flask import Blueprint, render_template, request, redirect, url_for, flash, Response
from flask_login import login_required, current_user

from app.extensions import db
from app.utils.decorators import role_required
from app.utils.activity import log_admin_activity, module_for_action, module_badge_class, MODULE_LABELS, DEFAULT_MODULE_LABEL
from app.utils.filters import date_range, iso
from app.utils.presence import is_online, ONLINE_THRESHOLD
from app.utils.settings import SETTINGS_SCHEMA, get_setting, set_setting
from app.utils.timezone import ph_time, ph_now
from app.utils.roles import ROLE_LABELS
from app.utils.mail import send_email
from app.models.user import User
from app.models.office import Office
from app.models.warehouse import WarehouseInventory
from app.models.barangay import Barangay
from app.models.activity_log import ActivityLog
from app.models.password_reset_request import PasswordResetRequest, DEFAULT_RESET_PASSWORD
from app.routes.pswdo import TARGET_LGUS
from app.ml.train import historical_allocation_for

admin_bp = Blueprint("admin", __name__)

ROLE_CHOICES = ["system_admin", "pswdo_admin", "cswdo_admin", "barangay_user"]


# Emails a user their temporary password.
# If email isn't set up, the password is shown on screen to the admin instead.
def _deliver_credentials(user, temp_password, subject, intro):
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
            f"Email delivery isn't configured, so here's the temporary password directly - "
            f"share it with {user.name} securely: {temp_password}",
            "success",
        )


# The office type shown on screen: Provincial, Warehouse, City, or Municipal.
def _office_type_label(office):
    if office.office_type == "pswdo":
        return "Provincial" if office.area_covered == "Province of Pangasinan" else "Warehouse"
    return "City" if office.area_covered == "Urdaneta City" else "Municipal"


# The short office code shown on screen (e.g. PSWDO, CSWDO, MSWDO-SB, WH-...).
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


# Page: /admin/dashboard - System Admin dashboard: total users, who is online, deactivated accounts,
# this month's activity count and recently active users.
@admin_bp.route("/dashboard")
@login_required
@role_required("system_admin")
def dashboard():
    total_users = User.query.count()
    active_sessions = User.query.filter(User.last_activity >= ph_now() - ONLINE_THRESHOLD).count()
    inactive_accounts = User.query.filter_by(is_active=False).count()
    month_start = ph_now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    activity_entries_this_month = ActivityLog.query.filter(ActivityLog.created_at >= month_start).count()

    recent_users = User.query.order_by(
        db.func.coalesce(User.last_login, User.created_at).desc()
    ).limit(5).all()

    return render_template(
        "admin/dashboard.html", now=ph_now(),
        total_users=total_users, active_sessions=active_sessions,
        inactive_accounts=inactive_accounts, activity_entries_this_month=activity_entries_this_month,
        recent_users=recent_users, is_online=is_online,
    )


# Page: /admin/users - User Management page: list of all user accounts.
# Can be searched by name/email and filtered by role and active/inactive status.
@admin_bp.route("/users")
@login_required
@role_required("system_admin")
def users():
    search_query = request.args.get("q", "").strip()
    status_filter = request.args.get("status", "all")
    role_filter = request.args.get("role", "all")

    base_q = User.query
    if search_query:
        like = f"%{search_query}%"
        base_q = base_q.filter(db.or_(User.name.ilike(like), User.email.ilike(like)))
    if role_filter in ROLE_CHOICES:
        base_q = base_q.filter(User.role == role_filter)

    active_count = base_q.filter(User.is_active.is_(True)).count()
    inactive_count = base_q.filter(User.is_active.is_(False)).count()

    users_q = base_q
    if status_filter == "active":
        users_q = users_q.filter(User.is_active.is_(True))
    elif status_filter == "inactive":
        users_q = users_q.filter(User.is_active.is_(False))

    user_list = users_q.order_by(User.name).all()
    offices = Office.query.order_by(Office.office_name).all()
    barangays = Barangay.query.order_by(Barangay.city_municipality, Barangay.barangay_name).all()

    return render_template(
        "admin/users.html", users=user_list, offices=offices, barangays=barangays,
        search_query=search_query, role_choices=ROLE_CHOICES, status_filter=status_filter, role_filter=role_filter,
        active_count=active_count, inactive_count=inactive_count, total_count=active_count + inactive_count,
        is_online=is_online,
    )


# Links a user to their office (for PSWDO/CSWDO admins) or to their barangay (for barangay users),
# depending on the chosen role.
def _apply_user_office_barangay(user, role):
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


# Action: /admin/users/add - Creates a new user account with a temporary password.
# The email must not already be used by another account.
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

    temp_password = DEFAULT_RESET_PASSWORD
    user = User(name=name, email=email, role=role, is_active=True, must_change_password=True)
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
        user, temp_password, "ReliefLine - Your account was created",
        f"Hi {name}, a ReliefLine account was created for you as a {ROLE_LABELS.get(role, role)}.",
    )
    return redirect(url_for("admin.users"))


# Action: /admin/users/<int:user_id>/edit - Saves changes to a user account (name, email, role, office or barangay).
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


# Action: /admin/users/<int:user_id>/reset-password - Resets a user to the default password (emailed or shown on screen),
# makes them change it at next login, and records it in the activity log.
@admin_bp.route("/users/<int:user_id>/reset-password", methods=["POST"])
@login_required
@role_required("system_admin")
def reset_user_password(user_id):
    user = User.query.get_or_404(user_id)
    temp_password = DEFAULT_RESET_PASSWORD
    user.set_password(temp_password)
    user.must_change_password = True

    log_admin_activity(current_user.user_id, "user_password_reset", f"{current_user.name} reset the password for {user.name}")
    db.session.commit()

    _deliver_credentials(
        user, temp_password, "ReliefLine - Your password was reset",
        f"Hi {user.name}, your ReliefLine password was reset by a System Administrator.",
    )
    return redirect(url_for("admin.users"))


# Action: /admin/users/<int:user_id>/toggle-active - Activates or deactivates a user account. Deactivated users can't log in.
# An admin can't deactivate themselves, and at least one active System Admin must remain.
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


# Page: /admin/users/<int:user_id>/activity - Shows everything one user has done in the system (their activity log), with filters.
@admin_bp.route("/users/<int:user_id>/activity")
@login_required
@role_required("system_admin")
def user_activity(user_id):
    user = User.query.get_or_404(user_id)
    search_query = request.args.get("q", "").strip()
    query, filters = _activity_filters(ActivityLog.query.filter_by(actor_id=user_id))
    rows = _activity_rows(query, search_query, limit=500)
    return render_template("admin/user_activity.html", user=user, rows=rows, search_query=search_query, **filters)


# Download: /admin/users/<int:user_id>/activity/export - Downloads one user's activity log as a CSV (spreadsheet) file.
@admin_bp.route("/users/<int:user_id>/activity/export")
@login_required
@role_required("system_admin")
def export_user_activity(user_id):
    user = User.query.get_or_404(user_id)
    filename = f"{user.name.replace(' ', '_')}_activity.csv"
    query, _ = _activity_filters(ActivityLog.query.filter_by(actor_id=user_id))
    return _export_activity(_search_activity(query, request.args.get("q", "").strip()), filename)


# Page: /admin/password-reset-requests - Password Reset Requests page: 'forgot password' requests to approve or deny.
# Opening the page clears the sidebar badge.
@admin_bp.route("/password-reset-requests")
@login_required
@role_required("system_admin")
def password_reset_requests():
    status_filter = request.args.get("status", "pending")

    base_q = PasswordResetRequest.query
    pending_count = base_q.filter_by(status="pending").count()
    approved_count = base_q.filter_by(status="approved").count()
    denied_count = base_q.filter_by(status="denied").count()

    requests_q = base_q
    if status_filter in ("pending", "approved", "denied"):
        requests_q = requests_q.filter_by(status=status_filter)

    request_list = requests_q.order_by(PasswordResetRequest.requested_at.desc()).all()

    PasswordResetRequest.query.filter_by(status="pending", is_seen=False).update(
        {"is_seen": True}, synchronize_session=False
    )
    db.session.commit()

    return render_template(
        "admin/password_reset_requests.html", requests=request_list, status_filter=status_filter,
        pending_count=pending_count, approved_count=approved_count, denied_count=denied_count,
        total_count=pending_count + approved_count + denied_count,
    )


# Action: /admin/password-reset-requests/<int:request_id>/approve - Approves a reset: the account gets the default reset password,
# and the user must choose a new password at their next login.
@admin_bp.route("/password-reset-requests/<int:request_id>/approve", methods=["POST"])
@login_required
@role_required("system_admin")
def approve_password_reset_request(request_id):
    reset_request = PasswordResetRequest.query.get_or_404(request_id)
    if reset_request.status != "pending":
        flash("That request has already been reviewed.", "error")
        return redirect(url_for("admin.password_reset_requests"))

    user = reset_request.user
    user.set_password(DEFAULT_RESET_PASSWORD)
    # The user must choose a new password at their next login.
    user.must_change_password = True
    reset_request.status = "approved"
    reset_request.reviewed_by = current_user.user_id
    reset_request.reviewed_at = ph_now()

    log_admin_activity(
        current_user.user_id, "password_reset_request_approved",
        f"{current_user.name} approved a password reset for {user.name}",
    )
    db.session.commit()
    flash(f"{user.name}'s password was reset to the default. They'll be asked to set a new one at their next login.", "success")
    return redirect(url_for("admin.password_reset_requests"))


# Action: /admin/password-reset-requests/<int:request_id>/deny - Denies a password reset request and records it in the activity log.
@admin_bp.route("/password-reset-requests/<int:request_id>/deny", methods=["POST"])
@login_required
@role_required("system_admin")
def deny_password_reset_request(request_id):
    reset_request = PasswordResetRequest.query.get_or_404(request_id)
    if reset_request.status != "pending":
        flash("That request has already been reviewed.", "error")
        return redirect(url_for("admin.password_reset_requests"))

    reset_request.status = "denied"
    reset_request.reviewed_by = current_user.user_id
    reset_request.reviewed_at = ph_now()

    log_admin_activity(
        current_user.user_id, "password_reset_request_denied",
        f"{current_user.name} denied a password reset request for {reset_request.user.name}",
    )
    db.session.commit()
    flash(f"Denied the password reset request for {reset_request.user.name}.", "success")
    return redirect(url_for("admin.password_reset_requests"))


# Page: /admin/offices - Warehouse Management page: list of PSWDO and CSWDO/MSWDO offices and their warehouses,
# with number of users, capacity and minimum food pack level.
@admin_bp.route("/offices")
@login_required
@role_required("system_admin")
def offices():
    office_list = Office.query.order_by(Office.office_type, Office.office_name).all()
    user_counts = dict(
        db.session.query(User.office_id, db.func.count(User.user_id))
        .filter(User.office_id.isnot(None)).group_by(User.office_id).all()
    )
    food_pack_mins = dict(
        db.session.query(WarehouseInventory.office_id, WarehouseInventory.min_stock_level)
        .filter(WarehouseInventory.item_type == "food_pack").all()
    )
    rows = [{
        "office": o, "code": _office_code(o), "type_label": _office_type_label(o),
        "user_count": user_counts.get(o.office_id, 0),
        "food_pack_min": food_pack_mins.get(o.office_id, 0),
    } for o in office_list]

    return render_template("admin/offices.html", rows=rows)


# Copies the office form fields (name, type, area, capacity, address, contact) into the office record.
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


# Saves the minimum food pack stock (reorder point) for an office's warehouse.
# Below this level, the stock shows as 'Low'.
def _apply_food_pack_min(office):
    raw = request.form.get("food_pack_min_stock", type=int)
    if raw is None:
        return
    fp = WarehouseInventory.query.filter_by(
        office_id=office.office_id, item_type="food_pack"
    ).first()
    if fp is None:
        fp = WarehouseInventory(
            office_id=office.office_id, item_type="food_pack",
            item_name="Food Packs", unit="packs", quantity_available=0,
        )
        db.session.add(fp)
    fp.min_stock_level = max(raw, 0)
    fp.updated_by = current_user.user_id


# Action: /admin/offices/add - Adds a new office/warehouse.
@admin_bp.route("/offices/add", methods=["POST"])
@login_required
@role_required("system_admin")
def add_office():
    office = Office(is_active=True)
    _apply_office_form(office)

    if not office.office_name or not office.area_covered:
        flash("Enter a warehouse name and area covered.", "error")
        return redirect(url_for("admin.offices"))

    db.session.add(office)
    db.session.flush()
    _apply_food_pack_min(office)
    log_admin_activity(current_user.user_id, "office_created", f"{current_user.name} added office {office.office_name}", office_id=office.office_id)
    db.session.commit()
    flash(f"{office.office_name} added.", "success")
    return redirect(url_for("admin.offices"))


# Action: /admin/offices/<int:office_id>/edit - Saves changes to an office/warehouse.
@admin_bp.route("/offices/<int:office_id>/edit", methods=["POST"])
@login_required
@role_required("system_admin")
def edit_office(office_id):
    office = Office.query.get_or_404(office_id)
    _apply_office_form(office)

    if not office.office_name or not office.area_covered:
        flash("Enter a warehouse name and area covered.", "error")
        return redirect(url_for("admin.offices"))

    _apply_food_pack_min(office)
    log_admin_activity(current_user.user_id, "office_updated", f"{current_user.name} updated office {office.office_name}", office_id=office.office_id)
    db.session.commit()
    flash(f"{office.office_name} updated.", "success")
    return redirect(url_for("admin.offices"))


# Action: /admin/offices/<int:office_id>/toggle-active - Activates or deactivates an office/warehouse.
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


# Page: /admin/barangays - Barangay Management page: list of barangays in the 3 municipalities,
# with population, households and typical past food pack allocation.
@admin_bp.route("/barangays")
@login_required
@role_required("system_admin")
def barangays():
    search_query = request.args.get("q", "").strip()
    municipality_filter = request.args.get("municipality", "all")
    barangays_q = Barangay.query.filter(Barangay.city_municipality.in_(TARGET_LGUS))
    if municipality_filter in TARGET_LGUS:
        barangays_q = barangays_q.filter(Barangay.city_municipality == municipality_filter)
    if search_query:
        barangays_q = barangays_q.filter(Barangay.barangay_name.ilike(f"%{search_query}%"))
    barangay_list = barangays_q.order_by(Barangay.city_municipality, Barangay.barangay_name).all()

    rows = [{
        "barangay": b,
        "historical_allocation": historical_allocation_for(b.barangay_id),
    } for b in barangay_list]

    total_barangays = len(barangay_list)

    return render_template(
        "admin/barangays.html", rows=rows, search_query=search_query, municipality_filter=municipality_filter,
        total_barangays=total_barangays, target_lgus=TARGET_LGUS,
    )


# Copies the barangay form fields (name, municipality, population, households) into the barangay record.
def _apply_barangay_form(barangay):
    barangay.barangay_name = request.form.get("barangay_name", "").strip()
    barangay.city_municipality = request.form.get("city_municipality", "")
    barangay.population = request.form.get("population", type=int) or 0
    barangay.num_households = request.form.get("num_households", type=int) or 0


# Action: /admin/barangays/add - Adds a new barangay.
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


# Action: /admin/barangays/<int:barangay_id>/edit - Saves changes to a barangay.
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


# Download: /admin/barangays/export - Downloads the barangay list as a CSV (spreadsheet) file.
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
        "Barangay", "Municipality", "Population", "Households", "Historical Allocation",
    ])
    for b in barangay_list:
        writer.writerow([
            b.barangay_name, b.city_municipality, b.population, b.num_households,
            historical_allocation_for(b.barangay_id),
        ])

    return Response(
        buffer.getvalue(), mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=barangays.csv"},
    )


ROLE_GROUP_ORDER = ["pswdo_admin", "cswdo_admin", "barangay_user", "system_admin"]


# The user groups for the activity log filter (All Users, PSWDO, CSWDO/MSWDO, Barangay...).
def _actor_groups():
    groups = [{"key": "all", "label": "All Users"}]
    for role in ROLE_GROUP_ORDER:
        groups.append({"key": f"role:{role}", "label": ROLE_LABELS.get(role, role)})
    return groups


# Filters users to one role group.
def _group_user_filter(query, group_key):
    if group_key and group_key.startswith("role:"):
        return query.filter_by(role=group_key.split(":", 1)[1])
    return query


# Filters the activity log to actions done by one user group.
def _apply_actor_group_filter(query, group_key):
    if not group_key or group_key == "all":
        return query
    return _group_user_filter(query.join(User, ActivityLog.actor_id == User.user_id), group_key)


# The user groups, each marked if someone in that group is online right now.
def _groups_with_online_flag():
    online_cutoff = ph_now() - ONLINE_THRESHOLD
    groups = _actor_groups()
    for g in groups:
        g["online"] = _group_user_filter(
            User.query.filter(User.last_activity >= online_cutoff), None if g["key"] == "all" else g["key"]
        ).count() > 0
    return groups


# Applies the 'section of the system' and date filters to the activity log.
def _activity_filters(query):
    module_filter = request.args.get("module", "all")
    date_from, date_to = date_range(request.args)
    if module_filter != "all":
        if module_filter == DEFAULT_MODULE_LABEL:
            query = query.filter(ActivityLog.action_type.notin_(list(MODULE_LABELS)))
        else:
            query = query.filter(ActivityLog.action_type.in_(
                [a for a, m in MODULE_LABELS.items() if m == module_filter]))
    if date_from:
        query = query.filter(db.func.date(ActivityLog.created_at) >= date_from)
    if date_to:
        query = query.filter(db.func.date(ActivityLog.created_at) <= date_to)
    modules = sorted(set(MODULE_LABELS.values())) + [DEFAULT_MODULE_LABEL]
    return query, {"module_filter": module_filter, "module_options": modules,
                   "date_from": iso(date_from), "date_to": iso(date_to)}


# Searches the activity log by description or user name.
def _search_activity(query, search_query):
    if search_query:
        query = query.join(User, ActivityLog.actor_id == User.user_id, isouter=True).filter(
            db.or_(ActivityLog.description.ilike(f"%{search_query}%"), User.name.ilike(f"%{search_query}%"))
        )
    return query


# Gets the activity log rows ready for display (newest first, with section and badge color).
def _activity_rows(query, search_query, limit=200):
    query = _search_activity(query, search_query)
    logs = query.order_by(ActivityLog.created_at.desc()).limit(limit).all()
    return [
        {"log": log, "module": module_for_action(log.action_type), "badge_class": module_badge_class(log.action_type)}
        for log in logs
    ]


# Page: /admin/activity - System Activity page: the full activity log of all users, with search and filters.
@admin_bp.route("/activity")
@login_required
@role_required("system_admin")
def activity():
    search_query = request.args.get("q", "").strip()
    group_key = request.args.get("role", "all")
    query, filters = _activity_filters(_apply_actor_group_filter(ActivityLog.query, group_key))
    rows = _activity_rows(query, search_query)
    groups = _groups_with_online_flag()
    return render_template(
        "admin/activity.html", rows=rows, search_query=search_query,
        groups=groups, selected_group=group_key, **filters,
    )


# Builds the activity log CSV file (up to 1,000 latest entries).
def _export_activity(query, filename):
    logs = query.order_by(ActivityLog.created_at.desc()).limit(1000).all()
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["Timestamp (PH Time)", "User", "Action", "Module", "Description", "IP Address"])
    for log in logs:
        writer.writerow([
            ph_time(log.created_at, "%Y-%m-%d %H:%M:%S") if log.created_at else "",
            log.actor.name if log.actor else "System",
            log.action_type, module_for_action(log.action_type), log.description,
            log.ip_address or "",
        ])
    return Response(
        buffer.getvalue(), mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


# Download: /admin/activity/export - Downloads the activity log as a CSV (spreadsheet) file.
@admin_bp.route("/activity/export")
@login_required
@role_required("system_admin")
def export_activity():
    query, _ = _activity_filters(_apply_actor_group_filter(ActivityLog.query, request.args.get("role", "all")))
    return _export_activity(_search_activity(query, request.args.get("q", "").strip()), "system_activity.csv")


# Page: /admin/settings - System Settings page: the warehouse 'Healthy' and 'Moderate' stock levels
# and the low-stock alert switch.
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


# Page: /admin/profile-settings - System Admin's own Profile Settings page.
@admin_bp.route("/profile-settings")
@login_required
@role_required("system_admin")
def profile_settings():
    return render_template("admin/profile_settings.html")


# Action: /admin/profile-settings - Saves the admin's own name and email (the email must not be used by another account).
@admin_bp.route("/profile-settings", methods=["POST"])
@login_required
@role_required("system_admin")
def update_profile_info():
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip().lower()

    if not name or not email:
        flash("Name and email are required.", "error")
        return redirect(url_for("admin.profile_settings"))

    email_taken = User.query.filter(User.email == email, User.user_id != current_user.user_id).first()
    if email_taken:
        flash(f"{email} is already in use by another account.", "error")
        return redirect(url_for("admin.profile_settings"))

    current_user.name = name
    current_user.email = email
    db.session.commit()
    flash("Profile information updated.", "success")
    return redirect(url_for("admin.profile_settings"))


# Action: /admin/profile-settings/password - Changes the admin's own password.
# The current password must be correct and the new one at least 8 characters.
@admin_bp.route("/profile-settings/password", methods=["POST"])
@login_required
@role_required("system_admin")
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

    return redirect(url_for("admin.profile_settings"))
