# Backend contract for Denis #62B

Refs #62. Backend first; Denis owns visible star controls, aggregate rendering,
accessibility and phone validation in a follow-up PR. No palette/template edits.
Decision published before implementation in
[issue #62](https://github.com/Slave-of-Skynet/Impact-Hackathon-2026/issues/62#issuecomment-6541338827).

## Schema and ownership

`library.0002_shelfentry_rating` adds nullable SmallIntegerField `rating` to
ShelfEntry. Existing rows get NULL; no rows/history are deleted, no backfill or
fake ratings. DB checks enforce NULL or 1..5, and non-NULL only when finished.
Existing unique(reader, book) provides one vote per reader/book without a new
table. PostgreSQL migration is transactional; SQLite may rebuild the table for
constraints. Production deployment/migration remains independently reviewed;
no production database commands were run. Reversing drops the new ratings,
preserving prior diary data. BookVM/ShelfEntryVM remain unchanged.

Reader comes only from accounts.authz.current_reader: adult self or owned active
child. An adult viewing a child's report cannot rate on that child's behalf.
Submitted reader/guardian/child fields are ignored. Only `rate_book` is added to
CHILD_ALLOWED, with its active-child revalidation intact. No PIN implementation
changes; coordinate the single allowlist line with #60 when it lands.

## Endpoint

`reverse('rate_book', kwargs={'entry': entry.public_id})` is
`POST /raft/<entry UUID>/evaluare/`. Submit `rating=1` through `5` plus CSRF.
No request_id: atomic replacement, same value repeated has the same effect.
Different concurrent values serialize, last commit wins; no new entry, progress
event or achievement. Owner lookup precedes input validation in HTTP requests.

| Result | Normal form | HTMX (`HX-Request: true`) |
|---|---|---|
| Commit | 302 PRG to shelf_entry | 204 empty + HX-Redirect to shelf_entry + HX-Trigger: saved |
| Invalid value | 422 text: `Alege o evaluare între 1 și 5.` | same, no saved/redirect header |
| Own unfinished entry | 422 text: `Poți evalua doar o carte terminată.` | same, no saved/redirect header |
| Foreign/unknown entry | 404 | 404 |
| Anonymous/expired | 302 login | 401 empty + login HX-Redirect |
| Invalid CSRF | 403 | 403 |
| GET | 405, no write | 405 |
| Lock timeout | 503 unsaved + Retry-After: 1 | same, no saved header |
| Unexpected DB error | 500, transaction rollback | no saved header |

Input is strict: missing/blank, decimal, NaN, boolean, whitespace, signs,
leading zeros and non-ASCII digits are rejected. There is no clear-rating action.
422 is UTF-8 plain text, an explicit exception to progress's HTML partial rule.
A native form works without JS; an HTMX enhancement must show 422 as text in an
error region, keep selection/progress unchanged, and never show saved on error.
Do not swap a rating error into the progress form. Success navigates to the owner
entry and reads stored data. Rating successes and validation/lock responses use
no-store.

## Additive context

Catalog, book_detail and my_shelf (adult/child variants) receive:

```python
book_ratings = {
    book_public_uuid: {"average": 4.333333333333333, "count": 3, "message": ""},
    other_book_uuid: {"average": None, "count": None, "message": "Nu sunt suficiente evaluări"},
}
personal_ratings = {book_public_uuid: 5}  # ONLY current reader; missing = unrated
```

Keys are UUID objects matching BookVM.public_id, not strings or database PKs.
Detail includes only its book, catalog its filtered active books, shelf its owned
books. A template mapping lookup helper can be added by #62B without changing
frozen VMs. Format visible average to one decimal and provide accessible text.

Only genuine non-NULL finished ratings contribute to Avg/Count. Both mean and
count are suppressed below three distinct readers (uniqueness guarantees one
vote per reader/book). No raw low-volume aggregate or identities enter context.
NULL is never a fabricated five stars. Personal maps are empty for anonymous
visitors and never include guardian-viewed children. Authenticated catalog/detail
are no-store because signed-in context can contain personal values. Anonymous
metadata retains its existing public cache policy. Preserve that distinction.
This population threshold does not prevent statistical inference from repeated
observations once an aggregate is public; no stronger privacy claim is made.

Owner shelf_entry and its progress partial additionally receive:

```python
personal_rating = 5  # int 1..5 or None
can_rate = True     # entry.status == 'finished'
```

Show the form only when can_rate, select the saved value, use native accessible
inputs and Romanian labels. Guardian child reports remain read-only. This backend
PR supplies the context; stars/controls/mobile screenshots remain Denis #62B.
Aggregate and owner queries are batched, independent of the number of books.

## Local UI integration scenario

Migrate a local/test database normally. Sign in, enter an owned child's mode,
add and finish a book with the reading form. POST rating=4 with CSRF; follow the
redirect, verify personal_rating=4. Change to 2, reload, sign in independently as
the same guardian and enter the same child: still 2. Adult-mode POST for that child
returns 404. Three synthetic finished readers' votes 2,4,5 yield 11/3 and count 3;
two yield neither average nor count. Never seed/reset/stress production.
