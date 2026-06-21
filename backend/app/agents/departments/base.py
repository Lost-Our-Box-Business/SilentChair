"""BaseDepartmentAgent — the contract every department must implement."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class BusinessContext:
    business_id: str
    user_id: str
    profile: dict
    business_context: dict
    autonomy: str
    tool_keys: dict
    active_dept_types: list[str]


@dataclass
class DeptResult:
    status: str           # 'completed' | 'awaiting_approval' | 'failed'
    task_id: str
    summary: str
    output: dict
    cost_usd: float


class BaseDepartmentAgent(ABC):
    dept_type: str = ""
    label_color: str = "#6b7280"   # gray default
    model_primary: str = "claude-sonnet-4-6"
    model_fast: str = "claude-haiku-4-5-20251001"

    @abstractmethod
    async def run(self, business_id: str, context: BusinessContext) -> DeptResult:
        """Execute this department's pipeline and return a DeptResult."""
        ...

    async def get_business_context(self, business_id: str) -> BusinessContext:
        raise NotImplementedError

    async def create_task(
        self, business_id: str, title: str, description: str
    ) -> str:
        """Insert a task row (status=in_progress) and return task_id."""
        raise NotImplementedError

    async def update_task(
        self,
        task_id: str,
        status: str,
        output: Optional[str] = None,
        cost_usd: float = 0.0,
    ) -> None:
        raise NotImplementedError

    async def log_activity(
        self,
        business_id: str,
        summary: str,
        requires_approval: bool = False,
        detail: Optional[dict] = None,
    ) -> None:
        raise NotImplementedError

    async def check_balance(self, user_id: str, estimated_cost: float = 0.01) -> bool:
        """Return True if the user has sufficient balance."""
        raise NotImplementedError

    async def deduct_spend(
        self, user_id: str, business_id: str, task_id: str, amount_usd: float
    ) -> None:
        raise NotImplementedError

    async def request_approval(
        self, business_id: str, task_id: str, detail: dict
    ) -> None:
        """Set task to awaiting_approval and log to activity feed."""
        raise NotImplementedError
