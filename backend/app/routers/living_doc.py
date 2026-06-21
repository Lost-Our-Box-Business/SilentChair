"""Living Business Document API — fetch and correct business context."""
import traceback
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services import living_doc

router = APIRouter(prefix="/business", tags=["business"])


class CorrectionRequest(BaseModel):
    message: str


@router.get("/{business_id}/context")
def get_context(business_id: str):
    """Return the business_context for a business. Lazily initializes if empty."""
    try:
        return living_doc.get_context(business_id)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{business_id}/context/correct")
def correct_context(business_id: str, req: CorrectionRequest):
    """Apply a user-stated correction to the business context."""
    try:
        return living_doc.propose_correction(business_id, req.message)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
