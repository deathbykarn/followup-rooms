# Ingestion: Transcript + Voice Upload — Implementation Plan (Plan 3)

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:executing-plans` (or `subagent-driven-development` if subagents available) to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Operator can upload a meeting transcript (text or audio) or a solo voice memo for a client; the system transcribes (if audio), stores raw event, extracts facts via the Plan 2 pipeline, regenerates the profile, and shows progress as the job runs.

**Architecture:** Async ingestion. POST /uploads accepts the file + client_id + upload_type, persists to Supabase Storage (Save Is Sacred — before any extraction), inserts an `ingestion_jobs` row in `queued` state, and schedules a FastAPI BackgroundTask. The worker walks the state machine `queued → transcribing → extracting → done` (or `failed`), updating `ingestion_jobs.state` so the frontend can poll. Transcription uses AssemblyAI (Universal-2 model; native diarization for multi-party). Voice memos and transcripts share the same pipeline — only the `source_type` enum value differs ('voice_memo' vs 'meeting_transcript') and `voice_memo` skips the `speaker_labels` prompt section.

**Tech Stack:** AssemblyAI Python SDK, Supabase Storage (already provisioned), FastAPI BackgroundTasks, react-dropzone (web), existing Plan 2 ExtractionPipeline + ProfileService.

**Out of scope (deferred):**
- WhatsApp ingestion (Plan 4)
- File drop / room attachments (Plan 5)
- Queue persistence across worker restarts (Arq + Redis — adopt when 10+ agents or transcripts >10min frequently fail)
- PDF / DOCX transcript parsing (Plan 3.5 if real users ask)
- Audio chunking for files > AssemblyAI's effective limit (not a v1 issue)

---

## Pre-flight Research (Task 1)

The user's saved feedback memory says: reflect on intent + research the meta before pattern-matching. Three things to verify before locking AssemblyAI in:

1. **AssemblyAI Singapore / APAC data residency.** SG PDPA expects personal data to either stay in-region or be transferred under acceptable safeguards. Verify AssemblyAI's data residency options as of May 2026. If none → either (a) document the PDPA exposure in operator onboarding, (b) switch to a provider with APAC region, or (c) self-host Whisper as a fallback.
2. **AssemblyAI Mandarin + Singlish accuracy.** SG real estate conversations frequently mix English, Mandarin, Singlish, sometimes Hokkien. AssemblyAI claims 99+ languages; verify Mandarin word-error-rate published benchmark + check whether code-switching mid-utterance is handled.
3. **AssemblyAI pricing May 2026.** Last public number (~$0.37/hr async) may have shifted. Budget impact: even at $1/hr × 50 hrs/agent/month × 5 agents = $250/mo, trivial for early validation but worth knowing.

If research reveals any blocker (no APAC, Mandarin WER >30%, pricing 10x'd), the plan pivots: see Decision Branch below.

**Decision branch (only if Task 1 blocks AssemblyAI):**
- Blocker = data residency only → Deepgram Nova-3 (US + EU regions, may have APAC by May 2026) + add PDPA disclosure to onboarding
- Blocker = Mandarin accuracy → AssemblyAI for English-only meetings + Whisper API fallback for Mandarin-flagged uploads (operator picks language at upload)
- Blocker = pricing → fall back to OpenAI Whisper API (already in deps); diarization deferred via PyAnnote post-process or just dropped

---

## Data Model

### New table: `ingestion_jobs` (migration 0011)

```sql
CREATE TABLE ingestion_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    operator_id UUID NOT NULL REFERENCES operators(id) ON DELETE CASCADE,
    client_id UUID NOT NULL REFERENCES clients(id) ON DELETE RESTRICT,

    -- What was uploaded
    upload_type TEXT NOT NULL CHECK (upload_type IN ('transcript', 'voice_memo')),
    storage_path TEXT NOT NULL,            -- Supabase Storage path; immutable
    original_filename TEXT NOT NULL,
    mime_type TEXT NOT NULL,
    size_bytes BIGINT NOT NULL CHECK (size_bytes > 0),

    -- State machine
    state TEXT NOT NULL DEFAULT 'queued' CHECK (state IN (
        'queued', 'transcribing', 'extracting', 'done', 'failed'
    )),
    error_message TEXT,                    -- populated when state='failed'
    error_code TEXT,                       -- machine-readable: transcription_failed | extraction_failed | storage_failed

    -- Outputs
    transcript_text TEXT,                  -- populated after transcription (also for text-uploaded transcripts)
    event_id UUID REFERENCES events(id),   -- populated after event creation
    transcription_metadata JSONB DEFAULT '{}'::jsonb,
        -- { provider: 'assemblyai', model: 'universal-2', duration_seconds: 1830,
        --   speakers: [{label: 'A', turn_count: 47}, ...], language: 'en' }

    -- Lifecycle
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_ingestion_jobs_operator_recent
    ON ingestion_jobs(operator_id, created_at DESC);
