"""Billing API — Stripe checkout, customer portal, and top-up sessions."""
from fastapi import APIRouter

router = APIRouter()


# POST /api/billing/checkout            → CheckoutResponse (subscription)
# POST /api/billing/topup               → CheckoutResponse (one-time top-up)
# POST /api/billing/portal              → {portal_url}
