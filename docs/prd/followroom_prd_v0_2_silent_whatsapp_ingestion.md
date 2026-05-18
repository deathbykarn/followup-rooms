# FollowRoom PRD
## Dynamic Client Follow-Up Rooms for Relationship-Driven Sales

**Version:** 0.2  
**Status:** Revised scope — silent WhatsApp forwarding inbox, not conversational bot  
**Primary user:** Relationship-driven sales operator / property agent / advisor  
**Core product:** Dynamic HTML follow-up rooms that contextualize evolving client relationships via ongoing updates

---

# 1. Product Thesis

Salespeople already live inside WhatsApp, meetings, voice notes, and scattered personal notes. Their real client relationships are built across messy conversations, not inside formal CRMs.

Existing tools solve fragments of the problem:

- WhatsApp handles conversation.
- Apple Voice Memos / Otter / Zoom AI handle transcription.
- CRMs handle pipeline records.
- Notes apps handle private memory.
- Calendars and reminders handle tasks.

But none of these create a **living, client-specific relationship workspace** that turns raw conversations into structured memory, next actions, and client-facing trust assets.

**FollowRoom turns meeting transcripts and selectively forwarded WhatsApp messages into dynamic client follow-up rooms.**

Each follow-up room is a **dynamic HTML page** that contextualizes an evolving client relationship through ongoing updates.

The room should continuously capture:

- what was discussed
- what matters to the client
- what changed over time
- what was promised
- what needs follow-up
- what can be safely shared back with the client

The product has two primary ingestion paths:

## 1.1 Meeting Transcript Upload

The operator uploads or pastes a meeting transcript. FollowRoom extracts relationship intelligence and updates the relevant client room.

## 1.2 Selective WhatsApp Message Forwarding

The operator forwards selected WhatsApp messages to the FollowRoom WhatsApp number. The system receives the inbound message, identifies or proposes the relevant client room, and updates the relationship record / follow-up room.

At this stage, the WhatsApp bot is **not conversational**.

The WhatsApp number is not intended to chat with the salesperson, ask MCQ questions, run command flows, or message the salesperson’s customers. It is a **silent forwarding inbox / ingestion endpoint**.

All clarification, correction, editing, approval, and publishing happen inside the **Operator Dashboard**.

The product does not replace WhatsApp or a CRM. It sits above them.

> WhatsApp is where the conversation happens.  
> FollowRoom is where the relationship becomes organized and legible over time.

---

# 2. Problem Statement

Relationship-driven salespeople struggle with continuity across client interactions.

They often remember high-level context, but important details are scattered across:

- WhatsApp chats
- voice notes
- meeting recordings
- Apple Notes
- CRM fields
- email threads
- spreadsheets
- mental memory

This creates five problems:

1. **Lost context** — important client details get buried in chat history or transcripts.
2. **Weak follow-up** — salespeople spend time reconstructing what was discussed.
3. **Manual admin burden** — even advanced salespeople who record meetings still need to file, summarize, label, and remember action items.
4. **Client trust leakage** — clients may feel heard during the meeting, but the follow-up often arrives as scattered WhatsApp messages, long PDFs, or nothing at all.
5. **CRM mismatch** — traditional CRMs are built around pipeline management, not relationship memory.

---

# 3. Target Users

## 3.1 Primary Persona: Relationship-Driven Property Agent

A modern realtor who sees himself or herself as an advisor, entrepreneur, and relationship builder rather than a transactional salesperson.

Characteristics:

- uses WhatsApp heavily
- meets clients in person or over calls
- handles high-value, high-context decisions
- cares about personal brand and trust
- may already use voice recording and transcription
- wants to appear organized, premium, and thoughtful
- does not want a heavy CRM

Pain points:

- client context is fragmented
- follow-ups take manual effort
- nuanced concerns are hard to preserve
- spouse/family dynamics matter
- budget, timing, and emotional hesitation are difficult to track cleanly
- wants client-facing trust assets without creating PDFs manually

## 3.2 Secondary Personas

- Insurance advisors
- Wealth advisors / mortgage brokers
- Renovation / interior design consultants
- B2B salespeople / consultants
- Recruiters / talent advisors

---

# 4. Product Positioning

## 4.1 Category

**AI client memory layer for relationship-driven sales.**

## 4.2 One-Liner

**FollowRoom turns client conversations into dynamic follow-up rooms, helping salespeople remember what matters, draft better replies, and move relationships forward.**

## 4.3 Plain-English Pitch

Upload meeting transcripts or forward selected WhatsApp messages. FollowRoom identifies the client, extracts what matters, updates the relationship record, drafts your next reply in the dashboard, and generates a private client-facing room you can share.

## 4.4 What It Is Not

FollowRoom is not:

- a generic meeting summarizer
- a full CRM replacement
- a WhatsApp inbox replacement
- a conversational WhatsApp bot
- a chatbot that talks to customers on behalf of the salesperson
- a social media scheduler
- a lead generation tool

## 4.5 What It Is

FollowRoom is:

- a relationship memory layer
- a follow-up assistant
- a client room generator
- a structured case file for each client
- a bridge between WhatsApp, meetings, and client-facing follow-up
- a dynamic HTML workspace for contextualizing evolving relationships

---

# 5. Product Principles

1. **WhatsApp-native, not WhatsApp-invasive** — the salesperson forwards selected messages; the product does not need full WhatsApp inbox access.
2. **Silent ingestion first** — the WhatsApp number is a forwarding inbox, not a conversational bot.
3. **Dashboard-based resolution** — clarification, correction, editing, approval, and publishing happen in the Operator Dashboard.
4. **Internal-first, client-facing by approval** — forwarded messages and transcript insights update internal memory by default; client-facing room updates require explicit approval.
5. **Human control over publishing** — the system suggests meaning and updates, but the operator decides what becomes client-facing.
6. **Relationship memory, not raw transcripts** — raw transcripts are inputs; structured memory, decisions, tasks, and follow-up are outputs.
7. **Polished trust surface** — the client-facing room should make the client feel listened to, not analyzed.
8. **Low-friction habit formation** — important client message? Forward it to FollowRoom.

