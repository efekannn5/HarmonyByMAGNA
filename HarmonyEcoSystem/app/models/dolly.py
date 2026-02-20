from datetime import date

from ..extensions import db


class DollyEOLInfo(db.Model):
    """Represents a dolly/VIN eşleşmesi."""

    __tablename__ = "DollyEOLInfo"
    __table_args__ = {"extend_existing": True}

    # FIXED: Composite primary key (DollyNo + VinNo)
    DollyNo = db.Column(db.String(20), primary_key=True, nullable=False)
    VinNo = db.Column(db.String(50), primary_key=True, nullable=False)
    DollyOrderNo = db.Column(db.String(20), nullable=True)
    CustomerReferans = db.Column(db.String(50), nullable=False)
    Adet = db.Column(db.Integer, nullable=False, default=1)
    EOLName = db.Column(db.String(50), nullable=False)
    EOLID = db.Column(db.String(20), nullable=False)
    EOLDATE = db.Column(db.Date, nullable=True, default=date.today)
    EOLDollyBarcode = db.Column(db.String(100), nullable=True)
    RECEIPTID = db.Column(db.Integer, nullable=True)
    InsertedAt = db.Column(db.DateTime, nullable=True)

    def __repr__(self) -> str:
        return f"<DollyEOLInfo DollyNo={self.DollyNo} VinNo={self.VinNo}>"
