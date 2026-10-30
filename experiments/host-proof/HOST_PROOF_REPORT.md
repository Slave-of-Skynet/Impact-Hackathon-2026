# Host Proof H1–H7 — evidence checkpoint (2026-10-30)

Issue: #11. Branch: `spike/host-proof-h1-h7`. **Status: H3/H4 PASS for manual post-redeploy and cross-device value tests (user-observed, HTTP logs corroborate request sequence); H1/H2/H5–H7 need remaining device, installability, performance, constraint, and fallback checks.**

## Scope and source integrity

This is an isolated synthetic Django probe in `experiments/host-proof/`, not the Gustul Cărților app, production settings, or a capacity benchmark. Evidence below is attributed either to the implementer's handoff or direct GitHub/Render connector inspection on 2026-10-30. No credentials, user data, internal database URL or secret values are in this document. The existing `utm-curs-i-orar-2027` service was not changed.

**Source branch commit:** `153a9e150c1c010626f700ea316eca2f8e9ae944` (before adding this report).

## Current infrastructure (verified through Render)

- Workspace: `My Workspace`.
- Isolated free web service: `gustul-host-proof-h-20261030`, `srv-dbi8lc6i0phs73d5opk0`, Frankfurt, Python; branch `spike/host-proof-h1-h7`; automatic Git-triggered deploy **off**. URL: https://gustul-host-proof-h-20261030.onrender.com
- Separate free PostgreSQL 18: `gustul-host-proof-h`, `dpg-dbi8k4dg1s2s73ea9sag-a`, Frankfurt, status `available`, expires **2026-11-29 12:14 UTC**. Free DB is temporary; do not rely on it for long-term data.
- Initial Render build **succeeded** (Django 5.2.18, dj-database-url 2.3.0, psycopg 3.2.12, gunicorn 23.0.0). Initial deploy `dep-dbi8lcei0phs73d5oqfg` **failed** at 2026-10-30 12:17:31 UTC, exit 1, because `DATABASE_URL` was absent.
- **Recovery verified via Render connector, 2026-10-30 12:29:40 UTC:** After the user saved environment settings, deployment `dep-dbi8qsss728c73clq180` ran successfully for commit `a808b7f9a91afd781fc9cd838e3f0b4582231518`. Logs show successful Django auth/contenttypes/sessions migrations, Gunicorn listening on `0.0.0.0:10000`, and Render says `Your service is live`. This first confirmed startup and DB connection; subsequent Render access logs confirmed public browser requests from Windows and Android, and a manual cross-device value readback was reported after the 303 fix. No credential or database URL is exposed.
- Container log indicated `WEB_CONCURRENCY=1`; other CPU, latency, and IP header behavior not tested. Separate attempted read-only DB connector query was blocked by an empty external IP allowlist; this does **not** establish failure of the internal Render connection.

## H1–H7 status

| Check | Status | Evidence or remaining requirement |
|---|---|---|
| H1 HTTPS accessible on phone + laptop | **PARTIAL** | Gunicorn logs show successful browser requests from Windows Chrome and Android Chrome to HTTPS-hosted URLs; phone's actual mobile-data connection/certificate warning status not independently observed |
| H2 Manifest, service worker, Android install | **PARTIAL** | Browser requests to `/sw.js`, `/manifest.webmanifest` and `/icon-192.png` returned HTTP 200 on Windows; Android installability, standalone launch and offline behavior NOT RUN |
| H3 Persist a database value through restart **and redeploy** | **PASS (manual, post-redeploy)** | User confirmed **Value: 35** after new deploy `dep-dbi93l0m7kps73c800k0` became **LIVE** at **12:48:21 UTC**, with Django `No migrations to apply` and new Gunicorn worker. Independent Render HTTP logs show Windows `GET /value/` **200** at **12:49:40 UTC** on the new instance after authentication; numeric value was observed by user, not captured in logs. This validates persistence through the deploy (which restarts the app). Separate standalone restart not tested |
| H4 Cross-device login / save / read | **PASS (manual, user-reported)** | User confirmed after hotfix: Android saved 35; Windows loaded 35 on refresh. Access logs corroborate Android POST 303 followed by GET 200 and Windows GET 200; payload contents are not logged, so 35 is user-observed, not independently read via SQL. Whether the phone used mobile data vs Wi-Fi is unverified |
| H5 Latency / cold-start / failure behavior | **NOT RUN** | Record actual phone load time and POST round-trip and first hit after idle |
| H6 Free-tier resource constraints | **PARTIAL** | Free web + free DB in Frankfurt; DB expires 2026-11-29; one web instance and default web concurrency 1. CPU, request limits, cold starts and forwarded IP header still unverified |
| H7 Demo fallback rehearsal | **NOT RUN** | Source supports local SQLite in non-Render mode; a laptop + phone LAN demonstration has not been observed |

