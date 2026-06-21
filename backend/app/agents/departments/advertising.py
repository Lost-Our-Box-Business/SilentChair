"""Advertising department — Meta and Google ad campaign creation and management."""
from app.agents.departments.base import BaseDepartmentAgent, BusinessContext, DeptResult


class AdvertisingAgent(BaseDepartmentAgent):
    dept_type = "advertising"
    label_color = "#ef4444"  # red

    async def run(self, business_id: str, context: BusinessContext) -> DeptResult:
        """Generate campaign proposals; launch approved campaigns; pull performance data."""
        raise NotImplementedError
        # Always requires approval before first launch of a campaign.
        # After approval, can make optimization changes within defined rules.
