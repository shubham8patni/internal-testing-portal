"""Dummy Request Payloads for API Testing

This module provides mock request payloads for the 7-step insurance API flow.
All payloads are placeholders and should be replaced with real API payloads in Phase 5 (Production Integration).

API Steps:
1. Application Submit
2. Apply Coupon
3. Payment Checkout
4. Admin Policy List
5. Admin Policy Details
6. Customer Policy List
7. Customer Policy Details
"""

from typing import Dict, Any
from datetime import datetime


def get_application_submit_payload(
    category: str,
    product_id: str,
    plan_id: str,
    customer_data: Dict[str, Any] | None = None
) -> Dict[str, Any]:
    """
    Generate dummy payload for Application Submit API.

    Args:
        category: Insurance category (MV4, MV2, PET, PA, TRAVEL)
        product_id: Product identifier (TOKIO_MARINE, SOMPO, ZURICH)
        plan_id: Plan identifier (COMPREHENSIVE, TOTAL_LOSS, etc.)
        customer_data: Optional customer details override

    Returns:
        Mock request payload for application submission
    """
    default_customer = {
        "customer_name": "John Doe",
        "customer_email": "john.doe@example.com",
        "customer_phone": "+60123456789",
        "date_of_birth": "1990-01-01",
        "address": {
            "street": "123 Main Street",
            "city": "Kuala Lumpur",
            "state": "Selangor",
            "postal_code": "50000",
            "country": "Malaysia"
        }
    }

    payload = {
        "category": category,
        "product_id": product_id,
        "plan_id": plan_id,
        "customer_data": customer_data or default_customer,
        "policy_start_date": "2026-02-01",
        "policy_end_date": "2027-01-31",
        "sum_insured": 50000,
        "application_date": datetime.now().isoformat()
    }

    return payload


def get_apply_coupon_payload(
    application_id: str,
    coupon_code: str = "SAVE10"
) -> Dict[str, Any]:
    """
    Generate dummy payload for Apply Coupon API.

    Args:
        application_id: ID of the submitted application
        coupon_code: Discount coupon code

    Returns:
        Mock request payload for coupon application
    """
    return {
        "application_id": application_id,
        "coupon_code": coupon_code,
        "applied_at": datetime.now().isoformat()
    }


def get_payment_checkout_payload(
    application_id: str,
    payment_method: str = "CREDIT_CARD",
    payment_details: Dict[str, Any] | None = None
) -> Dict[str, Any]:
    """
    Generate dummy payload for Payment Checkout API.

    Args:
        application_id: ID of the application to pay for
        payment_method: Payment method (CREDIT_CARD, FPX, etc.)
        payment_details: Optional payment method specific details

    Returns:
        Mock request payload for payment checkout
    """
    default_payment_details = {
        "card_number": "4111111111111111",
        "card_holder": "JOHN DOE",
        "expiry_month": "12",
        "expiry_year": "2027",
        "cvv": "123"
    }

    return {
        "application_id": application_id,
        "payment_method": payment_method,
        "payment_details": payment_details or default_payment_details,
        "amount": 500.00,
        "currency": "MYR",
        "checkout_date": datetime.now().isoformat()
    }


def get_admin_policy_list_payload(
    admin_token: str,
    filters: Dict[str, Any] | None = None
) -> Dict[str, Any]:
    """
    Generate dummy payload for Admin Policy List API.

    Args:
        admin_token: Admin authentication token
        filters: Optional filters for policy list

    Returns:
        Mock request payload for admin policy list
    """
    return {
        "admin_token": admin_token,
        "filters": filters or {},
        "page": 1,
        "limit": 50
    }


def get_admin_policy_details_payload(
    admin_token: str,
    policy_id: str
) -> Dict[str, Any]:
    """
    Generate dummy payload for Admin Policy Details API.

    Args:
        admin_token: Admin authentication token
        policy_id: ID of the policy to retrieve

    Returns:
        Mock request payload for admin policy details
    """
    return {
        "admin_token": admin_token,
        "policy_id": policy_id
    }


def get_customer_policy_list_payload(
    customer_token: str,
    filters: Dict[str, Any] | None = None
) -> Dict[str, Any]:
    """
    Generate dummy payload for Customer Policy List API.

    Args:
        customer_token: Customer authentication token
        filters: Optional filters for policy list

    Returns:
        Mock request payload for customer policy list
    """
    return {
        "customer_token": customer_token,
        "filters": filters or {},
        "page": 1,
        "limit": 50
    }


def get_customer_policy_details_payload(
    customer_token: str,
    policy_id: str
) -> Dict[str, Any]:
    """
    Generate dummy payload for Customer Policy Details API.

    Args:
        customer_token: Customer authentication token
        policy_id: ID of the policy to retrieve

    Returns:
        Mock request payload for customer policy details
    """
    return {
        "customer_token": customer_token,
        "policy_id": policy_id
    }


def get_payload_for_step(
    step: str,
    category: str,
    product_id: str,
    plan_id: str,
    **kwargs
) -> Dict[str, Any]:
    """
    Get dummy payload for a specific API step.

    Args:
        step: API step name (1-7)
        category: Insurance category
        product_id: Product identifier
        plan_id: Plan identifier
        **kwargs: Additional parameters for specific steps

    Returns:
        Mock request payload for the specified step

    Raises:
        ValueError: If step is not recognized
    """
    step_map = {
        "application_submit": get_application_submit_payload,
        "apply_coupon": get_apply_coupon_payload,
        "payment_checkout": get_payment_checkout_payload,
        "admin_policy_list": get_admin_policy_list_payload,
        "admin_policy_details": get_admin_policy_details_payload,
        "customer_policy_list": get_customer_policy_list_payload,
        "customer_policy_details": get_customer_policy_details_payload
    }

    if step not in step_map:
        raise ValueError(f"Unknown API step: {step}")

    payload_func = step_map[step]

    # Enhanced handling for dynamic data
    if step == "application_submit":
        return payload_func(category, product_id, plan_id, kwargs.get("customer_data"))
    elif step == "apply_coupon":
        application_id = kwargs.get("application_id", "app_12345")
        coupon_code = kwargs.get("coupon_code", "SAVE10")
        return payload_func(application_id, coupon_code)
    elif step == "payment_checkout":
        application_id = kwargs.get("application_id", "app_12345")
        return payload_func(application_id, kwargs.get("payment_method", "CREDIT_CARD"), kwargs.get("payment_details"))
    elif step in ["admin_policy_list", "customer_policy_list"]:
        token_key = "admin_token" if "admin" in step else "customer_token"
        return payload_func(kwargs.get(token_key, ""), kwargs.get("filters"))
    elif step in ["admin_policy_details", "customer_policy_details"]:
        token_key = "admin_token" if "admin" in step else "customer_token"
        return payload_func(kwargs.get(token_key, ""), kwargs.get("policy_id", "policy_12345"))
    else:
        return payload_func()
