"""
Timeline Reconstruction Node (Phase 9 - GG)

Builds a chronological narrative across services using evidence bundle
data, temporal trends, and dependency insights.
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


class TimelineReconstructionNode:
    def __init__(self, config: WorkflowConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.TimelineReconstructionNode")

    async def execute(self, state: AgentState) -> AgentState:
        try:
            bundle: Dict[str, Any] = state.get("evidence_bundle") or {}
            temporal = state.get("temporal_trends") or {}
            chains = state.get("dependency_chain_insights") or []

            timeline = self._build_timeline(bundle, temporal, chains)

            analysis_lines = [
                "",
                "NODE GG | Timeline Reconstruction",
                "  --------------------------------",
                f"  - Timeline events captured: {len(timeline.get('events', []))}",
                f"  - Earliest event: {timeline.get('start') or 'n/a'}",
                f"  - Latest event: {timeline.get('end') or 'n/a'}",
            ]

            analysis = state.get("analysis") or ""
            new_analysis = (analysis + "\n" + "\n".join(analysis_lines)).strip()

            updated = state.copy()
            updated.update({
                "current_step": "timeline_reconstruction_complete",
                "analysis": new_analysis,
                "timeline_summary": timeline,
                "timeline_generated_at": datetime.utcnow().isoformat(),
            })
            return updated
        except Exception as exc:  # pragma: no cover - defensive
            self.logger.error(f"TimelineReconstructionNode error: {exc}", exc_info=True)
            updated = state.copy()
            updated.update({
                "current_step": "timeline_reconstruction_error",
                "error": f"Timeline reconstruction failed: {exc}",
            })
            return updated

    def _build_timeline(
        self,
        bundle: Dict[str, Any],
        temporal: Dict[str, Any],
        chains: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        events: List[Dict[str, Any]] = []
        timeline_bins = temporal.get("bins") or []
        for bin_entry in timeline_bins[:10]:
            events.append({
                "time": bin_entry.get("hour"),
                "description": f"Log density {bin_entry.get('count')} entries",
            })

        key_findings = bundle.get("key_findings") or []
        for finding in key_findings[:5]:
            events.append({
                "time": bundle.get("timeline", {}).get("time"),
                "description": finding,
            })

        if chains:
            chain = chains[0]
            events.append({
                "time": chain.get("noted_at"),
                "description": f"Dependency impact detected on {chain.get('service')} (impact {chain.get('impact_score')})",
            })

        events = [e for e in events if e.get("time")]
        events.sort(key=lambda e: e["time"])

        start = events[0]["time"] if events else None
        end = events[-1]["time"] if events else None

        return {
            "events": events,
            "start": start,
            "end": end,
            "services": bundle.get("services_in_focus") or [],
        }

