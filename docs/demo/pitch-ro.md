# Pitch (RO) — 4:00 (240 s) · Gustul Cărților · Impact Hackathon 2026

**Scop oficial (organizatorii):** pitch pentru juriu de **exact 240 s (4:00)**, urmat de **până la 120 s Q&A**.
Formatul vechi de „3:00 pitch" este **învechit** pentru juriu; variația istorică de 3 minute rămâne doar ca
*repetiție funcțională E2E* separată, în [`run-of-show.md`](run-of-show.md) — nu este pitch-ul juriului.

**Cele 11 secțiuni oficiale, în ordinea impusă** (total exact 240 s): Copertă 10 s · Problema 30 s ·
Soluția 45 s · Validare / Progres 30 s · Model de sustenabilitate 30 s · Oportunitatea 15 s ·
Resurse financiare 15 s · Echipa 30 s · Alternative / Concurență 15 s · Finanțare necesară 10 s ·
Concluzie 10 s. **Nu se fuzionează și nu se elimină nicio secțiune.** Nu se inventează ponderi ale juriului.

**Vorbitori:** Vladimir (narativ + pitch) și Denis (demonstrația live, dacă e disponibil; altfel Vladimir
preia și demo-ul — replicile lui Denis sunt scrise ca să poată fi citite de oricine). **Înainte de scenă:**
două sesiuni independente autentificate în **același cont guardian** — **A = adult** pe `/panou/`, **B = copil**
(mod copil, pe ecranul de progres al cărții nefinalizate, pregătit „35"). Nu transforma A în mod copil.

**Regulă de onestitate (obligatorie pentru orice adaptare):**
- `FACT` = verificat (cod pe `main`, test rulat, pagină deschisă pe host, document din repo).
- `HYPOTHESIS` = intenție sau presupunere — **nu** o afirmație despre prezent.
- Fără statistici proprii inventate, fără criterii de juriu asumate, fără cifre TAM, fără „utilizatori reali".
  Singura cifră de context permisă: **„în jur de 70 de familii" — raportat de partener în întâlnirea din
  30.10.2026** ([discovery brief](../discovery/gustul-cartilor-meeting-2026-10-30.md), „reported, approximate").
- Nu se pretinde că PIN-ul verifică vârsta sau identitatea; nu se afirmă „securitate certificată".

---

## Fluxul de scenă — 0:00 → 4:00

### 1. Copertă — 0:00–0:10 (10 s)

- **Cine:** Vladimir.
- **Vizual:** slide de copertă (logo + „Gustul Cărților" + numele echipei) sau, la nevoie, landing `/` pe host.
- **Replică exactă (RO):** „Bună ziua! Suntem echipa **Gustul Cărților** — jurnalul de lectură al familiei,
  în limba română, pentru copiii de 7–15 ani și pentru cluburile de lectură care îi însoțesc."
- **Tranziție/fallback:** dacă slide-ul nu se deschide → arăți direct landing-ul `/` și continui.
- **Statut:** `FACT` (produsul există și rulează).

### 2. Problema — 0:10–0:40 (30 s)

- **Cine:** Vladimir.
- **Vizual:** slide „Problema" (sau rămâi pe landing; nu intra încă în aplicație).
- **Replică exactă (RO):** „Clubul de lectură cu care am discutat, la 30 octombrie, ne-a spus ceva simplu:
  **jurnalul de lectură este un scop central** pentru ei, iar familiile iau cărțile acasă — copilul citește
  departe de ochii clubului. Astăzi, acel drum — paginile citite, entuziasmul, abandonul — trăiește în
  caiete și în memoria părinților. Nu există un loc calm, în română, unde familia să vadă progresul fără
  presiune și fără ecrane sociale. **Nu avem statistici proprii — această nevoie e ipoteza noastră de
  lucru, iar pilotul o verifică.**"
- **Tranziție/fallback:** „Și exact aici vine produsul nostru."
- **Statut:** prima jumătate `FACT` (raportat de partener în întâlnirea din 30.10.2026, cu transcriere în
  repo); a doua jumătate + lipsa de soluții `HYPOTHESIS`, declarată ca atare.

### 3. Soluția — 0:40–1:25 (45 s)

- **Cine:** Vladimir 0:40–0:55, apoi **Denis** 0:55–1:25 (ecranul **B — copil**).
- **Vizual:** fereastra **B** (copil), cartea **„Capra cu trei iezi" — 120 pagini, nefinalizată**,
  ecranul de progres deja deschis.
- **Replică exactă (RO), Vladimir:** „Soluția noastră e o aplicație web în română, pentru toată familia.
  Copilul are un mod simplu, cu mascotă. Părintele are panoul lui, privat. Iar trecerea dintre ele e
  protejată de un PIN parental. Denis arată live."
- **Replică exactă (RO), Denis:** „Copilul alege cartea din catalog și citește acasă, pe hârtie. Când se
  oprește, salvează unde a ajuns — uită-te: pagina **35** din 120…" *(apasă „Am citit până aici")* „…
  și gata: mascotă, bară de progres, salvat."
- **Tranziție/fallback:** dacă salvarea ezită pe scenă: „Aplicația nu minte niciodată: dacă rețeaua
  ezită, scrie «Nu s-a salvat» — repetăm o dată și continuăm." (apoi traseul rapid din
  [`run-of-show.md`](run-of-show.md)).
- **Statut:** `FACT` (flux demonstrat live pe host public; Salvare 35/120 rulată real la 01.11.2026 —
  vezi [`acceptance-ledger.md`](acceptance-ledger.md)). **NU** încerca pe scenă: login, finish, PIN,
  răscumpărare cod, evaluări, întrebări — toate sunt în repetiția extinsă.

### 4. Validare / Progres — 1:25–1:55 (30 s)

- **Cine:** **Denis** până la 1:40, Vladimir 1:40–1:55.
- **Vizual:** **comutarea exactă B→A**: Denis trece pe fereastra **A (adult)** și apasă **refresh** pe `/panou/`.
- **Replică exactă (RO), Denis:** „Iar acum partea care contează: sesiunea părintelui — alt dispozitiv,
  alt login, făcut dinainte." *(refresh)* „Aceleași **35 din 120** — salvate de copil, văzute de părinte,
  aceeași bază de date."
- **Replică exactă (RO), Vladimir:** „În spatele demo-ului: produs funcțional pe `main`, **579 de teste
  automate verzi**, aplicație reală pe Render. Ce nu avem **încă**: utilizatori reali verificați și
  tracțiune măsurată — exact asta ne propunem să verificăm la pilotul pe care îl propunem."
- **Tranziție/fallback:** dacă A nu se reîmprospătează: „Actualizăm din nou sesiunea părintelui…" și
  reîncarcă o dată; dacă tot nu merge → traseul rapid de rezervă.
- **Statut:** B→A `FACT` (verificat pe hostul public la 01.11.2026, două sesiuni independente;
  **independent reviewer a inspectat dovezile, dar nu a reprodus singur fluxul autentificat**);
  „579 teste" `FACT` (CI Ubuntu pe `main@28b7030`); „nu avem utilizatori reali verificați și nici
  tracțiune măsurată" — spus explicit.

### 5. Model de sustenabilitate — 1:55–2:25 (30 s)

- **Cine:** Vladimir.
- **Vizual:** slide „Model de sustenabilitate" sau ecran A (panoul părintelui) pe fundal.
- **Replică exactă (RO):** „Cum susținem produsul? Astăzi rulează pe planul gratuit Render + PostgreSQL,
  deci demo-ul costă aproximativ zero — **un fapt curent, limitat**. Când pilotul crește, **costul
  găzduirii și al bazei de date va fi bugetat după tarifele curente, trafic și necesarul de mentenanță**.
  Întreținerea e muncă reală a echipei: remedieri, securitate, configurare; moderarea rămâne mică
  **prin construcție** — fără mesagerie, fără profiluri publice — dar **nu e gratuită**: e timp de
  oameni. **Nu promitem găzduire gratuită pentru totdeauna.**"
- **Tranziție/fallback:** „Deci modelul e realist: cost mic, responsabilitate clară."
- **Statut:** planul gratuit + degradare/cold-start `FACT`; cifrele de cost viitoare `HYPOTHESIS`
  (marcate „estimare").

### 6. Oportunitatea — 2:25–2:40 (15 s)

- **Cine:** Vladimir.
- **Vizual:** slide „Oportunitatea".
- **Replică exactă (RO):** „Oportunitatea e locală și concretă: clubul partener a raportat **în jur de
  70 de familii** implicate — familiile **clubului**, nu utilizatori ai platformei noastre. Propunem să
  începem pilotul cu **10 familii**. Nu pretindem că știm mărimea pieței — știm doar că publicul acesta
  există și e la un telefon distanță."
- **Tranziție/fallback:** „Și ce ne trebuie ca să atingem aceste familii?"
- **Statut:** „70 de familii" = `FACT` ca *raport al partenerului* (aproximativ, din transcriere);
  nu-l folosi ca TAM sau ca tracțiune a produsului nostru. „Pilot cu 10 familii" = `PROPOSAL` —
  propunerea noastră, subiect de acord cu partenerul/owner-ul, nu termeni acceptați.

### 7. Resurse financiare — 2:40–2:55 (15 s)

- **Cine:** Vladimir.
- **Vizual:** slide „Resurse".
- **Replică exactă (RO):** „Resursele de azi: timpul celor cinci membri, infrastructură gratuită și cod
  propriu, scris de la zero. Pentru pilot **propunem să nu cerem bani** — cerem partenerul
  (`PROPOSAL`, nu decizie deja aprobată de toți stakeholders)."
- **Tranziție/fallback:** direct la „Echipa".
- **Statut:** `FACT` (plan gratuit în uz); licențierea codului rămâne nehotărâtă — nu numiți proiectul
  „open-source".

### 8. Echipa — 2:55–3:25 (30 s)

- **Cine:** Vladimir (numele fiecăruia + o verigă).
- **Vizual:** slide „Echipa" cu 5 nume.
- **Replică exactă (RO):** „Suntem cinci. **Vladimir** — interfața adultului, PWA și integrarea finală.
  **Alice** — domeniul lecturii: raft, progres, salvări sigure sub concurență. **Arsenii** — fundația:
  identitate, modul copil, PIN, seria de zile de citit. **Denis** — experiența copilului: mascotă, tema
  caldă de poveste, evaluările cu stele. **Igor** — clubul: coduri, insigne și auditul de siguranță al
  copiilor. Fiecare livrare a trecut prin review independent și testare automată."
- **Tranziție/fallback:** „Și de ce noi, nu alții?"
- **Statut:** `FACT` — rolurile corespund livrărilor reale din GitHub (PR-uri revizuite independent).

### 9. Alternative / Concurență — 3:25–3:40 (15 s)

- **Cine:** Vladimir.
- **Vizual:** slide „Alternative".
- **Replică exactă (RO):** „Există trackere generale de lectură și rețele pentru cititori adulți. Nu le
  criticăm — servesc altui public. Noi construim altceva: controlul părintelui **în produs**, drepturile
  clubului printr-un cod unic și **niciun profil public de copil**."
- **Tranziție/fallback:** direct la „Finanțare".
- **Statut:** `FACT` pentru ce face produsul; **nu** enumera defecte inventate ale competitorilor
  (vezi răspunsul pregătit „De ce nu Goodreads/Discord?", mai jos).

### 10. Finanțare necesară — 3:40–3:50 (10 s)

- **Cine:** Vladimir.
- **Vizual:** slide „Cererea".
- **Replică exactă (RO):** „Vă **propunem** un pilot: **10 familii, o lună**, împreună definim regulile
  de siguranță și măsurăm dacă cititul crește."
- **Tranziție/fallback:** „Asta e tot ce cerem — și tot ce ne trebuie."
- **Statut:** `PROPOSAL / HYPOTHESIS` — **propunerea echipei, subiect de acord cu partenerul și
  owner-ul**, nu termeni deja acceptați. **Dacă un stakeholder cere o sumă numerică:** decizie de owner
  înainte de scenă; **nu inventa niciodată o sumă pe scenă**.

### 11. Concluzie — 3:50–4:00 (10 s)

- **Cine:** Vladimir.
- **Vizual:** slide final (logo + „Încercați cu noi") sau ecranul A cu progresul copilului.
- **Replică exactă (RO):** „**Gustul Cărților: copilul citește, familia vede, clubul rămâne aproape.**
  Vă invităm să-l încercați împreună cu noi. Mulțumim!"
- **Statut:** `FACT` (invitația) + viitorul (schimb de cărți, întâlniri offline) rămâne condiționat de
  siguranță și validarea partenerului — nu-l promiteți în Concluzie.

**Total: 240 s exact.** Replicile sunt scrise pentru ritm normal de vorbire; **măsoară** la repetiție
(vezi «Fișa de cronometrat», mai jos) și comprimă limbajul, nu secțiunile.

---

## Răspunsul pregătit: „De ce nu Goodreads/Discord?" (Q&A, 20–30 s)

**Nu enumerăm defecte ale competitorilor** — diferența e în ce alegem să facem (și ce refuzăm să facem):

1. **Controlul familiei, nu rețeaua.** La noi copilul nu are profil public, nu are DM, nu apare în feed-uri.
   Profilul copilului există doar în contul părintelui; serverul separă familiile. (`FACT`,
   audit: [`docs/reviews/2026-10-31-issue-44-child-safeguarding-igor.md`](../reviews/2026-10-31-issue-44-child-safeguarding-igor.md))
2. **Drepturile clubului.** Codul unic, emis de staff, activează activitățile clubului doar pentru membri —
   clubul își controlează propriul cerc, fără grupuri deschise pe care le moderăm greu. (`FACT`)
3. **Legătura offline, ca ipoteză viitoare.** Platformele generale nu cunosc clubul vostru de cartier.
   Noi vrem ca membrii să vadă activitățile publicate de club (`FACT`) și, în viitor, să faciliteze
   întâlniri reale — **doar după** regulile de însoțire și siguranță stabilite cu partenerul
   (`HYPOTHESIS`, nu prezent).
4. **Ce refuzăm intenționat azi:** mesagerie deschisă, profiluri publice de copii, generare AI, plăți —
   fiecare vine cu costuri de moderare și riscuri pentru minori. Mai puțin, dar sigur.

**Răspuns scurt (RO):** „Goodreads e pentru cititorul adult care vrea rețea; Discord e pentru comunități
open. Noi construim exact opusul pentru copii: fără profil public, fără DM, cu părintele în cadrul
produsului și cu clubul proprietarul propriului cerc. Socializarea reală — întâlnirile — o adăugăm
ulterior, doar împreună cu partenerul și cu regulile lui de siguranță."

## Pitch de urgență — 30 de secunde (RO)

> **64 de cuvinte** (≈ 130 cuv./min — ritm real de prezentare, cu timp pentru comutarea ecranului).
> Trei suporturi: (a) produs + problemă, (b) demo B→A + modul familial privat, (c) propunerea de pilot.

„Gustul Cărților e jurnalul de lectură al familiei, în română — pentru copiii care citesc pe hârtie și
pentru cluburile lor. Ați văzut demo-ul: copilul salvează pagina 35 din 120, iar părintele, în altă
sesiune independentă, o vede imediat. Ieșirea din modul copil e protejată de PIN; fără profiluri
publice, fără mesagerie. Vă propunem un pilot: zece familii, o lună, împreună măsurăm dacă cititul crește."

- `(a)` = fraza 1 · `(b)` = fraza 2–3 (arată B copil, apoi comută pe A adult în timpul frazei despre părinte)
  · `(c)` = fraza finală.
- Pilotul „zece familii, o lună" este `PROPOSAL` — **propunerea noastră**, nu termeni deja acceptați de
  partener; acordul aparține partenerului și owner-ului.

## Banca de răspunsuri Q&A — până la 120 s (RO)

Prieteni de ordine: răspuns scurt (15–20 s), onest, cu distincția fapt/ipoteză. Nu intra în detalii de
implementare dacă nu te întreabă nimeni.

1. **„Aveți dovezi de la partener? Impact real?"** — „Am avut o întâlnire cu un club de lectură local la
   30.10.2026: au numit jurnalul de lectură scop central și au raportat în jur de 70 de familii — familiile
   *clubului lor*, nu utilizatori ai platformei noastre. Aceasta e informație raportată, nu validare.
   Pilotul propus de 10 familii e exact pasul de validare pe care îl propunem (`PROPOSAL`, subiect de
   acord cu partenerul)."
2. **„Câți utilizatori reali aveți?"** — „**Nu avem utilizatori reali verificați și nici tracțiune
   măsurată.** Toate datele din demo sunt sintetice. Spunem asta public, în pitch."
3. **„De ce nu Goodreads / Discord?"** — răspunsul pregătit de mai sus (20–30 s).
4. **„Cât costă? Cine plătește?"** — „Acum: aproape zero — planul gratuit Render + PostgreSQL (**fapt
   curent, limitat**). După pilot: **costul găzduirii și al bazei de date se bugetează după tarifele
   curente, trafic și mentenanță** — nu dăm cifre de-a gata. Plus timpul echipei: **întreținerea și
   moderarea nu sunt gratuite — sunt timp de oameni**. Nu promitem gratuit pentru totdeauna."
5. **„Cine vede evaluările cu stele ale copilului?"** — „Evaluarea aparține cititorului. Media publică
   apare doar de la 3 evaluări; sub atât catalogul arată «Fără evaluări». Nu există evaluări false
   decorative."
6. **„Copilul poate accesa panoul părintelui pe dispozitiv comun?"** — „Ieșirea din modul copil cere PIN
   parental. După PIN există o fereastră de încredere de 30 de minute cu buton explicit de **Blocare**,
   care o închide imediat. PIN-ul protejează ieșirea din modul copil — **nu verifică vârsta sau
   identitatea** — și acest lucru îl spunem deschis."
7. **„GDPR / consimțământ pentru copii?"** — „În demonstrație folosim doar conturi și profiluri
   sintetice. Platforma are înregistrare publică, deci nu presupunem că toate înscrierile sunt fictive.
   Consimțământul parental, protecția datelor și retenția necesită reguli aprobate înainte de pilot
   (G1–G6); nu le prezentăm drept rezolvate."
8. **„Copertile cărților sunt licențiate?"** — „Onest: nu am încă confirmare de drepturi fișier cu
   fișier pentru cele 12 coperte publicate. E o decizie de conținut deschisă, cu plan de rezervă
   (fallback fără imagini) pregătit. Nu afirmăm că sunt licențiate."
9. **„PWA / offline pe Android?"** — „Codul are manifest, service worker și pagină offline, iar lansatorul
   `/app/` duce fiecare stare la ecranul corect. Ce nu am încă: instalarea și offline-ul verificate pe un
   Android fizic — o verificăm înainte de scenă, cu operator uman."
10. **„Am auzit de panne de 502 — e stabil?"** — „La 31.10 a fost o incidentă documentată: saturarea CPU
    pe planul gratuit a scurt timp picat rutarea, remadiată (1 worker × 8 thread-uri, health check-uri
    OK de atunci). Testul cu 5 dispozitive simultane rămâne pe lista zilei de demo — nu pretindem că e făcut."
11. **„Cât de capabilă e echipa?"** — „Cinci membri, fiecare cu livrări reale fuzionate prin review
    independent; 579 de teste verzi în CI. Nu afirmăm experiență în afara dovezilor din repo."
12. **„Cereți finanțare?"** — „Nicio sumă astăzi: **propunem** pilotul nefinanciar (10 familii, o lună,
    feedback) — `PROPOSAL`, nu termeni deja acceptați de partener. O cerere monetară ar fi o decizie
    separată a echipei, nu o inventăm pe scenă."

**Interdicții Q&A (hard):** PIN ≠ verificare de vârstă/identitate · fără copii reali în demo · fără
profiluri publice de copii sau DM · fără „securitate de nivel producție certificată" · fără cifre de
piață inventate · fără „copertile sunt licențiate" · fără promisiunea de hosting gratuit permanent.

---

## Fișa de cronometrat — OPERATOR ACTION REQUIRED (umân, nu agent)

> **Statut la 01.11.2026: `NOT RUN`.** Nu există încă nicio repetiție umană cronometrată a pitch-ului de
> 4:00. Agentul NU poate declara PASS pe baza textului. Operatorul cronometrează fiecare segment cu un
> cronometru real, completează coloana „Măsurat" și notează incidentele. Ținta: total măsurat < 4:00,
> păstrând toate cele 11 secțiuni.

| # | Segment | Țintă | Măsurat (run 1) | Măsurat (run 2) | Notițe |
|---|---|---|---|---|---|
| 1 | Copertă | 10 s | | | |
| 2 | Problema | 30 s | | | |
| 3 | Soluția (B copil salvează 35/120) | 45 s | | | |
| 4 | Validare (comutare B→A, refresh A) | 30 s | | | |
| 5 | Model de sustenabilitate | 30 s | | | |
| 6 | Oportunitatea | 15 s | | | |
| 7 | Resurse financiare | 15 s | | | |
| 8 | Echipa | 30 s | | | |
| 9 | Alternative / Concurență | 15 s | | | |
| 10 | Finanțare necesară | 10 s | | | |
| 11 | Concluzie | 10 s | | | |
| — | **TOTAL** | **240 s** | | | |

Plus: **o rulare de rezervă** completă pe host + **înregistrare backup** a demo-ului (fără parole/PIN/
coduri în cadru). Dacă timpul total măsurat depășește 240 s: comprimă limbajul din segmentele 5/8
(sustenabilitate, echipa), nu elimina secțiuni.

## Traducere rusă / подсказки команде

- **0:00 Коперта:** «Мы — Gustul Cărților, семейный дневник чтения на румынском для детей 7–15 и их клубов.»
- **0:10 Проблема:** клуб-партнёр на встрече 30.10.2026 назвал дневник чтения центральной целью;
  «70 семей» — *со слов партнёра*, приблизительно; остальное — гипотеза, так и говорим.
- **0:40 Решение (Владимир):** веб-приложение на румынском: детский режим с маскотом, приватная панель
  родителя, PIN между ними. **Денис:** ребёнок сохраняет 35/120 — только этот шаг.
- **1:25 Валидация (Денис → A):** переключение на окно родителя A, refresh → те же 35/120. Владимир:
  579 тестов зелёные, реальный хост; «подтверждённых пользователей нет и измеримой тракции нет» —
  так и говорим; пилот — наше **предложение** (PROPOSAL).
- **1:55 Сустейнабилити:** сейчас бесплатно (Render free) — текущий ограниченный факт; потом **стоимость
  хостинга и БД бюджетируется по текущим тарифам, трафику и maintenance** — без готовых цифр; модерация
  дешёвая по конструкции, но не бесплатная (время людей); бесплатность навсегда не обещаем.
- **2:25 Возможность:** локальный клуб, ~70 семей (со слов партнёра; **семьи клуба — не пользователи
  нашей платформы**), пилот — 10 семей (**наше предложение**, PROPOSAL); TAM не называем.
- **2:40 Ресурсы:** время пяти человек + бесплатная инфраструктура; для пилота деньги не нужны.
- **2:55 Команда:** Владимир — взрослый UI и PWA; Алиса — домен чтения; Арсений — фундамент и PIN;
  Денис — детский UX; Игорь — клуб и аудит безопасности.
- **3:25 Альтернативы:** не критикуем конкурентов; наш фокус — родительский контроль в продукте и права клуба.
- **3:40 Финансирование:** не деньги, а пилот — **наше предложение** (PROPOSAL, не принятые условия):
  10 семей, месяц, правила безопасности, замер чтения.
- **3:50 Вывод:** «Ребёнок читает — семья видит — клуб рядом. Попробуйте с нами.»

## Ce NU spunem pe scenă (verifică înainte de prezentare)

- Nu „70+ familii *ale noastre*" — 70 e raport al partenerului (aproximativ), nu tracțiunea produsului.
- Nu cifre PISA, nu TAM, nu „platforma universală pentru orice comunitate".
- Nu „copiii sunt verificați/în siguranță absolută": PIN protejează **ieșirea din modul copil**, nu vârsta.
- Nu „persistența pe Render e dovedită": dovedită doar sintetic (#43); restart/redeploy real — **NOT RUN**.
- Nu „aplicația e instalată pe Android": instalare fizică — **NOT RUN** (lansatorul `/app/` e verificat pe desktop).
- Nu „copertile sunt licențiate": 12 imagini publice `RIGHTS_UNVERIFIED`, decizie de conținut deschisă.
- Nu numim proiectul „open-source" (licența nu e decisă).
- Nu publicăm niciodată parole, PIN-uri, coduri de club sau date reale ale copiilor.
