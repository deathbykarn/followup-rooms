import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_settings_loads_from_env(monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "anon-test")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "service-test")
    monkeypatch.setenv("SUPABASE_DB_URL", "postgresql://test")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "ant-test")
    monkeypatch.setenv("OPENAI_API_KEY", "oa-test")

    settings = Settings()

    assert settings.supabase_url == "https://test.supabase.co"
    assert settings.supabase_anon_key == "anon-test"
    assert settings.supabase_service_role_key == "service-test"
    assert settings.anthropic_api_key == "ant-test"
    assert settings.openai_api_key == "oa-test"
    assert settings.env == "development"
    assert settings.log_level == "INFO"


def test_settings_requires_supabase_url(monkeypatch):
    # Clear env to ensure validation fires
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_supabase_client_factory_returns_new_instance_per_call():
    from app.core.supabase import get_anon_client
    c1 = get_anon_client()
    c2 = get_anon_client()
    # CRITICAL: must be different instances to avoid cross-user session leak
    assert c1 is not c2


def test_supabase_service_client_factory_returns_new_instance_per_call():
    from app.core.supabase import get_service_client
    c1 = get_service_client()
    c2 = get_service_client()
    assert c1 is not c2
