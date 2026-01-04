"""Session Service

Manages session lifecycle including creation, retrieval, and status updates.
Follows PRD requirements for session management (max 5 sessions, FIFO cleanup).
"""

from typing import List, Optional
from datetime import datetime
import logging

from app.models.session import Session
from app.schemas.session import SessionCreate, SessionResponse, SessionListResponse
from app.services.storage_service import StorageService
from app.core.config import settings

logger = logging.getLogger(__name__)


class SessionService:
    """Service for managing test sessions."""

    def __init__(self):
        self.storage = StorageService()

    def create_session(self, request: SessionCreate) -> Session:
        """
        Create a new session.

        Args:
            request: Session creation request

        Returns:
            Created Session model

        Raises:
            Exception: If session creation fails
        """
        try:
            timestamp = datetime.now()
            session_id = f"sess_{timestamp.strftime('%Y%m%d_%H%M%S')}"

            session_data = {
                "session_id": session_id,
                "user_name": request.user_name,
                "created_at": timestamp.isoformat(),
                "status": "active",
                "config": {},
                "executions": [],
                "execution_count": 0
            }

            session_list = self.storage.read_session_list()

            if len(session_list) >= settings.max_sessions:
                self.storage.cleanup_old_sessions(settings.max_sessions)
                session_list = self.storage.read_session_list()

            session_list.append({
                "session_id": session_id,
                "user_name": request.user_name,
                "created_at": timestamp.isoformat(),
                "status": "active",
                "execution_count": 0
            })

            self.storage.write_session_list(session_list)
            self.storage.write_session_data(session_id, session_data)

            logger.info(f"Session created: {session_id} by {request.user_name}")

            return Session(**session_data)

        except Exception as e:
            logger.error(f"Failed to create session: {e}", exc_info=True)
            raise

    def get_session(self, session_id: str) -> Optional[Session]:
        """
        Retrieve a session by ID.

        Args:
            session_id: Session identifier

        Returns:
            Session model or None if not found
        """
        session_data = self.storage.read_session_data(session_id)

        if not session_data:
            logger.warning(f"Session not found: {session_id}")
            return None

        return Session(**session_data)

    def get_session_list(self) -> List[SessionResponse]:
        """
        Retrieve list of all sessions.

        Returns:
            List of SessionResponse models
        """
        session_list = self.storage.read_session_list()

        return [
            SessionResponse(**session)
            for session in session_list
        ]

    def update_session_status(self, session_id: str, status: str):
        """
        Update session status.

        Args:
            session_id: Session identifier
            status: New status (active, completed, failed)
        """
        session_data = self.storage.read_session_data(session_id)

        if not session_data:
            logger.warning(f"Cannot update status - session not found: {session_id}")
            return

        session_data["status"] = status

        self.storage.write_session_data(session_id, session_data)

        session_list = self.storage.read_session_list()
        for session in session_list:
            if session["session_id"] == session_id:
                session["status"] = status
                break

        self.storage.write_session_list(session_list)
        logger.info(f"Session status updated: {session_id} -> {status}")

    def add_execution_to_session(self, session_id: str, execution_id: str):
        """
        Add an execution to a session.

        Args:
            session_id: Session identifier
            execution_id: Execution identifier
        """
        session_data = self.storage.read_session_data(session_id)

        if not session_data:
            logger.warning(f"Cannot add execution - session not found: {session_id}")
            return

        executions = session_data.get("executions", [])

        if len(executions) >= settings.max_executions_per_session:
            self.storage.cleanup_old_executions(session_id, settings.max_executions_per_session)
            session_data = self.storage.read_session_data(session_id)
            executions = session_data.get("executions", [])

        executions.append(execution_id)
        session_data["executions"] = executions
        session_data["execution_count"] = len(executions)

        self.storage.write_session_data(session_id, session_data)

        session_list = self.storage.read_session_list()
        for session in session_list:
            if session["session_id"] == session_id:
                session["executions"] = executions
                session["execution_count"] = len(executions)
                break

        self.storage.write_session_list(session_list)
        logger.debug(f"Execution added to session: {session_id} -> {execution_id}")

    def update_session_config(self, session_id: str, config: dict):
        """
        Update session configuration.

        Args:
            session_id: Session identifier
            config: Configuration dictionary
        """
        session_data = self.storage.read_session_data(session_id)

        if not session_data:
            logger.warning(f"Cannot update config - session not found: {session_id}")
            return

        session_data["config"] = config
        self.storage.write_session_data(session_id, session_data)
        logger.debug(f"Session config updated: {session_id}")