---

# 6. Core Surfaces

FollowRoom has three product surfaces.

## 6.1 Surface 1: WhatsApp Forwarding Inbox

Purpose: silent ingestion of selected WhatsApp messages.

The operator forwards important WhatsApp messages to the FollowRoom WhatsApp number. The system receives the message through the WhatsApp Business Platform webhook and processes it as an inbound relationship event.

At this stage, this is **not a conversational bot**.

The WhatsApp forwarding inbox should not:

- ask MCQ questions inside WhatsApp
- send clarifying questions through WhatsApp
- support WhatsApp slash commands
- send suggested replies back through WhatsApp
- message the operator’s customers
- attempt to replace the operator’s normal WhatsApp workflow

The WhatsApp forwarding inbox should:

- receive selected forwarded messages
- store the raw inbound event
- attempt client matching
- extract relationship intelligence
- update the relevant internal relationship record when confidence is high
- route uncertain events to the dashboard review queue
- trigger room update drafts in the dashboard

The forwarding inbox is a pipe, not the workspace.

## 6.2 Surface 2: Operator Dashboard

Purpose: command center for relationship memory, clarification, correction, editing, approval, and publishing.

Used for:

- viewing all client rooms
- reviewing auto-ingested WhatsApp events
- resolving uncertain client matches
- editing internal relationship memory
- uploading transcripts
- approving client-facing room updates
- generating suggested WhatsApp replies
- managing follow-up tasks
- searching relationship history
- reviewing cross-relationship meta intelligence

The dashboard is where meaning is resolved.

## 6.3 Surface 3: Client-Facing Follow-Up Room

Purpose: polished, private, branded dynamic HTML page that contextualizes the evolving client relationship.

Used for:

- meeting recaps
- goals
- options
- next steps
- documents
- timeline
- pending decisions
- follow-up updates
- booking/contact links

The client should not need to install an app or create an account for the MVP.

---

# 7. Core User Journey

## 7.1 Activation Journey

Goal: user reaches first magic moment in under 5 minutes.

### Step 1: Sign Up

User creates account and profile.

Fields:

- name
- company / agency
- role
- industry
- profile photo
- WhatsApp number
- default language
- preferred tone

### Step 2: Create First Client Room

User creates their first client room through the dashboard.

Minimum client fields:

- client name
- relationship type
- short context
- optional phone number
- optional tags

Example:

> Sarah Tan — HDB upgrade, East Coast, budget around $1.8M

### Step 3: Upload Meeting Transcript or Paste WhatsApp Snippet

User can validate the product immediately through web-first ingestion.

Input options:

- paste meeting transcript
- upload meeting transcript
- paste WhatsApp snippet manually
- add manual note

The system extracts relationship intelligence and updates the client room.

### Step 4: Save FollowRoom WhatsApp Number

The product shows:

> Save this number as FollowRoom Inbox. Forward important client messages here.

Important onboarding language:

> This number is a forwarding inbox, not a conversational assistant. Forward selected messages when you want them added to a client relationship record. Review and edit all updates in your dashboard.

### Step 5: Forward First WhatsApp Message

User forwards a selected client WhatsApp message to the FollowRoom number.

The system receives the inbound event and processes it silently.

If client matching confidence is high:

- internal relationship record is updated
- client-facing room update draft is created if relevant
- suggested reply is generated in the dashboard

If confidence is low:

- event is placed in the dashboard under “Needs Review” or “Unassigned”
- operator chooses the correct client in the dashboard

No WhatsApp reply is sent by default.

### Step 6: First Magic Output

Dashboard shows:

```text
New relationship event added to Sarah Tan.

Detected:
- Budget concern
- Spouse preference
- Location constraint

Suggested next reply:
“Totally fair. Let’s anchor this around comfort first, not maximum affordability. I’ll prepare a simple comparison showing options near Marine Parade, with estimated monthly repayment ranges, so both of you can review calmly.”

Suggested room update:
“Key consideration added: monthly repayment comfort and preference for Marine Parade / family proximity.”

Actions:
[Approve room update]
[Edit]
[Keep internal only]
[Create follow-up task]
```

### Step 7: Client Room Evolves Over Time

The same room continues to update through:

- meeting transcript uploads
- forwarded WhatsApp messages
- manual notes
- uploaded documents
- operator edits

The room becomes the dynamic relationship record.

---

# 8. Core Functional Requirements

## 8.1 Account and User Profile

Users must be able to:

- sign up and log in
- create a salesperson profile
- add company/agency branding
- upload profile image
- set industry and room template
- link WhatsApp number to account if required
- configure ingestion defaults

Profile fields:

```text
user_id
name
email
phone_number
company_name
role_title
industry
profile_photo_url
default_language
default_tone
timezone
created_at
updated_at
```

## 8.2 WhatsApp Forwarding Inbox Setup

Users must be able to:

- save the FollowRoom WhatsApp number
- link their WhatsApp identity to their FollowRoom account if required
- forward selected client messages to the FollowRoom number
- see forwarded messages appear in the Operator Dashboard
- review, correct, and approve updates in the dashboard

Explicit non-goals for this stage:

- no MCQ questions inside WhatsApp
- no clarifying questions through WhatsApp
- no slash commands inside WhatsApp
- no generated replies inside WhatsApp
- no room links sent back through WhatsApp
- no messaging of operator’s customers
- no WhatsApp state machine for client selection

