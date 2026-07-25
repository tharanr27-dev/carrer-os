import uuid

from fastapi import BackgroundTasks, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal
from app.infrastructure.cache.redis import get_redis
from app.infrastructure.storage.s3_client import s3_client
from app.modules.audit.service import AuditService
from app.modules.resumes.ai_analyzer import AIResumeAnalyzer
from app.modules.resumes.models import Resume, ResumeAnalysis, ResumeMetadata, ResumeSuggestion
from app.modules.resumes.repository import ResumeRepository


class ResumeService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = ResumeRepository(session)
        self.audit_service = AuditService(session)
        self.ai_analyzer = AIResumeAnalyzer()

    async def upload_and_process(
        self, user_id: uuid.UUID, file: UploadFile, background_tasks: BackgroundTasks
    ) -> Resume:
        # 1. Generate S3 Key and Save DB Record (Status: PROCESSING)
        s3_key = f"users/{user_id}/resumes/{uuid.uuid4()}_{file.filename}"

        resume = await self.repository.create_resume(
            Resume(
                user_id=user_id,
                file_name=file.filename,
                s3_key=s3_key,
                content_type=file.content_type,
            )
        )

        # 2. Read file content into memory (Limit enforced in router)
        file_content = await file.read()

        # 3. Offload S3 Upload and AI Processing to Background Tasks.
        # Pass only primitive data – background task opens its own DB session
        # because the request-scoped session will be closed before the task runs.
        background_tasks.add_task(
            self._async_pipeline_isolated,
            user_id,
            resume.id,
            file_content,
            s3_key,
            file.filename,
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
        """
        Background task that opens its OWN DB session so it is not coupled to
        the closed request-scoped session.
        """
        async with AsyncSessionLocal() as session:
            repository = ResumeRepository(session)
            audit_service = AuditService(session)
            ai_analyzer = AIResumeAnalyzer()

            try:
                # Upload to S3
                await s3_client.upload_file(file_content, file_name, s3_key)

                # Domain Event
                await audit_service.log_action(
                    user_id=user_id,
                    action="RESUME_UPLOADED",
                    entity_type="Resume",
                    entity_id=str(resume_id),
                )

                # Simulate PDF Text Extraction
                extracted_text = (
                    "Simulated parsed resume text containing Python and FastAPI experience."
                )

                # Run AI Analysis via Global Pipeline
                ai_result = await ai_analyzer.analyze_resume_text(extracted_text)

                # Persist Metadata
                metadata = ResumeMetadata(
                    resume_id=resume_id,
                    parsed_content={"raw_text": extracted_text},
                    extracted_skills={"skills": ai_result.extracted_skills},
                )
                await repository.save_metadata(metadata)

                # Persist AI Analysis
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

                # Update Status
                await repository.update_resume_status(resume_id, "COMPLETED")

                # Cache Invalidation
                redis = await get_redis()
                await redis.delete(f"user:{user_id}:resumes")

            except Exception as e:
                await repository.update_resume_status(resume_id, "FAILED")
                raise e

