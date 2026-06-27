"""Celery application instance."""
import ssl
from celery import Celery
from app.config import settings

celery_app = Celery(
    "silentchair",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.tasks.pipeline"],
)

_ssl_opts = {"ssl_cert_reqs": ssl.CERT_NONE} if settings.redis_url.startswith("rediss://") else None

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    # Don't store task results in Redis — all state is tracked in Supabase.
    # This is the biggest lever for staying under Upstash's free-tier request limit.
    task_ignore_result=True,
    result_expires=300,
    broker_use_ssl=_ssl_opts,
    redis_backend_use_ssl=_ssl_opts,
)
