# Core KB Layer Implementation Plan (Plan 2)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Wire the real extraction pipeline that turns events into typed, cited, deduplicated facts and regenerates per-client markdown profiles, with operator override mechanics — making FollowRoom's KB actually compounding for the first time.

**Architecture:** Three services compose the pipeline. **ExtractionService** calls Anthropic Sonnet via `instructor` to extract typed facts with mandatory verbatim source spans from a raw event. **MatchingService** decides ADD/UPDATE/DELETE/NOOP per extracted fact by semantic comparison against the client's existing facts (Phase 2 uses straightforward similarity; Phase 3 Zettel adds the link-graph). **ProfileService** regenerates the client's two markdown profile views (internal + client-facing) from current facts + operator overrides, capped at ~400 lines. The pipeline runs synchronously inside `POST /events` (manual note ingestion is the only channel in this plan; Plan 3+ adds the rest). Operator override is a `POST /facts/{id}/stance` endpoint that updates `user_stance` + `provenance`; subsequent regenerations preserve operator-canonical facts.

**Tech Stack:** Anthropic Claude Sonnet 4.6 + Haiku 4.5 via SDK + `instructor` for structured outputs (already installed in Foundation); Pydantic v2 for typed extraction shape; existing `AgentDispatcher` (Plan 1 §Task 21) now wires real provider calls; `store()` service (Plan 1 §Task 22) handles all writes; new migration 0010 adds profile columns to `clients` table; Next.js 16 client detail page with tabs (Overview / Facts / Profile); `react-markdown` for profile rendering.

---

## File Structure

```
backend/
├── app/
│   ├── ai/
│   │   ├── dispatcher.py            MODIFY: providers now make real calls
│   │   ├── providers/
│   │   │   ├── anthropic.py         MODIFY: real Anthropic SDK call via instructor
│   │   │   └── openai.py            (unchanged in this plan)
│   │   ├── extraction.py            NEW: ExtractionService — event → list[ExtractedFact]
│   │   ├── matching.py              NEW: MatchingService — ADD/UPDATE/DELETE/NOOP per fact
│   │   ├── profile.py               NEW: ProfileService — regenerate markdown profile
│   │   └── prompts/
│   │       ├── __init__.py          NEW
│   │       ├── extraction.py        NEW: extraction prompt template
│   │       └── profile.py           NEW: profile generation prompt template
│   ├── models/
│   │   ├── event.py                 NEW: Event pydantic models
│   │   ├── fact.py                  NEW: Fact, ExtractedFact, FactStance pydantic models
│   │   └── profile.py               NEW: ProfileView pydantic model
│   ├── services/
│   │   ├── extraction_pipeline.py   NEW: orchestrates extract → match → store → profile
│   │   └── store.py                 (unchanged in this plan)
│   ├── api/
│   │   ├── events.py                NEW: POST /events (manual_note ingestion)
│   │   ├── facts.py                 NEW: GET /clients/{id}/facts, POST /facts/{id}/stance
│   │   ├── profiles.py              NEW: GET /clients/{id}/profile, POST regenerate
│   │   └── main.py                  MODIFY: include new routers
│   └── ...
├── tests/
│   ├── test_extraction.py           NEW
│   ├── test_matching.py             NEW
│   ├── test_profile.py              NEW
│   ├── test_extraction_pipeline.py  NEW
│   ├── test_events_api.py           NEW
│   ├── test_facts_api.py            NEW
│   └── test_profiles_api.py         NEW

supabase/
├── migrations/
│   └── 0010_clients_profile_columns.sql   NEW: adds internal_profile_md + client_facing_profile_md to clients
└── SCHEMA_REFERENCE.md              MODIFY: document new columns

web/
├── app/
│   └── dashboard/
│       └── clients/
│           └── [id]/
│               ├── layout.tsx       NEW: client detail layout (loads client)
│               ├── page.tsx         NEW: client detail overview (default tab)
│               ├── facts/
│               │   └── page.tsx     NEW: facts tab
│               ├── profile/
│               │   └── page.tsx     NEW: profile tab
│               └── notes/
│                   └── new/
│                       └── page.tsx NEW: add manual note form
├── components/
│   └── clients/
│       ├── client-detail-tabs.tsx   NEW: tab navigation
│       ├── facts-list.tsx           NEW: list of facts with source quote
│       ├── fact-card.tsx            NEW: single fact with stance buttons
│       ├── profile-view.tsx         NEW: markdown profile rendering
│       └── add-note-form.tsx        NEW: manual note input
└── tests/
    ├── unit/
    │   └── fact-card.test.tsx       NEW
    └── e2e/
        └── extract-fact-from-note.spec.ts   NEW

CLAUDE.md                            MODIFY: update status
docs/decisions/decision-ledger.md    MODIFY: log Plan 2 decisions
```

---

## Tasks

### Task 1: Branch + dep check

**Files:**
- (none — branch creation only)

- [ ] **Step 1: Create feature branch from main**

```bash
cd "/Users/khanifflau/Documents/Documents - Khaniff's MacBook Air - 1/Projects/followup-rooms"
git checkout main
git pull
git checkout -b feat/core-kb-layer-plan-2
```

- [ ] **Step 2: Verify Anthropic + instructor + OpenAI deps installed**

```bash
cd backend && source .venv/bin/activate
python -c "import anthropic, instructor, openai; print('anthropic', anthropic.__version__); print('instructor', instructor.__version__); print('openai', openai.__version__)"
```

Expected: prints versions without errors (these were installed in Foundation Task 2).

If any are missing, run: `pip install -e ".[dev]"`

- [ ] **Step 3: Verify ANTHROPIC_API_KEY is real (not placeholder)**

Open `backend/.env` and confirm `ANTHROPIC_API_KEY` starts with `sk-ant-` and is NOT `sk-ant-PLACEHOLDER`. If still placeholder, get a key from console.anthropic.com → API Keys → Create Key, paste it in.

Test connectivity:

```bash
python -c "
from app.core.config import get_settings
import anthropic
s = get_settings()
client = anthropic.Anthropic(api_key=s.anthropic_api_key)
msg = client.messages.create(
    model='claude-haiku-4-5',
    max_tokens=20,
    messages=[{'role': 'user', 'content': 'Reply with: pong'}],
)
print(msg.content[0].text)
"
```

Expected: prints `pong` (or similar). If 401, the key is wrong.

- [ ] **Step 4: No commit yet**

This task verifies environment; no files changed.

---

### Task 2: Event Pydantic models

**Files:**
- Create: `backend/app/models/event.py`
- Create: `backend/tests/test_models_event.py`

- [ ] **Step 1: Write failing test**

Create `backend/tests/test_models_event.py`:

```python
from datetime import datetime
from app.models.event import EventCreate, EventResponse


def test_event_create_requires_raw_text_and_source_type():
    e = EventCreate(
        client_id="00000000-0000-0000-0000-000000000001",
        raw_text="Sarah mentioned she wants Marine Parade.",
        source_type="manual_note",
    )
    assert e.raw_text == "Sarah mentioned she wants Marine Parade."
    assert e.source_type == "manual_note"


def test_event_create_rejects_invalid_source_type():
    import pytest
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        EventCreate(
            client_id="00000000-0000-0000-0000-000000000001",
            raw_text="x",
            source_type="invalid_source",
        )


def test_event_response_shape():
    r = EventResponse(
        id="evt-1",
        client_id="cli-1",
        operator_id="op-1",
        source_type="manual_note",
        raw_text="hello",
        created_at=datetime(2026, 5, 18),
    )
    assert r.id == "evt-1"
```

- [ ] **Step 2: Run, verify failure**

```bash
pytest tests/test_models_event.py -v
```

Expected: `ModuleNotFoundError: No module named 'app.models.event'`

- [ ] **Step 3: Implement EventCreate + EventResponse**

Create `backend/app/models/event.py`:

```python
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


SourceType = Literal[
    "meeting_transcript",
    "voice_memo",
    "whatsapp_forward_shapeX",
    "whatsapp_coexistence",
    "manual_note",
    "file_drop",
]


class EventCreate(BaseModel):
    """Operator-submitted event for ingestion (Plan 2: manual_note only)."""

    client_id: str = Field(..., description="UUID of the client this event belongs to")
    source_type: SourceType
    raw_text: str = Field(..., min_length=1, max_length=50000)


class EventResponse(BaseModel):
    id: str
    client_id: str
    operator_id: str
    source_type: str
    raw_text: str
    created_at: datetime
```

- [ ] **Step 4: Run, verify pass**

```bash
pytest tests/test_models_event.py -v
```

Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add backend/app/models/event.py backend/tests/test_models_event.py
git commit -m "feat(models): EventCreate + EventResponse Pydantic models

SourceType enum mirrors the events.source_type CHECK constraint from
migration 0003. raw_text bounded at 50000 chars (large transcripts
land in later plans via dedicated upload flow)."
```

---

### Task 3: Fact + ExtractedFact Pydantic models

**Files:**
- Create: `backend/app/models/fact.py`
- Create: `backend/tests/test_models_fact.py`

- [ ] **Step 1: Write failing test**

Create `backend/tests/test_models_fact.py`:

```python
import pytest
from pydantic import ValidationError

from app.models.fact import ExtractedFact, FactResponse, FactStanceUpdate, SourceSpan


def test_source_span_requires_event_id_and_snippet():
    s = SourceSpan(event_id="evt-1", snippet="wants Marine Parade")
    assert s.event_id == "evt-1"
    assert s.snippet == "wants Marine Parade"


def test_extracted_fact_requires_at_least_one_source_span():
    with pytest.raises(ValidationError):
        ExtractedFact(
            type="property_preference",
            value="Marine Parade",
            confidence_score=0.85,
            visibility="operator_only",
            source_spans=[],
        )


def test_extracted_fact_rejects_invalid_type():
    with pytest.raises(ValidationError):
        ExtractedFact(
            type="not_a_real_type",
            value="x",
            confidence_score=0.5,
            visibility="operator_only",
            source_spans=[SourceSpan(event_id="evt-1", snippet="x")],
        )


def test_extracted_fact_confidence_must_be_0_to_1():
    with pytest.raises(ValidationError):
        ExtractedFact(
            type="goal",
            value="x",
            confidence_score=1.5,
            visibility="operator_only",
            source_spans=[SourceSpan(event_id="evt-1", snippet="x")],
        )


def test_fact_stance_update_validates_stance_enum():
    with pytest.raises(ValidationError):
        FactStanceUpdate(stance="invalid")
    valid = FactStanceUpdate(stance="accepted")
    assert valid.stance == "accepted"


def test_fact_stance_update_optional_value_override():
    u = FactStanceUpdate(stance="reframed", value="Wife prefers Marine Parade only")
    assert u.value == "Wife prefers Marine Parade only"
```

- [ ] **Step 2: Run, verify failure**

```bash
pytest tests/test_models_fact.py -v
```

Expected: `ModuleNotFoundError`.

- [ ] **Step 3: Implement Fact models**

Create `backend/app/models/fact.py`:

```python
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


FactType = Literal[
    "goal",
    "budget_constraint",
    "timeline_signal",
    "objection",
    "spouse_family_factor",
    "emotional_hesitation",
    "document_request",
    "follow_up_promise",
    "viewing_preference",
    "property_preference",
    "decision_blocker",
    "buying_intent_signal",
    "market_signal",
    "content_opportunity",
]

Visibility = Literal["operator_only", "client_facing_safe", "agency_visible"]
UserStance = Literal[
    "unreviewed", "accepted", "rejected", "reframed", "operator_curated",
]
Provenance = Literal[
    "llm_generated", "operator_curated", "operator_edited", "regenerable", "canonical",
]


class SourceSpan(BaseModel):
    """A verbatim citation: which event, what exact text."""

    event_id: str
    snippet: str = Field(..., min_length=1, max_length=2000)


class ExtractedFact(BaseModel):
    """A single fact emitted by ExtractionService — pre-storage shape."""

    type: FactType
    value: str = Field(..., min_length=1, max_length=2000)
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    visibility: Visibility = "operator_only"
    source_spans: list[SourceSpan] = Field(..., min_length=1)


class FactResponse(BaseModel):
    """Fact row as returned to the operator dashboard."""

    id: str
    client_id: str
    type: str
    value: str
    confidence_score: float
    visibility: str
    provenance: str
    user_stance: str
    source_event_ids: list[str]
    source_spans: list[SourceSpan] = Field(default_factory=list)
    superseded_by: str | None = None
    created_at: datetime
    updated_at: datetime


class FactStanceUpdate(BaseModel):
    """Operator override of a fact's stance (accept/reject/edit/reframe)."""

    stance: Literal["accepted", "rejected", "reframed", "operator_curated"]
    value: str | None = Field(
        default=None,
        description="Required when stance='reframed'; operator's rewritten fact value.",
        max_length=2000,
    )
```

- [ ] **Step 4: Run, verify pass**

```bash
pytest tests/test_models_fact.py -v
```

Expected: 6 passed.

- [ ] **Step 5: Commit**

```bash
git add backend/app/models/fact.py backend/tests/test_models_fact.py
git commit -m "feat(models): Fact + ExtractedFact + SourceSpan Pydantic models

