import uuid
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.admin.models import (
    AdminAction,
    LLMProvider,
    ModelConfiguration,
    PromptTemplate,
    PromptVersion,
)
from app.modules.admin.repository import AdminRepository
from app.modules.admin.schemas import (
    LLMProviderCreate,
    LLMProviderUpdate,
    ModelConfigurationCreate,
    ModelConfigurationUpdate,
    PromptTemplateCreate,
    PromptVersionCreate,
)


class AIConfigService:
    def __init__(self, db: AsyncSession):
        self.repo = AdminRepository(db)

    # ── LLM Providers ────────────────────────────────────────────────────
    async def create_provider(
        self, admin_id: uuid.UUID, provider_in: LLMProviderCreate
    ) -> LLMProvider:
        provider = LLMProvider(
            name=provider_in.name,
            api_key_vault_ref=provider_in.api_key_vault_ref,
            is_active=provider_in.is_active,
            priority=provider_in.priority,
            failover_provider_name=provider_in.failover_provider_name,
            daily_token_limit=provider_in.daily_token_limit,
            monthly_token_limit=provider_in.monthly_token_limit,
            created_by=admin_id,
        )
        result = await self.repo.create_provider(provider)
        await self.repo.log_admin_action(
            AdminAction(
                admin_id=admin_id,
                action="create_llm_provider",
                target_type="llm_provider",
                target_id=str(result.id),
                details={"name": provider.name},
            )
        )
        return result

    async def update_provider(
        self, admin_id: uuid.UUID, provider_name: str, update_in: LLMProviderUpdate
    ) -> Optional[LLMProvider]:
        provider = await self.repo.get_provider(provider_name)
        if not provider:
            return None

        if update_in.is_active is not None:
            provider.is_active = update_in.is_active
        if update_in.priority is not None:
            provider.priority = update_in.priority
        if update_in.failover_provider_name is not None:
            provider.failover_provider_name = update_in.failover_provider_name
        if update_in.daily_token_limit is not None:
            provider.daily_token_limit = update_in.daily_token_limit
        if update_in.monthly_token_limit is not None:
            provider.monthly_token_limit = update_in.monthly_token_limit
        if update_in.provider_status is not None:
            provider.provider_status = update_in.provider_status

        provider.updated_by = admin_id
        result = await self.repo.update_provider(provider)

        await self.repo.log_admin_action(
            AdminAction(
                admin_id=admin_id,
                action="update_llm_provider",
                target_type="llm_provider",
                target_id=str(provider.id),
                details={"name": provider.name},
            )
        )
        return result

    async def get_all_providers(self) -> List[LLMProvider]:
        return await self.repo.get_all_providers()

    # ── Model Configurations ─────────────────────────────────────────────
    async def create_model_config(
        self, admin_id: uuid.UUID, model_in: ModelConfigurationCreate
    ) -> ModelConfiguration:
        config = ModelConfiguration(
            provider_name=model_in.provider_name,
            model_name=model_in.model_name,
            temperature=model_in.temperature,
            top_p=model_in.top_p,
            max_tokens=model_in.max_tokens,
            retry_count=model_in.retry_count,
            timeout=model_in.timeout,
            created_by=admin_id,
        )
        result = await self.repo.create_model_config(config)
        await self.repo.log_admin_action(
            AdminAction(
                admin_id=admin_id,
                action="create_model_config",
                target_type="model_config",
                target_id=str(result.id),
                details={"model_name": config.model_name},
            )
        )
        return result

    async def update_model_config(
        self, admin_id: uuid.UUID, model_name: str, update_in: ModelConfigurationUpdate
    ) -> Optional[ModelConfiguration]:
        config = await self.repo.get_model_config(model_name)
        if not config:
            return None

        if update_in.temperature is not None:
            config.temperature = update_in.temperature
        if update_in.top_p is not None:
            config.top_p = update_in.top_p
        if update_in.max_tokens is not None:
            config.max_tokens = update_in.max_tokens
        if update_in.retry_count is not None:
            config.retry_count = update_in.retry_count
        if update_in.timeout is not None:
            config.timeout = update_in.timeout
        if update_in.is_active is not None:
            config.is_active = update_in.is_active

        config.updated_by = admin_id
        result = await self.repo.update_model_config(config)
        await self.repo.log_admin_action(
            AdminAction(
                admin_id=admin_id,
                action="update_model_config",
                target_type="model_config",
                target_id=str(config.id),
                details={"model_name": config.model_name},
            )
        )
        return result

    async def get_all_model_configs(self) -> List[ModelConfiguration]:
        return await self.repo.get_all_model_configs()

    # ── Prompt Versioning & Rollback ─────────────────────────────────────
    async def create_prompt_template(
        self, admin_id: uuid.UUID, template_in: PromptTemplateCreate
    ) -> PromptTemplate:
        template = PromptTemplate(
            module=template_in.module, description=template_in.description, created_by=admin_id
        )
        return await self.repo.create_prompt_template(template)

    async def create_prompt_version(
        self, admin_id: uuid.UUID, pv_in: PromptVersionCreate
    ) -> PromptVersion:
        pv = PromptVersion(
            module=pv_in.module,
            version=pv_in.version,
            prompt_text=pv_in.prompt_text,
            is_active=False,
            published_by=admin_id,
            created_by=admin_id,
        )
        return await self.repo.create_prompt_version(pv)

    async def get_prompt_versions(self, module: str) -> List[PromptVersion]:
        return await self.repo.get_prompt_versions(module)

    async def rollback_prompt(
        self, admin_id: uuid.UUID, module: str, version_str: str
    ) -> Optional[PromptVersion]:
        # Activating version_str automatically deactivates current and records PromptHistory
        return await self.repo.set_active_prompt(module, version_str, admin_id)
