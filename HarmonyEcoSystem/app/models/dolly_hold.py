from datetime import datetime

from ..extensions import db


class DollySubmissionHold(db.Model):
    """Represents a temporary holding record for forklift submissions.
    
    Workflow:
    1. Manuel/Forklift submission: DollyEOLInfo → DollySubmissionHold (Status: pending)
    2. Forklift completes loading: Status → loading_completed
    3. Web operator adds shipment details: SeferNumarasi, PlakaNo
    4. Web operator sends ASN/Irsaliye: DollySubmissionHold → SeferDollyEOL (DELETE + INSERT)
    """

    __tablename__ = "DollySubmissionHold"
    __table_args__ = {"extend_existing": True}

    Id = db.Column(db.Integer, primary_key=True)
    DollyNo = db.Column(db.String(20), nullable=False, index=True)
    VinNo = db.Column(db.String(50), nullable=False, index=True)
    Status = db.Column(db.String(20), nullable=False, default="pending", index=True)
    
    # EOL Information (copied from DollyEOLInfo)
    DollyOrderNo = db.Column(db.String(20), nullable=True)
    CustomerReferans = db.Column(db.String(50), nullable=True)
    PartNumber = db.Column(db.String(50), nullable=True)
    EOLName = db.Column(db.String(50), nullable=True)
    EOLID = db.Column(db.String(20), nullable=True)
    Adet = db.Column(db.Integer, nullable=True, default=1)
    InsertedAt = db.Column(db.DateTime, nullable=True)  # From DollyEOLInfo - preserves original EOL timestamp
    
    # Submission tracking
    TerminalUser = db.Column(db.String(100), nullable=True)  # Who submitted
    ScanOrder = db.Column(db.Integer, nullable=True)  # Sequence of scan (1, 2, 3...)
    LoadingSessionId = db.Column(db.String(50), nullable=True)  # Group scans by session
    LoadingCompletedAt = db.Column(db.DateTime, nullable=True)  # When forklift finished
    
    # Shipment details (operator adds)
    SeferNumarasi = db.Column(db.String(20), nullable=True)
    PlakaNo = db.Column(db.String(20), nullable=True)
    
    # Metadata
    Payload = db.Column(db.Text, nullable=True)
    CreatedAt = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    UpdatedAt = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    SubmittedAt = db.Column(db.DateTime, nullable=True)  # When operator completes ASN/Irsaliye

    def __repr__(self) -> str:
        return f"<DollySubmissionHold Dolly={self.DollyNo} VIN={self.VinNo} Status={self.Status}>"
