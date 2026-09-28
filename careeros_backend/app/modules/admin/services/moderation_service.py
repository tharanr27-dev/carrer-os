import uuid
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.modules.admin.models import AdminAction, ModerationDecision, ModerationQueue
from app.modules.admin.repository import AdminRepository
from app.modules.admin.schemas import ModerationDecisionCreate
from app.modules.auth.models import User, UserStatus


class ModerationService:
    def __init__(self, db: AsyncSession):
        self.repo = AdminRepository(db)
        self.db = db

    async def get_moderation_queue(self, status: str = "pending") -> List[ModerationQueue]:
        return await self.repo.get_moderation_queue(status)

    async def create_moderation_decision(
        self, admin_id: uuid.UUID, item_id: uuid.UUID, decision_in: ModerationDecisionCreate
    ) -> Optional[ModerationQueue]:
        item = await self.repo.get_moderation_item(item_id)
        if not item:
            return None

        # Execute Moderation Command logic based on type
        if decision_in.decision == "suspend":
            if item.entity_type == "user":
                stmt = select(User).where(User.id == item.entity_id)
                user = (await self.db.execute(stmt)).scalars().first()
                if user:
                    user.status = UserStatus.SUSPENDED
                    await self.db.commit()
        elif decision_in.decision == "restore":
            if item.entity_type == "user":
                stmt = select(User).where(User.id == item.entity_id)
                user = (await self.db.execute(stmt)).scalars().first()
                if user:
                    user.status = UserStatus.ACTIVE
                    await self.db.commit()

        # Update queue item
        item.status = "resolved"
        item.version += 1
        item.updated_by = admin_id
        await self.db.commit()

        # Record moderation decision log
        decision = ModerationDecision(
            queue_item_id=item.id,
            decision=decision_in.decision,
            reason=decision_in.reason,
            decided_by=admin_id,
            created_by=admin_id,
        )
        created_decision = await self.repo.create_moderation_decision(decision)

        # Log admin action audit
        await self.repo.log_admin_action(
            AdminAction(
                admin_id=admin_id,
                action=f"moderation_{decision_in.decision}",
                target_type=item.entity_type,
                target_id=str(item.entity_id),
                details={"reason": decision_in.reason},
            )
        )

        return created_decision
