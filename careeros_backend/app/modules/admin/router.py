import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import require_permissions
from app.core.responses import success_response
from app.db.session import get_db

# Schemas
from app.modules.admin.schemas import (
    AdminActionResponse,
    AdminDashboardSummary,
    AIProviderTestRequest,
    AIProviderTestResponse,
    AnnouncementCreate,
    AnnouncementResponse,
    BackgroundJobHistoryResponse,
    BroadcastNotificationCreate,
    BroadcastNotificationResponse,
    FeatureFlagCreate,
    FeatureFlagResponse,
    FeatureFlagUpdate,
    LLMProviderCreate,
    LLMProviderResponse,
    LLMProviderUpdate,
    MaintenanceWindowCreate,
    MaintenanceWindowResponse,
    ModelConfigurationCreate,
    ModelConfigurationResponse,
    ModelConfigurationUpdate,
    ModerationDecisionCreate,
    ModerationDecisionResponse,
    ModerationQueueResponse,
    PermissionResponse,
    PlatformSettingCreate,
    PlatformSettingResponse,
    PlatformSettingUpdate,
    PromptTemplateCreate,
    PromptTemplateResponse,
    PromptVersionCreate,
    PromptVersionResponse,
    RoleAssignRequest,
    RoleResponse,
    SystemHealthResponse,
    SystemHealthSnapshotResponse,
    UserStatusUpdateRequest,
)
from app.modules.admin.services.ai_config_service import AIConfigService
from app.modules.admin.services.announcement_service import AnnouncementService
from app.modules.admin.services.dashboard_service import AdminDashboardService
from app.modules.admin.services.feature_flag_service import FeatureFlagService
from app.modules.admin.services.moderation_service import ModerationService
from app.modules.admin.services.monitoring_service import MonitoringService

# Service Layers
from app.modules.admin.services.platform_config_service import PlatformConfigService
from app.modules.admin.services.user_admin_service import UserAdminService
from app.modules.auth.models import User

router = APIRouter()


# ── Platform Config settings ───────────────────────────────────────────
@router.post("/settings", response_model=PlatformSettingResponse)
async def create_setting(
    setting_in: PlatformSettingCreate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_permissions(["admin:write"])),
):
    service = PlatformConfigService(db)
    setting = await service.upsert_setting(admin.id, setting_in)
    return setting


@router.put("/settings/{key}", response_model=PlatformSettingResponse)
async def update_setting(
    key: str,
    update_in: PlatformSettingUpdate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_permissions(["admin:write"])),
):
    service = PlatformConfigService(db)
    setting = await service.update_setting(admin.id, key, update_in)
    if not setting:
        raise HTTPException(status_code=404, detail="Setting key not found")
    return setting


@router.get("/settings")
async def get_all_settings(
    db: AsyncSession = Depends(get_db), admin: User = Depends(require_permissions(["admin:read"]))
):
    service = PlatformConfigService(db)
    settings_list = await service.get_all_settings()
    return success_response(
        data=[PlatformSettingResponse.model_validate(s) for s in settings_list],
        message="Settings retrieved successfully",
    )


# ── Feature Flags ──────────────────────────────────────────────────────
@router.post("/flags", response_model=FeatureFlagResponse)
async def create_flag(
    flag_in: FeatureFlagCreate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_permissions(["admin:write"])),
):
    service = FeatureFlagService(db)
    flag = await service.create_flag(admin.id, flag_in)
    return flag


@router.put("/flags/{flag_id}", response_model=FeatureFlagResponse)
async def update_flag(
    flag_id: uuid.UUID,
    update_in: FeatureFlagUpdate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_permissions(["admin:write"])),
):
    service = FeatureFlagService(db)
    flag = await service.update_flag(admin.id, flag_id, update_in)
    if not flag:
        raise HTTPException(status_code=404, detail="Feature flag not found")
    return flag


@router.get("/flags")
async def get_all_flags(
    db: AsyncSession = Depends(get_db), admin: User = Depends(require_permissions(["admin:read"]))
):
    service = FeatureFlagService(db)
    flags = await service.get_all_flags()
    return success_response(
        data=[FeatureFlagResponse.model_validate(f) for f in flags],
        message="Feature flags retrieved successfully",
    )


