"""DepartmentManager — LLM-backed orchestrator for one department within one business.

Responsibilities:
- Evaluate the task queue + budget + business context and decide what to do next
- Update the department's plain-language status narrative after every state change
- Handle user chat (adjust priorities, direction, or intent)
"""
import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional

from anthropic import Anthropic

from app.config import settings
from app.db.client import get_supabase
from app.services.cost_tracker import get_budget_state

DEPT_DESCRIPTIONS: dict[str, str] = {
    "marketing": "content creation, SEO, social media, and content distribution",
    "lead_generation": "market research, lead identification, qualification, and outreach",
    "client_acquisition": "outreach, proposals, contract drafting, and invoicing",
    "sales": "outbound sales campaigns and inbound lead follow-up",
    "advertising": "paid ad campaign creation and optimization on Meta and Google",
    "customer_service": "inbound support emails and live chat triage",
    "business_advisor": "strategic briefings and business planning",
    "financial_advisor": "financial summaries and budget planning",
}


@dataclass
class ManagerDecision:
    action: str            # 'start_task' | 'schedule_later' | 'idle' | 'request_budget'
    task_id: Optional[str]     # task to start, if action='start_task'
    run_at: Optional[datetime]  # when to run, if action='schedule_later'
    reason: str


def _client() -> Anthropic:
    return Anthropic(api_key=settings.anthropic_api_key)


def _haiku(prompt: str, max_tokens: int = 600) -> str:
    resp = _client().messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.content[0].text.strip()


