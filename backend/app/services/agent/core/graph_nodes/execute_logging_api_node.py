"""
Execute Logging API Node (Phase 2 - Q)

Executes Google Cloud Logging `entries:list` using the prepared request options
and stores a capped set of normalized entries in state. This uses the REST API
endpoint: https://logging.googleapis.com/v2/entries:list with a request body
aligned to the example in `backend/app/api/routes/logs.py`:

  {
    "resourceNames": ["projects/<project_id>"],
    "filter": "<filter_str>",
    "orderBy": "timestamp desc",
    "pageSize": 500,
    "pageToken": "..."  # optional
  }
"""

import logging
from typing import Dict, Any

try:
    from .....models.agent import AgentState, WorkflowConfig
    from ....gcp.logging_client import GCPLoggingClient
except ImportError:
    import sys, os
    sys.path.append(os.path.join(os.path.dirname(__file__), '../../../..'))
    from app.models.agent import AgentState, WorkflowConfig
    from app.services.gcp.logging_client import GCPLoggingClient


logger = logging.getLogger(__name__)


class ExecuteLoggingAPINode:
    def __init__(self, config: WorkflowConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.ExecuteLoggingAPINode")

    async def execute(self, state: AgentState) -> AgentState:
        try:
            req: Dict[str, Any] = state.get("logging_request") or {}
            access_token = state.get("access_token") or ""
            if not access_token:
                raise ValueError("Missing access token")

            # Debug: print request options and filter preview (no secrets)
            try:
                flt = (req.get("filter") or "").strip()
                lines = [l for l in flt.split("\n") if l.strip()]
                preview = "\n".join(lines[:10])
                more = " …" if len(lines) > 10 else ""
                self.logger.info(
                    "[ExecuteLoggingAPINode] entries:list request – project_id=%s, order_by=%s, page_size=%s, max_pages=%s, resource_names=%s, filter_lines=%d%s\n%s",
                    req.get("project_id"), req.get("order_by"), req.get("page_size"), req.get("max_pages"),
                    (req.get("resource_names") or []), len(lines), more, preview
                )
            except Exception:
                pass

            client = GCPLoggingClient()
            # Use REST entries:list via the client helper (httpx → POST entries:list)
            result = await client.entries_list_paginated(
                access_token=access_token,
                project_id=req.get("project_id", ""),
                filter_str=req.get("filter"),
                order_by=req.get("order_by"),
                page_size=req.get("page_size"),
                max_pages=req.get("max_pages"),
                max_entries=req.get("max_entries"),
                field_mask=req.get("field_mask"),
                resource_names=req.get("resource_names"),
            )

            normalized = client.normalize_entries(result.get("entries", []) or [])
            store = normalized[:200]

            # Debug: print result summary
            try:
                self.logger.info(
                    "[ExecuteLoggingAPINode] entries:list result – page_count=%s, returned=%s, stored=%s, next_page_token_present=%s",
                    result.get("page_count"), len(normalized), len(store), bool(result.get("next_page_token"))
                )
            except Exception:
                pass

            updated = state.copy()
            tr = updated.get("tool_results") or {}
            tr.update({
                "logging_api": {
                    "returned": len(normalized),
                    "stored": len(store),
                    "page_count": result.get("page_count"),
                    "next_page_token": result.get("next_page_token"),
                    "endpoint": "https://logging.googleapis.com/v2/entries:list",
                }
            })
            updated.update({
                "current_step": "logging_api_executed",
                "relevant_logs": store,
                "tool_results": tr,
            })
            return updated
        except Exception as e:
            updated = state.copy()
            updated.update({
                "current_step": "logging_api_execute_error",
                "error": f"Logging API execution failed: {e}",
            })
            return updated
