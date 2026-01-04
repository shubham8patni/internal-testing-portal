"""Execution Service

Orchestrates test execution across all Category+Product+Plan combinations.
Implements sequential execution flow as per PRD requirements.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from app.models.execution import Execution
from app.schemas.execution import (
    ExecutionStartRequest,
    ExecutionStatusResponse,
    TabsListResponse,
    TabProgressResponse
)
from app.services.storage_service import StorageService
from app.services.session_service import SessionService
from app.services.config_service import ConfigService
from app.services.api_executor import APIExecutorService
from app.services.comparison_service import ComparisonService
from app.services.llm_reporter import LLMReporterService

logger = logging.getLogger(__name__)


class ExecutionService:
    """Service for orchestrating test execution."""

    def __init__(
        self,
        storage_service: StorageService = None,
        session_service: SessionService = None,
        config_service: ConfigService = None,
        api_executor: APIExecutorService = None,
        comparison_service: ComparisonService = None,
        llm_reporter: LLMReporterService = None
    ):
        self.storage = storage_service or StorageService()
        self.session_service = session_service or SessionService()
        self.config_service = config_service or ConfigService()
        self.api_executor = api_executor or APIExecutorService()
        self.comparison_service = comparison_service or ComparisonService()
        self.reporter = llm_reporter or LLMReporterService()

    def start_execution(self, request: ExecutionStartRequest) -> Execution:
        """
        Start a new test execution.

        Args:
            request: Execution start request

        Returns:
            Execution model

        Raises:
            ValueError: If session doesn't exist
        """
        try:
            session = self.session_service.get_session(request.session_id)

            if not session:
                raise ValueError(f"Session not found: {request.session_id}")

            timestamp = datetime.now()
            execution_id = f"{session.user_name}_{timestamp.strftime('%Y%m%d_%H%M%S')}"

            categories = request.categories if request.categories else ["all"]
            execution_type = "single" if len(categories) == 1 else "all"

            combinations = self.config_service.get_all_combinations(
                categories if categories != ["all"] else None
            )

            execution_data = {
                "execution_id": execution_id,
                "session_id": request.session_id,
                "session_name": session.user_name,
                "type": execution_type,
                "category": categories[0] if len(categories) == 1 else None,
                "status": "in_progress",
                "timestamp": timestamp.isoformat(),
                "api_calls": [],
                "comparisons": [],
                "reports": {},
                "has_failures": False,
                "total_tabs": len(combinations),
                "completed_tabs": 0
            }

            self.storage.write_execution(execution_id, execution_data)
            self.session_service.add_execution_to_session(
                request.session_id,
                execution_id
            )

            self.session_service.update_session_config(
                request.session_id,
                {
                    "categories": categories,
                    "admin_auth_token": request.admin_auth_token,
                    "customer_auth_token": request.customer_auth_token
                }
            )

            logger.info(
                f"Execution started: {execution_id} with {len(combinations)} combinations"
            )

            execution = Execution(**execution_data)

            return execution

        except Exception as e:
            logger.error(f"Failed to start execution: {e}", exc_info=True)
            raise

    async def execute_all_tabs(
        self,
        execution_id: str,
        session_id: str,
        categories: List[str],
        admin_token: Optional[str],
        customer_token: Optional[str]
    ):
        """
        Execute all Category+Product+Plan combinations (tabs).

        Args:
            execution_id: Execution identifier
            session_id: Session identifier
            categories: Categories to test
            admin_token: Admin authentication token
            customer_token: Customer authentication token

        Note:
            Executes sequentially as per PRD requirements.
        """
        try:
            logger.info(f"[EXECUTION] ===========================================")
            logger.info(f"[EXECUTION] Starting execution_all_tabs for {execution_id}")
            logger.info(f"[EXECUTION] Session ID: {session_id}")
            logger.info(f"[EXECUTION] Categories: {categories}")
            logger.info(f"[EXECUTION] Admin Token: {'Provided' if admin_token else 'Not provided'}")
            logger.info(f"[EXECUTION] Customer Token: {'Provided' if customer_token else 'Not provided'}")
            logger.info(f"[EXECUTION] ===========================================")

            combinations = self.config_service.get_all_combinations(
                categories if categories != ["all"] else None
            )
            logger.info(f"[EXECUTION] Generated {len(combinations)} combinations")
            logger.info(f"[EXECUTION] Combinations: {combinations}")

            if not combinations or len(combinations) == 0:
                logger.error(f"[EXECUTION] No combinations generated for {categories}")
                raise ValueError(f"No Category+Product+Plan combinations found for categories: {categories}")

            all_api_calls = []
            all_comparisons = []

            for i, combination in enumerate(combinations):
                tab_id = (
                    f"{combination['category']}_"
                    f"{combination['product_id']}_"
                    f"{combination['plan_id']}"
                )

                logger.info(f"[EXECUTION] Tab {i+1}/{len(combinations)}: {tab_id}")
                logger.info(f"[EXECUTION] Combination: {combination}")

                try:
                    logger.info(f"[EXECUTION] Calling _execute_tab for {tab_id}")
                    api_calls = self._execute_tab(
                        execution_id=execution_id,
                        tab_id=tab_id,
                        combination=combination,
                        admin_token=admin_token,
                        customer_token=customer_token
                    )
                    logger.info(f"[EXECUTION] Tab {tab_id} executed with {len(api_calls)} API calls")
                except Exception as e:
                    logger.error(f"[EXECUTION] Failed to execute tab {tab_id}: {e}", exc_info=True)
                    raise

                try:
                    logger.info(f"[EXECUTION] Calling _compare_tab_results for {tab_id}")
                    comparisons = self._compare_tab_results(
                        execution_id=execution_id,
                        api_calls=api_calls
                    )
                    logger.info(f"[EXECUTION] Tab {tab_id} compared with {len(comparisons)} comparisons")
                except Exception as e:
                    logger.error(f"[EXECUTION] Failed to compare tab {tab_id}: {e}", exc_info=True)
                    raise

                all_api_calls.extend(api_calls)
                all_comparisons.extend(comparisons)

                try:
                    logger.info(f"[EXECUTION] Updating progress for {execution_id}")
                    self._update_execution_progress(
                        execution_id=execution_id,
                        api_calls=all_api_calls,
                        comparisons=all_comparisons,
                        completed_tabs=i + 1,
                        total_tabs=len(combinations)
                    )
                    logger.info(f"[EXECUTION] Updated progress: {i+1}/{len(combinations)} tabs completed")
                except Exception as e:
                    logger.error(f"[EXECUTION] Failed to update progress for {execution_id}: {e}", exc_info=True)
                    raise

            try:
                logger.info(f"[EXECUTION] Reading execution data for report generation")
                execution_data = self.storage.read_execution(execution_id)
                logger.info(f"[EXECUTION] Generating report for {execution_id}")
                report = self.reporter.generate_execution_report(
                    execution_id=execution_id,
                    execution_data=execution_data,
                    comparisons=[c.dict() if hasattr(c, 'dict') else c for c in all_comparisons]
                )
                logger.info(f"[EXECUTION] Report generated for {execution_id}")
            except Exception as e:
                logger.error(f"[EXECUTION] Failed to generate report for {execution_id}: {e}", exc_info=True)
                raise

            try:
                logger.info(f"[EXECUTION] Finalizing execution for {execution_id}")
                self._finalize_execution(
                    execution_id=execution_id,
                    api_calls=all_api_calls,
                    comparisons=all_comparisons,
                    report=report.dict() if hasattr(report, 'dict') else report
                )
                logger.info(f"[EXECUTION] Execution finalized for {execution_id}")
            except Exception as e:
                logger.error(f"[EXECUTION] Failed to finalize execution {execution_id}: {e}", exc_info=True)
                raise

            self.session_service.update_session_status(session_id, "completed")
            logger.info(f"[EXECUTION] ===========================================")
            logger.info(f"[EXECUTION] Execution completed successfully: {execution_id}")
            logger.info(f"[EXECUTION] Total API calls: {len(all_api_calls)}")
            logger.info(f"[EXECUTION] Total comparisons: {len(all_comparisons)}")
            logger.info(f"[EXECUTION] ===========================================")
        except Exception as e:
            logger.error(f"[EXECUTION] execute_all_tabs failed for {execution_id}: {e}", exc_info=True)
            logger.error(f"[EXECUTION] Marking execution as failed")
            self._mark_execution_failed(execution_id)
            raise

    def _execute_tab(
        self,
        execution_id: str,
        tab_id: str,
        combination: Dict[str, str],
        admin_token: Optional[str],
        customer_token: Optional[str]
    ) -> List[Dict[str, Any]]:
        """
        Execute a single tab (Category+Product+Plan combination).

        Args:
            execution_id: Execution identifier
            tab_id: Tab identifier
            combination: Category, product, plan combination
            admin_token: Admin authentication token
            customer_token: Customer authentication token

        Returns:
            List of API call results
        """
        api_calls = []

        logger.info(f"[EXECUTION-TAB] ===========================================")
        logger.info(f"[EXECUTION-TAB] Executing tab {tab_id} across 3 environments (DEV, QA, STAGING)")
        logger.info(f"[EXECUTION-TAB] Combination: {combination}")
        logger.info(f"[EXECUTION-TAB] ===========================================")

        for environment in ["DEV", "QA", "STAGING"]:
            try:
                logger.info(f"[EXECUTION-TAB] Starting {tab_id} in {environment}")
                logger.info(f"[EXECUTION-TAB] API Executor: {type(self.api_executor)}")

                calls = self.api_executor.execute_7_step_flow(
                    execution_id=execution_id,
                    tab_id=tab_id,
                    environment=environment,
                    category=combination["category"],
                    product_id=combination["product_id"],
                    plan_id=combination["plan_id"],
                    admin_token=admin_token,
                    customer_token=customer_token
                )
                logger.info(f"[EXECUTION-TAB] Completed {tab_id} in {environment}: {len(calls)} API calls")

                api_calls.extend([
                    call.dict() if hasattr(call, 'dict') else call
                    for call in calls
                ])
                logger.info(f"[EXECUTION-TAB] Total API calls so far: {len(api_calls)}")

            except Exception as e:
                logger.error(
                    f"[EXECUTION-TAB] Failed to execute tab {tab_id} in {environment}: {e}",
                    exc_info=True
                )
                raise

        logger.info(f"[EXECUTION-TAB] ===========================================")
        logger.info(f"[EXECUTION-TAB] Tab {tab_id} completed with total {len(api_calls)} API calls")
        logger.info(f"[EXECUTION-TAB] ===========================================")

        return api_calls

    def _compare_tab_results(
        self,
        execution_id: str,
        api_calls: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Compare results across environments for a tab.

        Args:
            execution_id: Execution identifier
            api_calls: API call results

        Returns:
            List of comparison results
        """
        comparisons = []

        logger.info(f"[COMPARE] ===========================================")
        logger.info(f"[COMPARE] Comparing tab results for execution: {execution_id}")
        logger.info(f"[COMPARE] Total API calls to compare: {len(api_calls)}")

        dev_calls = [c for c in api_calls if c["environment"] == "DEV"]
        qa_calls = [c for c in api_calls if c["environment"] == "QA"]
        staging_calls = [c for c in api_calls if c["environment"] == "STAGING"]

        logger.info(f"[COMPARE] DEV calls: {len(dev_calls)}")
        logger.info(f"[COMPARE] QA calls: {len(qa_calls)}")
        logger.info(f"[COMPARE] STAGING calls: {len(staging_calls)}")

        for dev_call in dev_calls:
            logger.info(f"[COMPARE] Comparing DEV call: {dev_call.get('api_step')}")
            staging_call = self._find_matching_call(
                dev_call,
                staging_calls
            )

            if staging_call:
                logger.info(f"[COMPARE] Found matching STAGING call for: {dev_call.get('api_step')}")
                comparison = self.comparison_service.compare_api_calls(
                    execution_id=execution_id,
                    target_call=dev_call,
                    staging_call=staging_call
                )
                comparisons.append(
                    comparison[0].dict() if hasattr(comparison[0], 'dict') else comparison[0]
                )
                logger.info(f"[COMPARE] Added comparison for: {dev_call.get('api_step')}")
            else:
                logger.warning(f"[COMPARE] No matching STAGING call found for: {dev_call.get('api_step')}")

        for qa_call in qa_calls:
            logger.info(f"[COMPARE] Comparing QA call: {qa_call.get('api_step')}")
            staging_call = self._find_matching_call(
                qa_call,
                staging_calls
            )

            if staging_call:
                logger.info(f"[COMPARE] Found matching STAGING call for: {qa_call.get('api_step')}")
                comparison = self.comparison_service.compare_api_calls(
                    execution_id=execution_id,
                    target_call=qa_call,
                    staging_call=staging_call
                )
                comparisons.append(
                    comparison[0].dict() if hasattr(comparison[0], 'dict') else comparison[0]
                )
                logger.info(f"[COMPARE] Added comparison for: {qa_call.get('api_step')}")
            else:
                logger.warning(f"[COMPARE] No matching STAGING call found for: {qa_call.get('api_step')}")

        logger.info(f"[COMPARE] Total comparisons generated: {len(comparisons)}")
        logger.info(f"[COMPARE] ===========================================")

        return comparisons

    def _find_matching_call(
        self,
        target_call: Dict[str, Any],
        calls: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """Find matching API call by step name."""
        for call in calls:
            if call["api_step"] == target_call["api_step"]:
                return call
        return None

    def _update_execution_progress(
        self,
        execution_id: str,
        api_calls: List[Dict[str, Any]],
        comparisons: List[Dict[str, Any]],
        completed_tabs: int,
        total_tabs: int
    ):
        """Update execution progress."""
        logger.info(f"[PROGRESS] ===========================================")
        logger.info(f"[PROGRESS] Updating progress for execution: {execution_id}")
        logger.info(f"[PROGRESS] Completed tabs: {completed_tabs}/{total_tabs}")
        logger.info(f"[PROGRESS] API calls to save: {len(api_calls)}")
        logger.info(f"[PROGRESS] Comparisons to save: {len(comparisons)}")

        execution_data = self.storage.read_execution(execution_id)

        logger.info(f"[PROGRESS] Execution data read: {execution_data is not None}")

        if execution_data:
            logger.info(f"[PROGRESS] Updating execution data fields")
            execution_data["api_calls"] = api_calls
            execution_data["comparisons"] = comparisons
            execution_data["completed_tabs"] = completed_tabs
            execution_data["total_tabs"] = total_tabs

            logger.info(f"[PROGRESS] Writing updated execution data to storage")
            self.storage.write_execution(execution_id, execution_data)
            logger.info(f"[PROGRESS] Progress updated successfully")
        else:
            logger.error(f"[PROGRESS] Execution data is None for {execution_id}")

        logger.info(f"[PROGRESS] ===========================================")

    def _finalize_execution(
        self,
        execution_id: str,
        api_calls: List[Dict[str, Any]],
        comparisons: List[Dict[str, Any]],
        report: Dict[str, Any]
    ):
        """Finalize execution with complete data."""
        execution_data = self.storage.read_execution(execution_id)

        if execution_data:
            has_failures = any(
                c.get("status_code", 200) != 200 for c in api_calls
            )

            execution_data["api_calls"] = api_calls
            execution_data["comparisons"] = comparisons
            execution_data["reports"] = report
            execution_data["has_failures"] = has_failures
            execution_data["status"] = "completed"

            self.storage.write_execution(execution_id, execution_data)

    def _mark_execution_failed(self, execution_id: str):
        """Mark execution as failed."""
        execution_data = self.storage.read_execution(execution_id)

        if execution_data:
            execution_data["status"] = "failed"
            self.storage.write_execution(execution_id, execution_data)

    def get_execution_status(
        self,
        session_id: str
    ) -> ExecutionStatusResponse:
        """
        Get overall execution status for a session.

        Args:
            session_id: Session identifier

        Returns:
            Overall status with counts

        Raises:
            ValueError: If session not found
        """
        session = self.session_service.get_session(session_id)

        if not session:
            raise ValueError(f"Session not found: {session_id}")

        total_executions = len(session.executions)
        completed_executions = len([
            e_id for e_id in session.executions
            if self._is_execution_complete(e_id)
        ])
        failed_executions = len([
            e_id for e_id in session.executions
            if self._is_execution_failed(e_id)
        ])
        in_progress_executions = total_executions - completed_executions - failed_executions

        overall_status = (
            "completed" if in_progress_executions == 0
            else "in_progress"
        )

        return ExecutionStatusResponse(
            session_id=session_id,
            overall_status=overall_status,
            total_executions=total_executions,
            completed_executions=completed_executions,
            failed_executions=failed_executions,
            in_progress_executions=in_progress_executions
        )

    def get_execution_tabs(self, session_id: str) -> TabsListResponse:
        """
        Get all tabs (Category+Product+Plan combinations) for a session.

        Args:
            session_id: Session identifier

        Returns:
            List of tabs with status

        Raises:
            ValueError: If session not found
        """
        session = self.session_service.get_session(session_id)

        if not session:
            raise ValueError(f"Session not found: {session_id}")

        tabs = []

        for execution_id in session.executions:
            execution_data = self.storage.read_execution(execution_id)

            if execution_data:
                total_tabs = execution_data.get("total_tabs", 0)
                completed_tabs = execution_data.get("completed_tabs", 0)
                status = execution_data.get("status", "unknown")

                for i in range(1, total_tabs + 1):
                    tabs.append({
                        "tab_id": f"tab_{execution_id}_{i}",
                        "status": "completed" if i <= completed_tabs else "in_progress",
                        "api_calls_completed": completed_tabs * 21,
                        "api_calls_total": total_tabs * 21,
                        "has_failures": execution_data.get("has_failures", False)
                    })

        return TabsListResponse(
            session_id=session_id,
            tabs=tabs
        )

    def get_tab_progress(
        self,
        session_id: str,
        tab_id: str
    ) -> TabProgressResponse:
        """
        Get progress for a specific tab.

        Args:
            session_id: Session identifier
            tab_id: Tab identifier

        Returns:
            Tab progress with API calls

        Raises:
            ValueError: If session or tab not found
        """
        tab_parts = tab_id.split("_")
        execution_id = "_".join(tab_parts[1:-1])
        tab_index = int(tab_parts[-1])

        execution_data = self.storage.read_execution(execution_id)

        if not execution_data:
            raise ValueError(f"Execution not found: {execution_id}")

        api_calls = execution_data.get("api_calls", [])

        status = "in_progress"
        if tab_index <= execution_data.get("completed_tabs", 0):
            status = "completed"
        elif execution_data.get("status") == "failed":
            status = "failed"

        return TabProgressResponse(
            tab_id=tab_id,
            status=status,
            api_calls=api_calls
        )

    def _is_execution_complete(self, execution_id: str) -> bool:
        """Check if execution is complete."""
        execution_data = self.storage.read_execution(execution_id)
        return execution_data and execution_data.get("status") == "completed"

    def _is_execution_failed(self, execution_id: str) -> bool:
        """Check if execution failed."""
        execution_data = self.storage.read_execution(execution_id)
        return execution_data and execution_data.get("status") == "failed"