CREATE INDEX idx_ingestion_jobs_client_recent
    ON ingestion_jobs(client_id, created_at DESC);
CREATE INDEX idx_ingestion_jobs_active
    ON ingestion_jobs(state, created_at) WHERE state IN ('queued', 'transcribing', 'extracting');

-- RLS
ALTER TABLE ingestion_jobs ENABLE ROW LEVEL SECURITY;
CREATE POLICY ingestion_jobs_select ON ingestion_jobs
    FOR SELECT USING (operator_id = auth.uid());
CREATE POLICY ingestion_jobs_insert ON ingestion_jobs
    FOR INSERT WITH CHECK (operator_id = auth.uid());
CREATE POLICY ingestion_jobs_update ON ingestion_jobs
    FOR UPDATE USING (operator_id = auth.uid());
-- No DELETE policy; soft via state='failed' or just leave finished jobs.

-- Rollback:
-- DROP POLICY ingestion_jobs_update ON ingestion_jobs;
-- DROP POLICY ingestion_jobs_insert ON ingestion_jobs;
-- DROP POLICY ingestion_jobs_select ON ingestion_jobs;
-- DROP INDEX idx_ingestion_jobs_active;
-- DROP INDEX idx_ingestion_jobs_client_recent;
-- DROP INDEX idx_ingestion_jobs_operator_recent;
-- DROP TABLE ingestion_jobs;
```

### Supabase Storage bucket: `ingestion-uploads`

Created via migration 0012 (Storage buckets are objects in `storage.buckets`, manageable via SQL).

```sql
INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES (
    'ingestion-uploads',
    'ingestion-uploads',
    false,
    104857600,  -- 100 MB
    ARRAY[
        'text/plain', 'text/vtt', 'application/x-subrip',
        'audio/mpeg', 'audio/mp4', 'audio/x-m4a', 'audio/wav',
        'audio/ogg', 'audio/webm', 'audio/aac'
    ]
)
ON CONFLICT (id) DO NOTHING;

-- RLS on storage.objects for this bucket
CREATE POLICY ingestion_uploads_owner_select ON storage.objects
    FOR SELECT USING (
        bucket_id = 'ingestion-uploads'
        AND (storage.foldername(name))[1] = auth.uid()::text
    );
CREATE POLICY ingestion_uploads_owner_insert ON storage.objects
    FOR INSERT WITH CHECK (
        bucket_id = 'ingestion-uploads'
        AND (storage.foldername(name))[1] = auth.uid()::text
    );

-- Storage path convention: <operator_id>/<ingestion_job_id>/<original_filename>
-- Rollback:
-- DROP POLICY ingestion_uploads_owner_insert ON storage.objects;
-- DROP POLICY ingestion_uploads_owner_select ON storage.objects;
-- DELETE FROM storage.buckets WHERE id = 'ingestion-uploads';
```

---

## File Structure

```
backend/
├── app/
│   ├── api/
│   │   └── uploads.py              [NEW] POST /uploads, GET /uploads/{id}
│   ├── models/
│   │   └── ingestion.py            [NEW] Pydantic IngestionJob* models
│   ├── ai/
│   │   └── providers/
│   │       └── assemblyai.py       [NEW] AssemblyAIProvider — transcribe(path)
│   ├── services/
│   │   ├── transcription.py        [NEW] TranscriptionService abstraction
│   │   ├── storage.py              [NEW] Supabase Storage upload helper
│   │   ├── ingestion_worker.py     [NEW] Background worker — state machine
│   │   └── extraction_pipeline.py  [MODIFY] accept pre-existing event_id (skip insert)
│   └── ai/prompts/
│       └── extraction.py           [MODIFY] add speaker_labels support
└── tests/
    ├── test_storage_service.py     [NEW]
    ├── test_transcription_service.py [NEW]
    ├── test_ingestion_worker.py    [NEW]
    └── test_uploads_api.py         [NEW]

