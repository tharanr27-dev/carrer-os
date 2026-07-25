from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


# ── Platform Settings ────────────────────────────────────────────────────────
class PlatformSettingCreate(BaseModel):
    key: str
    value: str
    value_type: str = "string"
    description: Optional[str] = None


class PlatformSettingResponse(BaseModel):
    id: UUID
    key: str
    value: Optional[str]
    value_type: str
    description: Optional[str]
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class PlatformSettingUpdate(BaseModel):
    value: str


# ── Feature Flags ────────────────────────────────────────────────────────────
class FeatureFlagCreate(BaseModel):
    key: str
    is_enabled: bool = False
    description: Optional[str] = None
    allowed_roles: Optional[List[str]] = None
    allowed_users: Optional[List[UUID]] = None
    rollout_percentage: int = 100


class FeatureFlagResponse(BaseModel):
    id: UUID
    key: str
    is_enabled: bool
    description: Optional[str]
    allowed_roles: Optional[List[str]]
    allowed_users: Optional[List[UUID]]
    rollout_percentage: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class FeatureFlagUpdate(BaseModel):
    is_enabled: bool
    allowed_roles: Optional[List[str]] = None
    allowed_users: Optional[List[UUID]] = None
    rollout_percentage: Optional[int] = None


# ── LLM Provider / Models ────────────────────────────────────────────────────
class LLMProviderCreate(BaseModel):
    name: str
    api_key_vault_ref: Optional[str] = None
    is_active: bool = True
    priority: int = 1
    failover_provider_name: Optional[str] = None
    daily_token_limit: int = 0
    monthly_token_limit: int = 0


class LLMProviderResponse(BaseModel):
    id: UUID
    name: str
    api_key_vault_ref: Optional[str]
    is_active: bool
    priority: int
    failover_provider_name: Optional[str]
    daily_token_limit: int
    monthly_token_limit: int
    provider_status: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class LLMProviderUpdate(BaseModel):
    is_active: Optional[bool] = None
    priority: Optional[int] = None
    failover_provider_name: Optional[str] = None
    daily_token_limit: Optional[int] = None
    monthly_token_limit: Optional[int] = None
    provider_status: Optional[str] = None


class ModelConfigurationCreate(BaseModel):
    provider_name: str
    model_name: str
    temperature: float = 0.7
    top_p: float = 1.0
    max_tokens: int = 2048
    retry_count: int = 3
    timeout: int = 30


class ModelConfigurationResponse(BaseModel):
    id: UUID
    provider_name: str
    model_name: str
    temperature: float
    top_p: float
    max_tokens: int
    retry_count: int
    timeout: int
    is_active: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class ModelConfigurationUpdate(BaseModel):
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    max_tokens: Optional[int] = None
    retry_count: Optional[int] = None
    timeout: Optional[int] = None
    is_active: Optional[bool] = None


# ── Prompt Versions ──────────────────────────────────────────────────────────
class PromptTemplateCreate(BaseModel):
    module: str
    description: Optional[str] = None


class PromptTemplateResponse(BaseModel):
    id: UUID
    module: str
    description: Optional[str]
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class PromptVersionCreate(BaseModel):
    module: str
    version: str
    prompt_text: str


class PromptVersionResponse(BaseModel):
    id: UUID
    module: str
    version: str
    prompt_text: str
    is_active: bool
    published_by: Optional[UUID]
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ── Moderation ───────────────────────────────────────────────────────────────
class ModerationQueueResponse(BaseModel):
    id: UUID
    entity_type: str
    entity_id: UUID
    reason: Optional[str]
    reported_by: Optional[UUID]
    status: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class ModerationDecisionCreate(BaseModel):
    decision: str  # approve, reject, suspend, restore, escalate, delete
    reason: Optional[str] = None


class ModerationDecisionResponse(BaseModel):
    id: UUID
    queue_item_id: UUID
    decision: str
    reason: Optional[str]
    decided_by: UUID
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ── System Health ────────────────────────────────────────────────────────────
class SystemHealthResponse(BaseModel):
    database_ok: bool
    redis_ok: bool
    celery_ok: bool
    storage_ok: bool
    details: Optional[Dict[str, Any]] = None
    checked_at: datetime


class MaintenanceWindowCreate(BaseModel):
    start_time: datetime
    end_time: datetime
    description: Optional[str] = None


class MaintenanceWindowResponse(BaseModel):
    id: UUID
    start_time: datetime
    end_time: datetime
    description: Optional[str]
    is_active: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ── Admin Actions / Audit ────────────────────────────────────────────────────
class AdminActionResponse(BaseModel):
    id: UUID
    admin_id: UUID
    action: str
    target_type: Optional[str]
    target_id: Optional[str]
    details: Optional[Dict[str, Any]]
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ── Announcements & Broadcasts ───────────────────────────────────────────────
class AnnouncementCreate(BaseModel):
    title: str
    content: str
    severity: str = "info"
    expires_at: Optional[datetime] = None


class AnnouncementResponse(BaseModel):
    id: UUID
    title: str
    content: str
    severity: str
    is_active: bool
    expires_at: Optional[datetime]
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class BroadcastNotificationCreate(BaseModel):
    title: str
    content: str
    recipient_type: str  # all, students, recruiters, officers


class BroadcastNotificationResponse(BaseModel):
    id: UUID
    title: str
    content: str
    recipient_type: str
    sent_by: Optional[UUID]
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ── Pre-aggregated Dashboard Analytics ───────────────────────────────────────
class AdminDashboardSummary(BaseModel):
    total_users: int
    active_users: int
    pending_moderation_count: int
    system_status: str
    unresolved_reports: int
    ai_daily_token_usage: int
    ai_monthly_cost_usd: float


# ── Audit, Background Jobs, and System Health Telemetry ─────────────────────
class AuditLogResponse(BaseModel):
    id: UUID
    admin_id: UUID
    action: str
    target_type: Optional[str]
    target_id: Optional[str]
    details: Optional[Dict[str, Any]]
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class BackgroundJobHistoryResponse(BaseModel):
    id: UUID
    job_name: str
    status: str
    started_at: datetime
    completed_at: Optional[datetime]
    error_message: Optional[str]
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class SystemHealthSnapshotResponse(BaseModel):
    id: UUID
    database_ok: bool
    redis_ok: bool
    celery_ok: bool
    storage_ok: bool
    details: Optional[Dict[str, Any]]
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class AIProviderTestRequest(BaseModel):
    provider_name: str
    model_name: str
    prompt_text: str
    temperature: float = 0.7


class AIProviderTestResponse(BaseModel):
    status: str
    response_text: str
    latency_ms: int
    tokens_used: int
