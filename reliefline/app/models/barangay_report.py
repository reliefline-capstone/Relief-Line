# Database table: barangay situation reports.

from app.extensions import db

# Database table 'barangay_reports': a barangay's situation report during a disaster
# (affected families and people, damaged houses, flood level, photos) and its review status.
class BarangayReport(db.Model):
    __tablename__ = "barangay_reports"

    report_id = db.Column(db.Integer, primary_key=True)
    barangay_id = db.Column(db.Integer, db.ForeignKey("barangays.barangay_id"), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey("disaster_events.event_id"), nullable=True)

    submitted_by_name = db.Column(db.String(150), nullable=False)
    submitted_by_designation = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.text("CURRENT_TIMESTAMP"))
    submitted_at = db.Column(db.DateTime, nullable=True)

    incident_date = db.Column(db.Date, nullable=True)
    incident_time = db.Column(db.Time, nullable=True)
    flood_level = db.Column(
        db.Enum("normal", "monitoring", "needs_assistance", "high_priority"),
        default="normal"
    )

    affected_families = db.Column(db.Integer, default=0)
    affected_individuals = db.Column(db.Integer, default=0)
    affected_pwd = db.Column(db.Integer, nullable=False, default=0, server_default=db.text("0"))
    affected_seniors = db.Column(db.Integer, nullable=False, default=0, server_default=db.text("0"))
    affected_children = db.Column(db.Integer, nullable=False, default=0, server_default=db.text("0"))
    totally_damaged_houses = db.Column(db.Integer, default=0)
    partially_damaged_houses = db.Column(db.Integer, default=0)
    roofs_damaged = db.Column(db.Integer, nullable=False, default=0, server_default=db.text("0"))
    wind_signal = db.Column(db.String(20), nullable=True)

    requested_food_packs = db.Column(db.Integer, nullable=False, default=0, server_default=db.text("0"))
    hygiene_kits_est = db.Column(db.Integer, default=0)
    kitchen_kits_est = db.Column(db.Integer, nullable=False, default=0, server_default=db.text("0"))

    remarks = db.Column(db.Text, nullable=True)
    photo_paths = db.Column(db.String(500), nullable=True)

    status = db.Column(
        db.Enum("draft", "pending", "returned", "approved", "declined", "verified", "fulfilled"),
        default="draft"
    )
    review_remarks = db.Column(db.Text, nullable=True)
    reviewed_by = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=True)
    reviewed_at = db.Column(db.DateTime, nullable=True)

    barangay = db.relationship("Barangay", backref="reports")
    event = db.relationship("DisasterEvent")
    reviewed_by_user = db.relationship("User", foreign_keys=[reviewed_by])

    # True if the report is still a draft (saved but not yet submitted).
    @property
    def is_draft(self):
        return self.status == "draft"

    # The food pack allocation the CSWDO/MSWDO made from this report, if any.
    @property
    def allocation(self):
        from app.models.allocation import AllocationRecord
        return AllocationRecord.query.filter_by(barangay_report_id=self.report_id).first()

    # True if the report should show a 'New' tag:
    # it is still waiting for review and its disaster event hasn't ended.
    @property
    def is_new(self):
        if self.status != "pending":
            return False
        return not (self.event and self.event.status == "ended")

    # The report's reference number shown on screen, e.g. RR-2026-045.
    @property
    def ref(self):
        year = (self.submitted_at or self.created_at).year
        return f"RR-{year}-{self.report_id:03d}"

    # Suggested number of food packs for this report:
    # one per affected family, plus one more for each PWD and each senior citizen.
    @property
    def suggested_food_packs(self):
        return (self.affected_families or 0) + (self.affected_pwd or 0) + (self.affected_seniors or 0)
