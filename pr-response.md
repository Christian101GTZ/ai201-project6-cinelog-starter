# PR Response Doc — CineLog Watchlist Feature

## AI Usage
<!-- REVIEW AND EDIT THIS to reflect your own honest account before submitting. -->

- **Orientation:** Used AI to summarize `models.py`, `collection_service.py`,
  and `test_collection.py`, to walk through `add_to_collection()` step by step,
  and to explain the test structure. Verified the summaries against the code.
- **Comment 1 (rename):** AI performed the rename and found the call site; I
  reviewed the project-wide search result.
- **Comment 2 (deduplication):** AI wrote the duplicate-check and
  `AlreadyInWatchlistError`. NOTE: the course asks this be my own work — I should
  re-type it from the explanation and understand each line before submitting.
- **Comment 3 (test):** AI wrote `tests/test_watchlist.py` following the
  `test_collection.py` pattern.
- **Comments 4 & 5 (design decisions):** AI laid out the tradeoffs and gave
  recommendations; I chose the positions (private default; date-added order).
  AI drafted the write-ups — these are marked DRAFT and I need to rewrite them
  in my own words, since the course requires the reasoning to be mine.
- **Comment 6 (rebase):** AI ran the rebase and resolved the UUID conflict.

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
> DRAFT — rewrite in my own words before submitting (see AI Usage note).

**My position:** Watchlists should default to **private** (`public=False`).
Changed the model default in `models.py` from `True` to `False`.

**Reasoning:** CineLog is social, but a watchlist is a list of films a user
*hasn't* watched yet — it's aspirational and often personal (guilty pleasures,
films you're embarrassed to admit you haven't seen). By the principle of least
surprise, a user saving a film for later doesn't expect that action to broadcast
anything. Privacy-by-default treats sharing as a deliberate choice the user
opts into, which builds trust — the safer default when we're unsure, because a
user can always make a list public, but can't un-share something that was
exposed without their intent.

**Tradeoff acknowledged:** This weakens the social/discovery angle out of the
box — public feeds and "what are my friends planning to watch" stay empty until
users actively opt in, so the feature's social value is deferred rather than
immediate. If CineLog's product strategy is explicitly discovery-first, that's a
real cost; I'd mitigate it by making the "make public" toggle prominent in the
UI rather than by flipping the default back.

## Comment 5 — Sort order
> DRAFT — rewrite in my own words before submitting (see AI Usage note).

**My position:** Agree with the maintainer — sort by **date added, newest
first**. Changed `get_watchlist()` from `order_by(Film.title.asc())` to
`order_by(WatchlistEntry.date_added.desc())`.

**Reasoning:** A watchlist is a queue of intent. When someone opens it, the most
useful thing to surface is what they most recently decided they wanted to watch —
that's freshest in their mind. There's also a consistency argument the reviewer
didn't raise: `get_collection()` already sorts `date_added.desc()`, so matching
it means the whole app orders user lists the same way, which is less surprising
than having two lists sort by two different rules.

**Engagement with reviewer's point:** The reviewer's reasoning ("most users want
to see what they added recently") is exactly right, so I'm implementing their
preference, not just agreeing rhetorically. I did consider keeping alphabetical:
it's genuinely better for *finding one specific known title* in a long list.
But that's a search/filter problem, better solved with a search box later, not
by making the default sort optimize for the rarer case. I also considered
oldest-first (treat it as a FIFO backlog), but rejected it — recency matches
both the reviewer's point and `get_collection`, so newest-first is the most
consistent, least-surprising choice.

## Comment 6 — Rebase
**What conflicted:** `git fetch origin` + `git rebase origin/main` replayed my
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

**How I verified no conflict remains:** `git log --oneline --graph` shows my
commits linear on top of `origin/main` with no merge commit introduced by me.
`grep` for `Integer` / `<int>` / `999999` in the watchlist files returns only
the legitimate integer columns (`year`, `rating`) — no `film_id` integers left.
`pytest tests/ -v` → 7 passed. A safety branch `backup/pre-rebase-watchlist`
was created before rebasing.

## Commit History
`git log --oneline` on `feature/watchlist` (rewritten, conventional, no merge commits):

```
58dfb67 docs: add PR description and commit history to pr-response
88f99fb feat: default watchlists to private and order by date added
2c69c0e docs: record rebase resolution in pr-response
b45bc90 fix: update watchlist film_id references to UUID after main refactor
a6e42c4 test: add watchlist service tests for add_to_watchlist
203667e fix: add deduplication check to prevent duplicate watchlist entries
a7555a1 refactor: rename save_to_watchlist to add_to_watchlist per naming convention
0bf52ec feat: add watchlist model, service, and endpoint
```
<!-- Replace this code block with a SCREENSHOT of `git log --oneline` before submitting.
     (Commit hashes will differ again after you re-type Comment 2 and rewrite Comments 4 & 5.) -->

## PR Description

### What the watchlist feature does
Lets a user save films they want to watch **later** — a "watchlist" that is
separate from their collection of already-watched films. It adds:

- a `WatchlistEntry` model (linking a user to a film, with a `date_added`
  timestamp and a `public` visibility flag),
- service functions `add_to_watchlist(user_id, film_id)` and
  `get_watchlist(user_id)`, and
- two REST endpoints:
  - `POST /watchlist/<user_id>/add` — body `{ "film_id": "<uuid>" }` — save a film,
  - `GET /watchlist/<user_id>` — list the user's watchlist.

Saving a film that doesn't exist raises `FilmNotFoundError`; saving a film that's
already on the list raises `AlreadyInWatchlistError` (no duplicate is created).
Film IDs are UUIDs, consistent with the main-branch refactor.

### Design decisions
1. **Default visibility → private (`public=False`).** A watchlist is aspirational
   and often personal, and by the principle of least surprise a user saving a film
   shouldn't broadcast it. Sharing is an explicit opt-in. (Tradeoff: social
   discovery is weaker out of the box — see Comment 4.)
2. **Sort order → date added, newest first.** Matches the maintainer's preference
   and `get_collection()`'s ordering, so both user lists behave consistently.
   (See Comment 5.)

### How to manually test
1. Install dependencies and start the app:
   ```
   pip install -r requirements.txt
   python app.py        # serves at http://localhost:5000
   ```
2. There are no create endpoints for users/films, so seed one of each in a shell
   (in a second terminal) and note the printed IDs:
   ```
   python -c "from app import create_app, db; from models import User, Film; \
   app=create_app(); ctx=app.app_context(); ctx.push(); \
   u=User(username='alice', email='alice@example.com'); f=Film(title='Dune', year=2021, genre='Sci-Fi'); \
   db.session.add_all([u,f]); db.session.commit(); print('USER', u.id); print('FILM', f.id)"
   ```
3. **Add to watchlist** (expect `201` and `"public": false`):
   ```
   curl -X POST http://localhost:5000/watchlist/<USER_ID>/add \
        -H "Content-Type: application/json" -d "{\"film_id\": \"<FILM_ID>\"}"
   ```
4. **View watchlist** (expect the film, newest-added first):
   ```
   curl http://localhost:5000/watchlist/<USER_ID>
   ```
5. **Verify deduplication:** run the same POST from step 3 again, then GET again —
   the watchlist should still contain only **one** entry for that film.
6. (Optional) Add a second film, then GET — confirm the **most recently added**
   film appears first (date-added ordering).

You can also run the automated tests: `pytest tests/ -v` (7 passing).