"""Sales department — outbound email campaigns + inbound chat widget handler."""
from app.agents.departments.base import BaseDepartmentAgent, BusinessContext, DeptResult


class SalesAgent(BaseDepartmentAgent):
    dept_type = "sales"
    label_color = "#f97316"  # orange

    async def run(self, business_id: str, context: BusinessContext) -> DeptResult:
        """Execute outbound sales outreach for the current cycle."""
        raise NotImplementedError

    async def handle_inbound(self, business_id: str, visitor_message: str, session_id: str) -> str:
        """Handle a real-time inbound chat from the embeddable widget."""
        raise NotImplementedError
