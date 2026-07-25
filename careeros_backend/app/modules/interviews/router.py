import logging
import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, Request, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.core.responses import APIResponse, success_response
from app.db.session import get_db
from app.modules.auth.models import User
from app.modules.interviews.schemas import SessionCreateRequest, SessionResponse
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


@router.websocket("/ws/{session_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    session_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    # In production, we must authenticate the WebSocket connection using a short-lived token passed in the query string.
    # For architecture purposes, we assume connection is validated.
    await manager.connect(session_id, websocket)
    service = InterviewService(db)

    try:
        while True:
            data = await websocket.receive_json()
            await service.handle_websocket_event(session_id, data, background_tasks)

    except WebSocketDisconnect:
        manager.disconnect(session_id)
        logger.info(f"WebSocket Client disconnected from session {session_id}")
