"""Background scheduler — replaces Celery+Beat with no broker dependency.

Run with: python -m app.scheduler
Railway start command for eloquent-fulfillment:  python -m app.scheduler
"""
import logging

logger = logging.getLogger(__name__)


def run_tick_job():
    try:
        from app.services.department_runner import tick
        triggered = tick()
        logger.info(f"Tick complete: {triggered} action(s) triggered")
    except Exception as e:
        logger.error(f"Tick failed: {e}", exc_info=True)


if __name__ == "__main__":
    from apscheduler.schedulers.blocking import BlockingScheduler

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    scheduler = BlockingScheduler(timezone="UTC")
    scheduler.add_job(
        run_tick_job,
        "interval",
        minutes=5,
        id="agent-tick",
        max_instances=1,
        coalesce=True,
    )
    logger.info("Scheduler started — agent tick every 5 minutes")
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler stopped")
