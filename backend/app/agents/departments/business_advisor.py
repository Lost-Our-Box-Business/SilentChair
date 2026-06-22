"""Business Advisor department — weekly strategic brief + real-time Q&A."""
from app.agents.departments.base import BaseDepartmentAgent, BusinessContext, DeptResult


class BusinessAdvisorAgent(BaseDepartmentAgent):
    dept_type = "business_advisor"
    label_color = "#8b5cf6"  # violet

    cadence_hours = 168  # weekly

    async def run(self, business_id: str, context: BusinessContext) -> DeptResult:
        task_id = await self.create_task(business_id, "Strategic brief", "Business advisor run.")
        await self.update_task(task_id, "completed", output="Business advisor not yet active.")
        await self.log_activity(business_id, "Business advisor department: not yet active.")
        return DeptResult(
            status="completed", task_id=task_id,
            summary="Business advisor not yet active.",
            output={}, cost_usd=0.0,
        )

    async def chat(self, business_id: str, message: str) -> str:
        """Real-time conversational Q&A against the Living Business Document."""
        raise NotImplementedError