# ── AI Configurations ──────────────────────────────────────────────────
@router.post("/ai/providers", response_model=LLMProviderResponse)
async def create_provider(
    provider_in: LLMProviderCreate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_permissions(["admin:write"])),
):
    service = AIConfigService(db)
    return await service.create_provider(admin.id, provider_in)


@router.put("/ai/providers/{name}", response_model=LLMProviderResponse)
async def update_provider(
    name: str,
    update_in: LLMProviderUpdate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_permissions(["admin:write"])),
):
    service = AIConfigService(db)
    provider = await service.update_provider(admin.id, name, update_in)
    if not provider:
        raise HTTPException(status_code=404, detail="AI Provider not found")
    return provider


@router.get("/ai/providers")
async def get_providers(
    db: AsyncSession = Depends(get_db), admin: User = Depends(require_permissions(["admin:read"]))
):
    service = AIConfigService(db)
    providers = await service.get_all_providers()
    return success_response(
        data=[LLMProviderResponse.model_validate(p) for p in providers],
        message="AI Providers list retrieved",
    )


@router.post("/ai/prompts", response_model=PromptTemplateResponse)
async def create_prompt_template(
    template_in: PromptTemplateCreate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_permissions(["admin:write"])),
):
    service = AIConfigService(db)
    return await service.create_prompt_template(admin.id, template_in)


@router.post("/ai/prompts/versions", response_model=PromptVersionResponse)
async def create_prompt_version(
    pv_in: PromptVersionCreate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_permissions(["admin:write"])),
):
    service = AIConfigService(db)
    return await service.create_prompt_version(admin.id, pv_in)


@router.post("/ai/prompts/rollback")
async def rollback_prompt(
    module: str,
    version: Optional[str] = None,
    target_version: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_permissions(["admin:write"])),
):
    service = AIConfigService(db)
    ver = version or target_version or "1"
    pv = await service.rollback_prompt(admin.id, module, str(ver))
    if not pv:
        raise HTTPException(status_code=404, detail="Prompt version not found or rollback failed")
    return success_response(
        data=PromptVersionResponse.model_validate(pv),
        message=f"Prompt rollback to {ver} successful",
    )


# ── Moderation ─────────────────────────────────────────────────────────
@router.get("/moderation/queue")
async def get_moderation_queue(
    status_filter: str = "pending",
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_permissions(["admin:moderator"])),
):
    service = ModerationService(db)
    queue = await service.get_moderation_queue(status_filter)
    return success_response(
        data=[ModerationQueueResponse.model_validate(item) for item in queue],
        message="Moderation queue retrieved",
    )


@router.post("/moderation/queue/{item_id}/decision")
async def decide_moderation(
    item_id: uuid.UUID,
    decision_in: ModerationDecisionCreate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_permissions(["admin:moderator"])),
):
    service = ModerationService(db)
    result = await service.create_moderation_decision(admin.id, item_id, decision_in)
    if not result:
        raise HTTPException(status_code=404, detail="Moderation queue item not found")
    return success_response(
        data=ModerationDecisionResponse.model_validate(result),
        message="Moderation action complete",
    )


# ── Announcements & Broadcasts ───────────────────────────────────────────────
@router.post("/announcements", response_model=AnnouncementResponse)
async def create_announcement(
    ann_in: AnnouncementCreate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_permissions(["admin:write"])),
):
    service = AnnouncementService(db)
    return await service.create_announcement(admin.id, ann_in)


@router.post("/broadcast", response_model=BroadcastNotificationResponse)
async def create_broadcast(
    broadcast_in: BroadcastNotificationCreate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_permissions(["admin:write"])),
):
    service = AnnouncementService(db)
    return await service.create_broadcast(admin.id, broadcast_in)


# ── Monitoring & System Health ───────────────────────────────────────────────
@router.get("/health/check", response_model=SystemHealthResponse)
async def system_health_check(
    db: AsyncSession = Depends(get_db), admin: User = Depends(require_permissions(["admin:read"]))
):
    service = MonitoringService(db)
    return await service.check_health()


