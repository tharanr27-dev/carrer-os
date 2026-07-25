import json
import uuid
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.cache.redis import get_redis
from app.modules.admin.models import AdminAction, FeatureFlag
from app.modules.admin.repository import AdminRepository
from app.modules.admin.schemas import FeatureFlagCreate, FeatureFlagUpdate


class FeatureFlagService:
    def __init__(self, db: AsyncSession):
        self.repo = AdminRepository(db)
        self.db = db

    async def _get_cache_key(self, key: str) -> str:
        return f"admin:flag:{key}"

    async def is_enabled(
        self, key: str, user_id: Optional[uuid.UUID] = None, role: Optional[str] = None
    ) -> bool:
        redis = await get_redis()
        cache_key = await self._get_cache_key(key)

        cached_val = await redis.get(cache_key)
        if cached_val is not None:
            flag_data = json.loads(cached_val)
        else:
            flag = await self.repo.get_flag_by_key(key)
            if not flag:
                return False
            flag_data = {
                "is_enabled": flag.is_enabled,
                "allowed_roles": flag.allowed_roles or [],
                "allowed_users": flag.allowed_users or [],
                "rollout_percentage": flag.rollout_percentage,
            }
            await redis.set(cache_key, json.dumps(flag_data), ex=300)

        if not flag_data["is_enabled"]:
            return False

        # User-specific whitelists
        if user_id:
            user_str = str(user_id)
            if flag_data["allowed_users"] and user_str in flag_data["allowed_users"]:
                return True

        # Role-based constraints
        if flag_data["allowed_roles"]:
            if not role or role not in flag_data["allowed_roles"]:
                return False

        # Gradual/Percentage rollouts
        if flag_data["rollout_percentage"] < 100:
            if not user_id:
                return False
            # Deterministic hash evaluation
            user_hash = hash(str(user_id)) % 100
            if user_hash >= flag_data["rollout_percentage"]:
                return False

        return True

    async def create_flag(self, admin_id: uuid.UUID, flag_in: FeatureFlagCreate) -> FeatureFlag:
        flag = FeatureFlag(
            key=flag_in.key,
            is_enabled=flag_in.is_enabled,
            description=flag_in.description,
            allowed_roles=flag_in.allowed_roles,
            allowed_users=[str(u) for u in flag_in.allowed_users] if flag_in.allowed_users else [],
            rollout_percentage=flag_in.rollout_percentage,
            created_by=admin_id,
        )
        result = await self.repo.create_flag(flag)

        await self.repo.log_admin_action(
            AdminAction(
                admin_id=admin_id,
                action="create_feature_flag",
                target_type="feature_flag",
                target_id=str(result.id),
                details={"key": flag_in.key},
            )
        )
        return result

    async def update_flag(
        self, admin_id: uuid.UUID, flag_id: uuid.UUID, update_in: FeatureFlagUpdate
    ) -> Optional[FeatureFlag]:
        flag = await self.repo.get_flag(flag_id)
        if not flag:
            return None

        if update_in.is_enabled is not None:
            flag.is_enabled = update_in.is_enabled
        if update_in.allowed_roles is not None:
            flag.allowed_roles = update_in.allowed_roles
        if update_in.allowed_users is not None:
            flag.allowed_users = [str(u) for u in update_in.allowed_users]
        if update_in.rollout_percentage is not None:
            flag.rollout_percentage = update_in.rollout_percentage

        flag.updated_by = admin_id
        result = await self.repo.update_flag(flag)

        # Invalidate Cache
        redis = await get_redis()
        await redis.delete(await self._get_cache_key(flag.key))

        await self.repo.log_admin_action(
            AdminAction(
                admin_id=admin_id,
                action="update_feature_flag",
                target_type="feature_flag",
                target_id=str(flag_id),
                details={"key": flag.key},
            )
        )
        return result

    async def get_all_flags(self) -> List[FeatureFlag]:
        return await self.repo.get_all_flags()
