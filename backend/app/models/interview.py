from pydantic import BaseModel
from typing import Literal


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class InterviewRequest(BaseModel):
    session_id: str
    user_id: str
    message: str
    history: list[ChatMessage] = []


class InterviewResponse(BaseModel):
    session_id: str
    message: str
    is_complete: bool
    business_profile: dict | None = None


class BusinessProfile(BaseModel):
    name: str
    niche: str
    target_audience: str
    goals: list[str]
    tone_of_voice: str
    kpis: list[str]
    publishing_channels: list[str]
    additional_notes: str = ""
