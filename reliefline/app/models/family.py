# Database tables: family profiles, and affected families in a report.

from app.extensions import db


# Database table 'barangay_families': the families registered in each barangay (Family Profiles),
# with household head, purok, and the number of members, PWDs, seniors and children.
class Family(db.Model):
    __tablename__ = "barangay_families"

    family_id = db.Column(db.Integer, primary_key=True)
    barangay_id = db.Column(db.Integer, db.ForeignKey("barangays.barangay_id"), nullable=False)

    family_name = db.Column(db.String(150), nullable=False)
    head_name = db.Column(db.String(150), nullable=True)
    purok = db.Column(db.String(100), nullable=True)
    contact_number = db.Column(db.String(20), nullable=True)

    member_count = db.Column(db.Integer, nullable=False, default=1, server_default=db.text("1"))
    pwd_count = db.Column(db.Integer, nullable=False, default=0, server_default=db.text("0"))
    senior_count = db.Column(db.Integer, nullable=False, default=0, server_default=db.text("0"))
    children_count = db.Column(db.Integer, nullable=False, default=0, server_default=db.text("0"))

    is_active = db.Column(db.Boolean, nullable=False, default=True, server_default=db.text("1"))

    created_at = db.Column(db.DateTime, server_default=db.text("CURRENT_TIMESTAMP"))
    updated_at = db.Column(db.DateTime, nullable=True)

    barangay = db.relationship("Barangay", backref="families")

    # Suggested food packs for this family: 1, plus 1 more for each PWD and each senior citizen.
    @property
    def suggested_packs(self):
        return 1 + (self.pwd_count or 0) + (self.senior_count or 0)


# Database table 'barangay_report_families': the families listed as affected in a barangay report,
# and whether each one has already received its food packs.
class ReportAffectedFamily(db.Model):
    __tablename__ = "barangay_report_families"

    id = db.Column(db.Integer, primary_key=True)
    report_id = db.Column(db.Integer, db.ForeignKey("barangay_reports.report_id"), nullable=False)
    family_id = db.Column(db.Integer, db.ForeignKey("barangay_families.family_id", ondelete="SET NULL"), nullable=True)

    family_name = db.Column(db.String(150), nullable=False)
    head_name = db.Column(db.String(150), nullable=True)
    purok = db.Column(db.String(100), nullable=True)
    member_count = db.Column(db.Integer, nullable=False, default=0)
    pwd_count = db.Column(db.Integer, nullable=False, default=0)
    senior_count = db.Column(db.Integer, nullable=False, default=0)
    children_count = db.Column(db.Integer, nullable=False, default=0)

    received = db.Column(db.Boolean, nullable=False, default=False, server_default=db.text("0"))
    received_at = db.Column(db.DateTime, nullable=True)
    packs_given = db.Column(db.Integer, nullable=False, default=0, server_default=db.text("0"))
    received_by = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=True)

    report = db.relationship(
        "BarangayReport",
        backref=db.backref("affected_families_list", cascade="all, delete-orphan", order_by="ReportAffectedFamily.family_name"),
    )
    family = db.relationship("Family")
    received_by_user = db.relationship("User", foreign_keys=[received_by])

    # Suggested food packs for this family: 1, plus 1 more for each PWD and each senior citizen.
    @property
    def suggested_packs(self):
        return 1 + (self.pwd_count or 0) + (self.senior_count or 0)

    # The stock record that shows this family received its food packs
    # (empty if not yet received).
    @property
    def distribution_log(self):
        if not self.received:
            return None
        from app.models.barangay_inventory import BarangayStockLog
        return BarangayStockLog.query.filter_by(
            barangay_id=self.report.barangay_id, source_type="distribution",
            family_id=self.family_id, reason=f"{self.family_name} - {self.report.ref}",
        ).order_by(BarangayStockLog.log_id.desc()).first()
