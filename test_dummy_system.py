#!/usr/bin/env python3
"""
Test script to verify dummy system functionality independently.
This tests Fix 1: Verify Dummy System Components
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.utils import dummy_payloads, dummy_responses

def test_dummy_payloads():
    """Test payload generation for all 7 API steps."""
    print("🔍 Testing Dummy Payloads...")

    test_cases = [
        ("application_submit", "MV4", "TOKIO_MARINE", "COMPREHENSIVE"),
        ("apply_coupon", None, None, None),  # Uses application_id from kwargs
        ("payment_checkout", None, None, None),  # Uses application_id from kwargs
        ("admin_policy_list", None, None, None),  # Uses admin_token from kwargs
        ("admin_policy_details", None, None, None),  # Uses admin_token from kwargs
        ("customer_policy_list", None, None, None),  # Uses customer_token from kwargs
        ("customer_policy_details", None, None, None),  # Uses customer_token from kwargs
    ]

    for step, category, product_id, plan_id in test_cases:
        try:
            payload = None
            if step == "application_submit":
                payload = dummy_payloads.get_payload_for_step(step, category, product_id, plan_id)
            elif step in ["apply_coupon", "payment_checkout"]:
                payload = dummy_payloads.get_payload_for_step(step, "", "", "", application_id="app_12345")
            elif "admin" in step:
                payload = dummy_payloads.get_payload_for_step(step, "", "", "", admin_token="admin_token_123")
            elif "customer" in step:
                payload = dummy_payloads.get_payload_for_step(step, "", "", "", customer_token="customer_token_123")

            assert payload is not None, f"Payload is None for {step}"
            assert isinstance(payload, dict), f"Payload is not dict for {step}"
            assert len(payload) > 0, f"Payload is empty for {step}"

            print(f"✅ {step}: Payload generated successfully ({len(payload)} fields)")

        except Exception as e:
            print(f"❌ {step}: FAILED - {e}")
            return False

    return True

def test_dummy_responses():
    """Test response generation for all 7 API steps."""
    print("\n🔍 Testing Dummy Responses...")

    test_cases = [
        ("application_submit", "MV4", "TOKIO_MARINE", "COMPREHENSIVE"),
        ("apply_coupon", None, None, None),  # Uses application_id from kwargs
        ("payment_checkout", None, None, None),  # Uses application_id from kwargs
        ("admin_policy_list", None, None, None),  # Uses admin_token from kwargs
        ("admin_policy_details", None, None, None),  # Uses policy_id from kwargs
        ("customer_policy_list", None, None, None),  # Uses customer_token from kwargs
        ("customer_policy_details", None, None, None),  # Uses policy_id from kwargs
    ]

    for step, category, product_id, plan_id in test_cases:
        try:
            response = None
            if step == "application_submit":
                response = dummy_responses.get_response_for_step(step, category, product_id, plan_id)
            elif step in ["apply_coupon", "payment_checkout"]:
                response = dummy_responses.get_response_for_step(step, "", "", "", application_id="app_12345")
            elif "admin" in step:
                if step == "admin_policy_list":
                    response = dummy_responses.get_response_for_step(step, "", "", "", admin_token="admin_token_123")
                else:  # admin_policy_details
                    response = dummy_responses.get_response_for_step(step, "", "", "", policy_id="policy_12345")
            elif "customer" in step:
                if step == "customer_policy_list":
                    response = dummy_responses.get_response_for_step(step, "", "", "", customer_token="customer_token_123")
                else:  # customer_policy_details
                    response = dummy_responses.get_response_for_step(step, "", "", "", policy_id="policy_12345")

            assert response is not None, f"Response is None for {step}"
            assert isinstance(response, dict), f"Response is not dict for {step}"
            assert len(response) > 0, f"Response is empty for {step}"
            assert "status" in response, f"Response missing 'status' for {step}"

            # Check for critical fields
            if step == "application_submit":
                assert "application_id" in response, f"Response missing application_id for {step}"
            elif step == "payment_checkout":
                assert "policy_number" in response, f"Response missing policy_number for {step}"

            print(f"✅ {step}: Response generated successfully ({len(response)} fields)")

        except Exception as e:
            print(f"❌ {step}: FAILED - {e}")
            return False

    return True

def test_api_executor_integration():
    """Test API executor can call dummy functions."""
    print("\n🔍 Testing API Executor Integration...")

    try:
        from app.services.api_executor import APIExecutorService

        executor = APIExecutorService()

        # Test a simple API call
        call = executor.execute_api_call(
            execution_id="test_exec_123",
            tab_id="test_tab_123",
            api_step="application_submit",
            environment="DEV",
            category="MV4",
            product_id="TOKIO_MARINE",
            plan_id="COMPREHENSIVE"
        )

        assert call is not None, "API call returned None"
        assert call.status_code == 200, f"API call failed with status {call.status_code}"
        assert call.response_data is not None, "Response data is None"
        assert "application_id" in call.response_data, "Response missing application_id"

        print("✅ API Executor: Integration test passed")
        return True

    except Exception as e:
        print(f"❌ API Executor: Integration test FAILED - {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all dummy system tests."""
    print("🚀 Starting Dummy System Verification Tests")
    print("=" * 50)

    results = []

    # Test 1: Payloads
    results.append(test_dummy_payloads())

    # Test 2: Responses
    results.append(test_dummy_responses())

    # Test 3: Integration
    results.append(test_api_executor_integration())

    print("\n" + "=" * 50)
    print("📊 Test Results:")

    passed = sum(results)
    total = len(results)

    for i, result in enumerate(results, 1):
        status = "✅ PASSED" if result else "❌ FAILED"
        test_name = ["Payload Generation", "Response Generation", "API Executor Integration"][i-1]
        print(f"  Test {i}: {test_name} - {status}")

    print(f"\n🎯 Overall Result: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All dummy system tests PASSED! The issue is likely in execution flow, not dummy data.")
        return True
    else:
        print("⚠️  Some tests FAILED. The dummy system has issues that need fixing.")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)</content>
<parameter name="filePath">test_dummy_system.py