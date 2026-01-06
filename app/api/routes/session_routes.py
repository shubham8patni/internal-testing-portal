"""Session API Routes

Endpoints:
- POST /api/session/create - Create new session
- GET /api/session/{id} - Get session details
- GET /api/session/list - List all sessions
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
import logging

from app.schemas.session import SessionCreate, SessionResponse, SessionListResponse
from app.services.session_service import SessionService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/session", tags=["session"])
session_service = SessionService()


@router.post("/create", response_model=SessionResponse, status_code=201)
def create_session(request: SessionCreate):
    """
    Create a new test session.

    Args:
        request: Session creation request with user_name

    Returns:
        Created session details
    """
    try:
        session = session_service.create_session(request)
        return SessionResponse(
            session_id=session.session_id,
            user_name=session.user_name,
            created_at=session.created_at,
            status=session.status,
            execution_count=session.execution_count
        )
    except Exception as e:
        logger.error(f"Failed to create session: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(session_id: str):
    """
    Get session details by ID.

    Args:
        session_id: Session identifier

    Returns:
        Session details

    Raises:
        HTTPException: If session not found (404)
    """
    session = session_service.get_session(session_id)

    if not session:
        logger.warning(f"Session not found: {session_id}")
        raise HTTPException(status_code=404, detail="Session not found")

    return SessionResponse(
        session_id=session.session_id,
        user_name=session.user_name,
        created_at=session.created_at,
        status=session.status,
        execution_count=session.execution_count
    )


@router.get("/list", response_model=SessionListResponse)
async def list_sessions():
    """
    List all sessions.

    Returns:
        List of all sessions
    """
    sessions = session_service.get_session_list()
    return SessionListResponse(sessions=sessions)
