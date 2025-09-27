"""
Generate Investigative Hypotheses Node (Phase 7 - BB)

Produces additional hypotheses when confidence is low and prepares the
state for extended investigation loops.
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


class HypothesisGenerationNode:
    def __init__(self, config: WorkflowConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.HypothesisGenerationNode")

    async def execute(self, state: AgentState) -> AgentState:
        try:
            bundle: Dict[str, Any] = state.get("evidence_bundle") or {}
            resource_signals: List[Dict[str, Any]] = state.get("resource_correlation_insights") or []
            chains: List[Dict[str, Any]] = state.get("dependency_chain_insights") or []

            hypotheses = self._build_hypotheses(bundle, resource_signals, chains)

            analysis_lines = [
                "",
                "NODE BB | Investigative Hypotheses",
                "  --------------------------------",
                f"  - Hypotheses generated: {len(hypotheses)}",
            ]
            for idx, hyp in enumerate(hypotheses[:4], start=1):
                analysis_lines.append(f"  - Hypothesis {idx}: {hyp.get('summary')}")

            analysis = state.get("analysis") or ""
            new_analysis = (analysis + "\n" + "\n".join(analysis_lines)).strip()

            updated_hypotheses = list(state.get("generated_hypotheses") or [])
            updated_hypotheses.extend(hypotheses)

            updated = state.copy()
            updated.update({
                "current_step": "hypotheses_generated",
                "analysis": new_analysis,
                "generated_hypotheses": updated_hypotheses,
                "pending_investigation_tasks": self._derive_tasks(hypotheses),
                "last_hypothesis_generated_at": datetime.utcnow().isoformat(),
            })
            return updated
        except Exception as exc:  # pragma: no cover - defensive
            self.logger.error(f"HypothesisGenerationNode error: {exc}", exc_info=True)
            updated = state.copy()
            updated.update({
                "current_step": "hypothesis_generation_error",
                "error": f"Hypothesis generation failed: {exc}",
            })
            return updated

    def _build_hypotheses(
        self,
        bundle: Dict[str, Any],
        resource_signals: List[Dict[str, Any]],
        chains: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        hypotheses: List[Dict[str, Any]] = []
        services = bundle.get("services_in_focus") or []

        if resource_signals:
            top = sorted(resource_signals, key=lambda item: item.get("confidence", 0), reverse=True)[:2]
            for signal in top:
                hypotheses.append({
                    "type": "resource_correlation",
                    "service": signal.get("service"),
                    "resource_type": signal.get("resource_type"),
                    "confidence": signal.get("confidence"),
                    "summary": (
                        f"Investigate resource strain on {signal.get('service') or 'service'}"
                        f" ({signal.get('resource_type')})"
                    ),
                })

        if chains:
            critical = sorted(chains, key=lambda item: item.get("impact_score", 0), reverse=True)[:2]
            for chain in critical:
                hypotheses.append({
                    "type": "dependency_chain",
                    "service": chain.get("service"),
                    "impact": chain.get("impact_score"),
                    "summary": (
                        f"Trace upstream services affecting {chain.get('service')}"
                        f" (impact {chain.get('impact_score')})"
                    ),
                })

        if not hypotheses and services:
            for svc in services[:2]:
                hypotheses.append({
                    "type": "coverage_gap",
                    "service": svc,
                    "summary": f"Validate missing metrics for {svc}",
                })

        return hypotheses

    def _derive_tasks(self, hypotheses: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        tasks: List[Dict[str, Any]] = []
        for idx, hyp in enumerate(hypotheses, start=1):
            tasks.append({
                "id": f"hyp_task_{idx}",
                "type": hyp.get("type"),
                "service": hyp.get("service"),
                "summary": hyp.get("summary"),
            })
        return tasks

