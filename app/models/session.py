"""Session Data Model"""

from datetime import datetime
from typing import List
from pydantic import BaseModel, Field


class Session(BaseModel):
    session_id: str
    user_name: str
    created_at: datetime
    status: str
    config: dict
    executions: List[str]
    execution_count: int
