"""
Operator edit helpers: manual dolly add/remove for web panel.

Responsibilities:
- Append manual dolly records to a web operator task without breaking queue order.
- Remove only the last dolly within a specific EOL group (stack-like per EOL).
- Preserve source truth in DollyEOLInfo; do not mutate it, only read.
"""

from datetime import datetime
from typing import Optional

from flask import current_app

from ..extensions import db
from ..models import DollyEOLInfo, DollySubmissionHold, WebOperatorTask
from ..services.audit_service import AuditService


def _audit():
    try:
        return AuditService()
    except Exception:
        return None


def _is_last_in_eol(part_number: str, dolly_no: str, eol_name: str) -> bool:
    """Check whether given dolly is the last one (latest CreatedAt) within the same EOL for the task."""
    last = (
        DollySubmissionHold.query.filter_by(PartNumber=part_number, EOLName=eol_name)
        .filter(DollySubmissionHold.Status != "removed")
        .order_by(DollySubmissionHold.CreatedAt.desc(), DollySubmissionHold.Id.desc())
        .first()
    )
    return last is not None and last.DollyNo == dolly_no


def add_manual_dolly(
    part_number: str,
    actor: str,
    *,
    dolly_no: str,
    vin_no: str,
    eol_name: str,
    eol_id: Optional[str],
    customer_ref: Optional[str],
    dolly_order_no: Optional[str],
    adet: int,
    terminal_dt: datetime,
    eol_dt: datetime,
    sefer_no: Optional[str],
    plaka_no: Optional[str],
    lokasyon: Optional[str],
) -> bool:
    """Append a manual dolly to task; always at tail order."""
    task = WebOperatorTask.query.filter_by(PartNumber=part_number).first()
    if not task:
        return False

    # Read DollyEOLInfo (non-destructive) for consistency; fall back to provided fields.
    eol_row = (
        DollyEOLInfo.query.filter_by(DollyNo=dolly_no, VinNo=vin_no).first()
    )

    hold = DollySubmissionHold(
        DollyNo=dolly_no,
        VinNo=vin_no,
        PartNumber=part_number,
        Status="pending",
        TerminalUser=actor,
        CustomerReferans=customer_ref or (eol_row.CustomerReferans if eol_row else None),
        EOLName=eol_name or (eol_row.EOLName if eol_row else None),
        EOLID=eol_id or (eol_row.EOLID if eol_row else None),
        Adet=adet or 1,
        DollyOrderNo=dolly_order_no or (eol_row.DollyOrderNo if eol_row else None),
        CreatedAt=terminal_dt,
        UpdatedAt=terminal_dt,
        SubmittedAt=None,
        LoadingCompletedAt=None,
        SeferNumarasi=sefer_no,
        PlakaNo=plaka_no,
        Payload=None,
        ScanOrder=None,
    )
    db.session.add(hold)

    # Update task counts
    task.TotalItems = (task.TotalItems or 0) + 1
    task.UpdatedAt = datetime.utcnow()

    db.session.commit()

    audit = _audit()
    if audit:
        audit.log(
            action="operator.manual_dolly_add",
            resource="task",
            resource_id=part_number,
            actor_name=actor,
            metadata={
                "dolly_no": dolly_no,
                "vin_no": vin_no,
                "eol_name": eol_name,
                "dolly_order_no": dolly_order_no,
                "terminal_dt": terminal_dt.isoformat(),
                "eol_dt": eol_dt.isoformat(),
            },
        )
    current_app.logger.info(
        f"➕ Manual dolly added: part={part_number}, dolly={dolly_no}, vin={vin_no}, eol={eol_name}"
    )
    return True


def remove_last_dolly_in_eol(part_number: str, dolly_no: str, eol_name: str, actor: str) -> bool:
    """
    Remove only if dolly is last within its EOL group.
    Steps:
    1. Mark DollySubmissionHold records as 'removed'
    2. Delete from DollyEOLInfo so it can be re-scanned (returns to queue)
    3. Update task counts
    """
    if not _is_last_in_eol(part_number, dolly_no, eol_name):
        return False

    targets = (
        DollySubmissionHold.query.filter_by(PartNumber=part_number, DollyNo=dolly_no)
        .filter(DollySubmissionHold.Status != "removed")
        .all()
    )
    if not targets:
        return False

    # Step 1: Mark holds as removed
    for hold in targets:
        hold.Status = "removed"
        hold.UpdatedAt = datetime.utcnow()

    # Step 2: Delete from DollyEOLInfo so it returns to scan queue
    # This allows the dolly to be re-scanned and re-added to tasks
    eol_records = DollyEOLInfo.query.filter_by(DollyNo=dolly_no).all()
    for eol_rec in eol_records:
        db.session.delete(eol_rec)
        current_app.logger.info(
            f"🔄 Deleted from DollyEOLInfo: DollyNo={eol_rec.DollyNo}, VinNo={eol_rec.VinNo}"
        )

    # Step 3: Recalculate task counts
    task = WebOperatorTask.query.filter_by(PartNumber=part_number).first()
    if task:
        remaining = (
            DollySubmissionHold.query.filter_by(PartNumber=part_number)
            .filter(DollySubmissionHold.Status != "removed")
            .count()
        )
        task.TotalItems = remaining
        task.UpdatedAt = datetime.utcnow()

    db.session.commit()

    audit = _audit()
    if audit:
        audit.log(
            action="operator.manual_dolly_remove",
            resource="task",
            resource_id=part_number,
            actor_name=actor,
            metadata={"dolly_no": dolly_no, "eol_name": eol_name, "returned_to_queue": True},
        )
    current_app.logger.info(
        f"➖ Manual dolly removed & returned to queue: part={part_number}, dolly={dolly_no}, eol={eol_name}"
    )
    return True
