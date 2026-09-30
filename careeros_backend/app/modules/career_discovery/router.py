import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.core.responses import APIResponse, success_response
from app.db.session import get_db
from app.modules.auth.models import User
from app.modules.career_discovery.schemas import (
    AssessmentSubmitRequest,
    AssessmentTemplateResponse,
    CareerReportResponse,
)
from app.modules.career_discovery.service import DiscoveryService

router = APIRouter()


@router.get("/templates", response_model=APIResponse[list[AssessmentTemplateResponse]])
async def list_assessment_templates(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Assessment templates with their ordered questions, so clients can render the form."""
    service = DiscoveryService(db)
    templates = await service.repository.get_templates()
    for t in templates:
        t.questions.sort(key=lambda q: q.order_index or 0)
    req_id = getattr(request.state, "request_id", None)
    return success_response(
        data=[AssessmentTemplateResponse.model_validate(t) for t in templates],
        request_id=req_id,
    )


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
    # The submit endpoint hands back an assessment_id; accept either id so clients can poll
    # for the AI-generated report without a separate lookup.
    report = await service.repository.get_report_by_id(report_id)
    if not report:
        report = await service.repository.get_report_by_assessment_id(report_id)

    if not report:
        raise HTTPException(status_code=404, detail="Report not found or still processing")

    if report.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    req_id = getattr(request.state, "request_id", None)
    return success_response(data=CareerReportResponse.model_validate(report), request_id=req_id)
