import logging
import uuid

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    Request,
    WebSocket,
    WebSocketDisconnect,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_user_from_token
from app.core.responses import APIResponse, success_response
from app.db.session import get_db
from app.modules.auth.models import User
from app.modules.interviews.schemas import (
    InterviewReportResponse,
    SessionCreateRequest,
    SessionResponse,
)
from app.modules.interviews.service import InterviewService
from app.modules.interviews.websocket import manager

logger = logging.getLogger("careeros")
router = APIRouter()


@router.post("/sessions", response_model=APIResponse[SessionResponse])
async def init_session(
    payload: SessionCreateRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = InterviewService(db)
    session = await service.initialize_session(current_user.id, payload)
    req_id = getattr(request.state, "request_id", None)
    return success_response(data=SessionResponse.model_validate(session), request_id=req_id)


@router.get("/sessions/{session_id}/report", response_model=APIResponse[InterviewReportResponse])
async def get_session_report(
    session_id: uuid.UUID,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Final report for a finished interview. 404 while it is still being generated."""
    service = InterviewService(db)
    session = await service.repository.get_session(session_id)
    if not session or session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    report = await service.repository.get_report_for_session(session_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not ready yet")
    req_id = getattr(request.state, "request_id", None)
    return success_response(data=InterviewReportResponse.model_validate(report), request_id=req_id)


@router.websocket("/ws/{session_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    session_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    # Browsers cannot set headers on WebSockets, so the access token travels as ?token=...
    user = await get_user_from_token(websocket.query_params.get("token"), db)
    if user is None:
        await websocket.close(code=4401)
        return
    service = InterviewService(db)
    owned = await service.repository.get_session(session_id)
    if owned is None or owned.user_id != user.id:
        await websocket.close(code=4403)
        return
    await manager.connect(session_id, websocket)

    try:
        while True:
            data = await websocket.receive_json()
            await service.handle_websocket_event(session_id, data, background_tasks)

    except WebSocketDisconnect:
        manager.disconnect(session_id)
        logger.info(f"WebSocket Client disconnected from session {session_id}")
