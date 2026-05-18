# PROJECT_DEV_SOUL.md — FollowRoom

**The Khaniff Signature: Principles, Practices, and Sensibilities for Building Software That Matters.**

*Adapted for FollowRoom from the Decades constitution (37 days, 184 PRs, 71 migrations, 39 system specs, 17 findings memos, 65+ architectural decisions, 5 crises that became doctrine). The principles are universal. The Decades specifics have been refit for FollowRoom's domain: relationship-driven sales, silent WhatsApp ingestion, operator-controlled client-facing rooms.*

---

## How to Use This Document

This is the constitution. Adapt the specifics; preserve the principles.

It establishes:
1. **Philosophy** — how to think about what FollowRoom is for
2. **Architecture** — how to structure systems that earn the operator's and the end-client's trust
3. **Process** — how to work with velocity and quality
4. **Cadence** — how the builder works, and what the AI assistant should respect

---

## Part I: Philosophy

### 1.1 The Central Conviction

**Build things that hold something sacred for the user.**

For FollowRoom, the user is a relationship-driven salesperson. The sacred thing is the texture of their client relationships — the specific phrasing of a wife's preference for Marine Parade because her parents are nearby; the particular shape of a buyer's hesitation about monthly repayments after bonus season; the trust that builds when a client feels properly remembered between meetings.

If what you're holding is sacred, then:
- Never destroy it silently
- Never let one operator see another's
- Never let one client appear in another's room
- Never claim something the operator didn't say or the client didn't say
- Never publish to the client-facing surface without operator approval
- Never delete until you're certain it's safe
- Default to preserving, not cleaning up

### 1.2 Seven Core Principles

**1. Evidence Over Assertion**
Every extracted fact, every suggested reply, every room update must point to its source: the specific WhatsApp forward, the specific transcript line, the specific date. "We noticed your client mentioned Marine Parade" must link to the message that said it. Receipts are not a feature — they are the trust architecture.

**2. Celebration Over Correction**
The dashboard surfaces patterns; it does not prescribe behavior. "Three clients mentioned affordability this week" — not "you should change your pitch." The system is a witness to the operator's relationships, not a coach. Frame insights as discovery, not diagnosis.

**3. User Authority Over Truth**
When the operator corrects an extracted fact, edits a suggested reply, reassigns an event to a different client, or rewrites a draft room update, the correction wins. Permanently. Across all regenerations. Human judgment outranks machine extraction. Always. The system proposes; the operator disposes.

**4. Specificity Is Identity**
Generic relationship summaries ("interested buyer, family-oriented") could describe anyone. Specific summaries ("HDB upgrader, East Coast, $1.8M ceiling, wife's parents in Marine Parade, hesitating on monthly repayment after bonus") can only describe one client. Every system that touches relationship memory must preserve the particular texture.

**5. Graceful Failure Is Non-Negotiable**
Assume everything will fail. Build for recovery, not prevention.
- WhatsApp webhooks will retry duplicate events — store idempotently.
- Transcript uploads will partially fail — preserve raw input before extraction runs.
- Client matching will misfire — every event is reassignable, every match is undoable.
- The AI will hallucinate — every published claim is operator-approved.
- Every safety system will breed the next failure — plan for the cascade.

**6. Truth Over Fluency**
A suggested reply that sounds polished but mischaracterizes the client is worse than no suggested reply. A room update that reads beautifully but exposes a private inference is a trust breach, not a UX win. If a confidence score is low, surface that, don't paper over it.

**7. Ship Fast, Then Fortify**
Ship features quickly. Encounter reality. Write the postmortem. Update the doctrine. Build the prevention architecture. The cycle is: build → break → learn → codify → prevent. Speed is not the enemy of quality — speed *reveals* what quality means in practice.

### 1.3 The Failure-to-Doctrine Cycle

Every significant principle in this document was born from a specific failure (in Decades). FollowRoom inherits the principles; it will earn its own additions the same way.

```
Failure → Emergency Fix → Postmortem → Doctrine Update → Prevention Architecture
```

Principles written in advance are aspirational. Principles extracted from failures are load-bearing. When something breaks, you've just discovered a principle. Document it in `docs/postmortems/`. Codify it. Make it impossible to violate again.

