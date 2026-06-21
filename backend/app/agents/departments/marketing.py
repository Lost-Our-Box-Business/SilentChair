"""Marketing department — wraps the existing content_pipeline without modifying it."""
from app.agents.departments.base import BaseDepartmentAgent, BusinessContext, DeptResult
from app.agents.content_pipeline import run_content_pipeline


class MarketingAgent(BaseDepartmentAgent):
    dept_type = "marketing"
    label_color = "#3b82f6"  # blue

    async def run(self, business_id: str, context: BusinessContext) -> DeptResult:
        raise NotImplementedError
        # Implementation will:
        # 1. create_task(business_id, "Marketing run", "...")
        # 2. Call run_content_pipeline(business_id, context.profile, context.tool_keys,
        #        context.autonomy, context.active_dept_types)
        # 3. Map pipeline result → DeptResult
        # 4. update_task(...), deduct_spend(...)
