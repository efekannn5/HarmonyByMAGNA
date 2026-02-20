from datetime import datetime

from flask_login import UserMixin
from sqlalchemy.orm import deferred

from ..extensions import db


class UserRole(db.Model):
    __tablename__ = "UserRole"
    __table_args__ = {"extend_existing": True}

    Id = db.Column(db.Integer, primary_key=True)
    Name = db.Column(db.String(40), nullable=False, unique=True)
    Description = db.Column(db.String(255), nullable=True)
    CreatedAt = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


class UserAccount(db.Model, UserMixin):
    __tablename__ = "UserAccount"
    __table_args__ = {"extend_existing": True}

    Id = db.Column(db.Integer, primary_key=True)
    Username = db.Column(db.String(80), nullable=False, unique=True)
    DisplayName = db.Column(db.String(120), nullable=True)
    PasswordHash = db.Column(db.String(255), nullable=False)
    Barcode = db.Column(db.String(50), nullable=True, unique=False)  # Unique constraint via filtered index in DB
    RoleId = db.Column(db.Integer, db.ForeignKey("UserRole.Id"), nullable=False)
    IsActive = db.Column(db.Boolean, nullable=False, default=True)
    LastLoginAt = db.Column(db.DateTime, nullable=True)
    CreatedAt = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    UpdatedAt = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    role = db.relationship("UserRole", backref=db.backref("users", lazy=True))

    @property
    def is_active(self) -> bool:  # type: ignore[override]
        return bool(self.IsActive)

    def get_id(self) -> str:  # type: ignore[override]
        return str(self.Id)


class TerminalDevice(db.Model):
    __tablename__ = "TerminalDevice"
    __table_args__ = {"extend_existing": True}

    Id = db.Column(db.Integer, primary_key=True)
    Name = db.Column(db.String(80), nullable=False)
    DeviceIdentifier = db.Column(db.String(100), nullable=True)
    RoleId = db.Column(db.Integer, db.ForeignKey("UserRole.Id"), nullable=False)
    ApiKey = db.Column(db.String(128), nullable=False)
    BarcodeSecret = db.Column(db.String(128), nullable=False)
    IsActive = db.Column(db.Boolean, nullable=False, default=True)
    CreatedAt = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    UpdatedAt = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    role = db.relationship("UserRole", backref=db.backref("devices", lazy=True))


class TerminalBarcodeSession(db.Model):
    __tablename__ = "TerminalBarcodeSession"
    __table_args__ = {"extend_existing": True}

    Id = db.Column(db.Integer, primary_key=True)
    DeviceId = db.Column(db.Integer, db.ForeignKey("TerminalDevice.Id"), nullable=False)
    UserId = db.Column(db.Integer, db.ForeignKey("UserAccount.Id"), nullable=True)
    Token = db.Column(db.String(120), nullable=False)
    ExpiresAt = db.Column(db.DateTime, nullable=False)
    UsedAt = db.Column(db.DateTime, nullable=True)
    CreatedAt = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    device = db.relationship("TerminalDevice", backref=db.backref("sessions", lazy=True))
    user = db.relationship("UserAccount", backref=db.backref("terminal_sessions", lazy=True))


class AuditLog(db.Model):
    __tablename__ = "AuditLog"
    __table_args__ = {"extend_existing": True}

    Id = db.Column(db.Integer, primary_key=True)
    ActorType = db.Column(db.String(30), nullable=False)
    ActorId = db.Column(db.Integer, nullable=True)
    ActorName = db.Column(db.String(120), nullable=True)
    Action = db.Column(db.String(80), nullable=False)
    Resource = db.Column(db.String(80), nullable=True)
    ResourceId = db.Column(db.String(80), nullable=True)
    Payload = db.Column(db.Text, nullable=True)
    CreatedAt = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
