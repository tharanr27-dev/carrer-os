import uuid
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.modules.admin.models import AdminAction, MaintenanceWindow
from app.modules.admin.repository import AdminRepository
from app.modules.admin.schemas import MaintenanceWindowCreate
from app.modules.auth.models import Role, User, UserStatus


class UserAdminService:
    def __init__(self, db: AsyncSession):
        self.repo = AdminRepository(db)
        self.db = db

    async def update_user_status(
        self, admin_id: uuid.UUID, user_id: uuid.UUID, status: str
    ) -> Optional[User]:
        stmt = select(User).where(User.id == user_id)
        user = (await self.db.execute(stmt)).scalars().first()
        if not user:
            return None

        old_status = user.status
        user.status = UserStatus(status)
        await self.db.commit()

        await self.repo.log_admin_action(
            AdminAction(
                admin_id=admin_id,
                action="update_user_status",
                target_type="user",
                target_id=str(user_id),
                details={"old_status": old_status, "new_status": status},
            )
        )
        return user

    async def get_users_by_role(
        self, role_name: str, limit: int = 50, offset: int = 0
    ) -> List[User]:
        stmt = (
            select(User).join(User.roles).where(Role.name == role_name).offset(offset).limit(limit)
        )
        return list((await self.db.execute(stmt)).scalars().all())

    async def assign_role(
        self, admin_id: uuid.UUID, user_id: uuid.UUID, role_name: str
    ) -> Optional[User]:
        user_stmt = select(User).where(User.id == user_id)
        user = (await self.db.execute(user_stmt)).scalars().first()
        if not user:
            return None

        role_stmt = select(Role).where(Role.name == role_name)
        role = (await self.db.execute(role_stmt)).scalars().first()
        if not role:
            return None

        if role not in user.roles:
            user.roles.append(role)
            await self.db.commit()

            await self.repo.log_admin_action(
                AdminAction(
                    admin_id=admin_id,
                    action="assign_role",
                    target_type="user_role",
                    target_id=str(user_id),
                    details={"assigned_role": role_name},
                )
            )
        return user

    # ── Maintenance Mode Control ─────────────────────────────────────────
    async def schedule_maintenance(
        self, admin_id: uuid.UUID, win_in: MaintenanceWindowCreate
    ) -> MaintenanceWindow:
        win = MaintenanceWindow(
            start_time=win_in.start_time,
            end_time=win_in.end_time,
            description=win_in.description,
            is_active=True,
            created_by=admin_id,
        )
        result = await self.repo.create_maintenance_window(win)

        await self.repo.log_admin_action(
            AdminAction(
                admin_id=admin_id,
                action="schedule_maintenance",
                target_type="maintenance_window",
                target_id=str(result.id),
                details={"description": win_in.description},
            )
        )
        return result

    async def get_active_maintenance(self) -> Optional[MaintenanceWindow]:
        return await self.repo.get_active_maintenance()
