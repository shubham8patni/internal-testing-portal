"""Execution API Routes

Endpoints:
- POST /api/execution/start - Start test execution
- GET /api/execution/status/{session_id} - Get overall status
- GET /api/execution/tabs/{session_id} - Get all tabs
- GET /api/execution/progress/{session_id} - Get session progress for all executions
- GET /api/execution/{session_id}/api-call/{call_id} - Get API call details
- GET /api/execution/{session_id}/comparison/{call_id} - Get comparison results
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
import logging
import asyncio

from app.schemas.execution import (
    ExecutionStartRequest,
    ExecutionStartResponse,
    ExecutionStatusResponse,
    TabsListResponse,
    TabProgressResponse,
    ExecutionProgressResponse
)
from app.schemas.comparison import APICallDetails, ComparisonResponse
from app.services.execution_service import ExecutionService
from app.services.storage_service import StorageService
from app.services.session_service import SessionService
from app.services.config_service import ConfigService
from app.services.api_executor import APIExecutorService
from app.services.comparison_service import ComparisonService
from app.services.llm_reporter import LLMReporterService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/execution", tags=["execution"])


def get_execution_service() -> ExecutionService:
    """Dependency injection for ExecutionService."""
    storage_service = StorageService()
    session_service = SessionService()
    config_service = ConfigService()
    api_executor = APIExecutorService()
    comparison_service = ComparisonService()
    llm_reporter = LLMReporterService()

    return ExecutionService(
        storage_service=storage_service,
        session_service=session_service,
        config_service=config_service,
        api_executor=api_executor,
        comparison_service=comparison_service,
        llm_reporter=llm_reporter
    )


@router.post("/start", response_model=ExecutionStartResponse, status_code=202)
async def start_execution(
    request: ExecutionStartRequest,
    execution_service: ExecutionService = Depends(get_execution_service)
):
    """
    Start a new test execution with multiple Category+Product+Plan combinations.

    Args:
        request: Execution start request with session_id, categories, auth tokens

    Returns:
        ExecutionStartResponse with session_id and list of execution IDs

    Raises:
        HTTPException: If session not found (404)
    """
    try:
        execution_ids = execution_service.start_execution(request)
        logger.info(f"Created {len(execution_ids)} executions for test in session {request.session_id}")

        # Start sequential background execution of individual executions
        def background_execution():
            try:
                logger.info(f"[BG-EXEC] Starting sequential execution of {len(execution_ids)} executions for session {request.session_id}")
                for i, execution_id in enumerate(execution_ids):
                    try:
                        logger.info(f"[BG-EXEC] Starting execution {i+1}/{len(execution_ids)}: {execution_id}")

                        # Parse execution_id to get components
                        parts = execution_id.split('_')
                        category = parts[-3]
                        product_id = parts[-2]
                        plan_id = parts[-1]

                        logger.debug(f"[BG-EXEC] Parsed components - category: {category}, product: {product_id}, plan: {plan_id}")

                        execution_service.execute_single_execution(
                            execution_id=execution_id,
                            session_id=request.session_id,
                            target_env=request.target_environment,
                            category=category,
                            product_id=product_id,
                            plan_id=plan_id,
                            admin_token=request.admin_auth_token,
                            customer_token=request.customer_auth_token
                        )
                        logger.info(f"[BG-EXEC] Completed execution {i+1}/{len(execution_ids)}: {execution_id}")

                    except Exception as e:
                        logger.error(f"[BG-EXEC] Execution {execution_id} failed: {e}", exc_info=True)
                        # Continue with next execution

                logger.info(f"[BG-EXEC] All executions completed for session {request.session_id}")

            except Exception as e:
                logger.error(f"[BG-EXEC] Background execution failed for session {request.session_id}: {e}", exc_info=True)

        # Run in background thread to avoid blocking the response
        import threading
        thread = threading.Thread(target=background_execution, daemon=True)
        thread.start()
        logger.info(f"Test started with {len(execution_ids)} executions in session {request.session_id}")

        return ExecutionStartResponse(
            session_id=request.session_id,
            executions=execution_ids
        )

    except ValueError as e:
        logger.warning(f"Execution start failed: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error starting execution: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/status/{session_id}", response_model=ExecutionStatusResponse)
async def get_execution_status(
    session_id: str,
    execution_service: ExecutionService = Depends(get_execution_service)
):
    """
    Get overall execution status for a session.

    Args:
        session_id: Session identifier

    Returns:
        Overall status with counts

    Raises:
        HTTPException: If session not found (404)
    """
    try:
        status = execution_service.get_execution_status(session_id)
        return status
    except ValueError as e:
        logger.warning(f"Session not found: {session_id}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get execution status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tabs/{session_id}", response_model=TabsListResponse)
async def get_execution_tabs(
    session_id: str,
    execution_service: ExecutionService = Depends(get_execution_service)
):
    """
    Get all tabs (Category+Product+Plan combinations) for a session.

    Args:
        session_id: Session identifier

    Returns:
        List of tabs with status

    Raises:
        HTTPException: If session not found (404)
    """
    try:
        tabs = execution_service.get_execution_tabs(session_id)
        return tabs
    except ValueError as e:
        logger.warning(f"Session not found: {session_id}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get execution tabs: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/progress/{session_id}", response_model=ExecutionProgressResponse)
async def get_session_progress(
    session_id: str,
    execution_service: ExecutionService = Depends(get_execution_service)
):
    """
    Get progress for all executions in a session.

    Args:
        session_id: Session identifier

    Returns:
        Progress for all executions in the session

    Raises:
        HTTPException: If session not found (404)
    """
    try:
        progress = execution_service.get_session_progress(session_id)
        return progress
    except ValueError as e:
        logger.warning(f"Session not found: {session_id}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get session progress: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{session_id}/api-call/{call_id}", response_model=APICallDetails)
async def get_api_call(
    session_id: str,
    call_id: str,
    execution_service: ExecutionService = Depends(get_execution_service)
):
    """
    Get API call details.

    Args:
        session_id: Session identifier
        call_id: API call identifier

    Returns:
        API call details with request/response data

    Raises:
        HTTPException: If API call not found (404)
    """
    try:
        session = execution_service.session_service.get_session(session_id)

        if not session:
            raise ValueError(f"Session not found: {session_id}")

        comparisons = []

        for execution_id in session.executions:
            execution_data = storage_service.read_execution(execution_id)

            if execution_data:
                comparisons.extend(execution_data.get("comparisons", []))

        comparison = None
        target_response = None
        staging_response = None

        # Find comparison for this call
        for comp in comparisons:
            if comp.get("call_id") == call_id or call_id in comp.get("comparison_id", ""):
                comparison = comp
                break

        if not comparison:
            # Fallback: find by api_step
            api_calls = []
            for execution_id in session.executions:
                execution_data = storage_service.read_execution(execution_id)
                if execution_data:
                    api_calls.extend(execution_data.get("api_calls", []))

            target_call = None
            staging_call = None
            for call in api_calls:
                if call.get("call_id") == call_id:
                    if call.get("environment") == "STAGING":
                        staging_call = call
                    else:
                        target_call = call

            if target_call and staging_call:
                target_response = target_call.get("response_data")
                staging_response = staging_call.get("response_data")
                comparison = {
                    "comparison_id": f"cmp_{call_id}",
                    "target_environment": target_call.get("environment"),
                    "staging_environment": "STAGING",
                    "differences": [],
                    "summary": {}
                }

        if not comparison:
            logger.warning(f"Comparison not found for call: {call_id}")
            raise HTTPException(status_code=404, detail="Comparison not found")

        return ComparisonResponse(
            comparison_id=comparison.get("comparison_id"),
            call_id=call_id,
            target_environment=comparison.get("target_environment"),
            staging_environment=comparison.get("staging_environment"),
            target_response=target_response or comparison.get("target_response"),
            staging_response=staging_response or comparison.get("staging_response"),
            differences=comparison.get("differences", []),
            summary=comparison.get("summary", {})
        )

    except ValueError as e:
        logger.warning(f"Resource not found: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get API call: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{session_id}/comparison/{call_id}", response_model=ComparisonResponse)
async def get_comparison(
    session_id: str,
    call_id: str,
    execution_service: ExecutionService = Depends(get_execution_service)
):
    """
    Get comparison results for an API call.

    Args:
        session_id: Session identifier
        call_id: API call identifier

    Returns:
        Comparison results with differences

    Raises:
        HTTPException: If comparison not found (404)
    """
    try:
        session_service = SessionService()
        storage_service = StorageService()

        session = session_service.get_session(session_id)

        if not session:
            raise ValueError(f"Session not found: {session_id}")

        comparisons = []

        for execution_id in session.executions:
            execution_data = storage_service.read_execution(execution_id)

            if execution_data:
                comparisons.extend(execution_data.get("comparisons", []))

        comparison = None

        for comp in comparisons:
            if comp.get("comparison_id", "").startswith(f"cmp_{execution_id}"):
                comparison = comp
                break

        if not comparison:
            for comp in comparisons:
                call_id_parts = call_id.split("_")
                if any(part in comp.get("comparison_id", "") for part in call_id_parts):
                    comparison = comp
                    break

        if not comparison:
            logger.warning(f"Comparison not found for call: {call_id}")
            raise HTTPException(status_code=404, detail="Comparison not found")

        return ComparisonResponse(
            comparison_id=comparison.get("comparison_id"),
            call_id=call_id,
            target_environment=comparison.get("target_environment"),
            staging_environment=comparison.get("staging_environment"),
            target_response=comparison.get("target_response"),
            staging_response=comparison.get("staging_response"),
            differences=comparison.get("differences", []),
            summary=comparison.get("summary", {})
        )

    except ValueError as e:
        logger.warning(f"Resource not found: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get comparison: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
