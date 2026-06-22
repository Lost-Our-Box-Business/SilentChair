"""Celery tasks for scheduled and on-demand agent execution."""
from celery.schedules import crontab

from app.worker import celery_app


@celery_app.task(name="app.tasks.pipeline.run_tick")
def run_tick() -> dict:
    """
    Main heartbeat — runs every 5 minutes.
    Delegates to DepartmentRunner.tick() which:
    1. Resumes in-progress tasks whose resume_at has passed (agent micro-scheduling)
    2. Triggers manager.evaluate() for departments whose manager_next_eval_at has passed
    """
    from app.services.department_runner import tick
    triggered = tick()
    return {"triggered": triggered}


@celery_app.task(name="app.tasks.pipeline.start_agent_task")
def start_agent_task(business_id: str, dept_type: str, task_id: str, locale: str = "en") -> dict:
    """Start a specific planned agent task. Scheduled by DepartmentRunner when manager decides."""
    from app.services.department_runner import run_task
    try:
        result = run_task(business_id, dept_type, task_id=task_id, locale=locale)
        return {"status": result.status, "task_id": result.task_id}
    except Exception as e:
        return {"error": str(e)}


@celery_app.task(name="app.tasks.pipeline.resume_agent_task")
def resume_agent_task(business_id: str, dept_type: str, task_id: str, locale: str = "en") -> dict:
    """Resume an in-progress agent task after its requested delay (micro-scheduling)."""
    from app.services.department_runner import run_task
    try:
        result = run_task(business_id, dept_type, task_id=task_id, locale=locale)
        return {"status": result.status, "task_id": result.task_id}
    except Exception as e:
        return {"error": str(e)}


# Legacy task kept for backward compatibility with any existing Celery queue items
@celery_app.task(bind=True, name="app.tasks.pipeline.run_pipeline_for_business")
def run_pipeline_for_business(self, business_id: str) -> dict:
    """Deprecated: use DepartmentRunner.start() instead. Kept for queue drain."""
    from app.services.department_runner import start
    try:
        start(business_id)
        return {"status": "started"}
    except Exception as e:
        return {"error": str(e)}


celery_app.conf.beat_schedule = {
    "agent-tick": {
        "task": "app.tasks.pipeline.run_tick",
        "schedule": crontab(minute="*/5"),
    },
}
