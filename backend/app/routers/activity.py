"""Activity feed, pipeline trigger, and approval endpoints."""
from fastapi import APIRouter, HTTPException

from app.db.client import get_supabase
from app.services.activity import (
    get_activity_feed, approve_action, log_pipeline_run,
    notify, load_business_context, do_pipeline_resume,
)
from app.services import tasks_sync

router = APIRouter(tags=["activity"])


# ── Helpers ───────────────────────────────────────────────────────────────────

def _run_pipeline_for_archetype(business_id: str, ctx: dict) -> dict:
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


def _pipeline_summary(result: dict, archetype: str) -> dict:
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


# ── Routes ────────────────────────────────────────────────────────────────────

@router.get("/activity/{business_id}")
async def get_feed(business_id: str, limit: int = 50):
    return get_activity_feed(business_id, limit=limit)


@router.post("/activity/{activity_id}/approve")
async def approve(activity_id: str):
    db = get_supabase()
    row_result = db.table("activity_log").select("*").eq("id", activity_id).execute()
    if not row_result.data:
        raise HTTPException(status_code=404, detail="Activity not found")

    row = row_result.data[0]
    if not row.get("requires_approval"):
        raise HTTPException(status_code=400, detail="This action does not require approval")
    if row.get("approved_at"):
        raise HTTPException(status_code=400, detail="Already approved")

    updated = approve_action(activity_id)
    do_pipeline_resume(activity_id, row)
    tasks_sync.complete_pipeline_task(activity_id)
    return updated


@router.post("/pipeline/run/{business_id}")
async def run_pipeline(business_id: str):
    try:
        ctx = load_business_context(business_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    try:
        result = _run_pipeline_for_archetype(business_id, ctx)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline error: {e}")

    activity_log_id = log_pipeline_run(business_id, result)

    if result.get("approval_required"):
        notify(business_id, result.get("approval_action", "Action requires approval"), requires_approval=True)
    else:
        _notify_completion(business_id, ctx["archetype"], result)

    try:
        tasks_sync.create_pipeline_task(business_id, ctx["archetype"], result, activity_log_id)
    except Exception:
        pass

    return _pipeline_summary(result, ctx["archetype"])
