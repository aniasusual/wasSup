"""
Preventive Analysis Node (Phase 11 - TT)

Generates preventive actions based on the investigation outcomes and
learned repository insights.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List

try:
    from .....models.agent import AgentState, WorkflowConfig
    from ....project_architecture_service import project_architecture_service
except ImportError:
    import sys
    import os

    sys.path.append(os.path.join(os.path.dirname(__file__), '../../../..'))
    from app.models.agent import AgentState, WorkflowConfig
    from app.services.project_architecture_service import project_architecture_service


logger = logging.getLogger(__name__)


class PreventiveAnalysisNode:
    """Drafts preventive remediation plans for future incidents."""

    def __init__(self, config: WorkflowConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.PreventiveAnalysisNode")

    async def execute(self, state: AgentState) -> AgentState:
        try:
            timestamp = datetime.utcnow().isoformat()
            project_id = state.get("project_id")

            learning_summary = state.get("learning_repository_summary") or {}
            team_stats = state.get("team_knowledge_stats") or {}
            architecture_meta = state.get("architecture_learning_meta") or {}

            preventive_actions: List[Dict[str, Any]] = []
            top_tags = learning_summary.get("top_tags") or []
            top_services = learning_summary.get("top_services") or architecture_meta.get("top_services") or []

            if top_services:
                preventive_actions.append({
                    "type": "monitoring",
                    "description": f"Increase monitoring for services: {', '.join(top_services[:3])}",
                })
            if top_tags:
                preventive_actions.append({
                    "type": "playbook",
                    "description": f"Update incident playbooks to address recurring signals: {top_tags[:3]}",
                })
            if team_stats.get("common_actions"):
                preventive_actions.append({
                    "type": "process",
                    "description": "Streamline common remediation actions shared by the team",
                })
            if not preventive_actions:
                preventive_actions.append({
                    "type": "review",
                    "description": "Conduct post-mortem review to identify preventive measures",
                })

            lines = [
                "",
                "SECTION: Preventive Analysis",
                f"  - Preventive actions drafted: {len(preventive_actions)}",
            ]

            new_analysis = (state.get("analysis") or "")
            new_analysis = (new_analysis + "\n" + "\n".join(lines)).strip()

            updated = state.copy()
            updated.update({
                "current_step": "preventive_actions_prepared",
                "analysis": new_analysis,
                "preventive_actions": preventive_actions,
            })

            if self.config.enable_learning and project_id:
                try:
                    await project_architecture_service.update_context_management_snapshot(
                        project_id,
                        {"preventive_actions": preventive_actions},
                    )
                except Exception as persist_err:  # pragma: no cover - defensive
                    self.logger.warning(f"Preventive actions persistence skipped: {persist_err}")

            return updated
        except Exception as exc:  # pragma: no cover
            self.logger.error(f"PreventiveAnalysisNode error: {exc}", exc_info=True)
            updated = state.copy()
            updated.update({
                "current_step": "preventive_actions_error",
                "error": f"Preventive analysis failed: {exc}",
            })
            return updated
