"""DepartmentRunner — single dispatch point for all agent execution.

Coordinates between DepartmentManager (macro-scheduling) and
BaseDepartmentAgent subclasses (task execution).
"""
import asyncio
from datetime import datetime, timezone
from typing import Optional

from app.db.client import get_supabase
from app.agents.departments.base import BaseDepartmentAgent, DeptResult
from app.agents.departments.marketing import MarketingAgent
from app.agents.departments.lead_generation import LeadGenerationAgent
from app.agents.departments.client_acquisition import ClientAcquisitionAgent
from app.agents.departments.sales import SalesAgent
from app.agents.departments.advertising import AdvertisingAgent
from app.agents.departments.customer_service import CustomerServiceAgent
from app.agents.departments.business_advisor import BusinessAdvisorAgent
from app.agents.departments.financial_advisor import FinancialAdvisorAgent

AGENT_REGISTRY: dict[str, type[BaseDepartmentAgent]] = {
    "marketing": MarketingAgent,
    "lead_generation": LeadGenerationAgent,
    "client_acquisition": ClientAcquisitionAgent,
    "sales": SalesAgent,
    "advertising": AdvertisingAgent,
    "customer_service": CustomerServiceAgent,
    "business_advisor": BusinessAdvisorAgent,
    "financial_advisor": FinancialAdvisorAgent,
}


def _is_paused(business_id: str) -> bool:
    db = get_supabase()
    row = (
        db.table("businesses")
        .select("is_paused")
        .eq("id", business_id)
        .single()
        .execute()
        .data or {}
    )
    return bool(row.get("is_paused", False))


def _set_paused(business_id: str, paused: bool) -> None:
    get_supabase().table("businesses").update({"is_paused": paused}).eq("id", business_id).execute()


def _active_depts(business_id: str) -> list[str]:
    rows = (
        get_supabase()
        .table("departments")
        .select("dept_type")
        .eq("business_id", business_id)
        .eq("is_active", True)
        .execute()
        .data or []
    )
    return [r["dept_type"] for r in rows]


def _update_dept_run(business_id: str, dept_type: str, status: str) -> None:
    get_supabase().table("departments").update({
        "last_run_at": datetime.now(timezone.utc).isoformat(),
        "last_run_status": status,
    }).eq("business_id", business_id).eq("dept_type", dept_type).execute()


def run_task(
    business_id: str,
    dept_type: str,
    task_id: Optional[str] = None,
    locale: str = "en",
) -> DeptResult:
    """
    Instantiate the correct agent and run it. Called by the manager when it decides
    to start a task. After completion, triggers manager re-evaluation and narrative update.

    If DeptResult.resume_at is set, schedules a Celery task to re-invoke run_task.
    """
    from app.services import department_manager
    from app.services.activity import load_business_context, notify

    AgentClass = AGENT_REGISTRY.get(dept_type)
    if not AgentClass:
        raise ValueError(f"No agent registered for dept_type: {dept_type}")

    agent = AgentClass()
    context = asyncio.run(agent.get_business_context(business_id))

    # Inject the assigned task so agents can read what they're supposed to do
    if task_id:
        db = get_supabase()
        task_row = (
            db.table("tasks").select("id,title,description")
            .eq("id", task_id).single().execute().data
        )
        if task_row:
            context.profile["current_task"] = {
                "id": task_id,
                "title": task_row.get("title", ""),
                "description": task_row.get("description", ""),
            }

    # Inject locale instruction
    if locale and locale != "en":
        from app.services.pipeline_runner import LANGUAGE_NAMES
        lang = LANGUAGE_NAMES.get(locale)
        if lang:
            context.profile["language_instruction"] = (
                f"[IMPORTANT: Write ALL generated content in {lang}.]"
            )

    try:
        result = asyncio.run(agent.run(business_id, context))
    except Exception as e:
        _update_dept_run(business_id, dept_type, "failed")
        notify(business_id, f"{dept_type} agent failed: {e}")
        raise

    _update_dept_run(business_id, dept_type, result.status)

    # If agent needs to resume (micro-scheduling): schedule a Celery eta task
    if result.resume_at:
        _schedule_resume(business_id, dept_type, result.task_id, result.resume_at, locale)

    # Notify completion
    if result.status == "completed":
        notify(business_id, f"{dept_type.replace('_', ' ').title()} complete: {result.summary}")
    elif result.status == "awaiting_approval":
        notify(business_id, f"{dept_type.replace('_', ' ').title()} needs your approval.", requires_approval=True)

    # Manager re-evaluates and refreshes narrative (non-blocking: run in background thread)
    _result = result  # capture for closure
    def _post_run():
        try:
            # If agent proposed Living Document updates, let the coordinator decide
            if _result.context_updates:
                try:
                    from app.services import living_doc
                    living_doc.agent_propose_context_update(
                        business_id,
                        dept_type,
                        _result.context_updates,
                        _result.context_update_summary,
                    )
                except Exception:
                    pass

            department_manager.update_narrative(business_id, dept_type)
            decision = department_manager.evaluate(business_id, dept_type)
            if decision.action == "start_task" and decision.task_id:
                run_task(business_id, dept_type, decision.task_id, locale)
            elif decision.action == "schedule_later" and decision.task_id and decision.run_at:
                _schedule_task(business_id, dept_type, decision.task_id, decision.run_at, locale)
        except Exception:
            pass

    import threading
    threading.Thread(target=_post_run, daemon=True).start()

    return result