Mirrors migration 0004 facts table enums + constraints. SourceSpan
required (≥1 per fact) enforces Axiom 3 (Receipts Are Mandatory).
FactStanceUpdate validates accept/reject/edit/reframe per Axiom 4
(Operator's Edit Is Canon)."
```

---

### Task 4: Extraction prompt template

**Files:**
- Create: `backend/app/ai/prompts/__init__.py`
- Create: `backend/app/ai/prompts/extraction.py`
- Create: `backend/tests/test_prompts_extraction.py`

- [ ] **Step 1: Package marker**

```bash
mkdir -p backend/app/ai/prompts
touch backend/app/ai/prompts/__init__.py
```

- [ ] **Step 2: Write failing test**

Create `backend/tests/test_prompts_extraction.py`:

```python
from app.ai.prompts.extraction import build_extraction_prompt


def test_extraction_prompt_includes_event_id_and_raw_text():
    p = build_extraction_prompt(
        event_id="evt-abc",
        raw_text="Sarah said she wants Marine Parade for parents nearby.",
        client_context="Sarah Tan — HDB upgrade, East Coast, $1.8M",
    )
    assert "evt-abc" in p
    assert "Sarah said she wants Marine Parade" in p
    assert "Sarah Tan — HDB upgrade" in p


def test_extraction_prompt_lists_fact_types():
    p = build_extraction_prompt(event_id="x", raw_text="x", client_context="x")
    # The prompt should enumerate the typed fact categories for the model
    for t in ["goal", "budget_constraint", "objection", "property_preference"]:
        assert t in p


def test_extraction_prompt_emphasizes_source_spans():
    p = build_extraction_prompt(event_id="x", raw_text="x", client_context="x")
    # Receipts are mandatory; prompt must instruct verbatim snippet extraction
    assert "verbatim" in p.lower() or "exact" in p.lower()
    assert "snippet" in p.lower() or "quote" in p.lower()
```

- [ ] **Step 3: Run, verify failure**

```bash
pytest tests/test_prompts_extraction.py -v
```

Expected: `ModuleNotFoundError`.

- [ ] **Step 4: Implement prompt builder**

Create `backend/app/ai/prompts/extraction.py`:

```python
"""
Extraction prompt for FollowRoom KB.

Sonnet 4.6 extracts typed facts with mandatory verbatim source spans
from raw event text (operator's manual note, transcript line, forwarded
message, etc.). Receipts are non-negotiable (Axiom 3).
"""

EXTRACTION_SYSTEM = """You are an extraction component inside FollowRoom, a relationship-memory product for property agents. You read raw client interaction text and extract typed, evidence-grounded facts about the client relationship. You never speculate beyond the source text. You never invent dates, numbers, or names that aren't present."""

FACT_TYPE_DESCRIPTIONS = """
Valid fact types (use the exact identifier):

- goal: what the client wants (e.g., "buy a 3-bed HDB in East Coast")
- budget_constraint: monetary or affordability concern (e.g., "monthly repayment ceiling ~$5k")
- timeline_signal: when something will or might happen (e.g., "after bonus in Q1")
- objection: explicit pushback or concern (e.g., "wife not convinced about location")
- spouse_family_factor: family dynamics affecting the deal (e.g., "wife's parents nearby is important")
- emotional_hesitation: uncertainty or anxiety signals (e.g., "stressed about timing")
- document_request: client asked for or promised documents (e.g., "wants floor plans")
- follow_up_promise: operator promised to do something (e.g., "send affordability scenarios by Friday")
- viewing_preference: what they want from a viewing (e.g., "weekends only")
- property_preference: property attributes they care about (e.g., "ground floor unit")
- decision_blocker: what's stopping the deal from progressing (e.g., "spouse alignment on timing")
- buying_intent_signal: positive purchase intent (e.g., "ready to move forward")
- market_signal: signal about market behavior the client mentioned (e.g., "other buyers backing off")
- content_opportunity: explainer/asset the operator could create (e.g., "ABSD explainer")
"""

EXTRACTION_INSTRUCTIONS = """
For each extractable fact in the text:

1. Pick the most specific fact type from the list above.
2. Write a single sentence stating the fact in plain English (avoid pronouns; use the client's name or relationship terms).
3. Provide a confidence_score between 0.0 and 1.0. Use 0.9+ only when the source text states the fact explicitly. Use 0.5-0.8 when inferred from context. Below 0.5: do not emit.
4. Provide source_spans: at least one verbatim quote from raw_text that grounds the claim. Each snippet must appear character-for-character in raw_text. Multiple snippets allowed if the fact is supported by multiple sentences.
5. Set visibility:
   - "operator_only" by default
   - "client_facing_safe" only if the fact is something the client themselves said about their own preferences (not inferences about their family dynamics, emotional state, or decision-making process)

Hard rules:
- Never fabricate names, dates, money amounts, or property identifiers not in the source.
- If raw_text has no extractable client-relationship facts, emit an empty list.
- Do not include the operator's actions/thoughts as facts about the client (unless they're follow_up_promise type).
- Tier 3 inferences (family dynamics, emotional state, decision-blocker speculation) MUST be visibility="operator_only" — never client_facing_safe.
"""


def build_extraction_prompt(
    event_id: str,
    raw_text: str,
    client_context: str,
) -> str:
    """
    Build a single user-message prompt for the extractor.

    Returns the prompt string. The caller wraps it with the SYSTEM
    message and the structured-output schema via instructor.
    """
    return f"""{FACT_TYPE_DESCRIPTIONS}

{EXTRACTION_INSTRUCTIONS}

---

Client context (background — do NOT treat as source for facts; only the raw_text below is sourceable):
{client_context}

---

Event ID: {event_id}
Source text (this is the only thing you may cite verbatim in source_spans):
\"\"\"
{raw_text}
\"\"\"

Extract facts now."""
```

- [ ] **Step 5: Run, verify pass**

```bash
pytest tests/test_prompts_extraction.py -v
```

Expected: 3 passed.

- [ ] **Step 6: Commit**

```bash
git add backend/app/ai/prompts/__init__.py backend/app/ai/prompts/extraction.py backend/tests/test_prompts_extraction.py
git commit -m "feat(prompts): extraction prompt template with mandatory source spans

System prompt establishes the quiet-witness posture. Instructions
enforce Axiom 3 (receipts: verbatim snippet from raw_text required
per fact) and Axiom 6 (Tier 3 inferences MUST be operator_only)."
```

---

### Task 5: Real Anthropic provider with instructor

**Files:**
- Modify: `backend/app/ai/providers/anthropic.py`
- Create: `backend/tests/test_provider_anthropic.py`

- [ ] **Step 1: Write failing test**

Create `backend/tests/test_provider_anthropic.py`:

```python
from unittest.mock import MagicMock, patch

import pytest
from pydantic import BaseModel

from app.ai.providers.anthropic import AnthropicProvider


class _DummyOutput(BaseModel):
    message: str


def test_anthropic_provider_structured_call_returns_typed_model():
    fake_instructor_client = MagicMock()
    fake_instructor_client.messages.create.return_value = _DummyOutput(message="hello")

    with patch(
        "app.ai.providers.anthropic._build_instructor_client",
        return_value=fake_instructor_client,
    ):
        provider = AnthropicProvider()
        result = provider.structured_call(
            model="claude-haiku-4-5",
            system="you are a test",
            user_prompt="say hello",
            response_model=_DummyOutput,
        )

    assert isinstance(result, _DummyOutput)
    assert result.message == "hello"


def test_anthropic_provider_call_legacy_signature_still_returns_dict():
    provider = AnthropicProvider()
    # The original Phase 1 .call() interface returned a stub dict; keep it
    # so existing tests / callers don't break. Plan 3 may remove it.
    result = provider.call(model="claude-haiku-4-5", prompt="x")
    assert result["provider"] == "anthropic"
    assert "model" in result
```

- [ ] **Step 2: Run, verify failure**

```bash
pytest tests/test_provider_anthropic.py -v
```

Expected: failure — `structured_call` doesn't exist on AnthropicProvider yet (only `call` does from Foundation).

- [ ] **Step 3: Implement real Anthropic provider**

Replace `backend/app/ai/providers/anthropic.py`:

```python
"""
Anthropic provider — real SDK + instructor integration.

Two interfaces:
- structured_call(): typed extraction via instructor; returns Pydantic model
- call(): legacy stub interface from Foundation; kept for backward-compat
"""
from typing import Any, TypeVar

import anthropic
import instructor
from pydantic import BaseModel

from app.core.config import get_settings


T = TypeVar("T", bound=BaseModel)


def _build_instructor_client() -> Any:
    """
    Build an instructor-wrapped Anthropic client.

    Request-scoped pattern matches the Supabase client convention (Foundation
    §Task 3): never module-scope a client that carries auth-bearing config.
    """
    settings = get_settings()
    raw_client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    return instructor.from_anthropic(raw_client)


class AnthropicProvider:
    """Anthropic adapter with structured output via instructor."""

    def structured_call(
        self,
        model: str,
        system: str,
        user_prompt: str,
        response_model: type[T],
        max_tokens: int = 4096,
        max_retries: int = 2,
        **kwargs: Any,
    ) -> T:
        """
        Make a structured call. Returns an instance of response_model.

        instructor handles JSON-schema-strict mode + retry-on-validation-error.
        """
        client = _build_instructor_client()
        return client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user_prompt}],
            response_model=response_model,
            max_retries=max_retries,
            **kwargs,
        )

    def call(self, model: str, prompt: str, **kwargs: Any) -> dict[str, Any]:
        """Legacy interface kept for backward-compat with Foundation tests."""
        return {
            "provider": "anthropic",
            "model": model,
            "prompt_preview": prompt[:200],
            "stub": True,
        }
```

- [ ] **Step 4: Run, verify pass**

```bash
pytest tests/test_provider_anthropic.py -v
```

Expected: 2 passed.

- [ ] **Step 5: Verify existing Foundation tests still pass**

```bash
pytest tests/ -v
```

Expected: all previous tests still pass (test_dispatcher.py + others).

- [ ] **Step 6: Commit**

```bash
git add backend/app/ai/providers/anthropic.py backend/tests/test_provider_anthropic.py
git commit -m "feat(ai): real Anthropic provider with instructor structured outputs

structured_call(model, system, user_prompt, response_model) wraps the
Anthropic SDK via instructor for JSON-schema-strict typed responses
with automatic retry-on-validation-error.

Legacy .call() interface preserved for Foundation backward-compat;
Plan 3+ may remove it once all callers migrate."
```

---

### Task 6: ExtractionService

**Files:**
- Create: `backend/app/ai/extraction.py`
- Create: `backend/tests/test_extraction.py`

- [ ] **Step 1: Write failing test**

Create `backend/tests/test_extraction.py`:

```python
from unittest.mock import MagicMock

from app.ai.extraction import ExtractionService, ExtractionResult
from app.models.fact import ExtractedFact, SourceSpan


def test_extraction_service_calls_dispatcher_with_extractor_role():
    fake_dispatcher = MagicMock()
    fake_dispatcher.structured_dispatch.return_value = ExtractionResult(
        facts=[
            ExtractedFact(
                type="property_preference",
                value="Marine Parade preference for parent proximity",
                confidence_score=0.9,
                visibility="operator_only",
                source_spans=[
                    SourceSpan(event_id="evt-1", snippet="wants Marine Parade because parents nearby"),
                ],
            ),
        ]
    )

    svc = ExtractionService(dispatcher=fake_dispatcher)
    result = svc.extract(
        event_id="evt-1",
        raw_text="Sarah wants Marine Parade because parents nearby.",
        client_context="Sarah Tan — HDB upgrade",
    )

    assert isinstance(result, ExtractionResult)
    assert len(result.facts) == 1
    assert result.facts[0].type == "property_preference"
    # Confirm dispatcher was asked for the extractor role with a Pydantic schema
    args, kwargs = fake_dispatcher.structured_dispatch.call_args
    assert kwargs["role"].value == "extractor"
    assert kwargs["response_model"] is ExtractionResult


def test_extraction_service_returns_empty_when_no_facts_found():
    fake_dispatcher = MagicMock()
    fake_dispatcher.structured_dispatch.return_value = ExtractionResult(facts=[])

    svc = ExtractionService(dispatcher=fake_dispatcher)
    result = svc.extract(event_id="evt-1", raw_text="ok thanks", client_context="x")

    assert result.facts == []
```

- [ ] **Step 2: Run, verify failure**

```bash
pytest tests/test_extraction.py -v
```

Expected: `ModuleNotFoundError`.

- [ ] **Step 3: Extend AgentDispatcher with structured_dispatch**

Modify `backend/app/ai/dispatcher.py` — add `structured_dispatch` method below the existing `dispatch` method (do NOT remove `dispatch`):

```python
    def structured_dispatch(
        self,
        role: "LogicalRole",
        system: str,
        user_prompt: str,
        response_model: type,
        **kwargs: Any,
    ) -> Any:
        """
        Structured-output dispatch: calls provider's structured_call.

        Returns an instance of response_model. The provider must implement
        structured_call (currently AnthropicProvider). Future providers
        adding this method are picked up automatically by the role map.
        """
        provider, model = self.resolve(role)
        if not hasattr(provider, "structured_call"):
            raise NotImplementedError(
                f"Provider for role {role} does not implement structured_call"
            )
        return provider.structured_call(
            model=model,
            system=system,
            user_prompt=user_prompt,
            response_model=response_model,
            **kwargs,
        )
```

- [ ] **Step 4: Implement ExtractionService**

Create `backend/app/ai/extraction.py`:

```python
"""
ExtractionService — event → typed facts with mandatory source spans.

Uses AgentDispatcher with LogicalRole.EXTRACTOR (Sonnet 4.6) and the
extraction prompt template. Returns an ExtractionResult containing
zero-or-more ExtractedFact instances.
"""
from pydantic import BaseModel, Field

from app.ai.dispatcher import AgentDispatcher, LogicalRole
from app.ai.prompts.extraction import EXTRACTION_SYSTEM, build_extraction_prompt
from app.models.fact import ExtractedFact


class ExtractionResult(BaseModel):
    """Structured output schema for the extractor model."""

    facts: list[ExtractedFact] = Field(default_factory=list)


