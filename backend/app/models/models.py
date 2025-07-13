from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime

# Models
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class LogEntry(BaseModel):
    timestamp: datetime
    severity: str
    message: str
    resource: Dict
    labels: Dict
    insertId: str

class LogQuery(BaseModel):
    project_id: str
    filter: Optional[str] = None
    order_by: Optional[str] = "timestamp desc"
    page_size: Optional[int] = 100
