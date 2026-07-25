import uuid
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.modules.admin.models import (
    AdminAction,
    BackgroundJobHistory,
    BroadcastNotification,
    FeatureFlag,
    FeatureFlagHistory,
    LLMProvider,
    MaintenanceWindow,
    ModelConfiguration,
    ModerationDecision,
    ModerationQueue,
    PlatformConfigurationHistory,
    PlatformSetting,
    PromptHistory,
    PromptTemplate,
    PromptVersion,
    ResourceUsage,
    SystemAnnouncement,
    SystemHealthSnapshot,
    SystemMetric,
)


class AdminRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    # ── Platform Settings ────────────────────────────────────────────────
    async def get_setting(self, key: str) -> Optional[PlatformSetting]:
        stmt = select(PlatformSetting).where(
            PlatformSetting.key == key, PlatformSetting.deleted_at == None
        )
        return (await self.session.execute(stmt)).scalars().first()

    async def get_all_settings(self) -> List[PlatformSetting]:
        stmt = select(PlatformSetting).where(PlatformSetting.deleted_at == None)
        return list((await self.session.execute(stmt)).scalars().all())

    async def upsert_setting(self, setting: PlatformSetting) -> PlatformSetting:
        existing = await self.get_setting(setting.key)
        if existing:
            # Platform configuration history
            hist = PlatformConfigurationHistory(
                setting_key=existing.key,
                old_value=existing.value,
                new_value=setting.value,
                changed_by=setting.updated_by,
            )
            self.session.add(hist)
            existing.value = setting.value
            existing.value_type = setting.value_type
            existing.description = setting.description
            existing.version += 1
            existing.updated_by = setting.updated_by
            await self.session.commit()
            await self.session.refresh(existing)
            return existing
        self.session.add(setting)
        await self.session.commit()
        await self.session.refresh(setting)
        return setting

    # ── Feature Flags ────────────────────────────────────────────────────
    async def get_flag(self, flag_id: uuid.UUID) -> Optional[FeatureFlag]:
        stmt = select(FeatureFlag).where(FeatureFlag.id == flag_id, FeatureFlag.deleted_at == None)
        return (await self.session.execute(stmt)).scalars().first()

    async def get_flag_by_key(self, key: str) -> Optional[FeatureFlag]:
        stmt = select(FeatureFlag).where(FeatureFlag.key == key, FeatureFlag.deleted_at == None)
        return (await self.session.execute(stmt)).scalars().first()

    async def get_all_flags(self) -> List[FeatureFlag]:
        stmt = select(FeatureFlag).where(FeatureFlag.deleted_at == None)
        return list((await self.session.execute(stmt)).scalars().all())

    async def create_flag(self, flag: FeatureFlag) -> FeatureFlag:
        self.session.add(flag)
        await self.session.commit()
        await self.session.refresh(flag)

        hist = FeatureFlagHistory(
            flag_id=flag.id,
            key=flag.key,
            is_enabled=flag.is_enabled,
            allowed_roles=flag.allowed_roles,
            allowed_users=flag.allowed_users,
            rollout_percentage=flag.rollout_percentage,
            changed_by=flag.created_by,
            change_type="create",
        )
        self.session.add(hist)
        await self.session.commit()
        return flag

    async def update_flag(self, flag: FeatureFlag) -> FeatureFlag:
        flag.version += 1
        await self.session.commit()
        await self.session.refresh(flag)

        hist = FeatureFlagHistory(
            flag_id=flag.id,
            key=flag.key,
            is_enabled=flag.is_enabled,
            allowed_roles=flag.allowed_roles,
            allowed_users=flag.allowed_users,
            rollout_percentage=flag.rollout_percentage,
            changed_by=flag.updated_by,
            change_type="update",
        )
        self.session.add(hist)
        await self.session.commit()
        return flag

    # ── LLM Providers ────────────────────────────────────────────────────
    async def get_provider(self, name: str) -> Optional[LLMProvider]:
        stmt = select(LLMProvider).where(LLMProvider.name == name, LLMProvider.deleted_at == None)
        return (await self.session.execute(stmt)).scalars().first()

    async def get_all_providers(self) -> List[LLMProvider]:
        stmt = (
            select(LLMProvider)
            .where(LLMProvider.deleted_at == None)
            .order_by(LLMProvider.priority.asc())
        )
        return list((await self.session.execute(stmt)).scalars().all())

    async def create_provider(self, provider: LLMProvider) -> LLMProvider:
        self.session.add(provider)
        await self.session.commit()
        await self.session.refresh(provider)
        return provider

    async def update_provider(self, provider: LLMProvider) -> LLMProvider:
        await self.session.commit()
        await self.session.refresh(provider)
        return provider

    # ── Model Configurations ─────────────────────────────────────────────
    async def get_model_config(self, model_name: str) -> Optional[ModelConfiguration]:
        stmt = select(ModelConfiguration).where(
            ModelConfiguration.model_name == model_name, ModelConfiguration.deleted_at == None
        )
        return (await self.session.execute(stmt)).scalars().first()

    async def get_all_model_configs(self) -> List[ModelConfiguration]:
        stmt = select(ModelConfiguration).where(ModelConfiguration.deleted_at == None)
        return list((await self.session.execute(stmt)).scalars().all())

    async def create_model_config(self, config: ModelConfiguration) -> ModelConfiguration:
        self.session.add(config)
        await self.session.commit()
        await self.session.refresh(config)
        return config

    async def update_model_config(self, config: ModelConfiguration) -> ModelConfiguration:
        await self.session.commit()
        await self.session.refresh(config)
        return config

    # ── Prompt Templates & Versions ──────────────────────────────────────
    async def get_prompt_template(self, module: str) -> Optional[PromptTemplate]:
        stmt = select(PromptTemplate).where(
            PromptTemplate.module == module, PromptTemplate.deleted_at == None
        )
        return (await self.session.execute(stmt)).scalars().first()

    async def create_prompt_template(self, template: PromptTemplate) -> PromptTemplate:
        self.session.add(template)
        await self.session.commit()
        await self.session.refresh(template)
        return template

    async def get_prompt_versions(self, module: str) -> List[PromptVersion]:
        stmt = select(PromptVersion).where(
            PromptVersion.module == module, PromptVersion.deleted_at == None
        )
        return list((await self.session.execute(stmt)).scalars().all())

    async def create_prompt_version(self, pv: PromptVersion) -> PromptVersion:
        self.session.add(pv)
        await self.session.commit()
        await self.session.refresh(pv)
        return pv

    async def get_active_prompt(self, module: str) -> Optional[PromptVersion]:
        stmt = select(PromptVersion).where(
            PromptVersion.module == module,
            PromptVersion.is_active == True,
            PromptVersion.deleted_at == None,
        )
        return (await self.session.execute(stmt)).scalars().first()

    async def set_active_prompt(
        self, module: str, version_str: str, admin_id: uuid.UUID
    ) -> Optional[PromptVersion]:
        active_prompt = await self.get_active_prompt(module)
        old_version = active_prompt.version if active_prompt else None

        # Deactivate old prompts
        await self.session.execute(
            update(PromptVersion)
            .where(PromptVersion.module == module, PromptVersion.is_active == True)
            .values(is_active=False)
        )

        # Activate new version
        stmt = select(PromptVersion).where(
            PromptVersion.module == module,
            PromptVersion.version == version_str,
            PromptVersion.deleted_at == None,
        )
        new_active = (await self.session.execute(stmt)).scalars().first()
        if new_active:
            new_active.is_active = True

            hist = PromptHistory(
                module=module,
                action="update_active",
                from_version=old_version,
                to_version=version_str,
                changed_by=admin_id,
            )
            self.session.add(hist)
            await self.session.commit()
            await self.session.refresh(new_active)
            return new_active
        await self.session.commit()
        return None

    # ── Moderation ───────────────────────────────────────────────────────
    async def get_moderation_queue(self, status: str = "pending") -> List[ModerationQueue]:
        stmt = select(ModerationQueue).where(
            ModerationQueue.status == status, ModerationQueue.deleted_at == None
        )
        return list((await self.session.execute(stmt)).scalars().all())

    async def get_moderation_item(self, item_id: uuid.UUID) -> Optional[ModerationQueue]:
        stmt = select(ModerationQueue).where(
            ModerationQueue.id == item_id, ModerationQueue.deleted_at == None
        )
        return (await self.session.execute(stmt)).scalars().first()

    async def create_moderation_decision(self, decision: ModerationDecision) -> ModerationDecision:
        self.session.add(decision)
        await self.session.commit()
        await self.session.refresh(decision)
        return decision

    # ── Admin Actions ────────────────────────────────────────────────────
    async def log_admin_action(self, action: AdminAction) -> AdminAction:
        self.session.add(action)
        await self.session.commit()
        await self.session.refresh(action)
        return action

    async def get_admin_actions(self, limit: int = 50, offset: int = 0) -> List[AdminAction]:
        stmt = (
            select(AdminAction).order_by(AdminAction.created_at.desc()).offset(offset).limit(limit)
        )
        return list((await self.session.execute(stmt)).scalars().all())

    # ── Health Snapshots ─────────────────────────────────────────────────
    async def save_health_snapshot(self, snap: SystemHealthSnapshot) -> SystemHealthSnapshot:
        self.session.add(snap)
        await self.session.commit()
        await self.session.refresh(snap)
        return snap

    async def get_latest_health(self) -> Optional[SystemHealthSnapshot]:
        stmt = (
            select(SystemHealthSnapshot).order_by(SystemHealthSnapshot.created_at.desc()).limit(1)
        )
        return (await self.session.execute(stmt)).scalars().first()

    # ── Announcements ────────────────────────────────────────────────────
    async def create_announcement(self, ann: SystemAnnouncement) -> SystemAnnouncement:
        self.session.add(ann)
        await self.session.commit()
        await self.session.refresh(ann)
        return ann

    async def get_active_announcements(self) -> List[SystemAnnouncement]:
        stmt = select(SystemAnnouncement).where(
            SystemAnnouncement.is_active == True, SystemAnnouncement.deleted_at == None
        )
        return list((await self.session.execute(stmt)).scalars().all())

    # ── Broadcast Notifications ──────────────────────────────────────────
    async def create_broadcast(self, broadcast: BroadcastNotification) -> BroadcastNotification:
        self.session.add(broadcast)
        await self.session.commit()
        await self.session.refresh(broadcast)
        return broadcast

    # ── Maintenance Windows ──────────────────────────────────────────────
    async def create_maintenance_window(self, win: MaintenanceWindow) -> MaintenanceWindow:
        self.session.add(win)
        await self.session.commit()
        await self.session.refresh(win)
        return win

    async def get_active_maintenance(self) -> Optional[MaintenanceWindow]:
        now = datetime.now(timezone.utc)
        stmt = select(MaintenanceWindow).where(
            MaintenanceWindow.start_time <= now,
            MaintenanceWindow.end_time >= now,
            MaintenanceWindow.is_active == True,
            MaintenanceWindow.deleted_at == None,
        )
        return (await self.session.execute(stmt)).scalars().first()

    # ── System Metrics & Analytics ───────────────────────────────────────
    async def add_system_metric(
        self, name: str, val: float, tags: Optional[dict] = None
    ) -> SystemMetric:
        metric = SystemMetric(metric_name=name, metric_value=val, tags=tags)
        self.session.add(metric)
        await self.session.commit()
        return metric

    async def get_latest_metrics(self, name: str, limit: int = 10) -> List[SystemMetric]:
        stmt = (
            select(SystemMetric)
            .where(SystemMetric.metric_name == name)
            .order_by(SystemMetric.created_at.desc())
            .limit(limit)
        )
        return list((await self.session.execute(stmt)).scalars().all())

    # ── Background Jobs History ──────────────────────────────────────────
    async def create_job_history(self, job: BackgroundJobHistory) -> BackgroundJobHistory:
        self.session.add(job)
        await self.session.commit()
        await self.session.refresh(job)
        return job

    async def get_job_histories(self, limit: int = 50) -> List[BackgroundJobHistory]:
        stmt = (
            select(BackgroundJobHistory)
            .order_by(BackgroundJobHistory.started_at.desc())
            .limit(limit)
        )
        return list((await self.session.execute(stmt)).scalars().all())

    # ── Resource Usage Telemetry ──────────────────────────────────────────
    async def save_resource_usage(self, resource: ResourceUsage) -> ResourceUsage:
        self.session.add(resource)
        await self.session.commit()
        await self.session.refresh(resource)
        return resource