supabase/migrations/
├── 0011_ingestion_jobs.sql         [NEW]
└── 0012_ingestion_uploads_bucket.sql [NEW]

web/
├── app/dashboard/clients/[id]/
│   └── upload/page.tsx             [NEW] new tab
├── components/clients/
│   ├── upload-form.tsx             [NEW] drop zone + client component
│   └── ingestion-status-card.tsx   [NEW] polls /uploads/{id}, shows progress
├── lib/api/
│   └── uploads.ts                  [NEW] typed client for uploads endpoints
└── tests/unit/
    └── ingestion-status-card.test.tsx [NEW]
```

---

## Task Breakdown

### Task 1: Branch + research validation

**Files:**
- Read: design doc §5.1, §5.2 (transcript + voice memo channels)
- Research: AssemblyAI data residency, Mandarin support, May 2026 pricing

- [ ] **Step 1:** Confirm on branch `feat/ingestion-plan-3`. (`git status` shows branch.)
- [ ] **Step 2:** Use WebSearch / WebFetch to verify the three pre-flight items. Capture findings in `docs/findings/2026-05-18-assemblyai-validation.md` (≤200 words). If any blocker found, return to user before continuing — do not silently pivot.
- [ ] **Step 3:** Add `assemblyai>=0.30` to backend `pyproject.toml` dependencies. Add `aiofiles>=24` if not already (for streaming uploads).
- [ ] **Step 4:** `pip install -e ".[dev]"` to install.
- [ ] **Step 5:** Add `ASSEMBLYAI_API_KEY` to `backend/.env` placeholder + `app/core/config.py` Settings field.
- [ ] **Step 6:** Commit: `chore(deps): add assemblyai SDK + ASSEMBLYAI_API_KEY config`.

### Task 2: Pydantic models for IngestionJob

**Files:**
- Create: `backend/app/models/ingestion.py`
- Create: `backend/tests/test_models_ingestion.py`

- [ ] **Step 1:** Write the model module:

```python
# backend/app/models/ingestion.py
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

UploadType = Literal["transcript", "voice_memo"]
IngestionState = Literal["queued", "transcribing", "extracting", "done", "failed"]


class IngestionJobResponse(BaseModel):
    id: str
    client_id: str
    upload_type: UploadType
    original_filename: str
    mime_type: str
    size_bytes: int
    state: IngestionState
    error_message: str | None = None
    error_code: str | None = None
    transcript_text: str | None = None
    event_id: str | None = None
    transcription_metadata: dict[str, Any] = Field(default_factory=dict)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
```

- [ ] **Step 2:** Write `test_models_ingestion.py` covering: required fields enforce, optional fields default to None, state literal rejects bogus values.
- [ ] **Step 3:** `pytest tests/test_models_ingestion.py` — expect 3+ passing.
- [ ] **Step 4:** Commit: `feat(models): IngestionJob Pydantic models`.

### Task 3: Migration 0011 — ingestion_jobs table

**Files:**
- Create: `supabase/migrations/0011_ingestion_jobs.sql`

- [ ] **Step 1:** Write migration using the DDL from the Data Model section above. Include `-- Migration:` header and `-- Rollback:` block.
- [ ] **Step 2:** Add an `updated_at` trigger (mirror the one used on `clients` / `facts` for consistency).
- [ ] **Step 3:** `python backend/scripts/apply_migrations.py` — expect "Applying 1 new migration: 0011_ingestion_jobs.sql".
- [ ] **Step 4:** Verify in Supabase SQL editor:
  ```sql
  SELECT column_name, data_type FROM information_schema.columns
   WHERE table_name = 'ingestion_jobs' ORDER BY ordinal_position;
  ```
- [ ] **Step 5:** Commit: `feat(db): migration 0011 — ingestion_jobs table with state machine + RLS`.

### Task 4: Migration 0012 — storage bucket + RLS

**Files:**
- Create: `supabase/migrations/0012_ingestion_uploads_bucket.sql`

- [ ] **Step 1:** Write migration using the bucket SQL from the Data Model section. Use `ON CONFLICT DO NOTHING` so re-runs are safe.
- [ ] **Step 2:** Apply migration. Verify the bucket appears in Supabase Storage UI.
- [ ] **Step 3:** Verify policies:
  ```sql
  SELECT policyname FROM pg_policies WHERE tablename = 'objects'
   AND schemaname = 'storage' AND policyname LIKE 'ingestion_%';
  ```
  Expect 2 policies (select + insert).
- [ ] **Step 4:** Commit: `feat(db): migration 0012 — ingestion-uploads storage bucket + RLS`.

### Task 5: Storage service — upload to Supabase Storage

**Files:**
- Create: `backend/app/services/storage.py`
- Create: `backend/tests/test_storage_service.py`

- [ ] **Step 1:** Write `StorageService.upload(operator_id, ingestion_job_id, filename, content_bytes, mime_type) -> storage_path`:

```python
# backend/app/services/storage.py
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
        path = f"{operator_id}/{ingestion_job_id}/{filename}"
        self._db.storage.from_(BUCKET).upload(
            path=path,
            file=content,
            file_options={"content-type": mime_type, "upsert": "false"},
        )
        return path

    def download(self, storage_path: str) -> bytes:
        return self._db.storage.from_(BUCKET).download(storage_path)

    def signed_url(self, storage_path: str, expires_in_seconds: int = 3600) -> str:
        resp = self._db.storage.from_(BUCKET).create_signed_url(
            storage_path, expires_in_seconds,
        )
        return resp["signedURL"]
