from typing import Any, Optional, Dict, Callable
from agno.tools import tool
from ..helpers.agentHelpers import _fetch_logs_impl


def create_fetch_logs_tool(project_id: str, access_token: str) -> Callable[..., Dict[str, Any]]:
    """
    Return a tool function bound to the provided project and credentials.

    The closure captures `project_id` and `access_token` so the LLM only needs to
    supply query parameters when invoking the tool.
    """

    @tool(show_result=False)
    def fetch_logs_bound(
        filter_str: str,
        order_by: str = "timestamp desc",
        page_size: int = 100,
        page_token: Optional[str] = None,
        timeout: int = 60,
    ) -> Dict[str, Any]:
        return _fetch_logs_impl(
            filter_str=filter_str,
            order_by=order_by,
            page_size=page_size,
            page_token=page_token,
            timeout=timeout,
            project_id=project_id,
            access_token=access_token,
        )

    return fetch_logs_bound
