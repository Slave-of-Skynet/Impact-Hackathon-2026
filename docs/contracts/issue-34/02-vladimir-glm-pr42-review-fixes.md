# Issue #34 / PR #42 — исправить замечания независимого review (R1–R3)

**Исполнитель:** Владимир в Antigravity.  
**Модель:** **GLM 5.3 Flash**, **effort: max**. **Не переключать модель или effort.**  
**Независимый reviewer после push:** ChatGPT project brain (НЕ GLM).  
**Репозиторий:** https://github.com/Slave-of-Skynet/Impact-Hackathon-2026  
**PR для исправления:** https://github.com/Slave-of-Skynet/Impact-Hackathon-2026/pull/42  
**Issue:** https://github.com/Slave-of-Skynet/Impact-Hackathon-2026/issues/34  
**Review:** https://github.com/Slave-of-Skynet/Impact-Hackathon-2026/pull/42#pullrequestreview-5719505272  
**Проверенный базовый HEAD PR #42 на 2026-10-31:** `40f0d59ed48e175d407fc3d3b50bdde4f9872095`. **Перед изменениями перепроверь актуальный remote HEAD; он мог обновиться.**  
**Текущий статус:** CODE_READY / CI 374 passed, 4 skipped на run https://github.com/Slave-of-Skynet/Impact-Hackathon-2026/actions/runs/41139884310. HOST_LIVE и PERSISTENCE_VERIFIED — **NOT RUN**.

## 0. Твоя миссия — узкий fix, а не новый deployment task

Исправь **в существующей рабочей ветке PR #42** только два обязательных замечания independent review и одно уточнение документации. Затем запусти проверки, **немедленно commit + push в ту же ветку `feat/issue34-real-django-deploy`**, обнови PR #42 результатами и запроси повторное независимое review ChatGPT.

**Не открывай новый PR для исправлений**, не создавай второй production Blueprint, не мержи PR #42 самостоятельно, не закрывай #34. Не создавай облачные ресурсы, не изменяй Render Dashboard: пользователь Владимир отдельно принимает инфраструктурное решение после ревью. Секреты, коды и DSN не печатать.

Приоритет — быстро получить review-ready исправление. **Не меняй** `config/settings/prod.py`, общий Django-контракт, модели, миграции, бизнес-логику, `tests/test_foundation.py`, `tests/test_review_fixes.py` или CI без нового конкретного дефекта, который объяснит необходимость такой правки. Старые четыре Windows subprocess failures не являются целью задачи.

## 1. Перед правками — проверить live state

В используемой рабочей папке:
```bash
git status --short
git remote -v
git fetch --all --prune
git rev-parse HEAD
git rev-parse origin/main
git branch --show-current
```

Если локальный origin — fork/ветка отстаёт, получи истинный HEAD PR #42 через `gh pr view 42 --repo Slave-of-Skynet/Impact-Hackathon-2026 --json headRefOid,headRefName` или `git fetch https://github.com/Slave-of-Skynet/Impact-Hackathon-2026.git refs/pull/42/head`. **Не затирай локальные незакоммиченные изменения** — используй отдельный `git worktree`, если необходимо. Не создавай новую ветку от `main`: нужно обновить **именно существующий PR #42**, сохранив его код и историю.

Прочитай фактические `render.yaml`, `docs/demo-deployment.md` (§§3,4,7,10,11), полный review PR #42 и `AGENTS.md`. Если замечание уже исправлено новым HEAD, не переделывай его второй раз; проверь критерии и задокументируй.

## 2. R1 — безопасность Render PostgreSQL / P1

В корневом `render.yaml`, **именно у записи `databases: - name: gustul-cartilor-db`**, добавь `ipAllowList: []`:

```yaml
databases:
  - name: gustul-cartilor-db
    databaseName: gustul_cartilor
    region: frankfurt
    plan: free
    ipAllowList: []
```

Порядок ключей не принципиален. **Не добавляй** `ipAllowList` в web service, не создавай `0.0.0.0/0`, не заменяй `DATABASE_URL` на внешний адрес. Поддерживается официальной документацией Render Blueprint:
- https://render.com/docs/blueprint-spec — PostgreSQL `ipAllowList: []` означает только внутренние подключения; отсутствие поля означает разрешение внешних попыток с любого IP при наличии credentials.
- https://render.com/docs/postgresql-creating-connecting — Render service и DB в одном регионе могут работать по **internal** connection URL даже с запрещёнными внешними подключениями.

