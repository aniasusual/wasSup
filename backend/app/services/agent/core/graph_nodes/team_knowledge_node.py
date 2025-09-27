"""
Team Knowledge Node (Phase 10 - GGG)

Shares key findings to a team knowledge structure usable by other
investigations.
"""

import logging
from collections import Counter
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


class TeamKnowledgeNode:
    MAX_TEAM_NOTES = 120

    def __init__(self, config: WorkflowConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.TeamKnowledgeNode")

    async def execute(self, state: AgentState) -> AgentState:
        try:
            project_id = state.get("project_id")
            timestamp = datetime.utcnow().isoformat()

            team_knowledge: List[Dict[str, Any]] = list(state.get("team_knowledge") or [])
            summary = (state.get("formatted_response") or {}).get("summary")
            recommendations = state.get("actionable_recommendations") or []
            services = (state.get("evidence_package") or {}).get("metadata", {}).get("services") or []
            risk_level = (state.get("cascade_forecast") or {}).get("risk_level")
            confidence = state.get("investigation_confidence") or {}

            last_learning = (state.get("learning_repository") or [])[-1] if state.get("learning_repository") else {}
            tags = set(last_learning.get("tags") or [])
            if risk_level:
                tags.add(f"risk:{risk_level}")

            team_entry = {
                "timestamp": timestamp,
                "project_id": project_id,
                "owner": state.get("user_id"),
                "summary": summary,
                "services": services,
                "actions": recommendations,
                "risk_level": risk_level,
                "confidence": confidence,
                "tags": sorted(tags),
            }

            team_knowledge.append(team_entry)
            if len(team_knowledge) > self.MAX_TEAM_NOTES:
                team_knowledge = team_knowledge[-self.MAX_TEAM_NOTES:]

            action_counter = Counter()
            service_counter = Counter()
            high_risk_notes = 0
            for note in team_knowledge:
                for action in note.get("actions") or []:
                    if isinstance(action, dict):
                        for step in action.get("actions") or []:
                            action_counter[str(step)] += 1
                    else:
                        action_counter[str(action)] += 1
                for svc in note.get("services") or []:
                    service_counter[svc] += 1
                if (note.get("risk_level") or "").lower() == "high":
                    high_risk_notes += 1

            stats = {
                "total_entries": len(team_knowledge),
                "top_services": [svc for svc, _ in service_counter.most_common(5)],
                "common_actions": [act for act, _ in action_counter.most_common(5)],
                "high_risk_notes": high_risk_notes,
                "last_updated_at": timestamp,
            }

            lines = [
                "",
                "SECTION: Team Knowledge",
                f"  - Notes available: {stats['total_entries']}",
                f"  - High risk notes: {stats['high_risk_notes']}",
            ]

            new_analysis = (state.get("analysis") or "")
            new_analysis = (new_analysis + "\n" + "\n".join(lines)).strip()

            updated = state.copy()
            updated.update({
                "current_step": "team_knowledge_updated",
                "analysis": new_analysis,
                "team_knowledge": team_knowledge,
                "team_knowledge_stats": stats,
            })

            if self.config.enable_learning and project_id:
                try:
                    await project_architecture_service.update_context_management_snapshot(
                        project_id,
                        {
                            "team_knowledge": team_knowledge,
                            "team_knowledge_stats": stats,
                        },
                    )
                except Exception as persist_err:  # pragma: no cover - defensive
                    self.logger.warning(f"Team knowledge persistence skipped: {persist_err}")

            return updated
        except Exception as exc:  # pragma: no cover
            self.logger.error(f"TeamKnowledgeNode error: {exc}", exc_info=True)
            updated = state.copy()
            updated.update({
                "current_step": "team_knowledge_error",
                "error": f"Team knowledge update failed: {exc}",
            })
            return updated
