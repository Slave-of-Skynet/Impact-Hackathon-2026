# ADR-0001: Architecture for the Gustul Cărților P0 MVP

- **Status**: Proposed — awaiting independent review (Issue #7). Not partner-approved.
- **Date**: 2026-10-30
- **Deciders**: team (proposal by Arsenii / Claude Code)
- **Details**: [spec](../../specs/001-reading-diary-mvp/spec.md) · [plan](../../specs/001-reading-diary-mvp/plan.md) · [research](../../specs/001-reading-diary-mvp/research.md) · [data model](../../specs/001-reading-diary-mvp/data-model.md) · [routes](../../specs/001-reading-diary-mvp/contracts/routes.md) · [authorization](../../specs/001-reading-diary-mvp/contracts/authorization.md) · [execution plan](../../specs/001-reading-diary-mvp/execution-plan.md)

## Context

Five developers must ship, within the hackathon, one reliable demo: a child logs reading of a physical book, the linked parent sees the stored progress, and a verified club member unlocks a club-only achievement. The product serves children aged roughly 7–15, so authorization, privacy defaults and honest persistence matter more than feature count. The team prefers Python. The club wants maintainable code on GitHub afterwards.

## Decision

1. **Django 5.2 LTS monolith**, server-rendered templates with **HTMX**, packaged as an installable **PWA**. One process, one database (SQLite on a persistent disk for the demo; Postgres-compatible).
2. **Two presentation modes over one domain**: `templates/child/` and `templates/adult/` render the same view models.
3. **Reader abstraction**: adult accounts and child profiles each have one `Reader`; all shelves, progress, memberships and grants hang off `Reader`. Ownership is one function: own reader or a reader of one's own child.
4. **Child mode** is a server-side session state enforced by middleware with an allow-list of routes; leaving it requires the guardian's PIN or password, with lockout.
5. **Club membership** is a time-bounded entitlement row per reader, activated by staff in Django admin or by a hashed one-time code redeemed by a guardian; it is evaluated per request and never trusted from the client.
6. **Writes are transactional and idempotent** (client `request_id`, unique per reader); success is rendered only after commit; no offline write queue.
7. **Achievements** are granted only by server rules after stored changes, unique per reader; members-only rules check membership at evaluation time.
8. **Single contract style**: HTML forms + HTMX partials; no JSON API in P0.
9. **No AI in P0.** Mascot text is a fixed, translatable script. Future AI sits behind human review (mentor approves generated quizzes).

## Consequences

- ➕ Built-in auth, CSRF, admin, migrations and constraints cover the riskiest parts with little custom code; easy for AI agents and for handover.
- ➕ Clear module boundaries (apps + template sets) allow five parallel PRs after one foundation PR.
- ➖ Server-rendered UI is less "app-like" than a SPA; mitigated by HTMX partials and PWA install.
- ➖ SQLite limits horizontal scaling; acceptable for demo scale and switchable to Postgres.
- ➖ The foundation PR (all models) is a bottleneck; mitigated by keeping it small and letting UI and service work start against documented contracts.

## Alternatives considered

FastAPI + SQLAlchemy + Jinja/HTMX (more custom auth/admin code); Next.js + Supabase (contradicts Python preference, RLS risk); Flet/Reflex/NiceGUI (weak PWA/accessibility, tight UI–state coupling). See [research.md §2](../../specs/001-reading-diary-mvp/research.md#2-options-compared).

## Open decision gates

G1 KPI · G2 child accounts/consent (Law 195/2024) · G3 membership verification · G4 reward semantics · G5 social/leaderboard for minors · G6 delivery/hosting/assets — see [spec](../../specs/001-reading-diary-mvp/spec.md#decision-gates-blocking-items-need-answers-before-freezing).
