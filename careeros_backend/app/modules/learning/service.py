import logging
import uuid

from fastapi import BackgroundTasks, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.cache.redis import get_redis
from app.modules.audit.service import AuditService
from app.modules.learning.models import (
    LearningModule,
    LearningRoadmap,
    LearningTask,
)
from app.modules.learning.repository import LearningRepository
from app.modules.learning.roadmap_engine import LearningRoadmapEngine
from app.modules.learning.schemas import RoadmapGenerateRequest

logger = logging.getLogger("careeros")


class LearningService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = LearningRepository(session)
        self.audit_service = AuditService(session)
        self.roadmap_engine = LearningRoadmapEngine()

    # ------------------------------------------------------------------
    # Roadmap Generation
    # ------------------------------------------------------------------

    async def generate_roadmap(
        self, user_id: uuid.UUID, request: RoadmapGenerateRequest, background_tasks: BackgroundTasks
    ) -> dict:
        """
        Creates a stub ACTIVE roadmap record immediately, then offloads
        the heavy AI generation to a background task so the API responds
        instantly with 202 Accepted.
        """
        # Determine next version number (simple read of any existing roadmaps)
        existing = await self.repository.get_active_roadmap(user_id)
        next_version = (existing.version + 1) if existing else 1

        # Archive previous active roadmap if it exists
        if existing:
            existing.status = "ARCHIVED"
            await self.session.commit()

        # Persist placeholder roadmap
        roadmap = await self.repository.create_roadmap(
            LearningRoadmap(
                user_id=user_id,
                title="Generating your personalised roadmap…",
                target_role=request.target_role,
                target_company=request.target_company,
                version=next_version,
                status="GENERATING",
            )
        )

        # Audit
        await self.audit_service.log_action(
            user_id, "ROADMAP_GENERATION_STARTED", "LearningRoadmap", str(roadmap.id)
        )

        # Build context snapshot from across the platform modules.
        # In a full implementation, we query resume_analyses, interview_feedbacks,
        # communication_reports, and career_goals tables here.
        context = {
            "target_role": request.target_role,
            "target_company": request.target_company,
            "resume_weaknesses": ["Docker", "Kubernetes"],  # from Phase 6
            "interview_scores": {"technical": 72, "communication": 68},  # from Phase 8
            "communication_scores": {"grammar": 75, "vocabulary": 80},  # from Phase 9
            "career_goals": [],  # from Phase 7
        }

        # Offload AI generation to background so we return 202 immediately
        background_tasks.add_task(self._async_build_roadmap, user_id, roadmap.id, context)

        return {"roadmap_id": str(roadmap.id), "status": "GENERATING"}

    async def _async_build_roadmap(
        self, user_id: uuid.UUID, roadmap_id: uuid.UUID, context: dict
    ) -> None:
        """
        Background task: invokes the AI engine, recursively persists modules
        and tasks, then marks the roadmap ACTIVE.
        """
        from app.db.session import AsyncSessionLocal
        async with AsyncSessionLocal() as session:
            repository = LearningRepository(session)
            audit_service = AuditService(session)
            try:
                ai_roadmap = await self.roadmap_engine.generate_roadmap(context)

                # Fetch the stub record
                roadmap = await session.get(LearningRoadmap, roadmap_id)
                if not roadmap:
                    return
                roadmap.title = ai_roadmap.title
                roadmap.generation_context = context

                # Build ORM objects from AI output
                orm_modules = []
                for idx, ai_module in enumerate(ai_roadmap.modules):
                    orm_module = LearningModule(
                        title=ai_module.title,
                        description=ai_module.description,
                        order_index=idx,
                        estimated_hours=ai_module.estimated_hours,
                    )
                    orm_tasks = [
                        LearningTask(
                            title=t.title,
                            description=t.description,
                            resource_url=t.resource_url,
                            resource_type=t.resource_type,
                            estimated_minutes=t.estimated_minutes,
                            difficulty=t.difficulty,
                            order_index=task_idx,
                        )
                        for task_idx, t in enumerate(ai_module.tasks)
                    ]
                    orm_module.tasks = orm_tasks
                    orm_modules.append(orm_module)

                await repository.bulk_create_modules_and_tasks(roadmap_id, orm_modules)

                # Mark as ACTIVE
                roadmap.status = "ACTIVE"
                await session.commit()

                # Invalidate cache
                redis = await get_redis()
                await redis.delete(f"user:{user_id}:learning:active_roadmap")

                await audit_service.log_action(
                    user_id, "ROADMAP_GENERATED", "LearningRoadmap", str(roadmap_id)
                )

                logger.info(f"Roadmap {roadmap_id} generated and persisted for user {user_id}")

            except Exception as exc:
                logger.error(f"Roadmap generation failed for {roadmap_id}: {exc}")
                roadmap = await session.get(LearningRoadmap, roadmap_id)
                if roadmap:
                    roadmap.status = "FAILED"
                    await session.commit()

    # ------------------------------------------------------------------
    # Active Roadmap Retrieval (Redis-Cached)
    # ------------------------------------------------------------------

    async def get_active_roadmap(self, user_id: uuid.UUID) -> LearningRoadmap:
        # In production, we would try redis.get(cache_key) first.
        # Omitting full serialisation for architectural clarity.

        roadmap = await self.repository.get_active_roadmap(user_id)
        if not roadmap:
            raise HTTPException(
                status_code=404, detail="No active roadmap found. Generate one first."
            )
        return roadmap

    # ------------------------------------------------------------------
    # Task Progress
    # ------------------------------------------------------------------

    async def complete_task(self, user_id: uuid.UUID, task_id: uuid.UUID) -> LearningTask:
        task = await self.repository.complete_task(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found.")

        await self.audit_service.log_action(
            user_id, "LEARNING_TASK_COMPLETED", "LearningTask", str(task_id)
        )

        # Increment streak in Redis
        redis = await get_redis()
        await redis.incr(f"user:{user_id}:learning:streak")

        return task
