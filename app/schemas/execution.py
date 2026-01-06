"""Execution Request/Response Schemas"""

from pydantic import BaseModel, Field, validator
from typing import List, Dict
from typing import Optional, List, Dict, Any
from datetime import datetime


class ExecutionStartRequest(BaseModel):
    session_id: str
    target_environment: str
    categories: Optional[List[str]] = None
    admin_auth_token: Optional[str] = None
    customer_auth_token: Optional[str] = None

    @validator('target_environment')
    def validate_target_environment(cls, v):
        if v not in ["DEV", "QA"]:
            raise ValueError('target_environment must be either "DEV" or "QA"')
        return v


class ExecutionStartResponse(BaseModel):
    session_id: str
    executions: List[str]


class ExecutionProgressResponse(BaseModel):
    session_id: str
    executions: Dict[str, Dict[str, str]]  # execution_id -> {api_step: status}


class ExecutionStatusResponse(BaseModel):
    session_id: str
    overall_status: str
    total_executions: int
    completed_executions: int
    failed_executions: int
    in_progress_executions: int


class TabStatus(BaseModel):
    tab_id: str
    status: str
    api_calls_completed: int
    api_calls_total: int
    has_failures: bool


class TabsListResponse(BaseModel):
    session_id: str
    tabs: List[TabStatus]


class TabProgressResponse(BaseModel):
    tab_id: str
    status: str
    api_calls: List[Dict[str, Any]]
