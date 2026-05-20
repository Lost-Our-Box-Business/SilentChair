import uuid
import traceback
from fastapi import APIRouter, HTTPException
from app.models.interview import InterviewRequest, InterviewResponse
from app.agents.business_analyst import run_interview_turn
from app.db.client import get_supabase

router = APIRouter(prefix="/interview", tags=["interview"])


@router.post("/turn", response_model=InterviewResponse)
async def interview_turn(req: InterviewRequest):
    session_id = req.session_id or str(uuid.uuid4())

    history = [{"role": m.role, "content": m.content} for m in req.history]

    try:
        result = run_interview_turn(history=history, user_message=req.message)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

    if result["is_complete"] and result["business_profile"]:
        try:
            db = get_supabase()
            db.table("businesses").upsert({
                "id": session_id,
                "user_id": req.user_id,
                "profile": result["business_profile"],
                "name": result["business_profile"].get("name", "Untitled Business"),
                "status": "onboarding",
            }).execute()
        except Exception:
            pass

    return InterviewResponse(
        session_id=session_id,
        message=result["message"],
        is_complete=result["is_complete"],
        business_profile=result["business_profile"],
    )


@router.get("/session/{session_id}")
async def get_session(session_id: str):
    db = get_supabase()
    result = db.table("businesses").select("*").eq("id", session_id).single().execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Session not found")
    return result.data
