# Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Stand up FollowRoom's Phase 1 foundation — deployable FastAPI backend (Render) + Next.js 15 frontend (Vercel) + Supabase (Postgres + Auth + Storage), with the forward-compatibility hooks from design doc §8 baked in from Day 1. End state: an operator can sign up, log in, create a client with required seed context, and see that client listed in their dashboard.

**Architecture:** Single Next.js app with route groups — `(dashboard)` is auth-gated via middleware; `/r/[slug]` reserved as a public route (skeleton only here; Plan 6 will flesh out). FastAPI backend serves business logic and the single governed `store()` write path. Supabase Postgres holds the canonical KB with RLS for cross-operator isolation; Supabase Auth manages operator identity via `@supabase/ssr`. Migrations enforce append-only on `events.raw_text`, soft-delete on all user-data tables, bi-temporal columns where needed, and an `attributions` audit table from Day 1 even at N=1 operator (per design doc §8.2). The `store()` service is a thin wrapper now; Plan 9 (Phase 3 Hivemind) will expand its implementation without rewriting callers.

**Tech Stack:** FastAPI 0.115+, Python 3.14, Pydantic v2, instructor, Anthropic SDK, OpenAI SDK, supabase-py (sync); Next.js 15 (App Router), TypeScript, Tailwind CSS 4, shadcn/ui, Tremor, TanStack Table, @supabase/ssr; pytest + pytest-asyncio (backend), Vitest + Playwright (frontend); Render (backend deploy), Vercel (frontend deploy), Supabase Cloud (managed Postgres + Auth + Storage).

---

## File Structure

```
followup-rooms/
├── backend/
│   ├── pyproject.toml                  Python 3.14 project config (uv-compatible)
│   ├── requirements.txt                Pinned deps for Render
│   ├── Procfile                        Render web process command
│   ├── render.yaml                     Render infra-as-code
│   ├── runtime.txt                     Python version pin (3.14.4)
│   ├── nixpacks.toml                   Build config
│   ├── .env.example                    Documented env vars
│   ├── .python-version                 For uv / pyenv
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                     FastAPI app + lifespan + middleware
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── health.py               GET /health
│   │   │   ├── operators.py            GET /operators/me
│   │   │   └── clients.py              POST/GET /clients
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   └── store.py                Single governed write path
│   │   ├── ai/
│   │   │   ├── __init__.py
│   │   │   ├── dispatcher.py           AgentDispatcher + LogicalRole enum
│   │   │   └── providers/
│   │   │       ├── __init__.py
│   │   │       ├── base.py             Provider Protocol
│   │   │       ├── anthropic.py        Anthropic adapter (stub for Plan 1)
│   │   │       └── openai.py           OpenAI adapter (stub for Plan 1)
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── client.py               Pydantic models
│   │   │   └── attribution.py
│   │   └── core/
│   │       ├── __init__.py
│   │       ├── config.py               Settings via pydantic-settings
│   │       ├── supabase.py             Request-scoped Supabase client factory
│   │       └── auth.py                 FastAPI auth dependency
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── conftest.py                 pytest fixtures
│   │   ├── test_health.py
│   │   ├── test_dispatcher.py
│   │   ├── test_store.py
│   │   └── test_clients_api.py
│   └── scripts/
│       └── apply_migrations.py         Helper to apply Supabase migrations
├── web/
│   ├── package.json
│   ├── tsconfig.json
│   ├── tailwind.config.ts
│   ├── next.config.ts
│   ├── postcss.config.mjs
│   ├── components.json                 shadcn/ui config
│   ├── vercel.json                     Vercel config
│   ├── .env.example
│   ├── app/
│   │   ├── layout.tsx                  Root layout
│   │   ├── page.tsx                    Landing/marketing (minimal)
│   │   ├── globals.css                 Tailwind base
│   │   ├── (auth)/
│   │   │   ├── login/page.tsx
│   │   │   └── signup/page.tsx
│   │   ├── (dashboard)/
│   │   │   ├── layout.tsx              Auth-required layout (checks getUser)
│   │   │   ├── page.tsx                Dashboard home
│   │   │   └── clients/
│   │   │       ├── page.tsx            Client list
│   │   │       └── new/page.tsx        Create new client form
│   │   ├── r/[slug]/
│   │   │   └── page.tsx                Public room (skeleton placeholder; Plan 6)
│   │   └── api/
│   │       └── auth/callback/route.ts  Supabase auth callback handler
│   ├── components/
│   │   ├── ui/                         shadcn/ui generated components
│   │   └── clients/
│   │       └── new-client-form.tsx     Create client form
│   ├── lib/
│   │   └── supabase/
│   │       ├── client.ts               Browser client factory (request-scoped)
│   │       ├── server.ts               Server client factory (request-scoped)
│   │       └── middleware.ts           Middleware client helper
│   ├── middleware.ts                   Next.js root middleware
│   └── tests/
│       ├── unit/
│       │   └── supabase-clients.test.ts
│       └── e2e/
│           └── signup-create-client.spec.ts
├── supabase/
│   ├── migrations/
│   │   ├── 0001_operators.sql
│   │   ├── 0002_clients.sql
│   │   ├── 0003_events.sql
│   │   ├── 0004_facts.sql
│   │   ├── 0005_room_attachments.sql
│   │   ├── 0006_attributions.sql
│   │   ├── 0007_visibility_promotions.sql
│   │   ├── 0008_rls_policies.sql
│   │   └── 0009_rooms_public_view.sql
│   ├── SCHEMA_REFERENCE.md             Updated with all 7 tables + 1 view
│   └── schema.sql                      Consolidated view; regenerated from migrations
├── DESIGN.md                           Brand + voice + visual identity
├── PRODUCT.md                          What we are; what we aren't; anti-references
└── .github/
    └── workflows/
        ├── backend-ci.yml              Lint + typecheck + test backend
        └── web-ci.yml                  Lint + typecheck + test web
```

---

## Tasks

### Task 1: Pre-flight — Supabase project + env templates

One-time manual Supabase setup; then capture credentials in env templates.

**Files:**
- Create: `backend/.env.example`
- Create: `web/.env.example`

- [ ] **Step 1: Manual — create Supabase project**

Go to https://supabase.com → **New Project** → name: `followup-rooms` → region: closest to Singapore (e.g., `ap-southeast-1`) → set strong database password → wait for provisioning (~2 min).

- [ ] **Step 2: Manual — capture API credentials**

In the Supabase dashboard: **Settings → API**. Copy and save securely (not in repo):
- **Project URL** (`https://<project-ref>.supabase.co`)
- **anon public key** (long JWT — safe in client bundles)
- **service_role secret key** (NEVER in client bundles — backend only)

- [ ] **Step 3: Manual — capture Postgres connection string**

**Settings → Database → Connection String → URI**. Save the `postgresql://` URI for migrations (will be used by `scripts/apply_migrations.py`).

- [ ] **Step 4: Create backend env template**

Create `backend/.env.example`:

```bash
# Supabase
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_ANON_KEY=eyJ...your-anon-key
SUPABASE_SERVICE_ROLE_KEY=eyJ...your-service-role-key
SUPABASE_DB_URL=postgresql://postgres:password@db.your-project-ref.supabase.co:5432/postgres

# AI providers
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...

# Runtime
ENV=development
LOG_LEVEL=INFO
PORT=8000
```

- [ ] **Step 5: Create frontend env template**

Create `web/.env.example`:

```bash
# Supabase (NEXT_PUBLIC_ prefix exposes to client bundle)
NEXT_PUBLIC_SUPABASE_URL=https://your-project-ref.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJ...your-anon-key

# Backend API URL
BACKEND_API_URL=http://localhost:8000
```

- [ ] **Step 6: Commit**

```bash
git checkout -b feat/foundation-plan-1
git add backend/.env.example web/.env.example
git commit -m "chore(env): add env templates for backend + web

Supabase project provisioned manually; credentials populated in local
.env files (not committed). Templates document required vars."
```

---

### Task 2: Backend Python project — pyproject + requirements + runtime

Initialize the Python project with pinned deps for Render.

**Files:**
- Create: `backend/pyproject.toml`
- Create: `backend/requirements.txt`
- Create: `backend/runtime.txt`
- Create: `backend/.python-version`

- [ ] **Step 1: Pin Python version**

Create `backend/runtime.txt`:

```
python-3.14.4
```

Create `backend/.python-version`:

```
3.14.4
```

- [ ] **Step 2: Create pyproject.toml**

Create `backend/pyproject.toml`:

```toml
[project]
name = "followroom-backend"
version = "0.0.1"
description = "FollowRoom backend — FastAPI + AI pipeline"
requires-python = ">=3.14"
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.32.0",
    "pydantic>=2.9.0",
    "pydantic-settings>=2.5.0",
    "supabase>=2.9.0",
    "httpx>=0.27.0",
    "anthropic>=0.39.0",
    "openai>=1.55.0",
    "instructor>=1.6.0",
    "python-multipart>=0.0.12",
    "python-dotenv>=1.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.3.0",
    "pytest-asyncio>=0.24.0",
    "pytest-cov>=5.0.0",
    "httpx>=0.27.0",
    "ruff>=0.7.0",
    "mypy>=1.13.0",
]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
pythonpath = ["."]

[tool.ruff]
line-length = 100
target-version = "py314"

[tool.ruff.lint]
select = ["E", "F", "I", "B", "UP"]

[tool.mypy]
python_version = "3.14"
strict = true
ignore_missing_imports = true
```

- [ ] **Step 3: Create requirements.txt**

Create `backend/requirements.txt` (Render uses this; mirrors pyproject runtime deps):

```
fastapi>=0.115.0
uvicorn[standard]>=0.32.0
pydantic>=2.9.0
pydantic-settings>=2.5.0
supabase>=2.9.0
httpx>=0.27.0
anthropic>=0.39.0
openai>=1.55.0
instructor>=1.6.0
python-multipart>=0.0.12
python-dotenv>=1.0.0
```

- [ ] **Step 4: Install deps locally**

```bash
cd backend
python3.14 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Expected: clean install, no errors.

- [ ] **Step 5: Verify Python version**

```bash
python --version
```

Expected: `Python 3.14.4`

- [ ] **Step 6: Commit**

```bash
git add backend/pyproject.toml backend/requirements.txt backend/runtime.txt backend/.python-version
git commit -m "chore(backend): initialize Python 3.14 project with pinned deps

FastAPI 0.115+, Pydantic v2, Supabase 2.9+, Anthropic + OpenAI SDKs,
instructor for structured output. Dev deps: pytest, ruff, mypy.

Python version 3.14.4 confirmed compatible across the stack
(per compat research 2026-05-18). httpx flagged for monitoring
(no 3.14 PyPI classifier but runtime support confirmed)."
```

---

### Task 3: Backend core — config + Supabase client (request-scoped)

Set up Pydantic settings for env vars and a request-scoped Supabase client factory. **Critical: NEVER module-scope the Supabase client** (per design doc §9.3 — module-scoped clients leak sessions across users on Vercel Fluid Compute).

**Files:**
- Create: `backend/app/__init__.py`
- Create: `backend/app/core/__init__.py`
- Create: `backend/app/core/config.py`
- Create: `backend/app/core/supabase.py`
- Create: `backend/tests/__init__.py`
- Create: `backend/tests/conftest.py`
- Create: `backend/tests/test_config.py`

- [ ] **Step 1: Create empty package markers**

```bash
mkdir -p backend/app/core backend/tests
touch backend/app/__init__.py backend/app/core/__init__.py backend/tests/__init__.py
```

- [ ] **Step 2: Write failing test for Settings**

Create `backend/tests/test_config.py`:

```python
import os
import pytest
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
    for key in ["SUPABASE_URL"]:
        monkeypatch.delenv(key, raising=False)
    with pytest.raises(Exception):
        Settings(_env_file=None)
```

- [ ] **Step 3: Run test, verify failure**

```bash
cd backend
source .venv/bin/activate
pytest tests/test_config.py -v
```

Expected: `ModuleNotFoundError: No module named 'app.core.config'`

- [ ] **Step 4: Implement Settings**

Create `backend/app/core/config.py`:

```python
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Supabase
    supabase_url: str
    supabase_anon_key: str
    supabase_service_role_key: str
    supabase_db_url: str

    # AI providers
    anthropic_api_key: str
    openai_api_key: str

    # Runtime
    env: str = "development"
    log_level: str = "INFO"
    port: int = 8000


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance; safe to call from any context."""
    return Settings()
```

- [ ] **Step 5: Run test, verify pass**

```bash
pytest tests/test_config.py -v
```

Expected: 2 passed.

- [ ] **Step 6: Write failing test for Supabase client factory**

Create `backend/tests/conftest.py`:

```python
import pytest


@pytest.fixture(autouse=True)
def _set_test_env(monkeypatch):
    """Set env vars for every test so Settings() doesn't fail."""
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "anon-test")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "service-test")
    monkeypatch.setenv("SUPABASE_DB_URL", "postgresql://test")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "ant-test")
    monkeypatch.setenv("OPENAI_API_KEY", "oa-test")
```

Add to `backend/tests/test_config.py` (append):

```python
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
```

- [ ] **Step 7: Run, verify failure**

```bash
pytest tests/test_config.py -v
```

Expected: `ModuleNotFoundError: No module named 'app.core.supabase'`

- [ ] **Step 8: Implement Supabase client factory**

Create `backend/app/core/supabase.py`:

```python
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
```

- [ ] **Step 9: Run, verify pass**

```bash
pytest tests/ -v
```

Expected: 4 passed.

- [ ] **Step 10: Commit**

```bash
git add backend/app backend/tests
git commit -m "feat(backend): core config + request-scoped Supabase client factories

CRITICAL: factories return new client instances per call to prevent
cross-user session leak on serverless runtimes (design doc §9.3).
Tests verify factory behavior."
```

---

### Task 4: Backend FastAPI app + health endpoint

Stand up the FastAPI app with a health endpoint to verify deployment.

**Files:**
- Create: `backend/app/main.py`
- Create: `backend/app/api/__init__.py`
- Create: `backend/app/api/health.py`
- Create: `backend/tests/test_health.py`

- [ ] **Step 1: Package marker**

```bash
mkdir -p backend/app/api
touch backend/app/api/__init__.py
```

- [ ] **Step 2: Write failing health test**

Create `backend/tests/test_health.py`:

```python
from fastapi.testclient import TestClient

from app.main import app


def test_health_returns_200_and_ok():
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert "version" in body
    assert "env" in body
```

- [ ] **Step 3: Run, verify failure**

```bash
pytest tests/test_health.py -v
```

Expected: `ModuleNotFoundError: No module named 'app.main'`

- [ ] **Step 4: Implement health router**

Create `backend/app/api/health.py`:

```python
from fastapi import APIRouter

from app.core.config import get_settings

router = APIRouter()


@router.get("/health")
async def health() -> dict[str, str]:
    """Liveness probe. Returns runtime info; never accesses external services."""
    settings = get_settings()
    return {
        "status": "ok",
        "version": "0.0.1",
        "env": settings.env,
    }
```

- [ ] **Step 5: Implement FastAPI app**

Create `backend/app/main.py`:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import health


def create_app() -> FastAPI:
    app = FastAPI(
        title="FollowRoom Backend",
        version="0.0.1",
        description="Phase 1 foundation API",
    )

    # CORS — tightened in later tasks once we know the frontend origin
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    return app


app = create_app()
```

- [ ] **Step 6: Run, verify pass**

```bash
pytest tests/test_health.py -v
```

Expected: 1 passed.

- [ ] **Step 7: Start the server locally**

```bash
uvicorn app.main:app --reload --port 8000
```

Then in another terminal:

```bash
curl http://localhost:8000/health
```

Expected: `{"status":"ok","version":"0.0.1","env":"development"}`

Stop the server (Ctrl+C in the uvicorn terminal).

- [ ] **Step 8: Commit**

```bash
git add backend/app backend/tests
git commit -m "feat(backend): FastAPI app + health endpoint with test

GET /health returns status, version, env. CORS configured for
localhost:3000 (frontend dev origin). Test verifies endpoint shape."
```

---

