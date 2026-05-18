"""
FastAPI auth dependency.

Validates the Supabase JWT from the Authorization header and returns
the operator UUID. Uses getUser() which hits the Supabase auth server
to verify the token (only trustworthy check per design doc §9.3).
"""
from fastapi import Header, HTTPException

from app.core.supabase import get_anon_client


async def get_current_operator_id(
    authorization: str | None = Header(default=None),
) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or malformed Authorization header")

    token = authorization.removeprefix("Bearer ").strip()

    try:
        supabase = get_anon_client()
        response = supabase.auth.get_user(token)
    except Exception as exc:
        raise HTTPException(status_code=401, detail=f"Invalid token: {exc}") from exc

    if not response or not response.user:
        raise HTTPException(status_code=401, detail="Token did not resolve to a user")

    return str(response.user.id)
