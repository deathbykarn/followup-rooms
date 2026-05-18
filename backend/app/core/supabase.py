"""
Supabase client factory.

CRITICAL: Both factories MUST return a new client instance per call.
Module-scoped Supabase clients leak sessions across users on serverless
platforms (Vercel Fluid Compute, Cloud Run). See design doc §9.3.
"""
from supabase import Client, create_client

from app.core.config import get_settings


def get_anon_client() -> Client:
    """
    Returns a new Supabase client using the anon (public) key.
    Use this for operations that should respect RLS as the calling user.
    """
    settings = get_settings()
    return create_client(settings.supabase_url, settings.supabase_anon_key)


def get_service_client() -> Client:
    """
    Returns a new Supabase client using the service role key.
    Use this ONLY for backend operations that bypass RLS
    (e.g., migrations, system tasks). Never expose to client code.
    """
    settings = get_settings()
    return create_client(settings.supabase_url, settings.supabase_service_role_key)