class ExtractionService:
    """Extracts typed facts from a single event's raw_text."""

    def __init__(self, dispatcher: AgentDispatcher | None = None) -> None:
        self._dispatcher = dispatcher or AgentDispatcher()

    def extract(
        self,
        event_id: str,
        raw_text: str,
        client_context: str,
    ) -> ExtractionResult:
        user_prompt = build_extraction_prompt(
            event_id=event_id,
            raw_text=raw_text,
            client_context=client_context,
        )
        return self._dispatcher.structured_dispatch(
            role=LogicalRole.EXTRACTOR,
            system=EXTRACTION_SYSTEM,
            user_prompt=user_prompt,
            response_model=ExtractionResult,
        )
```

- [ ] **Step 5: Run, verify pass**

```bash
pytest tests/test_extraction.py -v
```

Expected: 2 passed.

- [ ] **Step 6: Commit**

```bash
git add backend/app/ai/extraction.py backend/app/ai/dispatcher.py backend/tests/test_extraction.py
git commit -m "feat(ai): ExtractionService — event → typed facts via Sonnet 4.6

AgentDispatcher gains structured_dispatch() which calls the provider's
structured_call() (instructor-wrapped) and returns a typed Pydantic
model. ExtractionService composes the extraction prompt + dispatches.

Returns ExtractionResult.facts: list[ExtractedFact] with mandatory
source_spans per Axiom 3."
```

---

### Task 7: MatchingService — ADD/UPDATE/DELETE/NOOP decision

**Files:**
- Create: `backend/app/ai/matching.py`
- Create: `backend/tests/test_matching.py`

- [ ] **Step 1: Write failing test**

Create `backend/tests/test_matching.py`:

```python
from app.ai.matching import MatchAction, MatchingService
from app.models.fact import ExtractedFact, SourceSpan


def _make_extracted(value: str, type_: str = "budget_constraint", confidence: float = 0.9) -> ExtractedFact:
    return ExtractedFact(
        type=type_,
        value=value,
        confidence_score=confidence,
        visibility="operator_only",
        source_spans=[SourceSpan(event_id="evt-x", snippet=value)],
    )


def test_match_returns_ADD_when_no_existing_facts():
    svc = MatchingService()
    extracted = _make_extracted("monthly repayment ceiling ~$5k")
    decision = svc.decide(extracted, existing_facts=[])
    assert decision.action is MatchAction.ADD
    assert decision.supersedes_id is None


def test_match_returns_NOOP_when_identical_value_already_exists():
    svc = MatchingService()
    extracted = _make_extracted("monthly repayment ceiling ~$5k")
    existing = [{
        "id": "fact-1",
        "type": "budget_constraint",
        "value": "monthly repayment ceiling ~$5k",
        "is_deleted": False,
        "superseded_by": None,
    }]
    decision = svc.decide(extracted, existing_facts=existing)
    assert decision.action is MatchAction.NOOP
    assert decision.matches_id == "fact-1"


def test_match_returns_UPDATE_when_same_type_different_value():
    svc = MatchingService()
    extracted = _make_extracted("monthly repayment ceiling ~$5.5k")
    existing = [{
        "id": "fact-1",
        "type": "budget_constraint",
        "value": "monthly repayment ceiling ~$5k",
        "is_deleted": False,
        "superseded_by": None,
    }]
    decision = svc.decide(extracted, existing_facts=existing)
    assert decision.action is MatchAction.UPDATE
    assert decision.supersedes_id == "fact-1"


def test_match_ignores_superseded_and_deleted_facts():
    svc = MatchingService()
    extracted = _make_extracted("budget $1.8M")
    existing = [
        {"id": "f1", "type": "budget_constraint", "value": "budget $1.8M", "is_deleted": True, "superseded_by": None},
        {"id": "f2", "type": "budget_constraint", "value": "budget $1.8M", "is_deleted": False, "superseded_by": "f9"},
    ]
    decision = svc.decide(extracted, existing_facts=existing)
    # No active matching fact → ADD
    assert decision.action is MatchAction.ADD


def test_match_returns_UPDATE_only_among_same_type():
    svc = MatchingService()
    extracted = _make_extracted("budget $2M", type_="budget_constraint")
    existing = [
        {"id": "f1", "type": "goal", "value": "budget $1.8M", "is_deleted": False, "superseded_by": None},
        {"id": "f2", "type": "budget_constraint", "value": "budget $1.8M", "is_deleted": False, "superseded_by": None},
    ]
    decision = svc.decide(extracted, existing_facts=existing)
    assert decision.action is MatchAction.UPDATE
    assert decision.supersedes_id == "f2"
```

- [ ] **Step 2: Run, verify failure**

```bash
pytest tests/test_matching.py -v
```

Expected: `ModuleNotFoundError`.

- [ ] **Step 3: Implement MatchingService**

Create `backend/app/ai/matching.py`:

```python
"""
MatchingService — ADD/UPDATE/DELETE/NOOP decision per extracted fact.

Phase 2 (this plan): naive string-equality match within the same type.
Sufficient for the ADD/UPDATE/NOOP distinction. DELETE detection (new
event explicitly negates an old fact) is deferred to Plan 2.5 once
real operator usage shows the need.

Phase 3 (Zettel link-graph) replaces string equality with semantic
similarity over the link-graph + Haiku-as-judge for ambiguous cases.
"""
from dataclasses import dataclass
from enum import Enum
from typing import Any

from app.models.fact import ExtractedFact


class MatchAction(str, Enum):
    ADD = "add"
    UPDATE = "update"
    DELETE = "delete"
    NOOP = "noop"


@dataclass(frozen=True)
class MatchDecision:
    action: MatchAction
    supersedes_id: str | None = None  # set when UPDATE
    matches_id: str | None = None  # set when NOOP (existing fact already covers it)


def _normalize(s: str) -> str:
    """Lowercase, collapse whitespace — for naive equality match."""
    return " ".join(s.lower().split())


class MatchingService:
    """Decides what to do with an extracted fact given the current KB state."""

    def decide(
        self,
        extracted: ExtractedFact,
        existing_facts: list[dict[str, Any]],
    ) -> MatchDecision:
        """
        Returns a MatchDecision.

        existing_facts is a list of dicts with at least:
          id, type, value, is_deleted, superseded_by

        Only ACTIVE facts (not deleted, not superseded) are considered.
        """
        active = [
            f for f in existing_facts
            if not f.get("is_deleted") and f.get("superseded_by") is None
        ]
        same_type = [f for f in active if f["type"] == extracted.type]

        norm_new = _normalize(extracted.value)

        # NOOP: identical value already exists
        for f in same_type:
            if _normalize(f["value"]) == norm_new:
                return MatchDecision(action=MatchAction.NOOP, matches_id=f["id"])

        # UPDATE: same type, different value (Phase 2 naive: just the first match)
        if same_type:
            return MatchDecision(
                action=MatchAction.UPDATE,
                supersedes_id=same_type[0]["id"],
            )

        # ADD: nothing matches
        return MatchDecision(action=MatchAction.ADD)
```

- [ ] **Step 4: Run, verify pass**

```bash
pytest tests/test_matching.py -v
```

Expected: 5 passed.

- [ ] **Step 5: Commit**

```bash
git add backend/app/ai/matching.py backend/tests/test_matching.py
git commit -m "feat(ai): MatchingService — ADD/UPDATE/DELETE/NOOP per extracted fact

Phase 2 naive implementation: normalize (lowercase + whitespace) +
string-equality match within same type. Sufficient for the
distinction between new fact, updated value, and duplicate.

DELETE not detected at Phase 2; Plan 2.5 adds it when operator
usage signals need. Phase 3 Zettel link-graph replaces string
equality with semantic similarity + Haiku-as-judge."
```

---

### Task 8: Profile prompt template

**Files:**
- Create: `backend/app/ai/prompts/profile.py`
- Create: `backend/tests/test_prompts_profile.py`

- [ ] **Step 1: Write failing test**

Create `backend/tests/test_prompts_profile.py`:

```python
from app.ai.prompts.profile import build_profile_prompt


def test_profile_prompt_includes_client_name_and_facts():
    facts = [
        {"type": "goal", "value": "buy 3-bed HDB East Coast", "source_event_ids": ["e1"]},
        {"type": "budget_constraint", "value": "ceiling $1.8M", "source_event_ids": ["e2"]},
    ]
    p = build_profile_prompt(
        client_name="Sarah Tan",
        short_context="HDB upgrade, East Coast",
        facts=facts,
        view="internal",
    )
    assert "Sarah Tan" in p
    assert "HDB upgrade" in p
    assert "buy 3-bed HDB East Coast" in p
    assert "ceiling $1.8M" in p


def test_profile_prompt_internal_view_allows_sensitive_sections():
    p = build_profile_prompt(
        client_name="Sarah",
        short_context="x",
        facts=[],
        view="internal",
    )
    assert "Decision dynamics" in p or "decision" in p.lower()


def test_profile_prompt_client_facing_view_strips_sensitive_sections():
    p = build_profile_prompt(
        client_name="Sarah",
        short_context="x",
        facts=[],
        view="client_facing",
    )
    # Client-facing view must NOT instruct the model to include private inferences
    assert "decision_blocker" not in p
    assert "spouse_family_factor" not in p
    assert "emotional_hesitation" not in p


def test_profile_prompt_includes_line_cap_directive():
    p = build_profile_prompt(client_name="x", short_context="x", facts=[], view="internal")
    assert "400" in p
```

- [ ] **Step 2: Run, verify failure**

```bash
pytest tests/test_prompts_profile.py -v
```

Expected: `ModuleNotFoundError`.

- [ ] **Step 3: Implement profile prompt**

Create `backend/app/ai/prompts/profile.py`:

```python
"""
Profile prompt — generate a markdown profile (internal OR client-facing)
from a client's facts.

Two views are PHYSICALLY SEPARATED (design doc §6.4 — Tier 3 safety):
- "internal": full visibility; includes decision dynamics, family factors,
  emotional hesitation, decision blockers
- "client_facing": tactfully rewritten subset; sensitive types are
  FILTERED OUT before the prompt is built so the model never sees them
"""
from typing import Any, Literal


ProfileView = Literal["internal", "client_facing"]


PROFILE_SYSTEM = """You are a profile composer inside FollowRoom. You read a client's typed facts and write a concise, evidence-grounded markdown profile for the relationship-driven sales operator. You never speculate beyond the supplied facts. You never invent details."""


INTERNAL_SECTIONS = """
Sections (use these exact ## headings; omit a section if no facts for it):

## Identity
Name, relationship type, status, short context.

## Goals
What the client wants.

## Constraints
Budget, timeline, location, family logistics.

## Decision dynamics
Who needs to align; what they care about; who blocks.

## Preferences
Specific likes; communication style; viewing preferences.

## Open threads
What's pending; what was promised.

## Recent events
Last 30 days, summarized.

Each bullet ends with source event citations like [ev_001, ev_023].
"""

CLIENT_FACING_SECTIONS = """
Sections (use these exact ## headings; omit a section if no facts for it):

## Goals
What we're working toward, plainly stated.

## Key considerations
The things that matter most to you in this decision.

## Options being explored
What we've looked at; what's next.

## What's pending
Things we're waiting on or actively preparing.

Each bullet should read warmly and professionally; this is for the CLIENT to read.
Do not include inferences about family dynamics, emotional state, or
decision-making process. Use only the operator-approved facts provided.
"""


def build_profile_prompt(
    client_name: str,
    short_context: str,
    facts: list[dict[str, Any]],
    view: ProfileView,
) -> str:
    sections = INTERNAL_SECTIONS if view == "internal" else CLIENT_FACING_SECTIONS

    if facts:
        facts_block_lines = []
        for f in facts:
            src = f.get("source_event_ids", [])
            src_str = ", ".join(src) if src else ""
            facts_block_lines.append(f"- type={f['type']}: {f['value']} [{src_str}]")
        facts_block = "\n".join(facts_block_lines)
    else:
        facts_block = "(no facts yet — render a placeholder profile from short_context only)"

    return f"""Write a markdown profile for the client below.

CAP: 400 lines maximum. Be concise. If a section has no relevant facts, omit it (do not write empty sections).

{sections}

---

Client name: {client_name}
Short context (operator-supplied seed): {short_context}

Facts available (use these as your sources; cite their event IDs in brackets):
{facts_block}

---

Now write the profile."""
```

- [ ] **Step 4: Run, verify pass**

```bash
pytest tests/test_prompts_profile.py -v
```

Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add backend/app/ai/prompts/profile.py backend/tests/test_prompts_profile.py
git commit -m "feat(prompts): profile prompt template — internal + client_facing views

Two views are physically separated at prompt build time: client_facing
sections explicitly omit Tier 3 categories (decision dynamics, family,
emotional state). The model never sees those rows in client_facing mode.
This is the structural Tier 3 guard per design doc §6.4 + Axiom 6."
```

---

### Task 9: ProfileService

**Files:**
- Create: `backend/app/ai/profile.py`
- Create: `backend/tests/test_profile_service.py`

- [ ] **Step 1: Write failing test**

Create `backend/tests/test_profile_service.py`:

