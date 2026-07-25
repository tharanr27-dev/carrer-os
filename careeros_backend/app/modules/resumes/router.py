import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, Request, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.core.responses import APIResponse, success_response
from app.db.session import get_db
from app.infrastructure.storage.s3_client import s3_client
from app.modules.auth.models import User
from app.modules.resumes.schemas import ResumeAnalysisResponse, ResumeUploadResponse
from app.modules.resumes.service import ResumeService

router = APIRouter()

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB


@router.post("/upload", response_model=APIResponse[ResumeUploadResponse], status_code=202)
async def upload_resume(
    background_tasks: BackgroundTasks,
    request: Request,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if file.content_type not in [
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ]:
        raise HTTPException(
            status_code=400, detail="Invalid file type. Only PDF and DOCX are supported."
        )

    service = ResumeService(db)
    resume = await service.upload_and_process(current_user.id, file, background_tasks)

    req_id = getattr(request.state, "request_id", None)
    return success_response(
        data=ResumeUploadResponse(
            id=resume.id,
            file_name=resume.file_name,
            status=resume.status,
            message="Resume uploaded and queued for AI analysis.",
        ),
        message="Upload Accepted",
        request_id=req_id,
    )


@router.get("/{resume_id}/analysis", response_model=APIResponse[ResumeAnalysisResponse])
async def get_resume_analysis(
    resume_id: uuid.UUID,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ResumeService(db)

    # RBAC & Ownership Validation
    resume = await service.repository.get_resume_by_id(resume_id)
    if not resume or resume.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    analysis = await service.repository.get_latest_analysis(resume_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not ready or failed.")

    req_id = getattr(request.state, "request_id", None)
    return success_response(data=ResumeAnalysisResponse.model_validate(analysis), request_id=req_id)


@router.get("/{resume_id}/download")
async def get_resume_download_link(
    resume_id: uuid.UUID,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ResumeService(db)
    resume = await service.repository.get_resume_by_id(resume_id)
    if not resume or resume.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    presigned_url = await s3_client.generate_presigned_url(resume.s3_key)

    req_id = getattr(request.state, "request_id", None)
    return success_response(data={"url": presigned_url}, request_id=req_id)
