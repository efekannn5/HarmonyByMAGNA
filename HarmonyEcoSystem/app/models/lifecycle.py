from datetime import datetime

from ..extensions import db


class DollyLifecycle(db.Model):
    """Tracks lifecycle status changes for each dolly."""

    __tablename__ = "DollyLifecycle"
    __table_args__ = {"extend_existing": True}

    Id = db.Column(db.Integer, primary_key=True)
    DollyNo = db.Column(db.String(20), nullable=False)
    VinNo = db.Column(db.String(50), nullable=False)
    Status = db.Column(db.String(40), nullable=False)
    Source = db.Column(db.String(30), nullable=True)
    Metadata = db.Column(db.Text, nullable=True)
    CreatedAt = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<DollyLifecycle Dolly={self.DollyNo} Status={self.Status}>"
