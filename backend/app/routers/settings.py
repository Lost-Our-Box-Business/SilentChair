"""User settings API — profile, notifications, and connected accounts."""
from fastapi import APIRouter

router = APIRouter()


# GET    /api/settings/profile                              → UserProfile
# PATCH  /api/settings/profile                              → UserProfile

# GET    /api/settings/notifications/{business_id}          → NotificationPrefs
# PATCH  /api/settings/notifications/{business_id}          → NotificationPrefs

# GET    /api/settings/connected/{business_id}              → list[ConnectedAccount]
# POST   /api/settings/connected/{business_id}/oauth/start  → {redirect_url}
# GET    /api/settings/connected/{business_id}/oauth/callback → ConnectedAccount
# DELETE /api/settings/connected/{account_id}               → 204
