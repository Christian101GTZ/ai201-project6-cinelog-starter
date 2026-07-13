# PR Response Doc — CineLog Watchlist Feature

## AI Usage

- **Orientation:** Used AI to summarize `models.py`, `collection_service.py`,
  and `test_collection.py`, to walk through `add_to_collection()` step by step,
  and to explain the test structure. Verified every summary against the code.
- **Comment 1 (rename):** Used AI to run the project-wide search for call sites;
  I reviewed the results and confirmed 0 matches for the old name remained.
- **Comment 2 (deduplication):** Studied how `add_to_collection()` guards
  duplicates, then wrote the parallel check and `AlreadyInWatchlistError` in
  `add_to_watchlist()` following that pattern.
- **Comment 3 (test):** Wrote `tests/test_watchlist.py` modeled on
  `test_collection.py`'s fixtures and assertions.
- **Comments 4 & 5 (design decisions):** I chose the positions myself (private
  default; date-added order). I then used AI as a devil's advocate — I asked it
  what counterarguments a careful reviewer would raise against each position and
  what tradeoff I wasn't acknowledging. It surfaced three things I hadn't fully
  addressed: (1) the `public` flag isn't enforced yet in `get_watchlist`, so the
  default is currently forward-looking metadata rather than active protection;
  (2) `CollectionEntry` has no visibility field at all, which makes a
  private-watchlist / open-collection split inconsistent; and (3) my sort-order
  argument leaned on "consistency with `get_collection`," which is weaker than a
  use-case argument because the two lists do different jobs. I revised both
  responses below to engage those points directly rather than delete them.
- **Comment 6 (rebase):** Used AI to help run the rebase and confirm the UUID
  conflict resolution; verified the result with the test suite and `git log`.
- **Bug found while verifying:** Driving `get_watchlist()` end-to-end (with AI
  help exercising the path) surfaced a real `AttributeError` — see the
  "Additional fix" section below.

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

**How I verified:** `pytest tests/test_watchlist.py -v` → all passed.
`pytest tests/ -v` (full suite) → 8 passed. (The file grew to four tests once
the retrieval regression test from the Additional fix was added.)

## Comment 4 — Default visibility

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

**Two things I want to be honest about, because they cut against me:**

1. *The flag isn't enforced yet.* As the code stands, `get_watchlist(user_id)`
   returns **every** entry regardless of `public`, and `GET /watchlist/<user_id>`
   has no owner-vs-viewer distinction — so today the default only changes the
   value echoed back in `to_dict`, it doesn't actually hide anything. I'm
   choosing the private default deliberately as the *forward-looking* correct
   value: when a real visibility filter is added to `get_watchlist` (return all
   rows to the owner, only `public=True` rows to others), the data already
   defaults to the safe state instead of needing a backfill/migration to walk
   back over-shared rows. Setting the safe default now is cheap; fixing an
   over-exposed default later is not.

2. *It's inconsistent with the collection.* `CollectionEntry` has no `public`
   column at all, so a user's *watched-and-rated* films are fully exposed via
   `GET /collection/<user_id>`. You could argue my privacy logic applies even
   more to the collection. I agree — and I read that as the watchlist being the
   *first* list to get a visibility flag and establishing privacy-by-default as
   the pattern the collection should adopt next, not as a reason to make the
   watchlist match the collection's current (accidental) openness.

## Comment 5 — Sort order

**My position:** Agree with the maintainer — sort by **date added, newest
first**. Changed `get_watchlist()` from `order_by(Film.title.asc())` to
`order_by(WatchlistEntry.date_added.desc())`.

**Reasoning (use-case first):** A watchlist is a queue of intent, and the most
common interaction is a quick glance — "what did I just add / what's on here?" —
not hunting for one specific title. Newest-first serves that glance directly:
the film freshest in the user's mind sits at the top. That's the primary reason,
and it's about what the list is *for*, not about matching another table.

**Consistency is a supporting point, not the main one.** `get_collection()`
already sorts `date_added.desc()`, so newest-first also keeps both user lists
ordered the same way. I'm deliberately listing this second, because I don't
think "match the collection" would be a good enough reason on its own — the two
lists do different jobs (the collection is an archival log of what you *watched*;
the watchlist is a queue of what you *intend* to watch), and symmetry between
them is only worth having when it doesn't fight the watchlist's purpose. Here it
doesn't, so it's a nice bonus rather than the argument.

**Engagement with the reviewer + alternatives I rejected:** The reviewer's
reasoning ("most users want to see what they added recently") matches my
use-case argument, so I'm implementing their preference on the merits, not just
deferring. I considered **alphabetical**: it genuinely helps find one known
title in a long list — but that's a search/filter job, and CineLog has no search
box today, so optimizing the default sort for the rarer "find a specific film"
case would hurt the common glance case now in exchange for a benefit a future
search box would deliver better. I also seriously considered **oldest-first**
(treat the watchlist as a FIFO backlog to clear, so old intentions don't sink
out of sight) — this is the strongest counter to newest-first, and if CineLog
later framed the watchlist explicitly as a "backlog to finish," I'd revisit it.
For the current glance-oriented use case, newest-first wins.

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
`pytest tests/ -v` → passed. A safety branch `backup/pre-rebase-watchlist`
was created before rebasing.

## Additional fix (found while verifying) — `get_watchlist` crash

**What I found:** While driving the feature end-to-end, `GET /watchlist/<user_id>`
raised `AttributeError: 'WatchlistEntry' object has no attribute 'film'` for any
non-empty watchlist. The existing tests passed only because none of them called
`get_watchlist()`.

**Root cause:** `get_watchlist()` builds its response with `entry.film`
(`watchlist_service.py`), but `WatchlistEntry` defined no `film` relationship.
The collection side works because `Film.collection_entries` declares
`backref="film"`, giving `CollectionEntry.film` — there was no equivalent for
the watchlist.

**Fix:** Added `film = db.relationship("Film", backref="watchlist_entries")` to
`WatchlistEntry` (mirroring the collection pattern), and added a regression test
`test_get_watchlist_returns_added_film` that calls `get_watchlist()` and asserts
the film details + metadata come back — so this path can't silently break again.

**How I verified:** Reproduced the `AttributeError` before the fix, confirmed the
endpoint returns the film after it, and ran the full suite → `8 passed`.

## Commit History
`git log --oneline origin/main..HEAD` on `feature/watchlist` (rewritten,
conventional, no merge commits):

![git log --oneline on feature/watchlist](Assets/Screenshot%202026-07-13%20143815.png)

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

You can also run the automated tests: `pytest tests/ -v` (8 passing).