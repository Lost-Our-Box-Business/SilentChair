"""Scheduler tasks — plain functions; APScheduler + threading replace Celery+Redis."""


def run_tick() -> dict:
    """Main heartbeat — called by APScheduler every 5 minutes via app.scheduler."""
    from app.services.department_runner import tick
    triggered = tick()
    return {"triggered": triggered}


def start_agent_task(business_id: str, dept_type: str, task_id: str, locale: str = "en") -> dict:
    """Start a specific planned agent task."""
    from app.services.department_runner import run_task
    try:
        result = run_task(business_id, dept_type, task_id=task_id, locale=locale)
        return {"status": result.status, "task_id": result.task_id}
    except Exception as e:
        return {"error": str(e)}


def resume_agent_task(business_id: str, dept_type: str, task_id: str, locale: str = "en") -> dict:
    """Resume an in-progress agent task after its requested delay."""
    from app.services.department_runner import run_task
    try:
        result = run_task(business_id, dept_type, task_id=task_id, locale=locale)
        return {"status": result.status, "task_id": result.task_id}
    except Exception as e:
        return {"error": str(e)}


def run_pipeline_for_business(business_id: str) -> dict:
    """Deprecated: use DepartmentRunner.start() instead. Kept for compatibility."""
    from app.services.department_runner import start
    try:
        start(business_id)
        return {"status": "started"}
    except Exception as e:
        return {"error": str(e)}
