"""Client Acquisition department — wraps the existing client_acquisition_pipeline."""
from app.agents.departments.base import BaseDepartmentAgent, BusinessContext, DeptResult
from app.agents.client_acquisition_pipeline import run_client_acquisition_pipeline


class ClientAcquisitionAgent(BaseDepartmentAgent):
    dept_type = "client_acquisition"
    label_color = "#f59e0b"  # amber

    async def run(self, business_id: str, context: BusinessContext) -> DeptResult:
        raise NotImplementedError
