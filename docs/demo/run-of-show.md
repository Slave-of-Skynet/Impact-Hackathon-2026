# Run of show — demonstrația live (2–3 minute)

Pereche cu [`pitch-ro.md`](pitch-ro.md) (ce se spune) și [`staging-and-recovery.md`](staging-and-recovery.md)
(pregătirea, codurile, recuperarea). **Verificat de E2E**: același traseu rulează automat în
`tests/test_demo_flow.py::test_guardian_child_reading_report_finish_and_real_club` (CI verde pe `main@3f2bb62`).

## Pregătit ÎNAINTE de scenă (obligatoriu)

1. **Codul de club este emis din timp** de staff autorizat (admin → Membership code → plaintext afișat o
   singură dată) și pus într-un plic. **NU se creează cod în Django admin în timpul scenei** și nu se
   publică nicăieri. Codul e single-use: o răscumpărare reușită îl consumă.
2. Starea raftului copilului demo este verificată conform [`staging-and-recovery.md`](staging-and-recovery.md).
3. Hostul este „încălzit" (un `GET /carti/` cu 1–2 minute înainte — serviciul gratuit doarme după 15 min
   de inactivitate; măsoară trezirea reală, nu o presupune).
4. Două **profiluri de browser separate** pe același laptop (sau laptop + telefon): „Părinte" și „Copil".
   Profiluri separate = sesiuni separate; nu două tab-uri în același profil.

## Traseul principal (țintă 2:30)

| # | Timp | Fereastra | Acțiune exactă | Rezultat așteptat |
|---|---|---|---|---|
| 1 | 0:00–0:15 | Părinte | Deschide `/cont/intrare/` → autentificare `parinte1@demo.local` (parola demo, nu o publicăm) | Aterizează pe `/panou/`, vede cardurile Mia și Alex |
| 2 | 0:15–0:30 | Părinte | Pe cardul Miei apasă butonul **mod copil** (`POST /familie/< Mia >/mod-copil/`) | `/copil/` — home copil cu mascota și cartea curentă |
| 3 | 0:30–0:55 | Copil | Catalog → „Capra cu trei iezi" → **„Adaugă pe raft"** → deschide cartea din `/copil/` | Cartea apare „Citesc acum"; ecranul de progres `/raft/<entry>/` |
| 4 | 0:55–1:10 | Copil | Introdu **35** → Salvează | Partial HTMX: bară ~29%, mascota „Bravo! Ai ajuns la pagina 35." |
| 5 | 1:10–1:25 | Părinte (a 2-a sesiune) | Refresh `/panou/` → raportul Miei | **35/120 vizibil imediat** — aceeași bază de date, sesiune separată |
| 6 | 1:25–1:45 | Copil | Pe ecranul cărții: **„Am terminat cartea"** → aruncă o privire la `/realizari/` | Partial „Felicitări"; insigna **„Prima carte"**; insigna de club afișată blocată „pentru membrii clubului" |
| 7 | 1:45–2:00 | Copil→Părinte | Apasă „Mod Părinte" → `/parinte/` → introdu PIN-ul corect | Revine în modul adult pe `/panou/` — arătăm că PIN-ul păzește trecerea |
| 8 | 2:00–2:15 | Părinte | `/club/cod/` → copil: **Mia**, cod din plic | Confirmare „Membru al clubului până la …"; al doilea cod sau re-folosire → 422 generic |
| 9 | 2:15–2:35 | Părinte→Copil | Repetă pasul 2 (mod copil pentru Mia) → `/clubul-meu/` → `/realizari/` | Activitățile clubului vizibile (member-only); insigna **„Cititor de Club"** deblocată |

Rezervă de timp: pașii 6 și 9 pot fi comprimați dacă întrebările vin mai devreme; pasul 5 este
**nedescurcabila** dovadă a persistenței — nu-l sări.

## Traseul rapid de rezervă (~1:00, dacă ceva se blochează)

1. Părinte autentificat → mod copil Mia (pas 2).
2. Cartea deja pe raft (stare verificată înainte) → salvează 35/120 (pas 4).
3. Fereastra Părinte → refresh → 35/120 (pas 5). **Stop.** Închizi cu: „Asta e produsul: progresul copilului,
   vizibil familiei, protejat de PIN."
4. Dacă și asta eșuează pe host: **fallback laptop** conform [`staging-and-recovery.md`](staging-and-recovery.md)
   (SQLite disposable local, același script, `http://127.0.0.1:8000`).

## Greșeli de evitat (constrânsuri hard)

- **Fără** crearea/afișarea codului în admin în timpul scenei; **fără** coduri fixe publicate (`CLUB-DEMO-2026`
  și prietenii sunt interzise în seed, teste, docs).
- **Fără** `seed_demo --reset` pe baza de date demo live — șterge rafturile și premiile copiilor demo.
- **Fără** parole/PIN/coduri reale pe ecran mai mult decât e necesar; nu le arăta în camere mari și nu le
  pune în slide-uri.
- Dacă o salvare eșuează pe scenă: **nu** deschide DevTools; treci pe traseul rapid de rezervă și menționează
  onest „rețeaua de la locație" — aplicația arată „Nu s-a salvat", nu minte.
