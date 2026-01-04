"""Storage Service

Handles all JSON file storage operations for sessions, executions, and data.
Follows FIFO cleanup strategy as per PRD requirements.

Storage Structure:
- storage/sessions/session_list.json - List of all sessions
- storage/session_data/session_{id}.json - Full session data
- storage/executions/execution_{id}.json - Execution results
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


class StorageService:
    """Service for managing JSON file storage operations."""

    def __init__(self):
        self.sessions_dir = Path(settings.storage_path) / "sessions"
        self.session_data_dir = Path(settings.storage_path) / "session_data"
        self.executions_dir = Path(settings.storage_path) / "executions"

        self._ensure_directories()

    def _ensure_directories(self):
        """Create storage directories if they don't exist."""
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        self.session_data_dir.mkdir(parents=True, exist_ok=True)
        self.executions_dir.mkdir(parents=True, exist_ok=True)
        logger.debug("Storage directories ensured")

    def _atomic_write(self, file_path: Path, data: Any):
        """
        Write data to file atomically (write to temp file, then rename).

        Args:
            file_path: Path to write to
            data: Data to write (must be JSON serializable)
        """
        temp_path = file_path.with_suffix('.tmp')
        try:
            with open(temp_path, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            os.replace(temp_path, file_path)
            logger.debug(f"Atomic write successful: {file_path.name}")
        except Exception as e:
            logger.error(f"Atomic write failed for {file_path}: {e}", exc_info=True)
            raise

    def read_json(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """
        Read JSON file safely.

        Args:
            file_path: Path to read from

        Returns:
            Parsed JSON data or None if file doesn't exist
        """
        try:
            if not file_path.exists():
                logger.debug(f"File not found: {file_path}")
                return None
            with open(file_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to read {file_path}: {e}", exc_info=True)
            return None

    def write_session_list(self, sessions: List[Dict[str, Any]]):
        """
        Write session list to storage.

        Args:
            sessions: List of session dictionaries
        """
        file_path = self.sessions_dir / "session_list.json"
        self._atomic_write(file_path, sessions)
        logger.info(f"Session list written: {len(sessions)} sessions")

    def read_session_list(self) -> List[Dict[str, Any]]:
        """
        Read session list from storage.

        Returns:
            List of session dictionaries or empty list
        """
        file_path = self.sessions_dir / "session_list.json"
        data = self.read_json(file_path)
        return data if data else []

    def write_session_data(self, session_id: str, session_data: Dict[str, Any]):
        """
        Write full session data to storage.

        Args:
            session_id: Session identifier
            session_data: Complete session data
        """
        file_path = self.session_data_dir / f"session_{session_id}.json"
        self._atomic_write(file_path, session_data)
        logger.debug(f"Session data written: {session_id}")

    def read_session_data(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Read session data from storage.

        Args:
            session_id: Session identifier

        Returns:
            Session data or None if not found
        """
        file_path = self.session_data_dir / f"session_{session_id}.json"
        return self.read_json(file_path)

    def write_execution(self, execution_id: str, execution_data: Dict[str, Any]):
        """
        Write execution results to storage.

        Args:
            execution_id: Execution identifier
            execution_data: Execution results
        """
        file_path = self.executions_dir / f"execution_{execution_id}.json"
        self._atomic_write(file_path, execution_data)
        logger.debug(f"Execution data written: {execution_id}")

    def read_execution(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """
        Read execution data from storage.

        Args:
            execution_id: Execution identifier

        Returns:
            Execution data or None if not found
        """
        file_path = self.executions_dir / f"execution_{execution_id}.json"
        return self.read_json(file_path)

    def cleanup_old_sessions(self, max_sessions: int = 5):
        """
        Clean up old sessions using FIFO strategy.

        Args:
            max_sessions: Maximum number of sessions to keep
        """
        session_list = self.read_session_list()

        if len(session_list) <= max_sessions:
            logger.debug("No session cleanup needed")
            return

        sessions_to_remove = len(session_list) - max_sessions
        logger.info(f"Cleaning up {sessions_to_remove} old sessions")

        sessions_to_remove_list = session_list[:sessions_to_remove]

        for session in sessions_to_remove_list:
            session_id = session.get("session_id")
            self.delete_session(session_id)

        remaining_sessions = session_list[sessions_to_remove:]
        self.write_session_list(remaining_sessions)
        logger.info(f"Session cleanup completed. {len(remaining_sessions)} sessions remaining")

    def delete_session(self, session_id: str):
        """
        Delete session and associated data.

        Args:
            session_id: Session identifier
        """
        session_data_path = self.session_data_dir / f"session_{session_id}.json"

        try:
            if session_data_path.exists():
                session_data_path.unlink()
                logger.debug(f"Deleted session data: {session_id}")
        except Exception as e:
            logger.error(f"Failed to delete session data {session_id}: {e}", exc_info=True)

    def cleanup_old_executions(self, session_id: str, max_executions: int = 10):
        """
        Clean up old executions for a session using FIFO strategy.

        Args:
            session_id: Session identifier
            max_executions: Maximum executions per session
        """
        session_data = self.read_session_data(session_id)

        if not session_data:
            return

        executions = session_data.get("executions", [])

        if len(executions) <= max_executions:
            logger.debug(f"No execution cleanup needed for session {session_id}")
            return

        executions_to_remove = len(executions) - max_executions
        logger.info(f"Cleaning up {executions_to_remove} old executions for session {session_id}")

        executions_to_remove_list = executions[:executions_to_remove]

        for execution in executions_to_remove_list:
            execution_id = execution.get("execution_id")
            self.delete_execution(execution_id)

        remaining_executions = executions[executions_to_remove:]
        session_data["executions"] = remaining_executions
        self.write_session_data(session_id, session_data)
        logger.info(f"Execution cleanup completed for session {session_id}. {len(remaining_executions)} executions remaining")

    def delete_execution(self, execution_id: str):
        """
        Delete execution data.

        Args:
            execution_id: Execution identifier
        """
        execution_path = self.executions_dir / f"execution_{execution_id}.json"

        try:
            if execution_path.exists():
                execution_path.unlink()
                logger.debug(f"Deleted execution data: {execution_id}")
        except Exception as e:
            logger.error(f"Failed to delete execution data {execution_id}: {e}", exc_info=True)