def _schedule_resume(
    business_id: str, dept_type: str, task_id: str, run_at: datetime, locale: str
) -> None:
    """Schedule an agent task to resume at run_at using a daemon thread timer."""
    import threading
    delay = max(0.0, (run_at - datetime.now(timezone.utc)).total_seconds())
    threading.Timer(delay, run_task, args=[business_id, dept_type, task_id, locale]).start()


def _schedule_task(
    business_id: str, dept_type: str, task_id: str, run_at: datetime, locale: str
) -> None:
    """Schedule a planned task to start at run_at using a daemon thread timer."""
    import threading
    delay = max(0.0, (run_at - datetime.now(timezone.utc)).total_seconds())
    threading.Timer(delay, run_task, args=[business_id, dept_type, task_id, locale]).start()


def start(business_id: str, locale: str = "en") -> None:
    """
    Initial start: unpause the business, trigger manager.evaluate() for each active dept.
    The manager will decide whether to start a task immediately or schedule one.
    """
    from app.services import department_manager

    _set_paused(business_id, False)
    for dept_type in _active_depts(business_id):
        try:
            decision = department_manager.evaluate(business_id, dept_type)
            if decision.action == "start_task" and decision.task_id:
                run_task(business_id, dept_type, decision.task_id, locale)
            elif decision.action == "schedule_later" and decision.task_id and decision.run_at:
                _schedule_task(business_id, dept_type, decision.task_id, decision.run_at, locale)
            department_manager.update_narrative(business_id, dept_type)
        except Exception:
            pass


def pause(business_id: str) -> None:
    """Pause all agent activity for this business."""
    _set_paused(business_id, True)


def resume(business_id: str, locale: str = "en") -> None:
    """Unpause and immediately re-evaluate all active departments."""
    start(business_id, locale)


def tick() -> int:
    """
    Called by Celery Beat every 5 minutes.
    1. Find tasks with resume_at <= now (agent micro-scheduling).
    2. Find departments with manager_next_eval_at <= now (manager macro-scheduling).
    Returns total count of actions triggered.
    """
    from app.services import department_manager

    db = get_supabase()
    now_iso = datetime.now(timezone.utc).isoformat()
    triggered = 0

    # 1. Resume in-progress agent tasks that have a scheduled resume time
    resume_rows = (
        db.table("tasks")
        .select("id,business_id,department")
        .eq("status", "in_progress")
        .lte("resume_at", now_iso)
        .not_.is_("resume_at", "null")
        .limit(20)
        .execute()
        .data or []
    )
    for row in resume_rows:
        biz_id = row["business_id"]
        dept = row["department"]
        if _is_paused(biz_id):
            continue
        # Clear resume_at so it doesn't retrigger
        db.table("tasks").update({"resume_at": None}).eq("id", row["id"]).execute()
        try:
            run_task(biz_id, dept, row["id"])
            triggered += 1
        except Exception:
            pass

    # 2. Re-evaluate departments whose manager_next_eval_at has passed
    eval_rows = (
        db.rpc("active_dept_evals_due", {"cutoff": now_iso})
        .execute()
        .data or []
    )
    # Fallback if RPC not available: direct query with join
    if not eval_rows:
        eval_rows = (
            db.table("departments")
            .select("business_id,dept_type,businesses!inner(is_paused)")
            .eq("is_active", True)
            .lte("manager_next_eval_at", now_iso)
            .not_.is_("manager_next_eval_at", "null")
            .limit(20)
            .execute()
            .data or []
        )

    for row in eval_rows:
        biz_id = row["business_id"]
        dept = row["dept_type"]
        biz_info = row.get("businesses") or {}
        if biz_info.get("is_paused"):
            continue
        try:
            decision = department_manager.evaluate(biz_id, dept)
            if decision.action == "start_task" and decision.task_id:
                run_task(biz_id, dept, decision.task_id)
                triggered += 1
            elif decision.action == "schedule_later" and decision.task_id and decision.run_at:
                _schedule_task(biz_id, dept, decision.task_id, decision.run_at, "en")
        except Exception:
            pass

    return triggered


def list_departments(business_id: str) -> list[dict]:
    """Return department status summary for the agents overview page."""
    from app.services.cost_tracker import get_today_spend

    db = get_supabase()
    rows = (
        db.table("departments")
        .select("dept_type,name,is_active,last_run_at,last_run_status,manager_next_eval_at,status_narrative")
        .eq("business_id", business_id)
        .execute()
        .data or []
    )
    spend = get_today_spend(business_id)
    by_dept = spend.get("by_dept", {})
    paused = _is_paused(business_id)

    result = []
    for r in rows:
        dept = r["dept_type"]
        agent_cls = AGENT_REGISTRY.get(dept)
        result.append({
            "dept_type": dept,
            "name": r.get("name") or dept.replace("_", " ").title(),
            "is_active": r.get("is_active", False),
            "is_paused": paused,
            "label_color": agent_cls.label_color if agent_cls else "#6b7280",
            "last_run_at": r.get("last_run_at"),
            "last_run_status": r.get("last_run_status"),
            "manager_next_eval_at": r.get("manager_next_eval_at"),
            "status_narrative": r.get("status_narrative") or "",
            "today_cost_usd": by_dept.get(dept, 0.0),
        })
    return result