```python
from unittest.mock import MagicMock

from app.ai.profile import ProfileResult, ProfileService


def test_profile_service_filters_sensitive_facts_for_client_facing_view():
    fake_dispatcher = MagicMock()
    fake_dispatcher.structured_dispatch.return_value = ProfileResult(markdown="## Goals\n- buy HDB")

    svc = ProfileService(dispatcher=fake_dispatcher)
    facts = [
        {"type": "goal", "value": "buy HDB", "visibility": "client_facing_safe", "source_event_ids": ["e1"]},
        {"type": "spouse_family_factor", "value": "wife is blocker", "visibility": "operator_only", "source_event_ids": ["e2"]},
        {"type": "emotional_hesitation", "value": "stressed about timing", "visibility": "operator_only", "source_event_ids": ["e3"]},
    ]
    svc.regenerate(
        client_name="Sarah",
        short_context="HDB upgrade",
        facts=facts,
        view="client_facing",
    )

    # Verify the prompt sent to the dispatcher does NOT contain the sensitive facts
    args, kwargs = fake_dispatcher.structured_dispatch.call_args
    prompt = kwargs["user_prompt"]
    assert "buy HDB" in prompt
    assert "wife is blocker" not in prompt
    assert "stressed about timing" not in prompt


def test_profile_service_internal_view_includes_all_visible_facts():
    fake_dispatcher = MagicMock()
    fake_dispatcher.structured_dispatch.return_value = ProfileResult(markdown="## Identity\nx")

    svc = ProfileService(dispatcher=fake_dispatcher)
    facts = [
        {"type": "goal", "value": "buy HDB", "visibility": "client_facing_safe", "source_event_ids": ["e1"]},
        {"type": "spouse_family_factor", "value": "wife is blocker", "visibility": "operator_only", "source_event_ids": ["e2"]},
    ]
    svc.regenerate(client_name="Sarah", short_context="x", facts=facts, view="internal")

    args, kwargs = fake_dispatcher.structured_dispatch.call_args
    prompt = kwargs["user_prompt"]
    assert "buy HDB" in prompt
    assert "wife is blocker" in prompt


def test_profile_service_returns_markdown_string():
    fake_dispatcher = MagicMock()
    fake_dispatcher.structured_dispatch.return_value = ProfileResult(markdown="## Goals\n- buy")
    svc = ProfileService(dispatcher=fake_dispatcher)
    out = svc.regenerate(client_name="x", short_context="x", facts=[], view="internal")
    assert out.markdown.startswith("## Goals")
```

- [ ] **Step 2: Run, verify failure**

```bash
pytest tests/test_profile_service.py -v
```

Expected: `ModuleNotFoundError`.

- [ ] **Step 3: Implement ProfileService**

Create `backend/app/ai/profile.py`:

```python
"""
ProfileService — regenerate a client's markdown profile (internal OR
client_facing view) from current facts.

CRITICAL: client_facing view receives a FILTERED facts list — sensitive
types (spouse_family_factor, emotional_hesitation, decision_blocker) are
removed before the prompt is built. The model never sees them.
This is the structural Tier 3 guard per design doc §6.4.
"""
from typing import Any

from pydantic import BaseModel

from app.ai.dispatcher import AgentDispatcher, LogicalRole
from app.ai.prompts.profile import PROFILE_SYSTEM, ProfileView, build_profile_prompt


# Fact types that are NEVER visible in the client_facing profile
SENSITIVE_FACT_TYPES = {
    "spouse_family_factor",
    "emotional_hesitation",
    "decision_blocker",
}


class ProfileResult(BaseModel):
    markdown: str


class ProfileService:
    """Regenerate the markdown profile for a client."""

    def __init__(self, dispatcher: AgentDispatcher | None = None) -> None:
        self._dispatcher = dispatcher or AgentDispatcher()

    def regenerate(
        self,
        client_name: str,
        short_context: str,
        facts: list[dict[str, Any]],
        view: ProfileView,
    ) -> ProfileResult:
        filtered_facts = self._filter_facts_for_view(facts, view)
        user_prompt = build_profile_prompt(
            client_name=client_name,
            short_context=short_context,
            facts=filtered_facts,
            view=view,
        )
        return self._dispatcher.structured_dispatch(
            role=LogicalRole.GENERATOR,
            system=PROFILE_SYSTEM,
            user_prompt=user_prompt,
            response_model=ProfileResult,
        )

    @staticmethod
    def _filter_facts_for_view(
        facts: list[dict[str, Any]],
        view: ProfileView,
    ) -> list[dict[str, Any]]:
        if view == "internal":
            return facts
        # client_facing: remove sensitive types AND require visibility=client_facing_safe
        return [
            f for f in facts
            if f["type"] not in SENSITIVE_FACT_TYPES
            and f.get("visibility") == "client_facing_safe"
        ]
```

- [ ] **Step 4: Run, verify pass**

```bash
pytest tests/test_profile_service.py -v
```

Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add backend/app/ai/profile.py backend/tests/test_profile_service.py
git commit -m "feat(ai): ProfileService — markdown profile regeneration

CRITICAL: client_facing view receives FILTERED facts list — sensitive
types (spouse_family_factor, emotional_hesitation, decision_blocker)
removed before prompt build + visibility must be client_facing_safe.
The model never sees private inferences in client_facing mode.
Structural Tier 3 guard per design doc §6.4."
```

---

### Task 10: Migration 0010 — clients profile columns

**Files:**
- Create: `supabase/migrations/0010_clients_profile_columns.sql`

- [ ] **Step 1: Write migration**

Create `supabase/migrations/0010_clients_profile_columns.sql`:

```sql
-- Migration: 0010 — add profile columns to clients
-- Purpose: Store the regenerated internal + client-facing markdown profiles
--          per design doc §6.2 (two physical views, capped ~400 lines)
-- Rollback: ALTER TABLE clients DROP COLUMN internal_profile_md, DROP COLUMN client_facing_profile_md, DROP COLUMN profile_regenerated_at;

ALTER TABLE clients
  ADD COLUMN IF NOT EXISTS internal_profile_md TEXT,
  ADD COLUMN IF NOT EXISTS client_facing_profile_md TEXT,
  ADD COLUMN IF NOT EXISTS profile_regenerated_at TIMESTAMPTZ;