Intended behavior:

```text
Operator forwards selected WhatsApp message
→ FollowRoom receives inbound webhook
→ Event is stored
→ AI attempts client matching
→ High-confidence events update the internal relationship record
→ Low-confidence events go to dashboard review queue
→ Suggested replies and room updates appear in dashboard
```

## 8.3 Client Creation and Management

Users must be able to:

- create client manually
- create client from forwarded WhatsApp event
- create client from transcript upload
- edit client profile
- add aliases
- add tags
- archive client
- search client list
- merge duplicate clients

Client fields:

```text
client_id
user_id
client_name
phone_number
aliases
relationship_type
status
tags
short_context
room_id
created_at
updated_at
```

Relationship types for real estate MVP:

- buyer
- seller
- landlord
- tenant
- investor
- commercial landlord
- commercial tenant
- referral partner
- other

## 8.4 Forwarded WhatsApp Message Processing

When the operator forwards a WhatsApp message to the FollowRoom number, the system must:

1. receive the inbound message via webhook
2. capture the raw forwarded content
3. store it as an event
4. attempt to match it to an existing client room
5. extract structured relationship intelligence
6. update the internal relationship record if client confidence is high
7. create a “Needs Review” item if client confidence is medium or low
8. draft a client-facing room update if relevant
9. generate a suggested WhatsApp reply in the dashboard
10. surface any follow-up task in the dashboard

No WhatsApp reply should be sent by default.

### Confidence Tiers

#### High Confidence

System silently attaches event to likely client and shows it in dashboard activity.

```text
Forwarded WhatsApp message added to Tan Family.
Confidence: High

Detected:
- Monthly repayment concern
- Marine Parade preference
- Spouse/family consideration

Actions:
[Review]
[Undo]
[Move to another client]
[Approve room update]
```

#### Medium Confidence

System creates a dashboard review item.

```text
New WhatsApp forward needs confirmation.

Likely clients:
1. Tan Family — HDB upgrade / East Coast
2. Lim Couple — Condo shortlist / D15
3. Sarah Ong — First-time buyer / affordability

Actions:
[Confirm Tan Family]
[Choose another]
[Create new client]
[Keep unassigned]
```

#### Low Confidence

System saves the event as unassigned.

```text
Unassigned WhatsApp forward.

Actions:
[Search client]
[Create new client]
[Discard]
```

## 8.5 Clarification and Review Questions

Clarification should happen inside the Operator Dashboard, not inside WhatsApp.

After a forwarded WhatsApp message or transcript is processed, the dashboard should ask only what is needed to safely proceed.

Default review card:

```text
How should this update be treated?

[Internal note only]
[Draft client-facing update]
[Create follow-up task]
[Generate suggested reply]
[All except client-facing]
```

Recommended default: **All except client-facing update**.

Rules:

- The system may update internal memory automatically when confidence is high.
- The system must not publish client-facing updates without operator approval.

## 8.6 Meeting Transcript Upload

Users must be able to:

- upload audio file
- upload transcript file
- paste transcript
- assign transcript to client
- create client from transcript
- extract structured meeting intelligence
- generate client-facing recap
- generate internal notes
- generate follow-up tasks
- generate WhatsApp-ready reply in the dashboard

Supported MVP inputs:

- plain text transcript
- TXT transcript upload
- PDF transcript upload if parsing is straightforward

Transcript processing output:

- meeting summary
- client goals
- constraints
- budget / price range
- timeline
- decision-makers
- objections
- emotional concerns
- promised follow-ups
- documents mentioned
- recommended next action
- client-facing recap draft
- suggested WhatsApp follow-up message

## 8.7 Internal Relationship Record

The internal record is the operator’s private memory layer.

It should include:

- relationship summary
- client profile
- goals
- constraints
- preferences
- objections
- decision-maker dynamics
- emotional concerns
- timeline
- budget
- open loops
- promised follow-ups
- suggested next actions
- draft replies
- event history
- meeting summaries
- forwarded WhatsApp snippets
- documents
- tasks

Sensitive insights should stay internal by default.

Example:

- internal note: “Spouse may be blocker.”
- client-facing version: “Both decision-makers may want to align on timing and comfort level.”

## 8.8 Client-Facing Follow-Up Room

The client-facing room is a polished, private, branded dynamic HTML page that helps the client review discussions and next steps.

MVP page sections:

- header with salesperson branding
- client / project title
- last updated date
- conversation recap
- client goals
- key considerations
- options being explored
- recommended next steps
- documents / links
- pending questions
- timeline
- contact / book follow-up button

Client access:

- private link
- optional passcode
- no client login required

## 8.9 Room Update Approval

Client-facing updates must require user approval.

Dashboard should show:

```text
Suggested client-facing room update:

“Key consideration added: monthly repayment comfort and proximity to family support.”

Actions:
[Publish]
[Edit]
[Keep internal only]
```

## 8.10 Suggested Replies

System must generate WhatsApp-ready replies in the dashboard based on:

- client context
- latest message
- salesperson tone
- relationship stage
- industry template
- internal memory

Replies should be:

- human
- concise
- useful
- low-pressure
- context-aware
- not obviously AI-generated
- aligned with salesperson’s brand

## 8.11 Follow-Up Tasks

System should detect and create follow-up tasks.

Task sources:

- promises made in meeting transcript
- client requests in WhatsApp
- salesperson manual instruction
- AI-suggested next action

Task fields:

```text
task_id
client_id
user_id
title
description
due_date
status
source_event_id
created_at
updated_at
```

## 8.12 Unassigned / Needs Review Queue

If the system cannot identify a client, it should save the event into a dashboard queue.

Queue types:

