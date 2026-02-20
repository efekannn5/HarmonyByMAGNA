from datetime import datetime

from ..extensions import db


class SeferDollyEOL(db.Model):
    """Represents shipment records created after gruplar terminale aktarıldığında."""

    __tablename__ = "SeferDollyEOL"
    __table_args__ = {"extend_existing": True}

    # Tablo fiziksel olarak PK içermiyor; ORM için kombinasyon belirleniyor.
    SeferNumarasi = db.Column(db.String(20), primary_key=True, nullable=True)
    DollyNo = db.Column(db.String(20), primary_key=True, nullable=True)
    VinNo = db.Column(db.String(50), primary_key=True, nullable=True)
    PlakaNo = db.Column(db.String(20), nullable=True)
    CustomerReferans = db.Column(db.String(50), nullable=True)
    Adet = db.Column(db.Integer, nullable=True)
    EOLName = db.Column(db.String(50), nullable=True)
    EOLID = db.Column(db.String(20), nullable=True)
    EOLDate = db.Column(db.DateTime, nullable=True)
    TerminalUser = db.Column(db.String(100), nullable=True)
    TerminalDate = db.Column(db.DateTime, nullable=True)
    VeriGirisUser = db.Column(db.String(100), nullable=True)
    ASNDate = db.Column(db.DateTime, nullable=True)
    IrsaliyeDate = db.Column(db.DateTime, nullable=True)
    PartNumber = db.Column(db.String(50), nullable=True)

    DollyOrderNo = db.Column(db.String(50), nullable=True)

    def __repr__(self) -> str:
        return f"<SeferDollyEOL Sefer={self.SeferNumarasi} Dolly={self.DollyNo}>"
