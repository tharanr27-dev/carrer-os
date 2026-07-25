import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.modules.learning.models import (
    LearningModule,
    LearningReport,
    LearningRoadmap,
    LearningTask,
    SkillProgress,
)


class LearningRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    # ------------------------------------------------------------------
    # Roadmap
    # ------------------------------------------------------------------

    async def create_roadmap(self, roadmap: LearningRoadmap) -> LearningRoadmap:
        self.session.add(roadmap)
        await self.session.commit()
        await self.session.refresh(roadmap)
        return roadmap

    async def get_active_roadmap(self, user_id: uuid.UUID) -> LearningRoadmap | None:
        stmt = (
            select(LearningRoadmap)
            .options(selectinload(LearningRoadmap.modules).selectinload(LearningModule.tasks))
            .where(LearningRoadmap.user_id == user_id, LearningRoadmap.status == "ACTIVE")
            .order_by(LearningRoadmap.version.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    # ------------------------------------------------------------------
    # Module & Task
    # ------------------------------------------------------------------

    async def bulk_create_modules_and_tasks(
        self, roadmap_id: uuid.UUID, modules: list[LearningModule]
    ) -> None:
        for module in modules:
            module.roadmap_id = roadmap_id
            self.session.add(module)

        await self.session.commit()

    async def complete_task(self, task_id: uuid.UUID) -> LearningTask | None:
        result = await self.session.execute(select(LearningTask).where(LearningTask.id == task_id))
        task = result.scalars().first()
        if task:
            task.status = "COMPLETED"
            await self.session.commit()
        return task

    # ------------------------------------------------------------------
    # Skill Progress
    # ------------------------------------------------------------------

    async def upsert_skill_progress(self, skill: SkillProgress) -> SkillProgress:
        stmt = select(SkillProgress).where(
            SkillProgress.user_id == skill.user_id, SkillProgress.skill_name == skill.skill_name
        )
        result = await self.session.execute(stmt)
        existing = result.scalars().first()

        if existing:
            existing.current_level = skill.current_level
            existing.learning_hours += skill.learning_hours
        else:
            self.session.add(skill)

        await self.session.commit()
        return existing or skill

    # ------------------------------------------------------------------
    # Report
    # ------------------------------------------------------------------

    async def save_report(self, report: LearningReport) -> LearningReport:
        self.session.add(report)
        await self.session.commit()
        await self.session.refresh(report)
        return report
