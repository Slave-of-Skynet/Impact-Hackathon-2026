# Research: stack and hosting for the P0 slice

**Date**: 2026-10-30 · **Feature**: [spec.md](./spec.md) · Facts marked ✅ were checked against the cited page on this date; ⚠️ means a third-party or unconfirmed source; ❓ means not verified.

## 1. Inputs that constrain the choice

- `[TEAM DECISION]` One responsive, installable PWA; Romanian first; server-side authorization for children and membership; no payments; no AI dependency in P0.
- `[TEAM INPUT — Arsenii, 2026-10-30, confirm in review]` "We write everything in Python." Treated as a strong preference: the comparison still lists a TypeScript option for completeness.
- Five developers working in parallel with AI agents (Claude Code, Codex, Antigravity), unknown remaining hackathon time `[UNKNOWN]`.
- The club must be able to take over the code later `[PARTNER REPORTED 19:20–19:33]`.

## 2. Options compared

| Criterion | **A. Django 5.2 LTS monolith + server-rendered templates + HTMX** | B. FastAPI + SQLAlchemy/SQLModel + Jinja2/HTMX | C. Next.js (TypeScript) + Supabase (Auth + Postgres RLS) | D. Python UI frameworks (Flet / Reflex / NiceGUI) |
|---|---|---|---|---|
| Matches Python input | Yes | Yes | **No** | Yes |
| Auth, sessions, CSRF, password hashing | Built in | Must assemble (libraries + own glue) | Managed service | Varies; mostly own glue |
| Admin back office (membership codes, revoke, catalog) | **Built-in Django admin** — near zero work | Must build | Supabase dashboard (not club-friendly) or build | Must build |
| Server-side authorization model | Views + one `authz` module; tests with Django test client | Dependencies per route; own tests | RLS policies in SQL — powerful but easy to get subtly wrong under time pressure | State lives on server websockets; unusual model |
| Migrations, seed data | Built in (`makemigrations`, fixtures/management command) | Alembic, extra setup | Supabase migrations | Varies |
| PWA on phones | Plain HTML + manifest + small service worker | Same as A | Strong (Next PWA tooling) | Weak: Flet web renders on canvas (heavy, poor accessibility); Reflex/NiceGUI need persistent websocket |
| Parallel work for 5 | Django apps = natural module boundaries; templates can be built against documented context | Similar, more shared glue code | Good, but frontend/backend split by language | Poor: UI and state tightly coupled |
| AI-agent friendliness | Very high: mature, heavily documented, conventional layout | High | High | Lower: newer, less training data, fast-changing APIs |
| Handover to club | One repo, one process, one DB file or Postgres | One process + more custom code | Two vendors (Vercel-like host + Supabase) | Niche framework |
| Third-party risk in hackathon | Low (no external service needed to run) | Low | Medium: service limits/config, keys | Medium |

**Decision: Option A — Django 5.2 LTS + HTMX, server-rendered, one canonical style (HTML forms + HTMX partials, no parallel JSON API in P0).**

Rationale: the riskiest parts of this product are *authorization* (guardian ↔ child, child mode, membership) and *persistence*; Django gives sessions, CSRF, password hashing, ORM constraints, migrations and an admin back office out of the box, so the team writes product logic instead of security plumbing. Everything runs in one process, which makes AI-assisted debugging and handover simple. HTMX keeps the UI responsive (progress updates without full reloads) while every state change still goes through the server.

Rejected: **B** duplicates what Django provides (auth/admin) with more custom security code; **C** contradicts the Python input and moves authorization into RLS policies the team has not tested; **D** weakens the PWA/mobile story and parallel UI work. Note: the Flet suggestion made earlier in chat (before the PWA requirement and review checklist were known) is withdrawn for these reasons.

Versions: Django 5.2 is an LTS release supported until April 2028 ⚠️ ([endoflife.date](https://endoflife.date/django)); Django 6.0 is supported only until April 2027 ⚠️. Pin `Django>=5.2,<5.3`. Python 3.12. HTMX 2.x vendored as a static file (no CDN dependency at demo time). Exact patch versions to be pinned in the first implementation PR via `uv lock`.

## 3. Storage

- **SQLite** for local development and for the demo host if it has a persistent disk; schema written to stay **PostgreSQL-compatible** (no SQLite-only features). Switching is a settings change (`DATABASE_URL`).
- SQLite runs in WAL mode; demo load (≤ 100 users) is far below its limits.
- Uniqueness and range invariants are enforced by **database constraints**, not only by forms (see [data-model.md](./data-model.md)).

## 4. Hosting options for the public demo (gate G6)

| Option | Facts | Fit |
|---|---|---|
| **PythonAnywhere free** (primary proposal) | One web app on `<user>.pythonanywhere.com`; persistent file system (SQLite survives restarts); 512 MB storage; outbound internet restricted to an allowlist; unused free apps expire after 1 month ⚠️ ([help page](https://help.pythonanywhere.com/pages/FreeAccountsFeatures/), [blog](https://blog.pythonanywhere.com/221/)). HTTPS on the free subdomain ❓ — must be checked in M0 (PWA install requires HTTPS) | Good: no cold starts claimed ❓, persistent SQLite, simple handover to club |
| Render free web service + Render free Postgres | Free web services have an **ephemeral** filesystem — SQLite is lost on redeploy/restart/spin-down ✅; free Postgres **expires 30 days** after creation, 1 GB, no backups ✅ ([render.com/docs/free](https://render.com/docs/free)); idle spin-down cold start ❓ | Acceptable for a hackathon only with Postgres; cold start risk on stage |
| Team VPS (if any member provides one) | Unknown `[UNKNOWN]` | Best control if available |
| **Fallback — local laptop** | `runserver`/`gunicorn` on the presenter laptop, phone on the same network (or a tunnel). Data persists in the laptop's SQLite file — real persistence, but **not a public deployment** | Always available; say so honestly in the pitch |

M0 must prove one host with: HTTPS URL, DB write survives a restart, admin login works.

## 5. PWA approach

- `manifest.webmanifest` (name, icons, `display: standalone`, theme color), served from the site root.
- Minimal service worker: cache static assets and an `/offline/` page; **network-only for all HTML and POST requests** — no background sync, no offline queue, so nothing is ever falsely shown as saved.
- HTMX error hooks show "Nu s-a salvat" on network or server errors.

## 6. Security building blocks (all built-in unless noted)

- Django auth (PBKDF2 password hashing), session cookies (`HttpOnly`, `Secure` in prod, `SameSite=Lax`), CSRF middleware (HTMX sends the token via `hx-headers`).
- PIN stored with Django's password hashers (`make_password`), attempts counted per session + account; lockout stored server-side.
- Membership codes: random 10-character code shown once to the admin, stored as a hash; constant-time lookup via hash; redemption attempts rate-limited per account.
- Rate limiting: small in-app counter in the database/cache — no extra service.

## 7. Open technical unknowns

- ❓ HTTPS and request limits on the chosen free host — verify in M0.
- ❓ Brand assets (logo, mascot) availability — G6; until then use a neutral placeholder mascot drawn by the team.
- ❓ Hackathon deadline and judging format — affects how much P1 is attempted.
