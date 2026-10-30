# Contract: routes, forms and template context (proposal)

**Style (single canonical contract):** server-rendered Django views. Mutations are HTML `POST` forms, enhanced with HTMX (`hx-post`) that swaps a partial on success. **No JSON API in P0.** Each view below states the template context it guarantees, so UI work can start against stubs before domain code exists.

Common rules for every mutating route:

- CSRF required; HTMX sends the token via `hx-headers` on `<body>`.
- Authorization through `accounts/authz.py` only (see [authorization.md](./authorization.md)). A foreign or unknown `public_id` → **404** with no hint of existence.
- Validation errors → **422** + the same partial re-rendered with messages (HTMX swaps it). Full-page POSTs re-render the page with errors.
- Server or network errors → HTMX `htmx:responseError` / `htmx:sendError` handler shows the "Nu s-a salvat" toast; the UI never switches to the saved state without a 2xx response.
- `request_id` = hidden UUID input generated at render time; regenerated after each successful save.

Mode legend: **pub** = anonymous OK · **adult** = signed-in, adult mode · **child** = child mode only · **staff** = `is_staff` in adult mode.

## Page map

| # | Path | Name | Mode | Purpose |
|---|---|---|---|---|
| 1 | `/` | `home` | pub | Landing: what the app is, sign up / sign in, about the club |
| 2 | `/carti/` | `catalog` | pub, adult, child | Catalog list (filters: age band, genre). Child mode renders the child template |
| 3 | `/carti/<book>/` | `book_detail` | pub, adult, child | Book metadata + "add to shelf" |
| 4 | `/cont/inregistrare/` | `signup` | pub | Adult sign-up |
| 5 | `/cont/intrare/`, `/cont/iesire/` | `login`, `logout` | pub / adult | Django auth views |
| 6 | `/panou/` | `adult_dashboard` | adult | Own shelf + stats; one card per child with stats |
| 7 | `/familie/` | `family` | adult | List / create / rename / delete children; set PIN |
| 8 | `/familie/<child>/` | `child_report` | adult | One child's shelf, progress, achievements |
| 9 | `/familie/<child>/mod-copil/` | `child_mode_start` | adult (POST) | Enter child mode for this child |
| 10 | `/club/cod/` | `redeem_code` | adult | Redeem membership code for self or a child |
| 11 | `/raft/` | `my_shelf` | adult, child | Current reader's shelf (adult or active child) |
| 12 | `/raft/<entry>/` | `shelf_entry` | adult, child | Progress screen for one book |
| 13 | `/realizari/` | `achievements` | adult, child | Earned + locked achievements of the current reader |
| 14 | `/clubul-meu/` | `club_corner` | adult, child — **member only** | Club activities |
| 15 | `/copil/` | `child_home` | child | Child home: mascot, current book, big buttons |
| 16 | `/parinte/` | `pin_gate` | child → adult | "Ask a parent" PIN screen; exit child mode |
| 17 | `/admin/` | Django admin | staff | Catalog, membership codes, activation/revocation |
| 18 | `/offline/`, `/manifest.webmanifest`, `/sw.js` | PWA | pub | Offline page, manifest, service worker (served at root scope) |

"Current reader" = the adult's own reader in adult mode, or the active child's reader in child mode. **Routes 11–14 never take a reader ID from the URL or form**; a guardian views a child's data only via route 8 (read-only in P0).

## Mutations

