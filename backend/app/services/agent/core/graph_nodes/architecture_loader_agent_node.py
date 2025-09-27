"""
Architecture Loader Agent Node (Phase 12 - NNN)

Builds a high-level summary of the loaded architecture for downstream
agents and persists it for reuse.
"""

import logging
from datetime import datetime
from typing import Any, Dict

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


class ArchitectureLoaderAgentNode:
    """Summarise architecture context for LangGraph agent integration."""

    def __init__(self, config: WorkflowConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.ArchitectureLoaderAgentNode")

    async def execute(self, state: AgentState) -> AgentState:
        try:
            architecture_context = state.get("architecture_context") or {}
            services = architecture_context.get("services") or []
            dependencies = architecture_context.get("service_dependencies") or {}

            summary = {
                "timestamp": datetime.utcnow().isoformat(),
                "services": len(services),
                "dependencies": sum(len(v) for v in dependencies.values()),
                "complexity": state.get("architecture_insights", {}).get("complexity_level"),
            }

            lines = [
                "",
                "SECTION: Architecture Agent",
                f"  - Services catalogued: {summary['services']}",
                f"  - Dependency edges: {summary['dependencies']}",
            ]

            new_analysis = (state.get("analysis") or "")
            new_analysis = (new_analysis + "\n" + "\n".join(lines)).strip()

            updated = state.copy()
            updated.update({
                "current_step": "architecture_agent_summary",
                "analysis": new_analysis,
                "architecture_agent_summary": summary,
            })

            if self.config.enable_learning and state.get("project_id"):
                try:
                    await project_architecture_service.update_context_management_snapshot(
                        state.get("project_id"),
                        {"architecture_agent_summary": summary},
                    )
                except Exception as persist_err:  # pragma: no cover - defensive
                    self.logger.warning(f"Architecture agent summary persistence skipped: {persist_err}")

            return updated
        except Exception as exc:  # pragma: no cover
            self.logger.error(f"ArchitectureLoaderAgentNode error: {exc}", exc_info=True)
            updated = state.copy()
            updated.update({
                "current_step": "architecture_agent_error",
                "error": f"Architecture agent processing failed: {exc}",
            })
            return updated
