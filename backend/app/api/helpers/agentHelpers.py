from datetime import datetime, timezone
from typing import Any, Optional, Dict, List, Literal
import json
import re
from uuid import uuid4

from fastapi import HTTPException, status
import requests
from agno.models.message import Message
from agno.run.agent import RunOutput

BASE_URL = "https://logging.googleapis.com/v2/entries:list"

from ...models.chat import (
    ChatTurnRequest,
    ChatMessageResponse,
    ChatTurnResponseModel,
    ChatSessionSummaryResponse,
    ChatSessionDetailResponse
)

def _timestamp_to_datetime(timestamp: Optional[int]) -> Optional[datetime]:
    if timestamp is None:
        return None
    try:
        return datetime.fromtimestamp(timestamp, tz=timezone.utc)
    except (OSError, OverflowError, ValueError, TypeError):
        return None


def _truncate(text: Optional[str], limit: int = 160) -> Optional[str]:
    if not text:
        return None
    trimmed = text.strip()
    if len(trimmed) <= limit:
        return trimmed
    return f"{trimmed[: limit - 1].rstrip()}…"


def _normalize_role(role: Optional[str]) -> Optional[str]:
    if role is None:
        return "assistant"
    normalized = role.lower()
    if normalized == "user":
        return "user"
    if normalized in {"assistant", "model", "chatbot"}:
        return "assistant"
    return None


def _extract_markdown_and_json(raw_content: str) -> tuple[str, Optional[str]]:
    pattern = re.compile(r"```json\s*([\s\S]*?)```", re.IGNORECASE)
    match = pattern.search(raw_content)
    if not match:
        return raw_content.strip(), None

    json_payload = match.group(1).strip()
    before = raw_content[: match.start()].strip()
    after = raw_content[match.end() :].strip()
    markdown_parts = [part for part in (before, after) if part]
    markdown = "\n\n".join(markdown_parts)
    return (markdown or raw_content.strip(), json_payload)


def _message_to_chat_message(
    message: Message,
    session_id: str,
    index: int,
) -> Optional[ChatMessageResponse]:
    role = _normalize_role(message.role)
    if role is None:
        return None

    timestamp = _timestamp_to_datetime(message.created_at) or datetime.now(timezone.utc)
    raw_content = message.get_content_string() if hasattr(message, "get_content_string") else ""
    content = raw_content
    metadata = message.model_dump(mode="json", exclude_none=True)
    if role == "user" and content:
        delimiter = "## User Query"
        if delimiter in content:
            _, after = content.split(delimiter, 1)
            content = after.lstrip("\n\r ") or content
    elif role == "assistant" and content:
        markdown, json_payload = _extract_markdown_and_json(content)
        if markdown:
            content = markdown
        if json_payload:
            metadata.setdefault("jsonPayload", json_payload)
        if markdown and markdown != raw_content:
            metadata.setdefault("markdown", markdown)

    if raw_content and metadata is not None:
        metadata.setdefault("rawContent", raw_content)

    message_id = metadata.get("id")
    if not isinstance(message_id, str) or not message_id.strip():
        message_id = f"{session_id}-{index}"

    return ChatMessageResponse(
        id=message_id,
        role=role,
        content=content or "",
        timestamp=timestamp,
        metadata=metadata,
    )


def _run_output_to_chat_message(run_output: RunOutput) -> ChatMessageResponse:
    timestamp = _timestamp_to_datetime(getattr(run_output, "created_at", None)) or datetime.now(timezone.utc)
    content = ""
    if hasattr(run_output, "get_content_as_string"):
        try:
            content = run_output.get_content_as_string()
        except Exception:
            pass
    if not content:
        raw_content = getattr(run_output, "content", None)
        if isinstance(raw_content, str):
            content = raw_content
        elif raw_content is not None:
            try:
                content = json.dumps(raw_content)
            except TypeError:
                content = str(raw_content)

    metadata = run_output.to_dict() if hasattr(run_output, "to_dict") else {}
    if not isinstance(metadata, dict):
        metadata = {}
    metadata.setdefault("rawContent", content)

    metrics = getattr(run_output, "metrics", None)
    if metrics is not None and hasattr(metrics, "to_dict"):
        metadata["metrics"] = metrics.to_dict()

    message_id = getattr(run_output, "run_id", None) or getattr(run_output, "session_id", None)
    if not isinstance(message_id, str) or not message_id.strip():
        message_id = f"run-{uuid4().hex}"

    return ChatMessageResponse(
        id=message_id,
        role="assistant",
        content=content or "",
        timestamp=timestamp,
        metadata=metadata,
    )



def build_investigation_context(architecture_summary: str, project_id: str) -> str:
    """Build the system context for the agent."""
    current_time = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    return f"""# Investigation Context

    ## Project Information
    - **Project ID**: {project_id}
    - **Current UTC Time**: {current_time}

    ## System Architecture
    {architecture_summary}

    ---

    **Important Instructions:**
    - Today’s reference time is {current_time} (UTC). Always use this to resolve relative time expressions like "last 30 minutes" or "yesterday".
    - Extract time range information from the user's query (e.g., "last 30 minutes", "past hour", "between 2pm and 3pm today").
    - If no time information is provided in the query, ASK the user to specify the time range.
    - Identify which GCP services are relevant based on the query and architecture.
    - If the service is not explicitly mentioned in the query, infer it from the architecture summary.
    """



def _basic_summary(entries: list[dict]) -> dict:
    total = len(entries)
    severities = {}
    for e in entries:
        sev = (
            e.get("severity")
            or e.get("jsonPayload", {}).get("severity")
            or e.get("protoPayload", {}).get("severity")
            or "DEFAULT"
        )
        severities[sev] = severities.get(sev, 0) + 1
    return {"total_entries": total, "by_severity": severities}


def _fetch_logs_impl(
    filter_str: str,
    order_by: str = "timestamp desc",
    page_size: int = 100,
    page_token: Optional[str] = None,
    timeout: int = 60,
    project_id: str = "",
    access_token: str = "",
) -> Dict[str, Any]:
    """
    Fetch logs from GCP Cloud Logging API.

    Notes:
    - `project_id` and `access_token` are injected via `functools.partial` when the tool is registered with the agent.
    - The LLM should only provide the query parameters like filter_str/order_by/page_size/page_token.
    """
    if not project_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing project_id for fetch_logs",
        )
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing access_token for fetch_logs",
        )

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    body = {
        "resourceNames": [f"projects/{project_id}"],
        "filter": filter_str,
        "orderBy": order_by,
        "pageSize": min(page_size, 1000),  # API max is 1000
    }
    if page_token:
        body["pageToken"] = page_token

    try:
        response = requests.post(BASE_URL, headers=headers, json=body, timeout=timeout)
        response.raise_for_status()
        result = response.json()
        entries = result.get("entries", [])
        result["summary"] = _basic_summary(entries)
        return result
    except requests.exceptions.Timeout:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Request to GCP Cloud Logging API timed out",
        )
    except requests.exceptions.HTTPError as e:
        error_detail = e.response.text if hasattr(e, "response") else str(e)
        raise HTTPException(
            status_code=(
                e.response.status_code
                if hasattr(e, "response")
                else status.HTTP_502_BAD_GATEWAY
            ),
            detail=f"GCP Cloud Logging API error: {error_detail}",
        )
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to fetch logs from GCP: {str(e)}",
        )
