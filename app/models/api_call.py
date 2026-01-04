"""API Call Data Model"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class APICall(BaseModel):
    call_id: str
    execution_id: str
    tab_id: str
    api_step: str
    environment: str
    endpoint: str
    request_payload: dict
    response_data: dict
    status_code: int
    execution_time_ms: int
    error: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)
