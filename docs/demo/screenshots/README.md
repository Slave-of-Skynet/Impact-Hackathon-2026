# LOCAL SYNTHETIC — скриншоты локальной браузерной проверки (2026-10-31)

Все изображения ниже — **локальные синтетические** прогоны: Django dev server
(`config.settings.dev`), disposable SQLite за пределами репозитория, `seed_demo`
(только вымышленные `@demo.local` аккаунты и книги из общественного достояния).
**Никаких реальных персональных данных, паролей, PIN-кодов или кодов клуба.**
Это НЕ доказательства работы на публичном хосте — проверка Render остаётся в
[`acceptance-ledger.md`](../acceptance-ledger.md) как NOT RUN.

Среда: checkout `origin/main@3f2bb62` + локально применённый незафиксированный PR
[#51](https://github.com/Slave-of-Skynet/Impact-Hackathon-2026/pull/51) (маршрут `/`),
Windows 10.0.26300, браузер ZCode in-app (Chromium), viewport 1280×900.

| Файл | Что показано |
|---|---|
| `01-local-landing-local-synthetic.png` | Публичный landing `/` (исправление #49) — hero, ссылки «Creează cont gratuit» / «Explorează cărțile», карточки возможностей |
| `02-local-parent-dashboard-local-synthetic.png` | `/panou/` после входа `parinte1@demo.local` — приветствие, статистика, карточки детей Mia и Alex с кнопками «Raport detaliat» / «Mod Copil» |
| `03-local-pwa-install-hint-local-synthetic.png` | Футер `/` с PWA-подсказкой «Cum instalez aplicația?» (исправление #58): кнопка установки скрыта (в этом Chromium `beforeinstallprompt` не сработал), раскрыты реальные шаги меню ⋮ для Android Chrome и Safari для iPhone |
| `04-local-landing-no-brand-emoji-desktop.png` | `/` desktop 1280px (исправление #73 A): бренд `Gustul Cărților` в шапке без эмодзи 📖 |
| `05-local-landing-no-brand-emoji-390px.png` | `/` mobile 390px (#73 A): бренд без эмодзи, мобильное меню не сломано |
| `06-local-child-report-dates-desktop.png` | `/familie/<child>/` desktop (#73 B): «Obținută la: 31.10.2026» и «Valabil până la: 19.01.2027» — числовой румынский формат без русских месяцев |
| `07-local-child-report-dates-390px.png` | `/familie/<child>/` mobile 390px (#73 B): те же даты, мобильная вёрстка целая |
| `08-local-book-detail-genre-label.png` | `/carti/<book>/` desktop (#73 D): бейдж жанра «Basme» вместо кода `fairy_tale` |

Проверенные шаги без скриншота (подтверждены DOM-снимками, журнал в PR):
вход в детском режиме → каталог → «Capra cu trei iezi» → добавление на полку →
сохранение страницы 35/120 через настоящую HTMX-форму (маскот: «Bravo! Ai ajuns
la pagina 35.») → карточка Mia в панели родителя показывает 35/120 (29%) →
PIN-шлюз: неверный PIN даёт «⚠️ PIN greșit.», верный возвращает на `/panou/` →
`/clubul-meu/` для не-участника: «Acces rezervat membrilor clubului.» →
выход + повторный вход: 35/120 сохраняется.
