# Host Proof H1–H7 — evidence checkpoint (2026-10-30)

Issue: #11. Branch: `spike/host-proof-h1-h7`. **Status: NO-GO for public demo; checkpoint only, not final proof.**

## Scope and source integrity

This is an isolated synthetic Django probe in `experiments/host-proof/`, not the Gustul Cărților app, production settings, or a capacity benchmark. Evidence below is attributed either to the implementer's handoff or direct GitHub/Render connector inspection on 2026-10-30. No credentials, user data, internal database URL or secret values are in this document. The existing `utm-curs-i-orar-2027` service was not changed.

**Source branch commit:** `153a9e150c1c010626f700ea316eca2f8e9ae944` (before adding this report).

## Current infrastructure (verified through Render)

- Workspace: `My Workspace`.
- Isolated free web service: `gustul-host-proof-h-20261030`, `srv-dbi8lc6i0phs73d5opk0`, Frankfurt, Python; branch `spike/host-proof-h1-h7`; automatic Git-triggered deploy **off**. URL: https://gustul-host-proof-h-20261030.onrender.com
- Separate free PostgreSQL 18: `gustul-host-proof-h`, `dpg-dbi8k4dg1s2s73ea9sag-a`, Frankfurt, status `available`, expires **2026-11-29 12:14 UTC**. Free DB is temporary; do not rely on it for long-term data.
- Initial Render build **succeeded** (installed Django 5.2.18, dj-database-url 2.3.0, psycopg 3.2.12, gunicorn 23.0.0). Deploy `dep-dbi8lcei0phs73d5oqfg` **failed** at 2026-10-30 12:17:31 UTC, exit 1. Logs: `RuntimeError: DATABASE_URL is required on Render; do not use ephemeral SQLite`. No HTTP success, remote DB writes, or phone results are claimed.
- Container log indicated `WEB_CONCURRENCY=1`; other CPU, latency, and IP header behavior not tested. Separate attempted read-only DB connector query was blocked by an empty external IP allowlist; this does **not** establish failure of the internal Render connection.

## H1–H7 status

| Check | Status | Evidence or remaining requirement |
|---|---|---|
| H1 HTTPS accessible on phone + laptop | **NOT PASSED** | Deploy failed before serving app; HTTPS public URL has not been verified on either device |
| H2 Manifest, service worker, Android install | **NOT RUN** | Endpoints exist in source; actual HTTPS installation, icons and offline page must be tested on device |
| H3 Persist a database value through restart **and redeploy** | **NOT RUN remotely** | Handoff reports local two-session values 17 and 35 and local server restart preserved 35; not independently reproduced; no Render write yet |
| H4 Cross-device login / save / read | **NOT RUN** | Requires phone on mobile data, laptop in a separate session, and working public service |
| H5 Latency / cold-start / failure behavior | **NOT RUN** | Record actual phone load time and POST round-trip and first hit after idle |
| H6 Free-tier resource constraints | **PARTIAL** | Free web + free DB in Frankfurt; DB expires 2026-11-29; one web instance and default web concurrency 1. CPU, request limits, cold starts and forwarded IP header still unverified |
| H7 Demo fallback rehearsal | **NOT RUN** | Source supports local SQLite in non-Render mode; a laptop + phone LAN demonstration has not been observed |

## Recovery steps (do not put credentials into GitHub, logs, screenshots, or chat)

1. On the Render **test database** dashboard copy **Internal Database URL**; paste it into environment variable `DATABASE_URL` on **only** the Render **test web service**. Both resources are in Frankfurt. Do not open the connection to the public internet.
2. In test service environment settings, verify `DJANGO_SECRET_KEY` has a random nonempty value. For reproducible password-protected smoke flows, set `PROOF_USERNAME` and a strong `PROOF_PASSWORD` (test-only values). Do not disclose any values. Verify or adjust `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS` only if logs/request behavior require it; the probe already uses Render's `RENDER_EXTERNAL_HOSTNAME` / `RENDER_EXTERNAL_URL`.
3. Save env variables; inspect the resulting deploy. Auto-deploy is off, so if saving did **not** start one, trigger one manual deploy. Inspect logs until `live`, then check `/health/`, `/manifest.webmanifest`, `/sw.js` (not just build status).
4. On **phone over mobile data** and laptop, use separate authenticated sessions at `/login/`, then `/value/`. Write 17 on device A and read 17 on B; write 35 on B and read 35 on A. Record date/time, HTTP outcomes and visibly observed readback. **No children's data.**
5. Restart just the web service and verify value 35; then deliberately redeploy the **same commit** and verify value 35 again. A single browser refresh is not enough for H3.
6. Test Android Chrome installation, launch in standalone mode, graceful offline navigation / no offline writes. Record H5 measurements, resource limits, and H7 laptop backup rehearsal. Never claim a capacity benchmark from one user.

### Review gates

- **Next independent review:** check whether the service is live, DB-backed writes survive restart and redeploy, phone ↔ laptop roundtrip is repeatable, and PWA works on-device. If any fail, document FAIL and invoke fallback.
- **Current decision:** **NO-GO** for announcing Render as a verified demo host; this does not block parallel M0 development.
- Probe is intentionally not production identity/child-mode logic. Its login and PWA shell do **not** prove minors' authorization, hardened production cookies or club entitlements.
