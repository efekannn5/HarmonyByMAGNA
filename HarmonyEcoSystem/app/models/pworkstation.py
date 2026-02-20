from ..extensions import db


class PWorkStation(db.Model):
    """Represents production workstations (EOL filtering is applied in service layer)."""

    __tablename__ = "PWorkStation"
    __table_args__ = {"extend_existing": True}

    Id = db.Column(db.Integer, primary_key=True)
    PlantId = db.Column(db.Integer, nullable=False)
    PWorkCenterId = db.Column(db.Integer, nullable=False)
    PWorkStationNo = db.Column(db.String(30), nullable=False)
    PWorkStationName = db.Column(db.String(50), nullable=False)
    GroupCode = db.Column(db.String(30), nullable=True)
    SpecCode1 = db.Column(db.String(30), nullable=True)
    SpecCode2 = db.Column(db.String(30), nullable=True)
    ErpWorkStationNo = db.Column(db.String(50), nullable=False)
    PlantPWorkStationId = db.Column(db.Integer, nullable=True)
    PlantCompanyId = db.Column(db.Integer, nullable=True)
    Status = db.Column(db.Integer, nullable=True)
    InsertDate = db.Column(db.DateTime, nullable=True)
    IsFinishProductStation = db.Column(db.Boolean, nullable=True)
    HideonFactoryConsole = db.Column(db.Boolean, nullable=True)

    def __repr__(self) -> str:
        return f"<PWorkStation Id={self.Id} Name={self.PWorkStationName}>"
