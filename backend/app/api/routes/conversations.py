from __future__ import annotations
from functools import partial
from typing import Any, Callable, Optional, Dict, List

from agno.tools import tool
from fastapi import APIRouter, Depends, HTTPException, status
from agno.agent import Agent
from agno.models.google import Gemini
from datetime import datetime, timezone

from ..routes.auth import refresh_token
import requests

from ...models.chat import (
    ChatMessagePayload,
    ChatTurnRequest,
    ChatTurnResponse,
    LogReference,  # Add this model
)
from agno.db.mongo import MongoDb

import xml.etree.ElementTree as ET
import os

from ..prompts.mainAgent import SYSTEM_PROMPT
from ..helpers.authHelper import get_current_user, get_user_tokens, is_token_expired

router = APIRouter(prefix="/conversations", tags=["conversations"])

BASE_URL = "https://logging.googleapis.com/v2/entries:list"

db_url = os.getenv("MONGODB_URL")

db = MongoDb(db_url=db_url)




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


def parse_log_references(response_text: str) -> List[Dict[str, Any]]:
    """
    Parse <log_references> XML from agent response.
    
    Returns a list of log reference dictionaries that can be sent to frontend.
    """
    log_refs = []
    
    # Find the <log_references> block
    match = re.search(r'<log_references>(.*?)</log_references>', response_text, re.DOTALL)
    if not match:
        return log_refs
    
    xml_content = f"<log_references>{match.group(1)}</log_references>"
    
    try:
        root = ET.fromstring(xml_content)
        
        for log_ref in root.findall('log_ref'):
            ref_id = log_ref.find('id')
            description = log_ref.find('description')
            filter_elem = log_ref.find('filter')
            metadata = log_ref.find('metadata')
            preview = log_ref.find('preview')
            
            ref_dict = {
                'id': ref_id.text if ref_id is not None else '',
                'description': description.text if description is not None else '',
                'filter': filter_elem.text if filter_elem is not None else '',
                'metadata': {},
                'preview': []
            }
            
            # Parse metadata
            if metadata is not None:
                for child in metadata:
                    ref_dict['metadata'][child.tag] = child.text
            
            # Parse preview entries
            if preview is not None:
                for entry in preview.findall('entry'):
                    if entry.text:
                        ref_dict['preview'].append(entry.text)
            
            log_refs.append(ref_dict)
    
    except ET.ParseError as e:
        print(f"[WARNING] Failed to parse log_references XML: {e}")
    
    return log_refs


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
    @tool(show_result=True)
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
    )

    # Combine context and user query
    full_message = f"{context}\n\n## User Query\n{payload.message}"

    # Run the agent with the enriched prompt
    response = agent.run(full_message)

    # For debugging - this will show tool execution
    agent.print_response(full_message, stream=True)

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
