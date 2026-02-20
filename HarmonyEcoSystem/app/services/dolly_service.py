from __future__ import annotations

import re
import json
from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Any, Dict, List, Optional, Tuple, Union

from flask import current_app
import re

from sqlalchemy import asc, desc, func, inspect as sa_inspect, text, case, or_

from ..extensions import db
from ..models import (
    DollyEOLInfo,
    DollyEOLInfoBackup,
    DollyGroup,
    DollyGroupEOL,
    DollySubmissionHold,
    DollyQueueRemoved,
    PWorkStation,
    SeferDollyEOL,
    WebOperatorTask,
)
from .audit_service import AuditService
from .realtime_service import RealtimeService
from .lifecycle_service import LifecycleService


@dataclass
class QueueEntry:
    dolly_no: str
    vin_no: str
    customer_ref: str
    eol_name: str
    eol_id: str
    eol_date: datetime | None = None
    adet: int = 1
    status: str = "waiting"
    metadata: Dict[str, str] = field(default_factory=dict)


@dataclass
class HoldEntry:
    id: int | None
    dolly_no: str
    vin_no: str
    status: str
    terminal_user: Optional[str] = None
    part_number: Optional[str] = None
    dolly_order_no: Optional[int] = None  # ÇOK ÖNEMLİ: CEVA'ya gönderilecek!
    scan_order: Optional[int] = None  # Okutma sırası (1, 2, 3...)
    scanned_at: Optional[datetime] = None
    submitted_at: Optional[datetime] = None
    payload: Dict[str, Any] = field(default_factory=dict)
    barcode: Optional[str] = None
    # DollyEOLInfo fields
    customer_referans: Optional[str] = None
    adet: Optional[int] = None
    eol_name: Optional[str] = None
    eol_id: Optional[str] = None
    eol_date: Optional[date] = None
    eol_dolly_barcode: Optional[str] = None
    vin_breakdown: List[Dict[str, Any]] = field(default_factory=list)


@dataclass 
class WebOperatorTaskEntry:
    id: int
    part_number: str
    status: str
    assigned_to: Optional[int]
    assigned_user_name: Optional[str]
    group_tag: str
    total_items: int
    processed_items: int
    progress_percentage: int
    can_submit_asn: bool
    can_submit_irsaliye: bool
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    hold_entries: List[HoldEntry] = field(default_factory=list)


@dataclass
class EOLStation:
    workstation_id: int
    name: str
    number: str
    spec_code: Optional[str] = None
    erp_code: Optional[str] = None
    shipping_tag: str = "both"


@dataclass
class GroupDefinition:
    group_id: int
    name: str
    description: Optional[str]
    eols: List[EOLStation] = field(default_factory=list)
    is_active: bool = True


@dataclass
class GroupSequence:
    definition: GroupDefinition
    queue: List[QueueEntry] = field(default_factory=list)


