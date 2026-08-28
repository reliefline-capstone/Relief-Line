from app.extensions import db

class BarangayReport(db.Model):
    """Barangay-submitted disaster impact report + relief request, reviewed by
    the CSWDO/MSWDO office. Verifying a report upserts the matching
    BarangayDisasterStatus row for the same barangay+event, so the priority
    tier shown here, on the dashboard, and on the GIS map all stay driven by
    one source of truth once a report is verified.

    The barangay states `requested_food_packs` — its own indication of need.
    The Linear Regression model (app.ml.predict) is shown alongside as
    *decision support*, never as the final figure: the manuscript (Ch.2) is
    explicit that "ReliefLine treats the predicted output as decision support
    rather than an automatic final allocation." CSWDO/MSWDO sets the final
    allocated quantity when it acts on the request.

    Severity (`flood_level`) is COMPUTED server-side from the entered impact
    data (see app.routes.barangay._compute_severity) — not picked by hand.

    Excludes evacuation-center/evacuee headcounts (manuscript: real-time
    evacuee monitoring not supported). Non-food item estimates
    (drinking_water_cases, hygiene_kits_est, blankets_est) are included on
    purpose — non-food requirements are "contingent on damage assessments."
    """
    __tablename__ = "barangay_reports"

    report_id = db.Column(db.Integer, primary_key=True)
    barangay_id = db.Column(db.Integer, db.ForeignKey("barangays.barangay_id"), nullable=False)
    # Nullable — a barangay can file a report anytime, not only while PSWDO
    # has a declared active DisasterEvent (see app.routes.barangay's
    # new_damage_report/_apply_report_form, which auto-links to whichever
    # event is currently active, or leaves this NULL when none is). A NULL
    # report never updates BarangayDisasterStatus (see
    # app.routes.cswdo.verify_damage_report) since that table stays
    # event-scoped — it just doesn't participate in a per-event GIS view.
    event_id = db.Column(db.Integer, db.ForeignKey("disaster_events.event_id"), nullable=True)

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
    # Situation-specific fields — only one branch is relevant per report,
    # chosen by disaster_type (Typhoon / Wind / Flash Flood). The form shows/
    # hides these; unused branch fields stay NULL/0.
    roofs_damaged = db.Column(db.Integer, nullable=False, default=0, server_default=db.text("0"))
    wind_signal = db.Column(db.String(20), nullable=True)          # e.g. "Signal No. 3"
    water_level_desc = db.Column(db.String(50), nullable=True)     # e.g. "Waist-deep"
    missing_persons = db.Column(db.Integer, default=0)
    casualties_deaths = db.Column(db.Integer, default=0)

    # Relief Needs step
    # Food packs the barangay is requesting — its own indication of need. The
    # model's estimate is shown next to this field as a reference only; the
    # barangay enters the figure, and CSWDO/MSWDO sets the final allocation.
    requested_food_packs = db.Column(db.Integer, nullable=False, default=0, server_default=db.text("0"))
    # Non-food item estimates (see class docstring)
    drinking_water_cases = db.Column(db.Integer, default=0)
    hygiene_kits_est = db.Column(db.Integer, default=0)
    blankets_est = db.Column(db.Integer, default=0)

    # Evidence step
    remarks = db.Column(db.Text, nullable=True)
    # Comma-joined filenames, same convention as DistributionRecord.validation_file
    photo_paths = db.Column(db.String(500), nullable=True)

    # draft -> pending -> {returned (barangay fixes & resubmits) |
    #   approved (CSWDO will fulfil, an AllocationRecord + delivery is created) |
    #   declined (CSWDO won't fulfil)} -> fulfilled (delivery confirmed received)
    status = db.Column(
        db.Enum("draft", "pending", "returned", "approved", "declined", "fulfilled"),
        default="draft"
    )
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
    def allocation(self):
        """The AllocationRecord CSWDO created when it approved this request, if any."""
        from app.models.allocation import AllocationRecord
        return AllocationRecord.query.filter_by(barangay_report_id=self.report_id).first()

    @property
    def ref(self):
        year = (self.submitted_at or self.created_at).year
        return f"RR-{year}-{self.report_id:03d}"