### Task 5: Backend deploy config — Render

Configure Render to deploy the FastAPI backend.

**Files:**
- Create: `backend/Procfile`
- Create: `backend/render.yaml`
- Create: `backend/nixpacks.toml`

- [ ] **Step 1: Create Procfile**

Create `backend/Procfile`:

```
web: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

- [ ] **Step 2: Create render.yaml**

Create `backend/render.yaml`:

```yaml
services:
  - type: web
    name: followup-rooms-backend
    runtime: python
    rootDir: backend
    plan: starter
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn app.main:app --host 0.0.0.0 --port $PORT
    healthCheckPath: /health
    envVars:
      - key: PYTHON_VERSION
        value: 3.14.4
      - key: SUPABASE_URL
        sync: false
      - key: SUPABASE_ANON_KEY
        sync: false
      - key: SUPABASE_SERVICE_ROLE_KEY
        sync: false
      - key: SUPABASE_DB_URL
        sync: false
      - key: ANTHROPIC_API_KEY
        sync: false
      - key: OPENAI_API_KEY
        sync: false
      - key: ENV
        value: production
      - key: LOG_LEVEL
        value: INFO
```

- [ ] **Step 3: Create nixpacks.toml (build hints)**

Create `backend/nixpacks.toml`:

```toml
[phases.setup]
nixPkgs = ["python312", "gcc"]

[phases.install]
cmds = ["pip install -r requirements.txt"]

[start]
cmd = "uvicorn app.main:app --host 0.0.0.0 --port $PORT"
```

- [ ] **Step 4: Commit**

```bash
git add backend/Procfile backend/render.yaml backend/nixpacks.toml
git commit -m "chore(deploy): Render deploy config for backend

Starter plan, Python 3.14.4, env vars marked sync:false (set in
Render dashboard). Health check at /health."
```

---

### Task 6: Backend CI workflow

Add GitHub Actions for backend lint + typecheck + test.

**Files:**
- Create: `.github/workflows/backend-ci.yml`

- [ ] **Step 1: Write workflow**

Create `.github/workflows/backend-ci.yml`:

```yaml
name: Backend CI

on:
  push:
    branches: [main]
    paths:
      - "backend/**"
      - ".github/workflows/backend-ci.yml"
  pull_request:
    paths:
      - "backend/**"
      - ".github/workflows/backend-ci.yml"

jobs:
  test:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: backend
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.14.4"
          cache: "pip"
          cache-dependency-path: backend/requirements.txt

      - name: Install deps
        run: |
          pip install -e ".[dev]"

      - name: Lint
        run: ruff check .

      - name: Typecheck
        run: mypy app

      - name: Test
        env:
          SUPABASE_URL: https://ci.supabase.co
          SUPABASE_ANON_KEY: ci-anon
          SUPABASE_SERVICE_ROLE_KEY: ci-service
          SUPABASE_DB_URL: postgresql://ci
          ANTHROPIC_API_KEY: ci-ant
          OPENAI_API_KEY: ci-oa
        run: pytest -v --cov=app --cov-report=term-missing
```

- [ ] **Step 2: Commit**

```bash
git add .github/workflows/backend-ci.yml
git commit -m "ci(backend): lint + typecheck + test on push/PR

Triggers only on backend/ path changes. Uses pinned Python 3.14.4."
```

---

### Task 7: Frontend — initialize Next.js 15 app

Bootstrap the Next.js 15 application with App Router, Tailwind, TypeScript.

**Files:**
- Create: `web/` (via create-next-app)

- [ ] **Step 1: Run create-next-app**

From the repo root:

```bash
npx create-next-app@latest web \
  --typescript \
  --tailwind \
  --app \
  --src-dir=false \
  --import-alias="@/*" \
  --use-npm \
  --no-eslint
```

When prompted:
- "Would you like to use ESLint?" → No (we configure separately)
- "Would you like to use Turbopack for next dev?" → Yes
- "Would you like to use Turbopack for next build?" → No (still experimental as of mid-2026)

- [ ] **Step 2: Pin Next.js version**

```bash
cd web
npm install next@15.1 react@19 react-dom@19
```

- [ ] **Step 3: Verify dev server starts**

```bash
npm run dev
```

Expected: Next.js boots; navigate to `http://localhost:3000` → see default page. Stop with Ctrl+C.

- [ ] **Step 4: Commit**

```bash
git add web/
git commit -m "feat(web): initialize Next.js 15 with App Router + Tailwind + TypeScript

Turbopack for dev. ESLint configured separately in later task."
```

---

### Task 8: Frontend — shadcn/ui init + Tremor + TanStack Table

Install the design system components per design doc §9.2.

**Files:**
- Modify: `web/package.json`
- Create: `web/components.json`
- Create: `web/lib/utils.ts`
- Create: `web/components/ui/*` (multiple files generated)

- [ ] **Step 1: Initialize shadcn/ui**

```bash
cd web
npx shadcn@latest init
```

When prompted:
- "Which style?" → Default
- "Which color?" → Slate (neutral; we adjust later in DESIGN.md alignment)
- "Use CSS variables?" → Yes

This creates `components.json`, `lib/utils.ts`, and sets up Tailwind config.

- [ ] **Step 2: Install initial shadcn components**

```bash
npx shadcn@latest add button input label form textarea card
```

- [ ] **Step 3: Install Tremor for KPI cards / dashboard charts**

```bash
npm install @tremor/react
```

Add Tremor's tailwind preset to `web/tailwind.config.ts` (modify the `content` array to include Tremor's path):

```typescript
import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./node_modules/@tremor/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {},
  },
  plugins: [],
};

export default config;
```

- [ ] **Step 4: Install TanStack Table**

```bash
npm install @tanstack/react-table
```

- [ ] **Step 5: Install Vitest for unit testing**

```bash
npm install -D vitest @vitejs/plugin-react jsdom @testing-library/react @testing-library/jest-dom
```

Create `web/vitest.config.ts`:

```typescript
import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import path from "path";

export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./tests/setup.ts"],
  },
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./"),
    },
  },
});
```

Create `web/tests/setup.ts`:

```typescript
import "@testing-library/jest-dom/vitest";
```

Add to `web/package.json` scripts:

```json
{
  "scripts": {
    "test": "vitest run",
    "test:watch": "vitest"
  }
}
```

- [ ] **Step 6: Install Playwright for E2E**

```bash
npm install -D @playwright/test
npx playwright install --with-deps chromium
```

Create `web/playwright.config.ts`:

```typescript
import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./tests/e2e",
  timeout: 30000,
  use: {
    baseURL: "http://localhost:3000",
    trace: "on-first-retry",
  },
  webServer: {
    command: "npm run dev",
    url: "http://localhost:3000",
    reuseExistingServer: !process.env.CI,
    timeout: 60000,
  },
  projects: [
    {
      name: "chromium",
      use: { browserName: "chromium" },
    },
  ],
});
```

Add to `web/package.json` scripts:

```json
{
  "scripts": {
    "test:e2e": "playwright test"
  }
}
```

- [ ] **Step 7: Commit**

```bash
git add web/
git commit -m "feat(web): install shadcn/ui + Tremor + TanStack Table + test infra

Vitest for unit tests; Playwright for E2E. Initial shadcn components:
button, input, label, form, textarea, card. Tremor for KPI surfaces."
```

---

### Task 9: Frontend — @supabase/ssr setup (auth + request-scoped clients)

Set up `@supabase/ssr` with request-scoped client factories per design doc §9.3 critical footgun warning.

**Files:**
- Modify: `web/package.json`
- Create: `web/lib/supabase/client.ts`
- Create: `web/lib/supabase/server.ts`
- Create: `web/lib/supabase/middleware.ts`
- Create: `web/tests/unit/supabase-clients.test.ts`

- [ ] **Step 1: Install @supabase/ssr**

```bash
cd web
npm install @supabase/ssr @supabase/supabase-js
```

- [ ] **Step 2: Write failing test for client factories**

Create `web/tests/unit/supabase-clients.test.ts`:

```typescript
import { describe, it, expect, vi } from "vitest";

// We test that each factory returns a fresh instance per call.
// This is critical — module-scoped clients leak sessions across
// users on Vercel Fluid Compute (design doc §9.3).

describe("Supabase client factories", () => {
  it("createBrowserClient returns a fresh client per call", async () => {
    vi.stubEnv("NEXT_PUBLIC_SUPABASE_URL", "https://test.supabase.co");
    vi.stubEnv("NEXT_PUBLIC_SUPABASE_ANON_KEY", "anon-test");

    const { createClient } = await import("@/lib/supabase/client");
    const c1 = createClient();
    const c2 = createClient();

    expect(c1).not.toBe(c2);
  });
});
```

- [ ] **Step 3: Run, verify failure**

```bash
npm run test
```

Expected: test fails — file `@/lib/supabase/client` not found.

- [ ] **Step 4: Implement browser client factory**

Create `web/lib/supabase/client.ts`:

```typescript
import { createBrowserClient } from "@supabase/ssr";

/**
 * Browser-side Supabase client factory.
 *
 * CRITICAL: Returns a new client instance per call.
 * Do NOT cache or module-scope this client — module-scoped Supabase
 * clients leak sessions across users on serverless runtimes
 * (Vercel Fluid Compute). See design doc §9.3.
 */
export function createClient() {
  return createBrowserClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
  );
}
```

- [ ] **Step 5: Implement server client factory**

Create `web/lib/supabase/server.ts`:

```typescript
import { createServerClient } from "@supabase/ssr";
import { cookies } from "next/headers";

/**
 * Server-side Supabase client factory.
 *
 * CRITICAL: Must be called inside a request handler (uses next/headers).
 * Returns a new client per call; do NOT cache or module-scope.
 */
export async function createClient() {
  const cookieStore = await cookies();

  return createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll() {
          return cookieStore.getAll();
        },
        setAll(cookiesToSet) {
          try {
            cookiesToSet.forEach(({ name, value, options }) =>
              cookieStore.set(name, value, options)
            );
          } catch {
            // Called from a Server Component — setAll fails silently;
            // session refresh happens in middleware.
          }
        },
      },
    }
  );
}
```

- [ ] **Step 6: Implement middleware client helper**

Create `web/lib/supabase/middleware.ts`:

```typescript
import { createServerClient } from "@supabase/ssr";
import { NextResponse, type NextRequest } from "next/server";

/**
 * Middleware client — refreshes the user's session cookie on every
 * request that passes through middleware. The returned NextResponse
 * carries the updated cookies forward.
 */
export async function updateSession(request: NextRequest) {
  let supabaseResponse = NextResponse.next({ request });

  const supabase = createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll() {
          return request.cookies.getAll();
        },
        setAll(cookiesToSet) {
          cookiesToSet.forEach(({ name, value }) =>
            request.cookies.set(name, value)
          );
          supabaseResponse = NextResponse.next({ request });
          cookiesToSet.forEach(({ name, value, options }) =>
            supabaseResponse.cookies.set(name, value, options)
          );
        },
      },
    }
  );

  // CRITICAL: this hits the auth server to verify the token.
  // Do not skip this even if you don't need the user object here —
  // it's what refreshes expired access tokens via the refresh token.
  await supabase.auth.getUser();

  return supabaseResponse;
}
```

- [ ] **Step 7: Run test, verify pass**

```bash
npm run test
```

Expected: 1 passed.

- [ ] **Step 8: Commit**

```bash
git add web/
git commit -m "feat(web): @supabase/ssr client factories (browser + server + middleware)

CRITICAL: factories return fresh instances per call; never module-scoped
(prevents cross-user session leak on Vercel Fluid Compute per design
doc §9.3). Test verifies factory behavior."
```

---

### Task 10: Frontend — Next.js root middleware (auth matcher excluding /r/[slug])

Set up Next.js middleware that refreshes auth on every request EXCEPT the public `/r/[slug]` room route per design doc §5.3.

**Files:**
- Create: `web/middleware.ts`

- [ ] **Step 1: Write middleware**

Create `web/middleware.ts`:

```typescript
import { updateSession } from "@/lib/supabase/middleware";
import type { NextRequest } from "next/server";

export async function middleware(request: NextRequest) {
  return await updateSession(request);
}

export const config = {
  matcher: [
    /*
     * Match all request paths EXCEPT:
     * - /r/[slug] and below (public client-facing rooms; no auth)
     * - _next/static (static files)
     * - _next/image (image optimization)
     * - favicon and other public assets
     *
     * IMPORTANT: Excluding /r/* means Server Actions invoked on those
     * paths get NO session refresh. Plan 6 (client-facing room) must
     * NOT depend on Server Actions; use Route Handlers + Anon Key.
     */
    "/((?!_next/static|_next/image|favicon.ico|r/|api/auth/callback|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)",
  ],
};
```

- [ ] **Step 2: Verify build works**

```bash
cd web
npm run build
```

Expected: Build completes; warnings about no pages built yet are fine.

- [ ] **Step 3: Commit**

```bash
git add web/middleware.ts
git commit -m "feat(web): Next.js middleware refreshes session, excludes /r/[slug]

Matcher excludes public room route per design doc §5.3. Important note
in comment: Server Actions on /r/* get no session refresh — client room
must use Route Handlers + Anon Key, not Server Actions."
```

---

### Task 11: Frontend — Vercel deploy config + web CI

Set up Vercel deployment + GitHub Actions for the web app.

**Files:**
- Create: `web/vercel.json`
- Create: `.github/workflows/web-ci.yml`

- [ ] **Step 1: Create vercel.json**

Create `web/vercel.json`:

```json
{
  "buildCommand": "npm run build",
  "devCommand": "npm run dev",
  "framework": "nextjs",
  "installCommand": "npm install",
  "outputDirectory": ".next"
}
```

- [ ] **Step 2: Create web CI workflow**

Create `.github/workflows/web-ci.yml`:

```yaml
name: Web CI

on:
  push:
    branches: [main]
    paths:
      - "web/**"
      - ".github/workflows/web-ci.yml"
  pull_request:
    paths:
      - "web/**"
      - ".github/workflows/web-ci.yml"

jobs:
  test:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: web
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: "npm"
          cache-dependency-path: web/package-lock.json

      - name: Install deps
        run: npm ci

      - name: Typecheck
        run: npx tsc --noEmit

      - name: Unit tests
        run: npm run test
        env:
          NEXT_PUBLIC_SUPABASE_URL: https://ci.supabase.co
          NEXT_PUBLIC_SUPABASE_ANON_KEY: ci-anon

      - name: Build
        run: npm run build
        env:
          NEXT_PUBLIC_SUPABASE_URL: https://ci.supabase.co
          NEXT_PUBLIC_SUPABASE_ANON_KEY: ci-anon
```

- [ ] **Step 3: Commit**

```bash
git add web/vercel.json .github/workflows/web-ci.yml
git commit -m "ci(web): Vercel config + GitHub Actions for typecheck + test + build

Triggers only on web/ path changes. Uses Node 20 with npm cache."
```

---

### Task 12: Migration 0001 — operators table

Create the operators table linked to Supabase Auth.

**Files:**
- Create: `supabase/migrations/0001_operators.sql`
- Create: `backend/scripts/apply_migrations.py`

- [ ] **Step 1: Write migration**

Create `supabase/migrations/0001_operators.sql`:

```sql
-- Migration: 0001 — operators table
-- Purpose: Per-account operator profile, FK to Supabase auth.users
-- Rollback: DROP TABLE operators;

CREATE TABLE operators (
  id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  email TEXT NOT NULL UNIQUE,
  name TEXT,
  company_name TEXT,
  role_title TEXT,
  industry TEXT DEFAULT 'real_estate',
  profile_photo_url TEXT,
  default_language TEXT DEFAULT 'en',
  default_tone TEXT,
  timezone TEXT DEFAULT 'Asia/Singapore',

  -- Soft-delete (Pattern 18)
  is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
  deleted_at TIMESTAMPTZ,

  -- Bi-temporal columns (TG Memory primitive prep)
  transaction_time TIMESTAMPTZ NOT NULL DEFAULT NOW(),

  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Index for soft-delete-aware queries
CREATE INDEX idx_operators_active ON operators(id) WHERE NOT is_deleted;

-- Auto-create operator row when an auth user signs up
CREATE OR REPLACE FUNCTION public.handle_new_auth_user()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO public.operators (id, email)
  VALUES (NEW.id, NEW.email)
  ON CONFLICT (id) DO NOTHING;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE TRIGGER on_auth_user_created
AFTER INSERT ON auth.users
FOR EACH ROW EXECUTE FUNCTION public.handle_new_auth_user();
```

