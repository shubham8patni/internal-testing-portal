"""Session Request/Response Schemas"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class SessionCreate(BaseModel):
    user_name: str = Field(..., min_length=1, max_length=100)


class SessionResponse(BaseModel):
    session_id: str
    user_name: str
    created_at: datetime
    status: str
    execution_count: int


class SessionListResponse(BaseModel):
    sessions: List[SessionResponse]
