# Public pages and login: home, login, logout, forgot password, help.

from app.utils.timezone import ph_now

from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user

from app.extensions import db
from app.models.user import User
from app.models.password_reset_request import PasswordResetRequest, DEFAULT_RESET_PASSWORD
from app.utils.activity import log_admin_activity

auth_bp = Blueprint("auth", __name__)

_ROLE_DASHBOARD_ENDPOINT = {
    "system_admin": "admin.dashboard",
    "pswdo_admin": "pswdo.dashboard",
    "cswdo_admin": "cswdo.dashboard",
    "barangay_user": "barangay.dashboard",
}


# Picks which dashboard to open after login, based on the user's role
# (System Admin, PSWDO, CSWDO/MSWDO, or Barangay).
def _dashboard_endpoint(role):
    return _ROLE_DASHBOARD_ENDPOINT.get(role, "auth.login")


# Page: / - The public home page anyone can see.
# It explains ReliefLine and has the login box.
@auth_bp.route("/")
def landing():
    return render_template("landing.html")


# Page: /login - Login page: checks the email and password.
# If correct, the user is logged in and sent to their dashboard; deactivated accounts are refused.
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        origin = request.form.get("origin", "login")
        retry = (
            redirect(url_for("auth.landing") + "#login-card")
            if origin == "landing" else redirect(url_for("auth.login"))
        )
        user = User.query.filter_by(email=email).first()

        if user and not user.is_active:
            flash("This account has been deactivated. Contact a System Administrator.", "error")
            return retry

        if user and user.check_password(password):
            # Password is correct: log the user in.
            login_user(user)
            user.last_login = ph_now()
            log_admin_activity(user.user_id, "login", f"{user.name} logged in")
            db.session.commit()
            if user.must_change_password:
                return redirect(url_for("auth.login"))
            return redirect(url_for(_dashboard_endpoint(user.role)))
        flash("Invalid username/email or password.", "error")
        return retry

    if current_user.is_authenticated and not current_user.must_change_password:
        return redirect(url_for(_dashboard_endpoint(current_user.role)))

    return render_template(
        "login.html",
        force_password_change=(
            current_user.is_authenticated and current_user.must_change_password
        ),
    )


# Page: /logout - Logs the user out and returns to the home page.
@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.landing"))


# Page: /forgot-password - 'Forgot password' form: sends a reset request to the System Admin to approve.
# Only one pending request per account is kept.
@auth_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        origin = request.form.get("origin", "landing")
        back = url_for("auth.login") if origin == "login" else url_for("auth.landing")
        user = User.query.filter_by(email=email).first()

        if user:
            already_pending = PasswordResetRequest.query.filter_by(
                user_id=user.user_id, status="pending"
            ).first()
            if not already_pending:
                db.session.add(PasswordResetRequest(user_id=user.user_id))
                db.session.commit()

        flash(
            "If that account exists, a password reset request has been sent "
            "to a System Administrator for approval.",
            "success",
        )
        return redirect(back)

    return redirect(url_for("auth.login"))


# Page: /force-change-password - Makes a user whose password was reset choose a new password (at least 8 characters,
# and not the default reset password) before they can use the app.
@auth_bp.route("/force-change-password", methods=["GET", "POST"])
@login_required
def force_change_password():
    if not current_user.must_change_password:
        return redirect(url_for(_dashboard_endpoint(current_user.role)))

    if request.method == "POST":
        new_password = request.form.get("new_password", "")
        confirm_password = request.form.get("confirm_password", "")

        if len(new_password) < 8:
            flash("New password must be at least 8 characters long.", "error")
        elif new_password != confirm_password:
            flash("New password and confirmation do not match.", "error")
        elif new_password == DEFAULT_RESET_PASSWORD:
            flash("Choose a password other than the default one.", "error")
        else:
            current_user.set_password(new_password)
            current_user.must_change_password = False
            db.session.commit()
            flash("Password updated. You're all set.", "success")
            return redirect(url_for(_dashboard_endpoint(current_user.role)))

    return redirect(url_for("auth.login"))


# Page: /help - Help page (public).
@auth_bp.route("/help")
def help_page():
    return render_template("help.html")


# Page: /contact - Contact page (public).
@auth_bp.route("/contact")
def contact_page():
    return render_template("contact.html")


# Page: /privacy - Privacy Policy page (public).
@auth_bp.route("/privacy")
def privacy_page():
    return render_template("privacy.html")


# Page: /terms - Terms of Use page (public).
@auth_bp.route("/terms")
def terms_page():
    return render_template("terms.html")
