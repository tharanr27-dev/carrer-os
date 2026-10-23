import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, Request, Response, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.core.responses import APIResponse, success_response
from app.db.session import get_db
from app.infrastructure.storage.local_storage import get_file_storage
from app.modules.auth.models import User
from app.modules.resumes.schemas import (
    ResumeAnalysisResponse,
    ResumeSummaryResponse,
    ResumeUploadResponse,
)
from app.modules.resumes.service import ResumeService
from app.modules.resumes.upload_validation import (
    ALLOWED_TYPES,
    MAX_RESUME_BYTES,
    safe_filename,
    validate_resume_upload,
)

router = APIRouter()


@router.get("", response_model=APIResponse[list[ResumeSummaryResponse]])
async def list_my_resumes(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """The current user's uploaded resumes, newest first."""
    service = ResumeService(db)
    resumes = await service.repository.list_resumes_for_user(current_user.id)
    req_id = getattr(request.state, "request_id", None)
    return success_response(
        data=[ResumeSummaryResponse.model_validate(r) for r in resumes], request_id=req_id
    )


@router.post("/upload", response_model=APIResponse[ResumeUploadResponse], status_code=202)
async def upload_resume(
    background_tasks: BackgroundTasks,
    request: Request,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Read at most MAX+1 bytes so an oversized upload is rejected without loading it all into memory.
    content = await file.read(MAX_RESUME_BYTES + 1)
    safe_name = validate_resume_upload(file.content_type, file.filename, content)

    service = ResumeService(db)
    resume = await service.upload_and_process(
        current_user.id, file, background_tasks, file_name=safe_name, content=content
    )

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
async def download_resume(
    resume_id: uuid.UUID,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ResumeService(db)
    resume = await service.repository.get_resume_by_id(resume_id)
    if not resume or resume.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    try:
        content = await get_file_storage().read(resume.s3_key)
    except ValueError:  # a key that tries to leave the storage root is never served
        content = None
    if content is None:
        raise HTTPException(
            status_code=404,
            detail="The original file is not available (it was uploaded before file storage was enabled).",
        )

    safe_name = safe_filename(resume.file_name, ALLOWED_TYPES.get(resume.content_type, ".pdf"))
    return Response(
        content=content,
        media_type=resume.content_type or "application/octet-stream",
        headers={
            "Content-Disposition": f'attachment; filename="{safe_name}"',
            "X-Content-Type-Options": "nosniff",
            "Cache-Control": "private, no-store",
        },
    )
