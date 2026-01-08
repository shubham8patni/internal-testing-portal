"""Sequential Execution Engine for Insurance API Testing

This module implements the core sequential execution logic that orchestrates
the complete insurance purchase flow for each Category+Product+Plan combination.

Execution Flow:
1. execute_master() - Main orchestrator for all combinations
2. execute_combination() - Sequential execution for one combination
3. API calls with random delays and failure handling
4. Progress saving after each step
5. Integration with storage and logging systems
"""

import time
import random
import json
import logging
from typing import Dict, Any, List
from pathlib import Path

from app.services.api_functions import (
    call_application_submit,
    call_apply_coupon,
    call_payment_checkout,
    call_admin_policy_list,
    call_admin_policy_details,
    call_customer_policy_list,
    call_customer_policy_details
)
from app.services.config_service import ConfigService
from app.services.storage_service import StorageService

logger = logging.getLogger(__name__)

class ExecutionEngine:
    """Sequential execution engine for insurance API testing."""

    def __init__(self):
        self.config_service = ConfigService()
        self.storage_service = StorageService()

    def execute_master(self, username: str, session_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Master execution orchestrator.

        Processes all Category+Product+Plan combinations sequentially.

        Args:
            username: User identifier for session
            session_id: Session identifier (format: username_date_timestamp)
            config: Configuration with categories, environment, tokens

        Returns:
            Dict with execution results summary
        """
        try:
            logger.info(f"[EXEC-MASTER] Starting master execution for user {username}, session {session_id}")

            # Use the provided session_id for directory creation
            session_dir = self.storage_service.create_session_directory(session_id)

            logger.info(f"[EXEC-MASTER] Created session directory: {session_dir}")

            # Generate combinations from config
            combinations = self.config_service.get_all_combinations(
                config.get("categories", [])
            )

            if not combinations:
                logger.warning("[EXEC-MASTER] No combinations generated from config")
                return {
                    "success": False,
                    "error": "No combinations found for the selected categories",
                    "executions": []
                }

            logger.info(f"[EXEC-MASTER] Generated {len(combinations)} combinations")

            # Execute each combination sequentially
            execution_results = []

            for i, combination in enumerate(combinations, 1):
                logger.info(f"[EXEC-MASTER] Executing combination {i}/{len(combinations)}: {combination}")

                try:
                    result = self.execute_combination(username, session_dir, combination, config)
                    execution_results.append(result)

                    # Check if this execution failed and log appropriately
                    if not result.get("success", False):
                        logger.warning(f"[EXEC-MASTER] Combination {combination} failed: {result.get('error')}")

                    # Continue to next combination even if this one failed
                    logger.info(f"[EXEC-MASTER] Completed combination {i}/{len(combinations)}")

                except Exception as e:
                    logger.error(f"[EXEC-MASTER] Unexpected error in combination {combination}: {e}")
                    execution_results.append({
                        "success": False,
                        "error": f"Unexpected error: {str(e)}",
                        "combination": combination
                    })

            # Calculate summary
            successful = sum(1 for r in execution_results if r.get("success"))
            total = len(execution_results)

            logger.info(f"[EXEC-MASTER] Master execution completed: {successful}/{total} combinations successful")

            return {
                "success": True,
                "session_id": session_id,
                "total_combinations": total,
                "successful_combinations": successful,
                "failed_combinations": total - successful,
                "executions": execution_results
            }

        except Exception as e:
            logger.error(f"[EXEC-MASTER] Master execution failed: {e}", exc_info=True)
            return {
                "success": False,
                "error": f"Master execution failed: {str(e)}",
                "executions": []
            }

    def execute_combination(self, username: str, session_dir: Path,
                          combination: Dict[str, str], config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a single Category+Product+Plan combination.

        Performs 14 API calls sequentially (7 DEV + 7 STAGING) with delays and failure handling.

        Args:
            username: User identifier
            session_dir: Session directory path
            combination: Category+Product+Plan combination
            config: Configuration with tokens and settings

        Returns:
            Dict with execution results
        """
        try:
            logger.info(f"[EXEC-COMB] Starting execution for {combination}")

            combination_key = f"{combination['category']}_{combination['product_id']}_{combination['plan_id']}"
            execution_id = f"{username}_{time.strftime('%Y%m%d_%H%M%S')}_{combination_key}"

            # Initialize execution data
            execution_data = {
                "execution_id": execution_id,
                "session_id": f"{username}_{session_dir.name.split('_')[-1]}",
                "username": username,
                "category": combination["category"],
                "product_id": combination["product_id"],
                "plan_id": combination["plan_id"],
                "target_environment": config.get("target_environment", "DEV"),
                "status": "in_progress",
                "api_calls": [],
                "comparisons": [],
                "reports": {},
                "has_failures": False,
                "created_at": time.time()
            }

            # Save initial progress
            self._save_progress(session_dir, combination, execution_data)

            # Track API call results
            api_results = []
            application_id = None
            execution_stopped = False

            # Define API call sequence
            api_steps = [
                ("application_submit", "DEV"),
                ("application_submit", "STAGING"),
                ("apply_coupon", "DEV"),
                ("apply_coupon", "STAGING"),
                ("payment_checkout", "DEV"),
                ("payment_checkout", "STAGING"),
                ("admin_policy_list", "DEV"),
                ("admin_policy_list", "STAGING"),
                ("admin_policy_details", "DEV"),
                ("admin_policy_details", "STAGING"),
                ("customer_policy_list", "DEV"),
                ("customer_policy_list", "STAGING"),
                ("customer_policy_details", "DEV"),
                ("customer_policy_details", "STAGING")
            ]

            logger.info(f"[EXEC-COMB] Starting {len(api_steps)} API calls for {combination_key}")

            # Execute API calls sequentially
            for step_name, environment in api_steps:
                if execution_stopped:
                    logger.info(f"[EXEC-COMB] Skipping {step_name} ({environment}) - execution stopped")
                    # Still record as skipped for progress tracking
                    skipped_result = {
                        "success": False,
                        "error": "Execution stopped due to previous failure",
                        "api_step": step_name,
                        "environment": environment,
                        "status_code": 0
                    }
                    api_results.append(skipped_result)
                    continue

                logger.debug(f"[EXEC-COMB] Executing {step_name} in {environment}")

                # Call appropriate API function
                result = self._call_api_function(step_name, combination, application_id, config)

                # Add environment to result for progress tracking
                if isinstance(result, dict):
                    result["environment"] = environment

                # Store result
                api_results.append(result)

                # Update execution data
                execution_data["api_calls"] = api_results

                # Check for failures
                if not result.get("success", False):
                    logger.warning(f"[EXEC-COMB] API call failed: {step_name} ({environment}) - {result.get('error')}")

                    # Special handling for payment_checkout failure - stop execution
                    if step_name == "payment_checkout" and environment == "DEV":
                        if combination["category"] == "MV4" and combination["product_id"] == "TOKIO_MARINE" and combination["plan_id"] == "COMPREHENSIVE":
                            logger.info(f"[EXEC-COMB] Payment checkout failed for failing combination - stopping execution")
                            execution_stopped = True
                            execution_data["has_failures"] = True
                        else:
                            logger.warning(f"[EXEC-COMB] Payment checkout failed but continuing (not the failing combination)")

                    execution_data["has_failures"] = True

                # Extract application_id from successful application_submit
                if step_name == "application_submit" and result.get("success") and environment == "DEV":
                    application_id = result.get("application_id")
                    logger.debug(f"[EXEC-COMB] Extracted application_id: {application_id}")

                # Save progress after each API call
                self._save_progress(session_dir, combination, execution_data)

                # Add random delay between calls (except for the last call in each pair)
                if not (step_name == "customer_policy_details" and environment == "STAGING"):
                    delay = random.randint(1, 3)
                    logger.debug(f"[EXEC-COMB] Adding {delay}s delay before next API call")
                    time.sleep(delay)

            # Finalize execution
            execution_data["status"] = "completed" if not execution_stopped else "completed_with_failures"
            execution_data["completed_at"] = time.time()
            execution_data["total_api_calls"] = len(api_results)
            execution_data["successful_api_calls"] = sum(1 for r in api_results if r.get("success"))

            # Save final results
            self._save_final_results(session_dir, combination, execution_data)

            logger.info(f"[EXEC-COMB] Completed execution for {combination_key}: {execution_data['successful_api_calls']}/{execution_data['total_api_calls']} API calls successful")

            return {
                "success": True,
                "execution_id": execution_id,
                "combination": combination,
                "api_calls_completed": len(api_results),
                "api_calls_successful": execution_data["successful_api_calls"],
                "has_failures": execution_data["has_failures"],
                "execution_stopped": execution_stopped
            }

        except Exception as e:
            logger.error(f"[EXEC-COMB] Execution failed for {combination}: {e}", exc_info=True)
            return {
                "success": False,
                "error": f"Execution failed: {str(e)}",
                "combination": combination
            }

    def _call_api_function(self, step_name: str, combination: Dict[str, str],
                          application_id: str = None, config: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Call the appropriate API function based on step name.

        Args:
            step_name: API step name
            combination: Category+Product+Plan combination
            application_id: Application ID for dependent calls
            config: Configuration dict

        Returns:
            API call result
        """
        try:
            if step_name == "application_submit":
                return call_application_submit(combination)
            elif step_name == "apply_coupon":
                return call_apply_coupon(combination, application_id or "default_app_id")
            elif step_name == "payment_checkout":
                return call_payment_checkout(combination, application_id or "default_app_id")
            elif step_name == "admin_policy_list":
                return call_admin_policy_list(combination)
            elif step_name == "admin_policy_details":
                return call_admin_policy_details(combination, "policy_12345")
            elif step_name == "customer_policy_list":
                return call_customer_policy_list(combination)
            elif step_name == "customer_policy_details":
                return call_customer_policy_details(combination, "policy_12345")
            else:
                return {
                    "success": False,
                    "error": f"Unknown API step: {step_name}",
                    "api_step": step_name,
                    "status_code": 500
                }

        except Exception as e:
            logger.error(f"[EXEC-API] API call failed for {step_name}: {e}")
            return {
                "success": False,
                "error": f"API call failed: {str(e)}",
                "api_step": step_name,
                "status_code": 500
            }

    def _save_progress(self, session_dir: Path, combination: Dict[str, str], execution_data: Dict[str, Any]):
        """Save current execution progress to JSON file."""
        try:
            combination_key = f"{combination['category']}_{combination['product_id']}_{combination['plan_id']}"
            progress_file = session_dir / f"{combination_key}_progress.json"

            with open(progress_file, 'w') as f:
                import json
                json.dump(execution_data, f, indent=2, default=str)

            logger.debug(f"[EXEC-SAVE] Saved progress for {combination_key}")

        except Exception as e:
            logger.error(f"[EXEC-SAVE] Failed to save progress: {e}")

    def _save_final_results(self, session_dir: Path, combination: Dict[str, str], execution_data: Dict[str, Any]):
        """Save final execution results to JSON file."""
        try:
            combination_key = f"{combination['category']}_{combination['product_id']}_{combination['plan_id']}"
            final_file = session_dir / f"{combination_key}_complete.json"

            with open(final_file, 'w') as f:
                json.dump(execution_data, f, indent=2, default=str)

            logger.info(f"[EXEC-SAVE] Saved final results for {combination_key}")

        except Exception as e:
            logger.error(f"[EXEC-SAVE] Failed to save final results: {e}")

    def get_session_progress(self, username: str, session_id: str) -> Dict[str, Any]:
        """
        Get progress for all executions in a session.

        Reads progress from JSON files and returns structured data for UI polling.

        Args:
            username: User identifier
            session_id: Session identifier

        Returns:
            Dict with session_id and executions progress data
        """
        try:
            logger.debug(f"[PROGRESS] Getting progress for session {session_id}")

            # Find session directory
            session_dir = self.storage_service.create_session_directory(session_id)

            executions_progress = {}
            progress_files_found = 0

            # Read all progress files in session directory
            if session_dir.exists():
                for progress_file in session_dir.glob("*_progress.json"):
                    try:
                        progress_files_found += 1

                        # Extract combination from filename
                        # Format: {category}_{product}_{plan}_progress.json
                        filename = progress_file.stem  # Remove .json extension
                        combination_key = filename.replace('_progress', '')

                        # Read progress data
                        with open(progress_file, 'r') as f:
                            execution_data = json.load(f)

                        # Extract API call statuses for progress
                        api_calls = execution_data.get("api_calls", [])

                        # Build progress map for UI
                        progress_map = {}

                        # Get all possible API steps (UI-expected keys without _call suffix)
                        all_steps = [
                            "application_submit",
                            "apply_coupon",
                            "payment_checkout",
                            "admin_policy_list",
                            "admin_policy_details",
                            "customer_policy_list",
                            "customer_policy_details"
                        ]

                        # Initialize all steps as "pending"
                        for step in all_steps:
                            progress_map[step] = "pending"

                        # Find the last failed call to determine stopping point
                        failed_step_index = None
                        for i, call in enumerate(api_calls):
                            if call.get('status_code', 200) != 200:
                                failed_step_index = i
                                break

                        # Map API calls to progress steps (UI-expected keys)
                        step_mapping = {
                            "application_submit": "application_submit",
                            "apply_coupon": "apply_coupon",
                            "payment_checkout": "payment_checkout",
                            "admin_policy_list": "admin_policy_list",
                            "admin_policy_details": "admin_policy_details",
                            "customer_policy_list": "customer_policy_list",
                            "customer_policy_details": "customer_policy_details"
                        }

                        # Update progress based on API calls (use first call per step for DEV environment)
                        dev_calls = {}
                        for call in api_calls:
                            api_step = call.get('api_step')
                            status_code = call.get('status_code', 200)

                            # Since environment field may be missing, use the first call for each step
                            if api_step and api_step not in dev_calls:
                                dev_calls[api_step] = call

                        for api_step, call in dev_calls.items():
                            status_code = call.get('status_code', 200)
                            if api_step in step_mapping:
                                ui_step = step_mapping[api_step]

                                if status_code == 200:
                                    progress_map[ui_step] = "succeed"
                                else:
                                    progress_map[ui_step] = "failed"

                        # Mark steps after failure as "can_not_proceed"
                        if failed_step_index is not None:
                            # Find which step failed
                            failed_call = api_calls[failed_step_index]
                            failed_api_step = failed_call.get('api_step')

                            if failed_api_step in step_mapping:
                                failed_ui_step = step_mapping[failed_api_step]
                                failed_index = all_steps.index(failed_ui_step)

                                # Mark all subsequent steps as can_not_proceed
                                for i in range(failed_index + 1, len(all_steps)):
                                    progress_map[all_steps[i]] = "can_not_proceed"

                        # Generate execution ID for UI
                        execution_id = f"{username}_{session_id}_{combination_key}"

                        executions_progress[execution_id] = progress_map

                        logger.debug(f"[PROGRESS] Loaded progress for {combination_key}: {progress_map}")

                    except Exception as e:
                        logger.error(f"[PROGRESS] Failed to read progress file {progress_file}: {e}")
                        continue

            logger.info(f"[PROGRESS] Found {progress_files_found} progress files, returned {len(executions_progress)} execution progress entries")

            return {
                "session_id": session_id,
                "executions": executions_progress
            }

        except Exception as e:
            logger.error(f"[PROGRESS] Failed to get session progress for {session_id}: {e}", exc_info=True)
            return {
                "session_id": session_id,
                "executions": {}
            }