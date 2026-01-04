"""Report Data Model"""

from datetime import datetime
from typing import List
from pydantic import BaseModel, Field


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
