"""Pydantic models for coach scheduling."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class CoachSession(BaseModel):
    id: str
    business_id: str
    calendly_event_id: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    coach_name: Optional[str] = None
    briefing: Optional[str] = None
    status: str = "scheduled"  # 'scheduled' | 'completed' | 'cancelled'
    created_at: datetime


class GenerateBriefingRequest(BaseModel):
    session_id: str
    business_id: str
