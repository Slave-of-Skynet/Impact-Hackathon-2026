# Acceptance Android fizic — PWA instalabilă, offline, dispozitiv partajat (issue #35)

> **Status: `NOT RUN` în totalitate până când o persoană cu dispozitiv fizic execută pașii și
> completează rezultatele.** Nu există NICIUN rezultat înregistrat în acest document; agentul sau
> emulatorul desktop **nu** pot produce `PASS`. Completează câmpurile „Observat" cu ce s-a văzut
> real, nu cu ce era așteptat.

## 0. Condiții prealabile (completează înainte de test)

| Câmp | Valoare (completează) |
|---|---|
| Model telefon / versiune Android | |
| Browser + versiune (ex. Chrome 130.x) | |
| Data + operator / tip rețea (**date mobile, NU Wi-Fi**) | |
| Operator test (persoană fizică) | |
| Cont sintetic nou folosit (create prin UI, **fără publicarea parolei/PIN**) | |
| Sesii părinte A pregătite separat (alt profil browser / laptop) pentru verificare încrucișată | |

**Reguli de siguranță la testare:**
- **Un cont guardian sintetic dedicat per testator simultan** — nu partaja contul, ca o încercare
  greșită de PIN a unuia să nu blocheze pe ceilalți (lock e per cont: 5 greșeli → 5 min).
- **Niciodată 5 PIN greșite consecutive pe contul folosit la scenă.** Cazul negativ PIN se face pe
  cont de consum, maximum 1–2 încercări greșite.
- Fără parole/PIN/coduri de club/date reale în capturi; înainte de a atașa orice screenshot/video,
  verifică că nu apar câmpuri de autentificare completate, adrese de email reale sau cookie-uri.

## 1. Pași de execuție (fiecare pas: completează „Observat" + „Status")

### T1 — Login și catalog pe date mobile

1. Deschide `https://gustul-cartilor.onrender.com` în Chrome (date mobile). Conectare cu contul sintetic nou.
2. Deschide `/carti/`, alege o carte (verifică numărul real de pagini, ex. „Capra cu trei iezi" = 120), adaug-o pe raft.
3. Salvează un progres (ex. 35) — notă: salvarea de pe telefon trebuie să spună „Salvat cu succes! ✓".
4. Verificare încrucișată: sesiunea adult A (alt profil/dispozitiv) → refresh `/panou/` → același progres.

| Măsurat | Valoare |
|---|---|
| Timp de login simțit (real, nu estimat) | |
| Latența percepută la salvare | |
| Observat | |
| Status | `NOT RUN` → `PASS` / `FAIL(+defect)` |

### T2 — Install affordance + Add to Home Screen

1. În sesiunea adult/copy publică: apare butonul de instalare al site-ului (affordance `beforeinstallprompt`)
   sau indică absența lui (atunci se folosește calea manuală de la pasul 2).
2. Meniul Chrome (⋮) → **„Instalează aplicația"** sau **„Adaugă pe ecranul de start"** — confirmă dialogul.
3. Verifică iconița apărută pe launcher/eco (nume „Gustul Cărților", icon 192/512 corect tăiat).

| Măsurat | Valoare |
|---|---|
| Cale folosită (buton site / meniu manual) | |
| Timp total instalare (real) | |
| Observat (nume/iconiță) | |
| Status | `NOT RUN` → `PASS` / `FAIL(+defect)` |

### T3 — Lansarea din icon instalat + rutarea `/app/` + limitele PIN

1. Închide complet Chrome; pornește aplicația **din iconul instalat** (fereastră standalone, fără UI de browser).
2. Repetă pentru cele 3 stări și notează unde aterizează `/app/`:
   - deconectat (anonim) → trebuie să ajungă pe landing-ul public `/`;
   - sesiune adult → `/panou/`;
   - mod copil activ → `/copil/`.
3. Din modul copil tastat `/panou/` → trebuie PIN-geit pe `/parinte/` (fără date de părinte);
   PIN corect → banner „Acces parental deblocat"; **Blochează** → PIN din nou obligatoriu.

| Observat | |
|---|---|
| Status | `NOT RUN` → `PASS` / `FAIL(+defect)` |

### T4 — Offline: ecranul, salvarea eșuată, revenirea

1. Pregătește o carte nefinalizată pe raft (nu cea terminată). Activează **modul avion** (date mobile oprite).
2. Deschide aplicația instalată și navighează: notează ce se vede real — pagina `/offline/` (conținut,
   butoane disponibile) sau eroare de rețea; ce rămâne funcțional.
3. Încearcă o salvare de progres în modul avion → **trebuie** să apară „Nu s-a salvat" / mesaj de eroare,
   **falsul „salvat" este defect grav (FAIL)**.
4. Notează valoarea afișată local; dezactivează modul avion; **fără a rescrie**, verifică după refresh că
   valoarea din server rămâne nemodificată (cea de dinainte de încercarea offline).
5. Rescrie progresul (acum online) → „Salvat cu succes! ✓" → verifică în sesiunea A.

| Măsurat | Valoare |
|---|---|
| Ce se vede offline (conținut real + butoane funcționale) | |
| Comportamentul salvării offline (text real afișat) | |
| Valoarea din server după reconnect, înainte de rescriere | |
| Status | `NOT RUN` → `PASS` / `FAIL(+defect)` |

### T5 — Negative: logout/Back/bfcache, al doilea browser

1. După Lock (T3), din modul copil apasă **Back** repetat și redeschide din istorie pagini adulte —
   nu trebuie să apară conținut privat contra permisiunilor (bfcache). Repeat după **logout**.
2. Dacă există al doilea browser instalat (Firefox etc.): repetă T1–T3 rapid (doar lansator + PIN) —
   sesiunile nu trebuie să se scurgă între browsere.
3. Nu inspecta conturile altora; folosește doar conturile de test create de tine.

| Observat | |
|---|---|
| Status | `NOT RUN` → `PASS` / `FAIL(+defect)` / `BLOCKED(+motive)` |

## 2. Registrul de dovezi (fără secrete)

| Pas | Screenshot/video (cale/link) | Notițe |
|---|---|---|
| T1 | | |
| T2 | | |
| T3 | | |
| T4 | | |
| T5 | | |

Stocare recomandată: `docs/demo/screenshots/issue-35/` (sanitizat) sau link la stocare aprobată;
notează în [`acceptance-ledger.md`](acceptance-ledger.md) rândul 9 și în
[`final-release-decision.md`](final-release-decision.md).

## 3. Ce NU dovedește acest document

- Nu dovedește fiabilitate la 5 dispozitive simultane (rândul 17 din ledger — ziua de demo, reguli în
  [`docs/qa/issue-59-demo-502.md`](../qa/issue-59-demo-502.md)).
- Nu dovedește persistența după restart/redeploy Render (rândul 13).
- Nu schimbă statutul `RIGHTS_UNVERIFIED` al copertelor afișate în catalog.
- Un `PASS` aici nu închide #35 singur: sunt necesare și repetiția 4:00 cronometrată, codurile de club
  pregătite de staff și decizia de conținut a owner-ului.
