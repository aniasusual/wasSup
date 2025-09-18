"""
Primary API Call Preparation Node (Phase 2 - P)

Prepares a structured request configuration for the Google Cloud Logging API
based on the current, optimized filter and context. This node does not make
the network call; it only assembles the inputs for the execution node (Q).
"""

import logging
from typing import Dict, Any, List, Optional

try:
    from .....models.agent import AgentState, WorkflowConfig
    from ....gcp.logging_client import GCPLoggingClient
except ImportError:
    import sys, os
    sys.path.append(os.path.join(os.path.dirname(__file__), '../../../..'))
    from app.models.agent import AgentState, WorkflowConfig
    from app.services.gcp.logging_client import GCPLoggingClient


logger = logging.getLogger(__name__)


class PrimaryCallPreparationNode:
    def __init__(self, config: WorkflowConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.PrimaryCallPreparationNode")

    async def execute(self, state: AgentState) -> AgentState:
        try:
            project_id = state.get("project_id") or ""
            if not project_id:
                raise ValueError("Missing project_id in state")

            filter_str = state.get("logging_filter") or ""
            order_by = state.get("order_by") or "timestamp desc"

            # Reasonable defaults for page sizing; keep conservative for UI streaming
            page_size = 500
            max_pages = 5
            max_entries = None  # Unlimited unless set later by policy

            # Resource scope: default to current project
            resource_names: List[str] = [f"projects/{project_id}"]

            # Field mask: leverage client helper for compact partial responses
            field_mask = GCPLoggingClient.build_default_field_mask(
                include_payloads=["textPayload", "jsonPayload", "protoPayload"],
                include_operation=False,
                include_trace=True,
            )

            # Prepare a request options object; Q can build the exact body
            request_options: Dict[str, Any] = {
                "project_id": project_id,
                "filter": filter_str,
                "order_by": order_by,
                "page_size": page_size,
                "max_pages": max_pages,
                "max_entries": max_entries,
                "field_mask": field_mask,
                "resource_names": resource_names,
            }

            # Also provide a concrete body preview (for diagnostics/UI)
            body_preview = GCPLoggingClient().build_entries_list_body(
                project_id=project_id,
                filter_str=filter_str,
                order_by=order_by,
                page_size=page_size,
                page_token=None,
                resource_names=resource_names,
                field_mask=field_mask,
            )

            updated = state.copy()
            updated.update({
                "current_step": "primary_call_prepared",
                "logging_request": request_options,
                "logging_request_body_preview": body_preview,
            })
            self.logger.info("Primary API call prepared")
            return updated
        except Exception as e:
            self.logger.error(f"PrimaryCallPreparationNode error: {e}")
            updated = state.copy()
            updated.update({
                "current_step": "primary_call_prep_error",
                "error": f"Primary call preparation failed: {e}",
            })
            return updated

