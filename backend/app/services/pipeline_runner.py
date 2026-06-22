"""Pipeline execution service — shared by activity and tasks routers."""
from app.db.client import get_supabase
from app.services.activity import (
    load_business_context, log_pipeline_run, notify,
)


class BudgetExhaustedError(Exception):
    pass


def _run_for_archetype(business_id: str, ctx: dict) -> dict:
    archetype = ctx["archetype"]
    if archetype == "lead_generation":
        from app.agents.lead_gen_pipeline import run_lead_gen_pipeline
        return run_lead_gen_pipeline(
            business_id=business_id,
            business_profile=ctx["business_profile"],
            tool_keys=ctx["tool_keys"],
            autonomy=ctx["autonomy"],
            active_dept_types=ctx["active_dept_types"],
        )
    elif archetype == "client_acquisition":
        from app.agents.client_acquisition_pipeline import run_client_acquisition_pipeline
        return run_client_acquisition_pipeline(
            business_id=business_id,
            business_profile=ctx["business_profile"],
            tool_keys=ctx["tool_keys"],
            autonomy=ctx["autonomy"],
            active_dept_types=ctx["active_dept_types"],
        )
    else:
        from app.agents.content_pipeline import run_content_pipeline
        return run_content_pipeline(
            business_id=business_id,
            business_profile=ctx["business_profile"],
            tool_keys=ctx["tool_keys"],
            autonomy=ctx["autonomy"],
            active_dept_types=ctx["active_dept_types"],
        )


def _notify_completion(business_id: str, archetype: str, result: dict) -> None:
    if archetype == "content_agency":
        n = len(result.get("published_urls", []))
        notify(business_id, f"Pipeline complete. Published {n} article(s).")
    elif archetype == "lead_generation":
        n = len(result.get("sent_results", []))
        notify(business_id, f"Lead gen complete. Sent {n} outreach email(s).")
    elif archetype == "client_acquisition":
        sent = len(result.get("sent_results", []))
        contracts = len(result.get("contracts", []))
        notify(business_id, f"Acquisition pipeline complete. {sent} emails sent, {contracts} contract(s) drafted.")


def to_summary(result: dict, archetype: str) -> dict:
    base = {
        "status": "awaiting_approval" if result.get("approval_required") else "complete",
        "approval_action": result.get("approval_action"),
        "log": result.get("log", []),
        "budget_state": result.get("budget_state", {}),
    }
    if archetype == "content_agency":
        base["published_urls"] = result.get("published_urls", [])
        base["social_posts"] = result.get("social_posts", [])
    elif archetype == "lead_generation":
        base["qualified_leads"] = result.get("qualified_leads", [])
        base["sent_results"] = result.get("sent_results", [])
    elif archetype == "client_acquisition":
        base["qualified_leads"] = result.get("qualified_leads", [])
        base["sent_results"] = result.get("sent_results", [])
        base["proposals"] = [{"company": p["company"], "title": p["title"]} for p in result.get("proposals", [])]
        base["contracts"] = [{"company": c["company"], "title": c["title"]} for c in result.get("contracts", [])]
        base["invoices"] = [{"company": i["company"], "title": i["title"], "amount": i.get("amount", 0)} for i in result.get("invoices", [])]
    return base


def execute(
    business_id: str,
    task_ids: list[str] | None = None,
    create_summary_task: bool = True,
) -> dict:
    """
    Run the pipeline for a business.

    task_ids: specific task IDs to track through this run. If None, all planned
              agent-assigned tasks for the business are loaded automatically.
    create_summary_task: whether to create an auto pipeline-summary task card.
                         Set False when triggered by a specific user task.
    """
    from app.services.cost_tracker import get_budget_state
    from app.services import tasks_sync

    ctx = load_business_context(business_id)
    db = get_supabase()

    # Pre-flight budget check
    budget = get_budget_state(business_id)
    if budget.get("daily_remaining") is not None and budget["daily_remaining"] <= 0:
        raise BudgetExhaustedError(
            f"Daily budget ${budget['daily_budget']:.2f} exhausted "
            f"(${budget['today_spend']:.4f} spent today)"
        )

    # Load pending agent tasks to track through this run
    if task_ids is None:
        res = db.table("tasks").select("id,title,description,department") \
            .eq("business_id", business_id) \
            .eq("status", "planned") \
            .eq("assigned_to", "agent") \
            .execute()
        pending = res.data or []
        tracking_ids = [t["id"] for t in pending]
    else:
        if task_ids:
            res = db.table("tasks").select("id,title,description,department") \
                .in_("id", task_ids) \
                .execute()
            pending = res.data or []
        else:
            pending = []
        tracking_ids = task_ids

    # Inject pending tasks as context for the pipeline LLM nodes
    if pending:
        ctx["business_profile"]["pending_tasks"] = [
            {
                "title": t["title"],
                "description": t.get("description") or "",
                "department": t.get("department") or "",
            }
            for t in pending
        ]

    # Mark tracked tasks as in_progress before pipeline runs
    if tracking_ids:
        db.table("tasks").update({"status": "in_progress"}) \
            .in_("id", tracking_ids).execute()

    # Run pipeline
    result = _run_for_archetype(business_id, ctx)

    # Log pipeline run
    activity_log_id = log_pipeline_run(business_id, result)

    # Notify and update task statuses based on result
    if result.get("approval_required"):
        notify(business_id, result.get("approval_action", "Action requires approval"), requires_approval=True)
        if tracking_ids:
            update: dict = {"status": "awaiting_approval"}
            if activity_log_id:
                update["activity_log_id"] = activity_log_id
            db.table("tasks").update(update).in_("id", tracking_ids).execute()
    else:
        _notify_completion(business_id, ctx["archetype"], result)
        if tracking_ids:
            db.table("tasks").update({"status": "completed"}).in_("id", tracking_ids).execute()

    # Create auto pipeline-summary task card
    if create_summary_task:
        try:
            tasks_sync.create_pipeline_task(business_id, ctx["archetype"], result, activity_log_id)
        except Exception:
            pass

    return to_summary(result, ctx["archetype"])
