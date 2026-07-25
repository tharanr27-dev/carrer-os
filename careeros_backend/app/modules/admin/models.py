from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.db.base import AuditableBase


class PlatformSetting(AuditableBase):
    """Key-value configuration store. Every mutation creates a ConfigurationHistory row."""

    __tablename__ = "admin_platform_settings"

    key = Column(String, unique=True, index=True, nullable=False)
    value = Column(Text, nullable=True)
    value_type = Column(String, default="string")  # string, bool, int, json
    description = Column(String, nullable=True)
    version = Column(Integer, default=1, nullable=False)


class FeatureFlag(AuditableBase):
    """Runtime feature toggles — read from Redis, written through DB."""

    __tablename__ = "admin_feature_flags"

    key = Column(String, unique=True, index=True, nullable=False)
    is_enabled = Column(Boolean, default=False)
    description = Column(String, nullable=True)
    allowed_roles = Column(JSONB, nullable=True)  # e.g. ["admin", "recruiter"]
    allowed_users = Column(JSONB, nullable=True)  # user IDs list
    rollout_percentage = Column(Integer, default=100, nullable=False)  # percentage rollouts
    version = Column(Integer, default=1, nullable=False)


class FeatureFlagHistory(AuditableBase):
    """History of changes to feature flags."""

    __tablename__ = "admin_feature_flag_history"

    flag_id = Column(UUID(as_uuid=True), index=True, nullable=False)
    key = Column(String, nullable=False)
    is_enabled = Column(Boolean, nullable=False)
    allowed_roles = Column(JSONB, nullable=True)
    allowed_users = Column(JSONB, nullable=True)
    rollout_percentage = Column(Integer, nullable=False)
    changed_by = Column(UUID(as_uuid=True), nullable=True)
    change_type = Column(String, nullable=False)  # create, update, delete


class PlatformConfigurationHistory(AuditableBase):
    """History of platform settings modifications."""

    __tablename__ = "admin_platform_configuration_history"

    setting_key = Column(String, index=True, nullable=False)
    old_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=True)
    changed_by = Column(UUID(as_uuid=True), nullable=True)


class AdminSession(AuditableBase):
    """Session records for active administration dashboard logins."""

    __tablename__ = "admin_sessions"

    user_id = Column(UUID(as_uuid=True), index=True, nullable=False)
    token = Column(String, unique=True, nullable=False)
    ip_address = Column(String, nullable=True)
    device_info = Column(String, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)


class PromptTemplate(AuditableBase):
    """Definition of Prompts."""

    __tablename__ = "admin_prompt_templates"

    module = Column(String, unique=True, index=True, nullable=False)
    description = Column(String, nullable=True)
    version = Column(Integer, default=1, nullable=False)


class PromptVersion(AuditableBase):
    """Version-controlled prompt templates. Only one version per module is active."""

    __tablename__ = "admin_prompt_versions"

    module = Column(String, index=True, nullable=False)  # mentor, interviews, resumes
    version = Column(String, nullable=False)  # v1.0, v1.1
    prompt_text = Column(Text, nullable=False)
    is_active = Column(Boolean, default=False)
    published_by = Column(UUID(as_uuid=True), nullable=True)


class PromptHistory(AuditableBase):
    """Audit logging for prompt rollbacks and active changes."""

    __tablename__ = "admin_prompt_history"

    module = Column(String, nullable=False)
    action = Column(String, nullable=False)  # rollback, update_active
    from_version = Column(String, nullable=True)
    to_version = Column(String, nullable=False)
    changed_by = Column(UUID(as_uuid=True), nullable=True)


