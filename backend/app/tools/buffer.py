"""Buffer API — schedules social media posts across connected channels."""
import httpx


def get_profiles(access_token: str) -> list[dict]:
    r = httpx.get(
        "https://api.bufferapp.com/1/profiles.json",
        params={"access_token": access_token},
        timeout=15,
    )
    r.raise_for_status()
    return [{"id": p["id"], "service": p["service"], "name": p.get("formatted_username", "")} for p in r.json()]


def schedule_update(access_token: str, profile_id: str, text: str, now: bool = False) -> dict:
    payload = {
        "text": text,
        "profile_ids[]": profile_id,
        "access_token": access_token,
    }
    if now:
        payload["now"] = "true"

    r = httpx.post(
        "https://api.bufferapp.com/1/updates/create.json",
        data=payload,
        timeout=15,
    )
    r.raise_for_status()
    data = r.json()
    updates = data.get("updates", [{}])
    first = updates[0] if updates else {}
    return {"update_id": first.get("id"), "status": first.get("status", "buffer")}


def schedule_to_all_profiles(access_token: str, text: str) -> list[dict]:
    profiles = get_profiles(access_token)
    results = []
    for profile in profiles:
        try:
            result = schedule_update(access_token, profile["id"], text)
            results.append({**result, "service": profile["service"]})
        except Exception as e:
            results.append({"service": profile["service"], "error": str(e)})
    return results
