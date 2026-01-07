"""Individual API Functions for Sequential Execution

This module contains dedicated functions for each of the 7 API steps in the insurance purchase flow.
Each function handles the complete API call process including payload generation, response processing,
and standardized error handling.

API Steps:
1. Application Submit - Creates new insurance application
2. Apply Coupon - Applies discount coupon to application
3. Payment Checkout - Processes payment for application
4. Admin Policy List - Lists policies (admin view)
5. Admin Policy Details - Gets specific policy details (admin view)
6. Customer Policy List - Lists policies (customer view)
7. Customer Policy Details - Gets specific policy details (customer view)
"""

from typing import Dict, Any, Optional
import logging

from app.utils import dummy_payloads, dummy_responses

logger = logging.getLogger(__name__)

def call_application_submit(combination: Dict[str, str]) -> Dict[str, Any]:
    """
    Call Application Submit API.

    Creates a new insurance application.

    Args:
        combination: Dict containing category, product_id, plan_id

    Returns:
        Dict with standardized API response
    """
    try:
        logger.debug(f"Calling application_submit for {combination}")

        # Generate payload
        payload = dummy_payloads.get_payload_for_step(
            "application_submit",
            combination["category"],
            combination["product_id"],
            combination["plan_id"]
        )

        # Get response
        response = dummy_responses.get_response_for_step(
            "application_submit",
            combination["category"],
            combination["product_id"],
            combination["plan_id"]
        )

        # Validate response
        if not response or response.get("status") != "success":
            logger.error(f"Application submit failed: {response}")
            return {
                "success": False,
                "error": response.get("error", "Application submission failed"),
                "status_code": response.get("status_code", 500),
                "api_step": "application_submit"
            }

        logger.info(f"Application submitted successfully: {response.get('application_id')}")
        return {
            "success": True,
            "data": response,
            "application_id": response.get("application_id"),
            "api_step": "application_submit",
            "status_code": 200
        }

    except Exception as e:
        logger.error(f"Application submit error: {e}", exc_info=True)
        return {
            "success": False,
            "error": f"Application submit failed: {str(e)}",
            "status_code": 500,
            "api_step": "application_submit"
        }

def call_apply_coupon(combination: Dict[str, str], application_id: str) -> Dict[str, Any]:
    """
    Call Apply Coupon API.

    Applies a discount coupon to an existing application.

    Args:
        combination: Dict containing category, product_id, plan_id
        application_id: ID of the application to apply coupon to

    Returns:
        Dict with standardized API response
    """
    try:
        logger.debug(f"Calling apply_coupon for application {application_id}")

        # Generate payload with application_id
        payload = dummy_payloads.get_payload_for_step(
            "apply_coupon",
            "", "", "",  # Not needed for this step
            application_id=application_id
        )

        # Get response
        response = dummy_responses.get_response_for_step(
            "apply_coupon",
            "", "", "",  # Not needed for this step
            application_id=application_id
        )

        # Validate response
        if not response or response.get("status") != "success":
            logger.error(f"Apply coupon failed: {response}")
            return {
                "success": False,
                "error": response.get("error", "Coupon application failed"),
                "status_code": response.get("status_code", 500),
                "api_step": "apply_coupon"
            }

        logger.info(f"Coupon applied successfully to application {application_id}")
        return {
            "success": True,
            "data": response,
            "application_id": application_id,
            "api_step": "apply_coupon",
            "status_code": 200
        }

    except Exception as e:
        logger.error(f"Apply coupon error: {e}", exc_info=True)
        return {
            "success": False,
            "error": f"Coupon application failed: {str(e)}",
            "status_code": 500,
            "api_step": "apply_coupon"
        }

def call_payment_checkout(combination: Dict[str, str], application_id: str) -> Dict[str, Any]:
    """
    Call Payment Checkout API.

    Processes payment for an insurance application.

    Args:
        combination: Dict containing category, product_id, plan_id
        application_id: ID of the application to process payment for

    Returns:
        Dict with standardized API response
    """
    try:
        logger.debug(f"Calling payment_checkout for application {application_id}")

        # Generate payload with application_id
        payload = dummy_payloads.get_payload_for_step(
            "payment_checkout",
            "", "", "",  # Not needed for this step
            application_id=application_id
        )

        # Get response (pass combination for failure logic)
        response = dummy_responses.get_response_for_step(
            "payment_checkout",
            combination["category"],
            combination["product_id"],
            combination["plan_id"],
            application_id=application_id
        )

        # Validate response
        if not response or response.get("status") != "success":
            logger.error(f"Payment checkout failed: {response}")
            return {
                "success": False,
                "error": response.get("error", "Payment processing failed"),
                "status_code": response.get("status_code", 500),
                "api_step": "payment_checkout"
            }

        logger.info(f"Payment processed successfully for application {application_id}")
        return {
            "success": True,
            "data": response,
            "application_id": application_id,
            "policy_number": response.get("policy_number"),
            "api_step": "payment_checkout",
            "status_code": 200
        }

    except Exception as e:
        logger.error(f"Payment checkout error: {e}", exc_info=True)
        return {
            "success": False,
            "error": f"Payment processing failed: {str(e)}",
            "status_code": 500,
            "api_step": "payment_checkout"
        }

