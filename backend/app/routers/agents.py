"""Agents router — business-level start/pause/resume and department overview."""
import traceback
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services import department_runner, approval_queue

router = APIRouter(prefix="/agents", tags=["agents"])


class ApprovalAction(BaseModel):
    user_id: str
    reason: str = ""


@router.get("/{business_id}")
def get_agents(business_id: str):
    """List all departments for a business with their current status and today's cost."""
    try:
        return department_runner.list_departments(business_id)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{business_id}/start")
def start_agents(business_id: str, locale: str = "en"):
    """Unpause the business and trigger the manager to evaluate each active department."""
    try:
        department_runner.start(business_id, locale=locale)
        return {"status": "started"}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{business_id}/pause")
def pause_agents(business_id: str):
    """Pause all agent activity for this business."""
    try:
        department_runner.pause(business_id)
        return {"status": "paused"}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{business_id}/resume")
def resume_agents(business_id: str, locale: str = "en"):
    """Unpause and immediately re-evaluate all active departments."""
    try:
        department_runner.resume(business_id, locale=locale)
        return {"status": "resumed"}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{business_id}/queue")
def get_approval_queue(business_id: str):
    """Return all pending approval items across all departments for this business."""
    try:
        return approval_queue.list_pending(business_id)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{business_id}/queue/{queue_id}/approve")
def approve_queue_item(business_id: str, queue_id: str, body: ApprovalAction):
    """Approve a pending approval queue item and execute the action."""
    try:
        return approval_queue.approve(queue_id, body.user_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{business_id}/queue/{queue_id}/reject")
def reject_queue_item(business_id: str, queue_id: str, body: ApprovalAction):
    """Reject a pending approval queue item."""
    try:
        return approval_queue.reject(queue_id, body.user_id, body.reason)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
