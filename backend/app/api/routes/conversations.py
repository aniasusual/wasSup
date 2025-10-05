from __future__ import annotations
import json
from typing import Any, Optional, Dict, List, Literal
from uuid import uuid4

from agno.tools import tool
from fastapi import APIRouter, Depends, HTTPException, status
from agno.agent import Agent
from agno.models.google import Gemini
from agno.models.message import Message
from agno.run.agent import RunOutput
from agno.session.agent import AgentSession as AgnoAgentSession
from agno.db.base import SessionType
from datetime import datetime, timezone

from ..routes.auth import refresh_token
import requests

from ...models.chat import (
    ChatTurnRequest,
)
from agno.db.mongo import MongoDb
from pydantic import BaseModel, Field, ConfigDict

import xml.etree.ElementTree as ET
import os

from ..prompts.mainAgent import SYSTEM_PROMPT
from ..helpers.authHelper import get_current_user, get_user_tokens, is_token_expired

router = APIRouter(prefix="/conversations", tags=["conversations"])

BASE_URL = "https://logging.googleapis.com/v2/entries:list"

db_url = os.getenv("MONGODB_URL")

db = MongoDb(db_url=db_url)



class ChatMessageResponse(BaseModel):
    """Serialized chat message returned to the frontend."""

    id: str
    role: Literal["user", "assistant"]
    content: str
    timestamp: datetime
    status: str = "sent"
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(populate_by_name=True)


class ChatTurnResponseModel(BaseModel):
    """Response shape for a single chat turn."""

    session_id: str = Field(alias="sessionId")
    reply: ChatMessageResponse
    plan: Optional[Dict[str, Any]] = None
    follow_up_questions: List[str] = Field(default_factory=list, alias="followUpQuestions")
    context_summary: str = Field(default="", alias="contextSummary")
    query_analysis: Optional[Dict[str, Any]] = Field(default=None, alias="queryAnalysis")
    query_history: List[Dict[str, Any]] = Field(default_factory=list, alias="queryHistory")

    model_config = ConfigDict(populate_by_name=True)


class ChatSessionSummaryResponse(BaseModel):
    """Lightweight session details for listing sessions."""

    session_id: str = Field(alias="sessionId")
    title: str
    created_at: Optional[datetime] = Field(default=None, alias="createdAt")
    updated_at: Optional[datetime] = Field(default=None, alias="updatedAt")
    last_message_preview: Optional[str] = Field(default=None, alias="lastMessagePreview")

    model_config = ConfigDict(populate_by_name=True)


class ChatSessionDetailResponse(BaseModel):
    """Full session payload with message history."""

    session_id: str = Field(alias="sessionId")
    title: str
    created_at: Optional[datetime] = Field(default=None, alias="createdAt")
    updated_at: Optional[datetime] = Field(default=None, alias="updatedAt")
    messages: List[ChatMessageResponse] = Field(default_factory=list)

    model_config = ConfigDict(populate_by_name=True)


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


def _message_to_chat_message(
    message: Message,
    session_id: str,
    index: int,
) -> Optional[ChatMessageResponse]:
    role = _normalize_role(message.role)
    if role is None:
        return None

    timestamp = _timestamp_to_datetime(message.created_at) or datetime.now(timezone.utc)
    content = message.get_content_string() if hasattr(message, "get_content_string") else ""
    metadata = message.model_dump(mode="json", exclude_none=True)

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


@router.post("/respond")
async def conversation_respond(
    payload: ChatTurnRequest,
    current_user: str = Depends(get_current_user),
):
    """Agent to manage GCP log investigation conversations."""

    if not payload.message.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="message cannot be empty",
        )

    user_token_data = await get_user_tokens(current_user)
    if not user_token_data:
        raise HTTPException(status_code=401, detail="User not authenticated")

    if is_token_expired(current_user):
        await refresh_token(current_user)
        user_token_data = await get_user_tokens(current_user)

    print("[Conversations] Handling request for user:", current_user)
    print("[Conversations] Payload:", payload)

    # Build the system context
    context = build_investigation_context(
        architecture_summary=payload.context.get(
            "architectureSummary", "No architecture information provided"
        ),
        project_id=payload.project_id,
    )

    access_token = user_token_data.get("access_token")
    if not access_token:
        raise HTTPException(
            status_code=401, detail="Missing access token for current user"
        )

    # Create a tool wrapper that captures project_id and access_token
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
            project_id=payload.project_id,
            access_token=access_token,
        )

    agent = Agent(
        model=Gemini(id="gemini-2.0-flash"),
        tools=[fetch_logs_bound],
        markdown=True,
        description=(SYSTEM_PROMPT),
        add_history_to_context=True,
        db=db,
        enable_user_memories=True,
        enable_agentic_memory=True,

    )

    # Combine context and user query
    full_message = f"{context}\n\n## User Query\n{payload.message}"

    # Run the agent with the enriched prompt
    response = agent.run(
        full_message,
        user_id=current_user,
        session_id=payload.session_id,
    )

    # For debugging - this will show tool execution
    agent.print_response(full_message, stream=True)

    session_id = response.session_id or payload.session_id or agent.session_id
    if not session_id:
        session_id = f"session-{uuid4().hex}"

    reply_message = _run_output_to_chat_message(response)

    metadata = getattr(response, "metadata", {}) or {}
    if hasattr(metadata, "model_dump"):
        metadata = metadata.model_dump(mode="json", exclude_none=True)
    elif not isinstance(metadata, dict):
        metadata = {}

    plan_data = metadata.get("plan")
    if hasattr(plan_data, "model_dump"):
        plan_data = plan_data.model_dump(mode="json", exclude_none=True)
    if not isinstance(plan_data, dict):
        plan_data = None

    follow_ups = metadata.get("follow_up_questions")
    if not isinstance(follow_ups, list):
        follow_ups = []
    follow_ups = [str(question) for question in follow_ups]

    context_summary = metadata.get("context_summary")
    if not isinstance(context_summary, str):
        context_summary = ""

    query_analysis = metadata.get("query_analysis")
    if hasattr(query_analysis, "model_dump"):
        query_analysis = query_analysis.model_dump(mode="json", exclude_none=True)
    elif query_analysis is not None and not isinstance(query_analysis, dict):
        query_analysis = None

    query_history = metadata.get("query_history")
    if not isinstance(query_history, list):
        query_history = []

    response_payload = ChatTurnResponseModel(
        session_id=session_id,
        reply=reply_message,
        plan=plan_data,
        follow_up_questions=follow_ups,
        context_summary=context_summary,
        query_analysis=query_analysis,
        query_history=query_history,
    )

    return response_payload.model_dump(by_alias=True)