---

## Part II: Architecture Principles

### 2.1 Data Is Sacred

**Never-Delete Policy:**
- Operator-created data (clients, rooms, manual notes) and ingested data (WhatsApp forwards, transcripts) must never be hard-deleted by default
- Implement soft-delete everywhere: `is_deleted = TRUE, deleted_at = NOW()`
- Restore must be trivial: flip the flag, child data reappears
- Hard deletion requires explicit operator action + grace period + audit trail
- Client-room link revocation is a publishing concern (regenerate slug), not a delete

**Source Immutability:**
- `events.raw_text` (forwarded WhatsApp message body, raw transcript) is append-only
- Derived artifacts (`extracted_facts`, summaries, suggested replies, room update drafts) are regenerable
- If the model changes, every output can be re-derived from the source
- Store regeneration metadata: `model_id`, `prompt_hash`, `schema_version`, `generated_at`

**Defense in Depth for Data:**
- Database triggers that prevent hard deletes on user-facing tables
- Foreign keys set to RESTRICT (not CASCADE) on critical child data
- RLS policies that prevent cross-operator access AND cross-client room leaks
- Application-layer guards (no `.delete()` calls in client code)
- Zero hard-delete API endpoints in MVP

### 2.2 Authentication & Authorization

**Layer Every Defense:**
- Row-Level Security on every operator-facing table
- JWT validation middleware on every API endpoint
- Path parameter validation (any `client_id` or `room_id` in URL must be owned by the JWT `sub`)
- Client-side token injection on every request
- Session isolation on account switch (clear all cached state)

**Public Room Access Is Its Own Problem:**
- Client-facing rooms are accessed via unauthenticated URLs (`rooms.public_slug`) and optional passcode
- The published surface must be a strict subset, not a JOIN-derived view of internal memory
- Specific RLS policies authorize anonymous reads on the published columns only
- Passcode rate-limited; slug regeneration revokes old links instantly
- View tracking, if added later, runs through own infrastructure (no third-party SDKs in client rooms — see 2.5)

**Auth Deployment Rule:**
Never deploy breaking auth changes (new middleware, required headers) without ensuring all surfaces in the field support the new contract. Safe order: ship surface update first → wait for adoption → enforce server-side.

**Key Segregation:**
- Operator dashboard uses anon/public Supabase key only
- Service role key isolated to backend environment
- Background jobs (extraction worker, WhatsApp webhook handler) use separate API key with minimum scope
- No secret key in any client bundle, ever

### 2.3 Schema & Migration Discipline

**Non-Destructive Migration Rules:**
- Never `DROP TABLE`, `DROP COLUMN`, or `ALTER COLUMN TYPE` on tables with operator data without an explicit rollback plan
- Follow expand → backfill → cutover → contract
- Every migration file includes a `-- Rollback:` comment
- Idempotent when possible: `IF NOT EXISTS`, `CREATE OR REPLACE`
- Sequential numbering with no gaps (or documented gaps)

**Schema Reference File (Golden Source):**
`supabase/SCHEMA_REFERENCE.md` documents every table and column. Read it before writing any migration. Column names are frequently non-obvious (split columns instead of JSONB, abbreviated names, hashes vs raw values).

**RLS Checklist for Every New Table:**
- [ ] RLS enabled
- [ ] SELECT policy for authenticated operator on own data
- [ ] INSERT policy for authenticated operator on own data
- [ ] UPDATE policy for authenticated operator on own data
- [ ] DELETE policy (prefer soft-delete; no DELETE policy if soft-delete is in use)
- [ ] If table has a public-facing dimension (rooms): explicit anonymous read policy on a strict column subset

### 2.4 AI Integration

**Centralize All AI Calls:**
Every LLM call goes through a single wrapper (e.g., `structured_call()` in `backend/app/ai/`). This provides:
- Consistent error handling
- Metadata capture (`model_id`, `prompt_hash`, `schema_version`)
- Single point for vendor switching
- Prompt caching management
- Cost tracking per operator

**Structured Output with Typed Models:**
- All AI responses parsed into typed models (Pydantic / Zod)
- Every model has a `SCHEMA_VERSION` for drift detection
- No string parsing with `find("{")` — use SDK-level structured output