```

- [ ] **Step 2:** Test with mocked supabase client (3 tests: upload path format, download passthrough, signed_url passthrough).
- [ ] **Step 3:** `pytest tests/test_storage_service.py`.
- [ ] **Step 4:** Commit: `feat(services): StorageService — upload/download/signed_url wrapper`.

### Task 6: Transcription provider — AssemblyAI

**Files:**
- Create: `backend/app/ai/providers/assemblyai.py`
- Create: `backend/app/services/transcription.py`
- Create: `backend/tests/test_transcription_service.py`

- [ ] **Step 1:** Write the AssemblyAI provider — `transcribe(audio_url, diarize=True) -> TranscriptionResult`:

```python
# backend/app/ai/providers/assemblyai.py
from dataclasses import dataclass
import assemblyai as aai
from app.core.config import get_settings


@dataclass
class SpeakerTurn:
    speaker: str  # 'A', 'B', etc.
    text: str
    start_ms: int
    end_ms: int


@dataclass
class TranscriptionResult:
    text: str
    language: str | None
    duration_seconds: int | None
    speaker_turns: list[SpeakerTurn]  # empty when diarize=False
    provider: str = "assemblyai"
    model: str = "universal-2"


class AssemblyAIProvider:
    def __init__(self) -> None:
        aai.settings.api_key = get_settings().assemblyai_api_key
        self._client = aai.Transcriber()

    def transcribe(self, audio_url: str, diarize: bool = True) -> TranscriptionResult:
        config = aai.TranscriptionConfig(
            speech_model=aai.SpeechModel.universal,
            speaker_labels=diarize,
            language_detection=True,
        )
        transcript = self._client.transcribe(audio_url, config=config)
        if transcript.status == aai.TranscriptStatus.error:
            raise RuntimeError(f"AssemblyAI transcription failed: {transcript.error}")

        turns = []
        if diarize and transcript.utterances:
            turns = [
                SpeakerTurn(speaker=u.speaker, text=u.text, start_ms=u.start, end_ms=u.end)
                for u in transcript.utterances
            ]
        return TranscriptionResult(
            text=transcript.text or "",
            language=transcript.json_response.get("language_code"),
            duration_seconds=int(transcript.audio_duration) if transcript.audio_duration else None,
            speaker_turns=turns,
        )
```

- [ ] **Step 2:** Write a thin `TranscriptionService` wrapper that swaps providers per config (Pattern 20 — Vendor Agnostic):

```python
# backend/app/services/transcription.py
from app.ai.providers.assemblyai import AssemblyAIProvider, TranscriptionResult

class TranscriptionService:
    def __init__(self, provider: AssemblyAIProvider | None = None) -> None:
        self._provider = provider or AssemblyAIProvider()

    def transcribe(self, audio_url: str, diarize: bool) -> TranscriptionResult:
        return self._provider.transcribe(audio_url, diarize=diarize)
