"""Sales department — outbound email campaigns + inbound chat widget handler."""
from app.agents.departments.base import BaseDepartmentAgent, BusinessContext, DeptResult


class SalesAgent(BaseDepartmentAgent):
    dept_type = "sales"
    label_color = "#f97316"  # orange
    cadence_hours = 24

    async def run(self, business_id: str, context: BusinessContext) -> DeptResult:
        task_id = await self.create_task(business_id, "Sales cycle", "Sales outreach run.")
        await self.update_task(task_id, "completed", output="Sales agent not yet active.")
        await self.log_activity(business_id, "Sales department: no active pipeline for this archetype.")
        return DeptResult(
            status="completed", task_id=task_id,
            summary="Sales agent not yet active for this archetype.",
            output={}, cost_usd=0.0,
        )

    async def handle_inbound(self, business_id: str, visitor_message: str, session_id: str) -> str:
        """Handle a real-time inbound chat from the embeddable widget."""
        raise NotImplementedError
