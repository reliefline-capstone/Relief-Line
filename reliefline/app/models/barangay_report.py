from app.extensions import db

class BarangayReport(db.Model):
    """Barangay-submitted disaster impact report, reviewed/verified by the
    CSWDO/MSWDO office (Table 10: "validation monitoring"). Verifying a report
    upserts the matching BarangayDisasterStatus row for the same barangay+event,
    so the priority tier shown here, on the dashboard, and on the GIS map all
    stay driven by one source of truth once a report is verified.

    Deliberately excludes evacuation-center/evacuee headcounts and any
    computed relief-pack quantity — the manuscript's Scope and Limitations
    section states real-time evacuee/evacuation-center monitoring is not
    supported, and that non-food item needs are not determined from damage
    assessments. Food pack quantities continue to come from the Linear
    Regression predictive model, not from this report.
    """
    __tablename__ = "barangay_reports"

    report_id = db.Column(db.Integer, primary_key=True)
    barangay_id = db.Column(db.Integer, db.ForeignKey("barangays.barangay_id"), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey("disaster_events.event_id"), nullable=False)

    submitted_by_name = db.Column(db.String(150), nullable=False)
    submitted_by_designation = db.Column(db.String(100), nullable=True)
    submitted_at = db.Column(db.DateTime, server_default=db.text("CURRENT_TIMESTAMP"))

    affected_families = db.Column(db.Integer, default=0)
    affected_individuals = db.Column(db.Integer, default=0)
    totally_damaged_houses = db.Column(db.Integer, default=0)
    partially_damaged_houses = db.Column(db.Integer, default=0)

    # Same 4-tier vocabulary as BarangayDisasterStatus.status, so a report's
    # flood level and the barangay's resulting priority tier are one concept
    # rendered consistently everywhere (dashboard, GIS map, this page).
    flood_level = db.Column(
        db.Enum("normal", "monitoring", "needs_assistance", "high_priority"),
        default="normal"
    )
    flood_depth_m = db.Column(db.Numeric(4, 2), nullable=True)
    remarks = db.Column(db.Text, nullable=True)
    # Comma-joined filenames, same convention as DistributionRecord.validation_file
    photo_paths = db.Column(db.String(500), nullable=True)

    status = db.Column(db.Enum("pending", "verified", "returned"), default="pending")
    review_remarks = db.Column(db.Text, nullable=True)
    reviewed_by = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=True)
    reviewed_at = db.Column(db.DateTime, nullable=True)

    barangay = db.relationship("Barangay", backref="reports")
    event = db.relationship("DisasterEvent")
    reviewed_by_user = db.relationship("User", foreign_keys=[reviewed_by])

    @property
    def ref(self):
        return f"RPT-{self.report_id:03d}"
