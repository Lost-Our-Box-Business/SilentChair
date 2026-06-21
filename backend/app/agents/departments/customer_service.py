"""Customer Service department — inbound chat + email triage."""
from app.agents.departments.base import BaseDepartmentAgent, BusinessContext, DeptResult


class CustomerServiceAgent(BaseDepartmentAgent):
    dept_type = "customer_service"
    label_color = "#ec4899"  # pink

    async def run(self, business_id: str, context: BusinessContext) -> DeptResult:
        """Process queued inbound emails and flag any requiring human escalation."""
        raise NotImplementedError

    async def handle_inbound(self, business_id: str, visitor_message: str, session_id: str) -> str:
        """Handle a real-time inbound support chat from the embeddable widget."""
        raise NotImplementedError

    async def handle_email(self, business_id: str, from_email: str, subject: str, body: str) -> str:
        """Generate a reply to an inbound support email."""
        raise NotImplementedError
