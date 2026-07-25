import uuid
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.modules.admin.models import AdminAction
from app.modules.admin.repository import AdminRepository
from app.modules.auth.models import Permission, Role, User


class AdminUserService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = AdminRepository(db)

    async def get_users_by_role(self, role_name: str) -> List[User]:
        stmt = select(User).join(User.roles).where(Role.name == role_name, User.deleted_at == None)
        return list((await self.db.execute(stmt)).scalars().all())

    async def get_roles(self) -> List[Role]:
        stmt = select(Role).where(Role.deleted_at == None)
        return list((await self.db.execute(stmt)).scalars().all())

    async def get_permissions(self) -> List[Permission]:
        stmt = select(Permission).where(Permission.deleted_at == None)
        return list((await self.db.execute(stmt)).scalars().all())

    async def assign_role(
        self, admin_id: uuid.UUID, user_id: uuid.UUID, role_name: str
    ) -> Optional[User]:
        user_stmt = select(User).where(User.id == user_id, User.deleted_at == None)
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
            await self.db.refresh(user)
            await self.repo.log_admin_action(
                AdminAction(
                    admin_id=admin_id,
                    action="assign_role",
                    target_type="user",
                    target_id=str(user_id),
                    details={"role": role_name},
                )
            )
        return user
