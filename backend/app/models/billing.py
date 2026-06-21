"""Pydantic models for the dollar balance and Stripe billing system."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class UserBalance(BaseModel):
    user_id: str
    balance_usd: float
    monthly_grant_usd: float
    subscription_tier: str
    stripe_customer_id: Optional[str] = None
    trial_ends_at: Optional[datetime] = None


class SpendEntry(BaseModel):
    id: str
    user_id: str
    business_id: Optional[str] = None
    task_id: Optional[str] = None
    amount_usd: float
    type: str  # 'subscription_grant' | 'top_up' | 'debit' | 'refund'
    description: Optional[str] = None
    balance_after: Optional[float] = None
    created_at: datetime


class CheckoutRequest(BaseModel):
    tier: str  # 'starter' | 'growth' | 'scale'
    success_url: str
    cancel_url: str


class TopUpRequest(BaseModel):
    amount_usd: float  # minimum $10
    success_url: str
    cancel_url: str


class CheckoutResponse(BaseModel):
    checkout_url: str
