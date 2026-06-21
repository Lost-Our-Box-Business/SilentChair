"""Financial Advisor department — monthly summary + conversational Q&A."""
from app.agents.departments.base import BaseDepartmentAgent, BusinessContext, DeptResult


class FinancialAdvisorAgent(BaseDepartmentAgent):
    dept_type = "financial_advisor"
    label_color = "#06b6d4"  # cyan

    async def run(self, business_id: str, context: BusinessContext) -> DeptResult:
        """Generate monthly financial summary from usage_events and user-provided data."""
        raise NotImplementedError

    async def chat(self, business_id: str, message: str) -> str:
        """Answer budget, cash flow, and financial planning questions."""
        raise NotImplementedError
