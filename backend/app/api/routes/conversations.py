from __future__ import annotations
from typing import List
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from agno.session.agent import AgentSession as AgnoAgentSession
from agno.db.base import SessionType


from ..agents.mainAgent import get_main_agent


from ...api.helpers.agentHelpers import (
    build_investigation_context,
    _run_output_to_chat_message,
    _timestamp_to_datetime,
    _normalize_role,
    _truncate,
    _message_to_chat_message,
)

from ..routes.auth import refresh_token

from ...models.chat import (
    ChatTurnRequest,
    ChatMessageResponse,
    ChatTurnResponseModel,
    ChatSessionSummaryResponse,
    ChatSessionDetailResponse,
)
from agno.db.mongo import MongoDb

import xml.etree.ElementTree as ET
import os

from ..helpers.authHelper import get_current_user, get_user_tokens, is_token_expired

router = APIRouter(prefix="/conversations", tags=["conversations"])

db_url = os.getenv("MONGODB_URL")

db = MongoDb(db_url=db_url)


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
    if not payload.project_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="project_id cannot be empty",
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

    # Create an agent instance with tools bound to the current project and user token
    agent = get_main_agent(
        project_id=payload.project_id,
        access_token=access_token,
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
                (
                    message.get_content_string()
                    if hasattr(message, "get_content_string")
                    else str(message.content or "")
                ),
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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Session not found"
        )

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
