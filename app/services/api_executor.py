"""API Executor Service

Executes API calls for the 7-step insurance purchase flow.
Currently uses dummy/mock responses. Should be replaced with real API calls in Phase 5 (Production Integration).

API Steps:
1. Application Submit
2. Apply Coupon
3. Payment Checkout
4. Admin Policy List
5. Admin Policy Details
6. Customer Policy List
7. Customer Policy Details
"""

from typing import Dict, Any, Optional
import time
import logging

from app.models.api_call import APICall
from app.utils import dummy_payloads, dummy_responses

logger = logging.getLogger(__name__)


class APIExecutorService:
    """Service for executing API calls."""

    def __init__(self):
        self.api_steps = [
            "application_submit",
            "apply_coupon",
            "payment_checkout",
            "admin_policy_list",
            "admin_policy_details",
            "customer_policy_list",
            "customer_policy_details"
        ]

    def execute_api_call(
        self,
        execution_id: str,
        tab_id: str,
        api_step: str,
        environment: str,
        category: str,
        product_id: str,
        plan_id: str,
        auth_token: Optional[str] = None,
        application_id: Optional[str] = None
    ) -> APICall:
        """
        Execute a single API call for the 7-step flow.

        Args:
            execution_id: Execution identifier
            tab_id: Tab identifier (category_product_plan)
            api_step: API step name
            environment: Environment (DEV, QA, STAGING)
            category: Insurance category
            product_id: Product identifier
            plan_id: Plan identifier
            auth_token: Optional authentication token

        Returns:
            APICall model with execution results
        """
        try:
            call_id = f"call_{execution_id}_{api_step}_{environment.lower()}"

            if api_step not in self.api_steps:
                raise ValueError(f"Unknown API step: {api_step}")

            start_time = time.time()

            payload = dummy_payloads.get_payload_for_step(
                api_step,
                category,
                product_id,
                plan_id,
                **self._get_payload_kwargs(api_step, auth_token, application_id)
            )

            response = dummy_responses.get_response_for_step(
                api_step,
                category,
                product_id,
                plan_id,
                **self._get_response_kwargs(api_step, auth_token, application_id)
            )

            execution_time_ms = int((time.time() - start_time) * 1000)

            # Check response status - dummy responses can indicate failures
            status_code = response.get("status_code", 200)
            error = response.get("error") if status_code != 200 else None

            api_call = APICall(
                call_id=call_id,
                execution_id=execution_id,
                tab_id=tab_id,
                api_step=api_step,
                environment=environment,
                endpoint=f"/api/v1/{self._normalize_step_name(api_step)}",
                request_payload=payload,
                response_data=response,
                status_code=status_code,
                execution_time_ms=execution_time_ms,
                error=error
            )

            logger.info(
                f"API call executed: {api_step} in {environment} "
                f"({execution_time_ms}ms) - {status_code}"
            )

            return api_call

        except Exception as e:
            logger.error(f"Failed to execute API call {api_step}: {e}", exc_info=True)
            return APICall(
                call_id=f"call_{execution_id}_{api_step}_{environment.lower()}",
                execution_id=execution_id,
                tab_id=tab_id,
                api_step=api_step,
                environment=environment,
                endpoint=f"/api/v1/{self._normalize_step_name(api_step)}",
                request_payload={},
                response_data={},
                status_code=500,
                execution_time_ms=0,
                error=str(e)
            )

    def execute_7_step_flow(
        self,
        execution_id: str,
        tab_id: str,
        environment: str,
        category: str,
        product_id: str,
        plan_id: str,
        admin_token: Optional[str] = None,
        customer_token: Optional[str] = None
    ) -> list[APICall]:
        """
        Execute all 7 API steps for a Category+Product+Plan combination.

        Args:
            execution_id: Execution identifier
            tab_id: Tab identifier
            environment: Environment (DEV, QA, STAGING)
            category: Insurance category
            product_id: Product identifier
            plan_id: Plan identifier
            admin_token: Optional admin authentication token
            customer_token: Optional customer authentication token

        Returns:
            List of APICall models for all 7 steps
        """
        api_calls = []
        application_id = None

        for i, step in enumerate(self.api_steps):
            auth_token = self._select_auth_token(
                step,
                admin_token,
                customer_token
            )

            if step == "apply_coupon" and application_id:
                kwargs = {"application_id": application_id}
            elif step == "payment_checkout" and application_id:
                kwargs = {"application_id": application_id}
            else:
                kwargs = {}

            api_call = self.execute_api_call(
                execution_id=execution_id,
                tab_id=tab_id,
                api_step=step,
                environment=environment,
                category=category,
                product_id=product_id,
                plan_id=plan_id,
                auth_token=auth_token,
                application_id=application_id
            )

            if step == "application_submit" and api_call.status_code == 200:
                application_id = api_call.response_data.get("application_id")

            api_calls.append(api_call)

            if api_call.status_code != 200:
                logger.warning(
                    f"API call failed: {step} in {environment} - "
                    f"continuing with remaining steps"
                )

        logger.info(
            f"Completed 7-step flow for {tab_id} in {environment}: "
            f"{len([c for c in api_calls if c.status_code == 200])}/7 successful"
        )

        return api_calls

    def _select_auth_token(
        self,
        api_step: str,
        admin_token: Optional[str],
        customer_token: Optional[str]
    ) -> Optional[str]:
        """
        Select appropriate auth token for API step.

        Args:
            api_step: API step name
            admin_token: Admin authentication token
            customer_token: Customer authentication token

        Returns:
            Appropriate token or None
        """
        if "admin" in api_step:
            return admin_token
        elif "customer" in api_step:
            return customer_token
        return None

    def _get_payload_kwargs(
        self,
        api_step: str,
        auth_token: Optional[str],
        application_id: Optional[str]
    ) -> Dict[str, Any]:
        """Get kwargs for payload generation based on API step."""
        kwargs = {}

        if api_step in ["admin_policy_list", "customer_policy_list"]:
            token_key = "admin_token" if "admin" in api_step else "customer_token"
            kwargs[token_key] = auth_token or ""
        elif api_step in ["admin_policy_details", "customer_policy_details"]:
            token_key = "admin_token" if "admin" in api_step else "customer_token"
            kwargs[token_key] = auth_token or ""
            kwargs["policy_id"] = "policy_12345"

        if application_id and api_step in ["apply_coupon", "payment_checkout"]:
            kwargs["application_id"] = application_id

        return kwargs

    def _get_response_kwargs(
        self,
        api_step: str,
        auth_token: Optional[str],
        application_id: Optional[str]
    ) -> Dict[str, Any]:
        """Get kwargs for response generation based on API step."""
        return self._get_payload_kwargs(api_step, auth_token, application_id)

    def _normalize_step_name(self, api_step: str) -> str:
        """Convert API step name to endpoint format."""
        return api_step.replace("_", "-")