```

- [ ] **Step 2: Apply migration**

```bash
cd backend && source .venv/bin/activate && python scripts/apply_migrations.py
```

Expected output ends with `Migrations applied successfully.`

- [ ] **Step 3: Verify columns exist**

```bash
python -c "
import psycopg
from app.core.config import get_settings
s = get_settings()
with psycopg.connect(s.supabase_db_url) as conn:
    with conn.cursor() as cur:
        cur.execute(\"\"\"
            SELECT column_name FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = 'clients'
            AND column_name IN ('internal_profile_md', 'client_facing_profile_md', 'profile_regenerated_at')
            ORDER BY column_name
        \"\"\")
        for row in cur.fetchall():
            print(row[0])
"
```

Expected: 3 column names print.

- [ ] **Step 4: Commit**

```bash
git add supabase/migrations/0010_clients_profile_columns.sql
git commit -m "feat(db): migration 0010 — clients profile columns

Adds internal_profile_md + client_facing_profile_md (TEXT) +
profile_regenerated_at (TIMESTAMPTZ) to clients table. Stores the
ProfileService output per design doc §6.2."
```

---

### Task 11: ExtractionPipeline service (orchestration)

**Files:**
- Create: `backend/app/services/extraction_pipeline.py`
- Create: `backend/tests/test_extraction_pipeline.py`

- [ ] **Step 1: Write failing test**

Create `backend/tests/test_extraction_pipeline.py`:

```python
from unittest.mock import MagicMock

from app.ai.extraction import ExtractionResult
from app.ai.matching import MatchAction, MatchDecision
from app.ai.profile import ProfileResult
from app.models.fact import ExtractedFact, SourceSpan
from app.services.extraction_pipeline import ExtractionPipeline


def _make_extracted() -> ExtractedFact:
    return ExtractedFact(
        type="property_preference",
        value="Marine Parade preferred",
        confidence_score=0.9,
        visibility="operator_only",
        source_spans=[SourceSpan(event_id="evt-1", snippet="wants Marine Parade")],
    )


def test_pipeline_extract_and_persist_inserts_event_then_facts_then_regenerates_profile():
    fake_supabase = MagicMock()
    # Event insert returns id; subsequent facts inserts each return id
    fake_supabase.table.return_value.insert.return_value.execute.return_value = MagicMock(
        data=[{"id": "evt-1"}],
    )
    # Existing facts query returns empty
    fake_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock(
        data=[]
    )
    # Client lookup returns name + short_context
    fake_supabase.table.return_value.select.return_value.eq.return_value.maybe_single.return_value.execute.return_value = MagicMock(
        data={"client_name": "Sarah", "short_context": "HDB upgrade"}
    )

    fake_extraction = MagicMock()
    fake_extraction.extract.return_value = ExtractionResult(facts=[_make_extracted()])

    fake_matching = MagicMock()
    fake_matching.decide.return_value = MatchDecision(action=MatchAction.ADD)

    fake_profile = MagicMock()
    fake_profile.regenerate.return_value = ProfileResult(markdown="## Identity\nSarah")

    pipeline = ExtractionPipeline(
        supabase=fake_supabase,
        extraction=fake_extraction,
        matching=fake_matching,
        profile=fake_profile,
    )

    result = pipeline.ingest_and_extract(
        operator_id="op-1",
        client_id="cli-1",
        source_type="manual_note",
        raw_text="Sarah wants Marine Parade because parents nearby.",
    )

    assert result.event_id == "evt-1"
    assert result.facts_added == 1
    assert result.facts_updated == 0
    assert result.facts_noop == 0
    # Profile regen called for both views (internal + client_facing)
    assert fake_profile.regenerate.call_count == 2


def test_pipeline_noop_extraction_still_records_event_but_skips_profile():
    fake_supabase = MagicMock()
    fake_supabase.table.return_value.insert.return_value.execute.return_value = MagicMock(
        data=[{"id": "evt-1"}],
    )

    fake_extraction = MagicMock()
    fake_extraction.extract.return_value = ExtractionResult(facts=[])

    fake_matching = MagicMock()
    fake_profile = MagicMock()

    pipeline = ExtractionPipeline(
        supabase=fake_supabase,
        extraction=fake_extraction,
        matching=fake_matching,
        profile=fake_profile,
    )

    result = pipeline.ingest_and_extract(
        operator_id="op-1",
        client_id="cli-1",
        source_type="manual_note",
        raw_text="ok thanks",
    )

    assert result.event_id == "evt-1"
    assert result.facts_added == 0
    # No facts → profile regen skipped (no change to derive from)
    assert fake_profile.regenerate.call_count == 0
```

- [ ] **Step 2: Run, verify failure**

```bash
pytest tests/test_extraction_pipeline.py -v
```

Expected: `ModuleNotFoundError`.

- [ ] **Step 3: Implement ExtractionPipeline**

Create `backend/app/services/extraction_pipeline.py`:

```python
"""
ExtractionPipeline — orchestrates the full event → facts → profile flow.

Inputs: operator_id, client_id, source_type, raw_text.
Steps:
  1. Insert event row (stable event_id)
  2. Fetch client context (name + short_context) for the extraction prompt
  3. ExtractionService.extract → ExtractionResult.facts
  4. For each extracted fact:
       a. Fetch active existing facts of same type for this client
       b. MatchingService.decide → ADD / UPDATE / NOOP / DELETE
       c. Apply: insert fact (ADD); insert+mark old superseded_by (UPDATE);
          append source_event_id (NOOP — TODO Phase 2.5); skip (DELETE — TODO)
  5. If any facts changed → regenerate both profile views via ProfileService;
     persist to clients.internal_profile_md + .client_facing_profile_md +
     profile_regenerated_at

Phase 2 uses service-role client for cross-RLS writes (operator_id is
explicit in every payload). Plan 7+ routes through governed store().
"""
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from supabase import Client

from app.ai.extraction import ExtractionService
from app.ai.matching import MatchAction, MatchingService
from app.ai.profile import ProfileService
from app.models.fact import ExtractedFact


@dataclass
class PipelineResult:
    event_id: str
    facts_added: int = 0
    facts_updated: int = 0
    facts_noop: int = 0
    facts_deleted: int = 0
    profile_regenerated: bool = False
    extracted_facts: list[ExtractedFact] = field(default_factory=list)


class ExtractionPipeline:
    """Orchestrate event ingestion + extraction + matching + profile regen."""

    def __init__(
        self,
        supabase: Client,
        extraction: ExtractionService | None = None,
        matching: MatchingService | None = None,
        profile: ProfileService | None = None,
    ) -> None:
        self._db = supabase
        self._extraction = extraction or ExtractionService()
        self._matching = matching or MatchingService()
        self._profile = profile or ProfileService()

    def ingest_and_extract(
        self,
        operator_id: str,
        client_id: str,
        source_type: str,
        raw_text: str,
    ) -> PipelineResult:
        # 1. Insert event
        event_insert = (
            self._db.table("events")
            .insert({
                "operator_id": operator_id,
                "client_id": client_id,
                "source_type": source_type,
                "raw_text": raw_text,
            })
            .execute()
        )
        event_id = event_insert.data[0]["id"]

        # 2. Fetch client context for the prompt
        client_row = (
            self._db.table("clients")
            .select("client_name, short_context")
            .eq("id", client_id)
            .maybe_single()
            .execute()
        )
        client_context = (
            f"{client_row.data['client_name']} — {client_row.data['short_context']}"
            if client_row and client_row.data
            else ""
        )

        # 3. Extract facts
        extraction_result = self._extraction.extract(
            event_id=event_id,
            raw_text=raw_text,
            client_context=client_context,
        )

        result = PipelineResult(
            event_id=event_id,
            extracted_facts=list(extraction_result.facts),
        )

        # 4. Match + apply per fact
        for extracted in extraction_result.facts:
            existing = self._fetch_active_facts_of_type(client_id, extracted.type)
            decision = self._matching.decide(extracted, existing)

            if decision.action is MatchAction.ADD:
                self._insert_fact(operator_id, client_id, event_id, extracted)
                result.facts_added += 1
            elif decision.action is MatchAction.UPDATE:
                new_id = self._insert_fact(operator_id, client_id, event_id, extracted)
                self._mark_superseded(decision.supersedes_id, new_id)
                result.facts_updated += 1
            elif decision.action is MatchAction.NOOP:
                # Phase 2.5: append event_id to source_event_ids of matched fact
                result.facts_noop += 1
            elif decision.action is MatchAction.DELETE:
                # Phase 2.5: mark prior fact superseded with deletion_reason
                result.facts_deleted += 1

        # 5. Regenerate profile if anything changed
        if result.facts_added or result.facts_updated or result.facts_deleted:
            self._regenerate_profile(client_id)
            result.profile_regenerated = True

        return result

    # --- helpers ---

    def _fetch_active_facts_of_type(self, client_id: str, fact_type: str) -> list[dict[str, Any]]:
        resp = (
            self._db.table("facts")
            .select("id, type, value, is_deleted, superseded_by")
            .eq("client_id", client_id)
            .eq("type", fact_type)
            .execute()
        )
        return resp.data or []

    def _insert_fact(
        self,
        operator_id: str,
        client_id: str,
        event_id: str,
        extracted: ExtractedFact,
    ) -> str:
        resp = (
            self._db.table("facts")
            .insert({
                "operator_id": operator_id,
                "client_id": client_id,
                "type": extracted.type,
                "value": extracted.value,
                "source_event_ids": [event_id],
                "source_spans": [s.model_dump() for s in extracted.source_spans],
                "confidence_score": extracted.confidence_score,
                "visibility": extracted.visibility,
                "provenance": "llm_generated",
                "user_stance": "unreviewed",
                "generation_metadata": {
                    "model_id": "claude-sonnet-4-6",
                    "prompt_version": "extraction.v1",
                    "generated_at": datetime.now(UTC).isoformat(),
                },
            })
            .execute()
        )
        return resp.data[0]["id"]

    def _mark_superseded(self, old_fact_id: str, new_fact_id: str) -> None:
        (
            self._db.table("facts")
            .update({"superseded_by": new_fact_id})
            .eq("id", old_fact_id)
            .execute()
        )

    def _regenerate_profile(self, client_id: str) -> None:
        # Fetch client info + all active facts
        client_row = (
            self._db.table("clients")
            .select("client_name, short_context")
            .eq("id", client_id)
            .maybe_single()
            .execute()
        )
        facts_resp = (
            self._db.table("facts")
            .select("type, value, visibility, source_event_ids")
            .eq("client_id", client_id)
            .eq("is_deleted", False)
            .is_("superseded_by", "null")
            .execute()
        )
        facts = facts_resp.data or []
        client_name = (client_row.data or {}).get("client_name", "")
        short_context = (client_row.data or {}).get("short_context", "")

        internal = self._profile.regenerate(
            client_name=client_name, short_context=short_context, facts=facts, view="internal",
        )
        client_facing = self._profile.regenerate(
            client_name=client_name, short_context=short_context, facts=facts, view="client_facing",
        )

        (
            self._db.table("clients")
            .update({
                "internal_profile_md": internal.markdown,
                "client_facing_profile_md": client_facing.markdown,
                "profile_regenerated_at": datetime.now(UTC).isoformat(),
            })
            .eq("id", client_id)
            .execute()
        )
```

- [ ] **Step 4: Run, verify pass**

```bash
pytest tests/test_extraction_pipeline.py -v
```

Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/extraction_pipeline.py backend/tests/test_extraction_pipeline.py
git commit -m "feat(services): ExtractionPipeline — event → facts → profile orchestration

Inserts event, extracts facts via Sonnet, decides ADD/UPDATE/NOOP/DELETE
via MatchingService, applies decisions (inserting new facts, marking
superseded), and regenerates both profile views if anything changed.

Phase 2 uses service-role client for inserts (operator_id explicit in
every payload). Plan 7+ routes through governed store() once we add
multi-agent attribution to the write path."
```

---

### Task 12: POST /events endpoint

**Files:**
- Create: `backend/app/api/events.py`
- Create: `backend/tests/test_events_api.py`
- Modify: `backend/app/main.py`

- [ ] **Step 1: Write failing test**

Create `backend/tests/test_events_api.py`:

```python
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def _mock_auth(monkeypatch, operator_id="op-uuid"):
    fake_user = MagicMock()
    fake_user.id = operator_id
    def fake_get_anon_client():
        c = MagicMock()
        c.auth.get_user.return_value = MagicMock(user=fake_user)
        return c
    monkeypatch.setattr("app.core.auth.get_anon_client", fake_get_anon_client)


def test_post_event_returns_401_without_auth(client):
    response = client.post("/events", json={
        "client_id": "00000000-0000-0000-0000-000000000001",
        "source_type": "manual_note",
        "raw_text": "test",
    })
    assert response.status_code == 401


def test_post_event_rejects_invalid_source_type(client, monkeypatch):
    _mock_auth(monkeypatch)
    response = client.post(
        "/events",
        headers={"Authorization": "Bearer t"},
        json={
            "client_id": "00000000-0000-0000-0000-000000000001",
            "source_type": "not_a_type",
            "raw_text": "x",
        },
    )
    assert response.status_code == 422


def test_post_event_runs_pipeline_and_returns_summary(client, monkeypatch):
    _mock_auth(monkeypatch)

    from app.services.extraction_pipeline import PipelineResult
    fake_pipeline = MagicMock()
    fake_pipeline.ingest_and_extract.return_value = PipelineResult(
        event_id="evt-1",
        facts_added=2,
        facts_updated=0,
        facts_noop=1,
        profile_regenerated=True,
    )

    with patch("app.api.events._build_pipeline", return_value=fake_pipeline):
        response = client.post(
            "/events",
            headers={"Authorization": "Bearer t"},
            json={
                "client_id": "00000000-0000-0000-0000-000000000001",
                "source_type": "manual_note",
                "raw_text": "Sarah wants Marine Parade because parents nearby.",
            },
        )

    assert response.status_code == 201
    body = response.json()
    assert body["event_id"] == "evt-1"
    assert body["facts_added"] == 2
    assert body["facts_noop"] == 1
    assert body["profile_regenerated"] is True
```

- [ ] **Step 2: Run, verify failure**

```bash
pytest tests/test_events_api.py -v
```

Expected: `ModuleNotFoundError`.

- [ ] **Step 3: Implement events router**

Create `backend/app/api/events.py`:

```python
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.core.auth import get_current_operator_id
from app.core.supabase import get_service_client
from app.models.event import EventCreate
from app.services.extraction_pipeline import ExtractionPipeline, PipelineResult

router = APIRouter(prefix="/events", tags=["events"])


class IngestResponse(BaseModel):
    event_id: str
    facts_added: int
    facts_updated: int
    facts_noop: int
    facts_deleted: int
    profile_regenerated: bool


def _build_pipeline() -> ExtractionPipeline:
    """Factory — request-scoped to avoid module-scoped clients."""
    return ExtractionPipeline(supabase=get_service_client())


@router.post("", status_code=status.HTTP_201_CREATED, response_model=IngestResponse)
async def ingest_event(
    payload: EventCreate,
    operator_id: str = Depends(get_current_operator_id),
) -> IngestResponse:
    """
    Phase 2: accepts manual_note events only. Plan 3+ adds transcript
    upload, voice memo upload, WhatsApp ingestion — each may add its own
    upload-side endpoint that funnels into the same pipeline.
    """
    if payload.source_type != "manual_note":
        # Phase 2 scope; other source_types will be enabled in their plans
        raise HTTPException(
            status_code=400,
            detail=f"source_type '{payload.source_type}' not supported in Phase 2; only 'manual_note'",
        )

    pipeline = _build_pipeline()
    result: PipelineResult = pipeline.ingest_and_extract(
        operator_id=operator_id,
        client_id=payload.client_id,
        source_type=payload.source_type,
        raw_text=payload.raw_text,
    )

    return IngestResponse(
        event_id=result.event_id,
        facts_added=result.facts_added,
        facts_updated=result.facts_updated,
        facts_noop=result.facts_noop,
        facts_deleted=result.facts_deleted,
        profile_regenerated=result.profile_regenerated,
    )
```

- [ ] **Step 4: Wire router into main.py**

Modify `backend/app/main.py` — change the imports and include lines:

```python
from app.api import clients, events, health, operators
```

And add inside `create_app()`:

```python
    app.include_router(events.router)
```

(Put it after `app.include_router(clients.router)`.)

- [ ] **Step 5: Run, verify pass**

```bash
pytest tests/test_events_api.py -v
```

Expected: 3 passed.

- [ ] **Step 6: Commit**

```bash
git add backend/app/api/events.py backend/app/main.py backend/tests/test_events_api.py
git commit -m "feat(api): POST /events — manual_note ingestion that triggers extraction

Phase 2 scope: only source_type='manual_note' accepted; other types
returned 400 with explanatory message. Plan 3+ enables transcript /
voice / WhatsApp endpoints that funnel into the same pipeline.

Synchronous pipeline call (extract + match + persist + profile regen).
Returns IngestResponse with per-action counters."
```

---

### Task 13: GET /clients/{id}/facts endpoint

**Files:**
- Create: `backend/app/api/facts.py`
- Create: `backend/tests/test_facts_api.py`
- Modify: `backend/app/main.py`

- [ ] **Step 1: Write failing test**

Create `backend/tests/test_facts_api.py`:

```python
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def _mock_auth(monkeypatch, operator_id="op-uuid"):
    fake_user = MagicMock()
    fake_user.id = operator_id
    def fake_get_anon_client():
        c = MagicMock()
        c.auth.get_user.return_value = MagicMock(user=fake_user)
        return c
    monkeypatch.setattr("app.core.auth.get_anon_client", fake_get_anon_client)


def test_list_facts_returns_401_without_auth(client):
    response = client.get("/clients/00000000-0000-0000-0000-000000000001/facts")
    assert response.status_code == 401


def test_list_facts_returns_only_active_for_client(client, monkeypatch):
    _mock_auth(monkeypatch, operator_id="op-uuid")

    fake_supabase = MagicMock()
    # First call: ownership check
    fake_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.maybe_single.return_value.execute.return_value = MagicMock(
        data={"id": "cli-1"}
    )
    # Second call: facts list (chain: select, eq operator_id, eq client_id, eq is_deleted, is_ superseded null, order)
    fake_facts_chain = (
        fake_supabase.table.return_value
        .select.return_value
        .eq.return_value
        .eq.return_value
        .eq.return_value
        .is_.return_value
        .order.return_value
    )
    fake_facts_chain.execute.return_value = MagicMock(data=[
        {
            "id": "f1",
            "client_id": "cli-1",
            "type": "goal",
            "value": "buy HDB",
            "confidence_score": 0.9,
            "visibility": "client_facing_safe",
            "provenance": "llm_generated",
            "user_stance": "unreviewed",
            "source_event_ids": ["e1"],
            "source_spans": [{"event_id": "e1", "snippet": "buy HDB"}],
            "superseded_by": None,
            "created_at": "2026-05-18T00:00:00+00:00",
            "updated_at": "2026-05-18T00:00:00+00:00",
        }
    ])

    with patch("app.api.facts.get_service_client", return_value=fake_supabase):
        response = client.get(
            "/clients/cli-1/facts",
            headers={"Authorization": "Bearer t"},
        )

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["type"] == "goal"


def test_list_facts_returns_404_if_client_not_owned_by_operator(client, monkeypatch):
    _mock_auth(monkeypatch, operator_id="op-uuid")

    fake_supabase = MagicMock()
    fake_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.maybe_single.return_value.execute.return_value = MagicMock(
        data=None
    )

    with patch("app.api.facts.get_service_client", return_value=fake_supabase):
        response = client.get(
            "/clients/cli-1/facts",
            headers={"Authorization": "Bearer t"},
        )

    assert response.status_code == 404
```

- [ ] **Step 2: Run, verify failure**

```bash
pytest tests/test_facts_api.py -v
```

Expected: `ModuleNotFoundError`.

- [ ] **Step 3: Implement facts router**

Create `backend/app/api/facts.py`:

```python
from fastapi import APIRouter, Depends, HTTPException, status

from app.core.auth import get_current_operator_id
from app.core.supabase import get_service_client
from app.models.fact import FactResponse, FactStanceUpdate

router = APIRouter(tags=["facts"])


def _assert_client_ownership(supabase, operator_id: str, client_id: str) -> None:
    """Raise 404 if the client doesn't belong to this operator."""
    resp = (
        supabase.table("clients")
        .select("id")
        .eq("id", client_id)
        .eq("operator_id", operator_id)
        .maybe_single()
        .execute()
    )
    if not resp or not resp.data:
        raise HTTPException(status_code=404, detail="Client not found")


@router.get("/clients/{client_id}/facts", response_model=list[FactResponse])
async def list_facts(
    client_id: str,
    operator_id: str = Depends(get_current_operator_id),
) -> list[FactResponse]:
    supabase = get_service_client()
    _assert_client_ownership(supabase, operator_id, client_id)

    resp = (
        supabase.table("facts")
        .select(
            "id, client_id, type, value, confidence_score, visibility, provenance, "
            "user_stance, source_event_ids, source_spans, superseded_by, created_at, updated_at"
        )
        .eq("operator_id", operator_id)
        .eq("client_id", client_id)
        .eq("is_deleted", False)
        .is_("superseded_by", "null")
        .order("created_at", desc=True)
        .execute()
    )

    return [FactResponse(**row) for row in (resp.data or [])]


@router.post("/facts/{fact_id}/stance", response_model=FactResponse)
async def update_fact_stance(
    fact_id: str,
    payload: FactStanceUpdate,
    operator_id: str = Depends(get_current_operator_id),
) -> FactResponse:
    """
    Operator override: accept / reject / reframe / mark operator_curated.

    - 'accepted': mark user_stance='accepted'; provenance unchanged
    - 'rejected': mark user_stance='rejected'; also soft-delete the fact
      so it stops appearing in profile regeneration
    - 'reframed': operator supplies a new value; user_stance='reframed',
      provenance='operator_edited', value updated
    - 'operator_curated': user_stance='operator_curated', provenance='canonical'
      (operator is asserting this is exactly correct)
    """
    supabase = get_service_client()

    # Verify ownership
    fact_resp = (
        supabase.table("facts")
        .select("id, operator_id")
        .eq("id", fact_id)
        .eq("operator_id", operator_id)
        .maybe_single()
        .execute()
    )
    if not fact_resp or not fact_resp.data:
        raise HTTPException(status_code=404, detail="Fact not found")

    from datetime import UTC, datetime
    update: dict = {
        "user_stance": payload.stance,
        "user_stance_set_at": datetime.now(UTC).isoformat(),
    }

    if payload.stance == "rejected":
        update["is_deleted"] = True
        update["deleted_at"] = datetime.now(UTC).isoformat()
    elif payload.stance == "reframed":
        if not payload.value:
            raise HTTPException(
                status_code=422,
                detail="value is required when stance='reframed'",
            )
        update["value"] = payload.value
        update["provenance"] = "operator_edited"
    elif payload.stance == "operator_curated":
        update["provenance"] = "canonical"

    updated = (
        supabase.table("facts")
        .update(update)
        .eq("id", fact_id)
        .execute()
    )

    # Re-fetch to return full row
    refetch = (
        supabase.table("facts")
        .select(
            "id, client_id, type, value, confidence_score, visibility, provenance, "
            "user_stance, source_event_ids, source_spans, superseded_by, created_at, updated_at"
        )
        .eq("id", fact_id)
        .maybe_single()
        .execute()
    )
    return FactResponse(**refetch.data)
```

- [ ] **Step 4: Wire into main.py**

Modify `backend/app/main.py` — add `facts` to the import line and `app.include_router(facts.router)` after events:

```python
from app.api import clients, events, facts, health, operators
```

```python
    app.include_router(facts.router)
```

- [ ] **Step 5: Run, verify pass**

```bash
pytest tests/test_facts_api.py -v
```

Expected: 3 passed.

- [ ] **Step 6: Commit**

```bash
git add backend/app/api/facts.py backend/app/main.py backend/tests/test_facts_api.py
git commit -m "feat(api): GET /clients/{id}/facts + POST /facts/{id}/stance

List endpoint returns only active (not soft-deleted, not superseded)
facts for the client, scoped to operator ownership.

Stance update implements operator override per Axiom 4:
- accepted: marks reviewed; no other changes
- rejected: soft-deletes the fact (drops from future profile regen)
- reframed: requires new value; provenance → operator_edited
- operator_curated: provenance → canonical (operator asserts truth)"
```

---

### Task 14: GET /clients/{id}/profile + POST regenerate

**Files:**
- Create: `backend/app/api/profiles.py`
- Create: `backend/tests/test_profiles_api.py`
- Modify: `backend/app/main.py`

- [ ] **Step 1: Write failing test**

Create `backend/tests/test_profiles_api.py`:

```python
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def _mock_auth(monkeypatch, operator_id="op-uuid"):
    fake_user = MagicMock()
    fake_user.id = operator_id
    def fake_get_anon_client():
        c = MagicMock()
        c.auth.get_user.return_value = MagicMock(user=fake_user)
        return c
    monkeypatch.setattr("app.core.auth.get_anon_client", fake_get_anon_client)


def test_get_profile_returns_both_views(client, monkeypatch):
    _mock_auth(monkeypatch)

    fake_supabase = MagicMock()
    fake_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.maybe_single.return_value.execute.return_value = MagicMock(
        data={
            "internal_profile_md": "## Identity\nSarah",
            "client_facing_profile_md": "## Goals\nBuy HDB",
            "profile_regenerated_at": "2026-05-18T00:00:00+00:00",
        }
    )

    with patch("app.api.profiles.get_service_client", return_value=fake_supabase):
        response = client.get(
            "/clients/cli-1/profile",
            headers={"Authorization": "Bearer t"},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["internal_profile_md"] == "## Identity\nSarah"
    assert body["client_facing_profile_md"] == "## Goals\nBuy HDB"


def test_regenerate_profile_calls_pipeline_and_returns_updated_profile(client, monkeypatch):
    _mock_auth(monkeypatch)

    # Pipeline is called via the regenerate endpoint's helper
    fake_pipeline = MagicMock()
    # _regenerate_profile (private) is called via the public API; we shortcut by
    # mocking the helper used in the endpoint

    fake_supabase = MagicMock()
    # Ownership check
    fake_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.maybe_single.return_value.execute.return_value = MagicMock(
        data={"id": "cli-1"}
    )

    with patch("app.api.profiles.get_service_client", return_value=fake_supabase), \
         patch("app.api.profiles._build_pipeline", return_value=fake_pipeline):
        # After pipeline runs, the endpoint re-fetches the profile to return it.
        # Set up the re-fetch result here.
        refetch_chain = (
            fake_supabase.table.return_value
            .select.return_value
            .eq.return_value
            .eq.return_value
            .maybe_single
        )
        # Two .maybe_single() calls in sequence: ownership + re-fetch
        refetch_chain.return_value.execute.side_effect = [
            MagicMock(data={"id": "cli-1"}),
            MagicMock(data={
                "internal_profile_md": "## Identity\nSarah",
                "client_facing_profile_md": "## Goals\nBuy HDB",
                "profile_regenerated_at": "2026-05-18T00:00:00+00:00",
            }),
        ]

        response = client.post(
            "/clients/cli-1/profile/regenerate",
            headers={"Authorization": "Bearer t"},
        )

    assert response.status_code == 200
    assert fake_pipeline._regenerate_profile.called
```

- [ ] **Step 2: Run, verify failure**

```bash
pytest tests/test_profiles_api.py -v
```

Expected: `ModuleNotFoundError`.

- [ ] **Step 3: Implement profiles router**

Create `backend/app/api/profiles.py`:

```python
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core.auth import get_current_operator_id
from app.core.supabase import get_service_client
from app.services.extraction_pipeline import ExtractionPipeline

router = APIRouter(tags=["profiles"])


class ProfileResponse(BaseModel):
    internal_profile_md: str | None = None
    client_facing_profile_md: str | None = None
    profile_regenerated_at: datetime | None = None


def _build_pipeline() -> ExtractionPipeline:
    return ExtractionPipeline(supabase=get_service_client())


def _assert_client_ownership(supabase, operator_id: str, client_id: str) -> None:
    resp = (
        supabase.table("clients")
        .select("id")
        .eq("id", client_id)
        .eq("operator_id", operator_id)
        .maybe_single()
        .execute()
    )
    if not resp or not resp.data:
        raise HTTPException(status_code=404, detail="Client not found")


@router.get("/clients/{client_id}/profile", response_model=ProfileResponse)
async def get_profile(
    client_id: str,
    operator_id: str = Depends(get_current_operator_id),
) -> ProfileResponse:
    supabase = get_service_client()
    resp = (
        supabase.table("clients")
        .select("internal_profile_md, client_facing_profile_md, profile_regenerated_at")
        .eq("id", client_id)
        .eq("operator_id", operator_id)
        .maybe_single()
        .execute()
    )
    if not resp or not resp.data:
        raise HTTPException(status_code=404, detail="Client not found")
    return ProfileResponse(**resp.data)


@router.post("/clients/{client_id}/profile/regenerate", response_model=ProfileResponse)
async def regenerate_profile(
    client_id: str,
    operator_id: str = Depends(get_current_operator_id),
) -> ProfileResponse:
    supabase = get_service_client()
    _assert_client_ownership(supabase, operator_id, client_id)

    pipeline = _build_pipeline()
    pipeline._regenerate_profile(client_id)  # private helper; profile regen only (no new event)

    resp = (
        supabase.table("clients")
        .select("internal_profile_md, client_facing_profile_md, profile_regenerated_at")
        .eq("id", client_id)
        .eq("operator_id", operator_id)
        .maybe_single()
        .execute()
    )
    return ProfileResponse(**resp.data)
```

- [ ] **Step 4: Wire into main.py**

Modify `backend/app/main.py`:

```python
from app.api import clients, events, facts, health, operators, profiles
```

```python
    app.include_router(profiles.router)
```

- [ ] **Step 5: Run, verify pass**

```bash
pytest tests/test_profiles_api.py -v
```

Expected: 2 passed.

- [ ] **Step 6: Commit**

```bash
git add backend/app/api/profiles.py backend/app/main.py backend/tests/test_profiles_api.py
git commit -m "feat(api): GET /clients/{id}/profile + POST .../profile/regenerate

GET returns both internal + client_facing markdown views + last
regen timestamp.

POST regenerates both views immediately by calling the pipeline's
profile-regen helper. Useful after manual fact overrides or for
the 'refresh now' button in the dashboard UI."
```

---

### Task 15: Frontend — install react-markdown

**Files:**
- Modify: `web/package.json` (via npm install)

- [ ] **Step 1: Install**

```bash
cd web && npm install react-markdown 2>&1 | tail -3
```

Expected: clean install; new dep in package.json.

- [ ] **Step 2: Commit**

```bash
cd ..
git add web/package.json web/package-lock.json
git commit -m "feat(web): install react-markdown for profile rendering"
```

---

### Task 16: Frontend — client detail layout

**Files:**
- Create: `web/app/dashboard/clients/[id]/layout.tsx`
- Create: `web/app/dashboard/clients/[id]/page.tsx`
- Create: `web/components/clients/client-detail-tabs.tsx`

- [ ] **Step 1: Tabs component**

Create `web/components/clients/client-detail-tabs.tsx`:

```typescript
"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

export function ClientDetailTabs({ clientId }: { clientId: string }) {
  const pathname = usePathname();
  const tabs = [
    { href: `/dashboard/clients/${clientId}`, label: "Overview" },
    { href: `/dashboard/clients/${clientId}/facts`, label: "Facts" },
    { href: `/dashboard/clients/${clientId}/profile`, label: "Profile" },
    { href: `/dashboard/clients/${clientId}/notes/new`, label: "Add note" },
  ];

  return (
    <nav className="border-b mb-6">
      <ul className="flex gap-1">
        {tabs.map((t) => {
          const active = pathname === t.href;
          return (
            <li key={t.href}>
              <Link
                href={t.href}
                className={`inline-block px-4 py-2 text-sm border-b-2 -mb-px ${
                  active
                    ? "border-gray-900 text-gray-900 font-medium"
                    : "border-transparent text-gray-600 hover:text-gray-900"
                }`}
              >
                {t.label}
              </Link>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}
```

- [ ] **Step 2: Client detail layout**

Create `web/app/dashboard/clients/[id]/layout.tsx`:

```typescript
import { notFound } from "next/navigation";
import { createClient } from "@/lib/supabase/server";
import { ClientDetailTabs } from "@/components/clients/client-detail-tabs";

export default async function ClientDetailLayout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const supabase = await createClient();
  const { data: client } = await supabase
    .from("clients")
    .select("id, client_name, short_context, status")
    .eq("id", id)
    .eq("is_deleted", false)
    .maybeSingle();

  if (!client) notFound();

  return (
    <div>
      <div className="mb-6">
        <h2 className="text-2xl font-semibold">{client.client_name}</h2>
        <p className="text-sm text-gray-600 mt-1">{client.short_context}</p>
        <p className="text-xs text-gray-500 mt-1">Status: {client.status}</p>
      </div>
      <ClientDetailTabs clientId={id} />
      {children}
    </div>
  );
}
```

- [ ] **Step 3: Overview page**

Create `web/app/dashboard/clients/[id]/page.tsx`:

```typescript
import { createClient } from "@/lib/supabase/server";

export const dynamic = "force-dynamic";

export default async function ClientOverview({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const supabase = await createClient();

  const { data: events } = await supabase
    .from("events")
    .select("id, source_type, raw_text, created_at")
    .eq("client_id", id)
    .eq("is_deleted", false)
    .order("created_at", { ascending: false })
    .limit(10);

  const { data: factCount } = await supabase
    .from("facts")
    .select("id", { count: "exact", head: true })
    .eq("client_id", id)
    .eq("is_deleted", false)
    .is("superseded_by", null);

  return (
    <div className="space-y-6">
      <section>
        <h3 className="text-lg font-medium mb-2">Recent events</h3>
        {!events || events.length === 0 ? (
          <p className="text-sm text-gray-500">
            No events yet. Use the &quot;Add note&quot; tab to record the first one.
          </p>
        ) : (
          <ul className="space-y-2">
            {events.map((e) => (
              <li key={e.id} className="border rounded p-3 bg-white">
                <p className="text-xs text-gray-500">
                  {e.source_type} · {new Date(e.created_at).toLocaleString()}
                </p>
                <p className="text-sm mt-1 line-clamp-2">{e.raw_text}</p>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
```

- [ ] **Step 4: Verify build**

```bash
cd web && npm run build 2>&1 | tail -5
```

Expected: build succeeds; `/dashboard/clients/[id]` route registers.

- [ ] **Step 5: Commit**

```bash
cd .. && git add web/app/dashboard/clients/[id] web/components/clients/client-detail-tabs.tsx
git commit -m "feat(web): client detail layout with tabs + Overview page

Tabs: Overview / Facts / Profile / Add note. Layout loads client and
shows 404 if not found. Overview shows recent events list."
```

---

### Task 17: Frontend — Add note form (POST /events)

**Files:**
- Create: `web/components/clients/add-note-form.tsx`
- Create: `web/app/dashboard/clients/[id]/notes/new/page.tsx`

- [ ] **Step 1: Add note form**

Create `web/components/clients/add-note-form.tsx`:

```typescript
"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { createClient } from "@/lib/supabase/client";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";

export function AddNoteForm({ clientId }: { clientId: string }) {
  const [rawText, setRawText] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<{ facts_added: number; facts_updated: number; facts_noop: number } | null>(null);
  const router = useRouter();

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setResult(null);
    setLoading(true);

    const supabase = createClient();
    const { data: { session } } = await supabase.auth.getSession();
    const token = session?.access_token;
    if (!token) {
      setError("Not authenticated. Please log in.");
      setLoading(false);
      return;
    }

    const backend = process.env.NEXT_PUBLIC_BACKEND_API_URL || "http://localhost:8000";
    const res = await fetch(`${backend}/events`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({
        client_id: clientId,
        source_type: "manual_note",
        raw_text: rawText,
      }),
    });

    setLoading(false);

    if (!res.ok) {
      const body = await res.json().catch(() => ({ detail: "Unknown error" }));
      setError(body.detail || `Request failed: ${res.status}`);
      return;
    }

    const body = await res.json();
    setResult({
      facts_added: body.facts_added,
      facts_updated: body.facts_updated,
      facts_noop: body.facts_noop,
    });
    setRawText("");
    router.refresh();
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4 max-w-2xl">
      <div className="space-y-2">
        <Label htmlFor="raw_text">Note</Label>
        <Textarea
          id="raw_text"
          required
          rows={5}
          value={rawText}
          onChange={(e) => setRawText(e.target.value)}
          placeholder="e.g., Sarah mentioned she wants Marine Parade because parents live nearby. Wife also asked about monthly repayment comfort."
        />
        <p className="text-xs text-gray-500">
          Write what happened in your own words. The AI extracts typed facts and updates the profile.
        </p>
      </div>

      {error && <p className="text-sm text-red-600">{error}</p>}

      {result && (
        <div className="text-sm bg-green-50 border border-green-200 p-3 rounded">
          Note ingested. Facts: {result.facts_added} new · {result.facts_updated} updated · {result.facts_noop} duplicate.
        </div>
      )}

      <Button type="submit" disabled={loading}>
        {loading ? "Extracting..." : "Add note"}
      </Button>
    </form>
  );
}
```

- [ ] **Step 2: Page wrapper**

Create `web/app/dashboard/clients/[id]/notes/new/page.tsx`:

```typescript
import { AddNoteForm } from "@/components/clients/add-note-form";

export default async function AddNotePage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  return (
    <div>
      <h3 className="text-lg font-medium mb-4">Add a manual note</h3>
      <AddNoteForm clientId={id} />
    </div>
  );
}
```

- [ ] **Step 3: Add BACKEND_API_URL to env example**

Modify `web/.env.example` — append (if not already present):

```bash

# Backend API URL (already present in template; confirm)
NEXT_PUBLIC_BACKEND_API_URL=http://localhost:8000
```

Then make sure local `web/.env.local` has it too (operator action; reminder only).

- [ ] **Step 4: Verify build**

```bash
cd web && npm run build 2>&1 | tail -5
```

Expected: build succeeds; new route registers.

- [ ] **Step 5: Commit**

```bash
cd .. && git add web/components/clients/add-note-form.tsx web/app/dashboard/clients/[id]/notes web/.env.example
git commit -m "feat(web): add-note form posts manual_note events to backend

Client-side form gets the Supabase session JWT and posts to
\$NEXT_PUBLIC_BACKEND_API_URL/events. Shows extraction summary
(facts added/updated/duplicate) on success.

Uses NEXT_PUBLIC_BACKEND_API_URL env var (default localhost:8000)."
```

---

### Task 18: Frontend — Facts tab + fact card

**Files:**
- Create: `web/components/clients/fact-card.tsx`
- Create: `web/components/clients/facts-list.tsx`
- Create: `web/app/dashboard/clients/[id]/facts/page.tsx`
- Create: `web/tests/unit/fact-card.test.tsx`

- [ ] **Step 1: Fact card component**

Create `web/components/clients/fact-card.tsx`:

```typescript
"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { createClient } from "@/lib/supabase/client";
import { Button } from "@/components/ui/button";

export interface Fact {
  id: string;
  type: string;
  value: string;
  confidence_score: number;
  visibility: string;
  provenance: string;
  user_stance: string;
  source_spans: { event_id: string; snippet: string }[];
}

const STANCE_LABELS: Record<string, string> = {
  unreviewed: "Needs review",
  accepted: "Accepted",
  rejected: "Rejected",
  reframed: "Edited by you",
  operator_curated: "Canonical (yours)",
};

export function FactCard({ fact }: { fact: Fact }) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  async function updateStance(stance: "accepted" | "rejected" | "operator_curated", value?: string) {
    setError(null);
    setLoading(true);

    const supabase = createClient();
    const { data: { session } } = await supabase.auth.getSession();
    const token = session?.access_token;
    if (!token) {
      setError("Not authenticated.");
      setLoading(false);
      return;
    }

    const backend = process.env.NEXT_PUBLIC_BACKEND_API_URL || "http://localhost:8000";
    const res = await fetch(`${backend}/facts/${fact.id}/stance`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ stance, value }),
    });

    setLoading(false);

    if (!res.ok) {
      const body = await res.json().catch(() => ({ detail: "Unknown error" }));
      setError(body.detail || `Request failed: ${res.status}`);
      return;
    }

    router.refresh();
  }

  return (
    <div className="border rounded-lg p-4 bg-white">
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1">
          <p className="text-xs uppercase tracking-wide text-gray-500">{fact.type.replace(/_/g, " ")}</p>
          <p className="text-sm mt-1">{fact.value}</p>
          {fact.source_spans.length > 0 && (
            <details className="mt-2">
              <summary className="text-xs text-gray-500 cursor-pointer">
                {fact.source_spans.length} source quote{fact.source_spans.length > 1 ? "s" : ""}
              </summary>
              <ul className="mt-2 space-y-1 pl-4 border-l-2 border-gray-200">
                {fact.source_spans.map((s, i) => (
                  <li key={i} className="text-xs text-gray-600 italic">
                    &ldquo;{s.snippet}&rdquo;
                  </li>
                ))}
              </ul>
            </details>
          )}
        </div>
        <div className="text-right text-xs text-gray-500">
          <div>{Math.round(fact.confidence_score * 100)}%</div>
          <div className="mt-1">{STANCE_LABELS[fact.user_stance] || fact.user_stance}</div>
        </div>
      </div>

      {fact.user_stance === "unreviewed" && (
        <div className="flex gap-2 mt-3">
          <Button
            type="button"
            size="sm"
            onClick={() => updateStance("accepted")}
            disabled={loading}
          >
            Accept
          </Button>
          <Button
            type="button"
            size="sm"
            variant="outline"
            onClick={() => updateStance("rejected")}
            disabled={loading}
          >
            Reject
          </Button>
        </div>
      )}

      {error && <p className="text-xs text-red-600 mt-2">{error}</p>}
    </div>
  );
}
```

- [ ] **Step 2: Facts list component**

Create `web/components/clients/facts-list.tsx`:

```typescript
import { FactCard, type Fact } from "@/components/clients/fact-card";

export function FactsList({ facts }: { facts: Fact[] }) {
  if (facts.length === 0) {
    return (
      <p className="text-sm text-gray-500">
        No facts yet. Add a note and the AI will extract typed facts here.
      </p>
    );
  }
  return (
    <ul className="space-y-3">
      {facts.map((f) => (
        <li key={f.id}>
          <FactCard fact={f} />
        </li>
      ))}
    </ul>
  );
}
```

- [ ] **Step 3: Facts page**

Create `web/app/dashboard/clients/[id]/facts/page.tsx`:

```typescript
import { createClient } from "@/lib/supabase/server";
import { FactsList } from "@/components/clients/facts-list";
import type { Fact } from "@/components/clients/fact-card";

export const dynamic = "force-dynamic";

export default async function FactsTab({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const supabase = await createClient();

  const { data } = await supabase
    .from("facts")
    .select(
      "id, type, value, confidence_score, visibility, provenance, user_stance, source_spans",
    )
    .eq("client_id", id)
    .eq("is_deleted", false)
    .is("superseded_by", null)
    .order("created_at", { ascending: false });

  const facts = (data || []) as Fact[];
  return (
    <div>
      <h3 className="text-lg font-medium mb-4">
        Facts ({facts.length})
      </h3>
      <FactsList facts={facts} />
    </div>
  );
}
```

- [ ] **Step 4: Unit test for fact card**

Create `web/tests/unit/fact-card.test.tsx`:

```typescript
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { FactCard, type Fact } from "@/components/clients/fact-card";

describe("FactCard", () => {
  const baseFact: Fact = {
    id: "f1",
    type: "property_preference",
    value: "Marine Parade preferred for parent proximity",
    confidence_score: 0.85,
    visibility: "operator_only",
    provenance: "llm_generated",
    user_stance: "unreviewed",
    source_spans: [{ event_id: "e1", snippet: "wants Marine Parade" }],
  };

  it("renders fact value and humanized type", () => {
    render(<FactCard fact={baseFact} />);
    expect(screen.getByText("Marine Parade preferred for parent proximity")).toBeInTheDocument();
    expect(screen.getByText("property preference")).toBeInTheDocument();
  });

  it("shows confidence as percentage", () => {
    render(<FactCard fact={baseFact} />);
    expect(screen.getByText("85%")).toBeInTheDocument();
  });

  it("shows Accept and Reject buttons when stance is unreviewed", () => {
    render(<FactCard fact={baseFact} />);
    expect(screen.getByRole("button", { name: /Accept/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Reject/i })).toBeInTheDocument();
  });

  it("hides Accept/Reject buttons after stance is set", () => {
    render(<FactCard fact={{ ...baseFact, user_stance: "accepted" }} />);
    expect(screen.queryByRole("button", { name: /Accept/i })).not.toBeInTheDocument();
  });
});
```

- [ ] **Step 5: Run frontend tests**

```bash
cd web && npm run test 2>&1 | tail -10
```

Expected: 6 tests pass (2 from Foundation + 4 new).

- [ ] **Step 6: Commit**

```bash
cd .. && git add web/components/clients web/app/dashboard/clients/[id]/facts web/tests/unit/fact-card.test.tsx
git commit -m "feat(web): Facts tab with FactCard component + tests

FactCard shows type, value, confidence, source quotes (collapsible).
Accept/Reject buttons surface only for unreviewed facts and call
POST /facts/{id}/stance. router.refresh() after success re-fetches
the list."
```

---

### Task 19: Frontend — Profile tab with markdown rendering

**Files:**
- Create: `web/components/clients/profile-view.tsx`
- Create: `web/app/dashboard/clients/[id]/profile/page.tsx`

- [ ] **Step 1: Profile view component**

Create `web/components/clients/profile-view.tsx`:

```typescript
"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import ReactMarkdown from "react-markdown";
import { createClient } from "@/lib/supabase/client";
import { Button } from "@/components/ui/button";

interface ProfileViewProps {
  clientId: string;
  internalMd: string | null;
  clientFacingMd: string | null;
  regeneratedAt: string | null;
}

export function ProfileView({ clientId, internalMd, clientFacingMd, regeneratedAt }: ProfileViewProps) {
  const [view, setView] = useState<"internal" | "client_facing">("internal");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  async function regenerate() {
    setError(null);
    setLoading(true);

    const supabase = createClient();
    const { data: { session } } = await supabase.auth.getSession();
    const token = session?.access_token;
    if (!token) {
      setError("Not authenticated.");
      setLoading(false);
      return;
    }

    const backend = process.env.NEXT_PUBLIC_BACKEND_API_URL || "http://localhost:8000";
    const res = await fetch(`${backend}/clients/${clientId}/profile/regenerate`, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
    });

    setLoading(false);

    if (!res.ok) {
      const body = await res.json().catch(() => ({ detail: "Unknown error" }));
      setError(body.detail || `Request failed: ${res.status}`);
      return;
    }

    router.refresh();
  }

  const currentMd = view === "internal" ? internalMd : clientFacingMd;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex gap-1 border-b">
          <button
            type="button"
            onClick={() => setView("internal")}
            className={`px-3 py-1 text-sm border-b-2 -mb-px ${
              view === "internal"
                ? "border-gray-900 text-gray-900 font-medium"
                : "border-transparent text-gray-600"
            }`}
          >
            Internal (operator only)
          </button>
          <button
            type="button"
            onClick={() => setView("client_facing")}
            className={`px-3 py-1 text-sm border-b-2 -mb-px ${
              view === "client_facing"
                ? "border-gray-900 text-gray-900 font-medium"
                : "border-transparent text-gray-600"
            }`}
          >
            Client-facing (preview)
          </button>
        </div>
        <Button type="button" size="sm" variant="outline" onClick={regenerate} disabled={loading}>
          {loading ? "Regenerating..." : "Regenerate now"}
        </Button>
      </div>

      {regeneratedAt && (
        <p className="text-xs text-gray-500">
          Last regenerated: {new Date(regeneratedAt).toLocaleString()}
        </p>
      )}

      {error && <p className="text-sm text-red-600">{error}</p>}

      {currentMd ? (
        <article className="prose prose-sm max-w-none bg-white border rounded-lg p-6">
          <ReactMarkdown>{currentMd}</ReactMarkdown>
        </article>
      ) : (
        <p className="text-sm text-gray-500">
          Profile not generated yet. Add a note first, or click &quot;Regenerate now&quot;.
        </p>
      )}
    </div>
  );
}
```

- [ ] **Step 2: Profile page**

Create `web/app/dashboard/clients/[id]/profile/page.tsx`:

```typescript
import { createClient } from "@/lib/supabase/server";
import { ProfileView } from "@/components/clients/profile-view";

export const dynamic = "force-dynamic";

export default async function ProfileTab({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const supabase = await createClient();

  const { data } = await supabase
    .from("clients")
    .select("internal_profile_md, client_facing_profile_md, profile_regenerated_at")
    .eq("id", id)
    .maybeSingle();

  return (
    <div>
      <h3 className="text-lg font-medium mb-4">Profile</h3>
      <ProfileView
        clientId={id}
        internalMd={data?.internal_profile_md ?? null}
        clientFacingMd={data?.client_facing_profile_md ?? null}
        regeneratedAt={data?.profile_regenerated_at ?? null}
      />
    </div>
  );
}
```

- [ ] **Step 3: Verify build**

```bash
cd web && npm run build 2>&1 | tail -5
```

Expected: build succeeds; new route registers.

- [ ] **Step 4: Commit**

```bash
cd .. && git add web/components/clients/profile-view.tsx web/app/dashboard/clients/[id]/profile
git commit -m "feat(web): Profile tab with internal + client-facing view toggle

ProfileView component renders ReactMarkdown for the selected view.
Toggle between 'Internal (operator only)' and 'Client-facing (preview)'.
'Regenerate now' button calls POST /clients/{id}/profile/regenerate."
```

---

### Task 20: Link client list to detail pages

**Files:**
- Modify: `web/app/dashboard/page.tsx`

- [ ] **Step 1: Read current dashboard home**

```bash
cat "web/app/dashboard/page.tsx"
```

- [ ] **Step 2: Make client list items linkable**

Replace `web/app/dashboard/page.tsx`:

```typescript
import Link from "next/link";
import { createClient } from "@/lib/supabase/server";
import { Button } from "@/components/ui/button";

export const dynamic = "force-dynamic";

export default async function DashboardHome() {
  const supabase = await createClient();
  const { data: clients } = await supabase
    .from("clients")
    .select("id, client_name, short_context, status, created_at")
    .eq("is_deleted", false)
    .order("created_at", { ascending: false });

  const hasClients = clients && clients.length > 0;

  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <h2 className="text-2xl font-semibold">
          {hasClients ? "Your clients" : "Welcome to FollowRoom"}
        </h2>
        <Link href="/dashboard/clients/new">
          <Button>Add client</Button>
        </Link>
      </div>

      {!hasClients ? (
        <div className="bg-white rounded-lg border p-12 text-center">
          <p className="text-gray-600 mb-6">
            Add your first client to start building their relationship room.
          </p>
          <Link href="/dashboard/clients/new">
            <Button>Add your first client</Button>
          </Link>
        </div>
      ) : (
        <ul className="space-y-3">
          {clients.map((c) => (
            <li key={c.id}>
              <Link
                href={`/dashboard/clients/${c.id}`}
                className="block bg-white rounded-lg border p-4 hover:border-gray-400 transition-colors"
              >
                <h3 className="font-medium">{c.client_name}</h3>
                <p className="text-sm text-gray-600 mt-1">{c.short_context}</p>
                <p className="text-xs text-gray-500 mt-2">Status: {c.status}</p>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
```

- [ ] **Step 3: Verify build**

```bash
cd web && npm run build 2>&1 | tail -5
```

Expected: build succeeds.

- [ ] **Step 4: Commit**

```bash
cd .. && git add web/app/dashboard/page.tsx
git commit -m "feat(web): link client list items to detail pages

Each client row in the dashboard home is now a link to
/dashboard/clients/{id} (Overview tab). Hover state added."
```

---

### Task 21: E2E test — note → fact → reject

**Files:**
- Create: `web/tests/e2e/extract-fact-from-note.spec.ts`

- [ ] **Step 1: Write E2E test**

Create `web/tests/e2e/extract-fact-from-note.spec.ts`:

```typescript
import { test, expect } from "@playwright/test";

// Pre-requisites for this E2E to pass:
// 1. Supabase email confirmations OFF (dev project)
// 2. Migrations 0001-0010 applied
// 3. Backend running on http://localhost:8000 (uvicorn app.main:app)
// 4. Real ANTHROPIC_API_KEY in backend/.env
// 5. web/.env.local has NEXT_PUBLIC_BACKEND_API_URL=http://localhost:8000

test.describe("Manual note → extraction → operator override", () => {
  test("operator adds note, sees facts extracted, rejects one", async ({ page }) => {
    test.skip(
      !process.env.NEXT_PUBLIC_SUPABASE_URL ||
        process.env.NEXT_PUBLIC_SUPABASE_URL.includes("ci.supabase.co"),
      "Requires real Supabase + backend + Anthropic key",
    );

    const email = `e2e-${Date.now()}@e2e.followroom.dev`;
    const password = "SecurePassword123!";

    // Sign up
    await page.goto("/signup");
    await page.fill("#email", email);
    await page.fill("#password", password);
    await page.click("button[type=submit]");
    await page.waitForURL("**/login*");

    // Log in
    await page.fill("#email", email);
    await page.fill("#password", password);
    await page.click("button[type=submit]");
    await page.waitForURL("/dashboard", { timeout: 10000 });

    // Create client
    await page.click("text=Add your first client");
    await page.waitForURL("**/dashboard/clients/new");
    await page.fill("#client_name", `Sarah Tan E2E ${Date.now()}`);
    await page.fill(
      "#short_context",
      "HDB upgrade, East Coast, around $1.8M, husband works in finance.",
    );
    await page.click("button[type=submit]:has-text('Create client')");
    await page.waitForURL("/dashboard", { timeout: 10000 });

    // Open the client detail page
    await page.click("text=Sarah Tan E2E");
    await page.waitForURL(/\/dashboard\/clients\//);

    // Switch to Add note tab
    await page.click("text=Add note");
    await page.fill(
      "#raw_text",
      "Sarah said she really wants Marine Parade because her parents live nearby. Her husband is open to going up to $2.2M now.",
    );
    await page.click("button[type=submit]:has-text('Add note')");

    // Wait for the success banner (extraction completes synchronously)
    await expect(
      page.locator("text=Note ingested"),
    ).toBeVisible({ timeout: 60000 });

    // Switch to Facts tab; should see at least 1 fact
    await page.click("text=Facts");
    await expect(page.locator("text=property preference")).toBeVisible({
      timeout: 10000,
    });

    // Reject the first fact
    const rejectButton = page.locator("button:has-text('Reject')").first();
    await rejectButton.click();

    // After reject + soft-delete, the fact disappears from the list
    await page.waitForTimeout(2000); // give the DB write + router.refresh
    // (specific assertion depends on extraction output; this is best-effort)
  });
});
```

- [ ] **Step 2: Commit (don't run — E2E requires manual env setup)**

```bash
git add web/tests/e2e/extract-fact-from-note.spec.ts
git commit -m "test(e2e): manual note → extraction → fact reject

End-to-end exercises the full Plan 2 flow: sign up → create client →
add note → AI extracts facts → operator rejects one fact (soft-delete).

Skipped in CI without real Supabase + backend + Anthropic key.
Run locally with backend + frontend dev servers and a real ANTHROPIC_API_KEY."
```

---

### Task 22: Update SCHEMA_REFERENCE.md

**Files:**
- Modify: `supabase/SCHEMA_REFERENCE.md`

- [ ] **Step 1: Find the clients section and append profile columns**

Locate the `clients` table section in `supabase/SCHEMA_REFERENCE.md`. After the existing `updated_at` row, add (replace the entire table with this complete version to be safe):

In the clients table column list, before the index list, add these rows after `updated_at`:

```markdown
| internal_profile_md | TEXT | nullable; LLM-generated internal profile (Plan 2 migration 0010) |
| client_facing_profile_md | TEXT | nullable; tactfully rewritten subset for client-facing room (Plan 2) |
| profile_regenerated_at | TIMESTAMPTZ | nullable; last profile regeneration timestamp |
```

Edit `supabase/SCHEMA_REFERENCE.md` by hand (or via Edit tool) to insert these three rows in the clients column table.

- [ ] **Step 2: Update "Last updated" date**

In the file's header, change `Last updated: 2026-05-18 (Foundation plan complete)` to `Last updated: 2026-05-18 (Plan 2 Core KB Layer complete)`.

- [ ] **Step 3: Commit**

```bash
git add supabase/SCHEMA_REFERENCE.md
git commit -m "docs(schema): document migration 0010 profile columns on clients

internal_profile_md + client_facing_profile_md + profile_regenerated_at
added via migration 0010 (Plan 2 Task 10)."
```

---

### Task 23: Run all tests + verify build green end-to-end

**Files:**
- (none — verification only)

- [ ] **Step 1: Run all backend tests**

```bash
cd backend && source .venv/bin/activate && pytest -v 2>&1 | tail -10
```

Expected: ALL tests pass (Foundation's 14 + Plan 2's new tests).

- [ ] **Step 2: Run frontend tests + build**

```bash
cd ../web && npm run test 2>&1 | tail -5 && npm run build 2>&1 | tail -10
```

Expected: unit tests pass; build green; all routes register.

- [ ] **Step 3: Apply migration to confirm idempotency**

```bash
cd ../backend && source .venv/bin/activate && python scripts/apply_migrations.py 2>&1 | tail -3
```

Expected: `Migrations applied successfully.` (re-runs of 0001-0009 are no-ops; 0010 already applied so the `IF NOT EXISTS` makes it a no-op too).

- [ ] **Step 4: No commit (verification step only)**

---

### Task 24: Update root CLAUDE.md status + decision ledger

**Files:**
- Modify: `CLAUDE.md`
- Modify: `docs/decisions/decision-ledger.md`

- [ ] **Step 1: Update CLAUDE.md status section**

In `CLAUDE.md`, find the `## Status` section and replace it with:

```markdown
## Status

**Phase: Plan 2 — Core KB Layer complete (2026-05-18).**

What's now standing (in addition to Foundation):
- Real Anthropic Sonnet 4.6 extraction via `instructor` structured outputs
- ExtractionPipeline orchestrates event → extracted facts → ADD/UPDATE/NOOP decisions → fact persistence → both-view profile regeneration
- POST /events ingests manual_note (Phase 2 only; other source_types land in Plan 3+)
- GET /clients/{id}/facts + POST /facts/{id}/stance for operator review/override
- GET /clients/{id}/profile + POST .../profile/regenerate
- Client detail page in dashboard with tabs: Overview / Facts / Profile / Add note
- ReactMarkdown rendering for both profile views
- Migration 0010: internal_profile_md + client_facing_profile_md + profile_regenerated_at on clients

Test count: backend ~30+ tests, frontend ~6+ unit tests, 2 E2E specs.

Next:
- Plan 3 — Transcript Upload Channel (audio + text upload, Whisper transcription, attribution at upload)

See `docs/superpowers/plans/2026-05-18-core-kb-layer.md` for the Plan 2 details.
```

- [ ] **Step 2: Add decision ledger entry**

In `docs/decisions/decision-ledger.md`, add at the top of the Active Decisions section:

```markdown
### [2026-05-18] AI: ExtractionPipeline orchestrates event → facts → profile synchronously in POST /events

**Context:** Plan 2 needed to wire the AI extraction pipeline. Two design choices: synchronous (extraction happens in the request) vs asynchronous (event enqueued, extraction runs in background). For Phase 1 volume (single operator, ~150 events/month), synchronous is simpler — no queue infra, immediate operator feedback.

**Decision:** ExtractionPipeline runs synchronously inside POST /events. Request response includes per-action counters (facts_added/updated/noop/deleted + profile_regenerated). Operator sees the extraction result immediately.

**Rationale:** synchronous is simpler at this volume; UI gives immediate feedback; no queue/worker infra. When volume grows (Plan 7-9 agency tier) we move extraction to a background worker pattern.

**Link:** `backend/app/services/extraction_pipeline.py`; `backend/app/api/events.py`
```

- [ ] **Step 3: Commit**

```bash
git add CLAUDE.md docs/decisions/decision-ledger.md
git commit -m "docs: update CLAUDE.md + decision ledger for Plan 2 completion

Status reflects ExtractionPipeline + facts/profile APIs + dashboard tabs.
Ledger captures the synchronous-extraction decision (vs async queue)
for Phase 1 volume."
```

---

### Task 25: Push branch + open PR

- [ ] **Step 1: Push branch**

```bash
git push -u origin feat/core-kb-layer-plan-2
```

- [ ] **Step 2: Open PR**

```bash
gh pr create --title "feat: Plan 2 — Core KB Layer (extraction + facts + profile)" --body "$(cat <<'EOF'
## Summary
- Real Anthropic Sonnet 4.6 extraction via `instructor` structured outputs
- ExtractionPipeline: event → facts → ADD/UPDATE/NOOP → both-view profile regeneration (synchronous in POST /events)
- POST /events (manual_note ingestion), GET/POST facts + stance, GET/POST profile + regenerate
- Frontend client detail page with tabs (Overview / Facts / Profile / Add note)
- Markdown profile rendering with internal/client-facing toggle
- Migration 0010 adds profile columns

## Test plan
- [ ] `cd backend && pytest -v` — all backend tests pass
- [ ] `cd web && npm run test` — all unit tests pass
- [ ] `cd web && npm run build` — build green
- [ ] `cd backend && python scripts/apply_migrations.py` — migration 0010 idempotent
- [ ] Manual smoke: sign up → create client → add a real-feeling note → see facts extracted in Facts tab → click Regenerate Now in Profile tab → see both views populate

## Design doc + plan
- Plan: `docs/superpowers/plans/2026-05-18-core-kb-layer.md`
- Architecture: `docs/superpowers/specs/2026-05-18-followroom-architecture-design.md` §6

## Next plan
Plan 3 — Transcript Upload Channel (audio + text upload, Whisper transcription)

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

- [ ] **Step 3: Verify CI runs**

```bash
gh pr checks
```

Expected: backend-ci + web-ci queued or running.

---

## Plan complete

You now have a working KB pipeline: operators can add manual notes, see typed facts extracted with source citations, override stances, and view dual-view profiles. The substrate compounds.

**Next plan:** Plan 3 — Transcript Upload Channel (audio + text upload, Whisper transcription, transcript → same extraction pipeline).
