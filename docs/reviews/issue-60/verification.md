# Issue #60 — short parent PIN verification

Base: `origin/main` `cae9d2bef5bc484477aa301ecb48c4e81dc64765` (includes #59 reliability, #62 backend and #63 reflections). Independent review and merge required. No deployment or production acceptance is claimed.

## Behavior and security boundaries

- Only an actual successful PIN POST grants an absolute 1,800-second server window. Login, GETs and mode changes do not grant or extend it. Verification binds guardian, exact database session key and keyed password/PIN fingerprint. No migration, dependency, settings or browser-storage change.
- Return is an explicit native POST+CSRF to a fixed dashboard, after active-child ownership and account PIN-lock checks. Direct adult URLs remain denied in child mode, including while verified. Blocked HTMX writes are never replayed and mode actions never emit `saved`.
- Lock revokes verification, rotates/deletes the old session and enters protected owned child mode; no safe child/PIN means full logout. Old loaded database-session snapshots cannot recreate the deleted session via `save()`. Tests exercise this sequential stale-writer scenario; this is not a multi-process load benchmark.
- Wrong PIN422 and account-wide five failures/15 minutes → five-minute429 remain. Correct PIN during lock is refused, including a lock created during hashing. Lock/logout do not erase the throttle. PIN reset still requires password re-authentication; its credential change invalidates verification on other sessions.
- Romanian status, expiry time, explicit handoff warning and Lock are visible in shared adult/child layouts. The new personal banner makes otherwise public responses private/no-store; existing private child cache headers are preserved.

## Executed checks

Commands below run on Windows/Python3.12 with the locked local environment. XML reports are local ignored `.venv/issue60-*.xml` files.

| Command | Actual result |
|---|---|
| `uv sync --frozen` on clean base | Checked 14 packages in 1ms |
| `uv run python manage.py check` | No issues, 0 silenced |
| `uv run python manage.py makemigrations --check --dry-run` | No changes detected |
| `uv run pytest tests/test_parent_session.py tests/test_child_mode.py tests/test_pin_hash_missing.py tests/test_login_throttle.py tests/test_private_no_store.py tests/test_authz.py -q --tb=short --junitxml=.venv/issue60-focused.xml` | 108 passed, 118.130s |
| `uv run pytest tests/test_parent_session.py -k 'account_wide_pin_lock or switching_trust or csrf_methods' -q --tb=short --junitxml=.venv/issue60-final-cases.xml` after final coverage additions | 3 passed, 5.570s |
| `uv run pytest tests/test_child_static_manifest.py::test_mod_copil_renders_child_home_with_manifest_urls tests/test_parent_session.py::test_controls_warning_and_private_cache_even_on_public_urls -q --tb=short --junitxml=.venv/issue60-cache.xml` after cache correction | 2 passed |
| `uv run pytest tests/test_parent_session.py tests/test_child_static_manifest.py -q --tb=short --junitxml=.venv/issue60-final-focused.xml` on final source | 37 passed, 51.075s |
| `git diff --check` | No whitespace errors |

The tests include clock29:59 valid /30:00 expired, unchanged GET timestamp, five independent authenticated clients, same/different owned children and adult reader isolation, no trust on login, foreign/deleted/malformed state, PIN/password/account changes, logout/session expiry, strict CSRF, HTMX401/403, PIN lock and stale session saves.

Baseline command before edits: `uv run pytest tests/test_review_fixes.py -q --tb=short --junitxml=.venv/issue60-main-probes.xml` → 4 passed, 4 failed, 11.062s. The four minimal-environment subprocess tests fail on this Windows host because their intentionally stripped environment omits SystemRoot and Python socket initialization raises `_overlapped` WinError10106 before application startup. They are `test_wsgi_without_settings_module_fails_closed_without_secret`, `test_wsgi_without_settings_module_starts_with_prod`, `test_wsgi_respects_explicit_settings_module`, and `test_manage_py_still_defaults_to_dev`. No foundation test was weakened for this feature.

`uv run pytest -q --tb=short --junitxml=.venv/issue60-full.xml` ran all508 cases: **499 passed, 5 failed, 4 skipped, 387.408s**. Four failures exactly match the clean-main Windows probes above. The fifth was an overly expanded cache header on the production-manifest child page; that compatibility defect was corrected and the affected cache tests then passed2/2. The full process had already imported the earlier middleware, so its original result is retained honestly. Final parent-session/manifest verification and exact-head Linux full-suite CI are recorded in the PR.

## Real local mobile browser checks

Executed through the computer-use skill's browser interface against an isolated synthetic database at localhost:8060; no production records or real credentials. Viewports 360×800, 390×844 and 430×932. This is browser viewport testing, not physical phone/PWA or five physical devices.

1. Login → Mia child → first Return shows PIN keypad. Correct PIN → dashboard with unlocked status, fixed expiry, exact warning and Lock.
2. Mia child → native Mod Părinte button → dashboard without PIN. Repeat for Alex; Alex's empty shelf remains separate from Mia's book. Displayed expiry stayed unchanged.
3. Adult Lock selecting Alex → protected Alex child mode. New tab requesting `/panou/` → `/parinte/` with PIN keypad and no quick Return. Correct PIN required again.
4. Enter Mia, press child-mode Lock → protected Mia. Direct `/panou/` again lands on PIN keypad.
5. DOM geometry: 390 viewport client/scroll width375/375; 360 viewport345/345; 430 viewport415/415. Lock button and child selector height52px; child Return52px and Lock54.2px. No horizontal overflow on measured states. Browser warning/error log empty at final inspected flow.

Evidence: [unlocked adult390](mobile-unlocked-390.png), [trusted child390](mobile-trusted-child-390.png), [locked child390](mobile-locked-child-390.png), [new-tab PIN360](mobile-pin-after-lock-360.png), [PIN after child Lock430](mobile-pin-after-child-lock-430.png).

## Risks and independent acceptance

A child given the same unlocked device during verification can return without PIN. The interface states this explicitly. TTL expiration disables the shortcut; it does not close an already-open adult session. Guardians must press Lock or logout before device handoff. A copied active session cookie remains a bearer credential; remote logout-everywhere is outside this issue. No schema/authorization bypass or blanket adult allowlist was added.

Production timeout/load and five physical devices remain #59/#35 operator QA. Independent reviewer should repeat login → child → PIN → repeated same/sibling Return, then Lock → new adult tab → PIN, using production after reviewed merge. Verify 29:59/30:00 with the automated fake-clock test rather than waiting during a live demo. Coordinate shared-layout integration with PWA PR#71 and ratings UI PR#70; neither open branch was overwritten.
