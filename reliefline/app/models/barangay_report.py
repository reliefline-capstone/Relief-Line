from app.extensions import db

class BarangayReport(db.Model):
    """Barangay-submitted disaster impact report, reviewed/verified by the
    CSWDO/MSWDO office (Table 10: "validation monitoring"). Verifying a report
    upserts the matching BarangayDisasterStatus row for the same barangay+event,
    so the priority tier shown here, on the dashboard, and on the GIS map all
    stay driven by one source of truth once a report is verified.

    Deliberately excludes evacuation-center/evacuee headcounts and any
    food-pack quantity request — the manuscript's Scope and Limitations
    section states real-time evacuee/evacuation-center monitoring is not
    supported, and food pack quantities come exclusively from the Linear
    Regression predictive model (app.ml.predict), never a manual barangay
    estimate. Non-food item estimates (drinking_water_cases, hygiene_kits_est,
    blankets_est) ARE included here on purpose — the manuscript's Scope and
    Limitations section states non-food item requirements are "contingent on
    damage assessments conducted during active disaster response operations,"
    i.e. reports like this one, unlike food packs.
    """
    __tablename__ = "barangay_reports"

    report_id = db.Column(db.Integer, primary_key=True)
    barangay_id = db.Column(db.Integer, db.ForeignKey("barangays.barangay_id"), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey("disaster_events.event_id"), nullable=False)

    submitted_by_name = db.Column(db.String(150), nullable=False)
    submitted_by_designation = db.Column(db.String(100), nullable=True)
    # Set only once the report actually leaves draft state — NULL while
    # status="draft", same created_at/submitted_at split ReliefRequestBatch
    # already uses (app/models/relief_request_batch.py) so "when was this
    # first drafted" and "when was it actually sent to MSWDO" stay distinct.
    created_at = db.Column(db.DateTime, server_default=db.text("CURRENT_TIMESTAMP"))
    submitted_at = db.Column(db.DateTime, nullable=True)

    # Disaster Info step
    disaster_type = db.Column(db.String(50), nullable=True)
    incident_date = db.Column(db.Date, nullable=True)
    incident_time = db.Column(db.Time, nullable=True)
    flood_depth_m = db.Column(db.Numeric(4, 2), nullable=True)
    # Same 4-tier vocabulary as BarangayDisasterStatus.status, so a report's
    # flood level and the barangay's resulting priority tier are one concept
    # rendered consistently everywhere (dashboard, GIS map, this page).
    flood_level = db.Column(
        db.Enum("normal", "monitoring", "needs_assistance", "high_priority"),
        default="normal"
    )

    # Damage Data step
    affected_families = db.Column(db.Integer, default=0)
    affected_individuals = db.Column(db.Integer, default=0)
    totally_damaged_houses = db.Column(db.Integer, default=0)
    partially_damaged_houses = db.Column(db.Integer, default=0)
    missing_persons = db.Column(db.Integer, default=0)
    casualties_deaths = db.Column(db.Integer, default=0)

    # Relief Needs step — non-food items only (see class docstring)
    drinking_water_cases = db.Column(db.Integer, default=0)
    hygiene_kits_est = db.Column(db.Integer, default=0)
    blankets_est = db.Column(db.Integer, default=0)

    # Evidence step
    remarks = db.Column(db.Text, nullable=True)
    # Comma-joined filenames, same convention as DistributionRecord.validation_file
    photo_paths = db.Column(db.String(500), nullable=True)

    status = db.Column(db.Enum("draft", "pending", "verified", "returned"), default="draft")
    review_remarks = db.Column(db.Text, nullable=True)
    reviewed_by = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=True)
    reviewed_at = db.Column(db.DateTime, nullable=True)

    barangay = db.relationship("Barangay", backref="reports")
    event = db.relationship("DisasterEvent")
    reviewed_by_user = db.relationship("User", foreign_keys=[reviewed_by])

    @property
    def is_draft(self):
        return self.status == "draft"

    @property
    def ref(self):
        year = (self.submitted_at or self.created_at).year
        return f"DR-{year}-{self.report_id:03d}"
