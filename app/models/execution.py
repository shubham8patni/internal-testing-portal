"""Execution Data Model"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class Execution(BaseModel):
    execution_id: str
    session_id: str
    session_name: str
    category: str
    product_id: str
    plan_id: str
    target_environment: str
    status: str
    timestamp: datetime
    api_calls: List[dict]
    comparisons: Optional[List[dict]] = None
    reports: dict
    has_failures: bool = False
