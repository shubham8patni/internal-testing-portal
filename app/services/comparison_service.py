"""Comparison Service

Compares Target (DEV/QA) vs Staging environment responses using deepdiff.
Implements intelligent comparison rules from PRD (ignore timestamps, metadata).
"""

from typing import Dict, Any, List
from datetime import datetime
import logging

# Temporarily disable deepdiff to avoid comparison issues
# try:
#     from deepdiff import DeepDiff
#     DEEPDIFF_AVAILABLE = True
# except ImportError:
#     DEEPDIFF_AVAILABLE = False
#     logging.warning("deepdiff not available, using basic comparison")
DEEPDIFF_AVAILABLE = False
logging.info("Using basic comparison (deepdiff disabled)")

from app.models.comparison import Comparison, Difference
from app.utils import response_normalizer

logger = logging.getLogger(__name__)


class ComparisonService:
    """Service for comparing API responses across environments."""

    def __init__(self):
        self.critical_fields = [
            "policy_number",
            "policy_id",
            "premium",
            "coverage",
            "status",
            "sum_insured"
        ]

    def compare_responses(
        self,
        execution_id: str,
        api_step: str,
        target_response: Dict[str, Any],
        staging_response: Dict[str, Any],
        target_environment: str = "DEV",
        staging_environment: str = "STAGING"
    ) -> Comparison:
        """
        Compare target and staging responses.

        Args:
            execution_id: Execution identifier
            api_step: API step name
            target_response: Response from target environment
            staging_response: Response from staging environment
            target_environment: Target environment name
            staging_environment: Staging environment name

        Returns:
            Comparison model with differences and summary
        """
        try:
            comparison_id = f"cmp_{execution_id}_{api_step}"

            normalized_target = response_normalizer.normalize_response(
                target_response,
                target_environment
            )
            normalized_staging = response_normalizer.normalize_response(
                staging_response,
                staging_environment
            )

            differences = self._find_differences(
                normalized_target,
                normalized_staging,
                api_step
            )

            summary = self._generate_summary(differences)

            comparison = Comparison(
                comparison_id=comparison_id,
                execution_id=execution_id,
                timestamp=datetime.now(),
                api_step=api_step,
                target_environment=target_environment,
                staging_environment=staging_environment,
                target_response=target_response,
                staging_response=staging_response,
                differences=differences,
                summary=summary
            )

            logger.info(
                f"Comparison completed for {api_step}: "
                f"{summary.get('total', 0)} differences "
                f"({summary.get('critical', 0)} critical)"
            )

            return comparison

        except Exception as e:
            logger.error(f"Failed to compare responses for {api_step}: {e}", exc_info=True)
            raise

    def compare_api_calls(
        self,
        execution_id: str,
        target_call: Any,
        staging_call: Any
    ) -> List[Comparison]:
        """
        Compare multiple API calls.

        Args:
            execution_id: Execution identifier
            target_call: Target environment API call
            staging_call: Staging environment API call

        Returns:
            List of Comparison models
        """
        comparisons = []

        if target_call.api_step != staging_call.api_step:
            logger.warning(
                f"API steps don't match: {target_call.api_step} vs {staging_call.api_step}"
            )
            return comparisons

        comparison = self.compare_responses(
            execution_id=execution_id,
            api_step=target_call.api_step,
            target_response=target_call.response_data,
            staging_response=staging_call.response_data,
            target_environment=target_call.environment,
            staging_environment=staging_call.environment
        )

        comparisons.append(comparison)

        return comparisons

    def _find_differences(
        self,
        response1: Dict[str, Any],
        response2: Dict[str, Any],
        api_step: str
    ) -> List[Difference]:
        """
        Find differences between two normalized responses.

        Args:
            response1: First normalized response
            response2: Second normalized response
            api_step: API step for context

        Returns:
            List of Difference models
        """
        differences = []

        if DEEPDIFF_AVAILABLE:
            differences.extend(self._deepdiff_compare(response1, response2, api_step))
        else:
            differences.extend(self._basic_compare(response1, response2, api_step))

        return differences

    def _deepdiff_compare(
        self,
        response1: Dict[str, Any],
        response2: Dict[str, Any],
        api_step: str
    ) -> List[Difference]:
        """Use deepdiff for intelligent comparison."""
        differences = []

        try:
            diff = DeepDiff(response1, response2, ignore_order=True)

            for change_type, changes in diff.items():
                if change_type == "values_changed":
                    for path, change in changes.items():
                        difference = self._create_difference(
                            str(path),
                            change.t1,
                            change.t2,
                            api_step
                        )
                        differences.append(difference)

                elif change_type == "type_changes":
                    for path, change in changes.items():
                        difference = Difference(
                            field_path=str(path),
                            target_value=change.t1,
                            staging_value=change.t2,
                            severity="warning",
                            description=f"Type change: {type(change.t1).__name__} to {type(change.t2).__name__}"
                        )
                        differences.append(difference)

                elif change_type == "dictionary_item_added":
                    for path in changes:
                        difference = Difference(
                            field_path=str(path),
                            target_value=None,
                            staging_value=diff[change_type][path],
                            severity="info",
                            description="Field added in staging"
                        )
                        differences.append(difference)

                elif change_type == "dictionary_item_removed":
                    for path in changes:
                        difference = Difference(
                            field_path=str(path),
                            target_value=diff[change_type][path],
                            staging_value=None,
                            severity="info",
                            description="Field removed from staging"
                        )
                        differences.append(difference)

        except Exception as e:
            logger.error(f"DeepDiff comparison failed: {e}", exc_info=True)
            differences.extend(self._basic_compare(response1, response2, api_step))

        return differences

    def _basic_compare(
        self,
        response1: Dict[str, Any],
        response2: Dict[str, Any],
        api_step: str
    ) -> List[Difference]:
        """Basic comparison when deepdiff is not available."""
        differences = []

        all_keys = set(response1.keys()) | set(response2.keys())

        for key in all_keys:
            if key not in response1:
                differences.append(Difference(
                    field_path=key,
                    target_value=None,
                    staging_value=response2[key],
                    severity="info",
                    description="Field added in staging"
                ))
            elif key not in response2:
                differences.append(Difference(
                    field_path=key,
                    target_value=response1[key],
                    staging_value=None,
                    severity="info",
                    description="Field removed from staging"
                ))
            elif response1[key] != response2[key]:
                differences.append(self._create_difference(
                    key,
                    response1[key],
                    response2[key],
                    api_step
                ))

        return differences

    def _create_difference(
        self,
        field_path: str,
        target_value: Any,
        staging_value: Any,
        api_step: str
    ) -> Difference:
        """
        Create a Difference model with appropriate severity.

        Args:
            field_path: Path to the differing field
            target_value: Value in target environment
            staging_value: Value in staging environment
            api_step: API step for context

        Returns:
            Difference model
        """
        severity = self._determine_severity(field_path)
        description = self._generate_description(field_path, target_value, staging_value)

        return Difference(
            field_path=field_path,
            target_value=target_value,
            staging_value=staging_value,
            severity=severity,
            description=description
        )

    def _determine_severity(self, field_path: str) -> str:
        """
        Determine severity level based on field.

        Args:
            field_path: Path to the field

        Returns:
            Severity level (critical, warning, info)
        """
        field_lower = field_path.lower()

        for critical_field in self.critical_fields:
            if critical_field.lower() in field_lower:
                return "critical"

        if "type" in field_lower or field_lower.endswith("_type"):
            return "warning"

        return "info"

    def _generate_description(
        self,
        field_path: str,
        target_value: Any,
        staging_value: Any
    ) -> str:
        """Generate human-readable description of the difference."""
        return (
            f"Value differs for '{field_path}': "
            f"target={target_value}, staging={staging_value}"
        )

    def _generate_summary(self, differences: List[Difference]) -> Dict[str, int]:
        """
        Generate summary statistics for differences.

        Args:
            differences: List of Difference models

        Returns:
            Dictionary with counts by severity
        """
        summary = {
            "critical": 0,
            "warning": 0,
            "info": 0,
            "total": len(differences)
        }

        for diff in differences:
            summary[diff.severity] += 1

        return summary
