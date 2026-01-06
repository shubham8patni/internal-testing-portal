"""Dummy API Responses for Testing

This module provides mock API responses for the 7-step insurance API flow.
All responses are placeholders and should be replaced with real API responses in Phase 5 (Production Integration).

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
import uuid


def get_application_submit_response(
    category: str,
    product_id: str,
    plan_id: str
) -> Dict[str, Any]:
    """
    Generate dummy response for Application Submit API.

    Args:
        category: Insurance category
        product_id: Product identifier
        plan_id: Plan identifier

    Returns:
        Mock API response for application submission
    """
    application_id = f"app_{uuid.uuid4().hex[:12]}"
    
    return {
        "status": "success",
        "application_id": application_id,
        "category": category,
        "product_id": product_id,
        "plan_id": plan_id,
        "premium": 500.00,
        "currency": "MYR",
        "application_date": "2026-01-03T00:00:00Z",
        "next_step": "apply_coupon",
        "message": "Application submitted successfully"
    }


def get_apply_coupon_response(
    application_id: str,
    coupon_code: str
) -> Dict[str, Any]:
    """
    Generate dummy response for Apply Coupon API.

    Args:
        application_id: Application ID
        coupon_code: Coupon code used

    Returns:
        Mock API response for coupon application
    """
    discount_percent = 10 if coupon_code == "SAVE10" else 5
    
    return {
        "status": "success",
        "application_id": application_id,
        "coupon_code": coupon_code,
        "discount_percent": discount_percent,
        "original_amount": 500.00,
        "discount_amount": 50.00,
        "new_amount": 450.00,
        "currency": "MYR",
        "message": f"Coupon applied successfully. You saved {discount_percent}%!"
    }


def get_payment_checkout_response(
    application_id: str,
    payment_method: str
) -> Dict[str, Any]:
    """
    Generate dummy response for Payment Checkout API.

    Args:
        application_id: Application ID
        payment_method: Payment method used

    Returns:
        Mock API response for payment checkout
    """
    payment_id = f"pay_{uuid.uuid4().hex[:12]}"
    transaction_ref = f"TXN{uuid.uuid4().hex[:10].upper()}"
    
    return {
        "status": "success",
        "application_id": application_id,
        "payment_id": payment_id,
        "transaction_ref": transaction_ref,
        "payment_method": payment_method,
        "amount": 450.00,
        "currency": "MYR",
        "payment_date": "2026-01-03T00:00:00Z",
        "payment_status": "completed",
        "policy_number": f"POL{uuid.uuid4().hex[:8].upper()}",
        "message": "Payment processed successfully"
    }


def get_admin_policy_list_response(
    admin_token: str
) -> Dict[str, Any]:
    """
    Generate dummy response for Admin Policy List API.

    Args:
        admin_token: Admin authentication token

    Returns:
        Mock API response for admin policy list
    """
    return {
        "status": "success",
        "admin_token": admin_token,
        "total_policies": 2,
        "page": 1,
        "limit": 50,
        "policies": [
            {
                "policy_id": f"policy_{uuid.uuid4().hex[:12]}",
                "policy_number": f"POL{uuid.uuid4().hex[:8].upper()}",
                "customer_name": "John Doe",
                "category": "MV4",
                "product_id": "TOKIO_MARINE",
                "plan_id": "COMPREHENSIVE",
                "premium": 450.00,
                "policy_status": "active",
                "issue_date": "2026-01-03"
            },
            {
                "policy_id": f"policy_{uuid.uuid4().hex[:12]}",
                "policy_number": f"POL{uuid.uuid4().hex[:8].upper()}",
                "customer_name": "Jane Smith",
                "category": "TRAVEL",
                "product_id": "SOMPO",
                "plan_id": "TRAVEL_COMPREHENSIVE",
                "premium": 300.00,
                "policy_status": "active",
                "issue_date": "2026-01-02"
            }
        ]
    }


def get_admin_policy_details_response(
    policy_id: str
) -> Dict[str, Any]:
    """
    Generate dummy response for Admin Policy Details API.

    Args:
        policy_id: Policy ID

    Returns:
        Mock API response for admin policy details
    """
    return {
        "status": "success",
        "policy_id": policy_id,
        "policy_number": f"POL{uuid.uuid4().hex[:8].upper()}",
        "customer_name": "John Doe",
        "customer_email": "john.doe@example.com",
        "category": "MV4",
        "product_id": "TOKIO_MARINE",
        "plan_id": "COMPREHENSIVE",
        "premium": 450.00,
        "sum_insured": 50000.00,
        "currency": "MYR",
        "policy_status": "active",
        "coverage": {
            "vehicle_type": "Car",
            "vehicle_make": "Toyota",
            "vehicle_model": "Camry",
            "vehicle_year": "2022",
            "registration_number": "ABC1234"
        },
        "benefits": [
            "Third Party Liability",
            "Own Damage",
            "Windscreen Coverage",
            "Legal Liability to Passengers"
        ],
        "issue_date": "2026-01-03",
        "start_date": "2026-02-01",
        "end_date": "2027-01-31"
    }


def get_customer_policy_list_response(
    customer_token: str
) -> Dict[str, Any]:
    """
    Generate dummy response for Customer Policy List API.

    Args:
        customer_token: Customer authentication token

    Returns:
        Mock API response for customer policy list
    """
    return {
        "status": "success",
        "customer_token": customer_token,
        "total_policies": 1,
        "page": 1,
        "limit": 50,
        "policies": [
            {
                "policy_id": f"policy_{uuid.uuid4().hex[:12]}",
                "policy_number": f"POL{uuid.uuid4().hex[:8].upper()}",
                "category": "MV4",
                "product_id": "TOKIO_MARINE",
                "plan_id": "COMPREHENSIVE",
                "premium": 450.00,
                "policy_status": "active",
                "renewal_date": "2027-01-31"
            }
        ]
    }


def get_customer_policy_details_response(
    policy_id: str
) -> Dict[str, Any]:
    """
    Generate dummy response for Customer Policy Details API.

    Args:
        policy_id: Policy ID

    Returns:
        Mock API response for customer policy details
    """
    return {
        "status": "success",
        "policy_id": policy_id,
        "policy_number": f"POL{uuid.uuid4().hex[:8].upper()}",
        "category": "MV4",
        "product_id": "TOKIO_MARINE",
        "plan_id": "COMPREHENSIVE",
        "premium": 450.00,
        "sum_insured": 50000.00,
        "currency": "MYR",
        "policy_status": "active",
        "start_date": "2026-02-01",
        "end_date": "2027-01-31",
        "benefits": [
            "Third Party Liability",
            "Own Damage",
            "Windscreen Coverage",
            "Legal Liability to Passengers"
        ],
        "exclusions": [
            "Driving under influence",
            "Unauthorized driver",
            "Racing competitions"
        ],
        "contact_support": {
            "phone": "+601800123456",
            "email": "support@insurance.com",
            "hours": "24/7"
        }
    }


def get_response_for_step(
    step: str,
    category: str,
    product_id: str,
    plan_id: str,
    **kwargs
) -> Dict[str, Any]:
    """
    Get dummy response for a specific API step.

    Args:
        step: API step name (1-7)
        category: Insurance category
        product_id: Product identifier
        plan_id: Plan identifier
        **kwargs: Additional parameters for specific steps

    Returns:
        Mock API response for the specified step

    Raises:
        ValueError: If step is not recognized
    """
    step_map = {
        "application_submit": get_application_submit_response,
        "apply_coupon": get_apply_coupon_response,
        "payment_checkout": get_payment_checkout_response,
        "admin_policy_list": get_admin_policy_list_response,
        "admin_policy_details": get_admin_policy_details_response,
        "customer_policy_list": get_customer_policy_list_response,
        "customer_policy_details": get_customer_policy_details_response
    }

    if step not in step_map:
        raise ValueError(f"Unknown API step: {step}")

    response_func = step_map[step]

    # Enhanced handling for consistency
    if step == "application_submit":
        return response_func(category, product_id, plan_id)
    elif step == "apply_coupon":
        application_id = kwargs.get("application_id", "app_12345")
        coupon_code = kwargs.get("coupon_code", "SAVE10")
        return response_func(application_id, coupon_code)
    elif step == "payment_checkout":
        application_id = kwargs.get("application_id", "app_12345")
        payment_method = kwargs.get("payment_method", "CREDIT_CARD")
        return response_func(application_id, payment_method)
    elif step in ["admin_policy_list", "customer_policy_list"]:
        token_key = "admin_token" if "admin" in step else "customer_token"
        return response_func(kwargs.get(token_key, ""))
    elif step in ["admin_policy_details", "customer_policy_details"]:
        return response_func(kwargs.get("policy_id", "policy_12345"))
    else:
        return response_func()
