"""Execution Service

Orchestrates test execution across all Category+Product+Plan combinations.
Implements sequential execution flow as per PRD requirements.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from app.services.storage_service import StorageService
from app.services.session_service import SessionService
from app.services.config_service import ConfigService
from app.services.api_executor import APIExecutorService
from app.services.comparison_service import ComparisonService
from app.services.llm_reporter import LLMReporterService
from app.schemas.execution import ExecutionStartRequest, ExecutionStatusResponse, TabsListResponse, TabProgressResponse
from app.models.execution import Execution

logger = logging.getLogger("InternalTestingPortal")


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

    def start_execution(self, request: ExecutionStartRequest) -> List[str]:
        """
        Start multiple executions for Category+Product+Plan combinations.

        Args:
            request: Execution start request

        Returns:
            List of execution IDs created

        Raises:
            ValueError: If session doesn't exist or no combinations found
        """
        try:
            session = self.session_service.get_session(request.session_id)

            if not session:
                raise ValueError(f"Session not found: {request.session_id}")

            timestamp = datetime.now()
            base_id = f"{session.user_name}_{timestamp.strftime('%Y%m%d_%H%M%S')}"

            categories = request.categories if request.categories else ["all"]

            combinations = self.config_service.get_all_combinations(
                categories if categories != ["all"] else None
            )
            logger.info(f"[EXECUTION] Generated {len(combinations)} combinations for categories: {categories}")

            if not combinations or len(combinations) == 0:
                logger.error(f"[EXECUTION] No combinations generated for {categories}")
                raise ValueError(f"No Category+Product+Plan combinations found for categories: {categories}")

            execution_ids = []

            # Create individual execution for each combination
            for i, combination in enumerate(combinations):
                execution_id = f"{base_id}_{combination['category']}_{combination['product_id']}_{combination['plan_id']}"

                # Get names for logging
                products = self.config_service.get_products_for_category(combination['category'])
                product_data = next((p for p in products if p.get('product_id') == combination['product_id']), {})
                product_name = product_data.get('name', combination['product_id'])

                plans = self.config_service.get_plans_for_product(combination['category'], combination['product_id'])
                plan_data = next((p for p in plans if p.get('plan_id') == combination['plan_id']), {})
                plan_name = plan_data.get('name', combination['plan_id'])

                execution_data = {
                    "execution_id": execution_id,
                    "session_id": request.session_id,
                    "session_name": session.user_name,
                    "category": combination['category'],
                    "product_id": combination['product_id'],
                    "plan_id": combination['plan_id'],
                    "target_environment": request.target_environment,
                    "status": "pending",  # Will be set to "in_progress" when background task starts
                    "timestamp": timestamp.isoformat(),
                    "api_calls": [],
                    "comparisons": [],
                    "reports": {},
                    "has_failures": False
                }

                self.storage.write_execution(execution_id, execution_data)
                execution_ids.append(execution_id)

                logger.debug(f"Created execution: {execution_id} ({combination['category']} → {product_name} → {plan_name})")

            # Update session with all execution IDs
            for execution_id in execution_ids:
                self.session_service.add_execution_to_session(
                    request.session_id,
                    execution_id
                )

            self.session_service.update_session_config(
                request.session_id,
                {
                    "target_environment": request.target_environment,
                    "categories": categories,
                    "admin_auth_token": request.admin_auth_token,
                    "customer_auth_token": request.customer_auth_token
                }
            )

            logger.info(f"Created {len(execution_ids)} executions for test {base_id}")

            # Cleanup old test directories
            self.storage.cleanup_old_test_directories()

            return execution_ids

        except Exception as e:
            logger.error(f"Failed to start executions: {e}", exc_info=True)
            raise

    def execute_single_execution(
        self,
        execution_id: str,
        session_id: str,
        target_env: str,
        category: str,
        product_id: str,
        plan_id: str,
        admin_token: Optional[str],
        customer_token: Optional[str]
    ):
        """
        Execute a single execution (Category+Product+Plan combination).

        Args:
            execution_id: Execution identifier
            session_id: Session identifier
            target_env: Target environment (DEV/QA)
            category: Insurance category
            product_id: Product identifier
            plan_id: Plan identifier
            admin_token: Admin authentication token
            customer_token: Customer authentication token
        """
        try:
            logger.info(f"[SINGLE-EXEC] Starting execution: {execution_id} for {category} → {product_id} → {plan_id} in {target_env}")

            # Update execution status to in_progress
            execution_data = self.storage.read_execution(execution_id)
            if execution_data:
                execution_data["status"] = "in_progress"
                self.storage.write_execution(execution_id, execution_data)
                logger.debug(f"[SINGLE-EXEC] Updated status to 'in_progress' for {execution_id}")
            else:
                logger.warning(f"[SINGLE-EXEC] Could not read execution data for {execution_id}")

            # Execute 14 API calls (7 target + 7 STAGING)
            logger.info(f"[SINGLE-EXEC] Executing 14 API calls for {execution_id}")
            api_calls = self._execute_tab(
                execution_id=execution_id,
                tab_id=execution_id,  # For single execution, tab_id = execution_id
                target_env=target_env,
                combination={
                    "category": category,
                    "product_id": product_id,
                    "plan_id": plan_id
                },
                admin_token=admin_token,
                customer_token=customer_token
            )
            logger.info(f"[SINGLE-EXEC] Completed API execution: {len(api_calls)} calls made for {execution_id}")

            # Generate comparisons
            comparisons = []
            if api_calls:
                logger.debug(f"[SINGLE-EXEC] Generating comparisons for {execution_id}")
                comparisons = self._compare_tab_results(
                    execution_id=execution_id,
                    target_env=target_env,
                    api_calls=api_calls
                )
                logger.info(f"[SINGLE-EXEC] Generated {len(comparisons)} comparisons for {execution_id}")
            else:
                logger.warning(f"[SINGLE-EXEC] No API calls were generated for {execution_id}")

            # Generate report (placeholder for now)
            report = {
                "execution_id": execution_id,
                "status": "completed",
                "total_api_calls": len(api_calls),
                "failed_api_calls": len([c for c in api_calls if c.get("status_code", 200) != 200]),
                "summary": "Execution completed"
            }

            # Update execution with final data
            logger.debug(f"[SINGLE-EXEC] Updating final execution data for {execution_id}")
            execution_data = self.storage.read_execution(execution_id)
            if execution_data:
                execution_data["api_calls"] = api_calls
                execution_data["comparisons"] = comparisons
                execution_data["reports"] = report
                execution_data["status"] = "completed"
                execution_data["has_failures"] = any(c.get("status_code", 200) != 200 for c in api_calls)
                self.storage.write_execution(execution_id, execution_data)
                logger.info(f"[SINGLE-EXEC] Updated execution data for {execution_id} - status: completed, has_failures: {execution_data['has_failures']}")
            else:
                logger.error(f"[SINGLE-EXEC] Could not read execution data for final update of {execution_id}")

            logger.info(f"[SINGLE-EXEC] Successfully completed execution: {execution_id} with {len(api_calls)} API calls")

        except Exception as e:
            logger.error(f"[SINGLE-EXEC] Failed execution {execution_id}: {e}", exc_info=True)
            # Mark as failed
            try:
                execution_data = self.storage.read_execution(execution_id)
                if execution_data:
                    execution_data["status"] = "failed"
                    self.storage.write_execution(execution_id, execution_data)
                    logger.info(f"[SINGLE-EXEC] Marked execution {execution_id} as failed")
            except Exception as update_error:
                logger.error(f"[SINGLE-EXEC] Could not update failed status for {execution_id}: {update_error}")
            raise

    async def execute_all_tabs(
        self,
        execution_id: str,
        session_id: str,
        target_env: str,
        categories: List[str],
        admin_token: Optional[str],
        customer_token: Optional[str],
        config_service: Any = None
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
            logger.info(f"[EXECUTION] Starting execute_all_tabs for {execution_id}")
            logger.info(f"[EXECUTION] Session ID: {session_id}")
            logger.info(f"[EXECUTION] Target Env: {target_env}")
            logger.info(f"[EXECUTION] Categories: {categories}")
            logger.info(f"[EXECUTION] Admin Token: {'Provided' if admin_token else 'Not provided'}")
            logger.info(f"[EXECUTION] Customer Token: {'Provided' if customer_token else 'Not provided'}")
            logger.info(f"[EXECUTION] ===========================================")

            combinations = self.config_service.get_all_combinations(
                categories if categories != ["all"] else None
            )
            logger.info(f"[EXECUTION] Generated {len(combinations)} combinations")

            if not combinations or len(combinations) == 0:
                logger.error(f"[EXECUTION] No combinations generated for {categories}")
                raise ValueError(f"No Category+Product+Plan combinations found for categories: {categories}")

            all_api_calls = []
            all_comparisons = []
            completed_tabs = 0

            for i, combination in enumerate(combinations):
                tab_index = i + 1  # 1-based
                # Get names for tab ID
                products = self.config_service.get_products_for_category(combination['category'])
                product_data = next((p for p in products if p.get('product_id') == combination['product_id']), {})
                product_name = product_data.get('name', combination['product_id']).replace(" ", "_").replace("-", "_")

                plans = self.config_service.get_plans_for_product(combination['category'], combination['product_id'])
                plan_data = next((p for p in plans if p.get('plan_id') == combination['plan_id']), {})
                plan_name = plan_data.get('name', combination['plan_id']).replace(" ", "_").replace("-", "_")

                tab_id = f"{execution_id}#{tab_index}#{combination['category']}#{product_name}#{plan_name}"

                logger.info(f"[EXECUTION] Processing tab {i+1}/{len(combinations)}: {tab_id}")

                try:
                    # Execute the tab (paired target + STAGING calls)
                    api_calls = self._execute_tab(
                        execution_id=execution_id,
                        tab_id=tab_id,
                        target_env=target_env,
                        combination=combination,
                        admin_token=admin_token,
                        customer_token=customer_token
                    )

                    if api_calls:
                        # Compare results between target and STAGING
                        comparisons = self._compare_tab_results(
                            execution_id=execution_id,
                            target_env=target_env,
                            api_calls=api_calls
                        )

                        # Collect results
                        all_api_calls.extend(api_calls)
                        all_comparisons.extend(comparisons)
                        completed_tabs += 1

                        # Update progress
                        self._update_execution_progress(
                            execution_id=execution_id,
                            api_calls=all_api_calls,
                            comparisons=all_comparisons,
                            completed_tabs=completed_tabs,
                            total_tabs=len(combinations)
                        )

                        logger.info(f"[EXECUTION] Tab {tab_id} completed successfully")
                    else:
                        logger.warning(f"[EXECUTION] Tab {tab_id} produced no API calls")

                except Exception as e:
                    logger.error(f"[EXECUTION] Failed to process tab {tab_id}: {e}")
                    # Continue to next tab as per PRD (don't stop execution)
                    continue

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
                logger.error(f"[EXECUTION] Failed to generate report for {execution_id}: {e}")
                report = None

            try:
                logger.info(f"[EXECUTION] Finalizing execution for {execution_id}")
                self._finalize_execution(
                    execution_id=execution_id,
                    api_calls=all_api_calls,
                    comparisons=all_comparisons,
                    report=report.dict() if report and hasattr(report, 'dict') else report or {}
                )
                logger.info(f"[EXECUTION] Execution finalized for {execution_id}")
            except Exception as e:
                logger.error(f"[EXECUTION] Failed to finalize execution {execution_id}: {e}")
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
        target_env: str,
        combination: Dict[str, str],
        admin_token: Optional[str],
        customer_token: Optional[str]
    ) -> List[Dict[str, Any]]:
        """
        Execute a single tab (Category+Product+Plan combination) with paired API calls.

        Executes each of the 7 steps in target environment first, then STAGING if target succeeds.
        Stops entire tab on any API failure.

        Args:
            execution_id: Execution identifier
            tab_id: Tab identifier
            target_env: Target environment (DEV or QA)
            combination: Category, product, plan combination
            admin_token: Admin authentication token
            customer_token: Customer authentication token

        Returns:
            List of API call results
        """
        api_calls = []
        application_id = None

        logger.info(f"[EXECUTION-TAB] Starting paired execution for tab {tab_id} in {target_env} vs STAGING")

        for step in self.api_executor.api_steps:
            # Select auth token for this step
            auth_token = self.api_executor._select_auth_token(step, admin_token, customer_token)

            # Execute target API call
            logger.info(f"[EXECUTION-TAB] Executing {step} in {target_env} for tab {tab_id}")
            target_call = self.api_executor.execute_api_call(
                execution_id=execution_id,
                tab_id=tab_id,
                api_step=step,
                environment=target_env,
                category=combination["category"],
                product_id=combination["product_id"],
                plan_id=combination["plan_id"],
                auth_token=auth_token,
                application_id=application_id
            )
            api_calls.append(target_call.dict() if hasattr(target_call, 'dict') else target_call)

            if target_call.status_code != 200:
                logger.warning(f"[EXECUTION-TAB] Target API failed for step '{step}' in {target_env} (status {target_call.status_code}), stopping tab {tab_id}")
                break  # Stop the entire tab on target failure

            # Update application_id from successful application_submit
            if step == "application_submit":
                application_id = target_call.response_data.get("application_id")
                logger.info(f"[EXECUTION-TAB] Retrieved application_id: {application_id}")

            # Execute STAGING API call for comparison
            logger.info(f"[EXECUTION-TAB] Executing {step} in STAGING for tab {tab_id}")
            staging_call = self.api_executor.execute_api_call(
                execution_id=execution_id,
                tab_id=tab_id,
                api_step=step,
                environment="STAGING",
                category=combination["category"],
                product_id=combination["product_id"],
                plan_id=combination["plan_id"],
                auth_token=auth_token,
                application_id=application_id
            )
            api_calls.append(staging_call.dict() if hasattr(staging_call, 'dict') else staging_call)

            if staging_call.status_code != 200:
                logger.warning(f"[EXECUTION-TAB] STAGING API failed for step '{step}' (status {staging_call.status_code}), stopping tab {tab_id}")
                break  # Stop the entire tab on STAGING failure

        logger.info(f"[EXECUTION-TAB] ===========================================")
        logger.info(f"[EXECUTION-TAB] Tab {tab_id} completed with {len(api_calls)} API calls")
        logger.info(f"[EXECUTION-TAB] ===========================================")

        return api_calls

    def _compare_tab_results(
        self,
        execution_id: str,
        target_env: str,
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
        logger.info(f"[COMPARE] Target env: {target_env}")
        logger.info(f"[COMPARE] Total API calls to compare: {len(api_calls)}")

        target_calls = [c for c in api_calls if c["environment"] == target_env]
        staging_calls = [c for c in api_calls if c["environment"] == "STAGING"]

        logger.info(f"[COMPARE] {target_env} calls: {len(target_calls)}")
        logger.info(f"[COMPARE] STAGING calls: {len(staging_calls)}")

        for target_call in target_calls:
            logger.info(f"[COMPARE] Comparing {target_env} call: {target_call.get('api_step')}")
            staging_call = self._find_matching_call(
                target_call,
                staging_calls
            )

            if staging_call:
                logger.info(f"[COMPARE] Found matching STAGING call for: {target_call.get('api_step')}")
                comparison = self.comparison_service.compare_api_calls(
                    execution_id=execution_id,
                    target_call=target_call,
                    staging_call=staging_call
                )
                comparisons.append(
                    comparison[0].dict() if hasattr(comparison[0], 'dict') else comparison[0]
                )
                logger.info(f"[COMPARE] Added comparison for: {target_call.get('api_step')}")
            else:
                logger.warning(f"[COMPARE] No matching STAGING call found for: {target_call.get('api_step')}")

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
        Get all execution tabs for a session.

        Args:
            session_id: Session identifier

        Returns:
            List of tabs with status
        """
        session = self.session_service.get_session(session_id)

        if not session:
            raise ValueError(f"Session not found: {session_id}")

        tabs = []

        for execution_id in session.executions:
            execution_data = self.storage.read_execution(execution_id)

            if execution_data:
                combinations = execution_data.get("combinations", [])
                total_tabs = len(combinations)
                completed_tabs = execution_data.get("completed_tabs", 0)
                status = execution_data.get("status", "unknown")

                for i, combination in enumerate(combinations, 1):
                    tab_id = f"{execution_id}#{i}#{combination['category']}#{combination['product_name']}#{combination['plan_name']}"

                    logger.info(f"Generated tab_id: {tab_id}")

                    tabs.append({
                        "tab_id": tab_id,
                        "status": "completed" if i <= completed_tabs else "in_progress" if status == "in_progress" else status,
                        "api_calls_completed": min(completed_tabs, i) * 14,  # 14 calls per tab (2 env x 7 steps)
                        "api_calls_total": total_tabs * 14,
                        "has_failures": execution_data.get("has_failures", False)
                    })

                logger.info(f"Total tabs for session {session_id}: {len(tabs)}")

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
        logger.info(f"get_tab_progress called with session_id: {session_id}, tab_id: {tab_id}")
        if "#" in tab_id:
            # New format: execution_id#index#category#product#plan
            parts = tab_id.split("#")
            if len(parts) < 5:
                raise ValueError(f"Invalid new tab_id format: {tab_id}")
            execution_id = parts[0]
            tab_index = int(parts[1])
            logger.debug(f"Parsed new format tab_id: execution_id={execution_id}, tab_index={tab_index}")
        else:
            # Old format fallback: execution_id (may be just execution_id or partial)
            parts = tab_id.split("_")
            if len(parts) < 3:
                raise ValueError(f"Invalid old tab_id format: {tab_id}")
            execution_id = "_".join(parts[:3]) if len(parts) >= 3 else tab_id
            tab_index = 1  # Default for backward compatibility
            logger.debug(f"Parsed old format tab_id: execution_id={execution_id}, tab_index={tab_index}")

        execution_data = self.storage.read_execution(execution_id)

        if not execution_data:
            logger.warning(f"Execution not found: {execution_id}, returning empty progress")
            return TabProgressResponse(tab_id=tab_id, status="not_found", api_calls=[])

        # Filter API calls for this specific tab
        api_calls = [c for c in execution_data.get("api_calls", []) if c.get("tab_id") == tab_id]

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

    def get_session_progress(self, session_id: str) -> Dict[str, Any]:
        """
        Get progress for all executions in a session.

        Args:
            session_id: Session identifier

        Returns:
            Progress data for all executions in the session

        Raises:
            ValueError: If session not found
        """
        session = self.session_service.get_session(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")

        executions_progress = {}

        # Get progress for each execution
        for execution_id in session.executions:
            try:
                execution_data = self.storage.read_execution(execution_id)
                if execution_data:
                    # Extract API call statuses for target environment only
                    api_progress = {}
                    api_calls = execution_data.get("api_calls", [])

                    # Group calls by api_step and get target environment status
                    for call in api_calls:
                        if call.get("environment") != "STAGING":  # Only target env
                            api_step = call.get("api_step", "")
                            status_code = call.get("status_code", 500)

                            # Map status codes to progress states
                            if status_code == 200:
                                status = "succeed"
                            elif call.get("error"):
                                status = "failed"
                            else:
                                status = "running"  # In progress

                            api_progress[api_step] = status

                    # Fill in missing steps as "pending"
                    all_steps = [
                        "application_submit", "apply_coupon", "payment_checkout",
                        "admin_policy_list", "admin_policy_details",
                        "customer_policy_list", "customer_policy_details"
                    ]

                    for step in all_steps:
                        if step not in api_progress:
                            api_progress[step] = "pending"

                    executions_progress[execution_id] = api_progress
                    logger.debug(f"Retrieved progress for execution {execution_id}: {len(api_progress)} steps")

                else:
                    logger.warning(f"Could not read execution data for {execution_id}")
                    executions_progress[execution_id] = {step: "pending" for step in [
                        "application_submit", "apply_coupon", "payment_checkout",
                        "admin_policy_list", "admin_policy_details",
                        "customer_policy_list", "customer_policy_details"
                    ]}

            except Exception as e:
                logger.error(f"Failed to get progress for execution {execution_id}: {e}")
                executions_progress[execution_id] = {step: "pending" for step in [
                    "application_submit", "apply_coupon", "payment_checkout",
                    "admin_policy_list", "admin_policy_details",
                    "customer_policy_list", "customer_policy_details"
                ]}

        logger.info(f"Retrieved progress for {len(executions_progress)} executions in session {session_id}")

        return {
            "session_id": session_id,
            "executions": executions_progress
        }
