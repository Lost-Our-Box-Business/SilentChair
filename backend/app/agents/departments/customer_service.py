"""Customer Service department — inbound chat + email triage."""
from app.agents.departments.base import BaseDepartmentAgent, BusinessContext, DeptResult


class CustomerServiceAgent(BaseDepartmentAgent):
    dept_type = "customer_service"
    label_color = "#ec4899"  # pink

    cadence_hours = 4  # checks frequently for inbound

    async def run(self, business_id: str, context: BusinessContext) -> DeptResult:
        task_id = await self.create_task(business_id, "Customer service check", "CS run.")
        await self.update_task(task_id, "completed", output="Customer service agent not yet active.")
        await self.log_activity(business_id, "Customer service department: not yet active.")
        return DeptResult(
            status="completed", task_id=task_id,
            summary="Customer service agent not yet active.",
            output={}, cost_usd=0.0,
        )

    async def handle_inbound(self, business_id: str, visitor_message: str, session_id: str) -> str:
        """Handle a real-time inbound support chat from the embeddable widget."""
        raise NotImplementedError

    async def handle_email(self, business_id: str, from_email: str, subject: str, body: str) -> str:
        """Generate a reply to an inbound support email."""
        raise NotImplementedError
