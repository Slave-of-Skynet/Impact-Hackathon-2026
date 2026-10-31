# Issue #59 — intermittent 502 on the public demo (diagnosis + bounded fix)

**Status:** root cause **REPRODUCED LOCALLY under a CPU limit matching the host**, consistent with every
observed fact; **not yet confirmed against Render metrics** (no CPU/health-check timeline was available
to the author). Confirming check for the Render operator in §5.

## 1. Observed facts

| When (UTC, 2026-10-31) | Evidence | Source |
|---|---|---|
| ≈08:25:44 | `GET /familie/<child>/mod-copil/` → Render **502 Bad Gateway** page (request id `a53145514f1c5e2e-KIV`); immediately after, 6× `GET /healthz/` → 502 in 0.1–0.4 s each, header `x-render-routing: no-deploy` | author's browser + curl |
| ≈08:26:08 | `/healthz/` back to 200 (≈30–60 s outage); no new commit, no deploy | curl, `git log origin/main` |
| ≈08:27:20–08:27:33 | second outage, same pattern (`/healthz/`, `/raft/`, `/realizari/`, `/club/cod/` all 502), back at 08:27:44 | curl |
| 08:28–08:31 | 36 probes 5 s apart: 0 failures | curl |
| — | Render events: **no restart / server_failed** in that period; app logs show no app-side 502 | #59 issue body (operator) |
| — | one live login `POST /cont/intrare/` = **2.76 s**, `GET /healthz/` = **0.10 s** | curl, single request |

Note for log readers: the bursts of `POST /parinte/` (all correct PIN, 302) and
`POST /familie/*/mod-copil/` around 08:25 and the `POST /cont/intrare/` at ≈08:27 include the author's own
scripted QA pass (6 child-mode switches + 6 correct PINs, then one curl login). They are not an attack or a
browser retry loop. The author entered **no** wrong PIN on the host, so the 422/429 at 08:30 are not from it.

## 2. Mechanism

1. Every login and every PIN check runs Django 5.2's default **PBKDF2-SHA256 with 1,000,000 iterations**:
   0.41 s on one laptop core, **≈2.6 s on the free plan's 0.1 CPU** (live login 2.76 s vs health 0.10 s).
2. Gunicorn ran `--workers 2 --threads 2` → **4 request slots**. Five phones logging in and unlocking the PIN
   gate (plus retries) keep all 4 slots busy hashing for seconds each.
3. Render's health check (`/healthz/`) needs a 2xx **within 5 s**. It is cheap but must wait for a free slot.
   After **15 s** of failed checks Render **stops routing** to the only instance → every request gets an
   immediate edge 502 with no app log line and **no restart event**; after 60 s it would restart it
   ([Render docs: Health Checks](https://render.com/docs/health-checks)). Matches §1 exactly.
4. Memory is not the constraint: total gunicorn RSS 113 MB (2×2) / 70 MB (1×8), far below 512 MB.

A related defect made it worse and was a security bug in itself: on a **locked** login (429) the view rendered
the *bound* form, whose `form.errors` ran `authenticate()`. So (a) each locked attempt still cost a full hash,
and (b) the page said "Email sau parolă greșită" only for wrong guesses and nothing for the right one — the
correct password was distinguishable **through** the lock. The PIN gate was not affected (it returns before
hashing and renders an unbound form).

## 3. Reproduction and measurements

Harness: `scripts/demo_load_check.py` — 5 concurrent clients loop *login → child mode → correct PIN* on the
same seeded demo account, while a prober hits `/healthz/` every second. Server: gunicorn with the exact
`render.yaml` flags, `config.settings.dev` on disposable SQLite, confined with
`systemd-run --user --scope -p CPUQuota=10%` to approximate the 0.1-CPU plan. WSL2, 8 cores, Python 3.12.
Run only against local/staging, never the shared demo host.

| Gunicorn | `/healthz/` probes | p50 | p95 | max | > 5 s (Render fail) |
|---|---|---|---|---|---|
| `--workers 2 --threads 2` (before) | 3 | 30.07 s | 30.08 s | 30.08 s (client timeout) | **2 / 3** |
| `--workers 2 --threads 8` | 39 | 0.4 s | 2.7 s | 4.04 s | 0 / 39 (near the limit) |
| `--workers 1 --threads 8` (**after**) | 46 | 0.3 s | 0.8 s | 1.8 s | **0 / 46** |
| `--workers 1 --threads 8`, re-run on this branch | 43 | 0.4 s | 0.9 s | 1.07 s | **0 / 43** |

Each 60-s run. Login+PIN flows themselves stay slow at 10 % CPU (≈150–200 s for 5 clients) because the hashes
are CPU-bound; threads do not add CPU, they only stop the health check from queueing behind them. PBKDF2
(`hashlib.pbkdf2_hmac`) releases the GIL, so 8 threads in one process hash as well as 2 processes.

## 4. Change in this PR

- `render.yaml` / `docs/demo-deployment.md`: `--workers 1 --threads 8` (measured above). **The live service's
  start command is set in the Render dashboard; it only changes if the operator updates it (or syncs the
  blueprint).**
- `ThrottledLoginView`: on 429 render an **unbound** form (email kept as initial), so no `authenticate()` runs
  and wrong/right guesses get byte-identical pages; `adult/login.html` shows
  "Prea multe încercări greșite. Încearcă din nou în N min." (same string as the PIN gate).
- Regression test `test_locked_response_does_not_reveal_or_check_the_password` (fails on the old code with 2
  authenticate calls during the lock, passes now).
- Unchanged on purpose: throttle limits/keys (lock after 5 wrong PIN/login stays account-wide), PIN gate,
  `SESSION_SAVE_EVERY_REQUEST`, hasher, DB settings.

## 5. Open decisions / next checks

1. **Operator check (confirms or refutes):** Render → Metrics → CPU around 08:25–08:28 UTC should sit at the
   0.1-CPU ceiling; events should show the instance marked unhealthy without a restart.
2. **Hash cost is a team security decision, not changed here.** At 0.1 CPU every login/PIN costs ≈2.6 s, so 5
   people unlocking at once still wait ≈10–15 s even though the site no longer drops. Options: keep (safest),
   upgrade the instance, or lower PBKDF2 iterations (Django re-hashes on next login). A 4–6-digit PIN gets
   little from 1 M iterations offline; its real protection is the online throttle.
3. **Demo practice (no code):** one authorized demo account per presenter device, so one person's wrong PINs
   do not lock everyone (lock is per account), and no repeated taps on "Deblochează"/"Conectează-te" while a
   request is in flight.
4. Not tested: PostgreSQL connection behaviour under this load (no local Postgres), real phones.
