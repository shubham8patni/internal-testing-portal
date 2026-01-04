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
            combinations = self.config_service.get_all_combinations(
                categories if categories != ["all"] else None
            )

            all_api_calls = []
            all_comparisons = []

            for i, combination in enumerate(combinations):
                tab_id = (
                    f"{combination['category']}_"
                    f"{combination['product_id']}_"
                    f"{combination['plan_id']}"
                )

                logger.info(
                    f"Executing tab {i+1}/{len(combinations)}: {tab_id}"
                )

                api_calls = self._execute_tab(
                    execution_id=execution_id,
                    tab_id=tab_id,
                    combination=combination,
                    admin_token=admin_token,
                    customer_token=customer_token
                )

                comparisons = self._compare_tab_results(
                    execution_id=execution_id,
                    api_calls=api_calls
                )

                all_api_calls.extend(api_calls)
                all_comparisons.extend(comparisons)

                self._update_execution_progress(
                    execution_id=execution_id,
                    api_calls=all_api_calls,
                    comparisons=all_comparisons,
                    completed_tabs=i + 1,
                    total_tabs=len(combinations)
                )

            report = self.reporter.generate_execution_report(
                execution_id=execution_id,
                execution_data=self.storage.read_execution(execution_id),
                comparisons=[c.dict() if hasattr(c, 'dict') else c for c in all_comparisons]
            )

            self._finalize_execution(
                execution_id=execution_id,
                api_calls=all_api_calls,
                comparisons=all_comparisons,
                report=report.dict() if hasattr(report, 'dict') else report
            )

            self.session_service.update_session_status(session_id, "completed")

            logger.info(f"Execution completed: {execution_id}")

        except Exception as e:
            logger.error(f"Failed to execute all tabs: {e}", exc_info=True)
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

        for environment in ["DEV", "QA", "STAGING"]:
            try:
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

                api_calls.extend([
                    call.dict() if hasattr(call, 'dict') else call
                    for call in calls
                ])

            except Exception as e:
                logger.error(
                    f"Failed to execute tab {tab_id} in {environment}: {e}",
                    exc_info=True
                )

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

        dev_calls = [c for c in api_calls if c["environment"] == "DEV"]
        qa_calls = [c for c in api_calls if c["environment"] == "QA"]
        staging_calls = [c for c in api_calls if c["environment"] == "STAGING"]

        for dev_call in dev_calls:
            staging_call = self._find_matching_call(
                dev_call,
                staging_calls
            )

            if staging_call:
                comparison = self.comparison_service.compare_api_calls(
                    execution_id=execution_id,
                    target_call=dev_call,
                    staging_call=staging_call
                )
                comparisons.append(
                    comparison[0].dict() if hasattr(comparison[0], 'dict') else comparison[0]
                )

        for qa_call in qa_calls:
            staging_call = self._find_matching_call(
                qa_call,
                staging_calls
            )

            if staging_call:
                comparison = self.comparison_service.compare_api_calls(
                    execution_id=execution_id,
                    target_call=qa_call,
                    staging_call=staging_call
                )
                comparisons.append(
                    comparison[0].dict() if hasattr(comparison[0], 'dict') else comparison[0]
                )

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
        execution_data = self.storage.read_execution(execution_id)

        if execution_data:
            execution_data["api_calls"] = api_calls
            execution_data["comparisons"] = comparisons
            execution_data["completed_tabs"] = completed_tabs
            execution_data["total_tabs"] = total_tabs

            self.storage.write_execution(execution_id, execution_data)

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