def _sonnet(prompt: str, max_tokens: int = 800) -> str:
    resp = _client().messages.create(
        model="claude-sonnet-4-6",
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.content[0].text.strip()


def _load_dept_tasks(business_id: str, dept_type: str) -> dict:
    """Return tasks grouped by status for a single department."""
    db = get_supabase()
    rows = (
        db.table("tasks")
        .select("id,title,description,status,cost_usd,created_at,completed_at")
        .eq("business_id", business_id)
        .eq("department", dept_type)
        .order("created_at", desc=True)
        .limit(50)
        .execute()
        .data or []
    )
    groups: dict = {"planned": [], "in_progress": [], "awaiting_approval": [], "completed": [], "failed": []}
    for t in rows:
        status = t.get("status", "planned")
        if status in groups:
            groups[status].append(t)
    return groups


def _load_dept_row(business_id: str, dept_type: str) -> dict:
    db = get_supabase()
    result = (
        db.table("departments")
        .select("*")
        .eq("business_id", business_id)
        .eq("dept_type", dept_type)
        .single()
        .execute()
        .data or {}
    )
    return result


def _update_dept(business_id: str, dept_type: str, updates: dict) -> None:
    db = get_supabase()
    db.table("departments").update(updates).eq("business_id", business_id).eq("dept_type", dept_type).execute()


class DepartmentManager:
    """Orchestrates one department's work for one business."""

    def evaluate(self, business_id: str, dept_type: str) -> ManagerDecision:
        """
        Called after: agent completes a task, user adds a task, user chats, or on schedule.
        Decides: start a planned task now, schedule for later, or stay idle.
        Updates manager_next_eval_at regardless of outcome.
        """
        tasks = _load_dept_tasks(business_id, dept_type)
        budget = get_budget_state(business_id)
        dept_row = _load_dept_row(business_id, dept_type)
        desc = DEPT_DESCRIPTIONS.get(dept_type, dept_type)

        # If an agent is already in_progress, do nothing — don't pile on
        if tasks["in_progress"] or tasks["awaiting_approval"]:
            decision = ManagerDecision(
                action="idle",
                task_id=None,
                run_at=None,
                reason="Agent is already busy. Will re-evaluate when current task completes.",
            )
            _update_dept(business_id, dept_type, {
                "manager_next_eval_at": (datetime.now(timezone.utc) + timedelta(minutes=15)).isoformat(),
            })
            return decision

        planned = tasks["planned"]
        if not planned:
            # No work to do — schedule a self-check based on cadence
            _update_dept(business_id, dept_type, {
                "manager_next_eval_at": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
            })
            return ManagerDecision(
                action="idle",
                task_id=None,
                run_at=None,
                reason="No planned tasks. Checking again in 1 hour.",
            )

        # Budget check — if no remaining budget, defer
        daily_remaining = budget.get("daily_remaining")
        if daily_remaining is not None and daily_remaining <= 0:
            _update_dept(business_id, dept_type, {
                "manager_next_eval_at": (datetime.now(timezone.utc) + timedelta(hours=6)).isoformat(),
            })
            return ManagerDecision(
                action="request_budget",
                task_id=None,
                run_at=None,
                reason=f"Daily budget exhausted. Will retry in 6 hours.",
            )

        # Ask LLM to decide which task to start and when
        prompt = self._build_eval_prompt(dept_type, desc, planned, tasks["completed"], budget)
        try:
            raw = _sonnet(prompt, 600)
            parsed = json.loads(raw)
            action = parsed.get("action", "start_task")
            task_id = parsed.get("task_id")
            delay_minutes = int(parsed.get("delay_minutes", 0))
            reason = parsed.get("reason", "Manager decision.")

            run_at = datetime.now(timezone.utc) + timedelta(minutes=delay_minutes)
            next_eval = run_at + timedelta(hours=1)
            _update_dept(business_id, dept_type, {"manager_next_eval_at": next_eval.isoformat()})

            if action == "start_task" and delay_minutes == 0 and task_id:
                return ManagerDecision(action="start_task", task_id=task_id, run_at=None, reason=reason)
            elif task_id:
                return ManagerDecision(action="schedule_later", task_id=task_id, run_at=run_at, reason=reason)
            else:
                return ManagerDecision(action="idle", task_id=None, run_at=None, reason=reason)
        except Exception:
            # Fall back to starting the first planned task immediately
            task_id = planned[0]["id"]
            _update_dept(business_id, dept_type, {
                "manager_next_eval_at": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
            })
            return ManagerDecision(action="start_task", task_id=task_id, run_at=None, reason="Default: start next planned task.")

    def chat(self, business_id: str, dept_type: str, user_message: str) -> str:
        """User sends a message to the manager. Manager responds and may re-order task queue."""
        dept_row = _load_dept_row(business_id, dept_type)
        history: list = dept_row.get("manager_chat_history") or []
        tasks = _load_dept_tasks(business_id, dept_type)
        budget = get_budget_state(business_id)
        desc = DEPT_DESCRIPTIONS.get(dept_type, dept_type)

        system = (
            f"You are the {dept_type.replace('_', ' ').title()} department manager for a business. "
            f"Your department handles: {desc}. "
            "You speak directly to the business owner. Be concise and practical. "
            "If the user adjusts priorities or direction, acknowledge it and describe what you'll do differently. "
            "You have visibility into the task queue and budget."
        )
        messages = []
        for entry in history[-10:]:  # keep last 10 for context
            messages.append({"role": entry["role"], "content": entry["content"]})

        task_context = (
            f"Current planned tasks: {[t['title'] for t in tasks['planned'][:5]]}\n"
            f"In progress: {[t['title'] for t in tasks['in_progress']]}\n"
            f"Budget remaining today: {'unlimited' if budget.get('daily_remaining') is None else f'${budget[\"daily_remaining\"]:.4f}'}"
        )
        messages.append({"role": "user", "content": f"{task_context}\n\nOwner says: {user_message}"})

        resp = _client().messages.create(
            model="claude-sonnet-4-6",
            max_tokens=500,
            system=system,
            messages=messages,
        )
        reply = resp.content[0].text.strip()

        # Persist chat history
        history.append({"role": "user", "content": user_message})
        history.append({"role": "assistant", "content": reply})
        _update_dept(business_id, dept_type, {"manager_chat_history": history[-40:]})  # keep last 40 messages

        # Refresh narrative after chat
        self.update_narrative(business_id, dept_type)
        return reply

    def update_narrative(self, business_id: str, dept_type: str) -> str:
        """Generate a fresh plain-language status paragraph and persist it."""
        tasks = _load_dept_tasks(business_id, dept_type)
        desc = DEPT_DESCRIPTIONS.get(dept_type, dept_type)

        done = [t["title"] for t in tasks["completed"][:5]]
        in_prog = [t["title"] for t in tasks["in_progress"] + tasks["awaiting_approval"]]
        planned = [t["title"] for t in tasks["planned"][:5]]

        prompt = (
            f"You are the {dept_type.replace('_', ' ').title()} department manager. "
            f"Your department handles: {desc}.\n\n"
            "Write a 2-3 sentence plain-language department status update in the first person plural (we/our). "
            "Cover three things: what has been done recently, what is being worked on now, and what is planned next. "
            "Be specific and factual. No bullet points.\n\n"
            f"Recently completed: {done if done else 'nothing yet'}\n"
            f"Currently working on: {in_prog if in_prog else 'nothing'}\n"
            f"Planned next: {planned if planned else 'nothing queued'}\n\n"
            "Return ONLY the status paragraph."
        )
        try:
            narrative = _haiku(prompt, 300)
        except Exception:
            narrative = f"The {dept_type.replace('_', ' ')} department is active and managing its task queue."

        _update_dept(business_id, dept_type, {"status_narrative": narrative})
        return narrative

    def _build_eval_prompt(
        self,
        dept_type: str,
        desc: str,
        planned: list,
        completed: list,
        budget: dict,
    ) -> str:
        now = datetime.now(timezone.utc).strftime("%A %H:%M UTC")
        daily_remaining = budget.get("daily_remaining")
        budget_str = "unlimited" if daily_remaining is None else f"${daily_remaining:.4f}"
        planned_items = [{"id": t["id"], "title": t["title"], "description": t.get("description", "")} for t in planned[:10]]
        recent_done = [t["title"] for t in completed[:5]]

        return (
            f"You are the {dept_type.replace('_', ' ').title()} department manager. "
            f"Your department handles: {desc}.\n\n"
            f"Current time: {now}\n"
            f"Budget remaining today: {budget_str}\n"
            f"Recently completed tasks: {recent_done if recent_done else 'none'}\n\n"
            f"Planned tasks (in order):\n{json.dumps(planned_items, indent=2)}\n\n"
            "Decide what to do next. Consider: Is now a good time to run this task? "
            "For example, social media posts should run at peak hours (9am or 6pm local business time). "
            "Outreach emails work best on weekday mornings. Content publishing is fine any time.\n\n"
            "Respond with ONLY valid JSON:\n"
            '{"action": "start_task" | "schedule_later" | "idle", '
            '"task_id": "<id of task to run or null>", '
            '"delay_minutes": <0 for now, or minutes to wait>, '
            '"reason": "<one sentence explanation>"}'
        )


# Module-level singleton
_manager = DepartmentManager()


def evaluate(business_id: str, dept_type: str) -> ManagerDecision:
    return _manager.evaluate(business_id, dept_type)


def chat(business_id: str, dept_type: str, user_message: str) -> str:
    return _manager.chat(business_id, dept_type, user_message)


def update_narrative(business_id: str, dept_type: str) -> str:
    return _manager.update_narrative(business_id, dept_type)
