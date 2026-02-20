from datetime import datetime
from typing import Optional

from ..extensions import db


class WebOperatorTask(db.Model):
    """Represents tasks assigned to web operators for processing part numbers."""

    __tablename__ = "WebOperatorTask"
    __table_args__ = {"extend_existing": True}

    Id = db.Column(db.Integer, primary_key=True)
    PartNumber = db.Column(db.String(50), nullable=False, unique=True)
    Status = db.Column(db.String(20), nullable=False, default="pending")  # pending, in_progress, completed
    AssignedTo = db.Column(db.Integer, db.ForeignKey("UserAccount.Id"), nullable=True)
    GroupTag = db.Column(db.String(20), nullable=False, default="both")  # asn, irsaliye, both
    TotalItems = db.Column(db.Integer, nullable=False, default=0)
    ProcessedItems = db.Column(db.Integer, nullable=False, default=0)
    Metadata = db.Column(db.Text, nullable=True)
    CreatedAt = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    UpdatedAt = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    CompletedAt = db.Column(db.DateTime, nullable=True)

    assigned_user = db.relationship("UserAccount", backref=db.backref("operator_tasks", lazy=True))

    @property
    def progress_percentage(self) -> int:
        if self.TotalItems == 0:
            return 0
        return int((self.ProcessedItems / self.TotalItems) * 100)

    @property
    def can_submit_asn(self) -> bool:
        return self.GroupTag in ["asn", "both"]

    @property
    def can_submit_irsaliye(self) -> bool:
        return self.GroupTag in ["irsaliye", "both"]

    def __repr__(self) -> str:
        return f"<WebOperatorTask {self.PartNumber} - {self.Status}>"