from __future__ import annotations

import json
from typing import Any, Optional

from flask import current_app

from ..extensions import db
from ..models import AuditLog, UserAccount, TerminalDevice


class AuditService:
    def log(
        self,
        action: str,
        resource: Optional[str] = None,
        resource_id: Optional[str] = None,
        actor_user: Optional[UserAccount] = None,
        actor_device: Optional[TerminalDevice] = None,
        actor_name: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> None:
        actor_type = "system"
        actor_id = None
        name = actor_name
        if actor_user:
            actor_type = "user"
            actor_id = actor_user.Id
            name = actor_user.DisplayName or actor_user.Username
        elif actor_device:
            actor_type = "device"
            actor_id = actor_device.Id
            name = actor_device.Name
        elif actor_name:
            name = actor_name
        payload = json.dumps(metadata, ensure_ascii=False) if metadata else None
        log = AuditLog(
            ActorType=actor_type,
            ActorId=actor_id,
            ActorName=name,
            Action=action,
            Resource=resource,
            ResourceId=resource_id,
            Payload=payload,
        )
        db.session.add(log)
        db.session.commit()
        try:
            current_app.logger.info(
                "AUDIT action=%s actor=%s resource=%s id=%s meta=%s",
                action,
                name or actor_type,
                resource or "-",
                resource_id or "-",
                payload or "",
            )
        except Exception:
            pass