- unassigned WhatsApp forward
- uncertain client match
- unclear transcript
- duplicate client candidate
- room update requiring approval
- sensitive note requiring review

Dashboard actions:

- assign to existing client
- create new client
- keep unassigned
- discard
- mark sensitive
- approve update
- edit extracted facts

---

# 9. Data Model

## 9.1 User

```text
user_id
name
email
phone_number
company_name
role_title
industry
profile_photo_url
default_language
default_tone
timezone
created_at
updated_at
```

## 9.2 Client

```text
client_id
user_id
client_name
phone_number
aliases
relationship_type
status
tags
short_context
room_id
created_at
updated_at
```

## 9.3 Room

```text
room_id
client_id
user_id
public_slug
access_mode
passcode_hash
client_visible_sections
internal_summary
last_published_at
created_at
updated_at
```

## 9.4 Event

```text
event_id
client_id
user_id
source_type
raw_text
raw_file_url
summary
extracted_facts
confidence_score
visibility
processing_status
created_at
updated_at
```

Source types:

- whatsapp_forward
- whatsapp_paste
- meeting_transcript
- manual_note
- document_upload
- future_api_ingestion

Processing statuses:

- received
- processed
- needs_review
- assigned
- published
- discarded

## 9.5 Extracted Fact

```text
fact_id
event_id
client_id
fact_type
fact_value
confidence_score
visibility
created_at
```

Fact types:

- goal
- budget_constraint
- timeline_signal
- objection
- spouse_family_factor
- emotional_hesitation
- document_request
- follow_up_promise
- viewing_preference
- property_preference
- decision_blocker
- buying_intent_signal
- market_signal
- content_opportunity

## 9.6 Task

```text
task_id
client_id
user_id
title
description
due_date
status
source_event_id
created_at
updated_at
```

## 9.7 Suggested Reply

```text
reply_id
client_id
event_id
suggested_text
status
created_at
updated_at
```

Statuses:

- draft
- copied
- edited
- discarded

## 9.8 Room Update Draft

```text
update_id
room_id
client_id
event_id
draft_text
status
published_at
created_at
updated_at
```

Statuses:

- draft
- approved
- edited
- published
- rejected

## 9.9 Review Queue Item

```text
review_id
user_id
event_id
client_id_nullable
review_type
suggested_client_ids
confidence_score
status
created_at
updated_at
```

Review types:

- client_match_uncertain
- unassigned_event
- sensitive_note
- room_update_pending
- duplicate_client_candidate

---

# 10. AI Processing Pipeline

## 10.1 Input Types

- forwarded WhatsApp message
- pasted WhatsApp snippet
- meeting transcript
- audio transcript
- manual note
- document summary

## 10.2 Pipeline Steps

1. **Normalize input** — clean text, remove noise, identify message boundaries, detect language.
2. **Client matching** — use aliases, names, phone numbers, past context, property names, location references, previous concerns, semantic similarity.
3. **Event classification** — classify input as requirement, objection, budget update, timeline update, location preference, document request, decision-maker signal, follow-up need, buying/selling intent, or general note.
4. **Fact extraction** — extract structured facts.
5. **Internal memory update** — append event and extracted facts to internal relationship record.
6. **Suggested next action** — generate recommended next action.
7. **Suggested reply** — generate WhatsApp-ready response in the dashboard.
8. **Client-facing draft** — generate sanitized client-facing update if appropriate.
9. **Approval gate** — only publish client-facing updates after operator approval.

Example extracted facts:

```json
{
  "budget_concern": "Monthly repayment comfort",
  "location_preference": "Marine Parade / near parents",
  "decision_maker": "Wife's preference is important",
  "next_action": "Prepare repayment scenario comparison"
}
```

---

# 11. Prompting / AI Behavior Requirements

## 11.1 Internal Memory Prompt Should

- preserve nuance
- extract actionable facts
- identify uncertainty
- avoid overclaiming
- separate stated facts from inferred insights
- mark sensitive notes as internal
- preserve original evidence reference

## 11.2 Client-Facing Prompt Should

- rewrite tactfully
- avoid exposing private inferences
- avoid sales pressure
- use professional tone
- emphasize clarity, next steps, and usefulness
- avoid saying “AI detected” or similar phrases

## 11.3 Reply Prompt Should

- sound like the salesperson
- be short enough for WhatsApp
- use the client’s actual concern
- move the relationship forward
- avoid overexplaining
- avoid hard sell

## 11.4 Safety Rule

Never auto-publish inferred emotional or family dynamics into client-facing rooms.

---

# 12. Privacy and Trust Requirements

MVP must include:

- clear privacy policy
- data deletion option
- client room access controls
- internal vs client-facing separation
- no auto-publishing of sensitive notes
- no direct customer messaging by default
- no full WhatsApp inbox ingestion

The salesperson is responsible for ensuring they have the right to process or store client conversation data. The product should provide user-facing reminders and configurable consent language.

Client room security:

- private unlisted URL
- optional passcode
- ability to revoke link
- ability to regenerate link

Data retention controls:

- delete client
- delete room
- delete event
- delete uploaded transcript/audio
- export client record

---

# 13. WhatsApp Integration Strategy

## 13.1 MVP Strategy

The MVP WhatsApp component is a **silent forwarding inbox**, not a conversational bot.

The operator forwards selected WhatsApp messages to the FollowRoom WhatsApp number. The system receives inbound messages via WhatsApp Business Platform webhook and processes them as relationship events.

The endpoint should not reply by default.

The endpoint should not ask MCQ questions, run slash commands, send suggested replies, or message the operator’s customers in this stage.

## 13.2 Why This Strategy

This approach preserves the intended user behavior:

> The salesperson keeps using normal WhatsApp with clients. When a message matters, they forward it to FollowRoom. FollowRoom updates the dynamic relationship room.

