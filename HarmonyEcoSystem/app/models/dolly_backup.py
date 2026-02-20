from ..extensions import db


class DollyEOLInfoBackup(db.Model):
    """Backup table for DollyEOLInfo - READ ONLY for production date lookup."""

    __tablename__ = "DollyEOLInfoBackup"
    __table_args__ = {"extend_existing": True}

    RECEIPTID = db.Column(db.Integer, primary_key=True)
    DollyNo = db.Column(db.String(50), nullable=True)
    DollyOrderNo = db.Column(db.Integer, nullable=True)
    VinNo = db.Column(db.String(50), nullable=True)
    EOLID = db.Column(db.String(50), nullable=True)
    EOLName = db.Column(db.String(100), nullable=True)
    CustomerReferans = db.Column(db.String(100), nullable=True)
    Adet = db.Column(db.Integer, nullable=True)
    EOLDATE = db.Column(db.DateTime, nullable=True)
    EOLDollyBarcode = db.Column(db.Integer, nullable=True)

    def __repr__(self) -> str:
        return f"<DollyEOLInfoBackup DollyNo={self.DollyNo} EOLDATE={self.EOLDATE}>"