В `docs/demo-deployment.md` (разделы 3, 4, 5 и 7) зафиксируй:
1. PostgreSQL **external access deny-by-default**, внутреннее соединение Render service ↔ DB через Blueprint `DATABASE_URL` должно оставаться работоспособным.
2. Одноразовый `seed_demo` с Windows-ноутбука возможен через **external database URL** только после **временного allowlist точного внешнего IPv4/IPv6/CIDR оператора** в Render Dashboard. После seed убрать этот IP, убедиться, что allowlist вновь пуст.
3. Никогда не публиковать external DB URL, секреты, пароли, PIN, одноразовые клубные коды и session cookies в PR/логах/чатах. Не оставлять открытую базу ради удобства демо.
4. Объяснить, что это **конфигурация для будущего provisioning**, а **не свидетельство фактически закрытого IP доступа**: service/DB ещё не созданы.

Проверь `render.yaml` на корректность YAML и совместимость с актуальным официальным Blueprint schema. Не добавляй новую зависимость для этого, если достаточно уже доступных инструментов; вручную проверь отступы, тип `[]` и положение ключа. Если используешь Render Blueprint Validation, не подтверждай provisioning/создание ресурсов.

**R1 PASS**, если в PR diff есть именно `databases[].ipAllowList: []`, docs описывают временное исключение для seed и окончательное закрытие, без обхода внутренней DB.

## 3. R2 — реально работоспособный fallback на Windows / P1

Сейчас `docs/demo-deployment.md` (раздел 10) ошибочно задаёт `DATABASE_URL` только для `migrate`/`seed_demo`, а для `runserver` — нет. Это может запустить сервер **с другой локальной БД** (репозиторный `db.sqlite3` вместо подготовленной вне репозитория). Там же нет `mkdir` для каталога SQLite и bind на `127.0.0.1` исключает телефон в LAN.

**Исправь `10`, предложив проверяемый Windows PowerShell сценарий** для владельца:
- явно создаёт каталог в `$env:LOCALAPPDATA` **вне репозитория**;
- устанавливает один `$env:DATABASE_URL` в **одной PowerShell-сессии** до `migrate`, `seed_demo` и `runserver`, с абсолютным Windows-путём в формате, который действительно поддерживает установленный `dj-database-url`;
- явно устанавливает `$env:DJANGO_SETTINGS_MODULE = 'config.settings.dev'`; **никогда не использует продовый DATABASE_URL, PostgreSQL или `config.settings.prod`**;
- использует только синтетические локальные пароли/PIN; не вставляет их в скрипт или Markdown в виде реальных значений;
- запускает `uv sync --frozen`, `migrate`, `seed_demo` **без `--reset`**, затем `runserver`, **не изменяя `DATABASE_URL`**;
- проверяет `DATABASES['default']['NAME']` перед/после и убеждается, что это одна и та же вне-репозиторная SQLite;
- не объявляет локальный сценарий `TESTED`, если реально не запускал.

**Раздели два режима:**
- **Laptop-only:** `runserver 127.0.0.1:8000` — две независимые browser sessions на одном ПК. Это нормальный fallback, но НЕ телефонный LAN.
- **Phone + laptop LAN (optional):** binding к частному IPv4 ноутбука (`<LAN_IP>:8000` или `0.0.0.0:8000`), `DJANGO_ALLOWED_HOSTS` с реальным LAN IP и использование `http://<LAN_IP>:8000` на телефоне в той же доверенной сети. Не отключай firewall глобально, не пробрасывай порт наружу, при необходимости разрешай только отдельный TCP порт для профиля Private. **HTTP LAN не доказывает HTTPS/PWA installability**; `Service Worker` на обычном HTTP LAN IP может быть недоступен.

PowerShell пример должен быть **копируемым и цельным**; не оставляй смешанные Bash-prefixed environment assignments как основную инструкцию для Windows. Если предлагаешь отдельную Bash версию, чётко пометь её как Bash-only.

**Проверить безопасно:** при возможности запусти локально smoke на **новом disposable внешнем SQLite файле**, выполни `migrate` → `seed_demo` → `/healthz/`/`/carti/` через Django dev, затем проверь тот же `DATABASES['default']['NAME']` и синтетические записи в той же БД. Не трогай существующий пользовательский SQLite, не запускай `--reset`. Если физический телефон/LAN не участвовал, скажи `LAN NOT RUN`; не притворяйся, что это выполнено.

**R2 PASS**, если все процессы смотрят в одну внешнюю SQLite, каталоги создаются заранее, две независимые сессии возможны на localhost, а телефонный LAN-план отличается от localhost; статусы реальной проверки честны.

## 4. R3 — формулировки Render и CI (documentation accuracy)

В `docs/demo-deployment.md` (раздел 3) исправь чрезмерно категоричное утверждение **«новый workspace = guaranteed zero cost / гарантированно свободный бесплатный quota»**:

