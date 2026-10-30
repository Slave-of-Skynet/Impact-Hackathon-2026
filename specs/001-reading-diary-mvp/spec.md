# Feature Specification: Gustul Cărților — P0 reading-diary vertical slice

**Feature Branch**: `001-reading-diary-mvp`

**Created**: 2026-10-30

**Status**: Draft — proposal for independent review ([Issue #7](https://github.com/Slave-of-Skynet/Impact-Hackathon-2026/issues/7)); not partner-approved

**Input**: User description: "Gustul Cartilor P0 vertical slice: reading diary with child and adult modes, guardian link, club membership entitlement and achievement"

## Sources and provenance labels

| Label | Meaning | Source |
|---|---|---|
| `[TEAM DECISION]` | Accepted by the team on 2026-10-30 | [product direction](../../docs/decisions/gustul-cartilor-product-direction.md), Issue #7 |
| `[PARTNER REPORTED]` | Said or shown by the club; not a binding requirement | [meeting discovery](../../docs/discovery/gustul-cartilor-meeting-2026-10-30.md), Issue #4, gustulcartilor.md |
| `[ASSUMPTION]` | Safe, reversible working choice made by this spec | this document |
| `[UNKNOWN]` | Open question; listed in *Decision gates* | this document |

Nothing in this spec is partner approval. The meeting record proves that ideas were *discussed*, not agreed.

## Actors (identity ≠ role ≠ entitlement)

| Actor | What it is | Notes |
|---|---|---|
| **Adult account** | A signed-in adult (email + password). Can read for themselves and/or be a guardian | `[TEAM DECISION]` adults without children are supported |
| **Guardian** | Relationship: an adult account that owns a child profile | Not a separate user type. MVP: exactly one guardian per child `[TEAM DECISION]` |
| **Child profile** | A minor reader created by a guardian. No email, no password, no independent sign-in in MVP | `[TEAM DECISION]` |
| **Reader** | Whoever owns a shelf and progress: an adult account or a child profile | Unifies progress for both modes `[ASSUMPTION]` |
| **Club membership** | Time-bounded entitlement attached to a reader; independent of role | `[TEAM DECISION]` separate axis |
| **Club admin** | Club staff operating the back office (activate/revoke membership, issue codes, catalog) | `[ASSUMPTION]` staff flag, not a reader role |
| Anonymous visitor | Not signed in | Sees landing + public catalog only |

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Child logs reading, guardian sees saved progress (Priority: P1)

A guardian signs in, creates a child profile (nickname, age band, avatar), and hands the phone over in **child mode**. The child picks a book card from the catalog, adds it to their shelf, and logs "I read up to page N" with large buttons. The mascot reacts. Later — after a reload or from another device — the guardian opens the **adult mode** dashboard and sees the child's saved pages, current book and finished books.

**Why this priority**: This is the critical demo journey `[TEAM DECISION]` and the reading-diary core the club named as the main purpose `[PARTNER REPORTED 08:20–08:43]`. Without it nothing else has value.

**Independent Test**: With seeded data, run the scenario on two browsers (child phone, parent laptop); the parent page shows numbers that came from the database, not from the child's browser.

**Acceptance Scenarios**:

1. **Given** a signed-in guardian with no children, **When** they create child "Mia" (age band 9–11), **Then** a private child profile exists linked only to this guardian and the dashboard lists it.
2. **Given** the guardian starts child mode for Mia, **When** the screen loads, **Then** only child-mode screens are reachable (home, catalog, my book, achievements) and adult navigation is not rendered.
3. **Given** Mia is in child mode, **When** she adds a seeded book with page count 120 to her shelf, **Then** it appears in "Citesc acum" with progress 0/120.
4. **Given** the book is on Mia's shelf at page 0, **When** she submits page 35, **Then** the server stores 35, the progress bar shows 29%, and the mascot shows the "progress saved" line.
5. **Given** Mia saved page 35, **When** the guardian reloads the adult dashboard on another device, **Then** it shows 35/120 for that book and the updated "pages this week".
6. **Given** Mia is at page 35, **When** she submits page 500 or −3, **Then** the server rejects it with a child-friendly message and the stored value stays 35.
7. **Given** Mia submits page 120 (or taps "Am terminat cartea"), **Then** the entry is marked finished once, "books finished" increases by exactly 1, and a second identical submit changes nothing.
8. **Given** the network fails while saving, **When** the request does not reach the server, **Then** the UI shows "Nu s-a salvat — încearcă din nou" and never shows the saved state.

---

### User Story 2 — Verified club member unlocks a club achievement (Priority: P1)

A club admin issues a one-time membership code (or activates membership directly in the back office). The guardian redeems the code for Mia in adult mode. From then on Mia's qualifying reading activity unlocks a **club-only achievement**, and the members-only "Clubul meu" page becomes available. A non-member doing the same reading gets general achievements only.

**Why this priority**: Shows the value of club membership — the end of the critical demo path `[TEAM DECISION]`. Must be enforced on the server.

**Independent Test**: Two seeded children with identical reading; only the member receives the club achievement; direct requests by the non-member to members-only URLs are denied.

**Acceptance Scenarios**:

1. **Given** an admin-issued unused code, **When** Mia's guardian redeems it, **Then** Mia gets an active membership with an expiry date, and the code becomes used.
2. **Given** a used, expired or unknown code, **When** anyone redeems it, **Then** redemption fails with one generic message and no membership is created; repeated failures are rate-limited.
3. **Given** Mia is a member, **When** she finishes her first book, **Then** she receives the club achievement "Cititor de Club" exactly once, and the mascot announces it.
4. **Given** non-member Alex finishes a book, **Then** Alex gets the general "Prima carte" achievement but not the club one, and the UI shows a neutral "available for club members" hint.
5. **Given** Alex (or his guardian) requests the members-only page, **Then** the server denies access (403) and no grant is stored; there is no endpoint through which a client can request a specific achievement.
6. **Given** the admin revokes Mia's membership, **When** Mia opens "Clubul meu", **Then** access is denied; already-earned achievements remain in history `[ASSUMPTION — gate G4]`.

---

### User Story 3 — Child cannot leave child mode without the guardian (Priority: P1)

On a shared phone, the child cannot reach adult settings, other children, or membership redemption by tapping a toggle. Leaving child mode requires the guardian's PIN (or password).

**Why this priority**: Child safety on shared devices is a review checklist item and shapes session design from day one.

**Independent Test**: In child mode, request every adult URL directly; all redirect to the PIN gate. A wrong PIN 5× locks the gate temporarily.

**Acceptance Scenarios**:

1. **Given** child mode is active, **When** the child opens any adult URL (dashboard, family, redeem, settings, back office), **Then** the server redirects to the "Cere ajutorul unui părinte" PIN screen.
2. **Given** the PIN screen, **When** the correct PIN is entered, **Then** adult mode resumes; **When** a wrong PIN is entered 5 times, **Then** the gate locks for 5 minutes.
3. **Given** a guardian without a PIN, **When** they try to start child mode, **Then** they are asked to set a 4–6 digit PIN first.

---

### User Story 4 — Adult reader without children (Priority: P2)

An adult signs up, adds books to their own shelf, logs pages and sees personal statistics in the adult interface.

**Why this priority**: Required by "one product for everyone" `[TEAM DECISION]`, and cheap because it reuses the US1 domain.

**Independent Test**: A new adult with no children completes add → progress → finish → stats.

**Acceptance Scenarios**:

1. **Given** a new adult account, **When** they add a book and log pages, **Then** their adult dashboard shows the shelf and totals; no child UI is shown.

---

### User Story 5 — Visitor browses the catalog (Priority: P2)

An anonymous visitor sees the landing page, the public catalog with book metadata, and a call to sign up or learn about the club.

**Independent Test**: A logged-out browser can open landing and catalog; any shelf action redirects to sign-in.

**Acceptance Scenarios**:

1. **Given** a logged-out visitor, **When** they tap "Adaugă în raft", **Then** they are redirected to sign-in, and nothing is stored.

---

### Edge Cases

- Same progress submit repeated (double tap, retry, back button): stored once (idempotency key); stats unchanged.
- Page lowered (child corrects a mistake): allowed down to 0 while not finished; the event log keeps the change; "pages in last 7 days" counts only positive deltas.
- Book already finished, then page edited: rejected in P0 (re-reading deferred).
- Book with unknown page count: not allowed in the P0 catalog.
- Guardian A requests guardian B's child ID in any URL or form: 404, no data leak (no "exists but forbidden" distinction).
- Membership expires while the child is in the app: the next server check denies members-only features; no client-cached entitlement.
- Session expired mid-save: redirect to sign-in; the save is reported as not saved.
- Offline: app shell and an offline page load; writes are disabled and clearly marked; no queued "fake saves".
- Two guardians wanting access to one child: not supported in MVP (gate G2).
- Child deleted by guardian: profile, shelf, progress, grants and memberships of that child are deleted `[ASSUMPTION]`.

## Requirements *(mandatory)*

### Functional Requirements

**Accounts, guardianship and modes**

- **FR-001**: System MUST let an adult create an account with email + password and sign in/out.
- **FR-002**: A signed-in adult MUST be able to create, rename and delete child profiles linked to themselves. A child profile stores only nickname, age band (7–8, 9–11, 12–15), avatar choice from a fixed set, and UI language. No real name, birth date, photo, school or contact data `[ASSUMPTION — PII minimization]`.
- **FR-003**: Each child profile MUST have exactly one guardian in MVP; ownership is set by the server from the session, never from submitted data.
- **FR-004**: A guardian MUST set a 4–6 digit PIN before starting child mode; the PIN is stored hashed.
- **FR-005**: In child mode the server MUST allow only child-mode routes for the active child; every other authenticated route MUST redirect to the PIN gate. Hiding links is not sufficient.
- **FR-006**: Leaving child mode MUST require the guardian's PIN or password; 5 failed attempts MUST lock the gate for 5 minutes.
- **FR-007**: Independent child sign-up and child credentials are out of scope.

**Catalog and reading diary**

- **FR-010**: System MUST provide a catalog of seeded books with metadata only (title, author, language, page count, age band, genre, generated cover). No full texts `[TEAM DECISION]` `[PARTNER REPORTED: club does not supply books]`.
- **FR-011**: A reader MUST be able to add a catalog book to their shelf once (duplicate add is a no-op).
- **FR-012**: A reader MUST be able to set current page `0 ≤ page ≤ page_count` for an unfinished book; values outside the range MUST be rejected server-side.
- **FR-013**: Reaching `page_count`, or an explicit "finish" action, MUST mark the entry finished exactly once and record the finish time.
- **FR-014**: Every accepted progress change MUST be persisted before success is shown; each write carries a client-generated idempotency key, and a repeated key MUST return the original result without a second change.
- **FR-015**: System MUST compute per-reader statistics from stored data: books on shelf, books finished, total pages read, pages in the last 7 days.
- **FR-016**: A guardian MUST see each of their children's shelf, progress and statistics in adult mode; no one else may see them.

**Club membership and achievements**

- **FR-020**: Club membership MUST be an entitlement record attached to a reader with `valid_from`, `valid_until`, status (active/revoked) and source (admin/code). Membership MUST be computed on the server at request time.
- **FR-021**: Club admins MUST be able to activate/revoke membership and issue one-time codes with an expiry date via the back office.
- **FR-022**: A guardian MUST be able to redeem a code for themselves or one of their children in adult mode. Codes are single-use, stored hashed, expire, and failed attempts are rate-limited. Redemption is not available in child mode.
- **FR-023**: Achievements MUST be granted only by server-side rules evaluated after a stored change (progress, finish, membership activation). There MUST be no endpoint that accepts an achievement identifier from the client.
- **FR-024**: Each achievement MUST be granted at most once per reader (uniqueness enforced in storage).
- **FR-025**: Club-only achievements and the members-only page MUST require active membership at evaluation/request time.
- **FR-026**: Demo achievements are digital only; the UI MUST NOT promise physical prizes `[TEAM DECISION]`.

**Child experience and mascot**

- **FR-030**: Child mode MUST use large tap targets, at most 4 primary destinations, book cards with covers, a visible progress bar, and a mascot speech bubble.
- **FR-031**: Mascot lines MUST come from a fixed, translatable script keyed by event (welcome, progress saved, book finished, achievement, error, offline). No generated text is shown to children in P0 `[TEAM DECISION: AI is not a P0 dependency]`.
- **FR-032**: No guilt-based or pressure messaging (e.g. "the mascot is sad you did not read") `[ASSUMPTION]`.

**Privacy, safety, platform**

- **FR-040**: Child profiles MUST be private by default: no public profile pages, leaderboards, feeds or messaging in P0.
- **FR-041**: Every read/write of reader data MUST check ownership on the server; foreign IDs MUST yield 404.
- **FR-042**: The app MUST be a responsive, installable PWA usable at 360 px width and on laptops.
- **FR-043**: Romanian is the default UI language; all UI strings MUST go through the translation layer. Russian is optional (P1).
- **FR-044**: Offline, the app MUST show a clear offline state; writes MUST NOT be reported as saved.
- **FR-045**: Logs MUST NOT contain emails, nicknames or PINs; use internal IDs.
- **FR-046**: Demo data MUST be synthetic; no real minors' data in Git, seeds, screenshots or logs.

### Key Entities

- **Account**: an adult identity (email, password hash, display name, language, PIN hash, staff flag).
- **Reader**: owner of a shelf — either an adult account (self-reader) or a child profile. Exactly one reader per account and per child.
- **Child profile**: nickname, age band, avatar, guardian (account). Has one reader.
- **Book**: catalog metadata, page count, age band, language, rights/source note.
- **Shelf entry**: reader × book, current page, status, start/finish time. Unique per reader + book.
- **Progress event**: append-only log of page changes with idempotency key.
- **Club membership**: reader entitlement with validity window and status.
- **Membership code**: hashed one-time code with expiry, issuer and redemption record.
- **Achievement**: rule definition (type, threshold, members-only flag, icon, translated title).
- **Achievement grant**: reader × achievement, once.
- **Club activity**: members-only item (title, date, place) shown on "Clubul meu".

Full field list and invariants: [data-model.md](./data-model.md).

## Scope tiers

| Tier | Items | Why |
|---|---|---|
| **P0** | US1, US2, US3; seeded catalog; adult dashboard for own children; scripted mascot; PWA shell; Romanian UI; synthetic seed + demo script | Critical demo path; each item is needed to show "child logs → parent sees → member unlocks" safely |
| **P1** | US4 and US5 polish; Russian UI; adult-added custom books; rule-based genre recommendations; weekly goal without pressure; club activity reminders; scripted onboarding dialogue with mascot answer buttons | Valuable and low-risk, but not on the critical path |
| **Deferred** | Payments/subscriptions; full-text reader; public leaderboard of minors; social feed/reviews by children; DMs or mentor chats; second guardian; independent child sign-in; AI features (quiz drafts for mentors, input validation, book Q&A); Roblox rewards; native store apps; physical rewards | Each needs a partner/legal/safety gate or exceeds hackathon time |

Note on AI (Deferred, recorded for the roadmap): the safest position for a model is behind a human — it drafts quizzes for a mentor who reviews and publishes them; children see only approved content. No generated text reaches children without review.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The full demo path (guardian creates child → child adds book → logs pages → guardian sees saved progress on a second device → member unlocks club achievement) completes in under 3 minutes on a phone over mobile data.
- **SC-002**: All 10 security counter-examples in [quickstart.md](./quickstart.md#security-counter-examples) are covered by an automated test or a scripted manual check before demo day; none is reported PASS without being run.
- **SC-003**: From the child home screen, logging progress takes at most 3 taps.
- **SC-004**: After any reload or device switch, the progress the guardian sees equals the database value (0 mismatches in the smoke script).
- **SC-005**: Repeating any write request 3× changes stored totals at most once.

## Decision gates (blocking items need answers before freezing)

| ID | Gate | Working assumption used in this spec | Blocks |
|---|---|---|---|
| G1 | Primary KPI (acquisition / retention / remote scale / mentor load) | Demo the end-to-end journey; claim no KPI | Pitch only |
| G2 | Child accounts: consent, age of digital consent under Moldovan Law 195/2024 `[UNKNOWN — verify on legis.md]`, independent sign-in, second guardian | Guardian-created, single guardian, no child credentials, synthetic data only | Production use |
| G3 | Membership verification process (who, how, revocation, link to existing subscriptions) | Admin activation + admin-issued one-time codes, 90-day default validity | Real launch, not demo |
| G4 | Reward semantics: what counts, what happens to earned club badges after revocation, existing club bonus system | Pages + finished books; earned badges kept; digital only | Gamification depth |
| G5 | Social/leaderboard visibility and moderation for minors | None in P0 | Any P1 social feature |
| G6 | Delivery: PWA acceptable? hosting owner? brand assets/mascot? book metadata and cover rights | PWA, generated covers, public metadata | Demo hosting, visuals |

## Assumptions

- Age bands follow the club website (7–8, 9–11, 12–15) `[PARTNER REPORTED]`; the 7–13 figure from the case summary is not used.
- Physical books are the reading medium; the app records progress only `[PARTNER REPORTED 06:54–07:13]`.
- Mentors work with groups; no mentor role in P0 `[PARTNER REPORTED 07:19–07:58]`.
- The demo uses a small seeded catalog of public-domain Romanian children's titles (metadata only) and generated covers.
- Single deployment, single region, demo-scale load (≤ 100 concurrent users).
