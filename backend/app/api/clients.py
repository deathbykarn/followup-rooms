from fastapi import APIRouter, Depends, HTTPException, status

from app.core.auth import get_current_operator_id
from app.core.supabase import get_service_client
from app.models.client import ClientResponse, CreateClientRequest

router = APIRouter(prefix="/clients", tags=["clients"])


@router.post("", status_code=status.HTTP_201_CREATED, response_model=ClientResponse)
async def create_client(
    payload: CreateClientRequest,
    operator_id: str = Depends(get_current_operator_id),
) -> ClientResponse:
    supabase = get_service_client()
    response = (
        supabase.table("clients")
        .insert({
            "operator_id": operator_id,
            "client_name": payload.client_name,
            "phone_number": payload.phone_number,
            "relationship_type": payload.relationship_type,
            "short_context": payload.short_context,
            "tags": payload.tags,
            "aliases": payload.aliases,
        })
        .execute()
    )

    if not response.data:
        raise HTTPException(status_code=500, detail="Failed to create client")

    return ClientResponse(**response.data[0])


@router.get("", response_model=list[ClientResponse])
async def list_clients(
    operator_id: str = Depends(get_current_operator_id),
) -> list[ClientResponse]:
    supabase = get_service_client()
    response = (
        supabase.table("clients")
        .select(
            "id, client_name, phone_number, relationship_type, status, "
            "short_context, tags, aliases, created_at, updated_at"
        )
        .eq("operator_id", operator_id)
        .eq("is_deleted", False)
        .order("created_at", desc=True)
        .execute()
    )

    return [ClientResponse(**row) for row in (response.data or [])]
