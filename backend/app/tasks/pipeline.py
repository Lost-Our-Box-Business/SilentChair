"""Celery tasks for scheduled pipeline runs."""
from celery.schedules import crontab

from app.worker import celery_app
from app.db.client import get_supabase
from app.services.activity import log_pipeline_run, notify


def _load_context(business_id: str) -> dict | None:
    db = get_supabase()

    biz_result = db.table("businesses").select("*").eq("id", business_id).execute()
    if not biz_result.data:
        return None
    biz = biz_result.data[0]

    tools_result = (
        db.table("agent_tools")
        .select("tool_name,key_source,encrypted_key")
        .eq("business_id", business_id)
        .execute()
    )
    tool_keys: dict = {}
    for row in tools_result.data:
        if row["key_source"] == "user" and row.get("encrypted_key"):
            tool_keys[row["tool_name"]] = row["encrypted_key"]
        else:
            tool_keys[row["tool_name"]] = None

    dept_result = (
        db.table("departments")
        .select("dept_type")
        .eq("business_id", business_id)
        .eq("is_active", True)
        .execute()
    )
    return {
        "profile": biz.get("profile", {}),
        "autonomy": biz.get("autonomy", "major_decisions"),
        "archetype": biz.get("archetype", "content_agency"),
        "tool_keys": tool_keys,
        "active_dept_types": [r["dept_type"] for r in dept_result.data],
    }


def _run(business_id: str, ctx: dict) -> dict:
    archetype = ctx["archetype"]
    kwargs = dict(
        business_id=business_id,
        business_profile=ctx["profile"],
        tool_keys=ctx["tool_keys"],
        autonomy=ctx["autonomy"],
        active_dept_types=ctx["active_dept_types"],
    )
    if archetype == "lead_generation":
        from app.agents.lead_gen_pipeline import run_lead_gen_pipeline
        return run_lead_gen_pipeline(**kwargs)
    elif archetype == "client_acquisition":
        from app.agents.client_acquisition_pipeline import run_client_acquisition_pipeline
        return run_client_acquisition_pipeline(**kwargs)
    else:
        from app.agents.content_pipeline import run_content_pipeline
        return run_content_pipeline(**kwargs)


@celery_app.task(bind=True, name="app.tasks.pipeline.run_pipeline_for_business")
def run_pipeline_for_business(self, business_id: str) -> dict:
    ctx = _load_context(business_id)
    if not ctx:
        return {"error": "Business not found"}

    result = _run(business_id, ctx)
    log_pipeline_run(business_id, result)

    if result.get("approval_required"):
        notify(business_id, result.get("approval_action", "Action requires approval"), requires_approval=True)
    else:
        notify(business_id, f"Scheduled pipeline complete for archetype: {ctx['archetype']}")

    return {"status": "awaiting_approval" if result.get("approval_required") else "complete"}


@celery_app.task(name="app.tasks.pipeline.run_all_active_pipelines")
def run_all_active_pipelines() -> dict:
    db = get_supabase()
    result = db.table("businesses").select("id").eq("status", "active").execute()
    for row in result.data:
        run_pipeline_for_business.delay(row["id"])
    return {"triggered": len(result.data)}


celery_app.conf.beat_schedule = {
    "daily-pipeline": {
        "task": "app.tasks.pipeline.run_all_active_pipelines",
        "schedule": crontab(hour=6, minute=0),
    },
}
