"""
Ingestion uploads API.

POST /uploads                — multipart file + client_id + upload_type;
                                persists to Storage, inserts ingestion_jobs,
                                schedules BackgroundTask worker, returns 202
                                + job row for immediate UI status card.
GET  /uploads/{id}           — fetch a single job (poll target).
GET  /uploads?client_id=...  — recent jobs for a client (status feed).
"""
import logging
from typing import Literal

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
    status,
)

from app.core.auth import get_current_operator_id
from app.core.supabase import get_service_client
from app.models.ingestion import IngestionJobResponse
from app.services.ingestion_worker import IngestionWorker
from app.services.storage import StorageService

router = APIRouter(prefix="/uploads", tags=["uploads"])
logger = logging.getLogger(__name__)

ALLOWED_MIME_TYPES = frozenset({
    "text/plain", "text/vtt", "application/x-subrip",
    "audio/mpeg", "audio/mp4", "audio/x-m4a",
    "audio/wav", "audio/x-wav",
    "audio/ogg", "audio/webm", "audio/aac",
})
MAX_BYTES = 100 * 1024 * 1024  # 100 MB; matches storage bucket limit


def _run_worker(job_id: str) -> None:
    """Background task entry point — instantiates a fresh worker with a
    fresh service-role supabase client per task (no shared state across
    BackgroundTasks; matches the request-scoped client pattern)."""
    try:
        worker = IngestionWorker(supabase=get_service_client())
        worker.run(job_id)
    except Exception:
        logger.exception("ingestion worker failed for job_id=%s", job_id)


@router.post("", status_code=status.HTTP_202_ACCEPTED, response_model=IngestionJobResponse)
async def create_upload(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    client_id: str = Form(...),
    upload_type: Literal["transcript", "voice_memo"] = Form(...),
    operator_id: str = Depends(get_current_operator_id),
) -> IngestionJobResponse:
    content = await file.read()
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="Empty file")
    if len(content) > MAX_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"File too large ({len(content)} bytes; 100MB max)",
        )
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=415,
            detail=(
                f"Unsupported mime type '{file.content_type}'. "
                f"Allowed: {sorted(ALLOWED_MIME_TYPES)}"
            ),
        )

    db = get_service_client()

    # 1. Insert the row with placeholder storage_path so we have an id.
    placeholder_path = f"{operator_id}/pending/{file.filename}"
    insert_resp = (
        db.table("ingestion_jobs")
        .insert({
            "operator_id": operator_id,
            "client_id": client_id,
            "upload_type": upload_type,
            "storage_path": placeholder_path,
            "original_filename": file.filename or "upload",
            "mime_type": file.content_type,
            "size_bytes": len(content),
        })
        .execute()
    )
    job_row = insert_resp.data[0]
    job_id = job_row["id"]

    # 2. Upload to Storage using the real path convention.
    storage = StorageService(db)
    try:
        storage_path = storage.upload(
            operator_id=operator_id,
            ingestion_job_id=job_id,
            filename=file.filename or "upload",
            content=content,
            mime_type=file.content_type,
        )
    except Exception as exc:
        # Roll the job into failed state so the UI surfaces the upload error.
        db.table("ingestion_jobs").update({
            "state": "failed",
            "error_code": "storage_failed",
            "error_message": str(exc)[:500],
        }).eq("id", job_id).execute()
        raise HTTPException(status_code=502, detail=f"Storage upload failed: {exc}") from exc

    # 3. Persist the real storage_path.
    updated = (
        db.table("ingestion_jobs")
        .update({"storage_path": storage_path})
        .eq("id", job_id)
        .execute()
    )
    job_row = updated.data[0] if updated.data else {**job_row, "storage_path": storage_path}

    # 4. Schedule the worker. BackgroundTasks runs after the response.
    background_tasks.add_task(_run_worker, job_id)

    return IngestionJobResponse(**job_row)


@router.get("/{job_id}", response_model=IngestionJobResponse)
async def get_upload(
    job_id: str,
    operator_id: str = Depends(get_current_operator_id),
) -> IngestionJobResponse:
    db = get_service_client()
    resp = (
        db.table("ingestion_jobs")
        .select("*")
        .eq("id", job_id)
        .eq("operator_id", operator_id)
        .maybe_single()
        .execute()
    )
    if not resp or not resp.data:
        raise HTTPException(status_code=404, detail="ingestion job not found")
    return IngestionJobResponse(**resp.data)


@router.get("", response_model=list[IngestionJobResponse])
async def list_uploads(
    client_id: str = Query(..., description="UUID of the client to list uploads for"),
    operator_id: str = Depends(get_current_operator_id),
) -> list[IngestionJobResponse]:
    db = get_service_client()
    resp = (
        db.table("ingestion_jobs")
        .select("*")
        .eq("operator_id", operator_id)
        .eq("client_id", client_id)
        .order("created_at", desc=True)
        .limit(50)
        .execute()
    )
    return [IngestionJobResponse(**row) for row in (resp.data or [])]
