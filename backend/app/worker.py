"""Stub — Celery replaced by APScheduler + threading. Kept to avoid import errors."""


class _NoOpTask:
    def apply_async(self, *a, **kw):
        pass

    def __call__(self, *a, **kw):
        pass


class _NoOpCelery:
    def task(self, *a, **kw):
        def decorator(fn):
            return fn
        return decorator


celery_app = _NoOpCelery()
