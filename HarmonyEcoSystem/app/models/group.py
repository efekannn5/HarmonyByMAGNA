from datetime import datetime

from ..extensions import db


class DollyGroup(db.Model):
    __tablename__ = "DollyGroup"
    __table_args__ = {"extend_existing": True}

    Id = db.Column(db.Integer, primary_key=True)
    GroupName = db.Column(db.String(100), nullable=False)
    Description = db.Column(db.String(255), nullable=True)
    IsActive = db.Column(db.Boolean, nullable=False, default=True)
    CreatedAt = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    UpdatedAt = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class DollyGroupEOL(db.Model):
    __tablename__ = "DollyGroupEOL"
    __table_args__ = {"extend_existing": True}

    Id = db.Column(db.Integer, primary_key=True)
    GroupId = db.Column(db.Integer, db.ForeignKey("DollyGroup.Id"), nullable=False)
    PWorkStationId = db.Column(db.Integer, db.ForeignKey("PWorkStation.Id"), nullable=False)
    ShippingTag = db.Column(db.String(20), nullable=False, default="both")
    CreatedAt = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    group = db.relationship("DollyGroup", backref=db.backref("eols", lazy="joined"))