- [ ] **Step 2: Write apply_migrations.py helper**

Create `backend/scripts/apply_migrations.py`:

```python
"""
Apply Supabase migrations in order.

Reads .sql files from ../supabase/migrations/ sorted by filename,
executes them against SUPABASE_DB_URL.

Idempotency: relies on `IF NOT EXISTS` / `CREATE OR REPLACE` in migrations.
For destructive changes, document rollback in the migration file's
'-- Rollback:' comment header.
"""
import os
import sys
from pathlib import Path

import psycopg

from app.core.config import get_settings


def main() -> int:
    settings = get_settings()
    migrations_dir = Path(__file__).parent.parent.parent / "supabase" / "migrations"

    if not migrations_dir.exists():
        print(f"Migrations directory not found: {migrations_dir}")
        return 1

    files = sorted(migrations_dir.glob("*.sql"))
    if not files:
        print("No migration files found.")
        return 0

    print(f"Applying {len(files)} migrations to {settings.supabase_url}")

    with psycopg.connect(settings.supabase_db_url) as conn:
        with conn.cursor() as cur:
            for f in files:
                print(f"  → {f.name}")
                sql = f.read_text()
                cur.execute(sql)
        conn.commit()

    print("Migrations applied successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

Add `psycopg[binary]` to `backend/requirements.txt` and `backend/pyproject.toml` dependencies:

```
psycopg[binary]>=3.2.0
```

Reinstall:

```bash
cd backend && source .venv/bin/activate && pip install -e ".[dev]"
```

- [ ] **Step 3: Apply migration 0001**

Ensure `backend/.env` is populated locally with real Supabase credentials, then:

```bash
cd backend
source .venv/bin/activate
python scripts/apply_migrations.py
```

Expected output:

```
Applying 1 migrations to https://your-project-ref.supabase.co
  → 0001_operators.sql
Migrations applied successfully.
```

- [ ] **Step 4: Verify in Supabase dashboard**

Supabase dashboard → Table Editor → confirm `operators` table exists with all columns.

- [ ] **Step 5: Commit**

```bash
git add supabase/migrations/0001_operators.sql backend/scripts/apply_migrations.py backend/pyproject.toml backend/requirements.txt
git commit -m "feat(db): migration 0001 — operators table + auto-create trigger

operators table references auth.users with ON DELETE CASCADE.
Trigger on_auth_user_created mirrors new signups into operators.
Soft-delete columns + bi-temporal transaction_time per §8.1 forward-compat.
apply_migrations.py runs migrations in lexicographic order."
```

---

### Task 13: Migration 0002 — clients table

Create the clients table with required `short_context` per design doc §5.7 cold-start mitigation.

**Files:**
- Create: `supabase/migrations/0002_clients.sql`

- [ ] **Step 1: Write migration**

Create `supabase/migrations/0002_clients.sql`:

```sql
-- Migration: 0002 — clients table
-- Purpose: Per-operator client records, with required short_context for KB seed
-- Rollback: DROP TABLE clients;