def call_admin_policy_list(combination: Dict[str, str]) -> Dict[str, Any]:
    """
    Call Admin Policy List API.

    Retrieves list of policies for admin view.

    Args:
        combination: Dict containing category, product_id, plan_id

    Returns:
        Dict with standardized API response
    """
    try:
        logger.debug(f"Calling admin_policy_list for {combination}")

        # Generate payload
        payload = dummy_payloads.get_payload_for_step(
            "admin_policy_list",
            "", "", "",  # Not needed for this step
            admin_token="admin_token_123"
        )

        # Get response
        response = dummy_responses.get_response_for_step(
            "admin_policy_list",
            "", "", "",  # Not needed for this step
            admin_token="admin_token_123"
        )

        # Validate response
        if not response or response.get("status") != "success":
            logger.error(f"Admin policy list failed: {response}")
            return {
                "success": False,
                "error": response.get("error", "Failed to retrieve admin policy list"),
                "status_code": response.get("status_code", 500),
                "api_step": "admin_policy_list"
            }

        logger.info(f"Admin policy list retrieved successfully: {len(response.get('policies', []))} policies")
        return {
            "success": True,
            "data": response,
            "policies": response.get("policies", []),
            "api_step": "admin_policy_list",
            "status_code": 200
        }

    except Exception as e:
        logger.error(f"Admin policy list error: {e}", exc_info=True)
        return {
            "success": False,
            "error": f"Failed to retrieve admin policy list: {str(e)}",
            "status_code": 500,
            "api_step": "admin_policy_list"
        }

def call_admin_policy_details(combination: Dict[str, str], policy_id: str) -> Dict[str, Any]:
    """
    Call Admin Policy Details API.

    Retrieves detailed information for a specific policy (admin view).

    Args:
        combination: Dict containing category, product_id, plan_id
        policy_id: ID of the policy to retrieve

    Returns:
        Dict with standardized API response
    """
    try:
        logger.debug(f"Calling admin_policy_details for policy {policy_id}")

        # Generate payload
        payload = dummy_payloads.get_payload_for_step(
            "admin_policy_details",
            "", "", "",  # Not needed for this step
            admin_token="admin_token_123",
            policy_id=policy_id
        )

        # Get response
        response = dummy_responses.get_response_for_step(
            "admin_policy_details",
            "", "", "",  # Not needed for this step
            policy_id=policy_id
        )

        # Validate response
        if not response or response.get("status") != "success":
            logger.error(f"Admin policy details failed: {response}")
            return {
                "success": False,
                "error": response.get("error", "Failed to retrieve admin policy details"),
                "status_code": response.get("status_code", 500),
                "api_step": "admin_policy_details"
            }

        logger.info(f"Admin policy details retrieved successfully for policy {policy_id}")
        return {
            "success": True,
            "data": response,
            "policy": response,
            "api_step": "admin_policy_details",
            "status_code": 200
        }

    except Exception as e:
        logger.error(f"Admin policy details error: {e}", exc_info=True)
        return {
            "success": False,
            "error": f"Failed to retrieve admin policy details: {str(e)}",
            "status_code": 500,
            "api_step": "admin_policy_details"
        }

def call_customer_policy_list(combination: Dict[str, str]) -> Dict[str, Any]:
    """
    Call Customer Policy List API.

    Retrieves list of policies for customer view.

    Args:
        combination: Dict containing category, product_id, plan_id

    Returns:
        Dict with standardized API response
    """
    try:
        logger.debug(f"Calling customer_policy_list for {combination}")

        # Generate payload
        payload = dummy_payloads.get_payload_for_step(
            "customer_policy_list",
            "", "", "",  # Not needed for this step
            customer_token="customer_token_123"
        )

        # Get response
        response = dummy_responses.get_response_for_step(
            "customer_policy_list",
            "", "", "",  # Not needed for this step
            customer_token="customer_token_123"
        )

        # Validate response
        if not response or response.get("status") != "success":
            logger.error(f"Customer policy list failed: {response}")
            return {
                "success": False,
                "error": response.get("error", "Failed to retrieve customer policy list"),
                "status_code": response.get("status_code", 500),
                "api_step": "customer_policy_list"
            }

        logger.info(f"Customer policy list retrieved successfully: {len(response.get('policies', []))} policies")
        return {
            "success": True,
            "data": response,
            "policies": response.get("policies", []),
            "api_step": "customer_policy_list",
            "status_code": 200
        }

    except Exception as e:
        logger.error(f"Customer policy list error: {e}", exc_info=True)
        return {
            "success": False,
            "error": f"Failed to retrieve customer policy list: {str(e)}",
            "status_code": 500,
            "api_step": "customer_policy_list"
        }

def call_customer_policy_details(combination: Dict[str, str], policy_id: str) -> Dict[str, Any]:
    """
    Call Customer Policy Details API.

    Retrieves detailed information for a specific policy (customer view).

    Args:
        combination: Dict containing category, product_id, plan_id
        policy_id: ID of the policy to retrieve

    Returns:
        Dict with standardized API response
    """
    try:
        logger.debug(f"Calling customer_policy_details for policy {policy_id}")

        # Generate payload
        payload = dummy_payloads.get_payload_for_step(
            "customer_policy_details",
            "", "", "",  # Not needed for this step
            customer_token="customer_token_123",
            policy_id=policy_id
        )

        # Get response
        response = dummy_responses.get_response_for_step(
            "customer_policy_details",
            "", "", "",  # Not needed for this step
            policy_id=policy_id
        )

        # Validate response
        if not response or response.get("status") != "success":
            logger.error(f"Customer policy details failed: {response}")
            return {
                "success": False,
                "error": response.get("error", "Failed to retrieve customer policy details"),
                "status_code": response.get("status_code", 500),
                "api_step": "customer_policy_details"
            }

        logger.info(f"Customer policy details retrieved successfully for policy {policy_id}")
        return {
            "success": True,
            "data": response,
            "policy": response,
            "api_step": "customer_policy_details",
            "status_code": 200
        }

    except Exception as e:
        logger.error(f"Customer policy details error: {e}", exc_info=True)
        return {
            "success": False,
            "error": f"Failed to retrieve customer policy details: {str(e)}",
            "status_code": 500,
            "api_step": "customer_policy_details"
        }