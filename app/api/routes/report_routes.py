"""Report API Routes

Endpoints:
- GET /api/reports/session/{session_id} - Get session report
- GET /api/reports/execution/{execution_id} - Get execution report
"""

from fastapi import APIRouter, HTTPException
import logging

from app.schemas.report import SessionSummaryReport, ExecutionReport
from app.services.execution_service import ExecutionService
from app.services.llm_reporter import LLMReporterService
from app.services.storage_service import StorageService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/reports", tags=["report"])
execution_service = ExecutionService()
reporter = LLMReporterService()
storage_service = StorageService()


@router.get("/session/{session_id}", response_model=SessionSummaryReport)
async def get_session_report(session_id: str):
    """
    Get session-level report.

    Args:
        session_id: Session identifier

    Returns:
        Session summary report

    Raises:
        HTTPException: If session not found (404)
    """
    try:
        session = execution_service.session_service.get_session(session_id)

        if not session:
            raise ValueError(f"Session not found: {session_id}")

        executions_data = []

        for execution_id in session.executions:
            execution_data.append(storage_service.read_execution(execution_id))

        report = reporter.generate_session_report(
            session_id=session_id,
            session_data=session.dict() if hasattr(session, 'dict') else session,
            executions=executions_data
        )

        return SessionSummaryReport(
            session_id=report["session_id"],
            total_executions=report["total_executions"],
            completed_executions=report["completed_executions"],
            failed_executions=report["failed_executions"],
            overall_status=report["overall_status"],
            critical_issues_count=report["critical_issues_count"],
            warnings_count=report["warnings_count"],
            summary=report["summary"]
        )

    except ValueError as e:
        logger.warning(f"Session not found: {session_id}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get session report: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/execution/{execution_id}", response_model=ExecutionReport)
async def get_execution_report(execution_id: str):
    """
    Get execution-level report.

    Args:
        execution_id: Execution identifier

    Returns:
        Execution report with breakdown

    Raises:
        HTTPException: If execution not found (404)
    """
    try:
        execution_data = storage_service.read_execution(execution_id)

        if not execution_data:
            raise ValueError(f"Execution not found: {execution_id}")

        comparisons = execution_data.get("comparisons", [])

        report = reporter.generate_execution_report(
            execution_id=execution_id,
            execution_data=execution_data,
            comparisons=comparisons
        )

        critical_issues = [
            {
                "severity": issue.severity,
                "api_step": issue.api_step,
                "description": issue.description,
                "recommendation": issue.recommendation
            }
            for issue in report.critical_issues
        ]

        recommendations = report.recommendations

        api_breakdown = [
            {
                "tab_id": bd.tab_id,
                "status": bd.status,
                "issues": bd.issues,
                "notes": bd.notes
            }
            for bd in report.api_breakdown
        ]

        return ExecutionReport(
            execution_id=execution_id,
            status=execution_data.get("status", "unknown"),
            has_failures=execution_data.get("has_failures", False),
            api_breakdown=api_breakdown,
            critical_issues=critical_issues,
            recommendations=recommendations
        )

    except ValueError as e:
        logger.warning(f"Execution not found: {execution_id}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get execution report: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
