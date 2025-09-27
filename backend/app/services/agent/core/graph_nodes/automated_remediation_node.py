"""
Automated Remediation Node (Phase 13 - GGGG)

Drafts automated remediation tasks from recommendations.
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


class AutomatedRemediationNode:
    """Prepare automated remediation actions."""

    def __init__(self, config: WorkflowConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.AutomatedRemediationNode")

    async def execute(self, state: AgentState) -> AgentState:
        try:
            recommendations: List[Dict[str, Any]] = state.get("actionable_recommendations") or []
            actions = []
            for bundle in recommendations:
                priority = bundle.get("priority")
                for action in bundle.get("actions", [])[:2]:
                    actions.append({
                        "priority": priority,
                        "action": action,
                    })
            summary = {
                "timestamp": datetime.utcnow().isoformat(),
                "actions": actions,
            }

            lines = [
                "",
                "SECTION: Automated Remediation",
                f"  - Actions generated: {len(actions)}",
            ]

            updated = state.copy()
            updated.update({
                "current_step": "automated_remediation_prepared",
                "analysis": ((state.get("analysis") or "") + "\n" + "\n".join(lines)).strip(),
                "automated_remediation_summary": summary,
            })
            return updated
        except Exception as exc:  # pragma: no cover
            self.logger.error(f"AutomatedRemediationNode error: {exc}", exc_info=True)
            updated = state.copy()
            updated.update({
                "current_step": "automated_remediation_error",
                "error": f"Automated remediation failed: {exc}",
            })
            return updated
