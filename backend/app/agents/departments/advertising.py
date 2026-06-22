"""Advertising department — Meta and Google ad campaign creation and management."""
from app.agents.departments.base import BaseDepartmentAgent, BusinessContext, DeptResult


class AdvertisingAgent(BaseDepartmentAgent):
    dept_type = "advertising"
    label_color = "#ef4444"  # red

    cadence_hours = 24

    async def run(self, business_id: str, context: BusinessContext) -> DeptResult:
        task_id = await self.create_task(business_id, "Ad campaign review", "Advertising run.")
        await self.update_task(task_id, "completed", output="Advertising agent not yet active.")
        await self.log_activity(business_id, "Advertising department: not yet active.")
        return DeptResult(
            status="completed", task_id=task_id,
            summary="Advertising agent not yet active.",
            output={}, cost_usd=0.0,
        )
