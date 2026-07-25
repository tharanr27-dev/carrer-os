from sqlalchemy import Column, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.db.base import AuditableBase


class AuditLog(AuditableBase):
    __tablename__ = "audit_logs"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    action = Column(String, nullable=False, index=True)
    entity_type = Column(String, nullable=True)  # e.g., "Resume", "Interview"
    entity_id = Column(String, nullable=True)
    metadata_json = Column(JSONB, nullable=True)
    ip_address = Column(String, nullable=True)
