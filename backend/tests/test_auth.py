from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from app.core.auth import get_current_operator_id


@pytest.mark.asyncio
async def test_get_current_operator_id_returns_uid_from_valid_token(monkeypatch):
    fake_user = MagicMock()
    fake_user.id = "op-uuid-from-jwt"

    fake_response = MagicMock()
    fake_response.user = fake_user

    fake_supabase = MagicMock()
    fake_supabase.auth.get_user.return_value = fake_response

    monkeypatch.setattr("app.core.auth.get_anon_client", lambda: fake_supabase)

    result = await get_current_operator_id(authorization="Bearer valid-token")
    assert result == "op-uuid-from-jwt"


@pytest.mark.asyncio
async def test_get_current_operator_id_rejects_missing_header():
    with pytest.raises(HTTPException) as exc:
        await get_current_operator_id(authorization=None)
    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_get_current_operator_id_rejects_invalid_token(monkeypatch):
    fake_supabase = MagicMock()
    fake_supabase.auth.get_user.side_effect = Exception("invalid token")
    monkeypatch.setattr("app.core.auth.get_anon_client", lambda: fake_supabase)

    with pytest.raises(HTTPException) as exc:
        await get_current_operator_id(authorization="Bearer bad-token")
    assert exc.value.status_code == 401