This avoids:

- full WhatsApp inbox access
- WhatsApp Web scraping
- forcing migration of customer conversations
- direct customer automation
- conversational bot complexity
- unnecessary outbound WhatsApp costs
- MCQ/state-machine friction inside WhatsApp

## 13.3 Recommended WhatsApp Flow

1. User saves FollowRoom WhatsApp number.
2. User forwards selected client message to FollowRoom.
3. FollowRoom receives inbound message webhook.
4. Backend stores raw event.
5. AI attempts client matching.
6. High-confidence match updates internal relationship record.
7. Low-confidence match appears in dashboard review queue.
8. Dashboard shows suggested reply, room update draft, and possible follow-up task.
9. Operator reviews, edits, approves, or publishes from dashboard.
10. Operator manually sends reply or room link to client through their normal WhatsApp chat if desired.

## 13.4 Cost Principle

Because the WhatsApp endpoint is silent by default, the product should avoid unnecessary outbound WhatsApp messages.

Charges should mainly be considered if/when FollowRoom sends outbound WhatsApp messages. The MVP should be designed so outbound WhatsApp replies are optional and disabled by default.

## 13.5 Constraints to Validate During Build

- WhatsApp Business Platform setup requirements
- inbound webhook reliability
- whether forwarded messages preserve enough original content
- whether forwarded contact cards can be parsed reliably
- how inbound-only usage is handled commercially by the chosen provider
- whether the business number needs any outbound templates for onboarding or support
- data privacy and consent language for forwarded client conversations

## 13.6 Fallback If WhatsApp Setup Is Deferred

Build web-first ingestion first:

- paste WhatsApp snippet into dashboard
- upload transcript
- generate room
- copy reply
- share link manually

Then add WhatsApp forwarding as a silent inbound channel using the same event ingestion pipeline.

---

# 14. Operator Dashboard Requirements

The Operator Dashboard is the salesperson’s control tower. It is where the user sees all client rooms, reviews relationship intelligence, edits records, approves client-facing updates, and adds new context manually.

## 14.1 Dashboard Home

Required sections:

- active client rooms
- recently updated clients
- follow-up tasks due today / this week
- draft client-facing updates awaiting approval
- unassigned WhatsApp notes
- recent meeting transcript uploads
- clients with stale follow-up
- high-intent or urgent client signals
- cross-relationship meta insights

Example:

```text
Today
- 3 follow-ups due
- 2 rooms awaiting approval
- 1 unassigned WhatsApp note

Recently Updated Rooms
1. Tan Family — HDB upgrade / East Coast
   Latest signal: monthly repayment concern
   Next action: prepare affordability comparison

2. Lim Holdings — Commercial lease
   Latest signal: wants revised rental range
   Next action: send comparable units
```

## 14.2 Client Room List

Users must be able to:

- view all client rooms
- search by client name, alias, tag, property, location, or concern
- filter by relationship type
- filter by status
- filter by last updated date
- filter by open tasks
- filter by unpublished updates
- sort by urgency, recent activity, stale follow-up, or room status
- open any client room
- create new client room
- archive inactive room

Suggested columns:

- client / room name
- relationship type
- status
- latest signal
- next action
- last updated
- open tasks
- client-facing room status

Example statuses:

- new lead
- active discussion
- awaiting client decision
- follow-up needed
- proposal sent
- viewing scheduled
- closed won
- closed lost
- dormant
- archived

## 14.3 Client Detail Workspace

Required tabs:

1. **Overview** — relationship summary, latest status, next action, room link.
2. **Internal Memory** — private relationship intelligence.
3. **Client-Facing Room** — preview and edit what the client sees.
4. **Events** — timeline of WhatsApp forwards, transcripts, manual notes, documents, updates.
5. **Tasks** — follow-up tasks, due dates, statuses, source events.
6. **Files** — transcripts, documents, property links, PDFs, images.
7. **Draft Replies** — AI-generated WhatsApp replies.
8. **Room Update Drafts** — pending client-facing updates.

---

# 15. Cross-Relationship Meta Intelligence Layer

The dashboard must surface meta intelligence across all client rooms.

This is not just a task-alert system. It is the sensemaking layer that helps the operator see patterns across their whole relationship portfolio.

The product should naturally surface meaning from accumulated relationship data: recurring objections, common client anxieties, emerging market signals, neglected opportunities, trust-building moments, and patterns in the salesperson’s own follow-up behavior.

The operator should not merely see a list of clients. They should see what their relationship universe is trying to tell them.

## 15.1 Operational Intelligence

The system should identify:

- which clients need follow-up
- which relationships have gone stale
- which clients show high buying/selling intent
- which clients have unresolved objections
- which clients have pending documents
- which clients are waiting on the salesperson
- which clients may be ready for the next step
- which client rooms have unpublished useful updates
- which conversations contain sensitive notes that should not be client-facing

## 15.2 Cross-Relationship Pattern Intelligence

The system should identify recurring themes across clients.

Examples:

- multiple clients are worried about monthly repayment comfort
- several buyers are delaying decisions until bonus season
- spouse/family alignment is repeatedly appearing as a blocker
- clients are asking similar ABSD or financing questions
- several prospects are stuck at the same decision stage

## 15.3 Market Signal Intelligence

For real estate users, the system should detect bottom-up market signals from client conversations.

Examples:

- “More buyers are asking about affordability rather than capital appreciation this month.”
- “Commercial tenants are increasingly asking for shorter lease flexibility.”
- “Family proximity is appearing more often than school proximity in recent buyer conversations.”

This should not pretend to be formal market research. It is conversation-derived field intelligence.

## 15.4 Operator Behavior Intelligence

The dashboard should also reflect the salesperson’s own operating patterns.

Examples:

