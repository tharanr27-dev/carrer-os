import uuid
from typing import Any, Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.audit.models import AuditLog


class AuditService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def log_action(
        self,
        arg1: Any = None,
        arg2: Any = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        metadata_json: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        *,
        action: Optional[str] = None,
        user_id: Optional[uuid.UUID] = None,
    ) -> AuditLog:
        resolved_action = action
        resolved_user_id = user_id

        if resolved_action is None and resolved_user_id is None:
            if isinstance(arg1, uuid.UUID):
                resolved_user_id = arg1
                resolved_action = str(arg2) if arg2 is not None else ""
            else:
                resolved_action = str(arg1) if arg1 is not None else ""
                resolved_user_id = arg2
        elif resolved_action is None:
            resolved_action = str(arg1) if arg1 is not None else ""
        elif resolved_user_id is None and isinstance(arg1, uuid.UUID):
            resolved_user_id = arg1

        audit_log = AuditLog(
            user_id=resolved_user_id,
            action=resolved_action or "UNKNOWN",
            entity_type=entity_type,
            entity_id=str(entity_id) if entity_id is not None else None,
            metadata_json=metadata_json,
            ip_address=ip_address,
        )
        self.session.add(audit_log)
        await self.session.commit()
        await self.session.refresh(audit_log)
        return audit_log
