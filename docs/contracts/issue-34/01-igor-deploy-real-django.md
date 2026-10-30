# ISSUE #34 — P0: разверни реальный Gustul Cărților на HTTPS с постоянной PostgreSQL

**Исполнитель:** Игорь (Codex; при необходимости Antigravity для ручной браузерной проверки).  
**Модель:** **gpt sol 6.1**, **effort: high**. Для сложного подтверждённого инфраструктурного блокера можно повысить **этой же модели** effort до **xhigh**.  
**Владелец приёмки и независимого code review:** ChatGPT project brain.  
**GitHub:** https://github.com/Slave-of-Skynet/Impact-Hackathon-2026  
**Issue:** https://github.com/Slave-of-Skynet/Impact-Hackathon-2026/issues/34  
**Зависимость:** #33 закрыт, E2E PR #37 merged в `main` (baseline `5bad4d39486678c73e0343638585ef3c87ae5e96`).  
**Связанная ручная браузерная приёмка:** #35 (Владимир + Денис).  
**Deliverable:** реальный работающий HTTPS URL + воспроизводимые конфигурация и evidence в `docs/demo-deployment.md` + GitHub PR.  
**Статус этого документа:** план исполнения, а не доказательство успешного деплоя.

> **Правило:** не ограничивайся `experiments/host-proof/`. Эта ветка содержит отдельную синтетическую Django-пробу, не продукт. Итоговый хост обязан исполнять `config.wsgi:application` настоящего приложения, его модели, сессии, маршруты, шаблоны и статические файлы.

## 0. Цель, ограничения времени и полномочия

Тебе поручена реализация последнего инфраструктурного P0 release gate. Дай команде **настоящий judge-facing product** по публичному HTTPS-адресу. Успех — это подтверждённое сохранение страницы 35/120 из детского режима, чтение её другой сессией родителя **после redeploy**, плюс готовность выполнить полный сценарий из #33 на том же хосте.

**Порядок приоритетов:**
1. работающий реальный Django + persistent DB + HTTPS + авторизованные формы;
2. доказанная сохранность значения между новыми процессами/deploy и отсутствие ложного сохранения;
3. переход в child mode, клубные права, раздача static/PWA;
4. удобный повторный деплой и запасной локальный вариант;
5. косметические улучшения и необязательная автоматизация — НЕ делать.

Не переделывай архитектуру, не расширяй функции, не исправляй P2 #40 в этом PR.

**Явные decision gates:** запрещены без подтверждения владельца:
- любые новые платные ресурсы или смена тарифного плана, влекущая оплату;
- использование существующей базы/сервиса с чужими данными или экспериментальными таблицами;
- удаление/recreate любой PostgreSQL, SQLite/volume, сервиса или пользовательских данных;
- изменение миграций/schema, публичных URL или базовых authz/club контрактов;
- перенос действующего `utm-curs-i-orar-2027` или изменение его конфигурации.

Бесплатные, изолированные и обратимые ресурсы разрешено рассматривать; **перед реальным созданием сверь бесплатность и лимиты в актуальном Render UI**, не опирайся на старое описание тарифов. Если нужен платёж, чужая база или неизбежная миграция — не делай рискованный шаг молча, оформи короткое `DECISION_REQUIRED` с альтернативами и закончи максимально возможную безопасную часть.

## 1. Актуальное известное состояние — подтверди live-проверкой

