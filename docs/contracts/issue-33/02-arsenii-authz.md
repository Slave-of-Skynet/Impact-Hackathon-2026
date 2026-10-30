# ISSUE-33 / EXECUTOR-02 — Arsenii: independent identity, child-mode and authorization verification

**Executor:** Arsenii (Claude Code). **Model: claude sonnet 5.5; effort: high**. Escalation for a demonstrated authz/concurrency root-cause blocker: **claude opus 5.5; effort: xhigh**.
**Parent issue:** https://github.com/Slave-of-Skynet/Impact-Hackathon-2026/issues/33
**Canonical acceptance:** docs/contracts/issue-33/00-acceptance.md
**Mode:** independent focused verifier / narrow accounts fixes only, NOT a second E2E implementation owner.
**Deliverable:** docs/reviews/issue-33-authz.md on a dedicated review branch + GitHub PR, or a minimal accounts bug-fix PR if objectively needed.

## Agent prompt (copy in full)

You are an independent verifier of the authentication, authorization and child-mode boundaries involved in the #33 integrated journey. Igor implements tests/test_demo_flow.py; **you must not modify that file** and must not duplicate his end-to-end feature work. Preserve the app's existing security rules. Your job is to find actual blockers or provide reproducible PASS evidence on the latest integrated repository state.

### 0. Read actual GitHub state

Fetch the latest origin/main, capture its SHA, inspect Issue #33 and Igor's PR if available, then read the canonical acceptance contract 00-acceptance.md. Inspect:
- apps/accounts/authz.py, middleware.py, throttle.py, forms.py, views.py, urls.py;
- apps/core/child_views.py and apps/core/urls.py;
- config/urls.py (read only), club.views.redeem_code (read only);
- tests/test_authz.py, test_child_mode.py, test_login_throttle.py, test_family.py, test_account_dashboard.py;
- specs/001-reading-diary-mvp/contracts/authorization.md.

Use current real code/commits, not earlier plan prose, when defining expected behavior. Do not claim tests run unless they were actually run.

### 1. Required proof

A. Verify standard login POST and family ownership:
- one adult account can create a private own child (Reader relationship), set PIN with valid guardian password, enter child mode by POST to the own child URL;
- foreign child's report and child-mode start attempts fail without information leaks;
- adult reader and child Reader remain distinct;
- new guardian sessions can read *their* child report while child-mode sessions may not view adult routes.

B. Verify session-mode boundaries:
- child mode GET /copil/ works with a valid own child; /panou/, /familie/, /club/cod/, /admin/ are denied by default;
- normal forbidden requests redirect 302 to /parinte/; HTMX requests return 403 and empty body;
- modified/deleted/foreign active_child session does not silently fall back to adult;
- correct PIN exits child mode, wrong PIN counts and is rejected, locked PIN cannot be bypassed by correct PIN, POST logout provides safe session termination;
- all forms changing identity/family/PIN remain POST + CSRF protected.

C. Verify expired/anonymous HTMX behavior:
- signed-out GET/post to protected child+adult resources responds by the actual authz contract (normal login redirect vs HTMX 401 + HX-Redirect);
- expired HTMX progress request produces no saved trigger, no successful partial and no stored event;
- token or session data never trusts reader/guardian supplied by a browser;
- stale Session data cannot expose another guardian's child.

D. Club target boundary cross-check (READ ONLY in Igor-owned module):
- redeem target "self" means actor's own adult reader;
- a child target is own ChildProfile public_id, not arbitrary Reader UUID or another guardian's child;
- child mode is denied by middleware;
- throttle is per-account and existing residual concurrent invalid-attempt limitation remains documented, not spuriously fixed or marked strict.

### 2. Test method

Prefer rerunning existing real Django HTTP tests, then add **small accounts-owned regression tests only if a concrete hole is uncovered**. Do not change tests into service mocks to make them pass. Check normal vs HTMX HTTP status, response headers and persisted DB state. For any found defect, write a minimal test that fails on current behavior before fixing; propose the smallest scoped fix. Avoid edits to apps/library, apps/club, shared templates, config/settings, models/migrations or tests/test_demo_flow.py without explicit owner decision.

Suggested checks (adapt only if repository commands differ):
- uv sync --frozen
- uv run pytest tests/test_authz.py tests/test_child_mode.py tests/test_login_throttle.py tests/test_family.py tests/test_account_dashboard.py -v
- uv run pytest
- uv run python manage.py check
- uv run python manage.py makemigrations --check --dry-run
- git diff --check

Confirm whether focused checks and full suite pass on *the same commit* Igor will integrate (review Igor's PR final SHA when published). A clean prior main pass is only baseline proof, not automatically E33 acceptance.

### 3. Report and GitHub handoff

Prepare docs/reviews/issue-33-authz.md with sections: base/head SHA, tested environment, test commands and exact counts, per-boundary PASS/FAIL/NOT RUN matrix, detailed smallest reproduction of every failure, and the specific accountable owner. Clearly distinguish code review from executed tests.

Push the report to GitHub immediately on branch review/issue33-authz (or another unoccupied review branch), open a PR referencing #33, and ask for independent ChatGPT project-brain review. If you introduce code changes, those must be explicit in a small accounts-only bug-fix PR; request Igor to rerun all E2E checks after integration. You must not self-merge.

### 4. Decision rules

- PASS: identity, child authorization, CSRF, PIN, session and HTMX refusal actually tested against final integrated candidate; no P0 defect.
- FAIL: reproducible access cross-over, false success or missing refusal; identify whether accounts module needs a separate fix.
- NOT RUN: any unchecked branch; cannot be converted to PASS based on source inspection.

Your final response must include branch/PR link, SHA, test evidence, findings and actionable handoff for Igor. Do not spend time implementing recommendations, a feed, a leaderboard, production policies or work for #34/#35.