```

- [ ] **Step 3:** Test with a mock AssemblyAIProvider (3 tests: passthrough, diarize=True returns turns, diarize=False returns empty turns). Do NOT hit the real API in unit tests.
- [ ] **Step 4:** `pytest tests/test_transcription_service.py`.
- [ ] **Step 5:** Commit: `feat(ai): AssemblyAIProvider + TranscriptionService with diarization`.

### Task 7: Modify ExtractionPipeline to accept pre-existing event

**Files:**
- Modify: `backend/app/services/extraction_pipeline.py`
- Modify: `backend/tests/test_extraction_pipeline.py`

Phase 2 created the event inside `ingest_and_extract()`. Phase 3 needs to extract from an event the worker already inserted (so the operator can see the event id immediately on the upload card).

- [ ] **Step 1:** Add a sibling method `extract_for_event(operator_id, client_id, event_id, raw_text, speaker_labels=None) -> PipelineResult` that skips the event-insert step and goes straight to fetch-context → extract → match → persist → profile-regen.
- [ ] **Step 2:** Keep `ingest_and_extract()` as a thin wrapper that does the insert then calls `extract_for_event()`.
- [ ] **Step 3:** Add a test for `extract_for_event()` (existing event id, extraction proceeds without re-insert).
- [ ] **Step 4:** Existing tests must still pass.
- [ ] **Step 5:** Commit: `refactor(pipeline): split event-insert from extract path for ingestion worker reuse`.

### Task 8: Extraction prompt — speaker labels

**Files:**
- Modify: `backend/app/ai/prompts/extraction.py`
- Modify: `backend/tests/test_prompts_extraction.py`

- [ ] **Step 1:** Add optional `speaker_labels` parameter to `build_extraction_prompt()`. When provided, prepend a small instruction block:

```
SPEAKER ATTRIBUTION
The transcript below contains speaker labels (A, B, C, ...). The OPERATOR is speaker "{operator_speaker}". The CLIENT or other parties are the other speakers. When extracting facts about the CLIENT, prefer claims that come from the client's own speech (e.g., "wife wants Marine Parade" said by Speaker B/client) over claims made about the client by the operator. Always quote the client's words verbatim in source_spans when available.
```

- [ ] **Step 2:** When `speaker_labels=None` (manual note / voice memo / undetected), the prompt is unchanged from Plan 2.
- [ ] **Step 3:** Heuristic for `operator_speaker`: the speaker with the most words is usually the operator in a real estate viewing (they ask more questions). Document this assumption in a comment; defer better detection to Plan 3.5 if it becomes wrong.
- [ ] **Step 4:** Add a test for the prompt with speaker labels present + without.
- [ ] **Step 5:** Commit: `feat(prompts): extraction prompt handles speaker labels with operator-vs-client attribution hint`.

### Task 9: Ingestion worker — state machine

**Files:**
- Create: `backend/app/services/ingestion_worker.py`
- Create: `backend/tests/test_ingestion_worker.py`

- [ ] **Step 1:** Implement `IngestionWorker.run(job_id)`:

```python
# backend/app/services/ingestion_worker.py — sketch
class IngestionWorker:
    def __init__(self, supabase, storage, transcription, pipeline) -> None: ...

    def run(self, job_id: str) -> None:
        job = self._fetch_job(job_id)
        try:
            # 1. Transcribe (if voice; else load text directly)
            if job["upload_type"] == "voice_memo" or self._is_audio(job["mime_type"]):
                self._set_state(job_id, "transcribing", started_at=now())
                signed = self._storage.signed_url(job["storage_path"])
                result = self._transcription.transcribe(
                    signed,
                    diarize=(job["upload_type"] == "transcript"),
                )
                transcript = result.text
                speaker_labels = self._format_speaker_turns(result.speaker_turns)
                meta = {"provider": "assemblyai", "model": result.model,
                        "duration_seconds": result.duration_seconds,
                        "language": result.language,
                        "speaker_count": len({t.speaker for t in result.speaker_turns})}
            else:
                transcript = self._storage.download(job["storage_path"]).decode("utf-8")
                speaker_labels = None
                meta = {"provider": "text_upload"}

            self._update_job(job_id, transcript_text=transcript, transcription_metadata=meta)

            # 2. Insert event
            source_type = "meeting_transcript" if job["upload_type"] == "transcript" else "voice_memo"
            event_id = self._insert_event(job, source_type, transcript)
            self._update_job(job_id, event_id=event_id)

            # 3. Extract + profile regen
            self._set_state(job_id, "extracting")
            self._pipeline.extract_for_event(
                operator_id=job["operator_id"],
                client_id=job["client_id"],
                event_id=event_id,
                raw_text=transcript,
                speaker_labels=speaker_labels,
            )

            self._set_state(job_id, "done", completed_at=now())
        except Exception as e:
            self._set_state(
                job_id, "failed",
                error_message=str(e)[:500],
                error_code=self._classify_error(e),
                completed_at=now(),
            )
            raise  # let FastAPI logger pick it up