# ── User Administration Control ──────────────────────────────────────────────
@router.put("/users/{user_id}/status")
async def update_user_status(
    user_id: uuid.UUID,
    payload: Optional[UserStatusUpdateRequest] = None,
    status_str: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_permissions(["admin:write"])),
):
    service = UserAdminService(db)
    resolved_status = (payload.status if payload else None) or status_str or "ACTIVE"
    user = await service.update_user_status(admin.id, user_id, resolved_status.upper())
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    status_val = user.status.value if hasattr(user.status, "value") else str(user.status)
    return success_response(
        data={"user_id": str(user.id), "status": status_val}, message="User status updated successfully"
    )


@router.post("/maintenance/schedule", response_model=MaintenanceWindowResponse)
async def schedule_maintenance(
    win_in: MaintenanceWindowCreate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_permissions(["admin:write"])),
):
    service = UserAdminService(db)
    return await service.schedule_maintenance(admin.id, win_in)


# ── Dashboard APIs ─────────────────────────────────────────────────────
@router.get("/dashboard/summary", response_model=AdminDashboardSummary)
async def get_dashboard_summary(
    db: AsyncSession = Depends(get_db), admin: User = Depends(require_permissions(["admin:read"]))
):
    service = AdminDashboardService(db)
    summary = await service.get_dashboard_summary()
    return summary


@router.post("/ai/testing/test", response_model=AIProviderTestResponse)
async def test_ai_provider(
    test_in: AIProviderTestRequest,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_permissions(["admin:write"])),
):
    service = AdminDashboardService(db)
    return await service.test_ai_provider(admin.id, test_in)


# ── Audit Log Explorer ─────────────────────────────────────────────────
@router.get("/audit/logs")
async def get_audit_logs(
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_permissions(["admin:read"])),
):
    """
    Cursor-based audit log explorer.
    Returns admin actions ordered by most recent, supporting limit/offset pagination.
    """
    from app.modules.admin.repository import AdminRepository

    repo = AdminRepository(db)
    logs = await repo.get_admin_actions(limit=limit, offset=offset)
    return success_response(
        data=[AdminActionResponse.model_validate(l) for l in logs],
        message="Audit logs retrieved",
    )


# ── Health Snapshot History ────────────────────────────────────────────
@router.get("/health/snapshots")
async def get_health_snapshots(
    db: AsyncSession = Depends(get_db), admin: User = Depends(require_permissions(["admin:read"]))
):
    """Returns the most recent system health snapshot."""
    from app.modules.admin.repository import AdminRepository

    repo = AdminRepository(db)
    snapshot = await repo.get_latest_health()
    if not snapshot:
        return success_response(data=None, message="No snapshots found")
    return success_response(
        data=SystemHealthSnapshotResponse.model_validate(snapshot),
        message="Latest health snapshot retrieved",
    )


# ── Resource Monitoring ────────────────────────────────────────────────
@router.get("/monitoring/resources")
async def get_resource_summary(
    db: AsyncSession = Depends(get_db), admin: User = Depends(require_permissions(["admin:read"]))
):
    """Live system resource usage: CPU, memory, disk, network."""
    service = MonitoringService(db)
    summary = await service.get_resource_summary()
    return success_response(data=summary, message="Resource usage summary")


# ── Background Job History ─────────────────────────────────────────────
@router.get("/monitoring/jobs")
async def get_background_job_history(
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_permissions(["admin:read"])),
):
    """Returns recent background job execution history for Celery task monitoring."""
    from app.modules.admin.repository import AdminRepository

    repo = AdminRepository(db)
    jobs = await repo.get_job_histories(limit=limit)
    return success_response(
        data=[BackgroundJobHistoryResponse.model_validate(j) for j in jobs],
        message="Background job history retrieved",
    )


# ── Role & Permission Management ───────────────────────────────────────
@router.get("/roles")
async def get_all_roles(
    db: AsyncSession = Depends(get_db), admin: User = Depends(require_permissions(["admin:read"]))
):
    """Lists all platform roles with their associated permissions."""
    from app.modules.admin.services.admin_user_service import AdminUserService

    service = AdminUserService(db)
    roles = await service.get_roles()
    return success_response(
        data=[{"id": r.id, "name": r.name, "description": r.description} for r in roles],
        message="Roles retrieved",
    )


