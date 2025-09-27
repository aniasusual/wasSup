"""
Session State Node (Phase 10 - EEE)

Stores the latest conversation and investigation state snapshot.
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


class SessionStateNode:
    MAX_SNAPSHOTS = 25

    def __init__(self, config: WorkflowConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.SessionStateNode")

    async def execute(self, state: AgentState) -> AgentState:
        try:
            timestamp = datetime.utcnow().isoformat()
            session_id = state.get("session_id") or "anonymous"
            confidence = state.get("investigation_confidence") or {}
            result_quality = state.get("result_quality") or (state.get("tool_results") or {}).get("response_analysis", {}).get("quality")

            session_state: Dict[str, Any] = dict(state.get("session_state") or {})
            history: List[Dict[str, Any]] = list(session_state.get("history") or [])
            metrics: Dict[str, Any] = dict(session_state.get("metrics") or {
                "investigations": 0,
                "optimal_results": 0,
                "clarification_requests": 0,
            })

            snapshot = {
                "timestamp": timestamp,
                "session_id": session_id,
                "investigation_id": (state.get("investigation_context") or {}).get("investigation_id"),
                "question": state.get("question"),
                "result_quality": result_quality,
                "confidence": confidence,
                "current_step": state.get("current_step"),
                "context_summary": state.get("context_summary"),
            }

            history.append(snapshot)
            if len(history) > self.MAX_SNAPSHOTS:
                history = history[-self.MAX_SNAPSHOTS:]

            metrics["investigations"] = metrics.get("investigations", 0) + 1
            if result_quality == "optimal":
                metrics["optimal_results"] = metrics.get("optimal_results", 0) + 1
            if state.get("needs_clarification"):
                metrics["clarification_requests"] = metrics.get("clarification_requests", 0) + 1

            session_state.update({
                "session_id": session_id,
                "history": history,
                "metrics": metrics,
                "last_snapshot": snapshot,
                "updated_at": timestamp,
            })

            lines = [
                "",
                "SECTION: Session State",
                f"  - Snapshots retained: {len(history)}",
                f"  - Total investigations this session: {metrics['investigations']}",
            ]

            new_analysis = (state.get("analysis") or "")
            new_analysis = (new_analysis + "\n" + "\n".join(lines)).strip()

            updated = state.copy()
            updated.update({
                "current_step": "session_state_saved",
                "analysis": new_analysis,
                "session_state": session_state,
                "session_state_snapshot": snapshot,
            })

            if self.config.enable_learning and state.get("project_id"):
                try:
                    await project_architecture_service.update_context_management_snapshot(
                        state.get("project_id"),
                        {"session_state": session_state},
                    )
                except Exception as persist_err:  # pragma: no cover - defensive
                    self.logger.warning(f"Session state persistence skipped: {persist_err}")

            return updated
        except Exception as exc:  # pragma: no cover
            self.logger.error(f"SessionStateNode error: {exc}", exc_info=True)
            updated = state.copy()
            updated.update({
                "current_step": "session_state_error",
                "error": f"Session state capture failed: {exc}",
            })
            return updated
