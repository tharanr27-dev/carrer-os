import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.core.responses import APIResponse, success_response
from app.db.session import get_db
from app.modules.auth.models import User
from app.modules.career_discovery.schemas import AssessmentSubmitRequest, CareerReportResponse
from app.modules.career_discovery.service import DiscoveryService

router = APIRouter()


@router.post("/assessments/{template_id}/submit", response_model=APIResponse)
async def submit_assessment(
    template_id: uuid.UUID,
    submission: AssessmentSubmitRequest,
    background_tasks: BackgroundTasks,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = DiscoveryService(db)
    assessment = await service.submit_assessment(
        current_user.id, template_id, submission, background_tasks
    )
    req_id = getattr(request.state, "request_id", None)

    return success_response(
        data={"assessment_id": str(assessment.id), "status": "AI processing started"},
        message="Assessment submitted successfully",
        request_id=req_id,
    )


@router.get("/reports/{report_id}", response_model=APIResponse[CareerReportResponse])
async def get_career_report(
    report_id: uuid.UUID,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = DiscoveryService(db)
    report = await service.repository.get_report_by_id(report_id)

    if not report:
        raise HTTPException(status_code=404, detail="Report not found or still processing")

    if report.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    req_id = getattr(request.state, "request_id", None)
    return success_response(data=CareerReportResponse.model_validate(report), request_id=req_id)
