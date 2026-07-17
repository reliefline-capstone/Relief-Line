from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required
from app.models.user import User

auth_bp = Blueprint("auth", __name__)

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