from unittest.mock import MagicMock

from app.services.storage import BUCKET, StorageService


def test_upload_uses_operator_then_job_then_filename_path():
    fake_db = MagicMock()
    svc = StorageService(supabase=fake_db)

    path = svc.upload(
        operator_id="op-1",
        ingestion_job_id="job-1",
        filename="viewing-sarah.txt",
        content=b"hello world",
        mime_type="text/plain",
    )

    assert path == "op-1/job-1/viewing-sarah.txt"
    fake_db.storage.from_.assert_called_once_with(BUCKET)
    upload_call = fake_db.storage.from_.return_value.upload
    upload_call.assert_called_once()
    _, kwargs = upload_call.call_args
    assert kwargs["path"] == "op-1/job-1/viewing-sarah.txt"
    assert kwargs["file"] == b"hello world"
    assert kwargs["file_options"]["content-type"] == "text/plain"
    assert kwargs["file_options"]["upsert"] == "false"


def test_download_passes_through_to_storage_client():
    fake_db = MagicMock()
    fake_db.storage.from_.return_value.download.return_value = b"file bytes"
    svc = StorageService(supabase=fake_db)

    result = svc.download("op-1/job-1/file.txt")
    assert result == b"file bytes"
    fake_db.storage.from_.return_value.download.assert_called_once_with("op-1/job-1/file.txt")


def test_signed_url_returns_signed_url_field():
    fake_db = MagicMock()
    fake_db.storage.from_.return_value.create_signed_url.return_value = {
        "signedURL": "https://supa/signed?token=abc",
    }
    svc = StorageService(supabase=fake_db)

    url = svc.signed_url("op-1/job-1/file.mp3", expires_in_seconds=7200)
    assert url == "https://supa/signed?token=abc"
    fake_db.storage.from_.return_value.create_signed_url.assert_called_once_with(
        "op-1/job-1/file.mp3", 7200,
    )
