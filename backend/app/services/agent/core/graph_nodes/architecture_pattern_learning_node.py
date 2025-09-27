"""
Architecture Pattern Learning Node (Phase 10 - OO)

Integrates new architecture insights into the architecture knowledge
store, leveraging the learning repository and evidence package.
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


class ArchitecturePatternLearningNode:
    MAX_ARCHITECTURE_ENTRIES = 120

    def __init__(self, config: WorkflowConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.ArchitecturePatternLearningNode")

    async def execute(self, state: AgentState) -> AgentState:
        try:
            project_id = state.get("project_id")
            timestamp = datetime.utcnow().isoformat()

            architecture_learning: List[Dict[str, Any]] = list(state.get("architecture_learning") or [])
            learning_repo = state.get("learning_repository") or []
            team_notes = state.get("team_knowledge") or []
            critical_path = state.get("critical_path_summary") or {}
            new_services = critical_path.get("services") or []
            confidence = state.get("investigation_confidence") or {}
            risk_level = (state.get("cascade_forecast") or {}).get("risk_level")

            latest_learning = learning_repo[-1] if learning_repo else {}
            latest_team_note = team_notes[-1] if team_notes else {}

            entry = {
                "timestamp": timestamp,
                "services": new_services,
                "risk_level": risk_level,
                "confidence_level": confidence.get("level"),
                "insights": list(latest_learning.get("key_findings") or []) + list(latest_team_note.get("tags") or []),
                "summary": (state.get("formatted_response") or {}).get("summary"),
            }

            architecture_learning.append(entry)
            if len(architecture_learning) > self.MAX_ARCHITECTURE_ENTRIES:
                architecture_learning = architecture_learning[-self.MAX_ARCHITECTURE_ENTRIES:]

            service_counter = Counter()
            risk_counter = Counter()
            for item in architecture_learning:
                for svc in item.get("services") or []:
                    service_counter[svc] += 1
                risk_counter[item.get("risk_level") or "unknown"] += 1

            meta = {
                "total_entries": len(architecture_learning),
                "top_services": [svc for svc, _ in service_counter.most_common(10)],
                "risk_profile": dict(risk_counter),
                "last_updated_at": timestamp,
            }

            lines = [
                "",
                "SECTION: Architecture Learning",
                f"  - Learned entries: {meta['total_entries']}",
                f"  - High risk patterns: {meta['risk_profile'].get('high', 0)}",
            ]

            new_analysis = (state.get("analysis") or "")
            new_analysis = (new_analysis + "\n" + "\n".join(lines)).strip()

            updated = state.copy()
            updated.update({
                "current_step": "architecture_learning_updated",
                "analysis": new_analysis,
                "architecture_learning": architecture_learning,
                "architecture_learning_meta": meta,
            })

            if self.config.enable_learning and project_id:
                try:
                    await project_architecture_service.update_context_management_snapshot(
                        project_id,
                        {
                            "architecture_learning": architecture_learning,
                            "architecture_learning_meta": meta,
                        },
                    )
                except Exception as persist_err:  # pragma: no cover - defensive
                    self.logger.warning(f"Architecture learning persistence skipped: {persist_err}")

                # Opportunistically enrich failure patterns with newly learned insight
                if new_services:
                    try:
                        failure_patterns = await project_architecture_service.get_failure_patterns(project_id)
                        signature = (tuple(sorted(new_services)), risk_level, entry.get("summary"))
                        existing_signatures = {
                            (tuple(sorted(fp.get("services") or [])), fp.get("risk_level"), fp.get("summary"))
                            for fp in failure_patterns or []
                        }
                        if signature not in existing_signatures:
                            failure_patterns = list(failure_patterns or [])
                            failure_patterns.append({
                                "pattern_id": entry["timestamp"],
                                "services": new_services,
                                "risk_level": risk_level,
                                "summary": entry.get("summary"),
                                "signals": entry.get("insights"),
                                "source": "learning_repository",
                                "created_at": timestamp,
                            })
                            failure_patterns = failure_patterns[-150:]
                            await project_architecture_service.update_failure_patterns(project_id, failure_patterns)
                    except Exception as pattern_err:  # pragma: no cover - defensive
                        self.logger.warning(f"Failure pattern enrichment skipped: {pattern_err}")

            return updated
        except Exception as exc:  # pragma: no cover
            self.logger.error(f"ArchitecturePatternLearningNode error: {exc}", exc_info=True)
            updated = state.copy()
            updated.update({
                "current_step": "architecture_learning_error",
                "error": f"Architecture pattern learning failed: {exc}",
            })
            return updated