**Vendor Agnosticism:**
- No business logic depends on a specific model vendor
- Models are adapters, not authorities
- Vendor-specific code quarantined to one module
- Business logic lives in services, not in prompt construction

**Epistemic Risk Tiers:**

| Tier | Risk | FollowRoom examples | Rule |
|------|------|---------------------|------|
| 1 — Safe | Non-interpretive (data capture, aggregation) | Storing raw event, counting events per client, dashboard activity feed | Ship freely |
| 2 — Conditional | Interpretive but regenerable (insights, summaries) | Extracted facts, suggested replies, room update drafts, cross-relationship pattern cards | Label as interpretive; require operator approval before client-facing publish; keep source separate |
| 3 — Frozen | Identity-shaping or relationship-defining; high reputational risk | Inferred family dynamics, emotional state, decision-blocker speculation, anything that pretends to know what the client is "really" thinking | Block from client-facing publishes entirely; surface to operator with caveats; require explicit operator opt-in for any persistence beyond the source event |

The Tier 3 rule is the most load-bearing for FollowRoom's trust position. The product's pitch is that clients feel **listened to**, not **analyzed**.

### 2.5 Privacy by Architecture

**Design Choices That Enable Privacy Claims:**
- Zero third-party analytics SDKs on the client-facing room surface (no Google Analytics, no Hotjar, no Intercom widgets — route any telemetry through own infrastructure)
- Operator consent default to OFF for any data sharing or research use of relationship content
- Consent audit trail logs every change with timestamp, IP, old/new values
- Account deletion with CASCADE on the operator's own data (delete auth record → all clients/rooms/events go)
- Data export endpoint per client (operator can hand a client's record back to them)

**Operator Responsibility, Not Just Builder Responsibility:**
The operator is responsible for ensuring they have the right to process or store client conversation data. The product must surface this:
- Onboarding states clearly: forwarded WhatsApp messages contain another person's words; the operator is responsible for compliance
- Per-client setting for whether to retain raw forwarded messages or only extracted facts
- Visible "what we store" page accessible from every client workspace

**The Privacy Policy Is a Product Feature:**
Don't treat privacy as legal boilerplate. Every privacy claim should trace to a specific architectural decision. "We never message your clients" is not a promise — it's the absence of any outbound WhatsApp code path in the MVP. "Sensitive inferences never appear in the client room" is not a promise — it's a Tier 3 filter in the publish pipeline.

---

## Part III: Process & Workflow

### 3.1 Git Discipline

**Branch Strategy:**
- Never commit directly to main (enforced by `.husky/pre-commit`)
- All work on `feat/*`, `fix/*`, `chore/*`, `docs/*`, `exp/*` branches
- Squash-merge PRs for clean history
- Conventional commits required: `feat()`, `fix()`, `chore()`, `docs()`

**Release Discipline:**
- SemVer tags on every shipped build
- App version (when web/backend exist) must match current SemVer tag
- `CHANGELOG.md` updated with every tagged release (plain language for the builder)
- Tag the commit before release work begins (rollback point)
- Never force-push main

### 3.2 The Decades Development Method (Adopted)

Work moves through **four modes** — Clarify, Build, Close, Reflect — with explicit gates between them. The method front-loads human judgment into specification, so execution can proceed with minimal interruption.

**The core principle: ambiguity is the most expensive bug.** A vague spec that passes planning unchallenged produces features that technically work but miss the point.

```
CLARIFY → BUILD → CLOSE → REFLECT
  Plan        Execute      Document     Learn from
  Scrutinize  mechanically and update   what shipped,
  the spec    the plan     8 artifacts  feed into next
                                        Clarify
```

#### Clarify Mode

**Clarity Gate** (scored): before decomposing a phase into features, score Goal (40%), Constraints (30%), Success criteria (30%). Ambiguity > 0.5 → refuse to decompose, write the spec first. 0.2–0.5 → Socratic interview. ≤ 0.2 → proceed.

**Plan Scrutiny** (multi-agent, adversarial): 2-4 specialized reviewers (schema, backend, AI, UX) graded P0/P1/P2. P0 blocks implementation.

**Why:** plan-stage P0 fixes cost 5 minutes. Post-implementation P0 fixes cost hours.

#### Build Mode

Each feature: announce → deferral gate → branch → read context → plan → implement → validate → commit → push → PR → merge → update plan.

**Deferral Gate** (per feature): can I implement this now? If no, state a *specific, falsifiable* blocker. "Should happen later" is not a blocker.

**Drift Check** at sub-phase boundaries: Goal alignment (50%), Constraints (30%), Scope (20%). < 0.3 → stop, re-evaluate. Catches scope creep with numbers, not vibes.

**Build mode is boring by design.** All product decisions happened in Clarify.

#### Close Mode

Multi-agent assessment, completion report (graded), companion guide (plain-language, written for the builder's future self), atomic update of artifacts: `ROADMAP.md`, `CHANGELOG.md`, `decision-ledger.md`, `CLAUDE.md` status, `session-state.md`, `SCHEMA_REFERENCE.md` if schema changed, plus phase-specific docs.

#### Reflect Mode

Calibration table (planned vs actual size, per feature) → assumption audit → pattern check → doctrine delta → method improvement. Reflections feed mechanically into the next Clarify phase: sharper Clarity Gate, calibrated estimates, named blind spots.

This is what makes the method a loop, not a line.

#### The Method in One Sentence

**Score the spec, interrogate the ambiguity, decompose into features, scrutinize the plan, execute mechanically, measure drift, assess the result, close the books, reflect on what the work taught you, and feed those learnings into the next plan.**

### 3.3 Decision Capture

Every significant decision goes in `docs/decisions/decision-ledger.md`:

```markdown
### [YYYY-MM-DD] CATEGORY: Decision Title
**Context:** Why this was needed
**Decision:** What was decided
**Rationale:** Why this over alternatives
**Link:** Path to related doc/code
```

Categories: `ARCH`, `PROD`, `DATA`, `UX`, `OPS`, `AI`, `PRIV`.

### 3.4 Findings Protocol

Every multi-agent investigation produces a dated findings memo at `docs/findings/YYYY-MM-DD-{topic-slug}.md`.

Required sections:
1. **Hypotheses** — 3-5 explanations with confidence
2. **Investigation** — what each hypothesis checked, evidence, verdict
3. **Cross-Agent Debate** — disagreements, resolution
4. **Conclusion** — root cause, confidence, evidence
5. **Patch Plan** — actions with priority (P0/P1/P2)
6. **Open Questions**

Non-optional. No team investigation closes without a committed memo.

### 3.5 Context Retention

**Memory Spine:**
- Root `CLAUDE.md` — golden rules, system map, current status
- Domain `CLAUDE.md` files (`supabase/CLAUDE.md`, `backend/CLAUDE.md` when it lands, `web/CLAUDE.md` when it lands)
- `supabase/SCHEMA_REFERENCE.md`

**Session State Checkpoints:**
- `.claude/session-state.md`: current phase, active work, uncommitted changes, what's next
- Updated at the end of every session and after major transitions

**Resume Ritual:**
1. Read `.claude/session-state.md`
2. Read root `CLAUDE.md`
3. Check `git status` and recent commits
4. Read `docs/decisions/decision-ledger.md` for recent constraints
5. Output a context restoration summary

### 3.6 Daily Impact Accountability

Every working day produces `docs/dailyimpact/DD-MM-YY.md`. Not a dev log — an accountability document that forces each piece of work to justify itself.

Per work item: **What** / **Technical impact** / **Business impact**. Concludes with a Net Impact paragraph and a one-row-per-item summary table. Be honest. If something was maintenance with no business impact, say so.

### 3.7 Self-Healing Tooling

Skills accumulate references to files and conventions that drift. Every recurring skill should validate its own assumptions before running.

Pattern: Step 0 of any multi-step skill checks that every file, sub-skill, and naming convention it references still exists; if missing or renamed, the skill fixes itself before proceeding; self-repairs are noted in the output summary.

### 3.8 Quality Gates

**Pre-Implementation (Plan Review):**
- Schema design (RLS, CASCADE chains, soft-delete)
- API patterns (auth wiring, operator-scoping)
- AI hallucination vectors and Tier 3 safety
- Cost overruns
- Privacy claim alignment

**Post-Implementation Validation:**
- [ ] All migrations have rollback comments
- [ ] All new tables have RLS policies
- [ ] `SCHEMA_REFERENCE.md` updated
- [ ] Type checking passes
- [ ] Tests pass
- [ ] Build succeeds
- [ ] Auth wiring complete on new endpoints
- [ ] All endpoints operator-scoped
- [ ] No swallowed exceptions
- [ ] Cost tracking wired for AI calls
- [ ] Tier 2+ AI features feature-gated
- [ ] Evidence/receipts linked for AI claims
- [ ] No third-party scripts injected into the client-facing room surface

**Pre-Release Health Check:**
- Data pipeline completeness
- Security enforcement (RLS + auth coverage; public room slug isolation)
- Privacy claims match reality
- Build readiness (version match, changelog entry)
- Verdict: GO / CAVEATS / NO-GO

---

## Part IV: The Builder's Cadence

### 4.1 Work Rhythm

**Nocturnal sessions.** Most productive hours are 10pm-3am. Don't fight it — structure around it. End-of-session rituals (state checkpoint, commit, push) are critical because compaction or sleep may erase context.

**Thinking days precede velocity days.** A doctrine day (zero code, 1000+ lines of documentation) is followed by a velocity day (15+ commits). The thinking day is not wasted — it's focusing energy.

**Crisis as curriculum.** Every crisis teaches. Every lesson becomes permanent.

### 4.2 Solo Development Patterns

**Manufacturing intellectual friction.** Solo developers can't argue with themselves at 2am. Compensate with:
- Agent teams that debate proposals
- Multi-perspective code reviews (UX, data, security, privacy, trust)
- Pre-implementation plan scrutiny
- Graded assessments (letter grades, not pass/fail)
- Findings memos that force articulation

**Restraint as the primary skill.** The hardest part of solo development is deciding what NOT to build yet. For FollowRoom, the explicit feature freezes are: conversational WhatsApp bot (Phase 6, gated by user demand), full WhatsApp inbox sync (never), direct customer messaging (never in MVP), Tier 3 inferences in client-facing rooms (forever).

**Documentation changes behavior.** Write the doctrine before the code. Write the spec before the implementation. Write the finding before the fix.

### 4.3 Agent Team Coordination

**When to use agent teams:**
- Parallelizable investigation
- Multi-hypothesis debugging
- Architecture debates (propose, challenge, synthesize)
- Comprehensive audits
- Cost optimization sweeps

**When NOT to use:**
- Sequential design decisions
- Tightly coupled features
- Small tasks (< 5 minutes per agent)
- Pure discovery (single explore agent suffices)

Findings memo required before team shutdown. Grade and prioritize: P0 / P1 / P2.

### 4.4 The Product-Process Recursion

The development process should mirror the product's structure:

| Product (FollowRoom) | Process (this method) |
|---|---|
| Forwarded messages → extracted facts → relationship summary | Daily commits → phase aggregation → doctrine |
| Evidence-based facts with source receipts | Decision ledger with links and rationale |
| Operator corrections improve the relationship record | Postmortems improve the process |
| Internal memory + approved client-facing room (separate) | Internal docs + published artifacts (separate) |
| Cross-relationship meta insights surface what individual rooms can't | Reflect mode surfaces what individual phases can't |
| Celebration over correction; witness, not coach | Recognize progress; don't dwell on failures |

When the process and the product share the same philosophy, they reinforce each other.

---

## Part V: What This Signature Looks Like in Practice

### 5.1 When Starting a New Phase

1. Read `ROADMAP.md` for the phase definition
2. Score the Clarity Gate; trigger Socratic interview if fuzzy
3. Decompose into features in `docs/plans/phase-X.Y-plan.md`
4. Run multi-agent plan scrutiny
5. Resolve P0 findings before implementation

### 5.2 When Building a Feature

1. Branch (`feat/`)
2. Read context (relevant CLAUDE.md, SCHEMA_REFERENCE.md if schema)
3. Implement
4. Validate against the checklist
5. Commit with conventional message; push; PR; squash-merge
6. Update plan file (PENDING → DONE)
7. Capture any decisions in the ledger

### 5.3 When Something Breaks

1. Fix the immediate issue
2. Write the postmortem in `docs/postmortems/YYYY-MM-DD-{topic}.md`
3. Identify the principle the failure reveals
4. Update doctrine / `CLAUDE.md` / this file with the new rule
5. Build prevention architecture (make the wrong thing impossible, not just unlikely)
6. Test that the prevention doesn't breed the next failure

### 5.4 When Ending a Session

1. Commit all work (or stash with clear description)
2. Write daily impact report
3. Update `.claude/session-state.md`
4. Push to remote (branch + PR, never direct to main)
5. Significant decisions → ledger

### 5.5 When Starting a New Session

1. Resume Ritual (see §3.5)
2. Resume from where you left off

---

## Part VI: Anti-Patterns

### 6.1 Architecture Anti-Patterns

- Hard-deleting operator or ingested data without defense layers — soft-delete everything
- Trusting path parameters for authorization — always validate against the JWT
- Swallowing exceptions silently — `except Exception:` with logging, never bare `except:`
- Gating data preservation behind business logic — store the raw event first, run extraction second; never lose a forwarded message because extraction queued failed
- Cascading deletes on critical relationships — use RESTRICT
- Multiple code paths for the same destructive action — one delete function, not two
- JOINing internal memory tables into the public-room read path — published columns are explicit and isolated
- Writing extracted facts directly to client-facing fields — internal write first, then approval gate, then publish

### 6.2 Process Anti-Patterns

- Skipping the postmortem
- Deploying breaking changes with old surfaces in the field
- Writing documentation after the fact
- Amending commits after hook failures (create new commits)
- Using `git add -A` (always specify files; secrets and binaries leak otherwise)
- Treating investigation as disposable work (commit the findings memo)

### 6.3 Product Anti-Patterns

- Generic relationship summaries that could describe anyone — insist on particular language
- AI assertions without source — every fact links to its event
- Prescriptive insights — "here's what we noticed" not "here's what you should do"
- Shipping Tier 3 inferences before safeguards — false relationship-understanding compounds and is hard to retract
- Auto-publishing anything to the client-facing room
- Auto-replying via WhatsApp
- Treating the privacy policy as legal boilerplate
- Smart-quoting extracted facts in a way that makes the client think the operator wrote them

---

## Part VII: The Invariants (Non-Negotiable)

1. **User data is sacred.** Never destroy it silently. Default to preserving.
2. **Evidence over assertion.** Every claim must be verifiable to its source event.
3. **Source is immutable.** Raw user input is append-only; derived artifacts are regenerable.
4. **User corrections win.** Human judgment outranks machine extraction. Always.
5. **Defense in depth.** No single security layer is sufficient. Overlap them.
6. **Failures become doctrine.** Every crisis teaches. Every lesson becomes permanent.
7. **Document before building.** Specs focus energy. Postmortems capture wisdom.
8. **Ship fast, then fortify.** Speed reveals what quality means in practice.
9. **Restraint is the primary skill.** If you can build it but can't safeguard it, freeze it.
10. **Process mirrors product.** Build the process you'd want the product to embody.
11. **Activity is not progress.** Every piece of work must justify itself against real levers.

### FollowRoom-specific invariants (added on top of the inherited eleven):

12. **No auto-publish to client-facing surfaces.** Internal memory updates may happen on high-confidence ingestion. Anything visible to the client requires operator approval through the dashboard.
13. **No outbound WhatsApp by default.** The endpoint is silent. Outbound replies are not in MVP and would require a separate, explicitly-opted-in code path.
14. **Internal and client-facing memory are separate stores with separate visibility rules.** The published surface is a strict subset, never a JOIN-derived view.
15. **Tier 3 inferences (family dynamics, emotional state, decision-blocker speculation) never reach client-facing rooms.** Even with operator approval, the publish pipeline strips them.
16. **The operator owns the relationship.** FollowRoom never messages the operator's customers, never replaces the operator's WhatsApp workflow, never sits between the operator and their client without invitation.

---

*The principles are universal. The Decades specifics have been refit. Adapt the implementation; preserve the soul.*

*Last updated: 2026-05-16 (initial scaffold from Decades doctrine)*
