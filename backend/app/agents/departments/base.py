"""BaseDepartmentAgent — the contract every department must implement."""
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from app.db.client import get_supabase


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
    status: str           # 'completed' | 'awaiting_approval' | 'failed' | 'resuming'
    task_id: str
    summary: str
    output: dict
    cost_usd: float
    resume_at: Optional[datetime] = None   # agent micro-scheduling: check back at this time


class BaseDepartmentAgent(ABC):
    dept_type: str = ""
    label_color: str = "#6b7280"   # gray default
    model_primary: str = "claude-sonnet-4-6"
    model_fast: str = "claude-haiku-4-5-20251001"
    cadence_hours: int = 24        # default scheduling hint for the manager

    @abstractmethod
    async def run(self, business_id: str, context: BusinessContext) -> DeptResult:
        """Execute this department's pipeline and return a DeptResult."""
        ...

    # ── Shared helpers ────────────────────────────────────────────────────────

    async def get_business_context(self, business_id: str) -> BusinessContext:
        """Load full execution context for this business from DB."""
        from app.services.activity import load_business_context
        db = get_supabase()

        ctx = load_business_context(business_id)

        biz = (
            db.table("businesses")
            .select("user_id, business_context")
            .eq("id", business_id)
            .single()
            .execute()
            .data or {}
        )

        return BusinessContext(
            business_id=business_id,
            user_id=biz.get("user_id", ""),
            profile=ctx["business_profile"],
            business_context=biz.get("business_context") or {},
            autonomy=ctx["autonomy"],
            tool_keys=ctx["tool_keys"],
            active_dept_types=ctx["active_dept_types"],
        )

    async def create_task(
        self, business_id: str, title: str, description: str
    ) -> str:
        """Insert a task row with status=in_progress and return task_id."""
        db = get_supabase()
        task_id = str(uuid.uuid4())
        db.table("tasks").insert({
            "id": task_id,
            "business_id": business_id,
            "title": title,
            "description": description,
            "status": "in_progress",
            "assigned_to": "agent",
            "created_by": "agent",
            "department": self.dept_type,
            "label_color": self.label_color,
        }).execute()
        return task_id

    async def update_task(
        self,
        task_id: str,
        status: str,
        output: Optional[str] = None,
        cost_usd: float = 0.0,
        resume_at: Optional[datetime] = None,
    ) -> None:
        """Update task status, output, cost, and optional resume timestamp."""
        db = get_supabase()
        update: dict = {"status": status, "cost_usd": cost_usd}
        if output is not None:
            update["output"] = output
        if status == "completed":
            update["completed_at"] = datetime.now(timezone.utc).isoformat()
        if resume_at is not None:
            update["resume_at"] = resume_at.isoformat()
        db.table("tasks").update(update).eq("id", task_id).execute()

    async def log_activity(
        self,
        business_id: str,
        summary: str,
        requires_approval: bool = False,
        detail: Optional[dict] = None,
    ) -> str:
        """Log an entry to activity_log and return the log entry id."""
        from app.services.activity import log_action
        return log_action(
            business_id=business_id,
            agent_id=None,
            action_type=f"dept_{self.dept_type}",
            summary=summary,
            requires_approval=requires_approval,
            detail=detail or {},
        )

    async def check_balance(self, business_id: str, estimated_cost: float = 0.01) -> bool:
        """Return True if the business has sufficient daily budget remaining."""
        from app.services.cost_tracker import daily_budget_ok
        ok, _ = daily_budget_ok(business_id)
        return ok

    async def deduct_spend(
        self,
        business_id: str,
        task_id: str,
        amount_usd: float,
        dept_type: Optional[str] = None,
    ) -> None:
        """Record an explicit spend event. Wrapped pipelines log their own LLM costs;
        call this only for additional charges not already tracked."""
        if amount_usd <= 0:
            return
        db = get_supabase()
        db.table("usage_events").insert({
            "business_id": business_id,
            "dept_type": dept_type or self.dept_type,
            "model": "manual",
            "event_type": "explicit_charge",
            "input_tokens": 0,
            "output_tokens": 0,
            "cache_read_tokens": 0,
            "cache_write_tokens": 0,
            "cost_usd": round(amount_usd, 8),
        }).execute()

    async def request_approval(
        self, business_id: str, task_id: str, detail: dict
    ) -> str:
        """Insert into approval_queue, set task to awaiting_approval. Returns queue_id."""
        db = get_supabase()
        queue_id = str(uuid.uuid4())
        action_type = detail.get("action_type", "review")
        db.table("approval_queue").insert({
            "id": queue_id,
            "business_id": business_id,
            "dept_type": self.dept_type,
            "action_type": action_type,
            "payload": detail,
            "status": "pending",
        }).execute()
        await self.update_task(task_id, "awaiting_approval")
        return queue_id
