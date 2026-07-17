from flask import Blueprint, render_template
from flask_login import login_required
from app.utils.decorators import role_required

cswdo_bp = Blueprint("cswdo", __name__)

@cswdo_bp.route("/dashboard")
@login_required
@role_required("cswdo_admin", "system_admin")
def dashboard():
    return render_template("cswdo/dashboard.html")