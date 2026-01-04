"""Response Normalizer for API Comparison

This module provides utilities to normalize API responses before comparison.
Normalization removes environment-specific metadata, timestamps, and other
non-business-critical fields to focus comparison on meaningful differences.

Based on PRD comparison rules:
- Ignore: timestamps, created_at, updated_at, environment metadata
- Focus on: policy-related data, business-critical fields
"""

from typing import Dict, Any, Set
import copy


def normalize_response(
    response: Dict[str, Any],
    environment: str | None = None
) -> Dict[str, Any]:
    """
    Normalize an API response by removing non-comparable fields.

    This function creates a deep copy of the response and removes:
    - Timestamps (created_at, updated_at, timestamp, date fields ending in _at)
    - Environment-specific metadata
    - Request IDs, transaction references (unique identifiers)
    - Metadata fields not relevant for comparison

    Args:
        response: Original API response to normalize
        environment: Optional environment name (for tracking)

    Returns:
        Normalized response ready for comparison

    Example:
        >>> original = {"policy_id": "123", "created_at": "2026-01-01"}
        >>> normalized = normalize_response(original)
        >>> normalized  # {"policy_id": "123"}
    """
    if not isinstance(response, dict):
        return response

    normalized = copy.deepcopy(response)
    _remove_fields(normalized)

    return normalized


def _remove_fields(
    data: Any,
    depth: int = 0,
    max_depth: int = 10
) -> None:
    """
    Recursively remove non-comparable fields from data structure.

    Args:
        data: Data structure to clean (dict or list)
        depth: Current recursion depth
        max_depth: Maximum recursion depth to prevent infinite loops
    """
    if depth > max_depth:
        return

    if isinstance(data, dict):
        keys_to_remove = _get_keys_to_remove(data)
        for key in keys_to_remove:
            data.pop(key, None)

        for key, value in data.items():
            if isinstance(value, (dict, list)):
                _remove_fields(value, depth + 1, max_depth)

    elif isinstance(data, list):
        for item in data:
            if isinstance(item, (dict, list)):
                _remove_fields(item, depth + 1, max_depth)


def _get_keys_to_remove(data: Dict[str, Any]) -> Set[str]:
    """
    Identify keys that should be removed from comparison.

    Args:
        data: Dictionary to analyze

    Returns:
        Set of keys to remove
    """
    keys_to_remove = set()

    for key in data.keys():
        key_lower = key.lower()

        should_remove = (
            _is_timestamp_field(key_lower) or
            _is_environment_metadata(key_lower) or
            _is_unique_identifier(key_lower) or
            _is_internal_metadata(key_lower) or
            _is_non_business_field(key_lower)
        )

        if should_remove:
            keys_to_remove.add(key)

    return keys_to_remove


def _is_timestamp_field(key: str) -> bool:
    """
    Check if key is a timestamp field.

    Args:
        key: Field name (lowercase)

    Returns:
        True if field is timestamp-related
    """
    timestamp_fields = {
        "created_at",
        "updated_at",
        "timestamp",
        "date",
        "time",
        "datetime",
        "issued_at",
        "applied_at",
        "checkout_date",
        "payment_date",
        "application_date",
        "generated_at"
    }

    return any(field in key for field in timestamp_fields)


def _is_environment_metadata(key: str) -> bool:
    """
    Check if key is environment-specific metadata.

    Args:
        key: Field name (lowercase)

    Returns:
        True if field is environment metadata
    """
    env_fields = {
        "environment",
        "env",
        "server",
        "hostname",
        "region",
        "zone",
        "instance_id",
        "deployment_id"
    }

    return any(field in key for field in env_fields)


def _is_unique_identifier(key: str) -> bool:
    """
    Check if key is a unique identifier that may differ between environments.

    Args:
        key: Field name (lowercase)

    Returns:
        True if field is a unique identifier
    """
    unique_id_fields = {
        "request_id",
        "transaction_id",
        "correlation_id",
        "trace_id",
        "uuid",
        "guid",
        "session_id",
        "execution_id"
    }

    return any(field in key for field in unique_id_fields)


def _is_internal_metadata(key: str) -> bool:
    """
    Check if key is internal system metadata.

    Args:
        key: Field name (lowercase)

    Returns:
        True if field is internal metadata
    """
    internal_fields = {
        "version",
        "build",
        "service",
        "component",
        "module",
        "internal"
    }

    return any(field in key for field in internal_fields)


def _is_non_business_field(key: str) -> bool:
    """
    Check if key is a non-business field not relevant for comparison.

    Args:
        key: Field name (lowercase)

    Returns:
        True if field is non-business
    """
    non_business_fields = {
        "message",
        "status_code",
        "response_time",
        "latency",
        "processing_time",
        "debug",
        "trace"
    }

    return any(field in key for field in non_business_fields)


def normalize_list_of_responses(
    responses: list[Dict[str, Any]],
    environment: str | None = None
) -> list[Dict[str, Any]]:
    """
    Normalize a list of API responses.

    Args:
        responses: List of API responses to normalize
        environment: Optional environment name (for tracking)

    Returns:
        List of normalized responses
    """
    return [
        normalize_response(response, environment)
        for response in responses
    ]


def compare_normalized_responses(
    response1: Dict[str, Any],
    response2: Dict[str, Any],
    environment1: str | None = None,
    environment2: str | None = None
) -> Dict[str, Any]:
    """
    Compare two normalized responses and return basic comparison results.

    This is a simplified comparison. Use deepdiff library for
    comprehensive comparison in the ComparisonService.

    Args:
        response1: First normalized response
        response2: Second normalized response
        environment1: First environment name (e.g., "DEV")
        environment2: Second environment name (e.g., "STAGING")

    Returns:
        Basic comparison results
    """
    norm1 = normalize_response(response1, environment1)
    norm2 = normalize_response(response2, environment2)

    return {
        "identical": norm1 == norm2,
        "environment1": environment1 or "unknown",
        "environment2": environment2 or "unknown",
        "response1_keys": set(norm1.keys()),
        "response2_keys": set(norm2.keys()),
        "missing_in_response1": list(set(norm2.keys()) - set(norm1.keys())),
        "missing_in_response2": list(set(norm1.keys()) - set(norm2.keys()))
    }
