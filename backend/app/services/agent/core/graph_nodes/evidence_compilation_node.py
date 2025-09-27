"""
Evidence Compilation & Documentation Node (Phase 9 - KK)

Aggregates investigation data into a documentation-ready package.
"""

import logging
from datetime import datetime
from typing import Any, Dict

try:
    from .....models.agent import AgentState, WorkflowConfig
except ImportError:
    import sys
    import os

    sys.path.append(os.path.join(os.path.dirname(__file__), '../../../..'))
    from app.models.agent import AgentState, WorkflowConfig


logger = logging.getLogger(__name__)


class EvidenceCompilationNode:
    def __init__(self, config: WorkflowConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.EvidenceCompilationNode")

    async def execute(self, state: AgentState) -> AgentState:
        try:
            bundle: Dict[str, Any] = state.get("evidence_bundle") or {}
            timeline: Dict[str, Any] = state.get("timeline_summary") or {}
            impact: Dict[str, Any] = state.get("impact_analysis") or {}
            critical = state.get("critical_path_summary") or {}
            cascade = state.get("cascade_forecast") or {}

            doc_package = {
                "metadata": {
                    "generated_at": datetime.utcnow().isoformat(),
                    "services": bundle.get("services_in_focus") or [],
                },
                "timeline": timeline,
                "impact": impact,
                "critical_path": critical,
                "cascade_forecast": cascade,
                "key_findings": bundle.get("key_findings") or [],
                "recommended_actions": bundle.get("recommended_actions") or [],
            }

            analysis_lines = [
                "",
                "NODE KK | Evidence Compilation",
                "  --------------------------------",
                f"  - Documentation sections: {len(doc_package)}",
                f"  - Key findings included: {len(doc_package.get('key_findings', []))}",
            ]

            analysis = state.get("analysis") or ""
            new_analysis = (analysis + "\n" + "\n".join(analysis_lines)).strip()

            updated = state.copy()
            updated.update({
                "current_step": "evidence_compilation_complete",
                "analysis": new_analysis,
                "evidence_package": doc_package,
            })
            return updated
        except Exception as exc:  # pragma: no cover
            self.logger.error(f"EvidenceCompilationNode error: {exc}", exc_info=True)
            updated = state.copy()
            updated.update({
                "current_step": "evidence_compilation_error",
                "error": f"Evidence compilation failed: {exc}",
            })
            return updated

