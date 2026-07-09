# PR Response Doc — CineLog Watchlist Feature

## AI Usage
<!-- Fill in at the end — how you used AI tools during this project -->

## Comment 1 — Rename
**What I did:** Renamed `save_to_watchlist()` to `add_to_watchlist()` in
`services/watchlist_service.py` to match the project's `verb_to_noun` naming
convention (as in `add_to_collection()`). Updated the one call site in
`routes/watchlist/watchlist.py` — both the `import` line and the call inside
the `add_film` endpoint.

**How I verified:** Ran a project-wide search for `save_to_watchlist` (Grep /
find-all-references) after the change — 0 matches remain. Ran `pytest tests/ -v`:
all 4 existing tests still pass, confirming nothing else referenced the old name.

## Comment 2 — Deduplication
**What I did:** Added a duplicate guard to `add_to_watchlist()` in
`services/watchlist_service.py`, following the pattern in `add_to_collection()`.
Defined a parallel error class `AlreadyInWatchlistError`, then—between the
`FilmNotFoundError` check and the insert—queried
`WatchlistEntry.query.filter_by(user_id=..., film_id=...).first()` and raised
`AlreadyInWatchlistError` if a row already exists. The check runs before
`db.session.add(...)`, so no duplicate is ever written. Also updated the
docstring `Raises:` section.

**How I verified:** Confirmed the new check sits above the insert (mirrors
`add_to_collection`, collection_service.py lines 52-58). Added
`test_add_to_watchlist_duplicate_raises` (see Comment 3) which asserts a second
add raises `AlreadyInWatchlistError` and that exactly one row exists afterward.
`pytest tests/ -v` passes.

## Comment 3 — Missing test
**What I did:** Created `tests/test_watchlist.py`, reusing the fixture pattern
from `test_collection.py` (`app` / `sample_user` / `sample_film`). Modeled the
required test on `test_add_to_collection_nonexistent_film_raises`: wrote
`test_add_to_watchlist_nonexistent_film_raises`, which passes a film_id that
doesn't exist and asserts `add_to_watchlist` raises `FilmNotFoundError` (via
`pytest.raises`). Also added a happy-path test and a duplicate test to cover
the Comment 2 behavior.

**How I verified:** `pytest tests/test_watchlist.py -v` → 3 passed.
`pytest tests/ -v` (full suite) → 7 passed.

## Comment 4 — Default visibility
**My position:**
**Reasoning:**
**Tradeoff acknowledged:**

## Comment 5 — Sort order
**My position:**
**Reasoning:**
**Engagement with reviewer's point:**

## Comment 6 — Rebase
**What conflicted:** `git fetch origin` + `git rebase origin/main` replayed my 6
branch commits onto main, which now contains
`07ca580 refactor: migrate film IDs from integer to UUID`. The conflict landed
in `models.py`: main defines `Film.id` and `CollectionEntry.film_id` as
`String(36)` UUIDs, while my branch still had them (and `WatchlistEntry.film_id`)
as `Integer`. (I also had to remove an untracked local `.gitignore` first, since
main now tracks one.)

**How I resolved it:** Took main's UUID types as the source of truth. In the
resolved `models.py`, `Film.id`, `CollectionEntry.film_id`, and
`WatchlistEntry.film_id` are all `db.String(36)`; kept my explanatory comments
but corrected the ones that claimed film IDs were integers. Then updated the
watchlist code that still assumed integers: the `film_id` docstring in
`add_to_watchlist`, the request-body doc in `routes/watchlist/watchlist.py`, and
the nonexistent-film test (now uses a UUID string, not `999999`).

**How I verified no conflict remains:** `git log --oneline --graph` shows my 6
commits linear on top of `origin/main` with no merge commit introduced by me.
`grep` for `Integer` / `<int>` / `999999` in the watchlist files returns only
the legitimate integer columns (`year`, `rating`) — no `film_id` integers left.
`pytest tests/ -v` → 7 passed. A safety branch `backup/pre-rebase-watchlist`
was created before rebasing.

## PR Description
<!-- Written at the end — feature overview, design decisions, manual testing steps -->