# Issue #35 — evidence screenshots (REAL PUBLIC HOST, 2026-11-01)

All evidence below was captured on **`https://gustul-cartilor.onrender.com`** (public demo host,
`main@28b7030` deploy `dep-dbiuqdivcj2c73edhvug`) on **2026-11-01, ~02:15–02:30 Europe/Chisinau (+02)**,
with a **disposable synthetic guardian account** created through the normal UI (signup → 2 synthetic
children → PIN). **No real children, no passwords, PINs, session cookies or club codes are shown.**
The account name visible in the screenshots is synthetic (`Familia Test Gate35`, children
`Test-Mia-35` / `Test-Alex-35`).

| File | What it proves |
|---|---|
| `b1-child-session-35-of-120.png` | **Session B (child mode, separate browser)**: “Capra cu trei iezi” (120 pagini) after saving page 35 — mascot “Bravo! Ai ajuns la pagina 35.”, “Pagina 35 din 120”, 29%, progress bar. Independent session A (separate login, curl cookie jar) fetched `/panou/` and the child report seconds later and showed the same `35 / 120 pag. (29%)` — cross-session persistence on the real host. |
| `b3-parent-trusted-banner.png` | **Session B after correct PIN** (one bounded wrong-PIN attempt rejected earlier): “🔓 Acces parental deblocat — până la 02:52”, explicit Lock button (“Blochează”), child switcher. After pressing Lock, `/panou/` returned to the PIN gate; within the 30-min trust window a second owned child switch and repeat exit did **not** require the PIN again (“PIN-ul a fost deja verificat pentru acest interval scurt”). |

Not screenshot-able (text evidence only, recorded in [`../../acceptance-ledger.md`](../../acceptance-ledger.md)):
- Session A HTML contained `35 / 120 pag. (29%)` (dashboard) and `35 / 120` + `29%` (child report) at 02:21:28 +02.
- `/clubul-meu/` with a non-member session → **HTTP 403**.
- `/app/` launcher: anonymous → `/`, adult → `/panou/`, active child → `/copil/`.
- `/healthz/` → `{"status": "ok", "db": true}`.

Notes:
- The “Capra cu trei iezi” cover thumbnail inside the child screenshot is the same image already
  committed at `static/img/covers/` (see the rights caveat in the ledger: `RIGHTS_UNVERIFIED`).
- The synthetic test account remains on the host as harmless disposable data; it is not the stage
  account. Do not reuse it for the live demo.
- **Reviewer scope note:** the independent reviewer (PR #88 review `5725788524`) inspected these
  screenshots, but did **not** independently replay the authorized two-session flow; the adult-session
  A side of the B→A proof is executor-reported HTML evidence (`35 / 120 pag. (29%)` fetched by an
  independent curl login), pending an independently reproduced or redacted-logged acceptance run.
