import logging
import uuid

from fastapi import BackgroundTasks, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal
from app.infrastructure.cache.redis import get_redis
from app.infrastructure.storage.local_storage import get_file_storage
from app.modules.audit.service import AuditService
from app.modules.resumes.ai_analyzer import AIResumeAnalyzer
from app.modules.resumes.models import Resume, ResumeAnalysis, ResumeMetadata, ResumeSuggestion
from app.modules.resumes.repository import ResumeRepository
from app.modules.resumes.text_extraction import extract_text

logger = logging.getLogger("careeros")


class ResumeService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = ResumeRepository(session)
        self.audit_service = AuditService(session)
        self.ai_analyzer = AIResumeAnalyzer()

    async def upload_and_process(
        self,
        user_id: uuid.UUID,
        file: UploadFile,
        background_tasks: BackgroundTasks,
        *,
        file_name: str | None = None,
        content: bytes | None = None,
    ) -> Resume:
        # `file_name` / `content` are the validated values from the router (sanitised name, size-capped bytes).
        file_name = file_name or file.filename
        # 1. Generate the storage key and save the DB record (status: PROCESSING).
        #    The column is still called s3_key for schema compatibility; it holds the local storage key.
        s3_key = f"users/{user_id}/resumes/{uuid.uuid4()}_{file_name}"

        resume = await self.repository.create_resume(
            Resume(
                user_id=user_id,
                file_name=file_name,
                s3_key=s3_key,
                content_type=file.content_type,
            )
        )

        # 2. File bytes were already read (and size-limited) by the router.
        file_content = content if content is not None else await file.read()

        # 3. Offload storage + analysis to a background task. Pass only primitive data: the task opens its
        #    own DB session because the request-scoped session is closed before it runs.
        background_tasks.add_task(
            self._async_pipeline_isolated,
            user_id,
            resume.id,
            file_content,
            s3_key,
            file_name,
        )

        return resume

    async def process_existing_file(self, resume: Resume, file_content: bytes) -> ResumeAnalysis:
        return await execute_resume_pipeline(
            session=self.session,
            repository=self.repository,
            audit_service=self.audit_service,
            ai_analyzer=self.ai_analyzer,
            user_id=resume.user_id,
            resume_id=resume.id,
            file_content=file_content,
            s3_key=resume.s3_key,
            file_name=resume.file_name,
            content_type=resume.content_type or "application/pdf",
            save_file=False,
        )

    async def _async_pipeline_isolated(
        self,
        user_id: uuid.UUID,
        resume_id: uuid.UUID,
        file_content: bytes,
        s3_key: str,
        file_name: str,
    ):
        """Store the file, extract its text, run the rule-based analysis and persist the derived results."""
        async with AsyncSessionLocal() as session:
            repository = ResumeRepository(session)
            audit_service = AuditService(session)
            ai_analyzer = AIResumeAnalyzer()

            try:
                resume = await repository.get_resume_by_id(resume_id)
                content_type = resume.content_type if resume else "application/pdf"
                await execute_resume_pipeline(
                    session=session,
                    repository=repository,
                    audit_service=audit_service,
                    ai_analyzer=ai_analyzer,
                    user_id=user_id,
                    resume_id=resume_id,
                    file_content=file_content,
                    s3_key=s3_key,
                    file_name=file_name,
                    content_type=content_type,
                    save_file=True,
                )
            except Exception:
                logger.exception("Resume pipeline failed for resume %s", resume_id)
                try:
                    await session.rollback()
                    await repository.update_resume_status(resume_id, "FAILED")
                except Exception:
                    logger.exception("Failed to mark resume %s as FAILED", resume_id)


async def _resolve_target_role(session: AsyncSession, user_id: uuid.UUID) -> str | None:
    try:
        async with session.begin_nested():
            from app.modules.training.models import TrainingProfile

            res = await session.execute(
                select(TrainingProfile.target_role).where(TrainingProfile.user_id == user_id)
            )
            val = res.scalar_one_or_none()
            if val:
                return val
    except Exception:
        pass

    try:
        async with session.begin_nested():
            from app.modules.roadmaps.models import LearningRoadmap

            res = await session.execute(
                select(LearningRoadmap.target_role).where(LearningRoadmap.user_id == user_id).limit(1)
            )
            val = res.scalar_one_or_none()
            if val:
                return val
    except Exception:
        pass

    try:
        async with session.begin_nested():
            from app.modules.profile.models import Profile

            res = await session.execute(
                select(Profile.headline).where(Profile.user_id == user_id).limit(1)
            )
            val = res.scalar_one_or_none()
            if val:
                return val
    except Exception:
        pass

    return None


async def execute_resume_pipeline(
    session: AsyncSession,
    repository: ResumeRepository,
    audit_service: AuditService,
    ai_analyzer: AIResumeAnalyzer,
    user_id: uuid.UUID,
    resume_id: uuid.UUID,
    file_content: bytes,
    s3_key: str,
    file_name: str,
    content_type: str = "application/pdf",
    save_file: bool = True,
) -> ResumeAnalysis:
    if save_file:
        await get_file_storage().save(s3_key, file_content)

    try:
        await audit_service.log_action(
            user_id=user_id,
            action="RESUME_UPLOADED",
            entity_type="Resume",
            entity_id=str(resume_id),
        )
    except Exception:
        logger.debug("Failed to log audit for resume upload %s", resume_id)

    extraction = extract_text(content_type, file_content)
    target_role = await _resolve_target_role(session, user_id)
    ai_result = await ai_analyzer.analyze_resume_text(
        extraction.text, target_role=target_role, warnings=extraction.warnings
    )

    await repository.save_metadata(
        ResumeMetadata(
            resume_id=resume_id,
            parsed_content={
                "method": extraction.method,
                "pages": extraction.pages,
                "word_count": len(extraction.text.split()),
                "text_extracted": extraction.ok,
            },
            extracted_skills={"skills": ai_result.extracted_skills, "method": "text_match_v1"},
        )
    )
    analysis = ResumeAnalysis(
        resume_id=resume_id,
        ats_score=ai_result.ats_score,
        grammar_score=ai_result.grammar_score,
        quality_score=ai_result.quality_score,
        keyword_analysis=ai_result.keyword_analysis,
    )
    suggestions = [
        ResumeSuggestion(
            category=sug.category,
            suggestion_text=sug.suggestion_text,
            impact=sug.impact,
        )
        for sug in ai_result.suggestions
    ]
    saved_analysis = await repository.save_analysis(analysis, suggestions)
    await repository.update_resume_status(resume_id, "COMPLETED")

    try:
        redis = await get_redis()
        await redis.delete(f"user:{user_id}:resumes")
    except Exception:
        pass

    return saved_analysis