На 30.10.2026 `main` @ `5bad4d39486678c73e0343638585ef3c87ae5e96`; post-merge GitHub Actions [run 41127164520](https://github.com/Slave-of-Skynet/Impact-Hackathon-2026/actions/runs/41127164520): **366 passed, 4 pre-existing optional snapshot skips**, Django checks/migration drift clean.

Фактический стек:
- Python 3.12; Django 5.2; HTMX и installable PWA; `gunicorn`, `whitenoise`, `dj-database-url` уже в `pyproject.toml`;
- драйвер PostgreSQL **уже объявлен optional extra** `postgres = ["psycopg[binary]>=3.2,<4"]`. Сначала используй существующий lock/extra, не добавляй новую дублирующую зависимость;
- `config/wsgi.py` запускает production settings; `config/settings/prod.py` требует `DJANGO_SECRET_KEY`, включает secure cookies/SSL redirect и настройку trusted proxy header;
- `config/settings/base.py` читает `DATABASE_URL` через dj-database-url; без него fallback на локальную SQLite — **это недопустимый silent fallback на Render**;
- `config/urls.py` включает `/healthz/`, который реально делает DB `SELECT 1`; ожидаем HTTP 200 `{"status":"ok","db":true}`;
- `seed_demo` создаёт **только синтетические** книги, пользователей, детей, достижения. Обрати внимание: повторный запуск `seed_demo` **переустанавливает пароли/PIN demo-пользователей**, а `--reset` удаляет их прогресс; не добавляй автоматический reset/seed на каждый рестарт/deploy;
- `config/settings/prod.py` использует WhiteNoise `CompressedManifestStaticFilesStorage`, так что обязательно нужен корректный `collectstatic` до запуска;
- ранее пройденный `experiments/host-proof` — **не production app**.

**Подключённый Render, проверено 30.10.2026:**
- отдельный экспериментальный сервис `gustul-host-proof-h-20261030`, branch `spike/host-proof-h1-h7`, auto-deploy выключен, URL `https://gustul-host-proof-h-20261030.onrender.com`;
- отдельная бесплатная PostgreSQL `gustul-host-proof-h` (Frankfurt), expiry **2026-11-29 12:14 UTC**, без подтверждённых резервных копий;
- ещё есть отдельный `utm-curs-i-orar-2027`, **вообще не трогай его**;
- в Render **не обнаружен** отдельный сервис с реальным Gustul Cărților на момент проверки.

Рекомендуемый путь — **Render Frankfurt, новый отдельный web service и логически изолированная PostgreSQL** на бесплатном плане, если допустимо по текущим квотам. Ничего не переключай в синтетическом host-proof. Если платформа не позволяет создать ещё одну бесплатную БД, выдай `DECISION_REQUIRED` (изоляция существующей БД — только с явным approval и планом разделения), не смешивай реальные таблицы с существующим экспериментом.

## 2. Recon до первой правки

Выполни и запиши SHA:
```bash
git status --short
git remote -v
git fetch --all --prune
git rev-parse HEAD
git rev-parse origin/main
```

Если `origin` — личный fork и отстаёт, возьми именно актуальный `Slave-of-Skynet/Impact-Hackathon-2026:main` как base. Не удаляй и не сбрасывай чужие незакоммиченные файлы; используй изолированный `git worktree`.

Прочитай `AGENTS.md`, `README.md`, `pyproject.toml`, `uv.lock`, `config/settings/{base,dev,prod}.py`, `config/wsgi.py`, `config/urls.py`, `.env.example`, `apps/core/views.py`, `apps/core/management/commands/seed_demo.py`, `tests/test_demo_flow.py`, `tests/test_seed.py`, `docs/deploy-club-integration.md`, `experiments/host-proof/HOST_PROOF_REPORT.md` и Issue #34/#35.

Сначала проверь реальную доступность Render workspace/прав на развёртывание и текущие лимиты. Не называй известный синтетический хост настоящим product-host.

## 3. Выполнение — минимальный надежный вертикальный slice

### D34-01. Изолированная инфраструктура и DATABASE_URL

Выбери новые однозначно именованные Render service/DB (если free tier действительно доступен). Укажи region и срок истечения бесплатной БД, если есть. Не создавай платные услуги и не меняй другие приложения.

Проверь, что production **фактически использует PostgreSQL**, а не SQLite: движок Django DB, подключение, applied migrations и `SELECT 1`; не публикуй DSN/пароль/имя пользователя DB. Изоляция от host-proof подтверждается идентификатором ресурса в приватном журнале работ (в публичном отчёте можно назвать только безопасные имена/region, без DSN).

Если `DATABASE_URL` пуст на production, приложение должно **падать безопасно**, а не тихо создать ephemeral `db.sqlite3`. Если требуется узкий prod-only guard, согласуй изменение `config/settings/prod.py` с accounts/foundation owner, добавь целевой тест и не затронь dev/test SQLite.

### D34-02. Воспроизводимая сборка/старт

Используй locked `uv` dependency graph, Python 3.12 и Postgres optional extra. Рекомендуемый *проверяемый кандидат*, а не заранее доказанный Render recipe:

```bash
uv sync --frozen --extra postgres --no-dev
uv run --no-sync python manage.py collectstatic --noinput
uv run --no-sync python manage.py check --deploy
uv run --no-sync python manage.py migrate --noinput
uv run --no-sync gunicorn config.wsgi:application --bind 0.0.0.0:$PORT
```

**Стадии различай:** `collectstatic` — на build; `migrate` — перед сервером или в поддерживаемом безопасном release step; `gunicorn` — runtime. Не копируй весь блок в один безусловный Render command. Сверь способ установки uv и переменную `PORT` с актуальной документацией Render. При использовании shell-runner явно передай `DJANGO_SETTINGS_MODULE=config.settings.prod` **в runtime environment**. Не запускай prod на `runserver`.

Если добавляешь `scripts/start.sh`, `render.yaml`, `Dockerfile` или узкий production settings guard — делай самое маленькое воспроизводимое решение; отмечай все env-переменные, не вставляя секреты. **Не включай `seed_demo --reset` или re-seed при каждом запуске.**

### D34-03. Секреты, HTTPS, сессии

Настрой env **в Render dashboard/secret environment**, а не в GitHub Markdown:
- `DJANGO_SETTINGS_MODULE=config.settings.prod`;
- `DJANGO_SECRET_KEY` — сгенерирован безопасно, не коммитить и не менять при каждом деплое;
- `DATABASE_URL` — именно выделенный PostgreSQL;
- `DJANGO_ALLOWED_HOSTS` — точный публичный hostname;
- `DJANGO_CSRF_TRUSTED_ORIGINS` — точный HTTPS origin;
- `DEMO_PASSWORD`, `DEMO_PIN` — только для однократного безопасного seed, не публиковать.

Проверить `DEBUG=False`, `SESSION_COOKIE_SECURE=True`, `CSRF_COOKIE_SECURE=True`, `SECURE_SSL_REDIRECT`, cookie HttpOnly и корректную `SECURE_PROXY_SSL_HEADER` **только при доверенном Render proxy**. Не отключай CSRF/HTTPS ради демо. Убедись, что `/_preview/…` не доступен в prod.

Логи, PR, screenshots, curl traces и отчёт **не должны содержать** DB URL, credentials, авторизационные cookie, session IDs, PIN, plaintext one-time codes или персональные данные детей.

### D34-04. Демо-данные и реальный клубный код

Выполни `seed_demo` без `--reset` **один раз после миграций** с подготовленными безопасными demo-credentials и проверь его итоговые счетчики. Для клубного сценария выпусти одноразовый код разрешённым существующим staff workflow; **`seed_demo` кодов не создаёт**. Не добавляй в fixture постоянный plaintext код и не логируй выданный код. Секреты передаются человеку вне публичных артефактов.

Проверяй, что повторный deploy **не запускает seed и не сбрасывает PIN/пароли/страницы/ачивки**.

### D34-05. Внешний HTTPS smoke реального приложения

На фактическом публичном домене подтвердить:
1. `GET /healthz/` → 200 и `db=true`; `GET /carti/` → 200 с настоящей каталогом (а не страницей из host-proof);
2. реальный login с demo guardian, authenticated session, PIN, переход в child mode;
3. книга **Capra cu trei iezi**, 120 страниц → добавить в полку ребёнка → POST progress **35** (через реальную форму, с CSRF) → страницу 35 видит *другая самостоятельно авторизованная guardian session* после refresh;
4. без повторного выполнения записи выполнить **настоящий Render restart и отдельный redeploy** (если оба поддерживаются); после каждого проверки увидеть сохранённые 35/120 и корректный reader/child. Запиши commit/deploy ID и наблюдаемое значение до/после. Если проверен только redeploy, так и напиши: `restart NOT RUN`;
5. затем завершить книгу, проверить первое достижение, погасить выданный staff-код для своего ребёнка и увидеть club-reader/`/clubul-meu/`; запрет без членства;
6. GET `/static/…`, `/manifest.webmanifest` и service worker URL проверять по **текущему фактическому `apps/core/urls.py`**, MIME/scope в браузере;
7. при повторном входе не сломать secure cookie/CSRF, не получить `DisallowedHost`, бесконечный HTTPS redirect или неверный источник статики.

**Оракул — наблюдение persisted state + HTTP responses, а не только «Render live».** Никаких fake/mock authz/services, локального test client вместо публичного хоста или синтетического smoke.py для зачёта D34.

Если доступна только CLI/Render API, зафиксируй фактически проверенные HTTP шаги и отдельно `MANUAL_REQUIRED` для входа в браузере/Android. **Нельзя заявлять PASS на двух устройствах, пока человек их не проверил.**

### D34-06. Реальный телефон и fallback

Передай Владимиру/Денису минимальный ручной чеклист: Android на мобильном интернете и ноутбук открывают один HTTPS URL, оба логинятся независимо, ребёнок сохраняет 35, guardian видит её после refresh, затем проверяется installability PWA/manifest/offline fallback. Запиши реальные устройства, приблизительное cold-start и save latency с конкретными измерениями (не придумывай). Полный UX/PWA/3-минутный pitch остаётся в **#35**.

Подготовь **фактически проверенный локальный fallback на настоящем Django**, в отдельном `sqlite:///...` вне репозитория: `uv sync --frozen`, `migrate`, однократный безопасный `seed_demo`, `runserver` на частном ноутбуке/LAN, одна сессия ребёнка + другая родителя. Не используй прод `DATABASE_URL` для fallback; не отключай firewall глобально, не открывай LAN порт в публичный интернет. LAN/HTTP **не подтверждает HTTPS/PWA installability**. Документируй ровно то, что запущено.

## 4. Проверка перед PR

На том же commit SHA, который отправишь в GitHub:

```bash
uv sync --frozen
uv run pytest tests/test_demo_flow.py -v
uv run pytest -rs
uv run python manage.py check
uv run python manage.py makemigrations --check --dry-run
git diff --check
```

Отдельно проверь production settings/build с **синтетическими** значениями в локальном безопасном окружении (без публикации env содержимого), `collectstatic`, `check --deploy` и реальную Postgres-маршрутизацию на Render. Внимание: `manage.py` по умолчанию загружает dev settings; обычный `check` НЕ доказывает production security, поэтому явно указывай `DJANGO_SETTINGS_MODULE` при prod check.

Если Windows subprocess tests из `tests/test_review_fixes.py` снова падают по окружению, не выдавай локальный FAIL за PASS и не отключай тесты. Запиши точные 4 ошибки отдельно и проверь GitHub Ubuntu CI. Не вводи новые `skip/xfail` ради зелёной статистики.

**Зафиксируй все реальные тесты и ручные проверки:** команда, ОС/Python, tested SHA, exit code, фактические status, latency, дата/время и источник evidence. Для Render — service/deploy identifiers и ссылки на обезличенные логи. Значение `35` после redeploy подтверждай реальным повторным чтением.

## 5. Рабочая ветка, отчёт, GitHub delivery

1. Создай новую ветку `feat/issue34-real-django-deploy` от актуального canonical `main`. Не касайся других незакоммиченных изменений в рабочей папке, используй worktree.
2. Минимально добавь reproducible deployment infrastructure и исправления только P0 deployment blocker; при cross-owner prod settings shared/security change зафиксируй decision gate и запроси owner review, вместо молчаливого redesign.
3. Создай **`docs/demo-deployment.md`** со структурой:
   - current base/tested commit, deployed commit, service public hostname (если можно публично показать), DB type/region/expiry/риски;
   - exact build/start/migration/static commands и имена env без значений;
   - D34-01..06: `PASS / FAIL / NOT RUN / BLOCKED / MANUAL_REQUIRED` + URL/HTTP/DB evidence;
   - **persistence ledger**: запись до (page=35), restart/deploy IDs, чтение после, сами HTTP/DB доказательства;
   - demo seed/code workflow, отдельный fallback, тесты и CI, ограничения;
   - handoff Владимиру для #35, как повторить demo без реальных несовершеннолетних.
4. Сразу **commit + push в GitHub**, даже если remote/credentials блокируют deployment; открой PR в `Slave-of-Skynet/Impact-Hackathon-2026:main`, заголовок `deploy: real Gustul Cartilor Django HTTPS + durable database (#34)`, тело: `Refs #34`; не пишите `Closes #34` до полного внешнего acceptance.
5. В PR прикрепи ссылку на **реальный продукт** и evidence (если уже есть), GitHub Actions exact head SHA, Render logs/deploy IDs, сохрани различие `CODE_READY` vs `HOST_LIVE` vs `PERSISTENCE_VERIFIED` vs `MANUAL_REQUIRED`.
6. **Сразу попроси независимый ChatGPT project-brain review. Не мержи собственный PR, не закрывай #34 и не меняй Render-branch на main без финальной координации.** После моего merge и нового deploy реальный host должен соответствовать проверенному merged main.

## 6. Exit criteria — честный verdict

`PASS` только если реально выполнено и документировано:
- полный merged Gustul Cărților живёт на настоящем HTTPS host с production settings, настоящей PostgreSQL и статикой;
- миграции успешны, всё работает на real URLconf/templates/authz, demo credentials выданы безопасно;
- страница **35/120** сохранилась после **реального redeploy** и прочитана **в независимой session**; не нужен новый seed/ручной DB edit;
- login/child/PIN/club/achievements работают через публичный домен;
- требуемые ручные device/fallback проверки исполнены либо явно отделены как **ещё не выполненные** (при таком состоянии #34 оставь OPEN);
- полный тестовый suite и CI имеют честно задокументированные результаты;
- опубликован GitHub PR и отчёт, все секреты остались вне GitHub.

Если существенное подтверждение отсутствует, verdict **PARTIAL/BLOCKED** вместо фиктивного PASS. Ценность даже частичного результата: воспроизводимая PR-ready конфигурация, работающая локальная сборка, список *конкретных* непройденных decision gates и быстрый ручной план для команды.

### Финальный ответ исполнителя — фиксированный формат

```text
MODEL: gpt sol 6.1 / effort high
STATUS: PASS | PARTIAL | BLOCKED
MAIN_BASE_SHA: <actual>
PR_URL: <actual>
HEAD_SHA: <actual>
HOST: <HTTPS URL / NOT CREATED>
DATABASE: <PostgreSQL verified / NOT VERIFIED>
PERSISTENCE: <before / deploy ID / after / NOT RUN>
PROD_SECURITY: <check --deploy and cookies / NOT RUN>
E2E: <real remote flow and results / NOT RUN>
TESTS: <exact counts + CI link>
MANUAL_DEVICE: <observations or MANUAL_REQUIRED>
FALLBACK: <tested commands/result or NOT RUN>
COST_DECISIONS: <none / explicitly required>
NEXT_OWNER_ACTION: <exact step Vladimir/Igor/ChatGPT should take>
```

**Главное:** сделать настоящий работающий продукт с проверенной долговечностью данных. Не трать timebox на документацию, облачную оптимизацию или идеальную инфраструктуру, если 35/120 ещё не переживает реальный redeploy.
