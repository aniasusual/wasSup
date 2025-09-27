"""
User Satisfaction & Next Steps Node (Phase 11 - QQ)

Evaluates post-investigation feedback to determine the next user flow
step (satisfied, drill-down, alternative path, or preventive analysis).
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional

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


class UserSatisfactionNode:
    """Determine the follow-up route based on user feedback."""

    VALID_ROUTES = {"satisfied", "drill_down", "alternative", "preventive"}
    MAX_FEEDBACK_HISTORY = 100

    def __init__(self, config: WorkflowConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.UserSatisfactionNode")

    async def execute(self, state: AgentState) -> AgentState:
        try:
            timestamp = datetime.utcnow().isoformat()
            project_id = state.get("project_id")

            feedback = dict(state.get("user_feedback") or {})
            explicit_route = self._extract_route(feedback)

            route = explicit_route or self._infer_route(feedback)
            if route not in self.VALID_ROUTES:
                route = "satisfied"

            satisfaction_score = feedback.get("satisfaction_score")
            history_entry = dict(state.get("query_history_entry") or {})
            history = list(state.get("query_history") or [])
            stats = dict(state.get("query_history_stats") or {})

            previous_route = history_entry.get("user_satisfaction")
            history_entry.update({
                "user_satisfaction": route,
                "user_feedback": feedback,
                "satisfaction_recorded_at": timestamp,
            })

            if history and history[-1].get("timestamp") == history_entry.get("timestamp"):
                history[-1] = history_entry

            satisfaction_breakdown = dict(stats.get("satisfaction_breakdown") or {})
            if previous_route and previous_route in satisfaction_breakdown:
                satisfaction_breakdown[previous_route] = max(0, satisfaction_breakdown[previous_route] - 1)
                if satisfaction_breakdown[previous_route] == 0:
                    satisfaction_breakdown.pop(previous_route)
            satisfaction_breakdown[route] = satisfaction_breakdown.get(route, 0) + 1
            stats["satisfaction_breakdown"] = satisfaction_breakdown
            stats["last_updated_at"] = timestamp

            feedback_history = list(state.get("user_feedback_history") or [])
            feedback_record = {
                "timestamp": timestamp,
                "route": route,
                "feedback": feedback,
                "satisfaction_score": satisfaction_score,
            }
            feedback_history.append(feedback_record)
            if len(feedback_history) > self.MAX_FEEDBACK_HISTORY:
                feedback_history = feedback_history[-self.MAX_FEEDBACK_HISTORY:]

            section_lines = [
                "",
                "SECTION: User Satisfaction",
                f"  - Route selected: {route.upper()}",
            ]
            if satisfaction_score is not None:
                section_lines.append(f"  - Satisfaction score: {satisfaction_score}")
            if feedback.get("comment"):
                section_lines.append(f"  - Comment: {feedback['comment']}")

            new_analysis = (state.get("analysis") or "")
            new_analysis = (new_analysis + "\n" + "\n".join(section_lines)).strip()

            updated = state.copy()
            updated.update({
                "current_step": "user_satisfaction_routed",
                "analysis": new_analysis,
                "user_feedback": feedback,
                "user_satisfaction": route,
                "satisfaction_route": route,
                "query_history": history,
                "query_history_entry": history_entry,
                "query_history_stats": stats,
                "user_feedback_history": feedback_history,
            })

            if self.config.enable_learning and project_id:
                try:
                    await project_architecture_service.update_context_management_snapshot(
                        project_id,
                        {
                            "query_history": history,
                            "query_history_stats": stats,
                            "user_feedback_history": feedback_history,
                        },
                    )
                except Exception as persist_err:  # pragma: no cover - defensive
                    self.logger.warning(f"User satisfaction persistence skipped: {persist_err}")

            return updated
        except Exception as exc:  # pragma: no cover
            self.logger.error(f"UserSatisfactionNode error: {exc}", exc_info=True)
            updated = state.copy()
            updated.update({
                "current_step": "user_satisfaction_error",
                "error": f"User satisfaction evaluation failed: {exc}",
                "satisfaction_route": "satisfied",
            })
            return updated

    def _extract_route(self, feedback: Dict[str, Any]) -> Optional[str]:
        for key in ("next_step", "route", "choice", "action"):
            value = feedback.get(key)
            if isinstance(value, str):
                return value.lower()
        if isinstance(feedback.get("preventive_analysis"), bool) and feedback["preventive_analysis"]:
            return "preventive"
        return None

    def _infer_route(self, feedback: Dict[str, Any]) -> str:
        score = feedback.get("satisfaction_score")
        try:
            if score is not None:
                score = float(score)
                if score >= 0.75:
                    return "satisfied"
                if score >= 0.5:
                    return "alternative"
                return "drill_down"
        except (TypeError, ValueError):
            pass
        if feedback.get("wants_preventive"):
            return "preventive"
        if feedback.get("needs_deep_dive"):
            return "drill_down"
        return "satisfied"
