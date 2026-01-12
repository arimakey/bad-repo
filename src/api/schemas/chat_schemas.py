from pydantic import BaseModel
from typing import Optional


class ChatRequest(BaseModel):
    message: str
    thread_id: Optional[str] = "default_thread"


class ChatResponse(BaseModel):
    response: str
    thread_id: str
