from typing import Literal
from pydantic import BaseModel, Field

class ChatRequest(BaseModel):
    session_id: str = "demo-session"
    message: str

class ChatResponse(BaseModel):
    session_id: str
    reply: str
    status: str
    appointment_id: str | None = None
    candidate_slots: list[dict] = Field(default_factory=list)

class DoctorDecisionRequest(BaseModel):
    decision: Literal['approve', 'decline']
    note: str | None = None

class DoctorDecisionResponse(BaseModel):
    appointment_id: str
    status: str
    message: str
