from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class WebsiteFile(BaseModel):
    path: str
    content: str


class ChatMessage(BaseModel):
    role: str  # "user" | "assistant"
    content: str


class WebsiteTurnRequest(BaseModel):
    website_id: str
    message: str
    current_files: list[WebsiteFile] = []


class WebsiteTurnResponse(BaseModel):
    website_id: str
    reply: str
    files: list[WebsiteFile]


class WebsiteRecord(BaseModel):
    id: str
    business_id: str
    subdomain: str
    custom_domain: Optional[str] = None
    files: list[WebsiteFile] = []
    chat_history: list[ChatMessage] = []
    published_url: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime


class CustomDomainRequest(BaseModel):
    custom_domain: str