- which types of clients receive fast follow-up
- which clients are repeatedly delayed
- which promised actions are commonly missed
- which relationship types tend to go stale
- whether the operator is over-serving low-intent clients and under-serving high-intent ones

## 15.5 Meaningful Narrative Summaries

Daily brief example:

```text
Today’s relationship picture:

You have 3 clients waiting on promised follow-ups. The strongest buying signal is from Sarah Ong, who asked about both loan eligibility and unit availability. Across recent conversations, affordability comfort is appearing more often than location aspiration.
```

Weekly digest example:

```text
This week, your client conversations clustered around three themes:

1. Affordability anxiety
Several clients are no longer asking “What can I buy?” but “What can I comfortably sustain?”

2. Family-aligned decision-making
Spouse and parent proximity appeared in 4 active conversations, suggesting family logistics are becoming a stronger decision driver.

3. Delayed action
Three clients expressed interest but pushed action beyond bonus season. This may be a good moment to prepare lower-pressure planning content rather than hard-sell messages.
```

## 15.6 Cross-Relationship Cards

Example cards:

```text
Recurring Concern
Monthly repayment comfort appeared in 5 client conversations this month.
Suggested action: Create a reusable affordability explainer.
```

```text
Content Opportunity
ABSD came up in 4 active rooms.
Suggested action: Create a short explainer and attach it to relevant client rooms.
```

```text
Relationship Risk
Two high-intent clients have not received updates in over 7 days.
Suggested action: Send soft check-ins today.
```

## 15.7 MVP Meta Intelligence Requirements

For MVP, include a lightweight version:

1. follow-up needed across clients
2. stale relationship detection
3. high-intent signal detection
4. recurring objection/theme detection
5. unpublished room update opportunities
6. weekly relationship digest
7. content/reusable asset suggestions based on repeated client questions

---

# 16. Editing, Tweaking, and Manual Additions

Operators must be able to manually edit, correct, and add context.

Users must be able to:

- edit client profile
- rename room
- edit short context
- add aliases
- add tags
- correct AI-extracted facts
- delete incorrect facts
- mark notes as sensitive
- move notes between clients
- merge duplicate clients
- add manual notes
- add files/links
- edit client-facing room sections
- approve or reject AI-generated room updates
- rewrite suggested replies
- mark tasks complete
- change task due dates

Manual add types:

- add note
- add task
- add document
- add property link
- add meeting summary
- add client preference
- add objection
- add budget/timeline update
- add internal-only sensitive note
- add client-facing update draft

---

# 17. Room Publishing Controls

The dashboard must let the operator control what the client sees.

Users must be able to:

- preview client-facing room
- edit room sections
- approve AI-drafted updates
- reject AI-drafted updates
- publish updates
- unpublish sections
- regenerate room link
- revoke room link
- set passcode
- copy room link
- view last published timestamp

---

# 18. Search Across Relationship Memory

Users should be able to search across all client rooms.

Example searches:

- “Marine Parade”
- “ABSD concern”
- “monthly repayment”
- “commercial lease”
- “wife prefers”
- “waiting for documents”

Search results should show:

- client name
- matching event or fact
- source type
- date
- internal/client-facing visibility
- link to client workspace

---

# 19. MVP Scope

## 19.1 MVP Must Have

1. User signup and profile
2. Basic web dashboard
3. Client creation
4. Client list/search
5. Dynamic client follow-up room generation
6. Internal relationship record
7. Meeting transcript upload / paste
8. Manual WhatsApp snippet paste
9. Generic event ingestion model
10. AI extraction from transcripts and WhatsApp snippets
11. Client matching with confidence score
12. Unassigned / Needs Review queue
13. Suggested reply generation in dashboard
14. Basic follow-up task creation
15. Client-facing room preview/editor
16. Manual approval before publishing room updates
17. Copy/share room link
18. Optional passcode for room
19. Basic cross-relationship meta insights
20. Architecture ready for future silent WhatsApp inbound webhooks

Optional in MVP if WhatsApp setup is available:

- silent inbound WhatsApp forwarding endpoint that receives and stores forwarded messages
- no outbound replies by default

## 19.2 MVP Should Not Have

- conversational WhatsApp bot
- WhatsApp MCQ flows
- WhatsApp slash commands
- WhatsApp outbound suggested replies
- direct customer messaging automation
- full CRM pipeline
- calendar scheduling
- WhatsApp inbox sync
- browser extension
- native mobile app
- Salesforce integration
- Zapier integration
- social media posting
- payment collection
- complex analytics
- multi-agent team management

---

# 20. MVP User Stories

## 20.1 Forwarded WhatsApp Message

As a property agent, I want to forward an important WhatsApp message to the FollowRoom inbox so that the client relationship record updates without me manually filing notes.

Acceptance criteria:

- inbound forwarded message is received
- raw event is stored
- system attempts client match
- high-confidence event updates internal record
- low-confidence event goes to review queue
- no WhatsApp reply is sent by default

## 20.2 Transcript Upload

As a property agent, I want to upload a meeting transcript so that the full discussion becomes structured notes and next steps.

Acceptance criteria:

- user can upload/paste transcript
- user selects or creates client
- system extracts summary, goals, concerns, tasks
- system proposes client-facing room update

## 20.3 Suggested Reply

As a property agent, I want the dashboard to draft a reply so that I can respond faster and more thoughtfully.

Acceptance criteria:

- reply uses client context
- reply is WhatsApp-length
- user can copy it
- reply is not sent automatically

## 20.4 Client-Facing Room

As a property agent, I want a client-facing page so that clients can review our discussion clearly.

Acceptance criteria:

- room is generated
- user can edit before publishing
- user can copy private link
- room has branded header and useful sections

## 20.5 Sensitive Notes

