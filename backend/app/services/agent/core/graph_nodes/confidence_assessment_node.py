"""
Confidence Assessment & Validation Node (Phase 7 - Z)

Calculates confidence metrics using the evidence bundle, coverage
signals, and historical pattern alignment. Produces a structured
confidence assessment for routing the decision engine.
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


class ConfidenceAssessmentNode:
    def __init__(self, config: WorkflowConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.ConfidenceAssessmentNode")

    async def execute(self, state: AgentState) -> AgentState:
        try:
            bundle: Dict[str, Any] = state.get("evidence_bundle") or {}
            existing_conf = state.get("investigation_confidence") or {}

            base_score = self._derive_base_score(bundle, existing_conf)
            coverage_score = self._derive_coverage_score(bundle)
            validation_score = self._derive_validation_score(bundle)
            risk_adjustment = self._derive_risk_adjustment(state)

            iteration_bonus = self._iteration_adjustment(state)
            raw_score = base_score + coverage_score + validation_score + risk_adjustment + iteration_bonus
            confidence_score = max(0.0, min(0.99, round(raw_score, 2)))
            level = self._select_level(confidence_score)

            rationale = self._build_rationale(bundle, coverage_score, validation_score, risk_adjustment, iteration_bonus)

            assessment = {
                "score": confidence_score,
                "level": level,
                "coverage_ratio": self._coverage_ratio(bundle),
                "evidence_sources": bundle.get("supporting_data") or {},
                "timestamp": datetime.utcnow().isoformat(),
                "rationale": rationale,
            }

            analysis_lines: List[str] = [
                "",
                "NODE Z | Confidence Assessment",
                "  --------------------------------",
                f"  - Confidence score: {confidence_score:.2f}",
                f"  - Confidence level: {level.upper()}",
                f"  - Coverage ratio: {assessment['coverage_ratio'] * 100:.1f}%",
            ]
            if rationale:
                for idx, item in enumerate(rationale[:4], start=1):
                    analysis_lines.append(f"  - Rationale {idx}: {item}")

            analysis = state.get("analysis") or ""
            new_analysis = (analysis + "\n" + "\n".join(analysis_lines)).strip()

            updated = state.copy()
            updated.update({
                "current_step": "confidence_assessment_complete",
                "analysis": new_analysis,
                "confidence_assessment": assessment,
                "investigation_confidence": {
                    "score": confidence_score,
                    "level": level,
                },
            })
            return updated
        except Exception as exc:  # pragma: no cover - defensive guard
            self.logger.error(f"ConfidenceAssessmentNode error: {exc}", exc_info=True)
            updated = state.copy()
            updated.update({
                "current_step": "confidence_assessment_error",
                "error": f"Confidence assessment failed: {exc}",
            })
            return updated

    def _derive_base_score(self, bundle: Dict[str, Any], fallback: Dict[str, Any]) -> float:
        score = None
        if bundle.get("confidence") and isinstance(bundle["confidence"], dict):
            score = bundle["confidence"].get("score")
        if score is None and fallback:
            score = fallback.get("score")
        if score is None:
            score = 0.55
        return float(score)

    def _coverage_ratio(self, bundle: Dict[str, Any]) -> float:
        services = bundle.get("services_in_focus") or []
        coverage = len(services)
        supporting = bundle.get("supporting_data") or {}
        followups = supporting.get("followups", 0)
        triggers = supporting.get("triggers", 0)

        denominator = max(1, coverage + followups + triggers)
        numerator = coverage + (followups * 0.5) + (triggers * 0.25)
        ratio = numerator / denominator
        return max(0.0, min(1.0, ratio))

    def _derive_coverage_score(self, bundle: Dict[str, Any]) -> float:
        ratio = self._coverage_ratio(bundle)
        if ratio >= 0.85:
            return 0.1
        if ratio >= 0.65:
            return 0.05
        if ratio <= 0.35:
            return -0.08
        return 0.0

    def _derive_validation_score(self, bundle: Dict[str, Any]) -> float:
        supporting = bundle.get("supporting_data") or {}
        triggers = supporting.get("triggers", 0)
        followups = supporting.get("followups", 0)
        anomalies = supporting.get("anomalies", 0)

        score = 0.0
        score += min(0.08, triggers * 0.02)
        score += min(0.05, followups * 0.015)
        if anomalies:
            score += 0.03
        return score

    def _derive_risk_adjustment(self, state: AgentState) -> float:
        risk_info = state.get("risk_profile") or {}
        if not isinstance(risk_info, dict):
            return 0.0

        severity = str(risk_info.get("incident_severity", "")).lower()
        urgency = str(risk_info.get("business_impact", "")).lower()

        adjustment = 0.0
        if severity in {"critical", "high"}:
            adjustment -= 0.07
        if urgency in {"critical", "high"}:
            adjustment -= 0.05
        return adjustment

    def _select_level(self, score: float) -> str:
        if score >= 0.80:
            return "high"
        if score >= 0.60:
            return "medium"
        return "low"

    def _iteration_adjustment(self, state: AgentState) -> float:
        iteration = int(state.get("low_confidence_iteration") or 0)
        if iteration <= 0:
            return 0.0
        return min(0.06, iteration * 0.03)

    def _build_rationale(
        self,
        bundle: Dict[str, Any],
        coverage_score: float,
        validation_score: float,
        risk_adj: float,
        iteration_bonus: float,
    ) -> List[str]:
        rationale: List[str] = []
        services = bundle.get("services_in_focus") or []
        if services:
            rationale.append(f"Coverage across {len(services)} services")
        supporting = bundle.get("supporting_data") or {}
        triggers = supporting.get("triggers", 0)
        followups = supporting.get("followups", 0)
        if triggers:
            rationale.append(f"Detected {triggers} cross-service triggers")
        if followups:
            rationale.append(f"Automated follow-ups executed: {followups}")
        if validation_score > 0:
            rationale.append("Correlated evidence sources aligned")
        if coverage_score < 0:
            rationale.append("Coverage below optimal threshold")
        if risk_adj < 0:
            rationale.append("Critical incident severity reduced confidence")
        if iteration_bonus > 0:
            rationale.append("Confidence boosted after additional investigation loop")
        return rationale
