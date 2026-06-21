"""Webhook handlers for Stripe and Calendly."""
from fastapi import APIRouter

router = APIRouter()


# POST /api/webhooks/stripe
#   Handles: checkout.session.completed, invoice.payment_succeeded,
#            customer.subscription.deleted, customer.subscription.updated

# POST /api/webhooks/calendly
#   Handles: invitee.created (booking confirmed) → create coach_sessions row
#            invitee.canceled → update session status