@router.get("/sessions")
async def list_conversation_sessions(
    current_user: str = Depends(get_current_user),
):
    try:
        sessions = db.get_sessions(
            session_type=SessionType.AGENT,
            user_id=current_user,
            sort_by="updated_at",
            sort_order="desc",
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch conversation sessions",
        ) from exc

    summaries: List[ChatSessionSummaryResponse] = []

    for session in sessions or []:
        if not isinstance(session, AgnoAgentSession):
            continue

        session_id = session.session_id
        if not isinstance(session_id, str) or not session_id:
            continue

        created_at = _timestamp_to_datetime(session.created_at)
        updated_at = _timestamp_to_datetime(session.updated_at)

        title = None
        session_data = session.session_data or {}
        if isinstance(session_data, dict):
            raw_title = session_data.get("session_name")
            if isinstance(raw_title, str) and raw_title.strip():
                title = raw_title.strip()

        if not title:
            suffix = session_id[-4:].upper()
            title = f"Session {suffix}"

        preview_text = None
        try:
            messages = session.get_messages_for_session(skip_history_messages=False)
        except Exception:
            messages = []

        for message in reversed(messages or []):
            normalized_role = _normalize_role(message.role)
            if normalized_role is None:
                continue
            preview_text = _truncate(
                message.get_content_string() if hasattr(message, "get_content_string") else str(message.content or ""),
                limit=160,
            )
            if preview_text:
                break

        summaries.append(
            ChatSessionSummaryResponse(
                session_id=session_id,
                title=title,
                created_at=created_at,
                updated_at=updated_at,
                last_message_preview=preview_text,
            )
        )

    return [summary.model_dump(by_alias=True) for summary in summaries]


@router.get("/sessions/{session_id}")
async def get_conversation_session(
    session_id: str,
    current_user: str = Depends(get_current_user),
):
    try:
        session = db.get_session(
            session_id=session_id,
            session_type=SessionType.AGENT,
            user_id=current_user,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to load conversation session",
        ) from exc

    if session is None or not isinstance(session, AgnoAgentSession):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    created_at = _timestamp_to_datetime(session.created_at)
    updated_at = _timestamp_to_datetime(session.updated_at)

    title = None
    session_data = session.session_data or {}
    if isinstance(session_data, dict):
        raw_title = session_data.get("session_name")
        if isinstance(raw_title, str) and raw_title.strip():
            title = raw_title.strip()
    if not title:
        suffix = session.session_id[-4:].upper()
        title = f"Session {suffix}"

    try:
        messages = session.get_messages_for_session(skip_history_messages=False)
    except Exception:
        messages = []

    chat_messages: List[ChatMessageResponse] = []
    for index, message in enumerate(messages or []):
        chat_message = _message_to_chat_message(message, session.session_id, index)
        if chat_message is None:
            continue
        chat_messages.append(chat_message)

    detail = ChatSessionDetailResponse(
        session_id=session.session_id,
        title=title,
        created_at=created_at,
        updated_at=updated_at,
        messages=chat_messages,
    )

    return detail.model_dump(by_alias=True)

    # Return response matching your ChatTurnResponse model structure
    # return ChatTurnResponse(
    #     session_id=payload.session_id or f"session-{current_user}",
    #     reply=response.content,
    #     plan={
    #         "model": "gemini-2.0-flash",
    #         "project_id": payload.project_id,
    #         "architecture_summary": payload.context.get('architectureSummary', ''),
    #         "original_query": payload.message
    #     }
    # )
