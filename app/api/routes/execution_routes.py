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
from app.schemas.comparison import APICallDetails, ComparisonResponse, ApiComparisonResponse
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
    Start a new test execution with sequential Category+Product+Plan combinations.

    Uses the new ExecutionEngine for proper sequential processing with random delays,
    failure handling, and real-time progress updates.

    Args:
        request: Execution start request with session_id, categories, auth tokens

    Returns:
        ExecutionStartResponse with session_id and list of execution IDs

    Raises:
        HTTPException: If session not found (404)
    """
    try:
        # Extract username from session_id (format: username_date_timestamp)
        username = request.session_id.split('_')[0]
        logger.info(f"[API-START] Starting execution for user {username}")

        # Prepare config for execution engine
        config = {
            "categories": request.categories if request.categories else [],
            "target_environment": request.target_environment,
            "admin_auth_token": request.admin_auth_token,
            "customer_auth_token": request.customer_auth_token
        }

        # Generate execution IDs based on combinations (before actual execution)
        from app.services.config_service import ConfigService
        config_service = ConfigService()
        combinations = config_service.get_all_combinations(config["categories"])

        execution_ids = []
        for combination in combinations:
            execution_id = f"{username}_{request.target_environment.lower()}_{combination['category']}_{combination['product_id']}_{combination['plan_id']}"
            execution_ids.append(execution_id)

        logger.info(f"[API-START] Generated {len(execution_ids)} execution IDs")

        # Start execution using new ExecutionEngine
        def background_execution():
            try:
                from app.services.execution_engine import ExecutionEngine
                engine = ExecutionEngine()

                logger.info(f"[API-START] Starting sequential execution for user {username}, session {request.session_id}")
                result = engine.execute_master(username, request.session_id, config)

                if result["success"]:
                    logger.info(f"[API-START] Sequential execution completed: {result['successful_combinations']}/{result['total_combinations']} combinations successful")
                else:
                    logger.error(f"[API-START] Sequential execution failed: {result.get('error')}")

            except Exception as e:
                logger.error(f"[API-START] Background execution failed: {e}", exc_info=True)

        # Run in background thread
        import threading
        thread = threading.Thread(target=background_execution, daemon=True)
        thread.start()

        logger.info(f"[API-START] Background execution thread started for user {username}")

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
async def get_session_progress(session_id: str):
    """
    Get progress for all executions in a session.

    Reads progress from JSON files in the session directory and returns
    structured data for UI polling with proper failure handling.

    Args:
        session_id: Session identifier

    Returns:
        Progress for all executions in the session

    Raises:
        HTTPException: If session not found (404)
    """
    try:
        # Extract username from session_id (format: username_date_timestamp)
        username = session_id.split('_')[0]

        from app.services.execution_engine import ExecutionEngine
        engine = ExecutionEngine()

        progress = engine.get_session_progress(username, session_id)
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
        storage_service = StorageService()
        session_service = SessionService()

        session = session_service.get_session(session_id)

        if not session:
            raise ValueError(f"Session not found: {session_id}")

        comparisons = []
        execution_id = None  # Initialize to avoid unbound variable warning

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
        execution_id = None  # Initialize to avoid unbound variable warning

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


@router.get("/{execution_id}/compare/{api_step}", response_model=ApiComparisonResponse)
async def get_api_comparison(
    execution_id: str,
    api_step: str,
    execution_service: ExecutionService = Depends(get_execution_service)
):
    """
    Get API response comparison for target vs staging environments.

    This endpoint allows users to compare the actual API responses between
    DEV/QA (target) and STAGING environments for a specific API step.

    Args:
        execution_id: Frontend execution ID (e.g., sess_DEV_MV4_SOMPO_COMPREHENSIVE)
        api_step: API step name (application_submit, apply_coupon, etc.)

    Returns:
        Structured comparison data with both environment responses

    Raises:
        HTTPException: If execution or API step not found (404)
    """
    try:
        result = execution_service.get_api_comparison(execution_id, api_step)
        return result
    except ValueError as e:
        logger.warning(f"API comparison not found: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get API comparison: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to load comparison data")
