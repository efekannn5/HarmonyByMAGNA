"""
DollyQueueRemoved Model
Sıradan manuel olarak kaldırılan dolly'lerin arşivi
"""
from datetime import datetime, timedelta
from ..extensions import db


class DollyQueueRemoved(db.Model):
    __tablename__ = "DollyQueueRemoved"
    
    # Primary Key
    Id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    # DollyEOLInfo'dan kopyalanan alanlar
    DollyNo = db.Column(db.String(20), nullable=False)  # FIXED: DollyEOLInfo ile eşleşmeli
    VinNo = db.Column(db.String(50), nullable=False)
    CustomerReferans = db.Column(db.String(50), nullable=True)
    Adet = db.Column(db.Integer, nullable=True)
    EOLName = db.Column(db.String(50), nullable=True)
    EOLID = db.Column(db.String(20), nullable=True)
    EOLDATE = db.Column(db.Date, nullable=True)
    EOLDollyBarcode = db.Column(db.String(100), nullable=True)
    DollyOrderNo = db.Column(db.String(20), nullable=True)
    RECEIPTID = db.Column(db.Integer, nullable=True)
    OriginalInsertedAt = db.Column(db.DateTime, nullable=True)
    
    # Arşiv metadata
    RemovedAt = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    RemovedBy = db.Column(db.String(100), nullable=True)
    RemovalReason = db.Column(db.String(500), nullable=True)
    
    def __repr__(self):
        return f"<DollyQueueRemoved {self.DollyNo}/{self.VinNo}>"
    
    def to_dict(self):
        """JSON serialization için"""
        return {
            'id': self.Id,
            'dolly_no': self.DollyNo,
            'vin_no': self.VinNo,
            'customer_referans': self.CustomerReferans,
            'adet': self.Adet,
            'eol_name': self.EOLName,
            'eol_id': self.EOLID,
            'eol_date': self.EOLDATE.isoformat() if self.EOLDATE else None,
            'eol_dolly_barcode': self.EOLDollyBarcode,
            'dolly_order_no': self.DollyOrderNo,
            'receipt_id': self.RECEIPTID,
            'original_inserted_at': self.OriginalInsertedAt.isoformat() if self.OriginalInsertedAt else None,
            'removed_at': self.RemovedAt.isoformat() if self.RemovedAt else None,
            'removed_by': self.RemovedBy,
            'removal_reason': self.RemovalReason,
        }
    
    @classmethod
    def from_dolly_eol(cls, dolly_eol_record, removed_by=None, reason=None):
        """DollyEOLInfo kaydından yeni arşiv kaydı oluştur"""
        removed = cls(
            DollyNo=dolly_eol_record.DollyNo,
            VinNo=dolly_eol_record.VinNo,
            CustomerReferans=dolly_eol_record.CustomerReferans,
            Adet=dolly_eol_record.Adet,
            EOLName=dolly_eol_record.EOLName,
            EOLID=dolly_eol_record.EOLID,
            EOLDATE=dolly_eol_record.EOLDATE,
            EOLDollyBarcode=dolly_eol_record.EOLDollyBarcode,
            DollyOrderNo=dolly_eol_record.DollyOrderNo,
            RECEIPTID=dolly_eol_record.RECEIPTID,
            OriginalInsertedAt=dolly_eol_record.InsertedAt,
            RemovedBy=removed_by,
            RemovalReason=reason,
        )
        return removed
