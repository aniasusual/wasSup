"""
Error Classification & Clustering Node (Phase 5 - V2)

Performs lightweight error grouping over the current result set to
identify dominant error families. Clustering is heuristic and
deterministic, based on message normalization and HTTP status/severity.

Outputs:
  - error_clusters: [ { name, count, sample_messages, fingerprint } ]
  - Appends a concise summary to analysis and tool_results.v2_errors
"""

import logging
import re
from typing import Dict, Any, List, Optional

try:
    from .....models.agent import AgentState, WorkflowConfig
except ImportError:
    import sys, os
    sys.path.append(os.path.join(os.path.dirname(__file__), '../../../..'))
    from app.models.agent import AgentState, WorkflowConfig


logger = logging.getLogger(__name__)


_HEX_RE = re.compile(r"\b[0-9a-fA-F]{8,}\b")
_UUID_RE = re.compile(r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b")
_NUM_RE = re.compile(r"\b\d{2,}\b")


def _normalize_message(msg: str) -> str:
    """Normalize message text to derive a simple fingerprint.
    Removes uuids, long hexes, and long numbers; lowercases and trims.
    """
    s = (msg or "").strip().lower()
    # Remove UUIDs/hex/long numbers to reduce noise
    s = _UUID_RE.sub("", s)
    s = _HEX_RE.sub("", s)
    s = _NUM_RE.sub("", s)
    # Collapse whitespace
    s = re.sub(r"\s+", " ", s).strip()
    return s[:200]


class ErrorClusteringNode:
    def __init__(self, config: WorkflowConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.ErrorClusteringNode")

    async def execute(self, state: AgentState) -> AgentState:
        try:
            logs: List[Dict[str, Any]] = list(state.get("relevant_logs") or [])
            total = len(logs)

            # Build buckets keyed by (severity, http_status, normalized message head)
            buckets: Dict[str, Dict[str, Any]] = {}
            for e in logs:
                sev = str(e.get("severity") or "").upper() or "UNKNOWN"
                http = e.get("http") or {}
                status = str(http.get("status") or "")
                msg = str(e.get("message") or "")
                norm = _normalize_message(msg)
                # Use a short head of normalized message as pattern anchor
                head = norm[:80]
                key = f"{sev}|{status}|{head}"
                b = buckets.get(key)
                if not b:
                    b = {
                        "name": head or (status if status else sev),
                        "severity": sev,
                        "status": status or None,
                        "count": 0,
                        "samples": [],
                        "fingerprint": key,
                    }
                    buckets[key] = b
                b["count"] += 1
                if len(b["samples"]) < 3 and msg:
                    b["samples"].append(msg[:300])

            clusters = sorted(buckets.values(), key=lambda x: (-x["count"], x["name"]))[:10]

            # Append to analysis
            lines: List[str] = ["", "SECTION: Error Classification and Clustering"]
            if clusters:
                top = "; ".join([f"{c['name']} x{c['count']}" for c in clusters[:5]])
                lines.append(f"  - Top clusters: {top}")
            else:
                lines.append("  - Outcome: clusters not derived from current results")

            analysis = state.get("analysis") or ""
            new_analysis = (analysis + "\n" + "\n".join(lines)).strip()

            updated = state.copy()
            tr = updated.get("tool_results") or {}
            tr.update({"v2_errors": {"cluster_count": len(clusters)}})
            updated.update({
                "current_step": "error_clusters_analyzed",
                "analysis": new_analysis,
                "error_clusters": clusters,
                "tool_results": tr,
            })
            return updated
        except Exception as e:
            self.logger.error(f"ErrorClusteringNode error: {e}")
            updated = state.copy()
            updated.update({
                "current_step": "error_clustering_error",
                "error": f"Error clustering failed: {e}",
            })
            return updated