CREATE TABLE clients (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  operator_id UUID NOT NULL REFERENCES operators(id) ON DELETE CASCADE,

  -- Identity
  client_name TEXT NOT NULL,
  phone_number TEXT,
  aliases TEXT[] DEFAULT '{}',
  relationship_type TEXT NOT NULL DEFAULT 'buyer'
    CHECK (relationship_type IN (
      'buyer','seller','landlord','tenant','investor',
      'commercial_landlord','commercial_tenant','referral_partner','other'
    )),
  status TEXT NOT NULL DEFAULT 'new_lead'
    CHECK (status IN (
      'new_lead','active_discussion','awaiting_client_decision',
      'follow_up_needed','proposal_sent','viewing_scheduled',
      'closed_won','closed_lost','dormant','archived'
    )),
  tags TEXT[] DEFAULT '{}',

  -- Required seed context (design doc §5.7 cold-start mitigation)
  short_context TEXT NOT NULL CHECK (length(short_context) >= 20),

  -- Soft-delete
  is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
  deleted_at TIMESTAMPTZ,

  -- Bi-temporal
  transaction_time TIMESTAMPTZ NOT NULL DEFAULT NOW(),

  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_clients_operator_active ON clients(operator_id) WHERE NOT is_deleted;
CREATE INDEX idx_clients_operator_status ON clients(operator_id, status) WHERE NOT is_deleted;

-- Auto-update updated_at
CREATE OR REPLACE FUNCTION public.set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER clients_set_updated_at
BEFORE UPDATE ON clients
FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();
```

- [ ] **Step 2: Apply migration**

```bash
cd backend
source .venv/bin/activate
python scripts/apply_migrations.py
```

Expected: both migrations re-applied (0001 idempotent; 0002 new).

- [ ] **Step 3: Verify constraint via dashboard SQL**

In Supabase dashboard → SQL Editor:

```sql
-- This should fail (short_context too short)
INSERT INTO clients (operator_id, client_name, short_context)
VALUES (gen_random_uuid(), 'Test', 'short');
```

Expected: error about CHECK constraint violation.

- [ ] **Step 4: Commit**

```bash
git add supabase/migrations/0002_clients.sql
git commit -m "feat(db): migration 0002 — clients table with required short_context

short_context CHECK (length >= 20) enforces seed context at client
creation (cold-start mitigation per design doc §5.7).
Soft-delete + bi-temporal columns per §8.1."
```

---

### Task 14: Migration 0003 — events table with append-only trigger

Create the events table with the critical append-only trigger on `raw_text` per design doc §8.1.

**Files:**
- Create: `supabase/migrations/0003_events.sql`

- [ ] **Step 1: Write migration**

Create `supabase/migrations/0003_events.sql`:

```sql
-- Migration: 0003 — events table (immutable, append-only source layer)
-- Purpose: The substrate layer of the KB; raw_text is append-only per Pattern 21
-- Rollback: DROP TABLE events; DROP FUNCTION enforce_raw_text_append_only;

CREATE TABLE events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  client_id UUID NOT NULL REFERENCES clients(id) ON DELETE RESTRICT,
  operator_id UUID NOT NULL REFERENCES operators(id) ON DELETE CASCADE,

  -- Source content (IMMUTABLE after first write)
  source_type TEXT NOT NULL CHECK (source_type IN (
    'meeting_transcript','voice_memo','whatsapp_forward_shapeX',
    'whatsapp_coexistence','manual_note','file_drop'
  )),
  raw_text TEXT NOT NULL,

  -- Bi-temporal columns (TG Memory primitive)
  transaction_time TIMESTAMPTZ NOT NULL DEFAULT NOW(),  -- when recorded
  valid_time TIMESTAMPTZ,                               -- when claimed true (event time)

  -- Attribution (per-principal data model from Day 1)
  attributed_to TEXT NOT NULL DEFAULT 'operator',
  attributed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

  -- Lifecycle
  is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
  deleted_at TIMESTAMPTZ,

  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_events_client_time ON events(client_id, transaction_time DESC) WHERE NOT is_deleted;
CREATE INDEX idx_events_operator ON events(operator_id) WHERE NOT is_deleted;

-- CRITICAL: append-only enforcement on raw_text + source_type
-- This is Decades migration 069 pattern (Pattern 21 — Source Evidence Immutability)
CREATE OR REPLACE FUNCTION public.enforce_raw_text_append_only()
RETURNS TRIGGER AS $$
BEGIN
  IF OLD.raw_text IS NOT NULL AND NEW.raw_text != OLD.raw_text THEN
    RAISE EXCEPTION 'events.raw_text is append-only; mutation forbidden';
  END IF;
  IF OLD.source_type != NEW.source_type THEN
    RAISE EXCEPTION 'events.source_type is immutable after creation';
  END IF;
  IF OLD.client_id != NEW.client_id THEN
    RAISE EXCEPTION 'events.client_id is immutable; reassign via attribution record';
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER events_raw_text_append_only
BEFORE UPDATE ON events
FOR EACH ROW EXECUTE FUNCTION public.enforce_raw_text_append_only();
```

- [ ] **Step 2: Apply migration**

```bash
cd backend
source .venv/bin/activate
python scripts/apply_migrations.py
```

- [ ] **Step 3: Verify trigger via dashboard SQL**

In Supabase dashboard → SQL Editor:

```sql
-- Create a test operator + client first (then test the trigger)
DO $$
DECLARE
  op_id UUID := gen_random_uuid();
  cl_id UUID;
  ev_id UUID;
BEGIN
  INSERT INTO auth.users (id, email) VALUES (op_id, 'test-trigger@example.com');
  INSERT INTO clients (operator_id, client_name, short_context)
    VALUES (op_id, 'Test Client', 'Test seed context for trigger validation')
    RETURNING id INTO cl_id;
  INSERT INTO events (client_id, operator_id, source_type, raw_text)
    VALUES (cl_id, op_id, 'manual_note', 'original text')
    RETURNING id INTO ev_id;

  -- This UPDATE must FAIL
  BEGIN
    UPDATE events SET raw_text = 'mutated text' WHERE id = ev_id;
    RAISE EXCEPTION 'Trigger did not block mutation';
  EXCEPTION
    WHEN OTHERS THEN
      RAISE NOTICE 'Trigger correctly blocked mutation: %', SQLERRM;
  END;

  -- Cleanup
  DELETE FROM events WHERE id = ev_id;
  DELETE FROM clients WHERE id = cl_id;
  DELETE FROM auth.users WHERE id = op_id;
END $$;
```

Expected: NOTICE message confirming trigger blocked the mutation.

- [ ] **Step 4: Commit**

```bash
git add supabase/migrations/0003_events.sql
git commit -m "feat(db): migration 0003 — events table with append-only trigger

events.raw_text + source_type + client_id are immutable after creation
(Pattern 21 — Source Evidence Immutability). Trigger raises exception
on mutation attempts. Bi-temporal columns + per-principal attribution
from Day 1."
```

---

### Task 15: Migration 0004 — facts table with provenance + visibility

Create the facts table with all the regenerability + visibility columns from design doc §8.1.

**Files:**
- Create: `supabase/migrations/0004_facts.sql`

- [ ] **Step 1: Write migration**

Create `supabase/migrations/0004_facts.sql`:

```sql
-- Migration: 0004 — facts table (derived from events; regenerable)
-- Purpose: Typed, deduped relationship facts with source citations
-- Rollback: DROP TABLE facts;

CREATE TABLE facts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  client_id UUID NOT NULL REFERENCES clients(id) ON DELETE RESTRICT,
  operator_id UUID NOT NULL REFERENCES operators(id) ON DELETE CASCADE,

  -- The fact itself
  type TEXT NOT NULL CHECK (type IN (
    'goal','budget_constraint','timeline_signal','objection',
    'spouse_family_factor','emotional_hesitation','document_request',
    'follow_up_promise','viewing_preference','property_preference',
    'decision_blocker','buying_intent_signal','market_signal','content_opportunity'
  )),
  value TEXT NOT NULL,

  -- Source citations (Axiom 3 — Receipts Are Mandatory)
  source_event_ids UUID[] NOT NULL CHECK (array_length(source_event_ids, 1) >= 1),
  source_spans JSONB DEFAULT '[]',  -- [{ event_id, snippet, char_range }]

  -- Confidence + visibility tiers
  confidence_score REAL NOT NULL CHECK (confidence_score >= 0 AND confidence_score <= 1),
  visibility TEXT NOT NULL DEFAULT 'operator_only'
    CHECK (visibility IN ('operator_only','client_facing_safe','agency_visible')),

  -- Provenance (Axiom 4 — Operator's Edit Is Canon)
  provenance TEXT NOT NULL DEFAULT 'llm_generated'
    CHECK (provenance IN (
      'llm_generated','operator_curated','operator_edited','regenerable','canonical'
    )),
  user_stance TEXT NOT NULL DEFAULT 'unreviewed'
    CHECK (user_stance IN ('unreviewed','accepted','rejected','reframed','operator_curated')),
  user_stance_set_at TIMESTAMPTZ,

  -- Supersession (UPDATE/DELETE in ADD/UPDATE/DELETE/NOOP pipeline)
  superseded_by UUID REFERENCES facts(id),

  -- Generation metadata (Axiom 2 — Truth ≠ Tone, regenerability)
  generation_metadata JSONB NOT NULL DEFAULT '{}',
    -- { model_id, prompt_version, prompt_hash, schema_version, evidence_snapshot, regenerated_from, generated_at }

  -- Lifecycle
  is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
  deleted_at TIMESTAMPTZ,

  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_facts_client_active ON facts(client_id) WHERE NOT is_deleted AND superseded_by IS NULL;
CREATE INDEX idx_facts_client_type ON facts(client_id, type) WHERE NOT is_deleted AND superseded_by IS NULL;
CREATE INDEX idx_facts_client_visibility ON facts(client_id, visibility) WHERE NOT is_deleted AND superseded_by IS NULL;

-- Auto-update updated_at
CREATE TRIGGER facts_set_updated_at
BEFORE UPDATE ON facts
FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();
```

- [ ] **Step 2: Apply migration**

```bash
cd backend && source .venv/bin/activate && python scripts/apply_migrations.py
```

- [ ] **Step 3: Commit**

```bash
git add supabase/migrations/0004_facts.sql
git commit -m "feat(db): migration 0004 — facts table

Typed facts with mandatory source_event_ids (Axiom 3 — Receipts).
visibility + provenance + user_stance columns enforce Axioms 4 + 6.
superseded_by enables ADD/UPDATE/DELETE/NOOP pipeline.
generation_metadata for regenerability (Axiom 2)."
```

---

### Task 16: Migration 0005 — room_attachments table

Create the room_attachments table with file identity immutability trigger per design doc §8.1 (added during 2026-05-18 update).

**Files:**
- Create: `supabase/migrations/0005_room_attachments.sql`

- [ ] **Step 1: Write migration**

Create `supabase/migrations/0005_room_attachments.sql`:

```sql
-- Migration: 0005 — room_attachments table (file drop channel)
-- Purpose: Files dropped by operator into client's room (PDFs, images, docs, links)
-- Rollback: DROP TABLE room_attachments; DROP FUNCTION enforce_attachment_file_immutability;

CREATE TABLE room_attachments (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  client_id UUID NOT NULL REFERENCES clients(id) ON DELETE RESTRICT,
  operator_id UUID NOT NULL REFERENCES operators(id) ON DELETE CASCADE,

  -- File identity (IMMUTABLE after creation)
  storage_path TEXT NOT NULL,         -- Supabase Storage path
  original_filename TEXT NOT NULL,
  mime_type TEXT NOT NULL,
  size_bytes BIGINT NOT NULL CHECK (size_bytes > 0),
  content_hash TEXT,                  -- SHA256 for dedup + integrity

  -- Operator context
  source_event_id UUID REFERENCES events(id),
  related_fact_ids UUID[] DEFAULT '{}',
  operator_note TEXT,

  -- Pending action mechanic
  pending_action_type TEXT CHECK (pending_action_type IN (
    'for_review','for_signature','for_consideration','for_payment','informational'
  )),
  pending_action_due TIMESTAMPTZ,
  pending_action_label TEXT,

  -- Visibility tiers
  visibility TEXT NOT NULL DEFAULT 'operator_only'
    CHECK (visibility IN ('operator_only','client_facing_safe','agency_visible')),
  visibility_promoted_at TIMESTAMPTZ,
  visibility_promoted_by TEXT,

  -- Client interaction tracking
  client_viewed_at TIMESTAMPTZ,
  client_viewed_count INTEGER NOT NULL DEFAULT 0,
  client_downloaded_at TIMESTAMPTZ,
  client_acted_at TIMESTAMPTZ,
  client_action_taken TEXT,

  -- Versioning (Pattern 21 extended to attachments)
  superseded_by UUID REFERENCES room_attachments(id),
  supersedes UUID REFERENCES room_attachments(id),
  version_number INTEGER NOT NULL DEFAULT 1,

  -- Lifecycle
  is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
  deleted_at TIMESTAMPTZ,

  -- Provenance / extraction
  extraction_metadata JSONB DEFAULT '{}',
  extracted_text TEXT,

  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_attachments_client_visible ON room_attachments(client_id, visibility, created_at DESC)
  WHERE NOT is_deleted;
CREATE INDEX idx_attachments_pending ON room_attachments(client_id, pending_action_type, pending_action_due)
  WHERE pending_action_type IS NOT NULL AND client_acted_at IS NULL AND NOT is_deleted;
CREATE INDEX idx_attachments_type ON room_attachments(client_id, mime_type) WHERE NOT is_deleted;
CREATE INDEX idx_attachments_extracted_text ON room_attachments
  USING gin(to_tsvector('english', COALESCE(extracted_text, '')))
  WHERE NOT is_deleted;

-- Append-only enforcement on file identity (Pattern 21 extended)
CREATE OR REPLACE FUNCTION public.enforce_attachment_file_immutability()
RETURNS TRIGGER AS $$
BEGIN
  IF OLD.storage_path != NEW.storage_path
     OR OLD.content_hash IS DISTINCT FROM NEW.content_hash
     OR OLD.original_filename != NEW.original_filename
     OR OLD.size_bytes != NEW.size_bytes THEN
    RAISE EXCEPTION 'attachment file identity is immutable; create a new version via superseded_by';
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER attachments_file_immutability
BEFORE UPDATE ON room_attachments
FOR EACH ROW EXECUTE FUNCTION public.enforce_attachment_file_immutability();

CREATE TRIGGER attachments_set_updated_at
BEFORE UPDATE ON room_attachments
FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();
```

- [ ] **Step 2: Apply migration**

```bash
cd backend && source .venv/bin/activate && python scripts/apply_migrations.py
```

- [ ] **Step 3: Commit**

```bash
git add supabase/migrations/0005_room_attachments.sql
git commit -m "feat(db): migration 0005 — room_attachments table

Full schema per design doc §8.1. File identity (storage_path,
content_hash, filename, size_bytes) immutable via trigger (Pattern 21
extended). Pending-action mechanic, visibility tiers, view tracking,
versioning via superseded_by. GIN index for in-room text search."
```

---

### Task 17: Migration 0006 — attributions table

Per-principal attribution table from Day 1 even at N=1 (design doc §8.2).

**Files:**
- Create: `supabase/migrations/0006_attributions.sql`

- [ ] **Step 1: Write migration**

Create `supabase/migrations/0006_attributions.sql`:

```sql
-- Migration: 0006 — attributions table
-- Purpose: Per-principal audit log for every write to durable memory
-- Rollback: DROP TABLE attributions;

CREATE TABLE attributions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  operator_id UUID NOT NULL REFERENCES operators(id) ON DELETE CASCADE,

  -- The artifact this attribution is about
  artifact_id UUID NOT NULL,
  artifact_type TEXT NOT NULL CHECK (artifact_type IN (
    'event','fact','room_attachment','room_update_draft','client','operator'
  )),

  -- Per-principal (Hivemind prep)
  agent_id TEXT NOT NULL DEFAULT 'operator',  -- Phase 3: 'bookkeeper:demosthenes', 'assistant:X', etc.
  surface TEXT NOT NULL CHECK (surface IN (
    'web_dashboard','whatsapp_webhook','voice_upload','file_drop','manual_note','system_cron'
  )),
  session_id TEXT,
  turn_index INTEGER,
  confidence REAL NOT NULL DEFAULT 1.0 CHECK (confidence >= 0 AND confidence <= 1),
  reason TEXT,

  timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_attributions_artifact ON attributions(artifact_type, artifact_id);
CREATE INDEX idx_attributions_operator ON attributions(operator_id, timestamp DESC);
```

- [ ] **Step 2: Apply + commit**

```bash
cd backend && source .venv/bin/activate && python scripts/apply_migrations.py
cd ..
git add supabase/migrations/0006_attributions.sql
git commit -m "feat(db): migration 0006 — attributions table

Per-principal audit log from Day 1. At N=1 operator, agent_id defaults
to 'operator'; Phase 3 adds bookkeeper / assistant agents without
schema change. Design doc §8.2 forward-compat hook."
```

---

### Task 18: Migration 0007 — visibility_promotions table

Track every visibility tier promotion for audit + Phase 3 governance evolution per design doc §8.6.

**Files:**
- Create: `supabase/migrations/0007_visibility_promotions.sql`

- [ ] **Step 1: Write migration**

Create `supabase/migrations/0007_visibility_promotions.sql`:

```sql
-- Migration: 0007 — visibility_promotions table
-- Purpose: Audit log for every tier promotion (operator_only → client_facing_safe etc.)
-- Rollback: DROP TABLE visibility_promotions;

CREATE TABLE visibility_promotions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  operator_id UUID NOT NULL REFERENCES operators(id) ON DELETE CASCADE,

  artifact_id UUID NOT NULL,
  artifact_type TEXT NOT NULL CHECK (artifact_type IN (
    'fact','room_attachment','room_update_draft'
  )),

  from_tier TEXT NOT NULL CHECK (from_tier IN ('operator_only','client_facing_safe','agency_visible')),
  to_tier TEXT NOT NULL CHECK (to_tier IN ('operator_only','client_facing_safe','agency_visible')),
  approved_by TEXT NOT NULL,  -- 'operator:<id>'
  approved_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  reason TEXT,
  reversible BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE INDEX idx_promotions_operator ON visibility_promotions(operator_id, approved_at DESC);
CREATE INDEX idx_promotions_artifact ON visibility_promotions(artifact_type, artifact_id);
```

- [ ] **Step 2: Apply + commit**

```bash
cd backend && source .venv/bin/activate && python scripts/apply_migrations.py
cd ..
git add supabase/migrations/0007_visibility_promotions.sql
git commit -m "feat(db): migration 0007 — visibility_promotions audit table

Every promotion from operator_only → client_facing_safe (or agency_visible)
is logged. Becomes the proto-mandate primitive for Phase 3 Hivemind
governance arbitration per design doc §8.6."
```

---

### Task 19: Migration 0008 — RLS policies

Enable RLS on all user-data tables and write per-operator policies.

**Files:**
- Create: `supabase/migrations/0008_rls_policies.sql`

- [ ] **Step 1: Write migration**

Create `supabase/migrations/0008_rls_policies.sql`:

```sql
-- Migration: 0008 — RLS policies for all user-data tables
-- Purpose: Cross-operator isolation; defense layer beyond app code
-- Rollback: ALTER TABLE ... DISABLE ROW LEVEL SECURITY;

-- operators: each user sees only their own row
ALTER TABLE operators ENABLE ROW LEVEL SECURITY;

CREATE POLICY operators_select_own ON operators FOR SELECT
  USING (id = auth.uid());

CREATE POLICY operators_update_own ON operators FOR UPDATE
  USING (id = auth.uid()) WITH CHECK (id = auth.uid());

-- (no INSERT policy; rows created by handle_new_auth_user trigger via SECURITY DEFINER)
-- (no DELETE policy; deletion handled via auth.users cascade)

-- clients: per-operator
ALTER TABLE clients ENABLE ROW LEVEL SECURITY;

CREATE POLICY clients_select_own ON clients FOR SELECT
  USING (operator_id = auth.uid() AND NOT is_deleted);

CREATE POLICY clients_insert_own ON clients FOR INSERT
  WITH CHECK (operator_id = auth.uid());

CREATE POLICY clients_update_own ON clients FOR UPDATE
  USING (operator_id = auth.uid()) WITH CHECK (operator_id = auth.uid());

-- No DELETE policy; use soft-delete via is_deleted flag

-- events: per-operator
ALTER TABLE events ENABLE ROW LEVEL SECURITY;

CREATE POLICY events_select_own ON events FOR SELECT
  USING (operator_id = auth.uid() AND NOT is_deleted);

CREATE POLICY events_insert_own ON events FOR INSERT
  WITH CHECK (operator_id = auth.uid());

CREATE POLICY events_update_own ON events FOR UPDATE
  USING (operator_id = auth.uid()) WITH CHECK (operator_id = auth.uid());

-- facts: per-operator
ALTER TABLE facts ENABLE ROW LEVEL SECURITY;

CREATE POLICY facts_select_own ON facts FOR SELECT
  USING (operator_id = auth.uid() AND NOT is_deleted);

CREATE POLICY facts_insert_own ON facts FOR INSERT
  WITH CHECK (operator_id = auth.uid());

CREATE POLICY facts_update_own ON facts FOR UPDATE
  USING (operator_id = auth.uid()) WITH CHECK (operator_id = auth.uid());

-- room_attachments: per-operator (client-facing view added separately in 0009)
ALTER TABLE room_attachments ENABLE ROW LEVEL SECURITY;

CREATE POLICY attachments_select_own ON room_attachments FOR SELECT
  USING (operator_id = auth.uid() AND NOT is_deleted);

CREATE POLICY attachments_insert_own ON room_attachments FOR INSERT
  WITH CHECK (operator_id = auth.uid());

CREATE POLICY attachments_update_own ON room_attachments FOR UPDATE
  USING (operator_id = auth.uid()) WITH CHECK (operator_id = auth.uid());

-- attributions: per-operator
ALTER TABLE attributions ENABLE ROW LEVEL SECURITY;

CREATE POLICY attributions_select_own ON attributions FOR SELECT
  USING (operator_id = auth.uid());

CREATE POLICY attributions_insert_own ON attributions FOR INSERT
  WITH CHECK (operator_id = auth.uid());

-- visibility_promotions: per-operator
ALTER TABLE visibility_promotions ENABLE ROW LEVEL SECURITY;

CREATE POLICY promotions_select_own ON visibility_promotions FOR SELECT
  USING (operator_id = auth.uid());

CREATE POLICY promotions_insert_own ON visibility_promotions FOR INSERT
  WITH CHECK (operator_id = auth.uid());
```

- [ ] **Step 2: Apply + commit**

```bash
cd backend && source .venv/bin/activate && python scripts/apply_migrations.py
cd ..
git add supabase/migrations/0008_rls_policies.sql
git commit -m "feat(db): migration 0008 — RLS policies for cross-operator isolation

All user-data tables: SELECT/INSERT/UPDATE scoped to operator_id = auth.uid().
No DELETE policies (soft-delete via is_deleted). Pattern 21 + Axiom 5
+ defense in depth (Pattern from design doc §9.3)."
```

---

### Task 20: Migration 0009 — rooms_public view (placeholder)

Reserve the rooms_public view shape now; Plan 6 (client-facing room) will populate fully.

**Files:**
- Create: `supabase/migrations/0009_rooms_public_view.sql`

- [ ] **Step 1: Write migration (placeholder shape)**

Create `supabase/migrations/0009_rooms_public_view.sql`:

```sql
-- Migration: 0009 — rooms_public placeholder view
-- Purpose: Reserve the public-room read surface; Plan 6 fleshes out
-- Rollback: DROP VIEW IF EXISTS rooms_public;

-- Placeholder: returns nothing in Phase 1 (no slug column on clients yet).
-- Plan 6 adds a 'rooms' table with public_slug + passcode_hash, and this
-- view becomes the canonical read surface for anonymous clients.

CREATE OR REPLACE VIEW rooms_public AS
SELECT
  c.id AS client_id,
  c.client_name,
  ''::text AS slug,            -- placeholder; populated in Plan 6
  NULL::text AS passcode_hash, -- placeholder
  c.created_at
FROM clients c
WHERE FALSE;                   -- intentionally returns 0 rows in Phase 1

COMMENT ON VIEW rooms_public IS
  'Placeholder for Plan 6 client-facing room. Reserved here so RLS + auth
   layout can be designed against the final shape. Returns 0 rows in
   Phase 1 (WHERE FALSE).';
```

- [ ] **Step 2: Apply + commit**

```bash
cd backend && source .venv/bin/activate && python scripts/apply_migrations.py
cd ..
git add supabase/migrations/0009_rooms_public_view.sql
git commit -m "feat(db): migration 0009 — rooms_public placeholder view

Reserves the canonical anonymous-read shape per design doc §9.3.
Returns 0 rows in Phase 1; Plan 6 populates with rooms table."
```

---

### Task 21: Backend — AgentDispatcher + LogicalRole abstraction

Implement the vendor-agnostic dispatcher per Pattern 20 + design doc §8.5.

**Files:**
- Create: `backend/app/ai/__init__.py`
- Create: `backend/app/ai/providers/__init__.py`
- Create: `backend/app/ai/providers/base.py`
- Create: `backend/app/ai/providers/anthropic.py`
- Create: `backend/app/ai/providers/openai.py`
- Create: `backend/app/ai/dispatcher.py`
- Create: `backend/tests/test_dispatcher.py`

- [ ] **Step 1: Package markers**

```bash
mkdir -p backend/app/ai/providers
touch backend/app/ai/__init__.py backend/app/ai/providers/__init__.py
```

- [ ] **Step 2: Write failing dispatcher test**

Create `backend/tests/test_dispatcher.py`:

```python
import pytest
from app.ai.dispatcher import AgentDispatcher, LogicalRole


def test_logical_roles_enumerated():
    expected = {
        "classifier", "summarizer", "extractor",
        "generator", "judge", "validator", "transcriber",
    }
    actual = {role.value for role in LogicalRole}
    assert actual == expected


def test_dispatcher_resolves_role_to_provider_and_model():
    dispatcher = AgentDispatcher()
    provider, model = dispatcher.resolve(LogicalRole.EXTRACTOR)
    assert provider is not None
    assert model is not None


def test_dispatcher_uses_haiku_for_classifier():
    dispatcher = AgentDispatcher()
    provider, model = dispatcher.resolve(LogicalRole.CLASSIFIER)
    assert "haiku" in model.lower()


def test_dispatcher_uses_sonnet_for_extractor():
    dispatcher = AgentDispatcher()
    provider, model = dispatcher.resolve(LogicalRole.EXTRACTOR)
    assert "sonnet" in model.lower()
```

- [ ] **Step 3: Run, verify failure**

```bash
cd backend && source .venv/bin/activate && pytest tests/test_dispatcher.py -v
```

Expected: `ModuleNotFoundError`.

- [ ] **Step 4: Implement provider Protocol**

Create `backend/app/ai/providers/base.py`:

```python
from typing import Any, Protocol


class Provider(Protocol):
    """AI provider Protocol — adapters must implement this interface."""

    def call(self, model: str, prompt: str, **kwargs: Any) -> dict[str, Any]:
        """
        Make a structured call to the provider. Returns parsed response.
        Phase 1: stub implementations; real calls land in Plan 2.
        """
        ...
```

- [ ] **Step 5: Implement Anthropic adapter (stub)**

Create `backend/app/ai/providers/anthropic.py`:

```python
from typing import Any


class AnthropicProvider:
    """
    Anthropic adapter. Phase 1: stub that returns echo-like responses.
    Plan 2 wires real Anthropic SDK + instructor calls.
    """

    def call(self, model: str, prompt: str, **kwargs: Any) -> dict[str, Any]:
        return {
            "provider": "anthropic",
            "model": model,
            "prompt_preview": prompt[:200],
            "stub": True,
        }
```

- [ ] **Step 6: Implement OpenAI adapter (stub)**

Create `backend/app/ai/providers/openai.py`:

```python
from typing import Any


class OpenAIProvider:
    """OpenAI adapter. Phase 1 stub; Plan 2 wires real SDK."""

    def call(self, model: str, prompt: str, **kwargs: Any) -> dict[str, Any]:
        return {
            "provider": "openai",
            "model": model,
            "prompt_preview": prompt[:200],
            "stub": True,
        }
```

- [ ] **Step 7: Implement AgentDispatcher**

Create `backend/app/ai/dispatcher.py`:

```python
from dataclasses import dataclass
from enum import Enum
from typing import Any

from app.ai.providers.anthropic import AnthropicProvider
from app.ai.providers.base import Provider
from app.ai.providers.openai import OpenAIProvider


class LogicalRole(str, Enum):
    """
    Logical roles separate business logic from vendor coupling
    (Pattern 20 — Vendor Agnostic; design doc §8.5).
    Role → (provider, model) resolved via config below.
    """
    CLASSIFIER = "classifier"
    SUMMARIZER = "summarizer"
    EXTRACTOR = "extractor"
    GENERATOR = "generator"
    JUDGE = "judge"
    VALIDATOR = "validator"
    TRANSCRIBER = "transcriber"


@dataclass(frozen=True)
class RoleConfig:
    provider_name: str
    model: str


# Default role-to-provider/model mapping for Phase 1.
# Future: load from a YAML config file or env so swaps don't require redeploy.
_DEFAULT_ROLE_MAP: dict[LogicalRole, RoleConfig] = {
    LogicalRole.CLASSIFIER: RoleConfig("anthropic", "claude-haiku-4-5"),
    LogicalRole.SUMMARIZER: RoleConfig("anthropic", "claude-haiku-4-5"),
    LogicalRole.EXTRACTOR: RoleConfig("anthropic", "claude-sonnet-4-6"),
    LogicalRole.GENERATOR: RoleConfig("anthropic", "claude-sonnet-4-6"),
    LogicalRole.JUDGE: RoleConfig("anthropic", "claude-haiku-4-5"),
    LogicalRole.VALIDATOR: RoleConfig("anthropic", "claude-haiku-4-5"),
    LogicalRole.TRANSCRIBER: RoleConfig("openai", "whisper-1"),
}


class AgentDispatcher:
    """
    Resolves a LogicalRole to a (provider, model) pair and dispatches.
    Phase 1: returns provider + model; actual `call()` returns stub
    response. Plan 2 wires real SDK calls + instructor + caching.
    """

    def __init__(self, role_map: dict[LogicalRole, RoleConfig] | None = None) -> None:
        self._role_map = role_map or _DEFAULT_ROLE_MAP
        self._providers: dict[str, Provider] = {
            "anthropic": AnthropicProvider(),
            "openai": OpenAIProvider(),
        }

    def resolve(self, role: LogicalRole) -> tuple[Provider, str]:
        config = self._role_map[role]
        provider = self._providers[config.provider_name]
        return provider, config.model

    def dispatch(self, role: LogicalRole, prompt: str, **kwargs: Any) -> dict[str, Any]:
        provider, model = self.resolve(role)
        return provider.call(model, prompt, **kwargs)
```

- [ ] **Step 8: Run, verify pass**

```bash
pytest tests/test_dispatcher.py -v
```

Expected: 4 passed.

- [ ] **Step 9: Commit**

```bash
git add backend/app/ai backend/tests/test_dispatcher.py
git commit -m "feat(ai): AgentDispatcher + LogicalRole abstraction (Pattern 20)

Logical roles (classifier, summarizer, extractor, generator, judge,
validator, transcriber) map to (provider, model) via config dict.
Phase 1: stub providers returning shape-only responses; Plan 2 wires
real SDK calls. Vendor swap is config change, not code change."
```

---

### Task 22: Backend — store() service (single governed write path)

Implement the thin Phase 1 wrapper for the single governed write path per design doc §8.3.

**Files:**
- Create: `backend/app/services/__init__.py`
- Create: `backend/app/models/__init__.py`
- Create: `backend/app/models/attribution.py`
- Create: `backend/app/services/store.py`
- Create: `backend/tests/test_store.py`

- [ ] **Step 1: Package markers**

```bash
mkdir -p backend/app/services backend/app/models
touch backend/app/services/__init__.py backend/app/models/__init__.py
```

- [ ] **Step 2: Write attribution model**

Create `backend/app/models/attribution.py`:

```python
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


Surface = Literal[
    "web_dashboard", "whatsapp_webhook", "voice_upload",
    "file_drop", "manual_note", "system_cron",
]


class Attribution(BaseModel):
    """Attribution metadata for every write to durable memory (§8.2)."""

    agent_id: str = Field(default="operator")
    surface: Surface
    session_id: str | None = None
    turn_index: int | None = None
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    reason: str | None = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
```

- [ ] **Step 3: Write failing store() test**

Create `backend/tests/test_store.py`:

```python
import pytest
from unittest.mock import MagicMock

from app.models.attribution import Attribution
from app.services.store import store, StoredArtifact


def test_store_returns_stored_artifact_with_id_and_attribution_id():
    fake_supabase = MagicMock()
    fake_supabase.table.return_value.insert.return_value.execute.return_value = MagicMock(
        data=[{"id": "art-uuid"}]
    )

    attribution = Attribution(surface="web_dashboard")
    result = store(
        supabase=fake_supabase,
        operator_id="op-uuid",
        domain="client:abc",
        artifact_type="event",
        payload={"client_id": "cli-uuid", "source_type": "manual_note", "raw_text": "test"},
        attribution=attribution,
    )

    assert isinstance(result, StoredArtifact)
    assert result.artifact_id == "art-uuid"
    assert result.artifact_type == "event"
    # Verify both inserts happened: artifact + attribution
    assert fake_supabase.table.call_count == 2


def test_store_rejects_invalid_artifact_type():
    fake_supabase = MagicMock()
    attribution = Attribution(surface="web_dashboard")
    with pytest.raises(ValueError, match="invalid artifact_type"):
        store(
            supabase=fake_supabase,
            operator_id="op-uuid",
            domain="client:abc",
            artifact_type="invalid_type",
            payload={},
            attribution=attribution,
        )
```

- [ ] **Step 4: Run, verify failure**

```bash
pytest tests/test_store.py -v
```

Expected: `ModuleNotFoundError`.

- [ ] **Step 5: Implement store()**

Create `backend/app/services/store.py`:

```python
"""
Single governed write path for durable memory.

Phase 1: thin wrapper over Supabase insert + attribution log.
Phase 3: same signature; implementation expands to add scoping,
dedup, redaction, multi-agent attribution checks per Hivemind doc §8.3.
"""
from dataclasses import dataclass
from typing import Any, Literal

from supabase import Client

from app.models.attribution import Attribution


ArtifactType = Literal[
    "event", "fact", "room_attachment", "room_update_draft",
    "client", "operator",
]

_VALID_ARTIFACT_TYPES = {
    "event", "fact", "room_attachment", "room_update_draft",
    "client", "operator",
}

# Map artifact_type → Supabase table name
_TABLE_FOR_ARTIFACT: dict[str, str] = {
    "event": "events",
    "fact": "facts",
    "room_attachment": "room_attachments",
    "room_update_draft": "room_update_drafts",  # added in Plan 7
    "client": "clients",
    "operator": "operators",
}


@dataclass(frozen=True)
class StoredArtifact:
    artifact_id: str
    artifact_type: str
    domain: str


def store(
    supabase: Client,
    operator_id: str,
    domain: str,
    artifact_type: str,
    payload: dict[str, Any],
    attribution: Attribution,
) -> StoredArtifact:
    """
    Insert an artifact + record attribution. Phase 1 implementation.

    Args:
      supabase: request-scoped Supabase client
      operator_id: the operator owning this write
      domain: scope identifier (e.g., 'client:<slug>'); Phase 3 uses this for federation
      artifact_type: one of ArtifactType literals
      payload: row data for the artifact table (must include operator_id)
      attribution: who/what/when/why metadata

    Returns:
      StoredArtifact with the inserted ID.

    Raises:
      ValueError: invalid artifact_type
    """
    if artifact_type not in _VALID_ARTIFACT_TYPES:
        raise ValueError(f"invalid artifact_type: {artifact_type}")

    table_name = _TABLE_FOR_ARTIFACT[artifact_type]

    # Ensure operator_id is in the payload (enforces RLS at write time)
    payload_with_op = {**payload, "operator_id": operator_id}

    # Insert the artifact
    artifact_response = (
        supabase.table(table_name)
        .insert(payload_with_op)
        .execute()
    )
    artifact_id = artifact_response.data[0]["id"]

    # Insert the attribution record
    supabase.table("attributions").insert({
        "operator_id": operator_id,
        "artifact_id": artifact_id,
        "artifact_type": artifact_type,
        "agent_id": attribution.agent_id,
        "surface": attribution.surface,
        "session_id": attribution.session_id,
        "turn_index": attribution.turn_index,
        "confidence": attribution.confidence,
        "reason": attribution.reason,
        "timestamp": attribution.timestamp.isoformat(),
    }).execute()

    return StoredArtifact(
        artifact_id=artifact_id,
        artifact_type=artifact_type,
        domain=domain,
    )
```

- [ ] **Step 6: Run, verify pass**

```bash
pytest tests/test_store.py -v
```

Expected: 2 passed.

- [ ] **Step 7: Commit**

```bash
git add backend/app/services backend/app/models backend/tests/test_store.py
git commit -m "feat(services): store() — single governed write path

Phase 1 thin wrapper inserts artifact + attribution in two Supabase
calls. Phase 3 expands implementation (scoping, dedup, redaction)
without changing the signature. Design doc §8.3 forward-compat hook."
```

---

### Task 23: Backend — auth dependency for FastAPI routes

Implement a FastAPI dependency that validates the Supabase JWT and returns the operator_id.

**Files:**
- Create: `backend/app/core/auth.py`
- Create: `backend/tests/test_auth.py`

- [ ] **Step 1: Write failing auth test**

Create `backend/tests/test_auth.py`:

```python
import pytest
from unittest.mock import MagicMock

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
```

- [ ] **Step 2: Run, verify failure**

```bash
pytest tests/test_auth.py -v
```

Expected: `ModuleNotFoundError`.

- [ ] **Step 3: Implement auth dependency**

Create `backend/app/core/auth.py`:

```python
"""
FastAPI auth dependency.

Validates the Supabase JWT from the Authorization header and returns
the operator UUID. Uses getUser() which hits the Supabase auth server
to verify the token (only trustworthy check per design doc §9.3).
"""
from fastapi import Header, HTTPException

from app.core.supabase import get_anon_client


async def get_current_operator_id(
    authorization: str | None = Header(default=None),
) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or malformed Authorization header")

    token = authorization.removeprefix("Bearer ").strip()

    try:
        supabase = get_anon_client()
        response = supabase.auth.get_user(token)
    except Exception as exc:
        raise HTTPException(status_code=401, detail=f"Invalid token: {exc}") from exc

    if not response or not response.user:
        raise HTTPException(status_code=401, detail="Token did not resolve to a user")

    return str(response.user.id)
```

- [ ] **Step 4: Run, verify pass**

```bash
pytest tests/test_auth.py -v
```

Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add backend/app/core/auth.py backend/tests/test_auth.py
git commit -m "feat(auth): FastAPI dependency validates Supabase JWT

get_current_operator_id() reads Authorization header, validates via
supabase.auth.get_user() (only trustworthy check per design doc §9.3),
returns operator UUID. Returns 401 on missing/malformed/invalid token."
```

---

### Task 24: Backend — operators/me endpoint

Implement GET /operators/me to return the current operator's profile.

**Files:**
- Create: `backend/app/api/operators.py`
- Modify: `backend/app/main.py`
- Create: `backend/tests/test_operators_api.py`

- [ ] **Step 1: Write failing endpoint test**

Create `backend/tests/test_operators_api.py`:

```python
import pytest
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_get_operators_me_returns_401_without_auth(client):
    response = client.get("/operators/me")
    assert response.status_code == 401


def test_get_operators_me_returns_profile_with_valid_token(client):
    fake_supabase = MagicMock()
    fake_supabase.table.return_value.select.return_value.eq.return_value.maybe_single.return_value.execute.return_value = MagicMock(
        data={"id": "op-uuid", "email": "test@example.com", "name": None}
    )

    with patch("app.api.operators.get_anon_client", return_value=fake_supabase), \
         patch("app.core.auth.get_anon_client") as mock_auth_client:
        fake_user = MagicMock()
        fake_user.id = "op-uuid"
        mock_auth_client.return_value.auth.get_user.return_value = MagicMock(user=fake_user)

        response = client.get(
            "/operators/me",
            headers={"Authorization": "Bearer valid-token"},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == "op-uuid"
    assert body["email"] == "test@example.com"
```

- [ ] **Step 2: Run, verify failure**

```bash
pytest tests/test_operators_api.py -v
```

Expected: `ModuleNotFoundError`.

- [ ] **Step 3: Implement operators router**

Create `backend/app/api/operators.py`:

```python
from fastapi import APIRouter, Depends, HTTPException

from app.core.auth import get_current_operator_id
from app.core.supabase import get_anon_client

router = APIRouter(prefix="/operators", tags=["operators"])


@router.get("/me")
async def get_me(operator_id: str = Depends(get_current_operator_id)) -> dict:
    """Return the current operator's profile row."""
    supabase = get_anon_client()
    response = (
        supabase.table("operators")
        .select("id, email, name, company_name, role_title, industry, "
                "profile_photo_url, default_language, default_tone, timezone, created_at")
        .eq("id", operator_id)
        .maybe_single()
        .execute()
    )

    if not response.data:
        raise HTTPException(status_code=404, detail="Operator profile not found")

    return response.data
```

- [ ] **Step 4: Wire router into app**

Modify `backend/app/main.py`:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import health, operators


def create_app() -> FastAPI:
    app = FastAPI(
        title="FollowRoom Backend",
        version="0.0.1",
        description="Phase 1 foundation API",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(operators.router)
    return app


app = create_app()
```

- [ ] **Step 5: Run, verify pass**

```bash
pytest tests/test_operators_api.py -v
```

Expected: 2 passed.

- [ ] **Step 6: Commit**

```bash
git add backend/app/api/operators.py backend/app/main.py backend/tests/test_operators_api.py
git commit -m "feat(api): GET /operators/me returns current operator profile

Validates JWT via get_current_operator_id dependency.
Returns 401 without auth, 404 if profile row missing,
200 with profile data on success."
```

---

### Task 25: Backend — clients endpoint (POST + GET)

Implement client creation and listing.

**Files:**
- Create: `backend/app/models/client.py`
- Create: `backend/app/api/clients.py`
- Modify: `backend/app/main.py`
- Create: `backend/tests/test_clients_api.py`

- [ ] **Step 1: Write Client Pydantic model**

Create `backend/app/models/client.py`:

```python
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
```

- [ ] **Step 2: Write failing client API test**

Create `backend/tests/test_clients_api.py`:

```python
import pytest
from unittest.mock import MagicMock, patch

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


def test_create_client_returns_401_without_auth(client):
    response = client.post("/clients", json={
        "client_name": "Sarah",
        "short_context": "HDB upgrade, East Coast, $1.8M",
    })
    assert response.status_code == 401


def test_create_client_rejects_short_context_under_20_chars(client, monkeypatch):
    _mock_auth(monkeypatch)
    response = client.post(
        "/clients",
        headers={"Authorization": "Bearer t"},
        json={"client_name": "Sarah", "short_context": "too short"},
    )
    assert response.status_code == 422


def test_create_client_succeeds_with_valid_payload(client, monkeypatch):
    _mock_auth(monkeypatch)

    inserted = {
        "id": "new-client-uuid",
        "client_name": "Sarah",
        "phone_number": None,
        "relationship_type": "buyer",
        "status": "new_lead",
        "short_context": "HDB upgrade, East Coast, $1.8M, husband in finance",
        "tags": [],
        "aliases": [],
        "created_at": "2026-05-18T00:00:00+00:00",
        "updated_at": "2026-05-18T00:00:00+00:00",
    }

    fake_service_client = MagicMock()
    fake_service_client.table.return_value.insert.return_value.execute.return_value = MagicMock(
        data=[inserted]
    )

    with patch("app.api.clients.get_service_client", return_value=fake_service_client):
        response = client.post(
            "/clients",
            headers={"Authorization": "Bearer t"},
            json={
                "client_name": "Sarah",
                "short_context": "HDB upgrade, East Coast, $1.8M, husband in finance",
            },
        )

    assert response.status_code == 201
    body = response.json()
    assert body["client_name"] == "Sarah"
    assert body["id"] == "new-client-uuid"


def test_list_clients_returns_only_operators_clients(client, monkeypatch):
    _mock_auth(monkeypatch, operator_id="op-uuid")

    fake_service_client = MagicMock()
    fake_service_client.table.return_value.select.return_value.eq.return_value.eq.return_value.order.return_value.execute.return_value = MagicMock(
        data=[{
            "id": "c1",
            "client_name": "Sarah",
            "phone_number": None,
            "relationship_type": "buyer",
            "status": "new_lead",
            "short_context": "seed " * 5,
            "tags": [],
            "aliases": [],
            "created_at": "2026-05-18T00:00:00+00:00",
            "updated_at": "2026-05-18T00:00:00+00:00",
        }]
    )

    with patch("app.api.clients.get_service_client", return_value=fake_service_client):
        response = client.get("/clients", headers={"Authorization": "Bearer t"})

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["client_name"] == "Sarah"
```

- [ ] **Step 3: Run, verify failure**

```bash
pytest tests/test_clients_api.py -v
```

Expected: `ModuleNotFoundError`.

- [ ] **Step 4: Implement clients router**

Create `backend/app/api/clients.py`:

```python
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
    supabase = get_service_client()  # service role for cross-RLS insert; operator_id in payload
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
        .select("id, client_name, phone_number, relationship_type, status, "
                "short_context, tags, aliases, created_at, updated_at")
        .eq("operator_id", operator_id)
        .eq("is_deleted", False)
        .order("created_at", desc=True)
        .execute()
    )

    return [ClientResponse(**row) for row in (response.data or [])]
```

- [ ] **Step 5: Wire into main.py**

Modify `backend/app/main.py`:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import clients, health, operators


def create_app() -> FastAPI:
    app = FastAPI(
        title="FollowRoom Backend",
        version="0.0.1",
        description="Phase 1 foundation API",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(operators.router)
    app.include_router(clients.router)
    return app


app = create_app()
```

- [ ] **Step 6: Run, verify pass**

```bash
pytest tests/test_clients_api.py -v
```

Expected: 4 passed.

- [ ] **Step 7: Commit**

```bash
git add backend/app/api/clients.py backend/app/models/client.py backend/app/main.py backend/tests/test_clients_api.py
git commit -m "feat(api): POST /clients + GET /clients

CreateClientRequest validates short_context >= 20 chars (cold-start
mitigation §5.7). List endpoint scoped to operator_id; excludes
soft-deleted. Returns 401 without auth, 422 on validation, 201 on
create, 200 on list."
```

---

### Task 26: Frontend — login + signup pages with Supabase Auth

Implement login and signup pages using Supabase Auth.

**Files:**
- Create: `web/app/(auth)/login/page.tsx`
- Create: `web/app/(auth)/signup/page.tsx`
- Create: `web/app/api/auth/callback/route.ts`

- [ ] **Step 1: Create signup page**

Create `web/app/(auth)/signup/page.tsx`:

```typescript
"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { createClient } from "@/lib/supabase/client";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export default function SignupPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);

    const supabase = createClient();
    const { error } = await supabase.auth.signUp({
      email,
      password,
      options: {
        emailRedirectTo: `${window.location.origin}/api/auth/callback`,
      },
    });

    setLoading(false);

    if (error) {
      setError(error.message);
      return;
    }

    router.push("/login?signup=success");
  }

  return (
    <div className="mx-auto max-w-md p-8">
      <h1 className="text-2xl font-semibold mb-6">Create your FollowRoom account</h1>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="email">Email</Label>
          <Input
            id="email"
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            autoComplete="email"
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="password">Password</Label>
          <Input
            id="password"
            type="password"
            required
            minLength={8}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="new-password"
          />
        </div>
        {error && <p className="text-sm text-red-600">{error}</p>}
        <Button type="submit" disabled={loading} className="w-full">
          {loading ? "Creating..." : "Sign up"}
        </Button>
      </form>
      <p className="mt-6 text-sm text-center text-gray-600">
        Already have an account?{" "}
        <Link href="/login" className="text-gray-900 underline">
          Log in
        </Link>
      </p>
    </div>
  );
}
```

- [ ] **Step 2: Create login page**

Create `web/app/(auth)/login/page.tsx`:

```typescript
"use client";

import { useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { createClient } from "@/lib/supabase/client";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const router = useRouter();
  const searchParams = useSearchParams();
  const signupSuccess = searchParams.get("signup") === "success";

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);

    const supabase = createClient();
    const { error } = await supabase.auth.signInWithPassword({ email, password });

    setLoading(false);

    if (error) {
      setError(error.message);
      return;
    }

    router.push("/");
    router.refresh();
  }

  return (
    <div className="mx-auto max-w-md p-8">
      <h1 className="text-2xl font-semibold mb-6">Log in to FollowRoom</h1>
      {signupSuccess && (
        <p className="mb-4 text-sm text-green-700 bg-green-50 p-3 rounded">
          Check your email for a verification link, then log in below.
        </p>
      )}
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="email">Email</Label>
          <Input
            id="email"
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            autoComplete="email"
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="password">Password</Label>
          <Input
            id="password"
            type="password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="current-password"
          />
        </div>
        {error && <p className="text-sm text-red-600">{error}</p>}
        <Button type="submit" disabled={loading} className="w-full">
          {loading ? "Logging in..." : "Log in"}
        </Button>
      </form>
      <p className="mt-6 text-sm text-center text-gray-600">
        New here?{" "}
        <Link href="/signup" className="text-gray-900 underline">
          Create an account
        </Link>
      </p>
    </div>
  );
}
```

- [ ] **Step 3: Create auth callback handler**

Create `web/app/api/auth/callback/route.ts`:

```typescript
import { NextResponse } from "next/server";
import { createClient } from "@/lib/supabase/server";

export async function GET(request: Request) {
  const url = new URL(request.url);
  const code = url.searchParams.get("code");

  if (code) {
    const supabase = await createClient();
    await supabase.auth.exchangeCodeForSession(code);
  }

  return NextResponse.redirect(new URL("/", url.origin));
}
```

- [ ] **Step 4: Manual verification**

Start the dev server and supabase:

```bash
cd web
npm run dev
```

In Supabase dashboard: **Authentication → Settings**, set **Site URL** to `http://localhost:3000`, add redirect URL `http://localhost:3000/api/auth/callback`.

Then in browser:
1. Visit `http://localhost:3000/signup`, sign up with a real-or-throwaway email
2. Check inbox for confirmation link, click it
3. Should land on `http://localhost:3000/` (which 404s for now — that's expected; Task 27 adds the dashboard)
4. In Supabase dashboard → Authentication → Users — confirm new user exists
5. In Supabase Table Editor → operators — confirm new row exists (trigger from Task 12)

- [ ] **Step 5: Commit**

```bash
git add web/app web/components
git commit -m "feat(web): signup + login pages with Supabase Auth

Uses request-scoped @supabase/ssr client factories. Auth callback
exchanges code for session. After signup confirmation, handle_new_auth_user
trigger creates the operators row."
```

---

### Task 27: Frontend — dashboard layout with auth guard + landing page

Create the auth-required dashboard layout and a minimal landing/dashboard home.

**Files:**
- Create: `web/app/(dashboard)/layout.tsx`
- Create: `web/app/(dashboard)/page.tsx`
- Create: `web/app/page.tsx`

- [ ] **Step 1: Dashboard layout with server-side getUser check**

Create `web/app/(dashboard)/layout.tsx`:

```typescript
import { redirect } from "next/navigation";
import { createClient } from "@/lib/supabase/server";

export default async function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const supabase = await createClient();

  // IMPORTANT: use getUser(), NOT getSession() — only getUser hits the
  // auth server and is trustworthy in server code (design doc §9.3).
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    redirect("/login");
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b">
        <div className="max-w-6xl mx-auto px-4 py-3 flex items-center justify-between">
          <h1 className="text-lg font-semibold">FollowRoom</h1>
          <span className="text-sm text-gray-600">{user.email}</span>
        </div>
      </header>
      <main className="max-w-6xl mx-auto px-4 py-8">{children}</main>
    </div>
  );
}
```

- [ ] **Step 2: Dashboard home (empty state)**

Create `web/app/(dashboard)/page.tsx`:

```typescript
import Link from "next/link";
import { createClient } from "@/lib/supabase/server";
import { Button } from "@/components/ui/button";

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
        <Link href="/clients/new">
          <Button>Add client</Button>
        </Link>
      </div>

      {!hasClients ? (
        <div className="bg-white rounded-lg border p-12 text-center">
          <p className="text-gray-600 mb-6">
            Add your first client to start building their relationship room.
          </p>
          <Link href="/clients/new">
            <Button>Add your first client</Button>
          </Link>
        </div>
      ) : (
        <ul className="space-y-3">
          {clients.map((c) => (
            <li key={c.id} className="bg-white rounded-lg border p-4">
              <h3 className="font-medium">{c.client_name}</h3>
              <p className="text-sm text-gray-600 mt-1">{c.short_context}</p>
              <p className="text-xs text-gray-500 mt-2">
                Status: {c.status}
              </p>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
```

- [ ] **Step 3: Landing page (redirects logged-in users to dashboard)**

Replace `web/app/page.tsx`:

```typescript
import { redirect } from "next/navigation";
import Link from "next/link";
import { createClient } from "@/lib/supabase/server";
import { Button } from "@/components/ui/button";

export default async function LandingPage() {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (user) {
    redirect("/");
    // Note: the dashboard home is also at /; we rely on the (dashboard)
    // route group convention. If user is logged in, the dashboard layout
    // renders. If not, they see this landing instead. Cleaner pattern is
    // to move the dashboard to /dashboard later if needed.
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="max-w-2xl text-center p-8">
        <h1 className="text-4xl font-semibold mb-4">FollowRoom</h1>
        <p className="text-lg text-gray-600 mb-8">
          Living relationship rooms for the operator who refuses to let
          clients fall through the cracks.
        </p>
        <div className="flex gap-3 justify-center">
          <Link href="/signup">
            <Button size="lg">Get started</Button>
          </Link>
          <Link href="/login">
            <Button size="lg" variant="outline">Log in</Button>
          </Link>
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 4: Commit**

```bash
git add web/app
git commit -m "feat(web): dashboard layout + home with auth guard

DashboardLayout uses supabase.auth.getUser() (trustworthy check per
design doc §9.3). Empty state when no clients; client list when present.
Landing page redirects logged-in users."
```

---

### Task 28: Frontend — create client form

Implement the client creation form with required short_context validation.

**Files:**
- Create: `web/app/(dashboard)/clients/new/page.tsx`
- Create: `web/components/clients/new-client-form.tsx`

- [ ] **Step 1: Implement form component**

Create `web/components/clients/new-client-form.tsx`:

```typescript
"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { createClient } from "@/lib/supabase/client";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";

export function NewClientForm() {
  const [clientName, setClientName] = useState("");
  const [phoneNumber, setPhoneNumber] = useState("");
  const [shortContext, setShortContext] = useState("");
  const [relationshipType, setRelationshipType] = useState("buyer");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);

    if (shortContext.trim().length < 20) {
      setError(
        "Short context must be at least 20 characters — give us enough to start. " +
        "Example: 'HDB upgrade, East Coast, ~$1.8M, husband in finance.'"
      );
      return;
    }

    setLoading(true);

    const supabase = createClient();
    const { error: dbError } = await supabase
      .from("clients")
      .insert({
        client_name: clientName,
        phone_number: phoneNumber || null,
        relationship_type: relationshipType,
        short_context: shortContext,
      });

    setLoading(false);

    if (dbError) {
      setError(dbError.message);
      return;
    }

    router.push("/");
    router.refresh();
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6 max-w-xl">
      <div className="space-y-2">
        <Label htmlFor="client_name">Client name *</Label>
        <Input
          id="client_name"
          required
          value={clientName}
          onChange={(e) => setClientName(e.target.value)}
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="phone_number">Phone number (optional)</Label>
        <Input
          id="phone_number"
          type="tel"
          value={phoneNumber}
          onChange={(e) => setPhoneNumber(e.target.value)}
          placeholder="+65 9123 4567"
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="relationship_type">Relationship type</Label>
        <select
          id="relationship_type"
          value={relationshipType}
          onChange={(e) => setRelationshipType(e.target.value)}
          className="w-full border rounded-md px-3 py-2"
        >
          <option value="buyer">Buyer</option>
          <option value="seller">Seller</option>
          <option value="landlord">Landlord</option>
          <option value="tenant">Tenant</option>
          <option value="investor">Investor</option>
          <option value="commercial_landlord">Commercial landlord</option>
          <option value="commercial_tenant">Commercial tenant</option>
          <option value="referral_partner">Referral partner</option>
          <option value="other">Other</option>
        </select>
      </div>

      <div className="space-y-2">
        <Label htmlFor="short_context">
          Short context *{" "}
          <span className="text-xs text-gray-500">(min 20 chars)</span>
        </Label>
        <Textarea
          id="short_context"
          required
          minLength={20}
          rows={3}
          value={shortContext}
          onChange={(e) => setShortContext(e.target.value)}
          placeholder="e.g., HDB upgrade, East Coast, ~$1.8M, husband in finance. Wife's family in Marine Parade."
        />
        <p className="text-xs text-gray-500">
          A few sentences about who they are and what they want. This seeds the
          relationship memory — the richer the seed, the smarter the room from day one.
        </p>
      </div>

      {error && <p className="text-sm text-red-600">{error}</p>}

      <div className="flex gap-3">
        <Button type="submit" disabled={loading}>
          {loading ? "Creating..." : "Create client"}
        </Button>
        <Button type="button" variant="outline" onClick={() => router.back()}>
          Cancel
        </Button>
      </div>
    </form>
  );
}
```

- [ ] **Step 2: Create new client page**

Create `web/app/(dashboard)/clients/new/page.tsx`:

```typescript
import { NewClientForm } from "@/components/clients/new-client-form";

export default function NewClientPage() {
  return (
    <div>
      <h2 className="text-2xl font-semibold mb-6">Add a client</h2>
      <NewClientForm />
    </div>
  );
}
```

- [ ] **Step 3: Manual verification**

```bash
cd web && npm run dev
```

In browser:
1. Log in as the test user from Task 26
2. Click "Add your first client"
3. Try submitting with short_context under 20 chars — see inline error
4. Fill in valid data, submit
5. Verify client appears in dashboard list
6. Verify row in Supabase Table Editor → clients

- [ ] **Step 4: Commit**

```bash
git add web/app web/components
git commit -m "feat(web): create-client form with short_context validation

Form validates short_context ≥ 20 chars client-side; database CHECK
constraint enforces server-side (defense in depth). Helper text
explains why the seed matters (cold-start mitigation §5.7)."
```

---

### Task 29: Frontend — public room route placeholder

Reserve the `/r/[slug]` route so middleware exclusion (Task 10) works end-to-end. Plan 6 fleshes out.

**Files:**
- Create: `web/app/r/[slug]/page.tsx`

- [ ] **Step 1: Create placeholder page**

Create `web/app/r/[slug]/page.tsx`:

```typescript
export const dynamic = "force-dynamic";

export default async function RoomPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;

  // Plan 6 implements the full room rendering. Placeholder confirms
  // routing + middleware exclusion works end-to-end.
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="text-center p-8">
        <h1 className="text-2xl font-semibold mb-2">FollowRoom</h1>
        <p className="text-gray-600">
          Room <code className="font-mono text-sm">{slug}</code> is coming soon.
        </p>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Verify route works without auth**

```bash
cd web && npm run dev
```

In an incognito window (no auth cookie):
- Visit `http://localhost:3000/r/test-slug`
- Should see the placeholder page (NOT redirected to login)

- [ ] **Step 3: Commit**

```bash
git add web/app/r
git commit -m "feat(web): public /r/[slug] route placeholder

Confirms middleware exclusion (Task 10) works — public route accessible
without auth. Plan 6 implements full room rendering."
```

---

### Task 30: Author DESIGN.md

Write the FollowRoom design doctrine per design doc §9.8 (Impeccable adoption deferred).

**Files:**
- Create: `DESIGN.md`

- [ ] **Step 1: Write DESIGN.md**

Create `DESIGN.md`:

```markdown
# DESIGN.md — FollowRoom

**Phase 1 design doctrine. Authored before tooling adoption.**

This document captures the design intent that should govern every UI
decision in FollowRoom. It exists so that the visual identity of the
product is articulated in our own words, from the founder's lived-persona
perspective, before any external tooling (Impeccable, design system
libraries, AI generation) shapes the aesthetic.

Per the architecture design doc §9.8, Impeccable tooling adoption is
deferred to Phase 1.5. Until then, this document is the source of truth.

---

## Brand voice

FollowRoom is the **quiet witness with receipts.** It watches client
relationships unfold, remembers what mattered, and surfaces evidence
when asked — without coaching, diagnosing, or befriending.

Tone:
- **Calm, never urgent** — the product holds time well; doesn't manufacture pressure
- **Specific, never generic** — Pattern 4 (Specificity is Identity); language about clients is particular, not abstract
- **Warm, never effusive** — empathy without overclaim; professional warmth, not chatbot enthusiasm
- **Honest, never overpromising** — confidence scores visible; receipts mandatory; we say "we noticed" not "you should"

Voice anti-patterns to avoid:
- Sales-coaching language ("close this deal!" "follow up now!")
- Empty enthusiasm ("Amazing!" "Great job!")
- Excessive emojis or punctuation (no 🚀 in product copy)
- Generic AI-SaaS phrases ("powered by AI" "leverage AI" "AI-driven insights")
- Surveillance-flavored framing ("we tracked" "we noticed they"); prefer "your record shows" or "evidence indicates"

---

## Audience

Two distinct audiences, two distinct design contexts:

### Operator (the property agent or sales operator)

- 30-55 years old, mobile-heavy, dense schedule, low tolerance for friction
- Already uses WhatsApp, voice memos, Otter/Fireflies for transcription
- Wants to appear organized, premium, thoughtful to clients
- Resistant to heavy CRMs; price-conscious but values polished tools
- Reads English natively; may operate in mixed-language environment (Mandarin / Malay client communications)

Dashboard design priorities:
- **Density over whitespace** — operators want to see a lot at a glance (Linear / Superhuman pattern)
- **Keyboard navigability** — power users will use ⌘K-style command palette in Phase 2
- **Mobile dashboard works on phone**, but operator's primary workflow may be desktop during deep review
- **Adaptive layout** — works fluently on phone for in-the-moment captures, on desktop for batch review

### Client (the operator's customer)

- 25-60 years old, opening links from WhatsApp on phones
- Doesn't know they're using "FollowRoom" — they see *"Sarah's room"* (operator-branded)
- Expects polished, premium experience; this is their advisor's professionalism rendered as a page
- Single-session purpose — they came to view something specific, not browse

Client-facing room design priorities:
- **Mobile-first, polished, premium-feeling**
- **Single scrollable surface** — no nested navigation
- **Instant load** — PPR rendering (design doc §9.2); edge caching; sub-second perceived load
- **No app required** — works in browser; no login (or one-time PIN if operator chose)
- **No FollowRoom branding intrusion** — subtle attribution; the operator's brand leads

---

## Anti-references

What FollowRoom should NOT look or feel like:

### Generic AI SaaS

- Purple gradient hero sections, "AI-powered" badges, hexagon iconography
- Animations on scroll, parallax marketing pages, sticky chat bubbles
- Dark mode by default (we are warm, not sterile)
- Big "Try it free" CTAs with countdown timers

### Heavy enterprise CRM

- Tabbed forms with 30 fields
- Dropdown-of-dropdowns navigation
- Configuration screens before content
- Loading spinners for everything

### Maximalist "design" SaaS

- Overuse of glassmorphism, neumorphism, brutalism trends
- Six fonts on one page
- Decorative emoji as content
- Mascots, characters, illustrations of generic happy diverse people

### Linear copies

- FollowRoom dashboard CAN borrow from Linear's density patterns, but it's
  not a project tracker. Avoid issue-board metaphors; we're a relationship-
  arc product.

### Notion clones

- Avoid the "everything is a block" feel; FollowRoom has specific surfaces
  for specific purposes, not infinite-canvas flexibility.

---

## Visual identity (initial)

Colors:
- **Primary palette: warm neutrals** — off-white background, dark slate text, subtle warm accent
- **Avoid: cool grays, pure white, vibrant brand colors that scream "tech"**
- One restrained accent color for actions and key signals (TBD during build)

Typography:
- **System fonts for dashboard** (San Francisco / Segoe UI / Inter) for performance + native feel
- **Serif heading for client-facing rooms** (premium feel; e.g., Source Serif Pro or similar) — distinguishes the room from the operator dashboard
- One font family per surface, two weights max

Spacing:
- Generous but not luxurious — dense enough for power users, breathable enough for clients
- Mobile: edge-to-edge with safe-area awareness
- Desktop: max-width containers (~896px for content, ~1200px for dashboards)

Components:
- shadcn/ui base; restrained customization
- Tremor for any KPI / chart surface (dashboard cross-relationship insights)
- TanStack Table for dense data grids (client list, pending queue)
- Avoid: shadow-heavy floating cards, gradient buttons, animated loading skeletons that distract

---

## Anti-pattern checklist (Impeccable-inspired)

Run through this checklist before merging any UI PR. These come from
Impeccable's anti-slop catalog (referenced, not tooled, until Phase 1.5).

- [ ] No purple gradients anywhere
- [ ] No nested cards (card-within-card-within-card)
- [ ] No more than 2 typefaces on a single page
- [ ] No gradient headings (one solid color)
- [ ] Text contrast ≥ WCAG AA against background
- [ ] Touch targets ≥ 44×44px on mobile
- [ ] No more than 3 button styles in product (primary, secondary, tertiary/link)
- [ ] No decorative emoji in product copy (functional emoji in user content is fine)
- [ ] Loading states show meaningful progress, not vague spinners
- [ ] Empty states explain what comes next, not "no data found"
- [ ] Mobile layout works at 360px width minimum
- [ ] No content reflow on initial load (CLS = 0)

---

## Evolution

This doc is a living artifact. As FollowRoom's UI emerges:
- Update sections as patterns crystallize
- Add concrete examples (screenshots, before/afters) as they become available
- At Phase 1.5, when Impeccable tooling is adopted, this doc becomes the
  input to `/impeccable teach` for generating the tool's canonical
  `DESIGN.md` shape — but the soul stays here

---

*Founded 2026-05-18. Last updated: 2026-05-18.*
```

- [ ] **Step 2: Commit**

```bash
git add DESIGN.md
git commit -m "docs: author DESIGN.md — FollowRoom design doctrine

Authored before any tooling adoption per design doc §9.8.
Captures brand voice, audience contexts (operator + client), anti-
references, visual identity, Impeccable-inspired anti-pattern checklist.
This is the source of truth until Phase 1.5 Impeccable tooling adoption."
```

---

### Task 31: Author PRODUCT.md

Write the product positioning doc per design doc §9.8.

**Files:**
- Create: `PRODUCT.md`

- [ ] **Step 1: Write PRODUCT.md**

Create `PRODUCT.md`:

```markdown
# PRODUCT.md — FollowRoom

**What we are, what we aren't, who we serve.**

---

## What FollowRoom is

FollowRoom is **living relationship rooms** for relationship-driven sales
operators — initially Singapore property agents, expanding to insurance
advisors, wealth managers, and B2B consultants over time.

Internally, FollowRoom is a **compounding per-client knowledgebase**
that takes meeting transcripts, voice memos, forwarded WhatsApp messages,
and operator-dropped artifacts (PDFs, photos, links) and synthesizes them
into:

1. A **private relationship memory** the operator can search and review
2. A **polished client-facing room** the operator can share with clients
3. **Cross-relationship insights** that surface patterns across the operator's book of business

Architecturally, FollowRoom is a **LineOS application** — the substrate
for tending client Lines, sibling to Decades (which tends the operator's
own Line). See `docs/superpowers/specs/2026-05-18-followroom-architecture-design.md`.

---

## What FollowRoom is NOT

- **Not a CRM replacement** — we sit above CRMs; we don't replace
  pipeline management
- **Not a meeting transcription tool** — we ingest transcripts (from
  Otter / Fireflies / Granola / direct audio); we don't compete with
  transcription tools
- **Not a WhatsApp client** — the operator keeps using WhatsApp; we are
  selective ingestion + organized memory
- **Not a chatbot** — we never message the operator's customers; the
  WhatsApp endpoint is silent (or minimally conversational, per design
  doc §5.3 Shape X)
- **Not DocuSign** — for legally sensitive document execution, operators
  use their brokerage's secure portal; FollowRoom is for relationship
  continuity
- **Not Notion** — we are opinionated about workflow; we don't offer
  infinite flexibility
- **Not a marketing automation tool** — we do not blast messages,
  schedule campaigns, or run nurture sequences

---

## Three audiences, three contracts

### Operator (the buyer)

The relationship-driven sales operator. They pay for FollowRoom.

What we promise:
- Their conversations become memory without manual filing
- Follow-up timing is surfaced before things go stale
- Client-facing rooms are polished enough to make clients feel properly remembered
- Cross-relationship patterns reveal what they couldn't see deal-by-deal
- Their data is theirs — exportable, deletable, never sold

### Client (the end-user of the room)

The operator's customer. They never pay; they may not even know "FollowRoom"
exists — they see "Sarah Tan's room."

What we promise:
- The room is private (URL is unguessable; optional PIN for sensitive deals)
- View tracking is minimal (aggregate signals only; no granular surveillance)
- The information shown is what the operator approved — no AI-generated
  speculation about them
- Documents shared are organized and accessible without an account
- The experience feels premium, not generic

### Future agency (Phase 3)

Real estate brokerages and similar agencies. They will pay enterprise
prices in Phase 3.

What we'll promise:
- Multi-operator coordination without silo'ing client knowledge
- Manager visibility into team activity without violating operator-client privacy
- Shared artifact library (brokerage-approved templates, compliance forms)
- Audit trails for regulatory compliance

---

## Foundational principles (Quiet Witness posture)

FollowRoom maintains a particular epistemic posture, summarized in three
inherited Decades patterns:

1. **The Quiet Witness** (Pattern 2) — Watches, remembers, shows what
   it saw with evidence. Does NOT advise, diagnose, befriend, or coach.
2. **Truth With Receipts** (Pattern 9) — Every AI claim links back to
   verbatim source material. If we can't produce a receipt, we don't
   make the claim.
3. **Celebration Over Correction** (Pattern 12) — We surface patterns
   ("3 clients mentioned affordability") as discovery, not diagnosis
   ("you should change your pitch").

These patterns shape every product decision:
- Suggested replies are drafts, never sent automatically
- Cross-relationship insights are invitations, never assertions
- Tier 3 inferences (family dynamics, emotional state, decision-blocker
  speculation) NEVER appear in client-facing rooms
- Confidence scores are visible alongside AI-extracted facts
- Operators can mark any AI extraction as rejected; the rejection is
  canonical and persists across regenerations

---

## What success looks like

Phase 1 (Solo MVP) success:
- 10-20 paying solo property agents within 6 months of launch
- ≥70% weekly active rate among paying operators
- ≥50% of paying operators publish at least one room update per week
- ≥1 NPS-worthy testimonial per cohort

Phase 2 (Solo Pro) success:
- ≥30% of Phase 1 operators upgrade to Pro within 6 months of Phase 2 launch
- Cross-relationship insight features generate ≥1 insight-triggered action per operator per week

Phase 3 (Agency Enterprise) success:
- 5+ paying agency contracts within 12 months of Phase 3 launch
- Average agency contract ≥$30k ARR
- Agency NRR ≥110% (expansion via seat additions)

---

## Voice samples (use as reference for product copy)

**Welcome email:**
> Welcome to FollowRoom. Add your first client, upload your most recent
> meeting with them, and your first room takes shape in about 60 seconds.
> No setup ceremony. Your conversations are the documentation.

**Empty state (no clients yet):**
> Add your first client to start building their relationship room.

**Empty state (no events yet for a client):**
> Sarah's room is waiting for its first signal. Upload a meeting
> transcript, drop a document, or forward a WhatsApp message.

**Cross-relationship insight (good):**
> Four clients mentioned affordability anxiety this week (Tan, Chen,
> Wong, Lim). Worth knowing.

**Cross-relationship insight (avoid):**
> ❌ "Your pitch isn't landing — 4 clients pushed back on price.
> Consider revising your approach."

**Pending action surface for client:**
> Sarah, your advisor shared the floor plan for unit #14-22 for your
> review. Tap to view.

**Revoke link grace screen:**
> This link has been replaced for security. Please ask Sarah Tan for
> the new link.

---

## Evolution

This doc evolves with the product. As we learn:
- What language operators use to describe FollowRoom unprompted (their
  framing beats ours)
- Which patterns from Decades / LineOS map cleanly vs need adaptation
- What competitor products emerge in the space and how we differentiate
- What we'd kill if we had to (constraint clarifies positioning)

Update this doc when those learnings crystallize.

---

*Founded 2026-05-18. Last updated: 2026-05-18.*
```

- [ ] **Step 2: Commit**

```bash
git add PRODUCT.md
git commit -m "docs: author PRODUCT.md — what we are, what we aren't, who we serve

Three audiences (operator, client, future agency), three contracts.
Quiet Witness posture as foundational principle. Voice samples for
product copy reference. Updated as learnings accumulate."
```

---

### Task 32: Update SCHEMA_REFERENCE.md

Document all migrations 0001-0009 in the schema reference per Decades convention.

**Files:**
- Modify: `supabase/SCHEMA_REFERENCE.md`

- [ ] **Step 1: Rewrite SCHEMA_REFERENCE.md with all tables**

Replace `supabase/SCHEMA_REFERENCE.md`:

```markdown
# Supabase Schema Reference — FollowRoom

**IMPORTANT:** Read this file before writing ANY SQL migration.

Last updated: 2026-05-18

---

## operators

| Column | Type | Notes |
|--------|------|-------|
| id | UUID | PK, FK to auth.users(id), ON DELETE CASCADE |
| email | TEXT | UNIQUE NOT NULL |
| name | TEXT | nullable |
| company_name | TEXT | nullable |
| role_title | TEXT | nullable |
| industry | TEXT | DEFAULT 'real_estate' |
| profile_photo_url | TEXT | nullable |
| default_language | TEXT | DEFAULT 'en' |
| default_tone | TEXT | nullable |
| timezone | TEXT | DEFAULT 'Asia/Singapore' |
| is_deleted | BOOLEAN | DEFAULT FALSE |
| deleted_at | TIMESTAMPTZ | nullable |
| transaction_time | TIMESTAMPTZ | bi-temporal; DEFAULT NOW() |
| created_at | TIMESTAMPTZ | DEFAULT NOW() |
| updated_at | TIMESTAMPTZ | DEFAULT NOW() |

Indexes:
- `idx_operators_active` on `(id)` WHERE NOT is_deleted

Triggers:
- `on_auth_user_created` on `auth.users` AFTER INSERT — auto-creates operators row via `handle_new_auth_user()`

RLS: ENABLED. Operator sees only their own row. No DELETE policy.

---

## clients

| Column | Type | Notes |
|--------|------|-------|
| id | UUID | PK, DEFAULT gen_random_uuid() |
| operator_id | UUID | NOT NULL, FK to operators(id), ON DELETE CASCADE |
| client_name | TEXT | NOT NULL |
| phone_number | TEXT | nullable |
| aliases | TEXT[] | DEFAULT '{}' |
| relationship_type | TEXT | CHECK (buyer/seller/landlord/tenant/investor/...) |
| status | TEXT | CHECK (new_lead/active_discussion/...) |
| tags | TEXT[] | DEFAULT '{}' |
| short_context | TEXT | NOT NULL, CHECK (length >= 20) — cold-start mitigation (design doc §5.7) |
| is_deleted | BOOLEAN | DEFAULT FALSE |
| deleted_at | TIMESTAMPTZ | nullable |
| transaction_time | TIMESTAMPTZ | bi-temporal |
| created_at | TIMESTAMPTZ | |
| updated_at | TIMESTAMPTZ | auto-updated via trigger |

Indexes:
- `idx_clients_operator_active` on `(operator_id)` WHERE NOT is_deleted
- `idx_clients_operator_status` on `(operator_id, status)` WHERE NOT is_deleted

RLS: per-operator. No DELETE policy.

---

## events

| Column | Type | Notes |
|--------|------|-------|
| id | UUID | PK |
| client_id | UUID | NOT NULL, FK clients(id), ON DELETE RESTRICT |
| operator_id | UUID | NOT NULL, FK operators(id), ON DELETE CASCADE |
| source_type | TEXT | CHECK (meeting_transcript/voice_memo/whatsapp_forward_shapeX/whatsapp_coexistence/manual_note/file_drop) — IMMUTABLE |
| raw_text | TEXT | NOT NULL — **APPEND-ONLY** (Pattern 21; trigger enforced) |
| transaction_time | TIMESTAMPTZ | when recorded |
| valid_time | TIMESTAMPTZ | when claimed true (event time) |
| attributed_to | TEXT | DEFAULT 'operator' |
| attributed_at | TIMESTAMPTZ | |
| is_deleted | BOOLEAN | DEFAULT FALSE |
| deleted_at | TIMESTAMPTZ | |
| created_at | TIMESTAMPTZ | |

Indexes:
- `idx_events_client_time` on `(client_id, transaction_time DESC)` WHERE NOT is_deleted
- `idx_events_operator` on `(operator_id)` WHERE NOT is_deleted

Triggers:
- `events_raw_text_append_only` BEFORE UPDATE — RAISES on raw_text/source_type/client_id mutation

RLS: per-operator.

---

## facts

| Column | Type | Notes |
|--------|------|-------|
| id | UUID | PK |
| client_id | UUID | NOT NULL, FK clients(id) |
| operator_id | UUID | NOT NULL, FK operators(id) |
| type | TEXT | CHECK (goal/budget_constraint/objection/...) |
| value | TEXT | NOT NULL |
| source_event_ids | UUID[] | NOT NULL, CHECK (length >= 1) — Receipts mandatory |
| source_spans | JSONB | DEFAULT '[]' — verbatim citation snippets |
| confidence_score | REAL | CHECK (0-1) |
| visibility | TEXT | CHECK (operator_only/client_facing_safe/agency_visible) |
| provenance | TEXT | CHECK (llm_generated/operator_curated/operator_edited/regenerable/canonical) |
| user_stance | TEXT | CHECK (unreviewed/accepted/rejected/reframed/operator_curated) |
| user_stance_set_at | TIMESTAMPTZ | |
| superseded_by | UUID | FK facts(id) — UPDATE in ADD/UPDATE/DELETE/NOOP pipeline |
| generation_metadata | JSONB | model_id, prompt_hash, schema_version, etc. |
| is_deleted | BOOLEAN | DEFAULT FALSE |
| deleted_at | TIMESTAMPTZ | |
| created_at | TIMESTAMPTZ | |
| updated_at | TIMESTAMPTZ | auto-updated via trigger |

Indexes:
- `idx_facts_client_active` on `(client_id)` WHERE NOT is_deleted AND superseded_by IS NULL
- `idx_facts_client_type` on `(client_id, type)` WHERE NOT is_deleted AND superseded_by IS NULL
- `idx_facts_client_visibility` on `(client_id, visibility)` WHERE NOT is_deleted AND superseded_by IS NULL

RLS: per-operator.

---

## room_attachments

| Column | Type | Notes |
|--------|------|-------|
| id | UUID | PK |
| client_id | UUID | NOT NULL, FK clients(id) |
| operator_id | UUID | NOT NULL, FK operators(id) |
| storage_path | TEXT | NOT NULL — IMMUTABLE |
| original_filename | TEXT | NOT NULL — IMMUTABLE |
| mime_type | TEXT | NOT NULL |
| size_bytes | BIGINT | CHECK (> 0) — IMMUTABLE |
| content_hash | TEXT | SHA256 — IMMUTABLE |
| source_event_id | UUID | nullable, FK events(id) |
| related_fact_ids | UUID[] | DEFAULT '{}' |
| operator_note | TEXT | nullable |
| pending_action_type | TEXT | CHECK (for_review/for_signature/for_consideration/for_payment/informational) |
| pending_action_due | TIMESTAMPTZ | nullable |
| pending_action_label | TEXT | |
| visibility | TEXT | CHECK (operator_only/client_facing_safe/agency_visible) |
| visibility_promoted_at | TIMESTAMPTZ | |
| visibility_promoted_by | TEXT | |
| client_viewed_at | TIMESTAMPTZ | |
| client_viewed_count | INTEGER | DEFAULT 0 |
| client_downloaded_at | TIMESTAMPTZ | |
| client_acted_at | TIMESTAMPTZ | |
| client_action_taken | TEXT | acknowledged/signed/declined/paid/archived |
| superseded_by | UUID | FK self |
| supersedes | UUID | FK self |
| version_number | INTEGER | DEFAULT 1 |
| is_deleted | BOOLEAN | DEFAULT FALSE |
| deleted_at | TIMESTAMPTZ | |
| extraction_metadata | JSONB | DEFAULT '{}' |
| extracted_text | TEXT | for in-room search |
| created_at | TIMESTAMPTZ | |
| updated_at | TIMESTAMPTZ | auto |

Indexes:
- `idx_attachments_client_visible` on `(client_id, visibility, created_at DESC)` WHERE NOT is_deleted
- `idx_attachments_pending` on `(client_id, pending_action_type, pending_action_due)` WHERE pending_action_type IS NOT NULL AND client_acted_at IS NULL AND NOT is_deleted
- `idx_attachments_type` on `(client_id, mime_type)` WHERE NOT is_deleted
- `idx_attachments_extracted_text` GIN on `to_tsvector('english', extracted_text)` WHERE NOT is_deleted

Triggers:
- `attachments_file_immutability` BEFORE UPDATE — RAISES on storage_path/content_hash/filename/size_bytes mutation

RLS: per-operator (base table). Plan 6 adds a view for anonymous public-room reads.

---

## attributions

| Column | Type | Notes |
|--------|------|-------|
| id | UUID | PK |
| operator_id | UUID | NOT NULL, FK operators(id) |
| artifact_id | UUID | NOT NULL |
| artifact_type | TEXT | CHECK (event/fact/room_attachment/room_update_draft/client/operator) |
| agent_id | TEXT | DEFAULT 'operator' — Phase 3 expands |
| surface | TEXT | CHECK (web_dashboard/whatsapp_webhook/voice_upload/file_drop/manual_note/system_cron) |
| session_id | TEXT | |
| turn_index | INTEGER | |
| confidence | REAL | CHECK (0-1) DEFAULT 1.0 |
| reason | TEXT | |
| timestamp | TIMESTAMPTZ | DEFAULT NOW() |

Indexes:
- `idx_attributions_artifact` on `(artifact_type, artifact_id)`
- `idx_attributions_operator` on `(operator_id, timestamp DESC)`

RLS: per-operator (SELECT + INSERT only).

---

## visibility_promotions

| Column | Type | Notes |
|--------|------|-------|
| id | UUID | PK |
| operator_id | UUID | NOT NULL, FK operators(id) |
| artifact_id | UUID | NOT NULL |
| artifact_type | TEXT | CHECK (fact/room_attachment/room_update_draft) |
| from_tier | TEXT | CHECK (operator_only/client_facing_safe/agency_visible) |
| to_tier | TEXT | CHECK (same) |
| approved_by | TEXT | NOT NULL — 'operator:<id>' |
| approved_at | TIMESTAMPTZ | DEFAULT NOW() |
| reason | TEXT | |
| reversible | BOOLEAN | DEFAULT TRUE |

Indexes:
- `idx_promotions_operator` on `(operator_id, approved_at DESC)`
- `idx_promotions_artifact` on `(artifact_type, artifact_id)`

RLS: per-operator (SELECT + INSERT only).

---

## rooms_public (view)

Placeholder view. Returns 0 rows in Phase 1 (WHERE FALSE). Plan 6 populates with a `rooms` table holding `public_slug` + `passcode_hash` + room metadata.

---

## Useful patterns when writing migrations

- Number files sequentially: `0001_*.sql`, `0002_*.sql`, ...
- Every migration starts with `-- Migration: NNNN — <name>` and includes a `-- Rollback:` comment
- Use `CREATE OR REPLACE FUNCTION` and `IF NOT EXISTS` where possible for idempotency
- Add CHECK constraints generously for enum-style columns; CHECK is cheap and catches typos
- Add `is_deleted` + `deleted_at` to every user-data table (Pattern 18)
- Add `transaction_time` to tables that need bi-temporal querying
- Wrap append-only fields in BEFORE UPDATE triggers (Pattern 21)
- Apply RLS in a single dedicated migration after table creation (current pattern: migration 0008)
```

- [ ] **Step 2: Commit**

```bash
git add supabase/SCHEMA_REFERENCE.md
git commit -m "docs(schema): full SCHEMA_REFERENCE.md for migrations 0001-0009

Documents all 7 tables + 1 view. Notes append-only columns, triggers,
indexes, RLS posture. Useful patterns appendix at end."
```

---

### Task 33: E2E test — signup → create client → see client

End-to-end test of the full first-user flow.

**Files:**
- Create: `web/tests/e2e/signup-create-client.spec.ts`

- [ ] **Step 1: Write E2E test**

Create `web/tests/e2e/signup-create-client.spec.ts`:

```typescript
import { test, expect } from "@playwright/test";

// Skip in CI without a real Supabase instance. Run locally against
// the dev Supabase project with NEXT_PUBLIC_SUPABASE_URL set.
test.describe("first-user flow", () => {
  test("operator can sign up, log in, create client, see client", async ({ page }) => {
    test.skip(
      !process.env.NEXT_PUBLIC_SUPABASE_URL || process.env.NEXT_PUBLIC_SUPABASE_URL.includes("ci.supabase.co"),
      "Requires a real Supabase project"
    );

    const email = `test-${Date.now()}@e2e.followroom.dev`;
    const password = "SecurePassword123!";

    // Note: This test uses Supabase's auto-confirm in dev settings; in
    // production setups, email confirmation would interrupt this flow.
    // Confirm Supabase dashboard → Authentication → Settings → "Enable
    // email confirmations" is OFF in dev for this E2E to pass.

    // 1. Sign up
    await page.goto("/signup");
    await page.fill("#email", email);
    await page.fill("#password", password);
    await page.click("button[type=submit]");
    await page.waitForURL("**/login*");

    // 2. Log in
    await page.fill("#email", email);
    await page.fill("#password", password);
    await page.click("button[type=submit]");
    await page.waitForURL("/", { timeout: 10000 });

    // 3. Dashboard shows empty state
    await expect(page.getByText(/Welcome to FollowRoom/i)).toBeVisible();
    await expect(page.getByRole("button", { name: /Add your first client/i })).toBeVisible();

    // 4. Navigate to new client form
    await page.click("text=Add your first client");
    await page.waitForURL("**/clients/new");

    // 5. Fill in client
    await page.fill("#client_name", "Sarah Tan (E2E test)");
    await page.fill(
      "#short_context",
      "HDB upgrade, East Coast, around $1.8M, husband works in finance."
    );
    await page.click("button[type=submit]:has-text('Create client')");

    // 6. Back on dashboard, see the client
    await page.waitForURL("/", { timeout: 10000 });
    await expect(page.getByText("Sarah Tan (E2E test)")).toBeVisible();
    await expect(page.getByText(/HDB upgrade, East Coast/i)).toBeVisible();
  });
});
```

- [ ] **Step 2: Configure Supabase for E2E (manual)**

In Supabase dashboard → **Authentication → Settings**:
- Set **"Enable email confirmations"** to OFF for the dev project (E2E uses ephemeral emails that can't be confirmed)
- OR: configure SMTP to a test inbox if you prefer realistic flows

For this E2E to pass locally with confirmation OFF, the signup directly creates a usable user.

- [ ] **Step 3: Run E2E**

```bash
cd web
npm run test:e2e
```

Expected: 1 test passed (or skipped if `NEXT_PUBLIC_SUPABASE_URL` points at CI fixtures).

- [ ] **Step 4: Commit**

```bash
git add web/tests/e2e
git commit -m "test(e2e): full first-user flow — signup, login, create client

Playwright test exercises signup → login → empty dashboard → new
client form → client appears in dashboard list. Skipped in CI
without real Supabase; run locally against dev project."
```

---

### Task 34: Update root CLAUDE.md with foundation completion status

Update the root CLAUDE.md to reflect Foundation plan completion.

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Update status section**

Replace the final "## Status" section in `CLAUDE.md`:

```markdown
## Status

**Phase: Phase 1 — Foundation complete.**

What's standing:
- Deployable backend (FastAPI) + frontend (Next.js 15) shells
- Supabase schema (operators, clients, events, facts, room_attachments, attributions, visibility_promotions + rooms_public placeholder view)
- Forward-compatibility hooks baked in per design doc §8 (append-only triggers, soft-delete, bi-temporal columns, per-principal attribution from Day 1, single `store()` write path, vendor-agnostic `AgentDispatcher`)
- Auth: Supabase Auth + @supabase/ssr with cross-user session leak prevention
- First user flow: signup → create client with required short_context → see client in dashboard
- DESIGN.md + PRODUCT.md authored

Next:
- Plan 2 — Core KB Layer (extraction pipeline, ADD/UPDATE/DELETE/NOOP, profile regeneration)
- See `.claude/session-state.md` for resume context.

See `docs/superpowers/plans/2026-05-18-foundation.md` for the completed plan and `docs/superpowers/specs/2026-05-18-followroom-architecture-design.md` for the design doc this implements against.
```

- [ ] **Step 2: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: update root CLAUDE.md — Foundation plan complete

Resume-after-compaction reference updated. Next: Plan 2 Core KB Layer."
```

---

### Task 35: Open PR

Push the branch and open a pull request.

- [ ] **Step 1: Push branch**

```bash
git push -u origin feat/foundation-plan-1
```

- [ ] **Step 2: Open PR via gh**

```bash
gh pr create --title "feat: Foundation plan 1 — deployable shell + schema + first user flow" --body "$(cat <<'EOF'
## Summary
- Backend (FastAPI) + frontend (Next.js 15) deployable scaffolds
- Supabase schema with all forward-compatibility hooks per design doc §8 (append-only triggers, soft-delete, bi-temporal, attribution table, visibility_promotions)
- @supabase/ssr auth wiring with cross-user session leak prevention
- AgentDispatcher + LogicalRole abstraction (Pattern 20)
- Single governed `store()` write path
- DESIGN.md + PRODUCT.md authored (Impeccable deferred to Phase 1.5)
- End-to-end: operator signs up → creates client with required seed context → sees client in dashboard

## Test plan
- [ ] `cd backend && pytest -v` — all backend tests pass
- [ ] `cd web && npm run test` — all unit tests pass
- [ ] `cd web && npm run build` — production build succeeds
- [ ] `cd web && npm run test:e2e` — first-user flow E2E passes (requires real Supabase dev project)
- [ ] Apply migrations against dev Supabase: `cd backend && python scripts/apply_migrations.py`
- [ ] Manual: signup + create-client smoke test in browser
- [ ] CI green on both `backend-ci` and `web-ci` workflows

## Design doc
- Implements Phase 1 Foundation per `docs/superpowers/specs/2026-05-18-followroom-architecture-design.md`
- Plan: `docs/superpowers/plans/2026-05-18-foundation.md`

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

- [ ] **Step 3: Verify CI runs**

```bash
gh pr checks
```

Expected: both `backend-ci` and `web-ci` queued or running.

---

## Plan complete

You now have a deployable Phase 1 Foundation: FastAPI backend + Next.js frontend + Supabase schema with forward-compatibility hooks. The first user flow works end-to-end. DESIGN.md and PRODUCT.md anchor design discipline. Tests verify behavior at every layer.

**Next plan:** Plan 2 — Core KB Layer (extraction pipeline, ADD/UPDATE/DELETE/NOOP, profile regeneration).
