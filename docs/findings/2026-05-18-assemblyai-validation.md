# AssemblyAI validation for Plan 3 — findings

**Date:** 2026-05-18
**Purpose:** Verify AssemblyAI fit for SG real estate operator ingestion (transcripts + voice memos) before locking it into Plan 3.

## Verdict

**Proceed with AssemblyAI.** Two of three pre-flight checks are clean; one (APAC data residency) is a soft finding that we mitigate with operator-onboarding disclosure rather than a provider swap.

## Findings

### 1. Data residency — SOFT FINDING

AssemblyAI offers two regions: **US (default)** and **EU** (added 2025; expanded to LLM Gateway + Speech Understanding in March 2026). **No APAC or Singapore region.**

Comparison: Deepgram also caps SaaS at US + EU. APAC presence for either provider requires enterprise Dedicated (single-tenant) or self-hosted deployments — both overkill for Phase 3.

**SG PDPA implication:** Personal data transfer overseas is permitted under PDPA with (a) deemed/explicit consent + (b) comparable protection safeguards (DPA terms, encryption in transit/at rest). AssemblyAI provides SOC 2 Type II, HIPAA BAA, and a Data Processing Addendum.

**Mitigation:**
- Operator onboarding (added in Plan 4 or whenever first external user signs up) will surface a one-line disclosure: *"Audio and transcripts are processed by AssemblyAI (US-based). Don't upload client-confidential audio without their awareness."*
- Plan 3.5 placeholder: draft the disclosure language; add to signup flow.
- Defer APAC-residency provider swap until an enterprise customer asks (Phase 3 agency tier).

### 2. Mandarin / Singlish / code-switching — STRONG FIT

Universal-2 supports Mandarin. The **October 2025 release** added automatic code-switching mid-sentence — speakers can switch English ↔ Mandarin within a single utterance and the model handles it without manual language flags. This is materially aligned with SG conversation patterns (operator: "Auntie, the unit got 99-year lease, but the rental yield is 一定 better than HDB lah").

No published Mandarin-specific WER (overall Universal-2 WER ~6.7% across languages). Acceptable for v1; revisit if real operators report quality issues.

### 3. Pricing — TRIVIAL FOR PHASE 3

- Base async: **$0.15/hr** ($0.0025/min)
- + Speaker diarization: +$0.02/hr → **$0.17/hr**
- Free credits: $50 at signup ≈ 185 hours of Universal-2 transcription

Budget projection for early validation (3 agents × ~30 hrs audio/month each):
- 90 hrs/month × $0.17/hr = **~$15/month total**
- Negligible until we hit 100+ agents.

## Decision

Lock AssemblyAI Universal-2 (with `speaker_labels=true` for transcript uploads, `false` for voice memos) as the Plan 3 transcription provider. Pattern 20 (Vendor Agnostic) is preserved via `TranscriptionService` wrapping `AssemblyAIProvider` — swap to Deepgram or Whisper API is a config + provider-class change if either becomes preferable.

## Open follow-ups (not blocking)

- [ ] Plan 3.5: PDPA disclosure copy + onboarding surface
- [ ] Watch AssemblyAI release notes for APAC region announcement (revisit before Phase 3 agency tier)
- [ ] Verify Singlish accuracy with a real recording once we have one (add to QA checklist when first operator onboards)
