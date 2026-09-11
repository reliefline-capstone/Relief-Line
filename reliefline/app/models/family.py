from app.extensions import db


class Family(db.Model):
    """A registered household/family profile for a barangay - the barangay's
    own resident *profiling* registry (panelist-requested addition). Filled
    in once by the barangay on the Family Profiles page and then reused as a
    checklist when filing a Barangay Report: instead of typing
    affected-families/individuals counts by hand, the barangay checks off
    which of its registered families were affected, and
    BarangayReport.affected_families/affected_individuals (plus the
    pwd/senior/children breakdown) are summed from that selection - see
    app.routes.barangay._apply_report_form and ReportAffectedFamily below.

    `pwd_count` / `senior_count` / `children_count` are informational
    sub-counts of `member_count` (a member can be none of the three, e.g. a
    working-age adult with no disability). They aren't forced to add up to
    member_count - they drive the food-pack suggestion formula (1 pack for
    the family + 1 per PWD member + 1 per senior member; see
    BarangayReport.suggested_food_packs), not a strict headcount audit.
    """
    __tablename__ = "barangay_families"

    family_id = db.Column(db.Integer, primary_key=True)
    barangay_id = db.Column(db.Integer, db.ForeignKey("barangays.barangay_id"), nullable=False)

    # A family label ("Dela Cruz Family"), the primary display on every
    # list/checklist. head_name (the actual household head's name, e.g.
    # "Josefa") is a secondary/subtitle field - mainly there to tell apart
    # two families that share both family_name and purok.
    family_name = db.Column(db.String(150), nullable=False)
    head_name = db.Column(db.String(150), nullable=True)
    purok = db.Column(db.String(100), nullable=True)
    contact_number = db.Column(db.String(20), nullable=True)

    member_count = db.Column(db.Integer, nullable=False, default=1, server_default=db.text("1"))
    pwd_count = db.Column(db.Integer, nullable=False, default=0, server_default=db.text("0"))
    senior_count = db.Column(db.Integer, nullable=False, default=0, server_default=db.text("0"))
    children_count = db.Column(db.Integer, nullable=False, default=0, server_default=db.text("0"))

    # Soft-archive rather than hard delete - a family already cited on a past
    # submitted report must stay resolvable. ReportAffectedFamily snapshots
    # its own counts so an archived (or edited) profile never rewrites a past
    # report's numbers; this flag just hides it from new checklists.
    is_active = db.Column(db.Boolean, nullable=False, default=True, server_default=db.text("1"))

    created_at = db.Column(db.DateTime, server_default=db.text("CURRENT_TIMESTAMP"))
    updated_at = db.Column(db.DateTime, nullable=True)

    barangay = db.relationship("Barangay", backref="families")

    @property
    def suggested_packs(self):
        """1 for the family + 1 per PWD member + 1 per senior member."""
        return 1 + (self.pwd_count or 0) + (self.senior_count or 0)


class ReportAffectedFamily(db.Model):
    """One Family checked off as affected on a specific BarangayReport.
    Snapshots the family's member/PWD/senior/children counts *as they were
    at submission time* so editing the family registry later - or archiving
    or deleting the family - never rewrites a past report's numbers.
    """
    __tablename__ = "barangay_report_families"

    id = db.Column(db.Integer, primary_key=True)
    report_id = db.Column(db.Integer, db.ForeignKey("barangay_reports.report_id"), nullable=False)
    family_id = db.Column(db.Integer, db.ForeignKey("barangay_families.family_id", ondelete="SET NULL"), nullable=True)

    family_name = db.Column(db.String(150), nullable=False)
    head_name = db.Column(db.String(150), nullable=True)
    member_count = db.Column(db.Integer, nullable=False, default=0)
    pwd_count = db.Column(db.Integer, nullable=False, default=0)
    senior_count = db.Column(db.Integer, nullable=False, default=0)
    children_count = db.Column(db.Integer, nullable=False, default=0)

    report = db.relationship(
        "BarangayReport",
        backref=db.backref("affected_families_list", cascade="all, delete-orphan", order_by="ReportAffectedFamily.family_name"),
    )
    family = db.relationship("Family")

    @property
    def suggested_packs(self):
        return 1 + (self.pwd_count or 0) + (self.senior_count or 0)
