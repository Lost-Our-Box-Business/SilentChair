"""Meta Ads API wrapper — Facebook and Instagram campaign management."""


async def create_campaign(access_token: str, ad_account_id: str, campaign: dict) -> dict:
    """Create a new Meta Ads campaign. Returns {campaign_id, status}."""
    raise NotImplementedError


async def get_campaign_insights(access_token: str, campaign_id: str) -> dict:
    """Return performance metrics for a campaign."""
    raise NotImplementedError


async def pause_campaign(access_token: str, campaign_id: str) -> None:
    raise NotImplementedError


async def resume_campaign(access_token: str, campaign_id: str) -> None:
    raise NotImplementedError
