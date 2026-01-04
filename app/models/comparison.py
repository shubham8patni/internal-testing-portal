"""Comparison Data Model"""

from datetime import datetime
from typing import List, Any, Optional
from pydantic import BaseModel, Field


class Difference(BaseModel):
    field_path: str
    target_value: Any
    staging_value: Any
    severity: str
    description: str


class Comparison(BaseModel):
    comparison_id: str
    execution_id: str
    timestamp: datetime = Field(default_factory=datetime.now)
    api_step: str
    target_environment: str
    staging_environment: str
    target_response: Optional[dict] = None
    staging_response: Optional[dict] = None
    differences: List[Difference]
    summary: dict
