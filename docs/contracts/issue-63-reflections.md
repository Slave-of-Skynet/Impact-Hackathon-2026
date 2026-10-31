# Issue #63 — private book reflections

Fixes #63, Refs #35. Decision published before implementation:
[schema and route gate](https://github.com/Slave-of-Skynet/Impact-Hackathon-2026/issues/63#issuecomment-6541575661).

## Product interpretation and scope

The [16 original fragments](issue-63-question-source.txt) are preserved verbatim.
Source 1+2 is one atomic prompt, giving **15 semantic questions**. This is the
task's working MVP interpretation, **not confirmed owner clarification**. Other
text is unchanged. `reflection_questions.py` contains the immutable v1 source,
IDs (1,3..16) and versioned pool. A future split/version requires deliberate
code/constraint migration, not editing an already published question in place.

Each new set uses server `random.sample(pool, 4)` then `shuffle`; rows persist
question IDs and positions. **GET never creates or redraws a set.** Completion
and ratings are independent and never require answers. Finished books have a
link from both the full entry page and the successful HTMX progress partial.

Conservative MVP: one set per shelf entry; no attempt history. `Alte întrebări`
works only when every saved answer is empty. After any nonempty save it is
disabled by the server, even for stale tabs. The UI warns to copy unsaved text
before requesting other questions. Answers can be edited, but an all-blank save
is rejected; there is no clear-all/delete/reset endpoint. This intentionally
prevents deleting saved work to bypass the redraw guard.

## Storage and migration

`library.0002_book_reflections` adds two new tables only:

- `BookReflectionSet`: OneToOne ShelfEntry, pool_version=1, positive revision,
  created_at/updated_at. Unique entry prevents duplicate sets.
- `BookReflectionAnswer`: set FK, position1..4, v1 question_id, text<=2000 chars.
  Unique(set, position) and unique(set, question_id), database range/pool/length
  checks. Four rows are created atomically by the service. DB uniqueness and the
  position range enforce at most four; the service enforces exactly four.

No existing row/column is changed, no backfill or seed ratings/answers. Existing
BookVM, ShelfEntryVM and ProgressEvent stay unchanged. PostgreSQL uses ordinary
transactional DDL; no production DB command is part of this change. Rollback
drops the **new reflection data**, preserving preexisting diary data. Snapshot
reflection data before any downgrade. Child/entry deletion uses existing cascade
semantics. New answer text is not exposed in admin, logs or public catalogs.
Sensitive POST fields are marked for Django exception reporting; private answers
are never deliberately included in exception messages or analytics.

## Routes, forms and status contract

All entry UUIDs are resolved through current_reader and get_entry_for_reader.
Adult mode acts on self; child mode on revalidated active child. No reader or
child ID is accepted from a form. Guardian read access is exclusively the existing
owned-child report, never authority to edit as that child. Only these three route
names enter CHILD_ALLOWED; untrusted adult routes and PIN remain gated.

| Name | Path suffix under `/raft/<entry>/` | Method / form |
|---|---|---|
| book_reflection | `ganduri/` | GET; no domain writes; unfinished entry shows explanatory state |
| start_reflection | `ganduri/set/` | POST; CSRF + revision (0 first time, current revision for unanswered redraw) |
| save_reflection | `ganduri/salveaza/` | POST; CSRF + revision + question_1..4 IDs + answer_1..4 text |

Strict forms require every listed field exactly once; reject missing, duplicate,
nested, extra/5th fields and unexpected IDs. Blank individual answers are allowed
if at least one answer is nonblank. Each field is capped at2000 characters before
trimming; text is escaped by Django, not rendered as HTML. Existing saved question
order is checked under lock; client question IDs never choose a different set.

Normal successful POST redirects to book_reflection (PRG); a server message is
queued only after commit. HTMX success is204 empty + HX-Redirect to the same page
+ HX-Trigger:saved. Native forms are the default, independent of JavaScript.
422 re-renders a full page or, for HTMX, `library/_reflection_form.html` with the
bound text. 409 stale revision also retains text under its original canonical
prompt, tells the reader to copy it before reloading, and changes nothing. No
automatic conflict overwrite. Current native UI shows409 directly; any future
HTMX enhancement must not enable global409 swapping. Existing422 policy applies.
No prior success notice is displayed on a rejected422/409 response.

Anonymous/expired: normal302 login; HTMX401 empty + HX-Redirect. Foreign/unknown
entry404, guardian-on-child write404, child adult route normal302 PIN/HTMX403.
Missing CSRF403; GET mutation405. Unfinished write422. DB lock503 unsaved with
Retry-After:1; unexpected DB error rolls back and propagates500, never saved.
Private pages and rendered validation/conflict responses are private,no-store.

Writes lock Reader then entry then reflection set. Revision comparison and all
four updates/redraw happen atomically. Simultaneous creates/saves have one
successful writer and a409 loser; retry after uncertain success may return409
and should be resolved by a read, not blindly retried. No progress request_id,
achievement or page event is added/changed by reflection services.

## Additive template context and report

The new adult/child reflection page and shared form receive entry (unchanged
ShelfEntryVM), reflection (private set or None), reflection_form (bound Django
form), start_form, can_reflect, has_answers, reflection_error, is_child_reader,
and reflection_messages. question_fields supplies ordered canonical labels,
hidden question ID fields and answer BoundFields. No personal text enters URLs.

Owned-child report receives `book_reflections`: list of
`{book_title, updated_at, questions: [{position, question_id, question, answer}]}`.
The helper takes the owned child's reader **after** get_child_for_guardian and
uses two queries regardless of book count (joined set/book + prefetched answers).
The report section contains no textareas, save forms or private edit links.

## Parallel integration with ratings #62 / PR #66

This branch starts from main374fcb5 while ratings PR66 is open. New tables are
independent of ShelfEntry.rating and public aggregation. Do not overwrite either
migration or either feature's allowlist names. Before the second PR merges,
rebase on the first and resolve Django's two library migration leaves: regenerate
the second migration's number/dependency or add a reviewed merge migration.
Also restore **all original migration leaf nodes** in schema-migration tests,
rather than leaving the test database at a hardcoded earlier migration. Run the
combined ratings/reflection tests and full CI after integration. Until then,
ratings compatibility is structural, not a claimed combined-suite PASS.

No PIN60 behavior, palette61 tokens, dependencies, secrets or deployment config
are changed. Independent ChatGPT review/merge and deployed Render SHA plus live
acceptance remain required before claiming availability to users.
