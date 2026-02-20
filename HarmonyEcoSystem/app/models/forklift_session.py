from datetime import datetime

from ..extensions import db


class ForkliftLoginSession(db.Model):
    """Tracks forklift operator logins via barcode scanning.
    
    Workflow:
    1. Operator scans their employee barcode on Android app
    2. System validates barcode and creates session
    3. Session token is returned to app
    4. App sends token with every API request
    5. System validates token and tracks user activity
    6. Session auto-expires after 8 hours or manual logout
    """

    __tablename__ = "ForkliftLoginSession"
    __table_args__ = {"extend_existing": True}

    Id = db.Column(db.Integer, primary_key=True)
    OperatorBarcode = db.Column(db.String(50), nullable=False)
    OperatorName = db.Column(db.String(100), nullable=False)
    DeviceId = db.Column(db.String(100), nullable=True)
    SessionToken = db.Column(db.String(128), nullable=False, unique=True)
    IsActive = db.Column(db.Boolean, nullable=False, default=True)
    IsAdmin = db.Column(db.Boolean, nullable=False, default=False)
    Role = db.Column(db.String(20), nullable=False, default='forklift')
    LoginAt = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    LogoutAt = db.Column(db.DateTime, nullable=True)
    ExpiresAt = db.Column(db.DateTime, nullable=False)
    LastActivityAt = db.Column(db.DateTime, nullable=True)
    IpAddress = db.Column(db.String(50), nullable=True)
    UserAgent = db.Column(db.String(255), nullable=True)
    Metadata = db.Column(db.Text, nullable=True)

    def __repr__(self) -> str:
        return f"<ForkliftLoginSession {self.OperatorName} - {self.SessionToken[:8]}...>"
    
    def is_expired(self) -> bool:
        """Check if session is expired"""
        return datetime.utcnow() > self.ExpiresAt
    
    def update_activity(self):
        """Update last activity timestamp"""
        self.LastActivityAt = datetime.utcnow()