@router.get("/permissions")
async def get_all_permissions(
    db: AsyncSession = Depends(get_db), admin: User = Depends(require_permissions(["admin:read"]))
):
    """Lists all platform-level permissions."""
    from app.modules.admin.services.admin_user_service import AdminUserService

    service = AdminUserService(db)
    perms = await service.get_permissions()
    return success_response(
        data=[{"id": p.id, "name": p.name, "description": p.description} for p in perms],
        message="Permissions retrieved",
    )


@router.post("/users/{user_id}/roles/assign")
async def assign_role_to_user(
    user_id: uuid.UUID,
    payload: Optional[RoleAssignRequest] = None,
    role_name: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_permissions(["admin:write"])),
):
    """Assign a platform role to a user. Logs the action."""
    from app.modules.admin.services.admin_user_service import AdminUserService

    service = AdminUserService(db)
    resolved_role = (payload.role_name if payload else None) or role_name
    if not resolved_role:
        raise HTTPException(status_code=422, detail="role_name required")
    user = await service.assign_role(admin.id, user_id, resolved_role)
    if not user:
        raise HTTPException(status_code=404, detail="User or role not found")
    return success_response(
        data={"user_id": str(user_id), "role": resolved_role}, message="Role assigned successfully"
    )


# ── Model Configuration ────────────────────────────────────────────────
@router.post("/ai/models", response_model=ModelConfigurationResponse)
async def create_model_config(
    model_in: ModelConfigurationCreate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_permissions(["admin:write"])),
):
    service = AIConfigService(db)
    return await service.create_model_config(admin.id, model_in)


@router.put("/ai/models/{model_name}", response_model=ModelConfigurationResponse)
async def update_model_config(
    model_name: str,
    update_in: ModelConfigurationUpdate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_permissions(["admin:write"])),
):
    service = AIConfigService(db)
    result = await service.update_model_config(admin.id, model_name, update_in)
    if not result:
        raise HTTPException(status_code=404, detail="Model configuration not found")
    return result


@router.get("/ai/models")
async def get_model_configs(
    db: AsyncSession = Depends(get_db), admin: User = Depends(require_permissions(["admin:read"]))
):
    service = AIConfigService(db)
    configs = await service.get_all_model_configs()
    return success_response(
        data=[ModelConfigurationResponse.model_validate(c) for c in configs],
        message="Model configurations retrieved",
    )


# ── Active Announcements (public endpoint for platform display) ────────
@router.get("/announcements/active")
async def get_active_announcements(
    db: AsyncSession = Depends(get_db), admin: User = Depends(require_permissions(["admin:read"]))
):
    service = AnnouncementService(db)
    anns = await service.get_active_announcements()
    return success_response(
        data=[AnnouncementResponse.model_validate(a) for a in anns],
        message="Active announcements retrieved",
    )


# ── Maintenance Status ─────────────────────────────────────────────────
@router.get("/maintenance/status")
async def get_maintenance_status(
    db: AsyncSession = Depends(get_db), admin: User = Depends(require_permissions(["admin:read"]))
):
    """Returns any currently active maintenance window."""
    from app.modules.admin.repository import AdminRepository

    repo = AdminRepository(db)
    window = await repo.get_active_maintenance()
    is_maintenance = window is not None
    return success_response(
        data={
            "is_maintenance": is_maintenance,
            "window": window,
        },
        message="Maintenance status retrieved",
    )


# ── Prompt Version Management ──────────────────────────────────────────
@router.get("/ai/prompts/{module}/versions")
async def get_prompt_versions(
    module: str,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_permissions(["admin:read"])),
):
    """Lists all prompt versions for a given module."""
    service = AIConfigService(db)
    versions = await service.get_prompt_versions(module)
    return success_response(
        data=[PromptVersionResponse.model_validate(v) for v in versions],
        message=f"Prompt versions for module '{module}'",
    )
