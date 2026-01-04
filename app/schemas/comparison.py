"""Comparison Request/Response Schemas"""

from pydantic import BaseModel
from typing import List, Any, Optional, Dict
from datetime import datetime


class APICallDetails(BaseModel):
    call_id: str
    api_step: str
    environment: str
    endpoint: str
    request_payload: Optional[Dict[str, Any]] = None
    response_data: Optional[Dict[str, Any]] = None
    status_code: int
    execution_time_ms: int
    error: Optional[str] = None


class ComparisonResponse(BaseModel):
    comparison_id: str
    call_id: str
    target_environment: str
    staging_environment: str
    target_response: Optional[Dict[str, Any]] = None
    staging_response: Optional[Dict[str, Any]] = None
    differences: List[Dict[str, Any]]
    summary: Dict[str, int]


class Difference(BaseModel):
    field_path: str
    target_value: Any
    staging_value: Any
    severity: str
    description: str