```

- [ ] **Step 2:** Helpers: `_format_speaker_turns()` returns a string like `Speaker A: …\nSpeaker B: …` for downstream extraction. `_is_audio()` checks mime_type prefix. `_classify_error()` returns one of `transcription_failed | extraction_failed | storage_failed`.
- [ ] **Step 3:** Tests with all mocks (no real network):
  - happy-path text transcript → state transitions queued→extracting→done
  - happy-path audio → transcribing→extracting→done
  - transcription failure → state=failed with error_code=transcription_failed
  - extraction failure → state=failed with error_code=extraction_failed
- [ ] **Step 4:** `pytest tests/test_ingestion_worker.py` — expect 4+ passing.
- [ ] **Step 5:** Commit: `feat(services): IngestionWorker state machine — transcribe→extract→profile`.

### Task 10: POST /uploads endpoint

**Files:**
- Create: `backend/app/api/uploads.py`
- Modify: `backend/app/main.py` (register router)
- Create: `backend/tests/test_uploads_api.py`

- [ ] **Step 1:** Endpoint accepts multipart form: file + client_id + upload_type. Validates mime type. Persists to Storage. Inserts ingestion_jobs row. Schedules BackgroundTask. Returns 202 Accepted + the job row.

```python
# sketch
@router.post("", status_code=202, response_model=IngestionJobResponse)
async def create_upload(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    client_id: str = Form(...),
    upload_type: Literal["transcript", "voice_memo"] = Form(...),
    operator_id: str = Depends(get_current_operator_id),
) -> IngestionJobResponse:
    content = await file.read()
    if len(content) > 100 * 1024 * 1024:
        raise HTTPException(413, "File too large (100MB max)")
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(415, f"Unsupported mime: {file.content_type}")

    db = get_service_client()
    job_row = db.table("ingestion_jobs").insert({
        "operator_id": operator_id,
        "client_id": client_id,
        "upload_type": upload_type,
        "original_filename": file.filename,
        "mime_type": file.content_type,
        "size_bytes": len(content),
        "storage_path": "pending",  # placeholder; updated after storage upload
    }).execute()
    job_id = job_row.data[0]["id"]

    storage = StorageService(db)
    path = storage.upload(operator_id, job_id, file.filename, content, file.content_type)
    db.table("ingestion_jobs").update({"storage_path": path}).eq("id", job_id).execute()

    background_tasks.add_task(_run_worker, job_id)
    return IngestionJobResponse(**job_row.data[0], storage_path=path)
```

- [ ] **Step 2:** GET /uploads/{job_id} returns the job row (operator-scoped). Tests cover 404 + 200 + auth.
- [ ] **Step 3:** GET /uploads?client_id=... lists recent jobs for a client (status feed).
- [ ] **Step 4:** Tests: rejects wrong mime, rejects oversized, schedules BackgroundTask (mock), 404 on stranger's job.
- [ ] **Step 5:** Register router in `app/main.py`.
- [ ] **Step 6:** `pytest tests/test_uploads_api.py` — expect 5+ passing.
- [ ] **Step 7:** Commit: `feat(api): POST /uploads + GET /uploads/{id} with BackgroundTasks`.

### Task 11: Web — uploads API client + Upload tab page

**Files:**
- Create: `web/lib/api/uploads.ts`
- Create: `web/app/dashboard/clients/[id]/upload/page.tsx`
- Modify: `web/app/dashboard/clients/[id]/layout.tsx` (add Upload tab)

- [ ] **Step 1:** Write `lib/api/uploads.ts` mirroring the Plan 2 shape:

```ts
export type UploadType = "transcript" | "voice_memo";
export type IngestionState = "queued" | "transcribing" | "extracting" | "done" | "failed";
export type IngestionJob = { /* match backend IngestionJobResponse */ };