class DollyService:
    def __init__(self, config: Dict | None = None):
        self.config = config or {}
        features = self.config.get("features", {})
        self.use_mock_data = bool(features.get("enable_mock_data"))
        self.lifecycle = LifecycleService()
        self.audit = AuditService()
    
    def _get_production_date_from_backup(self, dolly_no: str) -> Optional[datetime]:
        """
        DollyEOLInfoBackup tablosundan üretim tarihini parametrik sorgu ile al.
        ⚠️ CRITICAL: Sadece parametrik sorgu kullan, sistem yavaşlar!
        """
        if not dolly_no:
            return None
        try:
            # Parametrik sorgu - sadece bu DollyNo için
            backup_record = DollyEOLInfoBackup.query.filter_by(DollyNo=dolly_no).first()
            if backup_record and backup_record.EOLDATE:
                return backup_record.EOLDATE
        except Exception as e:
            current_app.logger.warning(f"⚠️ Backup tablosundan üretim tarihi alınamadı (DollyNo={dolly_no}): {e}")
        return None
        
    def _extract_dolly_number(self, dolly_no: str) -> int:
        """Dolly numarasının sonundaki sayısal kısmı çıkar"""
        try:
            # Dolly numarasından son sayısal kısmı al (örn: "5170427" -> 5170427)
            match = re.search(r'(\d+)$', str(dolly_no))
            if match:
                return int(match.group(1))
            return 0
        except (ValueError, AttributeError):
            return 0
    
    def _dolly_sort_key(self, record):
        """DollyEOLInfo kayıtları için sıralama anahtarı"""
        dolly_num = self._extract_dolly_number(record.DollyNo)
        return (dolly_num, record.DollyNo)
    
    def _dolly_entry_sort_key(self, entry):
        """QueueEntry objeler için sıralama anahtarı"""
        dolly_num = self._extract_dolly_number(entry.dolly_no)
        return (dolly_num, entry.dolly_no)
        self._mock_queue_entries = self._build_mock_queue_entries() if self.use_mock_data else []
        self._mock_hold_entries = self._build_mock_hold_entries() if self.use_mock_data else []
        self._mock_group_definitions = self._build_mock_group_definitions() if self.use_mock_data else []
        self.lifecycle = LifecycleService()
        self.audit = AuditService()

    def list_group_sequences(self, limit: Optional[int] = None, queue_limit: Optional[int] = None) -> List[GroupSequence]:
        definitions = self.list_group_definitions()
        if limit:
            definitions = definitions[:limit]
        sequences: List[GroupSequence] = []
        for definition in definitions:
            queue = self._queue_for_definition(definition, limit=queue_limit)
            sequences.append(GroupSequence(definition=definition, queue=queue))
        return sequences

    def list_groups(self) -> List[QueueEntry]:
        """Legacy view to keep dashboard compatibility."""
        if self.use_mock_data:
            return self._mock_queue_entries
        # Dolly No bazlı sıralama - sonundaki rakama göre
        records = DollyEOLInfo.query.all()
        records = sorted(records, key=self._dolly_sort_key)
        entries: List[QueueEntry] = []
        for record in records:
            self.lifecycle.ensure_received(record)
            entries.append(self._to_queue_entry(record))
        return entries

    def group_by_vin(self, vin_no: str) -> Optional[QueueEntry]:
        for group in self.list_groups():
            if group.vin_no == vin_no:
                return group
        return None

    def acknowledge_group(self, dolly_no: str, terminal_user: str) -> bool:
        """Marks a dolly as processed and logs it to SeferDollyEOL."""
        group = None
        for candidate in self.list_groups():
            if candidate.dolly_no == dolly_no:
                group = candidate
                break
        if not group:
            return False

        if self.use_mock_data:
            group.status = "acknowledged"
            group.metadata["terminal_user"] = terminal_user
            group.metadata["terminal_date"] = datetime.utcnow().isoformat()
            return True
        # PartNumber'ı hold kaydından yakala (varsa)
        hold_record = (
            DollySubmissionHold.query.filter_by(DollyNo=group.dolly_no)
            .order_by(desc(DollySubmissionHold.CreatedAt))
            .first()
        )

        # Terminal/EOL zamanlarını gerçek tarama verisinden al; yalnızca yoksa now()
        terminal_dt = hold_record.LoadingCompletedAt or hold_record.CreatedAt or group.eol_date or datetime.utcnow()
        
        # 📅 Üretim tarihini backup tablosundan al
        production_date = self._get_production_date_from_backup(group.dolly_no)
        eol_dt = production_date or group.eol_date

        record = SeferDollyEOL(
            SeferNumarasi=None,
            PlakaNo=None,
            DollyNo=group.dolly_no,
            VinNo=group.vin_no,
            Lokasyon="GHZNA",
            CustomerReferans=group.customer_ref,
            Adet=group.adet,
            EOLName=group.eol_name,
            EOLID=group.eol_id,
            EOLDate=eol_dt,
            PartNumber=getattr(hold_record, "PartNumber", None),
            TerminalUser=terminal_user,
            TerminalDate=terminal_dt,
        )
        shipping_tag = self._shipping_tag_for_eol(group.eol_name)
        # ASN / İrsaliye tarihleri işlem anı olsun; ancak terminal/EOL tarihleri korunur
        now_ts = datetime.utcnow()
        if shipping_tag in {"asn", "both"}:
            record.ASNDate = now_ts
        if shipping_tag in {"irsaliye", "both"}:
            record.IrsaliyeDate = now_ts
        db.session.add(record)
        db.session.commit()

        final_status = self._final_status_for_tag(shipping_tag)
        self.lifecycle.log_status(
            group.dolly_no,
            group.vin_no,
            final_status,
            source="OPERATOR",
            metadata={"terminalUser": terminal_user, "shippingTag": shipping_tag},
        )
        hold_record = (
            DollySubmissionHold.query.filter_by(DollyNo=group.dolly_no)
            .order_by(desc(DollySubmissionHold.CreatedAt))
            .first()
        )
        if hold_record:
            hold_record.Status = "completed"
            hold_record.UpdatedAt = datetime.utcnow()
            db.session.commit()
        self.audit.log(
            action="dolly.completed",
            resource="dolly",
            resource_id=group.dolly_no,
            actor_name=terminal_user or "operator",
            metadata={"vin": group.vin_no, "shippingTag": shipping_tag},
        )
        return True

    def list_group_definitions(self) -> List[GroupDefinition]:
        if self.use_mock_data:
            return self._mock_group_definitions
        if self._dolly_group_tables_available():
            definitions = self._fetch_dolly_group_definitions()
            if definitions:
                return definitions
        return self._build_groups_from_pworkstations()

    def list_eol_candidates(self) -> List[EOLStation]:
        pw_config = self.config.get("pworkstation") or {}
        suffix = pw_config.get("name_suffix", "EOL")
        require_finish = pw_config.get("require_finish_product_station", False)
        if not self._table_exists("PWorkStation"):
            return []
        query = PWorkStation.query
        if require_finish:
            query = query.filter_by(IsFinishProductStation=True)
        if suffix:
            pattern = f"%{suffix}"
            query = query.filter(PWorkStation.PWorkStationName.ilike(pattern))
        rows = query.order_by(PWorkStation.PWorkStationName.asc()).all()
        return [
            EOLStation(
                workstation_id=row.Id,
                name=row.PWorkStationName,
                number=row.PWorkStationNo,
                spec_code=row.SpecCode1,
                erp_code=row.ErpWorkStationNo,
            )
            for row in rows
        ]

    def list_hold_entries(self, status: Optional[str] = None) -> List[HoldEntry]:
        if self.use_mock_data:
            if status:
                return [entry for entry in self._mock_hold_entries if entry.status == status]
            return self._mock_hold_entries

        query = DollySubmissionHold.query
        if status:
            query = query.filter_by(Status=status)
        records = query.order_by(desc(DollySubmissionHold.CreatedAt)).all()
        return [self._to_hold_entry(record) for record in records]

    def enqueue_hold_entry(
        self,
        dolly_no: str,
        vin_no: str,
        terminal_user: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None,
    ) -> HoldEntry:
        payload = payload or {}
        barcode = payload.get("barcode")
        dolly_record = None
        if not self.use_mock_data:
            dolly_record = DollyEOLInfo.query.filter_by(DollyNo=dolly_no).first()
            if not dolly_record:
                raise ValueError("Dolly kaydı bulunamadı.")
            if not vin_no:
                vin_no = dolly_record.VinNo
            expected_barcode = dolly_record.EOLDollyBarcode
            if barcode and expected_barcode and barcode != expected_barcode:
                raise ValueError("Barkod eşleşmedi.")
        if self.use_mock_data:
            entry = HoldEntry(
                id=len(self._mock_hold_entries) + 1,
                dolly_no=dolly_no,
                vin_no=vin_no,
                status="scan_captured",
                terminal_user=terminal_user,
                scanned_at=datetime.utcnow(),
                payload=payload,
            )
            self._mock_hold_entries.append(entry)
            return entry

        record = DollySubmissionHold(
            DollyNo=dolly_no,
            VinNo=vin_no,
            Status="scan_captured",
            TerminalUser=terminal_user,
            Payload=json.dumps(payload),
        )
        db.session.add(record)
        db.session.flush()  # Get the ID
        
        # Generate part number for first scan of the day or use existing one
        part_number = self._get_or_create_part_number_for_dolly(dolly_no, dolly_record)
        record.PartNumber = part_number
        
        db.session.commit()
        self.lifecycle.log_status(
            dolly_no,
            vin_no,
            LifecycleService.Status.SCAN_CAPTURED,
            source="SCAN",
            metadata={"terminalUser": terminal_user, "barcode": barcode},
        )
        self.lifecycle.log_status(
            dolly_no,
            vin_no,
            LifecycleService.Status.WAITING_SUBMIT,
            source="SCAN",
        )
        self.audit.log(
            action="dolly.scan_captured",
            resource="dolly",
            resource_id=dolly_no,
            actor_name=terminal_user or "terminal",
            metadata={"vin": vin_no, "barcode": barcode},
        )
        return self._to_hold_entry(record)

    def create_group(
        self,
        name: str,
        description: Optional[str],
        eol_entries: List[Dict[str, Any]],
        actor_name: Optional[str] = None,
    ) -> GroupDefinition:
        """Create a new group with EOL associations"""
        if self.use_mock_data:
            new_id = len(self._mock_group_definitions) + 1
            selected_ids = [entry["id"] for entry in eol_entries]
            eols = [
                station
                for station in self.list_eol_candidates()
                if station.workstation_id in selected_ids
            ]
            for station in eols:
                tag = next((entry.get("tag", "both") for entry in eol_entries if entry["id"] == station.workstation_id), "both")
                station.shipping_tag = tag
            definition = GroupDefinition(group_id=new_id, name=name, description=description, eols=eols)
            self._mock_group_definitions.append(definition)
            return definition

        if not self._dolly_group_tables_available():
            raise RuntimeError("DollyGroup tabloları mevcut değil.")

        # Validate inputs
        if not name or not name.strip():
            raise ValueError("Grup adı boş olamaz")
        
        if not eol_entries or len(eol_entries) == 0:
            raise ValueError("En az bir EOL seçmelisiniz")

        # Check if group name already exists
        existing = DollyGroup.query.filter_by(GroupName=name.strip()).first()
        if existing:
            raise ValueError(f"'{name}' adında bir grup zaten mevcut")

        ids = [entry["id"] for entry in eol_entries]
        eol_rows = PWorkStation.query.filter(PWorkStation.Id.in_(ids)).all()
        if not eol_rows:
            raise ValueError("Seçilen EOL istasyonları bulunamadı.")
        
        if len(eol_rows) != len(ids):
            raise ValueError("Bazı EOL istasyonları bulunamadı")
            
        row_map = {row.Id: row for row in eol_rows}

        try:
            group = DollyGroup(GroupName=name.strip(), Description=description, IsActive=True)
            db.session.add(group)
            db.session.flush()
            
            enriched_rows = []
            for entry in eol_entries:
                row = row_map.get(entry["id"])
                if row:
                    tag = entry.get("tag", "both").lower()
                    enriched_rows.append((row, tag))
            
            self._update_group_eols(group.Id, enriched_rows)
            db.session.commit()
            
            definition = self.list_group_definition_by_id(group.Id)
            self.audit.log(
                action="group.create",
                resource="group",
                resource_id=str(group.Id),
                actor_name=actor_name or "system",
                metadata={"name": name, "eols": eol_entries},
            )
            return definition
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Grup oluşturma hatası: {e}")
            raise

    def update_group(
        self,
        group_id: int,
        name: Optional[str],
        description: Optional[str],
        eol_entries: List[Dict[str, Any]],
        actor_name: Optional[str] = None,
    ) -> Optional[GroupDefinition]:
        """Update an existing group"""
        if self.use_mock_data:
            for definition in self._mock_group_definitions:
                if definition.group_id == group_id:
                    if name:
                        definition.name = name
                    if description is not None:
                        definition.description = description
                    selected_ids = [entry["id"] for entry in eol_entries]
                    definition.eols = [
                        station
                        for station in self.list_eol_candidates()
                        if station.workstation_id in selected_ids
                    ]
                    for station in definition.eols:
                        tag = next((entry.get("tag", "both") for entry in eol_entries if entry["id"] == station.workstation_id), "both")
                        station.shipping_tag = tag
                    return definition
            return None

        if not self._dolly_group_tables_available():
            return None

        group = DollyGroup.query.get(group_id)
        if not group:
            return None
        
        # Validate inputs
        if name and not name.strip():
            raise ValueError("Grup adı boş olamaz")
        
        if not eol_entries or len(eol_entries) == 0:
            raise ValueError("En az bir EOL seçmelisiniz")
        
        # Check if name already exists (except current group)
        if name and name.strip() != group.GroupName:
            existing = DollyGroup.query.filter_by(GroupName=name.strip()).first()
            if existing and existing.Id != group_id:
                raise ValueError(f"'{name}' adında bir grup zaten mevcut")
        
        try:
            if name:
                group.GroupName = name.strip()
            if description is not None:
                group.Description = description
            group.UpdatedAt = datetime.utcnow()
            
            ids = [entry["id"] for entry in eol_entries]
            eol_rows = PWorkStation.query.filter(PWorkStation.Id.in_(ids)).all()
            if not eol_rows:
                raise ValueError("Seçilen EOL istasyonları bulunamadı.")
            
            if len(eol_rows) != len(ids):
                raise ValueError("Bazı EOL istasyonları bulunamadı")
                
            row_map = {row.Id: row for row in eol_rows}
            enriched_rows = []
            for entry in eol_entries:
                row = row_map.get(entry["id"])
                if row:
                    tag = entry.get("tag", "both").lower()
                    enriched_rows.append((row, tag))
            
            self._update_group_eols(group_id, enriched_rows)
            db.session.commit()
            
            definition = self.list_group_definition_by_id(group_id)
            self.audit.log(
                action="group.update",
                resource="group",
                resource_id=str(group_id),
                actor_name=actor_name or "system",
                metadata={"name": name, "eols": eol_entries},
            )
            return definition
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Grup güncelleme hatası: {e}")
            raise

    def delete_group(self, group_id: int, actor_name: Optional[str] = None) -> bool:
        """Delete a group and its EOL associations"""
        if self.use_mock_data:
            for idx, definition in enumerate(self._mock_group_definitions):
                if definition.group_id == group_id:
                    self._mock_group_definitions.pop(idx)
                    return True
            return False

        if not self._dolly_group_tables_available():
            return False

        try:
            group = DollyGroup.query.get(group_id)
            if not group:
                return False

            group_name = group.GroupName
            
            # Delete all EOL associations first
            deleted_count = DollyGroupEOL.query.filter_by(GroupId=group_id).delete()
            current_app.logger.info(f"Deleted {deleted_count} EOL associations for group {group_id}")
            
            # Delete the group
            db.session.delete(group)
            db.session.commit()

            self.audit.log(
                action="group.delete",
                resource="group",
                resource_id=str(group_id),
                actor_name=actor_name or "system",
                metadata={"group_name": group_name},
            )
            return True
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Grup silme hatası: {e}")
            raise

    def submit_hold_entry(self, dolly_no: str, terminal_user: Optional[str] = None) -> Optional[HoldEntry]:
        """Submit hold entry with new algorithm - creates part number and transfers to web operator"""
        if self.use_mock_data:
            for entry in self._mock_hold_entries:
                if entry.dolly_no == dolly_no and entry.status == "scan_captured":
                    entry.status = "waiting_operator"
                    entry.submitted_at = datetime.utcnow()
                    entry.terminal_user = terminal_user or entry.terminal_user
                    self.acknowledge_group(dolly_no, entry.terminal_user or "terminal")
                    entry.status = "completed"
                    return entry
            return None

        record = (
            DollySubmissionHold.query.filter_by(DollyNo=dolly_no)
            .order_by(desc(DollySubmissionHold.CreatedAt))
            .first()
        )
        if not record:
            return None

        # NEW ALGORITHM: Get dolly and group information
        dolly_info = DollyEOLInfo.query.filter_by(DollyNo=dolly_no).first()
        if not dolly_info:
            current_app.logger.warning(f"DollyEOLInfo not found for {dolly_no}")
            return None
            
        # Get group information for shipping tag (handle legacy column naming)
        eol_identifier = getattr(dolly_info, "EOLId", None)
        if eol_identifier is None:
            eol_identifier = getattr(dolly_info, "EOLID", None)

        group_info = self._get_dolly_group_info(eol_identifier)
        
        # Generate or get existing part number for this group
        part_number = self._get_or_create_group_part_number(group_info, terminal_user)
        
        # Update hold entry with part number and new status
        record.Status = "waiting_operator"
        record.PartNumber = part_number
        if terminal_user:
            record.TerminalUser = terminal_user
        record.SubmittedAt = datetime.utcnow()
        record.UpdatedAt = datetime.utcnow()
        
        # Update or create web operator task
        self._update_web_operator_task_for_part(part_number, group_info)
        
        db.session.commit()
        
        # Update web operator task if this dolly has part number
        if record.PartNumber:
            task = WebOperatorTask.query.filter_by(PartNumber=record.PartNumber).first()
            if task and task.Status == "pending":
                # Update total items count for this task
                total_items = DollySubmissionHold.query.filter_by(
                    PartNumber=record.PartNumber
                ).filter(DollySubmissionHold.Status != "removed").count()
                task.TotalItems = total_items
                task.UpdatedAt = datetime.utcnow()
                db.session.commit()
        
        latest = DollyEOLInfo.query.filter_by(DollyNo=dolly_no).first()
        vin = latest.VinNo if latest else record.VinNo
        self.lifecycle.log_status(
            dolly_no,
            vin,
            LifecycleService.Status.SUBMITTED_TERMINAL,
            source="TERMINAL",
            metadata={"terminalUser": terminal_user},
        )
        self.lifecycle.log_status(
            dolly_no,
            vin,
            LifecycleService.Status.WAITING_OPERATOR,
            source="TERMINAL",
        )
        self.audit.log(
            action="dolly.waiting_operator",
            resource="dolly",
            resource_id=dolly_no,
            actor_name=terminal_user or "terminal",
            metadata={"vin": vin},
        )
        return self._to_hold_entry(record)

    def list_group_definition_by_id(self, group_id: int) -> Optional[GroupDefinition]:
        if self.use_mock_data:
            for definition in self._mock_group_definitions:
                if definition.group_id == group_id:
                    return definition
            return None
        if self._dolly_group_tables_available():
            records = (
                db.session.query(DollyGroup, DollyGroupEOL, PWorkStation)
                .outerjoin(DollyGroupEOL, DollyGroup.Id == DollyGroupEOL.GroupId)
                .outerjoin(PWorkStation, DollyGroupEOL.PWorkStationId == PWorkStation.Id)
                .filter(DollyGroup.Id == group_id)
                .all()
            )
            if not records:
                return None
            group_def = GroupDefinition(
                group_id=records[0][0].Id,
                name=records[0][0].GroupName,
                description=records[0][0].Description,
                is_active=bool(records[0][0].IsActive),
                eols=[],
            )
            for _, link, workstation in records:
                if workstation:
                    group_def.eols.append(
                        EOLStation(
                            workstation_id=workstation.Id,
                            name=workstation.PWorkStationName,
                            number=workstation.PWorkStationNo,
                            spec_code=workstation.SpecCode1,
                            erp_code=workstation.ErpWorkStationNo,
                            shipping_tag=getattr(link, "ShippingTag", "both"),
                        )
                    )
            return group_def
        # fallback definitions are generated from PWorkStation; ensure id matches
        for definition in self._build_groups_from_pworkstations():
            if definition.group_id == group_id:
                return definition
        return None

    def _queue_for_definition(self, definition: GroupDefinition, limit: Optional[int] = None) -> List[QueueEntry]:
        if self.use_mock_data:
            return self._mock_queue_entries
        if not definition.eols:
            return []
        eol_names = [station.name for station in definition.eols]
        query = (
            DollyEOLInfo.query.filter(DollyEOLInfo.EOLName.in_(eol_names))
            .order_by(DollyEOLInfo.DollyNo)
        )
        if limit:
            query = query.limit(limit)
        rows = query.all()
        entries: List[QueueEntry] = []
        for row in rows:
            entry = self._to_queue_entry(row)
            entry.metadata["shippingTag"] = self._shipping_tag_for_eol(row.EOLName)
            entries.append(entry)
        return entries

    def _fetch_dolly_group_definitions(self) -> List[GroupDefinition]:
        records = (
            db.session.query(DollyGroup, DollyGroupEOL, PWorkStation)
            .outerjoin(DollyGroupEOL, DollyGroup.Id == DollyGroupEOL.GroupId)
            .outerjoin(PWorkStation, DollyGroupEOL.PWorkStationId == PWorkStation.Id)
            .order_by(DollyGroup.GroupName.asc(), PWorkStation.PWorkStationName.asc())
            .all()
        )
        definitions: Dict[int, GroupDefinition] = {}
        for group, link, workstation in records:
            if group.Id not in definitions:
                definitions[group.Id] = GroupDefinition(
                    group_id=group.Id,
                    name=group.GroupName,
                    description=group.Description,
                    is_active=bool(group.IsActive),
                    eols=[],
                )
            if workstation:
                definitions[group.Id].eols.append(
                    EOLStation(
                        workstation_id=workstation.Id,
                        name=workstation.PWorkStationName,
                        number=workstation.PWorkStationNo,
                        spec_code=workstation.SpecCode1,
                        erp_code=workstation.ErpWorkStationNo,
                        shipping_tag=getattr(link, "ShippingTag", "both"),
                    )
                )
        return list(definitions.values())

    def _build_groups_from_pworkstations(self) -> List[GroupDefinition]:
        stations = self.list_eol_candidates()
        definitions: List[GroupDefinition] = []
        for station in stations:
            definitions.append(
                GroupDefinition(
                    group_id=station.workstation_id,
                    name=station.name,
                    description=f"PWorkStationNo: {station.number}",
                    eols=[EOLStation(
                        workstation_id=station.workstation_id,
                        name=station.name,
                        number=station.number,
                        spec_code=station.spec_code,
                        erp_code=station.erp_code,
                        shipping_tag="both",
                    )],
                )
            )
        return definitions

    def _update_group_eols(self, group_id: int, eol_rows: List[Tuple[PWorkStation, str]]) -> None:
        """Update group EOL associations with proper cleanup"""
        # Önce mevcut ilişkileri sil
        DollyGroupEOL.query.filter_by(GroupId=group_id).delete()
        db.session.flush()  # Silme işlemini hemen uygula
        
        # Yeni ilişkileri ekle
        for row, tag in eol_rows:
            # Tag değerini validate et
            valid_tag = tag.lower() if tag in ['asn', 'irsaliye', 'both'] else 'both'
            record = DollyGroupEOL(
                GroupId=group_id, 
                PWorkStationId=row.Id, 
                ShippingTag=valid_tag
            )
            db.session.add(record)
        db.session.flush()  # Ekleme işlemini hemen uygula

    def _dolly_group_tables_available(self) -> bool:
        return self._table_exists("DollyGroup") and self._table_exists("DollyGroupEOL")

    def _to_queue_entry(self, record: DollyEOLInfo) -> QueueEntry:
        status = self.lifecycle.latest_status(record.DollyNo) or "waiting"
        metadata: Dict[str, str] = {}
        if record.EOLDollyBarcode:
            metadata["barcode"] = record.EOLDollyBarcode
            
        return QueueEntry(
            dolly_no=record.DollyNo,
            vin_no=record.VinNo,
            customer_ref=record.CustomerReferans,
            eol_name=record.EOLName,
            eol_id=record.EOLID,
            eol_date=record.EOLDATE,
            adet=record.Adet,
            status=status,
            metadata=metadata,
        )

    def _to_hold_entry(self, record: DollySubmissionHold) -> HoldEntry:
        payload: Dict[str, Any] = {}
        if record.Payload:
            try:
                payload = json.loads(record.Payload)
            except json.JSONDecodeError:
                payload = {"raw": record.Payload}
        barcode = payload.get("barcode") if isinstance(payload, dict) else None
        
        # Get DollyEOLInfo data for this dolly
        dolly_info = db.session.query(DollyEOLInfo).filter_by(DollyNo=record.DollyNo).first()
        
        return HoldEntry(
            id=record.Id,
            dolly_no=record.DollyNo,
            vin_no=record.VinNo,
            status=record.Status,
            terminal_user=record.TerminalUser,
            dolly_order_no=record.DollyOrderNo,  # ÇOK ÖNEMLİ: CEVA'ya gönderilecek!
            scan_order=record.ScanOrder,  # Okutma sırası
            scanned_at=record.CreatedAt,
            submitted_at=record.SubmittedAt,
            payload=payload,
            barcode=barcode,
            # DollyEOLInfo fields
            customer_referans=dolly_info.CustomerReferans if dolly_info else None,
            adet=dolly_info.Adet if dolly_info else None,
            eol_name=dolly_info.EOLName if dolly_info else None,
            eol_id=dolly_info.EOLID if dolly_info else None,
            eol_date=dolly_info.EOLDATE if dolly_info else None,
            eol_dolly_barcode=dolly_info.EOLDollyBarcode if dolly_info else None
        )

    def _shipping_tag_for_eol(self, eol_name: str) -> str:
        definitions = self.list_group_definitions()
        for definition in definitions:
            for eol in definition.eols:
                if eol.name == eol_name:
                    return eol.shipping_tag or "both"
        return "both"

    def _final_status_for_tag(self, tag: str) -> str:
        tag = (tag or "both").lower()
        if tag == "asn":
            return LifecycleService.Status.COMPLETED_ASN
        if tag == "irsaliye":
            return LifecycleService.Status.COMPLETED_IRS
        return LifecycleService.Status.COMPLETED_BOTH

    def lookup_dolly_by_barcode(self, barcode: str) -> Optional[QueueEntry]:
        if self.use_mock_data:
            for entry in self._mock_queue_entries:
                if entry.metadata.get("barcode") == barcode:
                    return entry
            return None
        if not barcode:
            return None
        record = DollyEOLInfo.query.filter_by(EOLDollyBarcode=barcode).first()
        if not record:
            return None
        self.lifecycle.ensure_received(record)
        vins = self._split_vin_numbers(record.VinNo) or [record.VinNo or record.DollyNo]
        entry = self._to_queue_entry(record)
        entry.vin_no = vins[0]
        entry.metadata["vin_options"] = ",".join(vins)
        return entry

    def _build_mock_queue_entries(self) -> List[QueueEntry]:
        return [
            _mock_entry("DL-1001", "3FA6P0LU6FR100001", "EOL-A1", 2),
            _mock_entry("DL-1002", "3FA6P0LU6FR100002", "EOL-A2", 1),
        ]

    def _build_mock_hold_entries(self) -> List[HoldEntry]:
        return [
            HoldEntry(
                id=1,
                dolly_no="DL-1001",
                vin_no="3FA6P0LU6FR100001",
                status="holding",
                scanned_at=datetime.utcnow(),
                payload={"note": "Mock entry"},
            )
        ]

    def _build_mock_group_definitions(self) -> List[GroupDefinition]:
        stations = [
            EOLStation(workstation_id=1, name="EOL-A1", number="WS-01"),
            EOLStation(workstation_id=2, name="EOL-A2", number="WS-02"),
        ]
        return [
            GroupDefinition(group_id=station.workstation_id, name=station.name, description=None, eols=[station])
            for station in stations
        ]

    def _split_vin_numbers(self, vin_value: Optional[str]) -> List[str]:
        if not vin_value:
            return []
        normalized = vin_value.replace("\r", "\n")
        parts = re.split(r"[\s,;|]+", normalized.strip())
        vins = []
        for part in parts:
            cleaned = part.strip().upper()
            if cleaned:
                vins.append(cleaned)
        return vins

    def _generate_part_number(self) -> str:
        """Generate unique part number for web operator tasks."""
        today = datetime.utcnow().strftime("%Y%m%d")
        
        # Get highest counter for today
        existing = db.session.execute(
            db.text("""
                SELECT ISNULL(MAX(CAST(RIGHT(PartNumber, 4) AS INT)), 0) + 1 as NextCounter
                FROM DollySubmissionHold
                WHERE PartNumber LIKE 'PT' + :date + '%'
            """),
            {"date": today}
        ).fetchone()
        
        counter = existing[0] if existing else 1
        return f"PT{today}{counter:04d}"
    
    def _get_eol_shipping_tags(self) -> Dict[str, str]:
        """Get shipping tags for all EOLs from DollyGroupEOL.
        
        Returns:
            Dict mapping EOL name to shipping tag (asn, irsaliye, or both)
        """
        try:
            if not self._dolly_group_tables_available():
                return {}
            
            results = db.session.query(
                PWorkStation.PWorkStationName,
                DollyGroupEOL.ShippingTag
            ).join(
                DollyGroupEOL, PWorkStation.Id == DollyGroupEOL.PWorkStationId
            ).all()
            
            return {row[0]: row[1] for row in results}
        except Exception as e:
            current_app.logger.error(f"Error getting EOL shipping tags: {e}")
            return {}

    def create_web_operator_task(self, part_number: str, group_tag: str = "both") -> WebOperatorTaskEntry:
        """Create a new web operator task."""
        task = WebOperatorTask(
            PartNumber=part_number,
            Status="pending",
            GroupTag=group_tag,
            TotalItems=0,
            ProcessedItems=0
        )
        db.session.add(task)
        db.session.commit()
        
        self.audit.log(
            action="web_operator_task.created",
            resource="task",
            resource_id=part_number,
            actor_name="system",
            metadata={"group_tag": group_tag}
        )
        
        return self._to_web_operator_task_entry(task)

    def list_web_operator_tasks(self, status: Optional[str] = None) -> List[WebOperatorTaskEntry]:
        """List web operator tasks with optional status filter."""
        query = WebOperatorTask.query
        if status:
            query = query.filter_by(Status=status)
        
        tasks = query.order_by(desc(WebOperatorTask.CreatedAt)).all()
        entries = []
        
        for task in tasks:
            task_entry = self._to_web_operator_task_entry(task)
            # Load hold entries for this task
            hold_entries = self.list_hold_entries_by_part_number(task.PartNumber)
            task_entry.hold_entries = hold_entries
            entries.append(task_entry)
            
        return entries

    def get_web_operator_task(self, part_number: str) -> Optional[WebOperatorTaskEntry]:
        """Get specific web operator task with its hold entries."""
        task = WebOperatorTask.query.filter_by(PartNumber=part_number).first()
        if not task:
            return None
            
        task_entry = self._to_web_operator_task_entry(task)
        task_entry.hold_entries = self.list_hold_entries_by_part_number(part_number)
        return task_entry

    def list_hold_entries_by_part_number(self, part_number: str) -> List[HoldEntry]:
        """Get all hold entries for a specific part number, grouped by dolly number."""
        holds = DollySubmissionHold.query.filter_by(PartNumber=part_number).order_by(
            DollySubmissionHold.DollyNo.asc(),
            desc(DollySubmissionHold.CreatedAt)
        ).all()
        return [self._to_hold_entry(hold) for hold in holds]

    @staticmethod
    def _normalize_identifier(value: Optional[str]) -> str:
        if not value:
            return ""
        return re.sub(r"[\s\-]", "", value).upper()

    def _fetch_dolly_vins(
        self,
        dolly_no: Optional[str],
        vin_hint: Optional[str] = None,
        fallback_customer: Optional[str] = None,
    ) -> List[DollyEOLInfo]:
        """Fetch all VIN rows for a dolly using robust matching."""
        trimmed = (dolly_no or "").strip()
        normalized = self._normalize_identifier(trimmed)
        records: List[DollyEOLInfo] = []

        if normalized:
            normalized_column = func.upper(
                func.replace(func.replace(DollyEOLInfo.DollyNo, " ", ""), "-", "")
            )
            records = (
                db.session.query(DollyEOLInfo)
                .filter(
                    (DollyEOLInfo.DollyNo == trimmed)
                    | (normalized_column == normalized),
                    DollyEOLInfo.VinNo.isnot(None)
                )
                .order_by(DollyEOLInfo.VinNo.asc())
                .all()
            )

        # FIXED: Only use fallback methods if NO records found with dolly_no
        # If we found records with dolly_no match, return them even if only 1
        if len(records) == 0 and vin_hint:
            prefix = vin_hint[: max(6, len(vin_hint) - 2)]
            if prefix:
                query = db.session.query(DollyEOLInfo).filter(DollyEOLInfo.VinNo.like(f"{prefix}%"))
                if fallback_customer:
                    query = query.filter(DollyEOLInfo.CustomerReferans == (fallback_customer or "").strip())
                records = query.order_by(DollyEOLInfo.VinNo.asc()).all()

        if len(records) == 0 and fallback_customer:
            records = (
                db.session.query(DollyEOLInfo)
                .filter(
                    DollyEOLInfo.CustomerReferans == (fallback_customer or "").strip()
                )
                .order_by(DollyEOLInfo.VinNo.asc())
                .all()
            )

        return records

    def assign_part_number_to_submission(self, dolly_no: str, part_number: str) -> bool:
        """Assign part number to submission hold entry."""
        hold = DollySubmissionHold.query.filter_by(DollyNo=dolly_no).order_by(
            desc(DollySubmissionHold.CreatedAt)
        ).first()
        
        if not hold:
            return False
            
        hold.PartNumber = part_number
        hold.UpdatedAt = datetime.utcnow()
        db.session.commit()
        
        # Update task total items
        task = WebOperatorTask.query.filter_by(PartNumber=part_number).first()
        if task:
            task.TotalItems = DollySubmissionHold.query.filter_by(PartNumber=part_number).count()
            task.UpdatedAt = datetime.utcnow()
            db.session.commit()
        
        self.audit.log(
            action="part_number.assigned",
            resource="dolly",
            resource_id=dolly_no,
            actor_name="system",
            metadata={"part_number": part_number}
        )
        
        return True

    def update_web_operator_task_status(self, part_number: str, status: str, user_id: Optional[int] = None) -> bool:
        """Update web operator task status."""
        task = WebOperatorTask.query.filter_by(PartNumber=part_number).first()
        if not task:
            return False
            
        task.Status = status
        task.UpdatedAt = datetime.utcnow()
        
        if user_id:
            task.AssignedTo = user_id
            
        if status == "completed":
            task.CompletedAt = datetime.utcnow()
            
        db.session.commit()
        return True

    def add_dolly_to_task(
        self,
        part_number: str,
        dolly_no: str,
        vin_no: str,
        terminal_user: str,
        sefer_no: Optional[str] = None,
        plaka_no: Optional[str] = None,
        lokasyon: Optional[str] = None,
    ) -> Optional[HoldEntry]:
        """Add a new dolly to an existing web operator task."""
        # Check if task exists
        task = WebOperatorTask.query.filter_by(PartNumber=part_number).first()
        if not task:
            return None
        
        # FIXED: Get all VINs for this dolly from DollyEOLInfo
        dolly_vins = self._fetch_dolly_vins(dolly_no, vin_hint=vin_no)
        
        if not dolly_vins:
            # If no records found, add with provided VIN only
            current_app.logger.warning(f"No DollyEOLInfo found for {dolly_no}, adding single VIN")
            dolly_vins = []
            
        # Create payload
        payload = {
            "manual_addition": True,
            "sefer_no": sefer_no,
            "plaka_no": plaka_no,
            "lokasyon": lokasyon or "GHZNA",
        }
        
        added_count = 0
        last_hold = None
        
        if dolly_vins:
            # Add one hold entry for each VIN in the dolly
            for dolly_info in dolly_vins:
                hold = DollySubmissionHold(
                    DollyNo=dolly_no,
                    VinNo=dolly_info.VinNo,
                    Status="submitted",
                    TerminalUser=terminal_user,
                    PartNumber=part_number,
                    SubmittedAt=datetime.utcnow(),
                    Payload=json.dumps(payload),
                )
                db.session.add(hold)
                last_hold = hold
                added_count += 1
        else:
            # Fallback: Add only the provided VIN
            hold = DollySubmissionHold(
                DollyNo=dolly_no,
                VinNo=vin_no,
                Status="submitted",
                TerminalUser=terminal_user,
                PartNumber=part_number,
                SubmittedAt=datetime.utcnow(),
                Payload=json.dumps(payload),
            )
            db.session.add(hold)
            last_hold = hold
            added_count = 1
        
        # Update task counts
        task.TotalItems += added_count
        task.UpdatedAt = datetime.utcnow()
        db.session.commit()
        
        self.audit.log(
            action="dolly.added_to_task",
            resource="dolly",
            resource_id=dolly_no,
            actor_name=terminal_user,
            metadata={
                "part_number": part_number, 
                "vin_count": added_count,
                "primary_vin": vin_no
            }
        )
        
        return self._to_hold_entry(last_hold) if last_hold else None

    def remove_dolly_from_task(self, part_number: str, dolly_no: str, actor_name: str) -> bool:
        """Remove a dolly from web operator task (only from end)."""
        # Get all active hold entries for this part number, ordered by dolly number then creation date
        active_holds = DollySubmissionHold.query.filter_by(
            PartNumber=part_number
        ).filter(
            DollySubmissionHold.Status != "removed"
        ).order_by(
            DollySubmissionHold.DollyNo.asc(),
            DollySubmissionHold.CreatedAt.asc()
        ).all()
        
        if not active_holds:
            return False
        
        # Get the last dolly_no in the list
        last_dolly_no = active_holds[-1].DollyNo
        
        # Check if the requested dolly_no is the last one
        if last_dolly_no != dolly_no:
            return False
        
        # Mark ALL entries with this dolly_no as removed
        removed_count = 0
        for hold in active_holds:
            if hold.DollyNo == dolly_no:
                hold.Status = "removed"
                hold.UpdatedAt = datetime.utcnow()
                removed_count += 1
        
        # Update task counts
        task = WebOperatorTask.query.filter_by(PartNumber=part_number).first()
        if task:
            # Recalculate total items from remaining active holds
            remaining_count = DollySubmissionHold.query.filter_by(
                PartNumber=part_number
            ).filter(
                DollySubmissionHold.Status != "removed"
            ).count()
            task.TotalItems = remaining_count
            task.UpdatedAt = datetime.utcnow()
            
        db.session.commit()
        
        # Audit log - safe fallback for missing audit service
        try:
            if hasattr(self, 'audit') and self.audit:
                self.audit.log(
                    action="dolly.removed_from_task",
                    resource="dolly", 
                    resource_id=dolly_no,
                    actor_name=actor_name,
                    metadata={"part_number": part_number, "removed_count": removed_count}
                )
        except AttributeError:
            current_app.logger.warning("Audit service not available for dolly removal")
        
        return True

    def submit_task_with_tag(self, part_number: str, tag_type: str, user_id: int) -> bool:
        """Submit task with ASN or Irsaliye tag."""
        task = WebOperatorTask.query.filter_by(PartNumber=part_number).first()
        if not task:
            return False
            
        # Get all active hold entries for this task
        holds = DollySubmissionHold.query.filter_by(
            PartNumber=part_number
        ).filter(DollySubmissionHold.Status != "removed").all()
        
        # Create sefer records
        for hold in holds:
            payload = {}
            if hold.Payload:
                try:
                    payload = json.loads(hold.Payload)
                except json.JSONDecodeError:
                    payload = {}

            # 📅 Üretim tarihini backup tablosundan al
            production_date = self._get_production_date_from_backup(hold.DollyNo)

            sefer = SeferDollyEOL(
                SeferNumarasi=payload.get("sefer_no"),
                PlakaNo=payload.get("plaka_no"),
                DollyNo=hold.DollyNo,
                VinNo=hold.VinNo,
                EOLDate=production_date,
                PartNumber=getattr(hold, "PartNumber", None),
                TerminalUser=hold.TerminalUser,
                TerminalDate=hold.SubmittedAt,
                VeriGirisUser=f"user_{user_id}"
            )
            
            if tag_type == "asn":
                sefer.ASNDate = datetime.utcnow()
            elif tag_type == "irsaliye":
                sefer.IrsaliyeDate = datetime.utcnow()
            elif tag_type == "both":
                sefer.ASNDate = datetime.utcnow()
                sefer.IrsaliyeDate = datetime.utcnow()
                
            db.session.add(sefer)
            
            # Update hold status
            hold.Status = "completed"
            hold.UpdatedAt = datetime.utcnow()
        
        # Update task
        task.Status = "completed"
        task.CompletedAt = datetime.utcnow()
        task.ProcessedItems = task.TotalItems
        task.AssignedTo = user_id
        task.UpdatedAt = datetime.utcnow()
        
        db.session.commit()
        
        self.audit.log(
            action=f"task.submitted_{tag_type}",
            resource="task",
            resource_id=part_number,
            actor_user=None,  # We could load user here if needed
            metadata={"tag_type": tag_type, "total_items": task.TotalItems}
        )
        
        return True

    def _to_web_operator_task_entry(self, task: WebOperatorTask) -> WebOperatorTaskEntry:
        """Convert WebOperatorTask model to WebOperatorTaskEntry dataclass."""
        assigned_user_name = None
        if task.assigned_user:
            assigned_user_name = task.assigned_user.DisplayName or task.assigned_user.Username
            
        return WebOperatorTaskEntry(
            id=task.Id,
            part_number=task.PartNumber,
            status=task.Status,
            assigned_to=task.AssignedTo,
            assigned_user_name=assigned_user_name,
            group_tag=task.GroupTag,
            total_items=task.TotalItems,
            processed_items=task.ProcessedItems,
            progress_percentage=task.progress_percentage,
            can_submit_asn=task.can_submit_asn,
            can_submit_irsaliye=task.can_submit_irsaliye,
            created_at=task.CreatedAt,
            updated_at=task.UpdatedAt,
            completed_at=task.CompletedAt,
            hold_entries=[]
        )

    def _to_hold_entry(self, hold: DollySubmissionHold) -> HoldEntry:
        """Convert DollySubmissionHold model to HoldEntry dataclass."""
        payload = {}
        if hold.Payload:
            try:
                payload = json.loads(hold.Payload)
            except json.JSONDecodeError:
                payload = {"raw": hold.Payload}

        customer_hint = None
        if isinstance(payload, dict):
            customer_hint = payload.get("customer_ref") or payload.get("customer")
            if not customer_hint:
                details = payload.get("dolly_details")
                if isinstance(details, dict):
                    customer_hint = details.get("customer_ref")

        # Get DollyEOLInfo data for this specific VIN
        dolly_record = db.session.query(DollyEOLInfo).filter(
            DollyEOLInfo.DollyNo == hold.DollyNo,
            DollyEOLInfo.VinNo == hold.VinNo
        ).first()

        # For breakdown, only show THIS VIN's data (not all VINs of the dolly)
        breakdown = []
        if dolly_record:
            breakdown.append({
                "vin_no": dolly_record.VinNo,
                "customer_ref": dolly_record.CustomerReferans,
                "adet": dolly_record.Adet,
                "eol_name": dolly_record.EOLName,
                "eol_id": dolly_record.EOLID,
                "eol_date": dolly_record.EOLDATE.strftime("%d.%m.%Y") if dolly_record.EOLDATE else None,
            })

        return HoldEntry(
            id=hold.Id,
            dolly_no=hold.DollyNo,
            vin_no=hold.VinNo,
            status=hold.Status,
            terminal_user=hold.TerminalUser,
            part_number=hold.PartNumber,
            dolly_order_no=hold.DollyOrderNo,  # ÇOK ÖNEMLİ: CEVA'ya gönderilecek!
            scan_order=hold.ScanOrder,  # Okutma sırası
            scanned_at=hold.CreatedAt,
            submitted_at=hold.SubmittedAt,
            payload=payload,
            barcode=payload.get("barcode") if isinstance(payload, dict) else None,
            # DollyEOLInfo fields
            customer_referans=dolly_record.CustomerReferans if dolly_record else None,
            adet=dolly_record.Adet if dolly_record else None,
            eol_name=dolly_record.EOLName if dolly_record else None,
            eol_id=dolly_record.EOLID if dolly_record else None,
            eol_date=dolly_record.EOLDATE if dolly_record else None,
            eol_dolly_barcode=dolly_record.EOLDollyBarcode if dolly_record else None,
            vin_breakdown=breakdown,
        )

    # Manual Dolly Management Methods
    def list_queue_dollys_grouped(self, per_group: int = 50) -> Dict[str, List[QueueEntry]]:
        """Get queue dollys grouped by active EOL groups (dynamic)"""
        try:
            # Get active EOL groups
            active_groups = db.session.query(
                DollyGroup.Id,
                DollyGroup.GroupName,
                DollyGroupEOL.PWorkStationId
            ).join(
                DollyGroupEOL, DollyGroup.Id == DollyGroupEOL.GroupId
            ).filter(
                DollyGroup.IsActive == True
            ).all()

            # Get all queue dollys
            all_dollys = self.list_groups()
            
            # Create dynamic groups
            grouped = {}
            station_to_group = {}
            
            # Build station-to-group mapping
            for group_info in active_groups:
                group_name = group_info.GroupName
                station_id = group_info.PWorkStationId
                station_to_group[station_id] = group_name
                if group_name not in grouped:
                    grouped[group_name] = []
            
            # Add "Diğer" group for unmapped stations
            if "Diğer" not in grouped:
                grouped["Diğer"] = []
            
            # Group dollys based on their EOL name/ID
            for dolly in all_dollys:
                # Try to find matching group by EOL name
                group_name = "Diğer"
                
                # Check if dolly's EOL matches any group's stations
                if hasattr(dolly, 'eol_name') and dolly.eol_name:
                    for group_info in active_groups:
                        # Simple name matching - can be improved
                        if group_info.GroupName in dolly.eol_name or dolly.eol_name in group_info.GroupName:
                            group_name = group_info.GroupName
                            break
                
                # If no match found, use project name grouping
                if group_name == "Diğer":
                    project = self._extract_project_name(
                        getattr(dolly, 'eol_name', ''),
                        getattr(dolly, 'customer_ref', '')
                    )
                    group_name = project
                    if group_name not in grouped:
                        grouped[group_name] = []
                
                grouped[group_name].append(dolly)
            
            # Sort each group by dolly number (numeric part at end)
            for project in grouped:
                grouped[project].sort(key=self._dolly_entry_sort_key)
                if per_group and per_group > 0:
                    grouped[project] = grouped[project][:per_group]
            
            return grouped
            
        except Exception as e:
            current_app.logger.error(f"Queue dollys grouped list error: {e}")
            # Fallback to original grouping
            all_dollys = self.list_groups()
            grouped = {"Diğer": all_dollys}
            return grouped

    def manual_add_dolly_to_queue(self, dolly_no: str, vin_no: str, customer_ref: str, 
                                  eol_name: str, eol_id: str, actor_name: str) -> QueueEntry:
        """Manually add a dolly to the queue"""
        # Check if dolly already exists
        existing = DollyEOLInfo.query.filter_by(DollyNo=dolly_no).first()
        if existing:
            raise ValueError(f"Dolly {dolly_no} zaten mevcut")
        
        # Create new dolly entry
        new_dolly = DollyEOLInfo(
            DollyNo=dolly_no,
            VinNo=vin_no,
            CustomerReferans=customer_ref,
            EOLName=eol_name,
            EOLID=eol_id,
            EOLDATE=datetime.utcnow().date(),
            Adet=1
        )
        db.session.add(new_dolly)
        db.session.commit()
        
        # Log lifecycle
        self.lifecycle.ensure_received(new_dolly)
        
        self.audit.log(
            action="dolly.manual_add",
            resource="dolly",
            resource_id=dolly_no,
            actor_name=actor_name,
            metadata={"vin": vin_no, "eol": eol_name, "source": "manual"}
        )
        
        return self._to_queue_entry(new_dolly)

    def manual_submit_dolly(self, dolly_no: str, actor_name: str) -> bool:
        """Manually submit a dolly from queue (simulate terminal submit)"""
        # Check if dolly exists
        dolly = DollyEOLInfo.query.filter_by(DollyNo=dolly_no).first()
        if not dolly:
            raise ValueError(f"Dolly {dolly_no} bulunamadı")
        
        # Create hold entry (simulate scan)
        hold_entry = self.enqueue_hold_entry(
            dolly_no=dolly_no,
            vin_no=dolly.VinNo,
            terminal_user=f"manual_{actor_name}",
            payload={"source": "manual_submit"}
        )
        
        # Submit immediately
        submit_entry = self.submit_hold_entry(dolly_no, f"manual_{actor_name}")
        
        self.audit.log(
            action="dolly.manual_submit",
            resource="dolly",
            resource_id=dolly_no,
            actor_name=actor_name,
            metadata={"vin": dolly.VinNo, "part_number": hold_entry.part_number}
        )
        
        return submit_entry is not None
    
    def _get_dolly_group_info(self, eol_id: Optional[Union[str, int]]) -> dict:
        """Get group information for a dolly based on EOL ID (handles legacy schemas)."""
        if eol_id is None:
            return {
                "group_id": 0,
                "group_name": "DEFAULT",
                "shipping_tag": "both",
            }

        # Normalize id to int when possible (database column is integer)
        normalized_eol_id: Optional[int]
        try:
            normalized_eol_id = int(eol_id)
        except (TypeError, ValueError):
            normalized_eol_id = None

        query = db.session.query(
            DollyGroup.Id.label("group_id"),
            DollyGroup.GroupName.label("group_name"),
            DollyGroupEOL.ShippingTag.label("shipping_tag"),
        ).join(
            DollyGroupEOL, DollyGroup.Id == DollyGroupEOL.GroupId
        ).filter(
            DollyGroup.IsActive == True
        )

        if normalized_eol_id is not None:
            query = query.filter(DollyGroupEOL.PWorkStationId == normalized_eol_id)
        else:
            # If we cannot normalize the id, force empty set so default values kick in
            query = query.filter(text("1=0"))

        group_query = query.first()

        if group_query:
            return {
                "group_id": group_query.group_id,
                "group_name": group_query.group_name,
                "shipping_tag": group_query.shipping_tag or "both",
            }

        return {
            "group_id": 0,
            "group_name": "DEFAULT",
            "shipping_tag": "both",
        }
    
    def _get_or_create_group_part_number(self, group_info: dict, terminal_user: str) -> str:
        """Generate unique part number for group - NEW ALGORITHM"""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        
        # Check if there's an active task for this group in last 4 hours
        from datetime import timedelta
        cutoff_time = datetime.utcnow() - timedelta(hours=4)
        
        existing_task = WebOperatorTask.query.filter(
            WebOperatorTask.GroupTag == group_info['shipping_tag'],
            WebOperatorTask.Status.in_(['pending', 'in_progress']),
            WebOperatorTask.CreatedAt >= cutoff_time
        ).filter(
            WebOperatorTask.PartNumber.like(f"%{group_info['group_name']}%")
        ).first()
        
        if existing_task:
            return existing_task.PartNumber
        else:
            # Create new unique part number
            return f"PART_{group_info['group_name']}_{timestamp}_{terminal_user}"
    
    def _update_web_operator_task_for_part(self, part_number: str, group_info: dict):
        """Update or create web operator task for part number"""
        task = WebOperatorTask.query.filter_by(PartNumber=part_number).first()
        
        if not task:
            # Create new task
            task = WebOperatorTask(
                PartNumber=part_number,
                GroupTag=group_info['shipping_tag'],
                Status='pending',
                TotalItems=1,
                ProcessedItems=0,
                Metadata=json.dumps({
                    'group_id': group_info['group_id'],
                    'group_name': group_info['group_name'],
                    'creation_type': 'terminal_submit'
                })
            )
            db.session.add(task)
        else:
            # Update existing task
            task.TotalItems += 1
            task.UpdatedAt = datetime.utcnow()
    
    def create_manual_part(self, group_id: int, selected_dollys: List[str], shipping_tag: str, actor_name: str) -> str:
        """Create manual part with selected dollys - SPECIAL CASE HANDLING"""
        # Get group information
        group = DollyGroup.query.filter_by(Id=group_id, IsActive=True).first()
        if not group:
            raise ValueError("Grup bulunamadı")
            
        # Generate unique manual part number
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        part_number = f"MANUAL_{group.Name}_{timestamp}_{actor_name}"
        
        # Create web operator task
        task = WebOperatorTask(
            PartNumber=part_number,
            GroupTag=shipping_tag,
            Status='pending',
            TotalItems=len(selected_dollys),
            ProcessedItems=0,
            Metadata=json.dumps({
                'group_id': group_id,
                'group_name': group.Name,
                'creation_type': 'manual_mix',
                'selected_dollys': selected_dollys,
                'actor': actor_name
            })
        )
        db.session.add(task)
        
        # Update selected dollys to this part
        for dolly_no in selected_dollys:
            # Find existing hold entry or create one
            hold = DollySubmissionHold.query.filter_by(DollyNo=dolly_no).order_by(desc(DollySubmissionHold.CreatedAt)).first()
            
            if hold:
                hold.PartNumber = part_number
                hold.Status = "manual_assigned"
                hold.UpdatedAt = datetime.utcnow()
            else:
                # Create new hold entry for manual assignment
                dolly_info = DollyEOLInfo.query.filter_by(DollyNo=dolly_no).first()
                if dolly_info:
                    new_hold = DollySubmissionHold(
                        DollyNo=dolly_no,
                        VinNo=dolly_info.VinNo,
                        PartNumber=part_number,
                        Status="manual_assigned",
                        TerminalUser=f"manual_{actor_name}",
                        SubmittedAt=datetime.utcnow()
                    )
                    db.session.add(new_hold)
        
        db.session.commit()
        
        # Audit log
        self.audit.log(
            action="manual.part_creation",
            resource="part",
            resource_id=part_number,
            actor_name=actor_name,
            metadata={
                "group_id": group_id,
                "dolly_count": len(selected_dollys),
                "dollys": selected_dollys,
                "shipping_tag": shipping_tag
            }
        )
        
        return part_number

    def reorder_queue_dollys(self, dolly_orders: List[Dict[str, Any]], actor_name: str) -> bool:
        """Reorder dollys in queue by updating their dates"""
        try:
            base_date = datetime.utcnow().date()
            
            for order_info in dolly_orders:
                dolly_no = order_info.get("dollyNo")
                new_position = order_info.get("position", 0)
                
                dolly = DollyEOLInfo.query.filter_by(DollyNo=dolly_no).first()
                if dolly:
                    # Adjust date based on position (add minutes to maintain order)
                    adjusted_date = base_date
                    if new_position > 0:
                        adjusted_date = base_date.replace(day=min(28, base_date.day + new_position))
                    
                    dolly.EOLDATE = adjusted_date
            
            db.session.commit()
            
            self.audit.log(
                action="queue.reorder",
                resource="queue",
                resource_id="manual_reorder",
                actor_name=actor_name,
                metadata={"dolly_count": len(dolly_orders)}
            )
            
            return True
        except Exception as e:
            db.session.rollback()
            return False

    def get_queue_stats(self) -> Dict[str, Any]:
        """Get queue statistics for dashboard - DOLLY BAZLI SAYIM"""
        grouped_dollys = self.list_queue_dollys_grouped()
        
        # Unique dolly numbersını say (VIN bazlı değil)
        all_dolly_nos = set()
        for dollys in grouped_dollys.values():
            for d in dollys:
                all_dolly_nos.add(d.dolly_no)
        
        stats = {
            "total_dollys": len(all_dolly_nos),  # Unique dolly sayısı
            "projects": [],
            "ready_for_submit": 0,
            "in_progress": 0
        }
        
        for project, dollys in grouped_dollys.items():
            # Her project için unique dolly'leri say
            project_dolly_nos = set(d.dolly_no for d in dollys)
            
            project_stats = {
                "name": project,
                "count": len(project_dolly_nos),  # Unique dolly sayısı
                "first_date": min(d.eol_date for d in dollys if d.eol_date) if dollys else None,
                "last_date": max(d.eol_date for d in dollys if d.eol_date) if dollys else None
            }
            stats["projects"].append(project_stats)
            
            # Count status - VIN level'da say
            for dolly in dollys:
                if dolly.status == "EOL_READY":
                    stats["ready_for_submit"] += 1
                elif dolly.status in ["SCAN_CAPTURED", "WAITING_SUBMIT"]:
                    stats["in_progress"] += 1
        
        return stats

    def _extract_project_name(self, eol_name: str, customer_ref: str) -> str:
        """Extract project name from EOL name or customer reference"""
        # Try to extract from EOL name first (V710MR-EOL -> V710MR)
        if eol_name:
            if "V710" in eol_name.upper():
                if "MR" in eol_name.upper():
                    return "V710MR"
                elif "LLS" in eol_name.upper():
                    return "V710LLS"
                else:
                    return "V710"
            elif "J74" in eol_name.upper():
                return "J74"
            elif "C5" in eol_name.upper():
                return "C5"
        
        # Try customer reference
        if customer_ref:
            customer_upper = customer_ref.upper()
            if "V710" in customer_upper:
                return "V710MR" if "MR" in customer_upper else "V710"
            elif "J74" in customer_upper:
                return "J74"
            elif "C5" in customer_upper:
                return "C5"
        
        return "OTHER"

    def get_active_groups(self):
        """Get list of active EOL groups"""
        try:
            groups = db.session.query(
                DollyGroup.Id,
                DollyGroup.GroupName,
                DollyGroup.Description
            ).filter(
                DollyGroup.IsActive == True
            ).order_by(DollyGroup.GroupName).all()
            
            return [{'id': g.Id, 'name': g.GroupName, 'description': g.Description} for g in groups]
            
        except Exception as e:
            current_app.logger.error(f"Get active groups error: {e}")
            return []

    def get_dollys_grouped_for_collection(self, limit: int = 50):
        """Get dollys grouped by DollyNo with their VINs - only those NOT in submission hold"""
        try:
            from collections import defaultdict
            
            # Get all DollyNo+VinNo combinations that are already in submission hold
            submitted_pairs = db.session.query(
                DollySubmissionHold.DollyNo,
                DollySubmissionHold.VinNo
            ).filter(
                DollySubmissionHold.Status.in_(['completed', 'pending', 'holding'])
            ).all()
            
            # Create set of (DollyNo, VinNo) tuples for quick lookup
            submitted_set = {(pair.DollyNo, pair.VinNo) for pair in submitted_pairs}
            
            # Get all dollys from DollyEOLInfo, ordered by DollyNo
            all_dollys = db.session.query(DollyEOLInfo).order_by(
                DollyEOLInfo.DollyNo.asc(),
                DollyEOLInfo.VinNo.asc()
            ).all()
            
            # Filter out already submitted VINs
            available_dollys = [
                dolly for dolly in all_dollys 
                if (dolly.DollyNo, dolly.VinNo) not in submitted_set
            ]
            
            # Group by DollyNo
            grouped = defaultdict(list)
            for dolly in available_dollys:
                grouped[dolly.DollyNo].append(dolly)
            
            # Convert to list - only include dollys that have ALL their VINs available
            result = []
            for dolly_no, vins in sorted(grouped.items())[:limit]:
                # Use first VIN's data as representative
                first = vins[0]
                result.append({
                    'DollyNo': dolly_no,
                    'VinCount': len(vins),
                    'Vins': [v.VinNo for v in vins],
                    'CustomerReferans': first.CustomerReferans,
                    'EOLName': first.EOLName,
                    'EOLID': first.EOLID,
                    'EOLDATE': first.EOLDATE,
                    'Adet': first.Adet,
                    'AllVinData': vins
                })
            
            current_app.logger.info(f"✅ Found {len(result)} available dollys (grouped) for manual collection (filtered from {len(all_dollys)} total VINs)")
            if len(result) > 0:
                current_app.logger.info(f"📦 First available: {result[0]['DollyNo']}, Last: {result[-1]['DollyNo']}")
            return result
            
        except Exception as e:
            current_app.logger.error(f"Get grouped dollys error: {e}")
            import traceback
            current_app.logger.error(traceback.format_exc())
            return []

    def get_dollys_by_eol_for_collection(self, limit: int = 100):
        """Get available dollys grouped by EOL, ordered by insertion time
        
        NOTE: Submit edilen dolly'ler DollyEOLInfo'dan silindiği için
        burada sadece mevcut kayıtları çekmek yeterli. Ek filtrelemeye gerek yok.
        """
        try:
            from collections import defaultdict
            
            # Get ALL dollys from DollyEOLInfo - ORDER BY InsertedAt (kayıt atılma sırası)
            # Submit edilenler zaten silinmiş olduğu için burada sadece available olanlar var
            available_dollys = db.session.query(DollyEOLInfo).order_by(
                db.case((DollyEOLInfo.InsertedAt == None, 1), else_=0),
                DollyEOLInfo.InsertedAt.asc()
            ).all()
            
            # Group by EOLName first, then by DollyNo within each EOL
            # Track insertion order globally for all dollys
            eol_groups = defaultdict(lambda: defaultdict(list))
            global_dolly_order = {}  # Track first occurrence of each DollyNo globally
            eol_first_occurrence = {}  # Track first occurrence of each EOL
            
            for idx, dolly in enumerate(available_dollys):
                eol_name = dolly.EOLName or 'Unknown'
                dolly_no = dolly.DollyNo
                
                # Track first occurrence of EOL
                if eol_name not in eol_first_occurrence:
                    eol_first_occurrence[eol_name] = idx
                
                # Track first occurrence of DollyNo globally (across all EOLs)
                if dolly_no not in global_dolly_order:
                    global_dolly_order[dolly_no] = idx
                
                eol_groups[eol_name][dolly_no].append(dolly)
            
            # Build result structure: EOL -> Dollys (preserve insert order)
            result = []
            
            # Sort EOLs by first occurrence
            for eol_name in sorted(eol_first_occurrence.keys(), key=lambda x: eol_first_occurrence[x]):
                dolly_dict = eol_groups[eol_name]
                dollys_in_eol = []
                
                # Sort dollys by GLOBAL first occurrence order (not within EOL)
                for dolly_no in sorted(dolly_dict.keys(), key=lambda x: global_dolly_order[x]):
                    vins = dolly_dict[dolly_no]
                    # VINs in insert order (no sorting)
                    first_vin = vins[0]
                    vin_list = [v.VinNo for v in vins]
                    
                    # Debug log
                    if len(vins) > 1:
                        current_app.logger.info(f"📦 Dolly {dolly_no}: {len(vins)} VINs = {vin_list}")
                    
                    dollys_in_eol.append({
                        'DollyNo': dolly_no,
                        'DollyOrderNo': first_vin.DollyOrderNo,
                        'VinCount': len(vins),
                        'Vins': vin_list,  # Insert order preserved
                        'CustomerReferans': first_vin.CustomerReferans,
                        'EOLID': first_vin.EOLID,
                        'EOLDATE': first_vin.EOLDATE,
                        'InsertedAt': first_vin.InsertedAt,
                        'Adet': first_vin.Adet,
                    })
                
                result.append({
                    'EOLName': eol_name,
                    'EOLID': dollys_in_eol[0]['EOLID'] if dollys_in_eol else None,
                    'DollyCount': len(dollys_in_eol),
                    'TotalVINs': sum(d['VinCount'] for d in dollys_in_eol),
                    'Dollys': dollys_in_eol
                })
            
            # Sort by DollyCount descending (en çok dolly olan üstte)
            result.sort(key=lambda x: x['DollyCount'], reverse=True)
            
            current_app.logger.info(f"✅ Found {len(result)} EOLs with dollys for manual collection")
            for eol in result:
                current_app.logger.info(f"  📦 {eol['EOLName']}: {eol['DollyCount']} dollys, {eol['TotalVINs']} VINs")
            
            return result[:limit]
            
        except Exception as e:
            current_app.logger.error(f"Get dollys by EOL error: {e}")
            import traceback
            current_app.logger.error(traceback.format_exc())
            return []

    def get_all_available_dollys_for_collection(self, limit: int = 100):
        """Get all available dollys from DollyEOLInfo, ordered by DollyNo"""
        try:
            # Get all dollys from DollyEOLInfo, ordered by DollyNo
            dollys = db.session.query(DollyEOLInfo).order_by(
                DollyEOLInfo.DollyNo.asc(),
                DollyEOLInfo.VinNo.asc()
            ).limit(limit).all()
            
            current_app.logger.info(f"Found {len(dollys)} dollys for manual collection")
            if dollys:
                current_app.logger.info(f"First dolly: {dollys[0].DollyNo} - {dollys[0].VinNo}")
                current_app.logger.info(f"Last dolly: {dollys[-1].DollyNo} - {dollys[-1].VinNo}")
            return dollys
            
        except Exception as e:
            current_app.logger.error(f"Get available dollys error: {e}")
            import traceback
            current_app.logger.error(traceback.format_exc())
            return []

    def get_manual_collection_groups(self):
        """Get groups with their EOLs and dolly counts for manual collection web interface
        
        Returns same structure as API endpoint but for web dashboard use
        """
        try:
            from sqlalchemy.orm import joinedload
            
            # Get active groups with their EOLs
            groups = DollyGroup.query.filter_by(IsActive=True).options(joinedload(DollyGroup.eols)).all()
            
            # Get all station IDs across all groups
            all_station_ids = []
            for group in groups:
                all_station_ids.extend([ge.PWorkStationId for ge in group.eols])
            
            # Fetch all stations in one query
            stations = {}
            if all_station_ids:
                stations = {s.Id: s for s in PWorkStation.query.filter(PWorkStation.Id.in_(all_station_ids)).all()}
            
            # Get all EOL names
            eol_names = [s.PWorkStationName for s in stations.values()]
            
            # Get all counts in ONE query
            eol_counts = {}
            if eol_names:
                count_query = """
                SELECT 
                    d.EOLName,
                    COUNT(DISTINCT d.DollyNo) as dolly_count,
                    COUNT(DISTINCT CASE WHEN h.DollyNo IS NOT NULL THEN h.DollyNo END) as scanned_count
                FROM DollyEOLInfo d
                LEFT JOIN DollySubmissionHold h 
                    ON d.DollyNo = h.DollyNo 
                    AND h.Status = 'scanned'
                WHERE d.EOLName IN :eol_names
                GROUP BY d.EOLName
                """
                
                result_proxy = db.session.execute(
                    text(count_query).bindparams(db.bindparam('eol_names', expanding=True)), 
                    {"eol_names": tuple(eol_names)}
                )
                rows = result_proxy.fetchall()
                
                for row in rows:
                    eol_counts[row[0]] = {
                        'dolly_count': row[1] if row[1] else 0,
                        'scanned_count': row[2] if row[2] else 0
                    }
            
            result = []
            for group in groups:
                eol_dict = {}  # Use dict to avoid duplicates
                
                for group_eol in group.eols:
                    # Get EOL name from pre-fetched stations
                    station = stations.get(group_eol.PWorkStationId)
                    if not station:
                        continue
                    
                    eol_name = station.PWorkStationName
                    
                    # Skip if already added
                    if eol_name in eol_dict:
                        continue
                    
                    # Get counts from pre-fetched data
                    counts = eol_counts.get(eol_name, {'dolly_count': 0, 'scanned_count': 0})
                    dolly_count = counts['dolly_count']
                    scanned_count = counts['scanned_count']
                    
                    if dolly_count > 0:  # Sadece dolly'si olan EOL'leri göster
                        eol_dict[eol_name] = {
                            "eol_id": group_eol.PWorkStationId,
                            "eol_name": eol_name,
                            "dolly_count": dolly_count,
                            "scanned_count": scanned_count
                        }
                
                if eol_dict:  # Sadece dolly'si olan grupları göster
                    eol_list = list(eol_dict.values())
                    total_dolly_count = sum(e['dolly_count'] for e in eol_list)
                    total_scanned_count = sum(e['scanned_count'] for e in eol_list)
                    
                    result.append({
                        "group_id": group.Id,
                        "group_name": group.GroupName,
                        "eols": eol_list,
                        "total_dolly_count": total_dolly_count,
                        "total_scanned_count": total_scanned_count
                    })
            
            current_app.logger.info(f"✅ Found {len(result)} groups with dollys for manual collection")
            return result
            
        except Exception as e:
            current_app.logger.error(f"Get manual collection groups error: {e}")
            import traceback
            current_app.logger.error(traceback.format_exc())
            return []

    def create_manual_web_operator_tasks(self, group_id: int, task_count: int, shipping_tag: str, actor_name: str):
        """Create manual web operator tasks for a group"""
        try:
            from datetime import datetime
            from ..models.web_operator_task import WebOperatorTask
            
            # Verify group exists
            group = db.session.query(DollyGroup).filter(
                DollyGroup.Id == group_id,
                DollyGroup.IsActive == True
            ).first()
            
            if not group:
                raise ValueError("Grup bulunamadı")
            
            created_tasks = []
            base_timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            
            for i in range(task_count):
                # Generate unique part number
                part_number = f"WO_{group.GroupName}_{base_timestamp}_{i+1:03d}"
                
                # Create task
                task = WebOperatorTask(
                    part_number=part_number,
                    group_id=group_id,
                    group_tag=shipping_tag,
                    status="pending",
                    total_items=0,  # Will be filled as dollys are added
                    processed_items=0
                )
                
                db.session.add(task)
                created_tasks.append(task)
            
            db.session.commit()
            
            # Log action
            self.audit.log(
                action="web_operator.create_manual_tasks",
                resource="task",
                resource_id=f"group_{group_id}",
                actor_name=actor_name,
                metadata={
                    "group_name": group.GroupName,
                    "task_count": task_count,
                    "shipping_tag": shipping_tag,
                    "part_numbers": [task.part_number for task in created_tasks]
                }
            )
            
            return created_tasks
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Create manual web operator tasks error: {e}")
            raise

    def get_dollys_by_group(self, group_id: int):
        """Get dollys for a specific group - with VIN breakdown"""
        try:
            # Get all dollys and filter by group stations
            group_eols = db.session.query(DollyGroupEOL).filter(
                DollyGroupEOL.GroupId == group_id
            ).all()
            if not group_eols:
                return []

            station_ids = [eol.PWorkStationId for eol in group_eols]
            dollys = db.session.query(DollyEOLInfo).filter(
                DollyEOLInfo.EOLID.in_([str(sid) for sid in station_ids])
            ).all()

            if not dollys:
                eol_names = [f"EOL_{sid}" for sid in station_ids]
                dollys = db.session.query(DollyEOLInfo).filter(
                    DollyEOLInfo.EOLName.in_(eol_names)
                ).all()

            dollys = sorted(dollys, key=self._dolly_sort_key)

            queue_entries = []
            for dolly in dollys:
                vin_list = self._split_vin_numbers(dolly.VinNo)
                if not vin_list:
                    vin_list = [dolly.VinNo or dolly.DollyNo]

                for vin in vin_list:
                    submitted_dolly = db.session.query(DollySubmissionHold).filter(
                        DollySubmissionHold.DollyNo == dolly.DollyNo,
                        DollySubmissionHold.VinNo == vin,
                        DollySubmissionHold.Status.in_(['submitted', 'completed'])
                    ).first()

                    entry = self._to_queue_entry(dolly)
                    entry.vin_no = vin
                    if submitted_dolly:
                        entry.status = "submitted"
                        entry.metadata["submitted_at"] = submitted_dolly.SubmittedAt.isoformat() if submitted_dolly.SubmittedAt else None

                    queue_entries.append(entry)

            queue_entries.sort(key=self._dolly_entry_sort_key)
            current_app.logger.info(f"Found {len(queue_entries)} VIN entries for group {group_id}")
            return queue_entries

        except Exception as e:
            current_app.logger.error(f"Get dollys by group error: {e}")
            return []

    def create_manual_collection_submission(self, group_id: int, group_name: str, dollys: list, actor_name: str):
        """Create manual collection submission from selected dollys"""
        try:
            from datetime import datetime
            from ..models.web_operator_task import WebOperatorTask
            from collections import defaultdict
            
            # Group VINs by dolly_no (frontend sends expanded VIN list)
            dolly_groups = defaultdict(list)
            for item in dollys:
                dolly_groups[item['dolly_no']].append(item)
            
            # Get unique dollys with order
            unique_dollys = []
            for dolly_no, vins in dolly_groups.items():
                unique_dollys.append({
                    'dolly_no': dolly_no,
                    'order': vins[0].get('order', 0),
                    'vin_count': len(vins),
                    'vins': [v['vin_no'] for v in vins]
                })
            
            # Sort by order
            unique_dollys.sort(key=lambda x: x['order'])
            
            current_app.logger.info(f"📦 Manuel toplama: {len(unique_dollys)} dolly, toplam {len(dollys)} VIN")
            
            # Verify group exists
            group = db.session.query(DollyGroup).filter(
                DollyGroup.Id == group_id,
                DollyGroup.IsActive == True
            ).first()
            
            if not group:
                current_app.logger.warning(f"⚠️ Group {group_id} not found, creating without group validation")
            
            # Generate unique part number for this collection
            # M- prefix for Manuel, T- prefix for Terminal
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            part_number = f"M-{group_name}-{timestamp}"
            
            # Create web operator task for this manual collection
            import json
            task = WebOperatorTask(
                PartNumber=part_number,
                GroupTag="both",  # Default to both ASN and Irsaliye
                Status="completed",  # Mark as completed since manually selected
                TotalItems=len(unique_dollys),
                ProcessedItems=len(unique_dollys),  # All items processed
                AssignedTo=None,  # Manual collection, no specific operator
                Metadata=json.dumps({
                    "submission_type": "manual_collection",
                    "group_id": group_id,
                    "group_name": group_name,
                    "total_vins": len(dollys),
                    "selected_dollys": [{"dolly_no": d['dolly_no'], "order": d['order'], "vin_count": d['vin_count']} for d in unique_dollys]
                })
            )
            
            db.session.add(task)
            db.session.flush()  # Get task.Id before using it
            
            # Create submission hold records for each VIN (already expanded by frontend)
            submission_count = 0
            for vin_data in dollys:
                dolly_no = vin_data['dolly_no']
                vin_no = vin_data['vin_no']
                
                # Check if already exists
                existing_submission = db.session.query(DollySubmissionHold).filter(
                    DollySubmissionHold.DollyNo == dolly_no,
                    DollySubmissionHold.VinNo == vin_no
                ).first()
                
                if not existing_submission:
                    submission = DollySubmissionHold(
                        DollyNo=dolly_no,
                        VinNo=vin_no,
                        Status="completed",  # Mark as completed
                        PartNumber=part_number,
                        TerminalUser="web_operator_manual",
                        CreatedAt=datetime.utcnow(),
                        UpdatedAt=datetime.utcnow(),
                        SubmittedAt=datetime.utcnow()
                    )
                    db.session.add(submission)
                    submission_count += 1
                else:
                    # Update existing submission
                    existing_submission.Status = "completed"
                    existing_submission.PartNumber = part_number
                    existing_submission.TerminalUser = "web_operator_manual"
                    existing_submission.UpdatedAt = datetime.utcnow()
                    existing_submission.SubmittedAt = datetime.utcnow()
                    submission_count += 1
            
            db.session.commit()
            
            current_app.logger.info(f"✅ {submission_count} VIN kaydı oluşturuldu/güncellendi")
            
            # Log the manual collection
            self.audit.log(
                action="manual.collection_submission",
                resource="task",
                resource_id=part_number,
                actor_name=actor_name,
                metadata={
                    "group_id": group_id,
                    "group_name": group_name,
                    "dolly_count": len(unique_dollys),
                    "total_vins": len(dollys),
                    "selected_dollys": [d['dolly_no'] for d in unique_dollys]
                }
            )
            
            current_app.logger.info(f"✅ Manuel toplama başarılı: {part_number} - {len(unique_dollys)} dolly, {len(dollys)} VIN")
            
            return {
                "part_number": part_number,
                "task_id": task.Id,
                "submitted_count": len(unique_dollys),
                "total_vins": len(dollys)
            }
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Manual collection submission error: {e}")
            raise

    def get_next_available_dollys(self, limit: int = 10):
        """Get next available dollys that are not yet submitted"""
        try:
            # Get dollys that are not in any submission hold
            submitted_dollys_query = db.session.query(DollySubmissionHold.DollyNo).distinct()
            
            available_dollys = db.session.query(DollyEOLInfo).filter(
                ~DollyEOLInfo.DollyNo.in_(submitted_dollys_query)
            ).order_by(
                DollyEOLInfo.DollyNo
            ).limit(limit).all()
            
            current_app.logger.info(f"Found {len(available_dollys)} available dollys")
            return available_dollys
            
        except Exception as e:
            current_app.logger.error(f"Get next available dollys error: {e}")
            return []

    def get_next_dollys_for_eols(self, eol_names: list, part_number: str, limit: int = 50):
        """Get next dollys for specific EOLs from DollyEOLInfo (not yet in submission hold for this task)
        
        Args:
            eol_names: List of EOL names to filter by. If None or empty, returns dollys from ALL EOLs.
            part_number: Part number to exclude already submitted dollys
            limit: Maximum number of dollys to return
        """
        try:
            current_app.logger.info(f"🔍 Searching DollyEOLInfo for EOLs: {eol_names or 'ALL EOLs'}")
            
            # Get dollys already in submission hold for this part
            submitted_dollys = db.session.query(DollySubmissionHold.DollyNo).filter(
                DollySubmissionHold.PartNumber == part_number,
                DollySubmissionHold.Status != 'removed'
            ).distinct().all()
            submitted_dolly_nos = [d[0] for d in submitted_dollys]
            
            current_app.logger.info(f"🔍 Already submitted dollys for this task: {submitted_dolly_nos}")
            
            # Get dollys from DollyEOLInfo
            query = db.session.query(DollyEOLInfo)
            
            # ✅ Sadece eol_names verilmişse filtrele, yoksa TÜM EOL'leri getir
            if eol_names:
                query = query.filter(DollyEOLInfo.EOLName.in_(eol_names))
            
            if submitted_dolly_nos:
                query = query.filter(~DollyEOLInfo.DollyNo.in_(submitted_dolly_nos))
            
            available_dollys = query.order_by(
                DollyEOLInfo.InsertedAt.asc(),  # İlk kaydedilen önce
                DollyEOLInfo.DollyNo.asc()
            ).limit(limit).all()
            
            current_app.logger.info(f"✅ Found {len(available_dollys)} next dollys from DollyEOLInfo")
            if len(available_dollys) > 0:
                current_app.logger.info(f"📦 Sample: DollyNo={available_dollys[0].DollyNo}, EOL={available_dollys[0].EOLName}, CustomerRef={available_dollys[0].CustomerReferans}")
            
            return available_dollys
            
        except Exception as e:
            current_app.logger.error(f"Get next dollys for EOLs error: {e}")
            import traceback
            current_app.logger.error(traceback.format_exc())
            return []

    def add_next_dolly_to_task(
        self,
        part_number: str,
        dolly_no: str,
        actor_name: str,
        sefer_no: Optional[str] = None,
        plaka_no: Optional[str] = None,
        lokasyon: Optional[str] = None,
    ) -> bool:
        """Add a dolly to existing web operator task"""
        try:
            # FIXED: Get all VINs for this dolly
            dolly_vins = self._fetch_dolly_vins(dolly_no)
            
            if not dolly_vins:
                current_app.logger.warning(f"Dolly {dolly_no} not found in DollyEOLInfo")
                return False
            
            # Check if already in submission hold
            existing = db.session.query(DollySubmissionHold).filter(
                DollySubmissionHold.DollyNo == dolly_no,
                DollySubmissionHold.PartNumber == part_number,
                DollySubmissionHold.Status != "removed"
            ).first()
            
            if existing:
                current_app.logger.warning(f"Dolly {dolly_no} already in task {part_number}")
                return False
            
            # Use first dolly info for metadata
            first_dolly = dolly_vins[0]
            
            # Create submission hold entry for each VIN
            hold_payload = {
                "manual_addition": True,
                "sefer_no": sefer_no,
                "plaka_no": plaka_no,
                "lokasyon": lokasyon or "GHZNA",
                "dolly_details": {
                    "customer_ref": first_dolly.CustomerReferans,
                    "eol_name": first_dolly.EOLName,
                    "eol_id": first_dolly.EOLID,
                    "eol_date": first_dolly.EOLDATE.isoformat() if first_dolly.EOLDATE else None,
                },
            }
            
            added_count = 0
            for dolly_info in dolly_vins:
                hold_entry = DollySubmissionHold(
                    DollyNo=dolly_info.DollyNo,
                    DollyOrderNo=dolly_info.DollyOrderNo,
                    VinNo=dolly_info.VinNo,
                    PartNumber=part_number,
                    CustomerReferans=dolly_info.CustomerReferans,
                    Adet=dolly_info.Adet or 1,
                    EOLName=dolly_info.EOLName,
                    EOLID=dolly_info.EOLID,
                    Status="pending",  # ✅ pending olmalı (scanned değil, çünkü manuel ekleme)
                    TerminalUser=actor_name,
                    SeferNumarasi=sefer_no if sefer_no else None,  # ✅ Opsiyonel - daha sonra ASN/İrsaliye'de doldurulur
                    PlakaNo=plaka_no if plaka_no else None,  # ✅ Opsiyonel - daha sonra ASN/İrsaliye'de doldurulur
                    CreatedAt=datetime.now(),  # ✅ Türkiye yerel saati
                    UpdatedAt=datetime.now(),  # ✅ Türkiye yerel saati
                    Payload=json.dumps(hold_payload),
                )
                db.session.add(hold_entry)
                added_count += 1
            
            # Update task counts
            task = db.session.query(WebOperatorTask).filter(
                WebOperatorTask.PartNumber == part_number
            ).first()
            
            if task:
                task.TotalItems = (task.TotalItems or 0) + added_count
                task.ProcessedItems = (task.ProcessedItems or 0) + added_count
                task.UpdatedAt = datetime.now()  # ✅ Türkiye yerel saati
            
            db.session.commit()
            
            # Log the addition
            if hasattr(self, 'audit') and self.audit:
                self.audit.log(
                    action="operator.add_dolly",
                    resource="dolly",
                    resource_id=dolly_no,
                    actor_name=actor_name,
                    metadata={
                        "part_number": part_number, 
                        "manual_addition": True,
                        "vin_count": added_count
                    }
                )
            
            current_app.logger.info(f"Dolly {dolly_no} with {added_count} VINs added to task {part_number}")
            return True
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Add dolly to task error: {e}")
            return False

    def create_manual_dolly_submission(self, session_id: str, group_id: int, group_name: str, dollys: list, actor_name: str):
        """Create manual dolly submission (simulates terminal workflow)"""
        try:
            from datetime import datetime
            from ..models.web_operator_task import WebOperatorTask
            
            # Verify group exists
            group = db.session.query(DollyGroup).filter(
                DollyGroup.Id == group_id,
                DollyGroup.IsActive == True
            ).first()
            
            if not group:
                raise ValueError("Grup bulunamadı")
            
            # Generate unique part number for manual submission
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            part_number = f"MANUAL_{group_name}_{timestamp}"
            
            # Create web operator task for this manual submission
            task = WebOperatorTask(
                part_number=part_number,
                group_id=group_id,
                group_tag="both",  # Default to both ASN and Irsaliye
                status="in_progress",
                total_items=len(dollys),
                processed_items=len(dollys),  # All items processed immediately
                assigned_to=None,  # Manual submission, no specific operator
                metadata={
                    "session_id": session_id,
                    "submission_type": "manual",
                    "dollys": [{"barcode": d["barcode"], "scanned_at": d["scannedAt"]} for d in dollys]
                }
            )
            
            db.session.add(task)
            
            # For each scanned dolly, create submission records
            # (In real system, this would integrate with existing dolly tracking)
            for dolly_data in dollys:
                barcode = dolly_data['barcode']
                scanned_at = datetime.fromisoformat(dolly_data['scannedAt'].replace('Z', '+00:00'))
                
                # Create DollySubmissionHold if not exists
                existing_submission = db.session.query(DollySubmissionHold).filter(
                    DollySubmissionHold.SeferKodu == barcode
                ).first()
                
                if not existing_submission:
                    submission = DollySubmissionHold(
                        SeferKodu=barcode,
                        Status="completed",  # Mark as completed since manually processed
                        PartNumber=part_number,
                        CreatedAt=scanned_at,
                        UpdatedAt=datetime.utcnow()
                    )
                    db.session.add(submission)
                else:
                    # Update existing submission
                    existing_submission.Status = "completed"
                    existing_submission.PartNumber = part_number
                    existing_submission.UpdatedAt = datetime.utcnow()
            
            # Mark task as completed
            task.status = "completed"
            task.updated_at = datetime.utcnow()
            
            db.session.commit()
            
            # Log the manual submission
            self.audit.log(
                action="manual.dolly_submission",
                resource="task",
                resource_id=part_number,
                actor_name=actor_name,
                metadata={
                    "session_id": session_id,
                    "group_name": group_name,
                    "dolly_count": len(dollys),
                    "dollys": [d["barcode"] for d in dollys]
                }
            )
            
            return {
                "part_number": part_number,
                "task_id": task.id,
                "submitted_count": len(dollys)
            }
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Manual dolly submission error: {e}")
            raise

    def _get_or_create_part_number_for_dolly(self, dolly_no: str, dolly_record: Optional[DollyEOLInfo]) -> str:
        """Get existing part number or create new one based on group settings."""
        # Check if there's already a part number for this dolly today
        existing_hold = DollySubmissionHold.query.filter_by(DollyNo=dolly_no).filter(
            DollySubmissionHold.PartNumber.isnot(None)
        ).order_by(desc(DollySubmissionHold.CreatedAt)).first()
        
        if existing_hold and existing_hold.PartNumber:
            return existing_hold.PartNumber
            
        # Generate new part number
        part_number = self.generate_part_number()
        
        # Determine group tag from dolly's EOL settings
        group_tag = "both"  # default
        if dolly_record:
            group_tag = self._shipping_tag_for_eol(dolly_record.EOLName)
            
        # Create web operator task for this part number
        self.create_web_operator_task(part_number, group_tag)
        
        return part_number

    def _table_exists(self, table_name: str) -> bool:
        try:
            inspector = sa_inspect(db.engine)
            return table_name in inspector.get_table_names()
        except Exception:
            return False

    # NEW WORKFLOW METHODS
    def forklift_scan_dolly(
        self,
        dolly_no: str,
        forklift_user: Optional[str] = None,
        loading_session_id: Optional[str] = None,
        barcode: Optional[str] = None
    ) -> HoldEntry:
        """Forklift scans a dolly barcode - creates hold entries for ALL VINs in the dolly.
        
        CRITICAL: One dolly can contain multiple VINs (e.g., 8 parts).
        This method creates a separate DollySubmissionHold record for EACH VIN.
        
        Args:
            dolly_no: Dolly number to scan
            forklift_user: Operator name
            loading_session_id: Session ID to group multiple scans (auto-generated if None)
            barcode: Optional barcode for validation
        
        Returns:
            HoldEntry with first VIN (for backward compatibility)
        """
        # Get ALL VINs for this dolly from DollyEOLInfo
        vin_records = DollyEOLInfo.query.filter_by(DollyNo=dolly_no).order_by(DollyEOLInfo.InsertedAt).all()
        if not vin_records:
            raise ValueError(f"Dolly {dolly_no} bulunamadı")
        
        first_record = vin_records[0]
        
        # Validate barcode if provided
        if barcode and first_record.EOLDollyBarcode:
            if barcode != first_record.EOLDollyBarcode:
                raise ValueError("Barkod eşleşmedi")
        
        # Generate session ID if not provided
        if not loading_session_id:
            loading_session_id = f"LOAD_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{forklift_user or 'UNKNOWN'}"
        
        # Calculate scan order (1, 2, 3... within this session)
        max_order = db.session.query(func.max(DollySubmissionHold.ScanOrder)).filter(
            DollySubmissionHold.LoadingSessionId == loading_session_id
        ).scalar() or 0
        scan_order = max_order + 1
        
        # Create hold entry for EACH VIN in the dolly
        first_hold = None
        for vin_record in vin_records:
            hold = DollySubmissionHold(
                DollyNo=dolly_no,
                VinNo=vin_record.VinNo,
                DollyOrderNo=vin_record.DollyOrderNo,  # ÇOK ÖNEMLİ: CEVA'ya gönderilecek!
                CustomerReferans=vin_record.CustomerReferans,  # Customer bilgisi
                EOLName=vin_record.EOLName,  # EOL bilgisi
                EOLID=vin_record.EOLID,  # EOL ID
                Adet=vin_record.Adet or 1,  # Adet bilgisi
                Status="scanned",
                TerminalUser=forklift_user,
                LoadingSessionId=loading_session_id,
                ScanOrder=scan_order,
                Payload=json.dumps({"barcode": barcode}) if barcode else None,
                CreatedAt=datetime.utcnow()
            )
            db.session.add(hold)
            
            if first_hold is None:
                first_hold = hold
            
            # Log lifecycle for each VIN
            self.lifecycle.log_status(
                dolly_no,
                vin_record.VinNo,
                LifecycleService.Status.SCAN_CAPTURED,
                source="FORKLIFT",
                metadata={"forkliftUser": forklift_user, "sessionId": loading_session_id, "scanOrder": scan_order}
            )
        
        db.session.commit()
        
        # Audit log (summary for all VINs)
        self.audit.log(
            action="forklift.scan",
            resource="dolly",
            resource_id=dolly_no,
            actor_name=forklift_user or "forklift",
            metadata={"sessionId": loading_session_id, "scanOrder": scan_order, "vinCount": len(vin_records)}
        )
        
        return self._to_hold_entry(first_hold)
    
    def forklift_remove_last_dolly(
        self,
        loading_session_id: str,
        dolly_barcode: str,
        forklift_user: Optional[str] = None
    ) -> Dict[str, Any]:
        """Remove last dolly from loading session (LIFO - Last In First Out).
        
        CRITICAL: This method implements strict JIS validation to prevent wrong dolly removal.
        Algorithm ensures that ONLY the last scanned dolly (MAX ScanOrder) can be removed.
        
        Steps:
        1. Query SQL Server for ALL scanned dollys in session (ordered by ScanOrder DESC)
        2. Get FIRST record = Last scanned dolly (MAX ScanOrder)
        3. Lookup dolly by barcode from DollyEOLInfo
        4. Compare: Does scanned barcode match the LAST dolly in SQL?
        5. If NO → Reject with clear error message
        6. If YES → Mark as removed and commit
        
        Args:
            loading_session_id: Session ID
            dolly_barcode: Barcode of dolly to remove
            forklift_user: Operator name
        
        Returns:
            Removed dolly info
        
        Raises:
            ValueError: If dolly is not the last one or not found
            RuntimeError: If system error occurs (with automatic rollback)
        """
        try:
            # STEP 1: Get ALL scanned dollys in this session, ordered by ScanOrder DESC
            # This ensures we get the LAST scanned dolly first
            scanned_dollys = DollySubmissionHold.query.filter_by(
                LoadingSessionId=loading_session_id,
                Status="scanned"
            ).order_by(DollySubmissionHold.ScanOrder.desc()).all()
            
            if not scanned_dollys:
                raise ValueError(f"Session {loading_session_id} bulunamadı veya tüm dollylar zaten çıkarılmış")
            
            # STEP 2: LAST scanned dolly (highest ScanOrder)
            last_dolly = scanned_dollys[0]
            
            # STEP 3: Find dolly by barcode
            dolly_info = DollyEOLInfo.query.filter_by(EOLDollyBarcode=dolly_barcode).first()
            if not dolly_info:
                raise ValueError(f"Barkod '{dolly_barcode}' sistemde bulunamadı")
            
            scanned_dolly_no = dolly_info.DollyNo
            
            # STEP 4: CRITICAL VALIDATION - Does scanned barcode match the LAST dolly?
            if last_dolly.DollyNo != scanned_dolly_no:
                raise ValueError(
                    f"Sadece en son eklenen dolly çıkarılabilir. "
                    f"En son: {last_dolly.DollyNo} (Sıra: {last_dolly.ScanOrder}), "
                    f"Okutulan: {scanned_dolly_no}"
                )
            
            # STEP 5: Mark as removed (validation passed)
            last_dolly.Status = "removed"
            last_dolly.UpdatedAt = datetime.utcnow()
            
            db.session.commit()
            
            # Log lifecycle
            self.lifecycle.log_status(
                last_dolly.DollyNo,
                last_dolly.VinNo,
                LifecycleService.Status.SCAN_CAPTURED,  # Back to previous state
                source="FORKLIFT_REMOVE",
                metadata={
                    "forkliftUser": forklift_user,
                    "sessionId": loading_session_id,
                    "removedOrder": last_dolly.ScanOrder,
                    "reason": "Operator removed from loading",
                    "barcodeScanned": dolly_barcode
                }
            )
            
            # Audit log
            self.audit.log(
                action="forklift.remove_dolly",
                resource="dolly",
                resource_id=last_dolly.DollyNo,
                actor_name=forklift_user or "forklift",
                metadata={
                    "sessionId": loading_session_id,
                    "scanOrder": last_dolly.ScanOrder,
                    "barcode": dolly_barcode,
                    "validationPassed": True
                }
            )
            
            return {
                "dollyNo": last_dolly.DollyNo,
                "vinNo": last_dolly.VinNo,
                "scanOrder": last_dolly.ScanOrder,
                "removedAt": last_dolly.UpdatedAt.isoformat()
            }
            
        except ValueError:
            raise
        except Exception as e:
            db.session.rollback()
            self._log_critical_error("forklift_remove_last_dolly", e, {
                "sessionId": loading_session_id,
                "barcode": dolly_barcode
            })
            raise RuntimeError(f"Dolly çıkarma hatası: {str(e)}")
    
    def forklift_complete_loading(
        self,
        loading_session_id: str,
        forklift_user: Optional[str] = None
    ) -> Dict[str, Any]:
        """Forklift completes loading - marks all scanned dollys as ready for operator.
        
        Args:
            loading_session_id: Session ID to complete
            forklift_user: Operator name
        
        Returns:
            Summary of completed loading
        """
        try:
            # Get all scanned dollys in this session
            holds = DollySubmissionHold.query.filter_by(
                LoadingSessionId=loading_session_id,
                Status="scanned"
            ).all()
            
            if not holds:
                raise ValueError(f"Session {loading_session_id} bulunamadı veya zaten tamamlanmış")
            
            # Update all to loading_completed status
            now = datetime.utcnow()
            for hold in holds:
                hold.Status = "loading_completed"
                hold.LoadingCompletedAt = now
                hold.UpdatedAt = now
                
                # Log lifecycle
                self.lifecycle.log_status(
                    hold.DollyNo,
                    hold.VinNo,
                    LifecycleService.Status.WAITING_OPERATOR,
                    source="FORKLIFT",
                    metadata={"forkliftUser": forklift_user, "sessionId": loading_session_id}
                )
            
            db.session.commit()
            
            # Create WebOperatorTask for this session
            part_number = self._generate_part_number()
            
            # Determine group tag from first dolly's EOL
            first_hold = holds[0]
            group_tag = "both"  # Default
            
            # Try to get group tag from EOL name
            try:
                from .dolly_service import DollyService
                # Get EOL info to determine shipping tag
                eol_info = db.session.query(DollyEOLInfo).filter_by(
                    DollyNo=first_hold.DollyNo
                ).first()
                
                if eol_info and eol_info.EOLName:
                    # Check if this EOL has a specific shipping tag
                    group_tag_mapping = self._get_eol_shipping_tags()
                    group_tag = group_tag_mapping.get(eol_info.EOLName, "both")
            except Exception as e:
                current_app.logger.warning(f"Could not determine group tag: {e}")
            
            # Create task
            task = WebOperatorTask(
                PartNumber=part_number,
                Status="pending",
                GroupTag=group_tag,
                CreatedAt=now,
                UpdatedAt=now
            )
            db.session.add(task)
            
            # Update all holds with the part number
            for hold in holds:
                hold.PartNumber = part_number
            
            db.session.commit()
            
            current_app.logger.info(f"✅ WebOperatorTask created: {part_number} for session {loading_session_id}")
            
            # Audit log
            self.audit.log(
                action="forklift.complete_loading",
                resource="loading_session",
                resource_id=loading_session_id,
                actor_name=forklift_user or "forklift",
                metadata={
                    "dollyCount": len(holds),
                    "partNumber": part_number,
                    "taskCreated": True
                }
            )
            
        except ValueError:
            raise
        except Exception as e:
            db.session.rollback()
            self._log_critical_error("forklift_complete_loading", e, {
                "sessionId": loading_session_id
            })
            raise RuntimeError(f"Loading tamamlama hatası: {str(e)}")
        
        return {
            "loadingSessionId": loading_session_id,
            "status": "loading_completed",
            "dollyCount": len(holds),
            "completedAt": now.isoformat(),
            "dollys": [{"dollyNo": h.DollyNo, "vinNo": h.VinNo, "scanOrder": h.ScanOrder} for h in holds]
        }
    
    def list_loading_sessions(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all loading sessions with their dollys.
        
        Args:
            status: Filter by status (scanned, loading_completed, completed)
        
        Returns:
            List of loading sessions
        """
        query = db.session.query(
            DollySubmissionHold.LoadingSessionId,
            DollySubmissionHold.Status,
            DollySubmissionHold.TerminalUser,
            func.count(DollySubmissionHold.Id).label('dolly_count'),
            func.min(DollySubmissionHold.CreatedAt).label('first_scan'),
            func.max(DollySubmissionHold.LoadingCompletedAt).label('completed_at')
        ).filter(
            DollySubmissionHold.LoadingSessionId.isnot(None)
        ).group_by(
            DollySubmissionHold.LoadingSessionId,
            DollySubmissionHold.Status,
            DollySubmissionHold.TerminalUser
        )
        
        if status:
            query = query.filter(DollySubmissionHold.Status == status)
        
        results = query.order_by(desc('first_scan')).all()
        
        sessions = []
        for row in results:
            sessions.append({
                "loadingSessionId": row.LoadingSessionId,
                "status": row.Status,
                "forkliftUser": row.TerminalUser,
                "dollyCount": row.dolly_count,
                "firstScanAt": row.first_scan.isoformat() if row.first_scan else None,
                "completedAt": row.completed_at.isoformat() if row.completed_at else None
            })
        
        return sessions
    
    def list_pending_shipments(self) -> List[Dict[str, Any]]:
        """List all loading sessions waiting for operator to add shipment details."""
        sessions = self.list_loading_sessions(status="loading_completed")
        
        # Enrich with dolly details
        for session in sessions:
            dollys = DollySubmissionHold.query.filter_by(
                LoadingSessionId=session["loadingSessionId"]
            ).order_by(DollySubmissionHold.ScanOrder).all()
            
            session["dollys"] = [
                {
                    "id": d.Id,  # Added ID for checkbox selection
                    "dollyNo": d.DollyNo,
                    "vinNo": d.VinNo,
                    "scanOrder": d.ScanOrder,
                    "scannedAt": d.CreatedAt.isoformat() if d.CreatedAt else None,
                    "customerReferans": None,  # Will be enriched from DollyEOLInfo
                    "eolName": None
                }
                for d in dollys
            ]
            
            # Enrich with DollyEOLInfo data
            for dolly_dict in session["dollys"]:
                eol_info = DollyEOLInfo.query.filter_by(DollyNo=dolly_dict["dollyNo"]).first()
                if eol_info:
                    dolly_dict["customerReferans"] = eol_info.CustomerReferans
                    dolly_dict["eolName"] = eol_info.EOLName
        
        return sessions
    
    def get_shipment_details(self, loading_session_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific loading session."""
        dollys = DollySubmissionHold.query.filter_by(
            LoadingSessionId=loading_session_id
        ).order_by(DollySubmissionHold.ScanOrder).all()
        
        if not dollys:
            return None
        
        # Get DollyEOLInfo details for each dolly
        dolly_details = []
        for hold in dollys:
            eol_info = DollyEOLInfo.query.filter_by(DollyNo=hold.DollyNo).first()
            dolly_details.append({
                "dollyNo": hold.DollyNo,
                "vinNo": hold.VinNo,
                "scanOrder": hold.ScanOrder,
                "scannedAt": hold.CreatedAt.isoformat() if hold.CreatedAt else None,
                "customerReferans": eol_info.CustomerReferans if eol_info else None,
                "eolName": eol_info.EOLName if eol_info else None,
                "adet": eol_info.Adet if eol_info else None
            })
        
        return {
            "loadingSessionId": loading_session_id,
            "status": dollys[0].Status,
            "forkliftUser": dollys[0].TerminalUser,
            "dollyCount": len(dollys),
            "firstScanAt": dollys[0].CreatedAt.isoformat() if dollys[0].CreatedAt else None,
            "completedAt": dollys[0].LoadingCompletedAt.isoformat() if dollys[0].LoadingCompletedAt else None,
            "dollys": dolly_details
        }
    
    def validate_sefer_format(self, sefer: str) -> bool:
        """Validate sefer number format (e.g., SFR20250001 or custom format)."""
        import re
        # Format: SFR + 8 digits or any alphanumeric 5-20 chars
        pattern = r'^[A-Z]{2,5}\d{4,10}$|^[A-Z0-9]{5,20}$'
        return bool(re.match(pattern, sefer.strip().upper()))
    
    def validate_plaka_format(self, plaka: str) -> bool:
        """Validate Turkish license plate format."""
        import re
        # Remove spaces and normalize
        normalized = plaka.strip().upper().replace(" ", "")
        # Format: 34ABC123 or 34A12345 or 34AB1234
        pattern = r'^\d{2}[A-Z]{1,3}\d{2,5}$'
        return bool(re.match(pattern, normalized))
    
    def check_duplicate_sefer(self, sefer: str) -> bool:
        """Check if sefer number already exists."""
        existing = SeferDollyEOL.query.filter_by(SeferNumarasi=sefer).first()
        return existing is not None
    
    def _log_critical_error(self, function_name: str, error: Exception, context: dict):
        """Log critical errors that could stop the system."""
        import traceback
        error_details = {
            "function": function_name,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "traceback": traceback.format_exc(),
            "context": context,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Log to audit system
        self.audit.log(
            action="system.critical_error",
            resource="system",
            resource_id=function_name,
            actor_name="system",
            metadata=error_details
        )
        
        # Also log to application logger
        import logging
        logger = logging.getLogger(__name__)
        logger.critical(f"CRITICAL ERROR in {function_name}: {error}", extra=error_details)
    
    def operator_complete_shipment(
        self,
        loading_session_id: str,
        sefer_numarasi: str,
        plaka_no: str,
        shipping_type: str,
        operator_user: Optional[str] = None,
        selected_dolly_ids: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """Web operator completes shipment by adding Sefer No, Plaka, and sending ASN/Irsaliye.
        
        Args:
            loading_session_id: Session ID to complete
            sefer_numarasi: Shipment number
            plaka_no: Truck plate number
            shipping_type: "asn", "irsaliye", or "both"
            operator_user: Operator username
            selected_dolly_ids: Optional list of DollySubmissionHold IDs to complete (for partial shipment)
        
        Returns:
            Summary of completed shipment
        
        Raises:
            ValueError: Validation errors
            RuntimeError: System errors
        """
        try:
            # Validations
            if not self.validate_sefer_format(sefer_numarasi):
                raise ValueError(
                    f"Geçersiz sefer numarası formatı: {sefer_numarasi}. "
                    "Örnek: SFR20250001 veya SFR2025001"
                )
            
            if not self.validate_plaka_format(plaka_no):
                raise ValueError(
                    f"Geçersiz plaka formatı: {plaka_no}. "
                    "Örnek: 34 ABC 123 veya 34ABC123"
                )
            
            if self.check_duplicate_sefer(sefer_numarasi):
                raise ValueError(
                    f"Sefer numarası {sefer_numarasi} daha önce kullanılmış. "
                    "Lütfen farklı bir numara girin."
                )
            
            # Get dollys in this session
            query = DollySubmissionHold.query.filter_by(
                LoadingSessionId=loading_session_id,
                Status="loading_completed"
            )
            
            # Partial shipment: only selected dollys
            if selected_dolly_ids:
                query = query.filter(DollySubmissionHold.Id.in_(selected_dolly_ids))
            
            holds = query.all()
            
            if not holds:
                if selected_dolly_ids:
                    raise ValueError(f"Seçili dolly'ler bulunamadı veya zaten tamamlanmış")
                else:
                    raise ValueError(f"Session {loading_session_id} bulunamadı veya zaten tamamlanmış")
            
            now = datetime.utcnow()
            completed_dollys = []
            
            # Process each dolly
            for hold in holds:
                # Update hold entry
                hold.SeferNumarasi = sefer_numarasi
                hold.PlakaNo = plaka_no
                hold.Status = "completed"
                hold.SubmittedAt = now
                hold.UpdatedAt = now
                
                # Get dolly info
                dolly_info = DollyEOLInfo.query.filter_by(DollyNo=hold.DollyNo).first()
                if not dolly_info:
                    continue
                
                # Create SeferDollyEOL record
                # 📅 Üretim tarihini backup tablosundan al
                production_date = self._get_production_date_from_backup(hold.DollyNo)
                eol_dt = production_date or getattr(dolly_info, "InsertedAt", None) or getattr(dolly_info, "EOLDATE", None) or hold.CreatedAt
                terminal_dt = hold.LoadingCompletedAt or hold.CreatedAt or eol_dt

                sefer_record = SeferDollyEOL(
                    SeferNumarasi=sefer_numarasi,
                    PlakaNo=plaka_no,
                    DollyNo=hold.DollyNo,
                    VinNo=hold.VinNo,
                    PartNumber=getattr(hold, "PartNumber", None),
                    CustomerReferans=dolly_info.CustomerReferans,
                    Adet=dolly_info.Adet,
                    EOLName=dolly_info.EOLName,
                    EOLID=dolly_info.EOLID,
                    EOLDate=eol_dt,
                    TerminalUser=hold.TerminalUser,
                    TerminalDate=terminal_dt,
                    VeriGirisUser=operator_user,
                    ASNDate=now if shipping_type in ["asn", "both"] else None,
                    IrsaliyeDate=now if shipping_type in ["irsaliye", "both"] else None
                )
                db.session.add(sefer_record)
                
                # Log lifecycle
                final_status = self._final_status_for_tag(shipping_type)
                self.lifecycle.log_status(
                    hold.DollyNo,
                    hold.VinNo,
                    final_status,
                    source="OPERATOR",
                    metadata={
                        "operatorUser": operator_user,
                        "seferNumarasi": sefer_numarasi,
                        "plakaNo": plaka_no,
                        "shippingType": shipping_type
                    }
                )
                
                completed_dollys.append({
                    "dollyNo": hold.DollyNo,
                    "vinNo": hold.VinNo,
                    "scanOrder": hold.ScanOrder
                })
            
            db.session.commit()
            
            # Audit log
            self.audit.log(
                action="operator.complete_shipment",
                resource="loading_session",
                resource_id=loading_session_id,
                actor_name=operator_user or "operator",
                metadata={
                    "seferNumarasi": sefer_numarasi,
                    "plakaNo": plaka_no,
                    "shippingType": shipping_type,
                    "dollyCount": len(completed_dollys),
                    "partialShipment": bool(selected_dolly_ids)
                }
            )
            
            return {
                "loadingSessionId": loading_session_id,
                "seferNumarasi": sefer_numarasi,
                "plakaNo": plaka_no,
                "shippingType": shipping_type,
                "dollyCount": len(completed_dollys),
                "completedAt": now.isoformat(),
                "dollys": completed_dollys,
                "partialShipment": bool(selected_dolly_ids)
            }
            
        except ValueError:
            # Validation errors - no rollback needed, just re-raise
            raise
        except Exception as e:
            # Critical error - rollback and log
            db.session.rollback()
            self._log_critical_error("operator_complete_shipment", e, {
                "sessionId": loading_session_id,
                "seferNumarasi": sefer_numarasi,
                "operator": operator_user
            })
            raise RuntimeError(
                f"Sevkiyat tamamlama hatası: {str(e)}. "
                "İşlem geri alındı, lütfen tekrar deneyin."
            )


    def remove_dolly_from_queue(
        self,
        dolly_no: int,
        vin_no: str,
        removed_by: str,
        reason: Optional[str] = None
    ) -> bool:
        """
        Sıradan dolly'yi manuel olarak kaldır ve arşivle (SÜRELİ OLARAK)
        
        Args:
            dolly_no: Dolly numarası
            vin_no: VIN numarası
            removed_by: İşlemi yapan kullanıcı
            reason: Kaldırma nedeni
            
        Returns:
            bool: Başarılı ise True
        """
        try:
            # DollyEOLInfo'dan kaydı bul
            dolly_record = DollyEOLInfo.query.filter_by(
                DollyNo=dolly_no,
                VinNo=vin_no
            ).first()
            
            if not dolly_record:
                raise ValueError(f"Dolly {dolly_no}/{vin_no} sırada bulunamadı")
            
            # Arşiv kaydı oluştur
            removed_record = DollyQueueRemoved.from_dolly_eol(
                dolly_eol_record=dolly_record,
                removed_by=removed_by,
                reason=reason
            )
            
            db.session.add(removed_record)
            
            # Orijinal kaydı sil
            db.session.delete(dolly_record)
            
            # Audit log
            self.audit.log(
                action="queue.remove_dolly",
                resource="dolly_queue",
                resource_id=f"{dolly_no}/{vin_no}",
                actor_name=removed_by,
                metadata={
                    "dolly_no": dolly_no,
                    "vin_no": vin_no,
                    "reason": reason,
                    "archive_id": removed_record.Id
                }
            )
            
            db.session.commit()
            return True
            
        except Exception as e:
            db.session.rollback()
            self._log_critical_error("remove_dolly_from_queue", e, {
                "dolly_no": dolly_no,
                "vin_no": vin_no,
                "removed_by": removed_by
            })
            raise RuntimeError(f"Dolly kaldırma hatası: {str(e)}")
    
    
    def remove_multiple_dollys_from_queue(
        self,
        dolly_list: List[Dict[str, Any]],
        removed_by: str,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Birden fazla dolly'yi toplu olarak sıradan kaldır (SÜRELİ ARŞİV)
        
        Args:
            dolly_list: [{"dolly_no": 123, "vin_no": "ABC123"}, ...]
            removed_by: İşlemi yapan kullanıcı
            reason: Kaldırma nedeni
            
        Returns:
            Dict: {"success_count": 5, "failed": [], "removed_ids": []}
        """
        success_count = 0
        failed = []
        removed_ids = []
        
        try:
            # Aynı dolly'yi birden çok VIN ile gönderebileceğimiz için gruplayıp tek seferde çekelim.
            grouped_dollys: Dict[str, set[str]] = {}
            for item in dolly_list:
                dolly_no = str(item.get("dolly_no") or "").strip()
                vin_no = str(item.get("vin_no") or "").strip()
                
                if not dolly_no:
                    failed.append({"dolly_no": dolly_no, "vin_no": vin_no, "error": "Eksik dolly no"})
                    continue
                grouped_dollys.setdefault(dolly_no, set())
                if vin_no:
                    grouped_dollys[dolly_no].add(vin_no)
            
            for dolly_no, vin_set in grouped_dollys.items():
                # Dollynin tüm VIN'lerini tek seferde al (seçili VIN listesi varsa filtrele)
                query = DollyEOLInfo.query.filter_by(DollyNo=dolly_no)
                if vin_set:
                    query = query.filter(DollyEOLInfo.VinNo.in_(vin_set))
                
                records = query.all()
                if not records:
                    failed.append({"dolly_no": dolly_no, "vin_no": None, "error": "Kayıt bulunamadı"})
                    continue
                
                for record in records:
                    removed_record = DollyQueueRemoved.from_dolly_eol(
                        dolly_eol_record=record,
                        removed_by=removed_by,
                        reason=reason
                    )
                    db.session.add(removed_record)
                    db.session.delete(record)
                    success_count += 1
                    removed_ids.append(removed_record.Id)
            
            # Audit log
            self.audit.log(
                action="queue.remove_multiple_dollys",
                resource="dolly_queue",
                resource_id="bulk_operation",
                actor_name=removed_by,
                metadata={
                    "total_requested": len(dolly_list),
                    "success_count": success_count,
                    "failed_count": len(failed),
                    "reason": reason
                }
            )
            
            db.session.commit()
            
            return {
                "success_count": success_count,
                "failed": failed,
                "removed_ids": removed_ids
            }
            
        except Exception as e:
            db.session.rollback()
            self._log_critical_error("remove_multiple_dollys_from_queue", e, {
                "count": len(dolly_list),
                "removed_by": removed_by
            })
            raise RuntimeError(f"Toplu dolly kaldırma hatası: {str(e)}")
    
    
    def list_removed_dollys(
        self,
        page: int = 1,
        per_page: int = 50,
        search_term: str = "",
        filter_dolly_no: str = "",
        filter_vin: str = "",
        filter_customer_ref: str = "",
        filter_eol_name: str = "",
        filter_eol_id: str = "",
        filter_barcode: str = "",
        filter_removed_by: str = "",
        filter_reason: str = ""
    ) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
        """Arşivlenmiş dolly'leri sayfalı listele."""
        query = DollyQueueRemoved.query
        if search_term:
            term = f"%{search_term}%"
            query = query.filter(or_(
                DollyQueueRemoved.DollyNo.like(term),
                DollyQueueRemoved.VinNo.like(term),
                DollyQueueRemoved.CustomerReferans.like(term),
                DollyQueueRemoved.EOLName.like(term),
                DollyQueueRemoved.EOLID.like(term),
                DollyQueueRemoved.EOLDollyBarcode.like(term),
                DollyQueueRemoved.RemovedBy.like(term),
                DollyQueueRemoved.RemovalReason.like(term)
            ))
        if filter_dolly_no:
            query = query.filter(DollyQueueRemoved.DollyNo.like(f"%{filter_dolly_no}%"))
        if filter_vin:
            query = query.filter(DollyQueueRemoved.VinNo.like(f"%{filter_vin}%"))
        if filter_customer_ref:
            query = query.filter(DollyQueueRemoved.CustomerReferans.like(f"%{filter_customer_ref}%"))
        if filter_eol_name:
            query = query.filter(DollyQueueRemoved.EOLName.like(f"%{filter_eol_name}%"))
        if filter_eol_id:
            query = query.filter(DollyQueueRemoved.EOLID.like(f"%{filter_eol_id}%"))
        if filter_barcode:
            query = query.filter(DollyQueueRemoved.EOLDollyBarcode.like(f"%{filter_barcode}%"))
        if filter_removed_by:
            query = query.filter(DollyQueueRemoved.RemovedBy.like(f"%{filter_removed_by}%"))
        if filter_reason:
            query = query.filter(DollyQueueRemoved.RemovalReason.like(f"%{filter_reason}%"))
        query = query.order_by(desc(DollyQueueRemoved.RemovedAt))
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        items = [record.to_dict() for record in pagination.items]
        meta = {
            "page": pagination.page,
            "per_page": pagination.per_page,
            "total_count": pagination.total,
            "total_pages": pagination.pages if pagination.per_page else 1,
            "has_prev": pagination.has_prev,
            "has_next": pagination.has_next,
        }
        return items, meta

    def list_sefer_history(
        self,
        page: int = 1,
        per_page: int = 50
    ) -> Tuple[List[SeferDollyEOL], Dict[str, int]]:
        """SeferDollyEOL geçmişini sayfalı getir."""
        query = SeferDollyEOL.query.order_by(
            case((SeferDollyEOL.PartNumber.is_(None), 1), else_=0),
            SeferDollyEOL.PartNumber.asc(),
            case((SeferDollyEOL.TerminalDate.is_(None), 1), else_=0),
            SeferDollyEOL.TerminalDate.desc(),
            case((SeferDollyEOL.EOLDate.is_(None), 1), else_=0),
            SeferDollyEOL.EOLDate.desc(),
        )
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        meta = {
            "page": pagination.page,
            "per_page": pagination.per_page,
            "total_count": pagination.total,
            "total_pages": pagination.pages if pagination.per_page else 1,
            "has_prev": pagination.has_prev,
            "has_next": pagination.has_next,
        }
        return pagination.items, meta
    
    
    def restore_dolly_to_queue(self, archive_id: int, restored_by: str) -> bool:
        """Arşivden dolly'yi geri sıraya al"""
        try:
            with db.session.no_autoflush:
                removed_record = DollyQueueRemoved.query.filter_by(Id=archive_id).first()
            
            if not removed_record:
                raise ValueError(f"Arşiv kaydı {archive_id} bulunamadı")
            
            # Duplicate kontrolü
            existing = DollyEOLInfo.query.filter_by(
                DollyNo=removed_record.DollyNo,
                VinNo=removed_record.VinNo
            ).first()
            
            if existing:
                raise ValueError(f"Dolly {removed_record.DollyNo}/{removed_record.VinNo} zaten sırada")
            
            # Yeni DollyEOLInfo kaydı oluştur
            new_record = DollyEOLInfo(
                DollyNo=removed_record.DollyNo,
                VinNo=removed_record.VinNo,
                CustomerReferans=removed_record.CustomerReferans,
                Adet=removed_record.Adet,
                EOLName=removed_record.EOLName,
                EOLID=removed_record.EOLID,
                EOLDATE=removed_record.EOLDATE,
                EOLDollyBarcode=removed_record.EOLDollyBarcode,
                DollyOrderNo=removed_record.DollyOrderNo,
                RECEIPTID=removed_record.RECEIPTID,
                InsertedAt=datetime.utcnow()  # Yeni ekleme zamanı
            )
            
            db.session.add(new_record)
            db.session.delete(removed_record)
            
            conn = db.session.connection()
            try:
                conn.execute(text("SET IDENTITY_INSERT DollyEOLInfo ON"))
                db.session.flush()
            finally:
                conn.execute(text("SET IDENTITY_INSERT DollyEOLInfo OFF"))
            
            # Audit log
            self.audit.log(
                action="queue.restore_dolly",
                resource="dolly_queue",
                resource_id=f"{removed_record.DollyNo}/{removed_record.VinNo}",
                actor_name=restored_by,
                metadata={
                    "archive_id": archive_id,
                    "dolly_no": removed_record.DollyNo,
                    "vin_no": removed_record.VinNo
                }
            )
            
            db.session.commit()
            return True
            
        except Exception as e:
            db.session.rollback()
            self._log_critical_error("restore_dolly_to_queue", e, {
                "archive_id": archive_id,
                "restored_by": restored_by
            })
            raise RuntimeError(f"Dolly geri yükleme hatası: {str(e)}")

    def restore_multiple_dollys(
        self,
        archive_ids: List[int],
        restored_by: str
    ) -> Dict[str, Any]:
        """Arşivden birden fazla dolly'yi geri sıraya al."""
        success = 0
        failed: List[Dict[str, Any]] = []
        restored_ids: List[int] = []
        
        try:
            conn = db.session.connection()
            conn.execute(text("SET IDENTITY_INSERT DollyEOLInfo ON"))
            for archive_id in archive_ids:
                with db.session.no_autoflush:
                    removed_record = DollyQueueRemoved.query.filter_by(Id=archive_id).first()
                
                if not removed_record:
                    failed.append({"archive_id": archive_id, "error": "Arşiv kaydı bulunamadı"})
                    continue
                
                existing = DollyEOLInfo.query.filter_by(
                    DollyNo=removed_record.DollyNo,
                    VinNo=removed_record.VinNo
                ).first()
                if existing:
                    failed.append({"archive_id": archive_id, "error": "Zaten sırada"})
                    continue
                
                new_record = DollyEOLInfo(
                    DollyNo=removed_record.DollyNo,
                    VinNo=removed_record.VinNo,
                    CustomerReferans=removed_record.CustomerReferans,
                    Adet=removed_record.Adet,
                    EOLName=removed_record.EOLName,
                    EOLID=removed_record.EOLID,
                    EOLDATE=removed_record.EOLDATE,
                    EOLDollyBarcode=removed_record.EOLDollyBarcode,
                    DollyOrderNo=removed_record.DollyOrderNo,
                    RECEIPTID=removed_record.RECEIPTID,
                    InsertedAt=datetime.utcnow()
                )
                
                db.session.add(new_record)
                db.session.delete(removed_record)
                
                success += 1
                restored_ids.append(archive_id)
            
            db.session.flush()
            conn.execute(text("SET IDENTITY_INSERT DollyEOLInfo OFF"))
            
            self.audit.log(
                action="queue.restore_multiple_dollys",
                resource="dolly_queue",
                resource_id="bulk_restore",
                actor_name=restored_by,
                metadata={
                    "total_requested": len(archive_ids),
                    "success_count": success,
                    "failed_count": len(failed)
                }
            )
            db.session.commit()
            
            return {
                "success_count": success,
                "failed": failed,
                "restored_ids": restored_ids
            }
        except Exception as e:
            db.session.rollback()
            self._log_critical_error("restore_multiple_dollys", e, {
                "count": len(archive_ids),
                "restored_by": restored_by
            })
            try:
                # Off in case of mid-loop failure
                db.session.connection().execute(text("SET IDENTITY_INSERT DollyEOLInfo OFF"))
            except Exception:
                pass
            raise RuntimeError(f"Toplu geri yükleme hatası: {str(e)}")
    

def _mock_entry(dolly_no: str, vin: str, eol_name: str, adet: int) -> QueueEntry:
    return QueueEntry(
        dolly_no=dolly_no,
        vin_no=vin,
        customer_ref="FORD-EXPORT",
        eol_name=eol_name,
        eol_id=eol_name,
        adet=adet,
    )
