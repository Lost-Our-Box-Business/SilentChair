"""Business Advisor department — weekly strategic brief + real-time Q&A."""
from app.agents.departments.base import BaseDepartmentAgent, BusinessContext, DeptResult


class BusinessAdvisorAgent(BaseDepartmentAgent):
    dept_type = "business_advisor"
    label_color = "#8b5cf6"  # violet

    async def run(self, business_id: str, context: BusinessContext) -> DeptResult:
        """Generate weekly strategic brief from business_context."""
        raise NotImplementedError

    async def chat(self, business_id: str, message: str) -> str:
        """Real-time conversational Q&A against the Living Business Document."""
        raise NotImplementedError
