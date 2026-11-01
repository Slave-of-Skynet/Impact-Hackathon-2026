# Final release decision — issue #35 (2026-11-01)

**Scop:** matricea release-gate pentru **Gustul Cărților**, blocantele rămase și lista explicită de
decizii umane. Acest document **nu** declară demo-ready și **nu** închide #35 — independent review
(ChatGPT project brain) + acceptanța owner-ului sunt condiții obligatorii.

## 1. Starea verificată

| Element | Valoare |
|---|---|
| `main` la redactare | `28b7030ee412139d550dace27a24cb8fa976dfa4` (#87), CI [41205782111](https://github.com/Slave-of-Skynet/Impact-Hackathon-2026/actions/runs/41205782111): 579 passed / 4 skipped |
| Deploy Render | `dep-dbiuqdivcj2c73edhvug` pe exact `28b7030`, LIVE din 31.10.2026 13:30 UTC |
| Host verificat la 01.11.2026 | `/`, `/carti/`, `/healthz/` (`{"status": "ok", "db": true}`), `/offline/`, manifest, `sw.js`, coperte — 200 |
| Verificări browser reale (host public, cont sintetic de consum) | B1 două-sesiuni 35/120 **PASS** · B2 parcurs extins **PASS** · B3 PIN/încredere/Lock **PASS** · `/app/` launcher **PASS** (desktop) · `/clubul-meu/` non-membru **403 PASS** |
| PR al release-gate | `docs(release): finalize #35 Romanian pitch and evidence gate` (link în #35) |

## 2. Matricea release-gate

| Poartă | Status | Blocant rămâne? | Detalii |
|---|---|---|---|
| Pitch RO 4:00 corect (11 secțiuni, 240 s) + 0:30 urgență + 2:00 Q&A | **DONE (text)** | Nu — dar repetiția umană lipsește | [`pitch-ro.md`](pitch-ro.md); cronometrat uman = rândul 14 din ledger |
| B1: B→A 35/120 pe host public | **PASS** | Nu | ledger rândul 1 + [`screenshots/issue-35/`](screenshots/issue-35/) |
| B2: parcurs funcțional extins pe host | **PASS** | Nu (partial: club code) | ledger rândurile 5–6; cod club = rândul 7 NOT RUN |
| B3: PIN / încredere 30 min / Lock | **PASS** | Nu (1 încercare greșită max; blocarea completă rămâne test automat) | ledger rândul 8 |
| Android fizic: instalare PWA + offline | **NOT RUN** | **DA — P0** | runbook [`android-pwa-acceptance.md`](android-pwa-acceptance.md) (T1–T5); emulator ≠ PASS fizic |
| Lansator `/app/` pe cele 3 stări | **PASS (desktop)** | Nu | ledger rândul 4; fizic rămâne la Android |
| Fiabilitate 5 dispozitive | **NOT RUN** | P1 (ziua demo) | reguli [`docs/qa/issue-59-demo-502.md`](../qa/issue-59-demo-502.md) |
| Persistență după restart/redeploy real | **NOT RUN** | DA (decizie owner; nu se forțează) | ledger rândul 13; #43 rămâne doar sintetic |
| Cold start măsurat | **PASS** — 32,36 s primul request după 16 min idle (01.11.2026) | Nu | ledger rândul 12 |
| Fallback laptop Mode A repetat | **NOT RUN** | P1 (recomandat înainte de demo) | [`docs/demo-deployment.md` §10](../demo-deployment.md) |
| Înregistrare backup demo | **NOT RUN** | P1 | după prima rulare reușită |
| **Drepturi coperte (12 fișiere)** | **BLOCKED — `RIGHTS_UNVERIFIED`** | **DA — P0 de conținut** | inventar în PR; fie permisiuni scrise fișier-cu-fișier, fie PR țintit de înlocuire/eliminare |
| Repetiție cronometrată 4:00 (×2) + rulare de rezervă | **NOT RUN** | **DA — P0** | fișa de cronometrat în [`pitch-ro.md`](pitch-ro.md) |
| Cod de club pe host (răscumpărare + colț membru) | **NOT RUN** | P1 (ținta E2E completă) | necesită cod emis de staff din `/admin/` |

## 3. Decizii umane necesare (owner + termen: înainte de demo)

1. **Vladimir (owner):** acceptă/elimină copertele — decizie de drepturi de conținut (rândul 16 din
   ledger). Niciun agent nu aprobă drepturi în tăcere.
2. **Vladimir (owner Render):** decide dacă se execută un restart/redeploy real pentru dovada de
   persistență (rândul 13) — nu se face doar pentru bifă.
3. **Vladimir + Denis:** repetiția cronometrată 4:00 (rândul 14) + testul Android fizic pe
   [`android-pwa-acceptance.md`](android-pwa-acceptance.md) (rândul 9) + înregistrarea backup (rândul 18).
4. **Vladimir (staff):** emite 2–3 coduri de club single-use în plic pentru ziua demo (rândul 7).
5. **Echipa:** dacă un stakeholder cere sumă monetară — decizie înainte de scenă; agentul nu inventează sume.

## 4. Regula de închidere

`demo-ready` + închiderea #35 se fac **doar după**: review independent (ChatGPT) + merge + corelarea
deploy-SHA + B1 reproductibil pe host + Android fizic sau excepție documentată de owner + PIN/Lock
acceptat + repetiție 4:00 măsurată + fără 502/500 blocante pe scenă + drepturi de conținut rezolvate
sau coperte retrase. Fiecare „waiver" se documentează explicit aici, cu semnătura owner-ului —
**rândul respectiv rămâne `NOT RUN`/`BLOCKED` în ledger, nu devine PASS**.
