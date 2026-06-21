"""Task Board API — CRUD for tasks table."""
from fastapi import APIRouter

router = APIRouter()


# GET  /api/tasks/{business_id}         → list[Task] (filterable by ?status= and ?department=)
# POST /api/tasks/{business_id}         → Task (user-created task)
# PATCH /api/tasks/{task_id}/status     → Task
# POST /api/tasks/{task_id}/approve     → Task (awaiting_approval → completed, resumes pipeline)
# DELETE /api/tasks/{task_id}           → 204
# GET  /api/tasks/global/{user_id}      → list[Task] (all businesses, for global view)
