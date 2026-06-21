"""Stripe API wrapper — customers, checkout sessions, customer portal, webhooks."""


async def get_or_create_customer(user_id: str, email: str) -> str:
    """Return Stripe customer_id, creating one if it doesn't exist."""
    raise NotImplementedError


async def create_subscription_checkout(
    customer_id: str,
    tier: str,
    success_url: str,
    cancel_url: str,
) -> str:
    """Return a Stripe Checkout Session URL for a subscription."""
    raise NotImplementedError


async def create_topup_checkout(
    customer_id: str,
    amount_usd: float,
    success_url: str,
    cancel_url: str,
) -> str:
    """Return a Stripe Checkout Session URL for a one-time top-up."""
    raise NotImplementedError


async def create_portal_session(customer_id: str, return_url: str) -> str:
    """Return a Stripe Customer Portal URL for managing the subscription."""
    raise NotImplementedError


def verify_webhook(payload: bytes, signature: str) -> dict:
    """Verify Stripe webhook signature and return the event dict."""
    raise NotImplementedError


TIER_MONTHLY_GRANTS = {
    "starter": 30.00,
    "growth": 100.00,
    "scale": 300.00,
}
