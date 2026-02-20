from __future__ import annotations

import json
from typing import Optional

from ..extensions import db
from ..models import DollyLifecycle, DollyEOLInfo


class LifecycleService:
    class Status:
        EOL_READY = "EOL_READY"
        SCAN_CAPTURED = "SCAN_CAPTURED"
        WAITING_SUBMIT = "WAITING_SUBMIT"  # DEPRECATED - kept for backward compatibility
        SUBMITTED_TERMINAL = "SUBMITTED_TERMINAL"  # DEPRECATED
        WAITING_OPERATOR = "WAITING_OPERATOR"
        COMPLETED_ASN = "COMPLETED_ASN"
        COMPLETED_IRS = "COMPLETED_IRS"
        COMPLETED_BOTH = "COMPLETED_BOTH"
        
        # New workflow statuses
        LOADING_IN_PROGRESS = "LOADING_IN_PROGRESS"  # Forklift scanning dollys
        LOADING_COMPLETED = "LOADING_COMPLETED"      # Forklift finished, waiting for operator

    def ensure_received(self, record: DollyEOLInfo) -> None:
        if not record:
            return
        exists = (
            DollyLifecycle.query.filter_by(DollyNo=record.DollyNo, Status=self.Status.EOL_READY)
            .limit(1)
            .first()
        )
        if exists:
            return
        self.log_status(record.DollyNo, record.VinNo, self.Status.EOL_READY, source="EOL_FEED")

    def log_status(
        self,
        dolly_no: str,
        vin_no: str,
        status: str,
        source: str,
        metadata: Optional[dict] = None,
    ) -> None:
        payload = json.dumps(metadata, ensure_ascii=False) if metadata else None
        log = DollyLifecycle(
            DollyNo=dolly_no,
            VinNo=vin_no,
            Status=status,
            Source=source,
            Metadata=payload,
        )
        db.session.add(log)
        db.session.commit()

    def latest_status(self, dolly_no: str) -> Optional[str]:
        log = (
            DollyLifecycle.query.filter_by(DollyNo=dolly_no)
            .order_by(DollyLifecycle.CreatedAt.desc())
            .first()
        )
        return log.Status if log else None
