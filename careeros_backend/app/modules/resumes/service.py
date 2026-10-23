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

                # 1. Store the original privately on local disk (served only by the authenticated download route).
                await get_file_storage().save(s3_key, file_content)

                await audit_service.log_action(
                    user_id=user_id,
                    action="RESUME_UPLOADED",
                    entity_type="Resume",
                    entity_id=str(resume_id),
                )

                # 2. Real text extraction (PDF via pypdf, DOCX via the document XML).
                extraction = extract_text(content_type, file_content)

                # 3. Rule-based analysis against the student's target role (set in Interview Prep), if any.
                from app.modules.training.models import TrainingProfile

                target_role = (
                    await session.execute(
                        select(TrainingProfile.target_role).where(TrainingProfile.user_id == user_id)
                    )
                ).scalar_one_or_none()
                ai_result = await ai_analyzer.analyze_resume_text(
                    extraction.text, target_role=target_role, warnings=extraction.warnings
                )

                # 4. Persist derived data only. The raw résumé text is deliberately NOT stored in the database.
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
                await repository.save_analysis(analysis, suggestions)

                await repository.update_resume_status(resume_id, "COMPLETED")

                redis = await get_redis()
                await redis.delete(f"user:{user_id}:resumes")

            except Exception:
                logger.exception("Resume pipeline failed for resume %s", resume_id)
                await repository.update_resume_status(resume_id, "FAILED")
