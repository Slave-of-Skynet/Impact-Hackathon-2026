# LOCAL SYNTHETIC — capturi pentru README-ul produs (issue #89, 2026-11-01)

Toate imaginile de mai jos sunt **capturi locale sintetice**, făcute special pentru README-ul public:

- checkout `origin/main@43c55f9` (fără modificări de cod), server Django dev (`config.settings.dev`),
  SQLite **disposable în afara repo-ului** (`%TEMP%\gustul-readme-89\db.sqlite3`), `seed_demo`
  (doar conturi fictive `@demo.local`; `DEMO_PASSWORD`/`DEMO_PIN` setate local, niciodată publicate).
- Parcursul a fost realizat **prin UI-ul normal** (login → panou → Mod Copil → catalog → raft → salvări de progres).
- Cartea din capturi, „Fata babei și fata moșneagului" (Ion Creangă), e **metadată sintetică adăugată local**
  (operă în domeniul public). Nu are fișier de copertă, deci UI folosește coperta **generată** (culoare + emoji) —
  intenționat, ca să nu apară în README copertile scanate din `static/img/covers/` cu drepturi
  `RIGHTS_UNVERIFIED` (vezi ledger, rândul 16).
- Seria „🔥 3 zile consecutive": două evenimente `ProgressEvent` au fost datate înapoi (vineri/sâmbătă),
  cu aceeași metodă documentată în [`issue-65/`](../issue-65/) — date sintetice, nu utilizatori reali.
- Browser: ZCode in-app Chromium, viewporturi 390×844 (mobil) și 1280×900 (desktop), Windows.
- **Nu sunt dovezi de pe hostul public** — verificările hostului rămân în
  [`acceptance-ledger.md`](../../acceptance-ledger.md). Fără date personale reale, parole, PIN-uri sau coduri de club.

| Fișier | Ce arată |
|---|---|
| `01-child-home-mobile-390.png` | Mod copil (Mia): mascota Gusti, seria de lectură „3 zile consecutive" cu săptămâna V–S–D, cartea curentă 35/120 (29%), meniul copilului. |
| `02-child-progress-saved-mobile-390.png` | Momentul de lectură: după salvarea paginii 35 — mascota „Bravo! Ai ajuns la pagina 35.", bara de progres 29%, formularul de salvare și butonul de terminare. |
| `03-parent-dashboard-desktop.png` | Panoul părintelui (desktop): cardul Miei — 35 pagini citite, „3 zile consecutive", cartea curentă „35 / 120 pag. (29%)", raport detaliat + intrare în Mod Copil; Alex fără lectură. |