As a property agent, I want sensitive insights to remain private so that I do not accidentally expose internal notes.

Acceptance criteria:

- internal and client-facing sections are separate
- sensitive insights default to internal
- client-facing updates require approval

---

# 21. Success Metrics

Activation metrics:

- % users who create first client
- % users who upload first transcript
- % users who paste or forward first WhatsApp message
- time to first generated reply
- time to first client room
- % users who publish first room update

Engagement metrics:

- forwarded/pasted messages per active user per week
- transcripts uploaded per user per month
- rooms updated per user per week
- suggested replies copied
- follow-up tasks created
- follow-up tasks completed
- review queue items resolved

Value metrics:

- % users who share a room link with client
- repeat room updates per client
- user-reported time saved
- user-reported follow-up quality
- client room revisit rate
- number of active client rooms per user

Retention metrics:

- week 1 retention
- week 4 retention
- monthly active users
- number of users with 5+ active rooms
- number of users with 20+ relationship events

Monetization metrics:

- free-to-paid conversion
- average revenue per user
- rooms created per paid user
- cost per processed message/transcript
- gross margin per paid user

---

# 22. Pricing Hypothesis

## Free Tier

- 3 active client rooms
- limited relationship events/month
- limited transcript uploads/month
- basic branding
- watermark

## Pro Tier: $19–$39/month

- more active rooms
- higher event limits
- transcript uploads
- branded rooms
- suggested replies
- follow-up tasks
- room links

## Premium Tier: $59–$99/month

- unlimited or high room limit
- advanced templates
- custom branding
- analytics
- passcode rooms
- file attachments
- export
- priority processing

Recommended initial pricing test: **$29/month for solo professionals**.

---

# 23. Roadmap

## Phase 0: Prototype

Goal: prove output quality.

Build:

- manual transcript/chat paste
- AI extraction
- static generated room
- suggested reply
- manual client selection

No WhatsApp bot yet.

## Phase 1: Web-First MVP

Goal: prove core relationship-room workflow.

Build:

- operator dashboard
- client creation
- client room list
- internal memory
- client-facing dynamic HTML room
- transcript upload/paste
- WhatsApp snippet paste
- event ingestion model
- review queue
- suggested replies in dashboard
- basic meta-insights

## Phase 1.5: Silent WhatsApp Forwarding Inbox

Goal: add WhatsApp as an inbound pipe, not a conversational bot.

Build:

- WhatsApp Business Platform webhook
- inbound message storage
- event creation from forwarded messages
- client matching
- dashboard review queue
- no outbound replies by default

## Phase 2: Relationship Memory System

Goal: make rooms compound over time.

Build:

- event timeline
- fact memory
- open loops
- follow-up task intelligence
- room update diffing
- search across clients
- better client matching

## Phase 3: Vertical Templates

Goal: deepen value for target industries.

Build templates for:

- real estate buyer
- real estate seller
- commercial property
- insurance
- wealth advisory
- renovation
- B2B sales

## Phase 4: Collaboration and Team Features

Goal: support agencies and teams.

Build:

- multi-user accounts
- shared branding
- manager view
- team templates
- permissioning
- audit logs

## Phase 5: Integrations

Goal: reduce manual work for power users.

Potential integrations:

- Google Drive
- Calendar
- Zoom
- Otter
- HubSpot
- Salesforce
- Zapier/Make
- Email

## Phase 6: Optional Conversational Bot Layer

Goal: only if user demand proves strong.

Potential features:

- WhatsApp confirmation replies
- WhatsApp command flow
- WhatsApp reminders
- WhatsApp suggested reply delivery
- templates for proactive messages

This should not be MVP.

---

# 24. Technical Architecture

## 24.1 Recommended Stack

Frontend:

- Next.js
- Tailwind
- React

Backend:

- FastAPI or Next.js API routes
- Python preferred if AI pipeline is complex

Database:

- Supabase Postgres
- pgvector optional for semantic client matching

Storage:

- Supabase Storage or S3-compatible storage

AI:

- OpenAI / Anthropic for extraction and generation
- model abstraction layer recommended

Messaging:

- WhatsApp Business Platform / Cloud API for future silent forwarding inbox
- webhooks for inbound messages only in Phase 1.5

Authentication:

- Supabase Auth or Clerk

Deployment:

- Railway / Render / Fly.io for MVP
- Cloudflare for DNS/security

## 24.2 Services

### Event Ingestion Service

Handles:

- pasted WhatsApp snippets
- transcript uploads
- manual notes
- future WhatsApp webhook events

### AI Processing Service

Handles:

- transcript analysis
- message classification
- fact extraction
- reply generation
- room update drafting
- meta-insight classification

### Room Service

Handles:

- room generation
- room publishing
- room link access
- passcode validation

### Review Queue Service

Handles:

- uncertain client matches
- unassigned notes
- sensitive notes
- pending room updates

### Task Service

Handles:

- follow-up task creation
- reminders
- completion status

### Dashboard API

Handles:

- client CRUD
- room editing
- transcript upload
- event review

---

# 25. Risk Register

## 25.1 WhatsApp Platform Constraints

The silent forwarding inbox may face setup, webhook, or commercial constraints.

Mitigation:

- build web-first ingestion first
- keep WhatsApp inbound-only by default
- avoid direct customer automation
- validate inbound-only pricing and forwarding behavior early

## 25.2 Wrong Client Matching

System may attach message to wrong client.

Mitigation:

- confidence thresholds
- dashboard review queue
- undo/move event
- unassigned queue
- no silent client-facing updates

## 25.3 Creepy Client-Facing Output

System may expose sensitive inferred insights.

Mitigation:

- internal/client-facing separation
- approval gate
- tactful rewrite layer
- sensitive category detection

