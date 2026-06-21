"""Balance API — read user balance and spend ledger."""
from fastapi import APIRouter

router = APIRouter()


# GET  /api/balance                     → UserBalance
# GET  /api/balance/ledger              → list[SpendEntry] (last 30 days, ?business_id= optional)
