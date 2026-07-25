import uuid
from typing import List

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.admin.models import AdminAction, BroadcastNotification, SystemAnnouncement
from app.modules.admin.repository import AdminRepository
from app.modules.admin.schemas import AnnouncementCreate, BroadcastNotificationCreate


class AnnouncementService:
    def __init__(self, db: AsyncSession):
        self.repo = AdminRepository(db)

    async def create_announcement(
        self, admin_id: uuid.UUID, ann_in: AnnouncementCreate
    ) -> SystemAnnouncement:
        ann = SystemAnnouncement(
            title=ann_in.title,
            content=ann_in.content,
            severity=ann_in.severity,
            expires_at=ann_in.expires_at,
            created_by_admin=admin_id,
        )
        result = await self.repo.create_announcement(ann)

        await self.repo.log_admin_action(
            AdminAction(
                admin_id=admin_id,
                action="create_system_announcement",
                target_type="announcement",
                target_id=str(result.id),
                details={"title": ann_in.title},
            )
        )
        return result

    async def get_active_announcements(self) -> List[SystemAnnouncement]:
        return await self.repo.get_active_announcements()

    async def create_broadcast(
        self, admin_id: uuid.UUID, broadcast_in: BroadcastNotificationCreate
    ) -> BroadcastNotification:
        broadcast = BroadcastNotification(
            title=broadcast_in.title,
            content=broadcast_in.content,
            recipient_type=broadcast_in.recipient_type,
            sent_by=admin_id,
            created_by=admin_id,
        )
        result = await self.repo.create_broadcast(broadcast)

        # Celery background jobs can be queued here to dispatch real-time broadcast websocket tasks

        await self.repo.log_admin_action(
            AdminAction(
                admin_id=admin_id,
                action="create_broadcast_notification",
                target_type="broadcast_notification",
                target_id=str(result.id),
                details={"recipient_type": broadcast_in.recipient_type},
            )
        )
        return result
