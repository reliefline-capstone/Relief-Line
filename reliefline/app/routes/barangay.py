from flask import Blueprint, render_template
from flask_login import login_required
from app.utils.decorators import role_required

barangay_bp = Blueprint("barangay", __name__)

@barangay_bp.route("/dashboard")
@login_required
@role_required("barangay_user")
def dashboard():
    return render_template("barangay/dashboard.html")