"""
User Preferences Node (Phase 10 - DDD)

Captures inferred user preferences from the current investigation to
influence future runs (e.g., preferred services or time windows).
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Set

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


class UserPreferencesNode:
    def __init__(self, config: WorkflowConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.UserPreferencesNode")

    async def execute(self, state: AgentState) -> AgentState:
        try:
            preferences: Dict[str, Any] = dict(state.get("user_preferences") or {})
            history_stats = state.get("query_history_stats") or {}
            history_entry = state.get("query_history_entry") or {}
            filter_components = state.get("logging_filter_components") or {}

            timestamp = datetime.utcnow().isoformat()

            preferred_services: Set[str] = set(preferences.get("preferred_services") or [])
            preferred_services.update(history_stats.get("service_popularity") or [])
            preferred_services.update((history_entry.get("services") or []))

            preferred_time_ranges: Set[str] = set(preferences.get("preferred_time_ranges") or [])
            time_range = state.get("time_range")
            if time_range:
                preferred_time_ranges.add(str(time_range))
            stage_temporal = (filter_components.get("time") or {}).get("indicator")
            if stage_temporal:
                preferred_time_ranges.add(str(stage_temporal))

            severity = (filter_components.get("severity") or {}).get("threshold") or (filter_components.get("severity") or {}).get("selected")
            preferred_severities: Set[str] = set(preferences.get("preferred_severities") or [])
            if severity:
                preferred_severities.add(str(severity))

            analysis_depth = preferences.get("analysis_depth") or "focused"
            if len(state.get("auto_followup_investigations") or []) > 0 or len(state.get("filter_plan") or []) > 1:
                analysis_depth = "comprehensive"

            clarification_rate = history_stats.get("clarification_rate", 0.0)
            clarification_style = preferences.get("clarification_style") or "minimal"
            if clarification_rate >= 0.3 or history_entry.get("needs_clarification"):
                clarification_style = "collaborative"
            elif clarification_rate >= 0.1:
                clarification_style = "balanced"

            weights = preferences.get("weights") or {}
            confidence = history_entry.get("confidence") or {}
            confidence_score = confidence.get("score")
            if confidence_score is not None:
                weights["confidence"] = round(confidence_score, 4)
            weights["preferred_service_hit_rate"] = len(preferred_services)
            weights["clarification_rate"] = clarification_rate

            preferences.update({
                "preferred_services": sorted(preferred_services),
                "preferred_time_ranges": sorted(preferred_time_ranges),
                "preferred_severities": sorted(preferred_severities),
                "analysis_depth": analysis_depth,
                "clarification_style": clarification_style,
                "weights": weights,
                "last_updated_at": timestamp,
            })

            summary = {
                "primary_services": preferences["preferred_services"][:5],
                "analysis_depth": analysis_depth,
                "clarification_style": clarification_style,
                "preferred_severities": preferences["preferred_severities"][:3],
            }

            lines = [
                "",
                "SECTION: User Preferences",
                f"  - Analysis depth: {analysis_depth}",
                f"  - Clarification style: {clarification_style}",
            ]

            new_analysis = (state.get("analysis") or "")
            new_analysis = (new_analysis + "\n" + "\n".join(lines)).strip()

            updated = state.copy()
            updated.update({
                "current_step": "user_preferences_updated",
                "analysis": new_analysis,
                "user_preferences": preferences,
                "user_preferences_summary": summary,
            })

            if self.config.enable_learning and state.get("project_id"):
                try:
                    await project_architecture_service.update_context_management_snapshot(
                        state.get("project_id"),
                        {"user_preferences": preferences},
                    )
                except Exception as persist_err:  # pragma: no cover - defensive
                    self.logger.warning(f"User preferences persistence skipped: {persist_err}")

            return updated
        except Exception as exc:  # pragma: no cover
            self.logger.error(f"UserPreferencesNode error: {exc}", exc_info=True)
            updated = state.copy()
            updated.update({
                "current_step": "user_preferences_error",
                "error": f"User preference update failed: {exc}",
            })
            return updated
