from fastapi import APIRouter, Depends, HTTPException

from app.core.auth import get_current_operator_id
from app.core.supabase import get_anon_client

router = APIRouter(prefix="/operators", tags=["operators"])


@router.get("/me")
async def get_me(operator_id: str = Depends(get_current_operator_id)) -> dict:
    """Return the current operator's profile row."""
    supabase = get_anon_client()
    response = (
        supabase.table("operators")
        .select(
            "id, email, name, company_name, role_title, industry, "
            "profile_photo_url, default_language, default_tone, timezone, created_at"
        )
        .eq("id", operator_id)
        .maybe_single()
        .execute()
    )

    if not response.data:
        raise HTTPException(status_code=404, detail="Operator profile not found")

    return response.data
