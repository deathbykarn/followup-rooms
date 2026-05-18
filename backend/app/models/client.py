from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


RelationshipType = Literal[
    "buyer", "seller", "landlord", "tenant", "investor",
    "commercial_landlord", "commercial_tenant", "referral_partner", "other",
]


class CreateClientRequest(BaseModel):
    client_name: str = Field(..., min_length=1, max_length=200)
    phone_number: str | None = Field(default=None, max_length=50)
    relationship_type: RelationshipType = "buyer"
    short_context: str = Field(
        ...,
        min_length=20,
        max_length=1000,
        description="Required seed context (cold-start mitigation per design doc §5.7)",
    )
    tags: list[str] = Field(default_factory=list)
    aliases: list[str] = Field(default_factory=list)


class ClientResponse(BaseModel):
    id: str
    client_name: str
    phone_number: str | None
    relationship_type: str
    status: str
    short_context: str
    tags: list[str]
    aliases: list[str]
    created_at: datetime
    updated_at: datetime
