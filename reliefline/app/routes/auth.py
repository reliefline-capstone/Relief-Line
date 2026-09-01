from datetime import datetime

from app.utils.timezone import ph_now

from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user

from app.extensions import db
from app.models.user import User
from app.models.password_reset_request import PasswordResetRequest, DEFAULT_RESET_PASSWORD
from app.utils.activity import log_admin_activity

auth_bp = Blueprint("auth", __name__)

# Where each role lands after login (and after a forced password change).
_ROLE_DASHBOARD_ENDPOINT = {
    "system_admin": "admin.dashboard",
    "pswdo_admin": "pswdo.dashboard",
    "cswdo_admin": "cswdo.dashboard",
    "barangay_user": "barangay.dashboard",
}


def _dashboard_endpoint(role):
    return _ROLE_DASHBOARD_ENDPOINT.get(role, "auth.login")


@auth_bp.route("/")
def landing():
    return render_template("landing.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        # Which page the form was submitted from, so a failed attempt lands the
        # user back where they were instead of bouncing them to a different
        # login screen. "landing" = the marketing page's hero login card;
        # anything else = the standalone /login page.
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
            login_user(user)
            user.last_login = ph_now()
            log_admin_activity(user.user_id, "login", f"{user.name} logged in")
            db.session.commit()
            if user.must_change_password:
                return redirect(url_for("auth.force_change_password"))
            return redirect(url_for(_dashboard_endpoint(user.role)))
        flash("Invalid username/email or password.", "error")
        return retry

    # The standalone login page has been retired — the landing page's hero
    # already has a full login form (origin=landing), so a bare GET here
    # just lands the user there instead of a separate page.
    return redirect(url_for("auth.landing") + "#login-card")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.landing"))


@auth_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        user = User.query.filter_by(email=email).first()

        if user:
            already_pending = PasswordResetRequest.query.filter_by(
                user_id=user.user_id, status="pending"
            ).first()
            if not already_pending:
                db.session.add(PasswordResetRequest(user_id=user.user_id))
                db.session.commit()

        # Same confirmation message whether or not the email is registered,
        # so this can't be used to probe which emails have accounts.
        flash(
            "If that account exists, a password reset request has been sent "
            "to a System Administrator for approval.",
            "success",
        )
        return redirect(url_for("auth.landing"))

    # Forgot Password is now a modal on the landing page (opened by the
    # "Forgot Password?" button) rather than its own standalone page.
    return redirect(url_for("auth.landing"))


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

    return render_template("force_change_password.html")


@auth_bp.route("/help")
def help_page():
    return render_template("help.html")


@auth_bp.route("/contact")
def contact_page():
    return render_template("contact.html")


@auth_bp.route("/privacy")
def privacy_page():
    return render_template("privacy.html")


@auth_bp.route("/terms")
def terms_page():
    return render_template("terms.html")
