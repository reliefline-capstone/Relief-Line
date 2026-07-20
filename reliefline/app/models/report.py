from app.extensions import db

class ReportLog(db.Model):
    __tablename__ = "report_logs"

    report_id = db.Column(db.Integer, primary_key=True)
    report_type = db.Column(db.String(50), nullable=False)
    format = db.Column(db.Enum("pdf", "excel"), nullable=False)
    pages = db.Column(db.Integer, default=1)
    filters_json = db.Column(db.Text, nullable=True)
    generated_by = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=True)
    generated_at = db.Column(db.DateTime, server_default=db.text("CURRENT_TIMESTAMP"))

    generated_by_user = db.relationship("User")
