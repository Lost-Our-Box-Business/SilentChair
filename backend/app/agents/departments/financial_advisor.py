"""Financial Advisor department — monthly summary + conversational Q&A."""
from app.agents.departments.base import BaseDepartmentAgent, BusinessContext, DeptResult


class FinancialAdvisorAgent(BaseDepartmentAgent):
    dept_type = "financial_advisor"
    label_color = "#06b6d4"  # cyan

    cadence_hours = 720  # monthly

    async def run(self, business_id: str, context: BusinessContext) -> DeptResult:
        task_id = await self.create_task(business_id, "Financial summary", "Financial advisor run.")
        await self.update_task(task_id, "completed", output="Financial advisor not yet active.")
        await self.log_activity(business_id, "Financial advisor department: not yet active.")
        return DeptResult(
            status="completed", task_id=task_id,
            summary="Financial advisor not yet active.",
            output={}, cost_usd=0.0,
        )

    async def chat(self, business_id: str, message: str) -> str:
        """Answer budget, cash flow, and financial planning questions."""
        raise NotImplementedError
