import uuid
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.admin.models import AdminAction, PlatformSetting
from app.modules.admin.repository import AdminRepository
from app.modules.admin.schemas import PlatformSettingCreate, PlatformSettingUpdate


class PlatformConfigService:
    def __init__(self, db: AsyncSession):
        self.repo = AdminRepository(db)

    async def get_all_settings(self) -> List[PlatformSetting]:
        return await self.repo.get_all_settings()

    async def get_setting(self, key: str) -> Optional[PlatformSetting]:
        return await self.repo.get_setting(key)

    async def upsert_setting(
        self, admin_id: uuid.UUID, setting_in: PlatformSettingCreate
    ) -> PlatformSetting:
        setting = PlatformSetting(
            key=setting_in.key,
            value=setting_in.value,
            value_type=setting_in.value_type,
            description=setting_in.description,
        )
        result = await self.repo.upsert_setting(setting)

        # Audit log
        await self.repo.log_admin_action(
            AdminAction(
                admin_id=admin_id,
                action="upsert_platform_setting",
                target_type="platform_setting",
                target_id=setting_in.key,
                details={"value": setting_in.value},
            )
        )

        return result

    async def update_setting(
        self, admin_id: uuid.UUID, key: str, update_in: PlatformSettingUpdate
    ) -> Optional[PlatformSetting]:
        existing = await self.repo.get_setting(key)
        if not existing:
            return None
        old_value = existing.value
        existing.value = update_in.value
        await self.repo.session.commit()
        await self.repo.session.refresh(existing)

        await self.repo.log_admin_action(
            AdminAction(
                admin_id=admin_id,
                action="update_platform_setting",
                target_type="platform_setting",
                target_id=key,
                details={"old_value": old_value, "new_value": update_in.value},
            )
        )

        return existing
