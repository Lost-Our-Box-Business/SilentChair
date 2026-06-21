"""Lead Generation department — wraps the existing lead_gen_pipeline."""
from app.agents.departments.base import BaseDepartmentAgent, BusinessContext, DeptResult
from app.agents.lead_gen_pipeline import run_lead_gen_pipeline


class LeadGenerationAgent(BaseDepartmentAgent):
    dept_type = "lead_generation"
    label_color = "#10b981"  # green

    async def run(self, business_id: str, context: BusinessContext) -> DeptResult:
        raise NotImplementedError