- новый отдельный Hobby workspace — **предпочтительный кандидат**, но **не подтверждённая доступность в аккаунте пользователя**; его создание может запрашивать payment method / подтверждение billing;
- **решение принимает Владимир**, только после проверки в своём Render UI фактического плана, допустимости второй бесплатной PostgreSQL и отсутствия потенциальных затрат;
- не создавать новые workspace/DB/платные сервисы агентом без явного owner approval.

Авторитетный источник: https://render.com/docs/team-members (создание workspace, до пяти Hobby workspaces, step payment method); https://render.com/docs/free (текущие ограничения бесплатных ресурсов). Не изобретай точную цену или гарантированную бесплатность.

В `docs/demo-deployment.md` (раздел 11) добавь подтверждённый **pre-fix** GitHub CI snapshot:
- HEAD `40f0d59ed48e175d407fc3d3b50bdde4f9872095`;
- Actions run https://github.com/Slave-of-Skynet/Impact-Hackathon-2026/actions/runs/41139884310;
- **374 passed, 4 skipped, 0 failed** на Ubuntu.

После собственного push **обнови `11` или PR description** до фактического нового HEAD с реальным результатом нового CI. Не выдавай старый CI за CI нового HEAD.

## 5. Проверки после изменений

Минимально:
```bash
git diff --check
uv sync --frozen --extra postgres
uv run pytest tests/test_prod_settings.py tests/test_foundation.py tests/test_review_fixes.py -q
uv run python manage.py check
uv run python manage.py makemigrations --check --dry-run
uv run pytest -rs
```

Если Windows subprocess-сбои остались (исторически 4 в `tests/test_review_fixes.py`), зафиксируй реальные exit code и точный traceback, **не добавляй skips и не называй local full suite PASS**. Новый CI на Ubuntu должен пройти; смотри workflow runs exact new SHA, различай тесты и optional skips.

Для документации/Blueprint проверь отдельно:
- новая `render.yaml` DB allowlist **точно** `[]`;
- `docs/demo-deployment.md` содержит одну PowerShell-сессию/один DB path, private-LAN условия и честные `NOT RUN`;
- нет изменений к `uv.lock`, моделям, миграциям, authz и cloud-resource state;
- в staged diff отсутствуют `.env`, секреты, `db.sqlite3`, `staticfiles/`, IDE/Antigravity/Spec Kit артефакты.

Ни одна из проверок локального Django не является проверкой **живого** Render PostgreSQL/HTTPS — это остаётся `NOT RUN`.

## 6. Сразу отправить на GitHub и запросить re-review

1. В существующей ветке `feat/issue34-real-django-deploy` исправь `render.yaml` и `docs/demo-deployment.md`. Добавь тест/документ только если действительно нужен; избегай изменения других файлов.
2. `git diff --check`, прогоны из `5`, `git status --short`, затем **commit и push немедленно**. Например commit: `fix(deploy): restrict Postgres external access and repair Windows fallback (#34)`.
3. **Не создавай новый PR**: измени действующий https://github.com/Slave-of-Skynet/Impact-Hackathon-2026/pull/42.
4. В PR comment или description укажи exact HEAD, закрытые R1/R2/R3, какие команды действительно выполнены, старые известные Windows failures и ссылку на новый Actions run **для точного нового SHA**. Если CI не успевает завершиться, поставь `CI PENDING` вместо выдуманного PASS, но commit/push не откладывай.
5. Прямо попроси **ChatGPT project brain** провести независимый re-review этого HEAD. Самостоятельно **не approve, не merge, не close #34**.
6. Не создавай Render workspace, service или DB как часть этой правки. Итоговая цель этой итерации — **REVIEW_READY CODE**, а не фиктивный `HOST_LIVE`.

## 7. Финальный формат ответа агента

```text
MODEL: GLM 5.3 Flash / effort max
PR_URL: https://github.com/Slave-of-Skynet/Impact-Hackathon-2026/pull/42
NEW_HEAD_SHA: <exact GitHub HEAD>
R1_POSTGRES_ALLOWLIST: PASS / BLOCKED (explain)
R2_WINDOWS_FALLBACK: PASS / BLOCKED (explain)
R2_ACTUALLY_EXECUTED: <commands and DB-path evidence / NOT RUN>
R2_PHYSICAL_LAN: PASS / NOT RUN
R3_RENDER_COST_AND_CI_DOCS: PASS / BLOCKED
FILES_CHANGED: <exact>
LOCAL_TESTS: <actual counts, failures and skips>
GITHUB_CI: <exact new-head run URL + conclusion / PENDING>
HOST_LIVE: NOT RUN
PERSISTENCE_VERIFIED: NOT RUN
SECRETS_PUBLISHED: NO
NEXT: independent ChatGPT review; Владимир decides Render provisioning afterwards
```

**Не анализируй всё приложение заново. Исправь R1 + R2 + R3, подтверди diff/CI, запушь в PR #42.**
