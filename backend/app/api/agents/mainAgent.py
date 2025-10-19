import os
from typing import Optional

from agno.agent import Agent
from agno.models.google import Gemini
from agno.db.mongo import MongoDb

from ...api.tools.logFetch import create_fetch_logs_tool
from ...api.prompts.mainAgent import SYSTEM_PROMPT

db_url = os.getenv("MONGODB_URL")
db = MongoDb(db_url=db_url)


def get_main_agent(
    model_id: str = "gemini-2.0-flash",
    debug_mode: bool = False,
    project_id: Optional[str] = None,
    access_token: Optional[str] = None,
) -> Agent:
    if not project_id or not access_token:
        raise ValueError("project_id and access_token are required to initialize the main agent")

    return Agent(
        model=Gemini(id=model_id),
        tools=[create_fetch_logs_tool(project_id=project_id, access_token=access_token)],
        markdown=True,
        description=SYSTEM_PROMPT,
        add_history_to_context=True,
        db=db,
        enable_user_memories=True,
        enable_agentic_memory=True,
    )