export async function createUpload(file: File, clientId: string, uploadType: UploadType): Promise<IngestionJob> {
  // multipart — need bespoke fetch (callBackend only does JSON)
  const supabase = createClient();
  const { data: { session } } = await supabase.auth.getSession();
  const form = new FormData();
  form.append("file", file);
  form.append("client_id", clientId);
  form.append("upload_type", uploadType);
  const resp = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_API_URL}/uploads`, {
    method: "POST",
    headers: { Authorization: `Bearer ${session!.access_token}` },
    body: form,
  });
  if (!resp.ok) throw new Error((await resp.json()).detail || `Upload ${resp.status}`);
  return resp.json();
}

export function getUpload(jobId: string): Promise<IngestionJob> {
  return callBackend<IngestionJob>(`/uploads/${jobId}`);
}

export function listUploads(clientId: string): Promise<IngestionJob[]> {
  return callBackend<IngestionJob[]>(`/uploads?client_id=${clientId}`);
}
```

- [ ] **Step 2:** Add Upload tab to client detail nav (`layout.tsx` TABS array).
- [ ] **Step 3:** Page component renders `<UploadForm clientId={id} />` + `<IngestionFeed clientId={id} />`.
- [ ] **Step 4:** `npx tsc --noEmit`.
- [ ] **Step 5:** Commit: `feat(web): uploads API client + Upload tab scaffolding`.

### Task 12: Web — UploadForm with drop zone

**Files:**
- Create: `web/components/clients/upload-form.tsx`

- [ ] **Step 1:** Install `react-dropzone` via npm (single dep). `npm install react-dropzone`.
- [ ] **Step 2:** Build form: drop zone accepting text + audio mimes, upload_type radio (transcript vs voice memo), submit calls `createUpload()`, on success appends the returned job to a parent-controlled list so the IngestionFeed picks it up.

```tsx
// sketch
const { getRootProps, getInputProps, acceptedFiles } = useDropzone({
  accept: {
    "text/plain": [".txt"],
    "text/vtt": [".vtt"],
    "application/x-subrip": [".srt"],
    "audio/*": [".mp3", ".m4a", ".wav", ".ogg", ".webm"],
  },
  maxSize: 100 * 1024 * 1024,
  multiple: false,
});
```

- [ ] **Step 3:** Show selected file name + size. Disable submit if no file.
- [ ] **Step 4:** Commit: `feat(web): UploadForm with react-dropzone + transcript/voice-memo toggle`.

### Task 13: Web — IngestionStatusCard with polling

**Files:**
- Create: `web/components/clients/ingestion-status-card.tsx`
- Create: `web/components/clients/ingestion-feed.tsx`
- Create: `web/tests/unit/ingestion-status-card.test.tsx`

- [ ] **Step 1:** `IngestionStatusCard` polls `getUpload(jobId)` every 3s while state ∈ {queued, transcribing, extracting}; stops polling on done|failed. Shows: state pill, original filename, elapsed time, error_message if failed. On `done` shows a link to the Facts tab.
- [ ] **Step 2:** `IngestionFeed` fetches `listUploads(clientId)` once on mount; renders an `<IngestionStatusCard>` per job. New uploads (from the form) are prepended via prop.
- [ ] **Step 3:** Unit test: state machine UI — render with state=queued shows "Queued"; state=done renders the Facts link; state=failed shows error_message; polling stops when state becomes terminal.
- [ ] **Step 4:** `npm test` — expect existing tests still passing + new ones added.
- [ ] **Step 5:** Commit: `feat(web): IngestionStatusCard with polling + IngestionFeed list`.

### Task 14: E2E test — upload happy path

**Files:**
- Create: `web/tests/e2e/upload-extraction.spec.ts`

- [ ] **Step 1:** Skip in CI (no real AssemblyAI key). Locally:
  - Sign up + log in (reuse pattern from `note-extraction-reject.spec.ts`)
  - Create a client
  - Navigate to Upload tab
  - Upload a fixture text transcript (`web/tests/fixtures/sample-transcript.txt` — 1 page sample real-estate viewing convo)
  - Wait for state=done (timeout 180s)
  - Switch to Facts tab → expect ≥1 fact