## Cross-device value overwrite investigation (2026-10-30, 12:36 UTC)

- Render Gunicorn access logs show `POST /value/` with HTTP **200** from Android at **12:36:14 UTC**, followed by two `POST /value/` HTTP **200** from Windows at **12:36:19 UTC** and **12:36:24 UTC**. The server logs contain request paths and statuses, **not posted numeric values**.
- The original `value()` handler wrote on POST then returned HTML **200** rather than a redirect. Browser refresh on a POST result can resend the previous form. This is a strong explanation for the user reporting that the PC did not show the phone's value `35`: the PC appears to have sent subsequent writes; exact numeric overwrite remains **unverified**.
- **Fix pushed in** `1e4f6fb` and `a0383f9`: successful save returns **HTTP 303 `Location: /value/`**; successful login also returns 303 to the read page; GET value responses set **Cache-Control: no-store**. No domain contracts or unrelated services changed. A deployment was initiated for commit `a0383f9` (deploy `dep-dbi8vu6gekts7397eblg`). Render deployment **became live** at **12:40:32 UTC** for commit `a0383f9` (build and deploy succeeded). After rollout, logs show Android `POST /value/` **303** at **12:46:36 UTC**, automatic Android `GET /value/` **200** at **12:46:37 UTC**, and Windows `GET /value/` **200** at **12:46:39 UTC**. User confirmed Windows displayed `35`. **H4 passed at manual-evidence level**, without exposing numeric form payload in logs.
- Regression test after deploy: first browser save 17 → must navigate via GET and show 17; second device save 35 → first device **refreshes GET** and shows 35; no second POST from the first device on refresh. Then validate persistence across restart/redeploy.

## Recovery steps (do not put credentials into GitHub, logs, screenshots, or chat)

1. **DONE (user reported, operationally corroborated):** test database's **Internal Database URL** was configured as `DATABASE_URL` on the isolated test web service; the redeploy now runs migrations and Gunicorn. Both resources are in Frankfurt. Do not open the connection to the public internet.
2. In test service environment settings, verify `DJANGO_SECRET_KEY` has a random nonempty value. For reproducible password-protected smoke flows, set `PROOF_USERNAME` and a strong `PROOF_PASSWORD` (test-only values). Do not disclose any values. Verify or adjust `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS` only if logs/request behavior require it; the probe already uses Render's `RENDER_EXTERNAL_HOSTNAME` / `RENDER_EXTERNAL_URL`.
3. **DONE:** Saving environment settings triggered a successful `service_updated` deployment on 2026-10-30 12:29:40 UTC, even though Git-triggered auto-deploy is off. **STILL NEEDED:** check `/health/`, `/manifest.webmanifest`, `/sw.js` over HTTPS on a real browser.
4. On **phone over mobile data** and laptop, use separate authenticated sessions at `/login/`, then `/value/`. Write 17 on device A and read 17 on B; write 35 on B and read 35 on A. Record date/time, HTTP outcomes and visibly observed readback. **No children's data.**
5. **Follow-up redeploy succeeded**: `dep-dbi93l0m7kps73c800k0` became LIVE at 12:48:21 UTC, same application code and documentation changes. **DONE, reported by user**: opened `/value/` in a fresh tab after the deployment, authenticated and saw `35` without writing again; Windows HTTP GET 200 at 12:49:40 UTC corroborated. This confirms the pre-redeploy stored value survived. An additional standalone restart-only test is optional but not performed.
6. Test Android Chrome installation, launch in standalone mode, graceful offline navigation / no offline writes. Record H5 measurements, resource limits, and H7 laptop backup rehearsal. Never claim a capacity benchmark from one user.

### Review gates

- **Next independent review:** H3/H4 have user-confirmed manual evidence corroborated by Render logs. Next confirm mobile-data HTTPS and PWA installation on Android, measured first-hit latency and save time, and an actual laptop/phone fallback rehearsal. If any fail, document FAIL and invoke fallback.
- **Current decision:** **CONDITIONAL**: Render has successfully deployed and started. **CONDITIONAL GO** for Render + PostgreSQL as an operational, HTTPS-served, cross-device persisted data backend for the hackathon demo, based on H3 and H4 manual observations. **NOT YET GO** for claiming fully verified installable PWA, reliable presentation resilience or production readiness until H2 installability, H5 cold-start/latency and H7 fallback are tested. H1 mobile-data detail remains unknown. This does not block M0.
- Probe is intentionally not production identity/child-mode logic. Its login and PWA shell do **not** prove minors' authorization, hardened production cookies or club entitlements.
