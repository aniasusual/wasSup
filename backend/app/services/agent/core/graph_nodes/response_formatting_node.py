"""
Response Formatting & Presentation Node (Phase 9 - MM)

Formats the final investigation summary for presentation to the user,
assembling timeline, impact, and recommendations.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List

try:
    from .....models.agent import AgentState, WorkflowConfig
except ImportError:
    import sys
    import os

    sys.path.append(os.path.join(os.path.dirname(__file__), '../../../..'))
    from app.models.agent import AgentState, WorkflowConfig


logger = logging.getLogger(__name__)


class ResponseFormattingNode:
    def __init__(self, config: WorkflowConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.ResponseFormattingNode")

    async def execute(self, state: AgentState) -> AgentState:
        try:
            timeline = state.get("timeline_summary") or {}
            impact = state.get("impact_analysis") or {}
            critical = state.get("critical_path_summary") or {}
            cascade = state.get("cascade_forecast") or {}
            recommendations = state.get("actionable_recommendations") or []

            formatted = self._format_response(timeline, impact, critical, cascade, recommendations)

            summary_lines = formatted.get("summary", "").splitlines()
            recommendation_lines = [
                f"    - {action}"
                for bundle in formatted.get("recommendations", [])
                for action in bundle.get("actions", [])
            ]

            final_sections: List[str] = [
                "",
                "SECTION: Investigation Summary",
            ]
            if summary_lines:
                final_sections += [f"  - {line}" for line in summary_lines if line.strip()]
            else:
                final_sections.append("  - Summary unavailable")

            final_sections.append("\nSECTION: Next Actions")
            if recommendation_lines:
                final_sections.extend(recommendation_lines[:6])
            else:
                final_sections.append("    - No follow-up actions captured")

            new_analysis = "\n".join(final_sections).strip()

            updated = state.copy()
            updated.update({
                "current_step": "response_formatted",
                "analysis": new_analysis,
                "formatted_response": formatted,
            })
            return updated
        except Exception as exc:  # pragma: no cover
            self.logger.error(f"ResponseFormattingNode error: {exc}", exc_info=True)
            updated = state.copy()
            updated.update({
                "current_step": "response_formatting_error",
                "error": f"Response formatting failed: {exc}",
            })
            return updated

    def _format_response(
        self,
        timeline: Dict[str, Any],
        impact: Dict[str, Any],
        critical: Dict[str, Any],
        cascade: Dict[str, Any],
        recommendations: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        summary_lines: List[str] = []

        if timeline.get("events"):
            first = timeline["events"][0]
            summary_lines.append(
                f"Initial trigger at {first.get('time')}: {first.get('description')}"
            )
        if impact.get("service_count"):
            summary_lines.append(
                f"Impact across {impact['service_count']} service(s); ~{impact.get('estimated_users') or 'unknown'} users affected"
            )
        if critical.get("services"):
            chain = " → ".join(str(s) for s in critical.get("services", []) if s)
            if chain:
                summary_lines.append(f"Critical path {chain}")
        if cascade.get("risk_level"):
            summary_lines.append(f"Cascade risk {cascade['risk_level']}")
        if not summary_lines:
            summary_lines.append("Investigation complete; no additional summary available")

        summary = "\n".join(summary_lines)

        return {
            "summary": summary,
            "impact": impact,
            "critical_path": critical,
            "recommendations": recommendations,
            "cascade": cascade,
            "timeline": timeline,
            "generated_at": datetime.utcnow().isoformat(),
        }
