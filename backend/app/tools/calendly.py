"""Calendly API wrapper — scheduling links and event data."""


async def get_scheduling_link(event_type_uri: str) -> str:
    """Return a one-off scheduling link for the given event type."""
    raise NotImplementedError


async def get_scheduled_events(organization: str, count: int = 10) -> list:
    """Return upcoming scheduled events for the organization."""
    raise NotImplementedError