class LLMProvider(AuditableBase):
    """Configuration for LLM Providers."""

    __tablename__ = "admin_llm_providers"

    name = Column(String, unique=True, index=True, nullable=False)  # openai, gemini, claude, local
    api_key_vault_ref = Column(String, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    priority = Column(Integer, default=1, nullable=False)
    failover_provider_name = Column(String, nullable=True)
    daily_token_limit = Column(Integer, default=0, nullable=False)
    monthly_token_limit = Column(Integer, default=0, nullable=False)
    provider_status = Column(String, default="healthy", nullable=False)


class ModelConfiguration(AuditableBase):
    """Configurations associated with LLM models."""

    __tablename__ = "admin_model_configurations"

    provider_name = Column(String, index=True, nullable=False)
    model_name = Column(String, unique=True, index=True, nullable=False)
    temperature = Column(Float, default=0.7)
    top_p = Column(Float, default=1.0)
    max_tokens = Column(Integer, default=2048)
    retry_count = Column(Integer, default=3)
    timeout = Column(Integer, default=30)
    is_active = Column(Boolean, default=True, nullable=False)


class AIConfiguration(AuditableBase):
    """High level cost and usage limits for AI Platform orchestration."""

    __tablename__ = "admin_ai_configurations"

    key = Column(String, unique=True, nullable=False)
    value = Column(JSONB, nullable=False)


class ModerationQueue(AuditableBase):
    """Items pending admin review (flagged posts, reported users, etc.)."""

    __tablename__ = "admin_moderation_queue"

    entity_type = Column(
        String, index=True, nullable=False
    )  # post, comment, user, company, recruiter, college
    entity_id = Column(UUID(as_uuid=True), nullable=False)
    reason = Column(String, nullable=True)
    reported_by = Column(UUID(as_uuid=True), nullable=True)
    status = Column(String, default="pending")  # pending, reviewed, resolved, escalated
    version = Column(Integer, default=1, nullable=False)


class ModerationDecision(AuditableBase):
    """Audit trail for every moderation action taken."""

    __tablename__ = "admin_moderation_decisions"

    queue_item_id = Column(UUID(as_uuid=True), nullable=False)
    decision = Column(String, nullable=False)  # approve, reject, suspend, restore, escalate, delete
    reason = Column(Text, nullable=True)
    decided_by = Column(UUID(as_uuid=True), nullable=False)


class AdminAction(AuditableBase):
    """
    Compliance log. Every admin mutation is recorded here.
    Append-only — never updated or deleted.
    """

    __tablename__ = "admin_actions"

    admin_id = Column(UUID(as_uuid=True), index=True, nullable=False)
    action = Column(String, nullable=False)  # e.g. "update_feature_flag"
    target_type = Column(String, nullable=True)  # e.g. "feature_flag"
    target_id = Column(String, nullable=True)
    details = Column(JSONB, nullable=True)


class ConfigurationAudit(AuditableBase):
    """Detailed metadata logging for configuration changes."""

    __tablename__ = "admin_configuration_audits"

    config_type = Column(String, nullable=False)  # setting, feature_flag, ai_provider
    action = Column(String, nullable=False)
    changed_by = Column(UUID(as_uuid=True), nullable=True)
    payload = Column(JSONB, nullable=True)


class SystemHealthSnapshot(AuditableBase):
    """Point-in-time system health probes, persisted by Celery Beat."""

    __tablename__ = "admin_system_health_snapshots"

    database_ok = Column(Boolean, default=True)
    redis_ok = Column(Boolean, default=True)
    celery_ok = Column(Boolean, default=True)
    storage_ok = Column(Boolean, default=True)
    details = Column(JSONB, nullable=True)


class MaintenanceWindow(AuditableBase):
    """Scheduled maintenance windows where platform features are locked or throttled."""

    __tablename__ = "admin_maintenance_windows"

    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)
    description = Column(String, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)


class SystemAnnouncement(AuditableBase):
    """Platform-wide announcements with optional expiry."""

    __tablename__ = "admin_system_announcements"

    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    severity = Column(String, default="info")  # info, warning, critical
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    created_by_admin = Column(UUID(as_uuid=True), nullable=True)


class AdminNotification(AuditableBase):
    """Notifications targeted specifically for admins."""

    __tablename__ = "admin_notifications"

    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False, nullable=False)


class BroadcastNotification(AuditableBase):
    """Notifications broadcast to groups of platform users."""

    __tablename__ = "admin_broadcast_notifications"

    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    recipient_type = Column(String, nullable=False)  # all, students, recruiters, officers
    sent_by = Column(UUID(as_uuid=True), nullable=True)


class BackgroundJobHistory(AuditableBase):
    """Tracks history and execution state of system analytics/health background jobs."""

    __tablename__ = "admin_background_jobs_history"

    job_name = Column(String, index=True, nullable=False)
    status = Column(String, default="running")  # running, completed, failed
    started_at = Column(DateTime(timezone=True), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)


class SystemMetric(AuditableBase):
    """Pre-aggregated system metrics for dashboard charts."""

    __tablename__ = "admin_system_metrics"

    metric_name = Column(String, index=True, nullable=False)
    metric_value = Column(Float, nullable=False)
    tags = Column(JSONB, nullable=True)


class ResourceUsage(AuditableBase):
    """Memory, CPU, and Disk metrics snapshot for reporting."""

    __tablename__ = "admin_resource_usage"

    cpu_percent = Column(Float, nullable=False)
    memory_percent = Column(Float, nullable=False)
    disk_percent = Column(Float, nullable=False)
    network_latency_ms = Column(Float, nullable=True)
