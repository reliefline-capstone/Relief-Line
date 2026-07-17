from flask import Blueprint, render_template
from flask_login import login_required

prediction_bp = Blueprint("prediction", __name__)

@prediction_bp.route("/")
@login_required
def index():
    return render_template("prediction/index.html")