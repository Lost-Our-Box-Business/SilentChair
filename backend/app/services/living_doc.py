"""Living Business Document — initialize, update, version, and summarize."""


async def initialize_from_profile(business_id: str, profile: dict) -> dict:
    """Convert the interview profile JSON into a structured business_context on first run."""
    raise NotImplementedError


async def update_context(
    business_id: str,
    updates: dict,
    change_summary: str,
    triggered_by: str = "agent",
) -> dict:
    """Merge updates into business_context and snapshot old version to history."""
    raise NotImplementedError


async def get_context(business_id: str) -> dict:
    """Return the full business_context JSONB for a business."""
    raise NotImplementedError


async def get_context_summary(business_id: str) -> str:
    """Return a 3–5 sentence plain-English summary suitable for the UI card."""
    raise NotImplementedError


async def propose_correction(business_id: str, user_message: str) -> dict:
    """Interpret a user correction via Haiku and apply it to business_context."""
    raise NotImplementedError
