"""
Context-Aware Enhancement Node (Phase 2 - N)

Enhances the current Logging filter using architecture context:
- Adds resource label hints from known service types (e.g., Cloud Run service_name)
- Broadens to upstream/downstream related services when appropriate
- Incorporates technology keywords as lightweight payload contains

This is a heuristic pass – precise enrichment should evolve with real context.
"""

import logging
from typing import Dict, Any, List, Optional

try:
    from .....models.agent import AgentState, WorkflowConfig
except ImportError:
    import sys, os
    sys.path.append(os.path.join(os.path.dirname(__file__), '../../../..'))
    from app.models.agent import AgentState, WorkflowConfig


logger = logging.getLogger(__name__)


class ContextAwareEnhancementNode:
    def __init__(self, config: WorkflowConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.ContextAwareEnhancementNode")

    async def execute(self, state: AgentState) -> AgentState:
        try:
            base_filter = state.get("logging_filter") or ""
            arch = state.get("architecture_context") or {}
            relevant = state.get("relevant_services") or []

            # No-op if no architecture
            if not arch:
                updated = state.copy()
                updated.update({
                    "current_step": "context_aware_filter_constructed",
                    "logging_filter": base_filter,
                    "logging_filter_components": state.get("logging_filter_components") or {},
                    "context_enrichment": {"applied": False, "reason": "no_architecture"},
                })
                return updated

            flines: List[str] = [l for l in (base_filter.split("\n") if base_filter else []) if l.strip()]
            components = dict(state.get("logging_filter_components") or {})
            components.setdefault("context_labels", [])
            components.setdefault("context_keywords", [])
            components.setdefault("related_services", [])

            # A) Service label hints from parsed services
            # Expect parsed_services entries like {type,name} or strings
            parsed_services = arch.get("parsed_services") or []
            add_count = 0
            for svc in parsed_services:
                stype = None
                sname = None
                if isinstance(svc, dict):
                    stype = (svc.get("type") or svc.get("name") or "").lower()
                    sname = svc.get("name") or svc.get("service_name") or svc.get("id")
                elif isinstance(svc, str):
                    stype = svc.lower()
                if not stype:
                    continue
                # Respect relevant services if provided
                if relevant and not any(r in stype for r in [str(x).lower() for x in relevant]):
                    continue
                # Heuristic label mappings
                label_line = self._label_hint_for_service(stype, sname)
                if label_line and label_line not in flines:
                    flines.append(label_line)
                    components["context_labels"].append({"service_type": stype, "label": label_line})
                    add_count += 1
                # If we have a concrete name but no label mapping, try contains
                if sname and add_count == 0:
                    contains = self._simple_contains(sname)
                    if contains not in flines:
                        flines.append(contains)
                        components["context_keywords"].append({"contains": sname})

            # B) Technologies as keywords
            tech = arch.get("technologies") or []
            for t in tech[:3]:
                if isinstance(t, str) and t.strip():
                    contains = self._simple_contains(t)
                    if contains not in flines:
                        flines.append(contains)
                        components["context_keywords"].append({"contains": t})

            # C) Dependencies — include related service types
            deps = arch.get("dependencies") or []
            for dep in deps:
                if not isinstance(dep, str):
                    continue
                dlow = dep.lower()
                for r in relevant or []:
                    if str(r).lower() in dlow:
                        # Pull out other service types mentioned in dep
                        for svc in parsed_services:
                            st = None
                            if isinstance(svc, dict):
                                st = (svc.get("type") or svc.get("name") or "").lower()
                            elif isinstance(svc, str):
                                st = svc.lower()
                            if st and st in dlow:
                                # try label hint
                                label_line = self._label_hint_for_service(st, None)
                                if label_line and label_line not in flines:
                                    flines.append(label_line)
                                    components["related_services"].append(st)

            new_filter = "\n".join(flines)
            updated = state.copy()
            updated.update({
                "current_step": "context_aware_filter_constructed",
                "logging_filter": new_filter,
                "logging_filter_components": components,
                "context_enrichment": {"applied": True},
            })
            self.logger.info("Context-aware filter constructed")
            return updated
        except Exception as e:
            self.logger.error(f"ContextAwareEnhancementNode error: {e}")
            updated = state.copy()
            updated.update({
                "current_step": "context_aware_filter_error",
                "error": f"Context-aware filter construction failed: {e}",
            })
            return updated

    def _label_hint_for_service(self, stype: str, sname: Optional[str]) -> Optional[str]:
        # Minimal label mapping for common GCP services
        st = stype.lower()
        if "cloud_run" in st:
            if sname:
                return f"resource.labels.service_name=\"{sname}\""
            # at least assert resource.type if not present
            return "resource.type=\"cloud_run_revision\""
        if "gke" in st or "k8s" in st:
            # Without specifics, avoid overfitting; leave to later phases
            return None
        if "app_engine" in st or "gae" in st:
            if sname:
                return f"resource.labels.module_id=\"{sname}\""
            return "resource.type=\"gae_app\""
        if "cloud_sql" in st:
            return "resource.type=\"cloudsql_database\""
        if "gce" in st or "compute" in st or "vm" in st:
            return "resource.type=\"gce_instance\""
        if "bigquery" in st:
            return "resource.type=\"bigquery_dataset\""
        return None

    def _simple_contains(self, keyword: str) -> str:
        k = keyword.replace('"', '\\"')
        # Use global full-text search (quoted phrase)
        return f'"{k}"'
