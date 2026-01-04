"""Report Request/Response Schemas"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any
from typing import List, Any
from datetime import datetime


class SessionSummaryReport(BaseModel):
    session_id: str
    total_executions: int
    completed_executions: int
    failed_executions: int
    overall_status: str
    critical_issues_count: int
    warnings_count: int
    summary: str


class ExecutionReport(BaseModel):
    execution_id: str
    status: str
    has_failures: bool
    api_breakdown: List[Dict[str, str]]
    critical_issues: List[Dict[str, Any]]
    recommendations: List[str]


class APIBreakdown(BaseModel):
    tab_id: str
    status: str
    issues: List[str]
    notes: str


class Issue(BaseModel):
    severity: str
    api_step: str
    description: str
    recommendation: str


class Report(BaseModel):
    report_id: str
    execution_id: str
    timestamp: datetime = Field(default_factory=datetime.now)
    executive_summary: str
    api_breakdown: List[APIBreakdown]
    critical_issues: List[Issue]
    recommendations: List[str]
    overall_status: str
