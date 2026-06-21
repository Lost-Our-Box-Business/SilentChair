"""Pydantic models for the Task Board."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class Task(BaseModel):
    id: str
    business_id: str
    agent_id: Optional[str] = None
    title: str
    description: Optional[str] = None
    status: str  # 'planned' | 'in_progress' | 'awaiting_approval' | 'completed' | 'failed'
    output: Optional[str] = None
    output_meta: Optional[dict] = None
    department: Optional[str] = None
    cost_usd: float = 0.0
    label_color: Optional[str] = None
    created_by: str = "agent"  # 'agent' | 'user'
    approved_by: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None


class CreateTaskRequest(BaseModel):
    title: str
    description: Optional[str] = None
    department: Optional[str] = None


class UpdateTaskStatusRequest(BaseModel):
    status: str