## 25.4 Users Do Not Build Forwarding Habit

Salespeople may forget to forward messages.

Mitigation:

- make first experience magical
- simple onboarding
- dashboard reminders
- weekly relationship digest

## 25.5 Output Quality Is Too Generic

Suggested replies may sound like generic AI.

Mitigation:

- tone calibration
- user examples
- industry templates
- memory-aware replies
- short WhatsApp-native style

## 25.6 Market Misunderstanding

Market may think this is just another meeting summarizer or CRM.

Mitigation:

- position as client memory layer
- lead with dynamic room demo
- show WhatsApp-to-room workflow
- emphasize living relationship record

## 25.7 Privacy Concerns

Users may worry about uploading or forwarding client conversations.

Mitigation:

- clear data controls
- delete/export options
- no full inbox ingestion
- optional redaction later
- strong privacy messaging

---

# 26. Open Questions

## 26.1 Product Questions

1. Should first vertical be real estate only or broader relationship sales?
2. Should client-facing room be enabled by default or optional?
3. Should transcripts be required for best experience, or should WhatsApp forwarding be enough?
4. Should WhatsApp silent ingestion be Phase 1.5 or included in Phase 1?
5. What is the minimum room that feels premium enough to share?

## 26.2 Technical Questions

1. What metadata is preserved when forwarding WhatsApp messages to the FollowRoom number?
2. Can contact cards be reliably parsed?
3. What is the fastest path to provisioning a WhatsApp Business Platform number?
4. Is inbound-only webhook ingestion commercially straightforward?
5. What is the best model/cost tradeoff for short message extraction?
6. Should semantic client matching use pgvector from day one?

## 26.3 GTM Questions

1. Which users have the strongest pain: property agents, insurance agents, mortgage brokers, or consultants?
2. Will users pay for client rooms before live WhatsApp integration?
3. Does the phrase “follow-up room” resonate?
4. Is the strongest promise time-saving, better follow-up, or premium client trust?
5. Should rooms include view analytics from day one?

---

# 27. Recommended First Build Scope

Recommended answer to builders:

```text
Build Phase 1 web-first MVP with silent-ingestion-ready architecture.

Deliver:
- Operator dashboard
- Client list / client rooms
- Client detail workspace
- Internal relationship memory
- Client-facing dynamic HTML room preview/editor
- Transcript upload/paste
- Paste WhatsApp snippet manually
- Generic event ingestion model
- AI extraction
- Client matching with confidence score
- Unassigned / Needs Review queue
- Suggested reply generated in dashboard
- Room update approval flow
- Basic cross-relationship meta insights
- Supabase schema + RLS for MVP entities

Defer:
- Conversational WhatsApp bot
- WhatsApp MCQ flows
- WhatsApp outbound replies
- WhatsApp command state machine
- Direct customer messaging
```

WhatsApp intake clarification:

```text
The intended WhatsApp flow is silent inbound ingestion.

The salesperson forwards selected WhatsApp messages to the FollowRoom WhatsApp Business number.
The system receives the message via webhook and updates the relationship record / follow-up room.
The bot does not reply by default.
All clarification, correction, approval, and publishing happen in the Operator Dashboard.
```

---

# 28. Demo Script

## Scene 1: Messy WhatsApp Conversation

Client says:

> We’re still worried about monthly repayment. My wife also prefers Marine Parade because her parents are nearby. Maybe we should wait until after bonus.

## Scene 2: Forward to FollowRoom Inbox

Salesperson forwards the selected WhatsApp message to the FollowRoom WhatsApp number.

The WhatsApp endpoint does not reply.

## Scene 3: Silent Ingestion

FollowRoom receives the inbound message and processes it.

If confidence is high, the event is attached to the likely client room.

If confidence is low, it appears under Needs Review in the Operator Dashboard.

## Scene 4: Operator Dashboard Review

Dashboard shows:

```text
New WhatsApp event added to Tan Family.
Confidence: High

Detected:
- Monthly repayment concern
- Spouse preference matters
- Location priority: Marine Parade / near parents
- Timeline may shift until after bonus

Suggested next action:
Prepare 3 scenarios — buy now, wait 6 months, sell first.

Suggested reply:
“Totally fair. Let’s anchor this around comfort first, not maximum affordability. I’ll prepare a simple comparison showing options near Marine Parade, with estimated monthly repayment ranges, so both of you can review calmly.”

Suggested client-facing room update:
“Key consideration added: monthly repayment comfort, timing after bonus, and preference for Marine Parade / family proximity.”

Actions:
[Approve room update]
[Edit]
[Keep internal only]
[Create task]
[Copy suggested reply]
```

## Scene 5: Dynamic Client Room Updates

The client-facing follow-up room now reflects the approved update:

- goals
- key considerations
- options
- next steps
- open questions

## Scene 6: Operator Shares Link Manually

Salesperson sends through normal WhatsApp:

> I’ve updated your private planning page with the main considerations and next steps before our next chat.

## Scene 7: Value Moment

Salesperson did not need to:

- search old WhatsApp messages
- rewrite notes manually
- create a PDF
- update CRM fields
- draft from scratch

Client feels:

- remembered
- respected
- guided
- clear on next steps

---

# 29. Final Product Thesis

FollowRoom is the client memory layer for relationship-driven sales.

It does not replace WhatsApp, CRMs, or meeting recorders. It connects them into a living client relationship workspace.

The wedge is simple:

> Upload meeting transcripts or forward selected WhatsApp messages. FollowRoom updates a dynamic relationship room that helps you remember what matters, follow up better, and make clients feel properly seen.

The deeper strategic bet:

> In high-trust sales, the salesperson who remembers better follows up better. The salesperson who follows up better wins more trust. FollowRoom makes memory operational.
