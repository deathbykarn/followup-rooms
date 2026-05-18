"""
StorageService — thin wrapper over Supabase Storage for ingestion uploads.

Path convention: <operator_id>/<ingestion_job_id>/<original_filename>
The operator_id-first segment matches the RLS policy in migration 0012,
so authenticated reads via the anon client see only the operator's own
files; uploads via the service-role client bypass RLS but still honor
the convention.
"""
from supabase import Client

BUCKET = "ingestion-uploads"


class StorageService:
    def __init__(self, supabase: Client) -> None:
        self._db = supabase

    def upload(
        self,
        operator_id: str,
        ingestion_job_id: str,
        filename: str,
        content: bytes,
        mime_type: str,
    ) -> str:
        """Upload bytes to Storage; return the storage path."""
        path = f"{operator_id}/{ingestion_job_id}/{filename}"
        self._db.storage.from_(BUCKET).upload(
            path=path,
            file=content,
            file_options={"content-type": mime_type, "upsert": "false"},
        )
        return path

    def download(self, storage_path: str) -> bytes:
        """Download raw bytes for a stored object."""
        return self._db.storage.from_(BUCKET).download(storage_path)

    def signed_url(self, storage_path: str, expires_in_seconds: int = 3600) -> str:
        """
        Create a time-limited signed URL — used to hand the file to
        AssemblyAI for transcription without exposing the bucket publicly.
        """
        resp = self._db.storage.from_(BUCKET).create_signed_url(
            storage_path, expires_in_seconds,
        )
        return resp["signedURL"]
