"""Google Ads API wrapper — search and display campaign management."""


async def create_campaign(credentials: dict, customer_id: str, campaign: dict) -> dict:
    """Create a new Google Ads campaign. Returns {campaign_id, status}."""
    raise NotImplementedError


async def get_campaign_metrics(credentials: dict, customer_id: str, campaign_id: str) -> dict:
    """Return performance metrics for a campaign."""
    raise NotImplementedError


async def pause_campaign(credentials: dict, customer_id: str, campaign_id: str) -> None:
    raise NotImplementedError
