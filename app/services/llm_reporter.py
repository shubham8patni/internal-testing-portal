"""LLM Reporter Service

Generates AI-powered reports using Hugging Face LLM.
Currently placeholder - to be implemented in Phase 3 (LLM Integration).
"""

from typing import Dict, Any, List
import logging

from app.models.report import Report, APIBreakdown, Issue

logger = logging.getLogger(__name__)


class LLMReporterService:
    """Service for generating AI-powered reports."""

    def __init__(self):
        self.huggingface_api_key = None
        self.huggingface_model = None

    def generate_execution_report(
        self,
        execution_id: str,
        execution_data: Dict[str, Any],
        comparisons: List[Dict[str, Any]]
    ) -> Report:
        """
        Generate execution report using LLM.

        Args:
            execution_id: Execution identifier
            execution_data: Execution results data
            comparisons: List of comparison results

        Returns:
            Report model with AI-generated insights

        Note:
            Currently placeholder - returns basic report without LLM integration.
            To be implemented in Phase 3 (LLM Integration).
        """
        try:
            logger.info(f"Generating execution report: {execution_id}")

            report = self._generate_placeholder_report(
                execution_id,
                execution_data,
                comparisons
            )

            logger.info(f"Report generated: {report.report_id}")
            return report

        except Exception as e:
            logger.error(f"Failed to generate report: {e}", exc_info=True)
            raise

    def generate_session_report(
        self,
        session_id: str,
        session_data: Dict[str, Any],
        executions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate session-level report.

        Args:
            session_id: Session identifier
            session_data: Session information
            executions: List of execution results

        Returns:
            Session report dictionary

        Note:
            Currently placeholder - to be enhanced with LLM integration.
        """
        try:
            logger.info(f"Generating session report: {session_id}")

            total_executions = len(executions)
            completed_executions = len([
                e for e in executions if e.get("status") == "completed"
            ])
            failed_executions = total_executions - completed_executions

            critical_issues = self._count_critical_issues(executions)
            warnings_count = self._count_warnings(executions)

            overall_status = "completed" if failed_executions == 0 else "failed"

            report = {
                "session_id": session_id,
                "total_executions": total_executions,
                "completed_executions": completed_executions,
                "failed_executions": failed_executions,
                "overall_status": overall_status,
                "critical_issues_count": critical_issues,
                "warnings_count": warnings_count,
                "summary": self._generate_session_summary(
                    total_executions,
                    completed_executions,
                    failed_executions,
                    critical_issues
                )
            }

            logger.info(f"Session report generated: {session_id}")
            return report

        except Exception as e:
            logger.error(f"Failed to generate session report: {e}", exc_info=True)
            raise

    def _generate_placeholder_report(
        self,
        execution_id: str,
        execution_data: Dict[str, Any],
        comparisons: List[Dict[str, Any]]
    ) -> Report:
        """
        Generate placeholder report without LLM.

        Args:
            execution_id: Execution identifier
            execution_data: Execution results
            comparisons: Comparison results

        Returns:
            Report model with basic analysis
        """
        api_breakdown = []
        critical_issues = []
        recommendations = []

        total_critical = 0
        total_warning = 0
        total_info = 0

        for comparison in comparisons:
            summary = comparison.get("summary", {})
            api_step = comparison.get("api_step", "unknown")

            total_critical += summary.get("critical", 0)
            total_warning += summary.get("warning", 0)
            total_info += summary.get("info", 0)

            has_critical = summary.get("critical", 0) > 0
            has_failures = comparison.get("has_failures", False)

            api_breakdown.append(APIBreakdown(
                tab_id=execution_data.get("category", "unknown"),
                status="failed" if has_failures else "completed",
                issues=self._extract_issues(comparison),
                notes=f"Total differences: {summary.get('total', 0)}"
            ))

            for diff in comparison.get("differences", []):
                if diff.get("severity") == "critical":
                    critical_issues.append(Issue(
                        severity="critical",
                        api_step=api_step,
                        description=diff.get("description", "Critical difference found"),
                        recommendation="Investigate and fix critical data mismatch"
                    ))

        if total_critical > 0:
            recommendations.append(
                "Review and fix critical field mismatches before deployment"
            )
        else:
            recommendations.append(
                "No critical issues found. Minor differences may be acceptable."
            )

        if total_warning > 0:
            recommendations.append(
                "Review warning-level differences for potential type changes"
            )

        overall_status = "completed" if total_critical == 0 else "failed"

        executive_summary = self._generate_executive_summary(
            total_critical,
            total_warning,
            total_info,
            len(comparisons)
        )

        return Report(
            report_id=f"rpt_{execution_id}",
            execution_id=execution_id,
            executive_summary=executive_summary,
            api_breakdown=api_breakdown,
            critical_issues=critical_issues,
            recommendations=recommendations,
            overall_status=overall_status
        )

    def _generate_executive_summary(
        self,
        critical: int,
        warning: int,
        info: int,
        total_comparisons: int
    ) -> str:
        """Generate executive summary text."""
        if critical > 0:
            return (
                f"Execution completed with {critical} critical issues. "
                f"Immediate attention required before deployment to production."
            )
        elif warning > 0:
            return (
                f"Execution completed with {warning} warnings. "
                f"Review recommended but no blocking issues."
            )
        else:
            return (
                f"Execution completed successfully with {info} informational differences. "
                f"No blocking issues detected. Ready for production deployment."
            )

    def _generate_session_summary(
        self,
        total: int,
        completed: int,
        failed: int,
        critical_issues: int
    ) -> str:
        """Generate session summary text."""
        if critical_issues > 0:
            return (
                f"Session completed with {critical_issues} critical issues across "
                f"{total} executions. Review and fix before production deployment."
            )
        elif failed > 0:
            return (
                f"Session completed with {failed} failed executions. "
                f"Investigate failures before proceeding."
            )
        else:
            return (
                f"Session completed successfully. All {total} executions passed. "
                f"Ready for production deployment."
            )

    def _extract_issues(self, comparison: Dict[str, Any]) -> List[str]:
        """Extract issue descriptions from comparison."""
        issues = []

        for diff in comparison.get("differences", []):
            severity = diff.get("severity", "info")
            description = diff.get("description", "")

            if severity in ["critical", "warning"]:
                issues.append(f"[{severity.upper()}] {description}")

        return issues

    def _count_critical_issues(self, executions: List[Dict[str, Any]]) -> int:
        """Count critical issues across all executions."""
        count = 0

        for execution in executions:
            reports = execution.get("reports", {})
            critical_issues = reports.get("critical_issues", [])
            count += len(critical_issues)

        return count

    def _count_warnings(self, executions: List[Dict[str, Any]]) -> int:
        """Count warnings across all executions."""
        count = 0

        for execution in executions:
            comparisons = execution.get("comparisons", [])

            for comparison in comparisons:
                summary = comparison.get("summary", {})
                count += summary.get("warning", 0)

        return count

    def configure_huggingface(
        self,
        api_key: str,
        model: str = "mistralai/Mistral-7B-Instruct-v0.2"
    ):
        """
        Configure Hugging Face API for LLM integration.

        Args:
            api_key: Hugging Face API key
            model: Model name to use

        Note:
            To be used in Phase 3 (LLM Integration).
        """
        self.huggingface_api_key = api_key
        self.huggingface_model = model
        logger.info("Hugging Face configuration updated")
