"""
Proactive Monitoring Setup Node (Phase 11 - VV)

Transforms preventive actions into an actionable proactive monitoring
plan and persists it for future sessions.
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


class ProactiveMonitoringSetupNode:
    """Build a proactive monitoring plan before closing the session."""

    def __init__(self, config: WorkflowConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.ProactiveMonitoringSetupNode")

    async def execute(self, state: AgentState) -> AgentState:
        try:
            timestamp = datetime.utcnow().isoformat()
            project_id = state.get("project_id")

            preventive_actions = state.get("preventive_actions") or []
            monitoring_plan: Dict[str, Any] = {
                "generated_at": timestamp,
                "actions": preventive_actions,
                "owners": [],
                "status": "pending",
            }

            team_stats = state.get("team_knowledge_stats") or {}
            if team_stats.get("top_services"):
                monitoring_plan["focus_services"] = team_stats["top_services"][:5]

            lines = [
                "",
                "SECTION: Proactive Monitoring",
                f"  - Monitoring tasks queued: {len(preventive_actions)}",
            ]

            new_analysis = (state.get("analysis") or "")
            new_analysis = (new_analysis + "\n" + "\n".join(lines)).strip()

            updated = state.copy()
            updated.update({
                "current_step": "proactive_monitoring_prepared",
                "analysis": new_analysis,
                "proactive_monitoring_plan": monitoring_plan,
            })

            if self.config.enable_learning and project_id:
                try:
                    await project_architecture_service.update_context_management_snapshot(
                        project_id,
                        {"proactive_monitoring_plan": monitoring_plan},
                    )
                except Exception as persist_err:  # pragma: no cover - defensive
                    self.logger.warning(f"Proactive monitoring persistence skipped: {persist_err}")

            return updated
        except Exception as exc:  # pragma: no cover
            self.logger.error(f"ProactiveMonitoringSetupNode error: {exc}", exc_info=True)
            updated = state.copy()
            updated.update({
                "current_step": "proactive_monitoring_error",
                "error": f"Proactive monitoring setup failed: {exc}",
            })
            return updated
