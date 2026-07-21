import hashlib

from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app
from flask_login import login_user, logout_user, login_required
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

from app.extensions import db
from app.models.user import User
from app.utils.mail import send_email

auth_bp = Blueprint("auth", __name__)

RESET_TOKEN_MAX_AGE = 3600  # 1 hour


def _reset_serializer():
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"], salt="password-reset")


def _password_fingerprint(password_hash):
    """Short fingerprint of the user's CURRENT password hash, embedded in the
    reset token. Resetting the password changes this hash, which invalidates
    every token issued before the reset — no separate token/expiry table
    needed, and a token can't be replayed after it's been used once."""
    return hashlib.sha256(password_hash.encode()).hexdigest()[:16]


def _make_reset_token(user):
    return _reset_serializer().dumps({"uid": user.user_id, "pwf": _password_fingerprint(user.password)})


def _verify_reset_token(token):
    try:
        data = _reset_serializer().loads(token, max_age=RESET_TOKEN_MAX_AGE)
    except (BadSignature, SignatureExpired):
        return None
    user = User.query.get(data.get("uid"))
    if not user or _password_fingerprint(user.password) != data.get("pwf"):
        return None
    return user


@auth_bp.route("/")
def landing():
    return redirect(url_for("auth.login"))


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            login_user(user)
            if user.role == "pswdo_admin":
                return redirect(url_for("pswdo.dashboard"))
            elif user.role == "cswdo_admin":
                return redirect(url_for("cswdo.dashboard"))
            elif user.role == "barangay_user":
                return redirect(url_for("barangay.dashboard"))
            return redirect(url_for("auth.login"))
        flash("Invalid username/email or password.", "error")

    return render_template("login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))


@auth_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        user = User.query.filter_by(email=email).first()

        # Same message whether or not the email is registered, so this page
        # can't be used to probe which emails have accounts.
        generic_message = "If that email is registered, a reset link has been sent to it."

        if user:
            token = _make_reset_token(user)
            reset_url = url_for("auth.reset_password", token=token, _external=True)
            sent = False
            try:
                sent = send_email(
                    user.email, "ReliefLine — Reset your password",
                    f"Hi {user.name},\n\nUse the link below to reset your ReliefLine password. "
                    f"This link expires in 1 hour.\n\n{reset_url}\n\n"
                    f"If you didn't request this, you can ignore this email.",
                )
            except Exception:
                sent = False

            if sent:
                flash(generic_message, "success")
            else:
                # No MAIL_SERVER configured yet (see app/utils/mail.py) — show the
                # link directly so the reset flow stays fully usable without real
                # SMTP credentials. Starts sending real email automatically once
                # MAIL_SERVER/MAIL_USERNAME/MAIL_PASSWORD are set in .env.
                flash(
                    "Email delivery isn't configured yet, so here's your reset link directly: "
                    f'<a href="{reset_url}">{reset_url}</a> (expires in 1 hour)',
                    "success",
                )
        else:
            flash(generic_message, "success")

        return redirect(url_for("auth.forgot_password"))

    return render_template("forgot_password.html")


@auth_bp.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    user = _verify_reset_token(token)
    if not user:
        flash("That reset link is invalid or has expired. Request a new one below.", "error")
        return redirect(url_for("auth.forgot_password"))

    if request.method == "POST":
        new_password = request.form.get("new_password", "")
        confirm_password = request.form.get("confirm_password", "")

        if len(new_password) < 8:
            flash("New password must be at least 8 characters long.", "error")
        elif new_password != confirm_password:
            flash("New password and confirmation do not match.", "error")
        else:
            user.set_password(new_password)
            db.session.commit()
            flash("Password reset. You can now log in with your new password.", "success")
            return redirect(url_for("auth.login"))

    return render_template("reset_password.html", user_email=user.email)


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