- [ ] **Step 2:** Add the fixture file.
- [ ] **Step 3:** Commit: `test(e2e): upload → transcribe-skip → extract → facts visible`.

### Task 15: SCHEMA_REFERENCE.md update

**Files:**
- Modify: `supabase/SCHEMA_REFERENCE.md`

- [ ] **Step 1:** Add `ingestion_jobs` table section (columns, indexes, RLS, state machine description).
- [ ] **Step 2:** Add storage bucket section noting the `ingestion-uploads` bucket + path convention.
- [ ] **Step 3:** Update "Last updated" line.
- [ ] **Step 4:** Commit: `docs(schema): document ingestion_jobs + ingestion-uploads bucket`.

### Task 16: Decision ledger + CLAUDE.md

**Files:**
- Modify: `docs/decisions/decision-ledger.md`
- Modify: `CLAUDE.md`

- [ ] **Step 1:** Add ledger entries:
  - **AI: AssemblyAI Universal-2 as Phase 3 transcription provider** (context: SG agents need diarization for viewings; alternatives considered; PDPA stance)
  - **OPS: FastAPI BackgroundTasks for async ingestion (deferred Arq+Redis to scale signal)** — rationale: in-process is sufficient for single-Render-instance + 1-3 agents; the queue table is the durability layer (state survives worker restart even if the BackgroundTask itself dies — operator can manually re-trigger via a `/uploads/{id}/retry` endpoint added in Plan 3.5 if needed)
- [ ] **Step 2:** Update CLAUDE.md Status block to Plan 3 complete; flip Next pointer to Plan 4 (WhatsApp ingestion).
- [ ] **Step 3:** Commit: `docs: decision ledger + CLAUDE.md for Plan 3 completion`.

### Task 17: Full local CI sweep + push + PR

**Files:** none (verification only)

- [ ] **Step 1:** `cd backend && source .venv/bin/activate && ruff check . && mypy app && pytest`. Fix anything red.
- [ ] **Step 2:** `cd web && npm test && npx tsc --noEmit && npm run build`. Fix anything red.
- [ ] **Step 3:** Push branch.
- [ ] **Step 4:** `gh pr create` against main with body summarizing what landed + test plan (upload sample transcript locally; verify facts appear).
- [ ] **Step 5:** Wait for CI; merge when both green.
- [ ] **Step 6:** Tag `v0.3.0` on the resulting main HEAD; push tag.
- [ ] **Step 7:** Update CHANGELOG with v0.3.0 entry.

---

## Risks & Mitigations

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| AssemblyAI cold-call returns weak Mandarin/Singlish quality | Med | Task 1 research; fallback path documented in pre-flight |
| BackgroundTask dies mid-extraction on Render restart | Med | Job state survives (DB row stays at `transcribing` or `extracting`); add a watchdog endpoint in Plan 3.5 to surface stuck jobs and let operator retry |
| Long transcripts (>30k tokens) hit extraction prompt size warnings | Low | Sonnet 4.6 = 200k context; no v1 issue. Add chunked-extraction strategy in Plan 5 if needed |
| Operator picks wrong upload_type (e.g., uploads multi-party recording as 'voice_memo' → no diarization) | Med | UI copy clarifies the choice; diarization can be re-run by editing the job (Plan 3.5 if real users hit it) |
| File upload eats memory on backend (FastAPI loads into RAM) | Low | 100MB cap = safe on Render starter tier. Streaming upload to Supabase Storage is a Plan 5 optimization |
| PDPA exposure for SG client data sent to US-based AssemblyAI | Med | Document in onboarding; add data-processing addendum link; revisit in Plan 4 |

---

## Done Criteria

- Operator can drop a `.txt` transcript on the Upload tab → within 30s see the state card move through Queued → Extracting → Done and the Facts tab shows ≥1 extracted fact.
- Operator can drop a `.m4a` voice memo → within 60s see Queued → Transcribing → Extracting → Done, and the Facts tab shows facts derived from the transcribed audio.
- Multi-party transcript uploaded as `transcript` produces facts that attribute claims to the client when possible (verifiable by inspecting source_spans).
- All backend tests pass; web build + Vitest pass; CI green.
- Plan 2's existing manual-note path is unchanged (regression check via existing E2E).
- `v0.3.0` tagged on `main`; CHANGELOG entry written in plain language.
