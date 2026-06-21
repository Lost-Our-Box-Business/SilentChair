"""Dollar balance system — grant, deduct, check, and audit trail."""


class InsufficientBalanceError(Exception):
    pass


async def get_balance(user_id: str) -> dict:
    """Return {balance_usd, subscription_tier, monthly_grant_usd, trial_ends_at}."""
    raise NotImplementedError


async def check_sufficient(user_id: str, estimated_cost_usd: float) -> bool:
    """True if the user has enough balance to cover estimated_cost_usd."""
    raise NotImplementedError


async def deduct(
    user_id: str,
    business_id: str,
    task_id: str,
    amount_usd: float,
    description: str,
) -> float:
    """Atomic deduction. Returns balance_after. Raises InsufficientBalanceError if result < 0."""
    raise NotImplementedError


async def grant(
    user_id: str,
    amount_usd: float,
    type: str,
    description: str,
) -> float:
    """Credit the account. Returns balance_after. Used by Stripe webhook handler."""
    raise NotImplementedError


async def create_trial_balance(user_id: str) -> None:
    """Create user_balances row with $5 trial grant. No-op if row already exists."""
    raise NotImplementedError


async def get_ledger(user_id: str, limit: int = 50) -> list:
    """Return the most recent spend_ledger entries for a user."""
    raise NotImplementedError
