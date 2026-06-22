"""Marketing department — wraps the existing content_pipeline without modifying it."""
import asyncio
from app.agents.departments.base import BaseDepartmentAgent, BusinessContext, DeptResult
from app.agents.content_pipeline import run_content_pipeline


class MarketingAgent(BaseDepartmentAgent):
    dept_type = "marketing"
    label_color = "#3b82f6"  # blue
    cadence_hours = 24

    async def run(self, business_id: str, context: BusinessContext) -> DeptResult:
        task_id = await self.create_task(
            business_id,
            "Marketing pipeline run",
            "Content research, writing, editing, publishing, and social distribution.",
        )
        try:
            result = await asyncio.to_thread(
                run_content_pipeline,
                business_id=business_id,
                business_profile=context.profile,
                tool_keys=context.tool_keys,
                autonomy=context.autonomy,
                active_dept_types=context.active_dept_types,
            )
            cost = result.get("budget_state", {}).get("today_spend", 0.0)
            log = result.get("log", [])
            summary = log[-1] if log else "Content pipeline complete."

            if result.get("approval_required"):
                await self.request_approval(business_id, task_id, {
                    "action_type": result.get("approval_action", "publish_content"),
                    "edited_articles": result.get("edited_articles", []),
                    "outreach_emails": result.get("outreach_emails", []),
                })
                return DeptResult(
                    status="awaiting_approval",
                    task_id=task_id,
                    summary=summary,
                    output=result,
                    cost_usd=cost,
                )

            await self.update_task(task_id, "completed", output="\n".join(log), cost_usd=cost)
            await self.log_activity(business_id, summary)
            return DeptResult(
                status="completed",
                task_id=task_id,
                summary=summary,
                output=result,
                cost_usd=cost,
            )
        except Exception as e:
            await self.update_task(task_id, "failed", output=str(e))
            raise
