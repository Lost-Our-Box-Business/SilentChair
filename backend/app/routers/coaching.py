"""Coach scheduling API — sessions and AI briefing generation."""
from fastapi import APIRouter

router = APIRouter()


# GET  /api/coaching/{business_id}/sessions             → list[CoachSession]
# POST /api/coaching/{business_id}/briefing/{session_id} → CoachSession (generates AI briefing)
# GET  /api/coaching/link/{business_id}                 → {scheduling_url} (Calendly link)
