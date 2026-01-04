"""Execution Data Model"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class Execution(BaseModel):
    execution_id: str
    session_id: str
    session_name: str
    type: str
    category: Optional[str] = None
    status: str
    timestamp: datetime
    api_calls: List[dict]
    comparisons: Optional[List[dict]] = None
    reports: dict
    has_failures: bool = False
    total_tabs: int = 0
    completed_tabs: int = 0