| Route | Method | Form fields (validation) | Authz | Success | Errors | Idempotency |
|---|---|---|---|---|---|---|
| `signup` | POST | `email` (valid, unique), `password` (Django validators), `display_name` (1–40) | pub | redirect `adult_dashboard` | 422 | email unique |
| `family` create | POST `/familie/` | `nickname` 2–20, `age_band` enum, `avatar` enum | adult | redirect `family` | 422; 6-child limit → 422 | none needed (double submit creates two — UI disables button; acceptable) |
| `family` rename/delete | POST `/familie/<child>/editeaza/`, `/familie/<child>/sterge/` | nickname / confirm | adult + owns child | redirect | 404 foreign | delete is naturally idempotent (2nd → 404) |
| PIN set | POST `/familie/pin/` | `pin` 4–6 digits ×2, `password` (re-auth) | adult | redirect | 422 | — |
| `child_mode_start` | POST | — | adult + owns child + PIN set | session `mode=child`, `active_child=<id>`; redirect `child_home` | 404 foreign; redirect PIN setup | repeat = same state |
| `pin_gate` | POST | `pin` | session in child mode | clears child mode; redirect `adult_dashboard` | 422 wrong; 429 locked | — |
| add to shelf | POST `/carti/<book>/adauga/` | — | adult/child, current reader | 200 partial "Pe raftul tău" (HTMX) or redirect `shelf_entry` | 404 unknown/inactive book | `get_or_create` |
| record progress | POST `/raft/<entry>/progres/` | `page` int, `request_id` UUID | entry.reader == current reader | 200 partial: progress bar, mascot line, new achievement toasts | 422 out of range / finished; 404 foreign | `(reader, request_id)` unique → replay returns same result, `replayed=true`, no new grants |
| finish book | POST `/raft/<entry>/terminat/` | `request_id` | same | 200 partial "Felicitări" + grants | 422 already finished (replay with same `request_id` → 200 replay) | same |
| `redeem_code` | POST | `code` (normalized: upper, strip spaces/dashes), `reader` = `self` or a child `public_id` from **the actor's own children list** | adult; rate limit 5 failures / 15 min / account | redirect with "Membru al clubului până la …" | one generic 422 "Cod invalid sau expirat"; 429 | single-use conditional update |

There is deliberately **no** route that creates achievement grants, memberships (outside admin/redeem), or accepts `reader`/`guardian`/`is_member` from the client except the constrained `reader` choice in `redeem_code`.

## Template context contracts (for parallel UI work)

| Template | Context keys (types) |
|---|---|
| `child/home.html` | `child` {nickname, avatar}, `current_entry` (ShelfEntryVM \| None), `mascot` MascotLine, `is_member` bool, `recent_grants` [GrantVM] |
| `child/shelf_entry.html` + partial `child/_progress.html` | `entry` ShelfEntryVM, `request_id` UUID, `mascot` MascotLine, `new_grants` [GrantVM], `errors` [str] |
| `adult/dashboard.html` | `me` {display_name}, `my_stats` StatsVM \| None, `children` [{child ChildVM, stats StatsVM, current_entry ShelfEntryVM \| None}] |
| `adult/child_report.html` | `child` ChildVM, `stats` StatsVM, `entries` [ShelfEntryVM], `grants` [GrantVM], `memberships` [{valid_until, status}] |
| `catalog.html` (`adult/`, `child/` variants) | `books` [BookVM], `filters` {age_band, genre}, `shelf_book_ids` set |
| `achievements.html` | `earned` [GrantVM], `locked` [{AchievementVM, members_only, hint}] |
| `club_corner.html` | `activities` [{title, starts_at, place}] |

View models (plain dataclasses in `core/viewmodels.py`):

- `BookVM`: public_id, title, author, page_count, cover_color, cover_emoji, genre, age_band
- `ShelfEntryVM`: public_id, book BookVM, current_page, page_count, percent (int 0–100), status
- `StatsVM`: books_on_shelf, books_finished, pages_total, pages_7d
- `GrantVM`: code, title, icon, granted_at, members_only
- `ChildVM`: public_id, nickname, avatar, age_band
- `MascotLine`: key (enum), text (translated), mood (`happy`/`cheer`/`think`/`oops`)

## Mascot script (P0, fixed text, translatable)

| key | When | Example (ro) |
|---|---|---|
| `welcome` | child home, no active book | "Salut! Hai să alegem o carte." |
| `progress_saved` | progress 2xx | "Bravo! Ai ajuns la pagina {page}." |
| `book_finished` | finish 2xx | "Ai terminat cartea! Ce aventură!" |
| `achievement` | any new grant | "Ai deblocat «{title}»!" |
| `member_hint` | locked members-only achievement | "Insigna asta e pentru membrii clubului." |
| `error` | 422 | "Hmm, verifică numărul paginii." |
| `offline` | offline / send error | "Nu am internet acum. Încercăm mai târziu?" |

No pressure or guilt lines (FR-032).
