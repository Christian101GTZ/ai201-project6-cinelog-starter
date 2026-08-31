# CineLog API

CineLog is a community film tracking API where users can browse films, track movies they've watched, rate them, build collections, and save films to a personal watchlist.

The backend is built with Flask and SQLAlchemy and uses a local SQLite database for persistent storage.

---

## Features

* Browse films in the catalog
* Filter films by genre and year
* Retrieve individual films by UUID
* Add and remove films from a user's collection
* Save films to a watchlist
* Prevent duplicate watchlist entries
* Retrieve watchlist entries newest-first
* Store watchlist visibility metadata
* UUID-based film and user identifiers
* Automated testing with pytest

---

## Tech Stack

* Python
* Flask
* SQLAlchemy
* SQLite
* pytest
* REST APIs

---

## Setup

Install the project dependencies:

```bash
pip install -r requirements.txt
```

Start the Flask application:

```bash
python app.py
```

The app starts on:

```text
http://localhost:5000
```

and uses a local SQLite database:

```text
cinelog.db
```

---

## Project Structure

```text
cinelog-api/
├── app.py                     # Flask app factory and route registration
├── models.py                  # SQLAlchemy database models
├── services/
│   ├── collection_service.py  # Collection business logic
│   └── watchlist_service.py   # Watchlist business logic
├── routes/
│   ├── films.py               # Film browsing endpoints
│   ├── collection.py          # Collection endpoints
│   └── watchlist/
│       └── watchlist.py       # Watchlist endpoints
├── tests/
│   ├── test_collection.py     # Collection service tests
│   └── test_watchlist.py      # Watchlist service tests
├── CONTRIBUTING.md            # Project conventions
├── pr-response.md             # Code-review responses and design decisions
└── requirements.txt
```

The project separates database models, API routes, and business logic into different modules to make the backend easier to maintain and test.

---

## API Overview

### Films

| Method | Endpoint           | Description                                           |
| ------ | ------------------ | ----------------------------------------------------- |
| GET    | `/films/`          | List all films and optionally filter by genre or year |
| GET    | `/films/<film_id>` | Get a single film by UUID                             |

### Collection

| Method | Endpoint                       | Description                           |
| ------ | ------------------------------ | ------------------------------------- |
| GET    | `/collection/<user_id>`        | Get a user's collection, newest first |
| POST   | `/collection/<user_id>/add`    | Add a film to the collection          |
| DELETE | `/collection/<user_id>/remove` | Remove a film from the collection     |

### Watchlist

| Method | Endpoint                   | Description                          |
| ------ | -------------------------- | ------------------------------------ |
| GET    | `/watchlist/<user_id>`     | Get a user's watchlist, newest first |
| POST   | `/watchlist/<user_id>/add` | Add a film to the user's watchlist   |

When adding a film to the watchlist, the request body should contain the film UUID:

```json
{
  "film_id": "<uuid>"
}
```

The API prevents duplicate watchlist entries and rejects film IDs that do not exist.

---

## Data Models

### Film

Represents a film in the CineLog catalog.

Film identifiers use UUIDs.

### User

Represents a CineLog user.

User identifiers also use UUIDs.

### CollectionEntry

Links a user to a film they have watched.

Collection entries can store information such as:

* Rating
* Date added

A user can only have one collection entry for each film.

### WatchlistEntry

Links a user to a film they want to watch later.

Watchlist entries contain:

* User ID
* Film ID
* Date added
* Public visibility flag

The model also defines a SQLAlchemy relationship to its associated `Film`.

New watchlist entries currently default to:

```python
public = False
```

The visibility field is stored in the model, but viewer-based authorization is not yet implemented by the API.

---

## Naming Conventions

Service functions follow a `verb_to_noun` naming pattern.

Examples include:

```python
add_to_collection()
add_to_watchlist()
get_collection()
get_watchlist()
```

See `CONTRIBUTING.md` for additional project conventions.

---

## Running Tests

Run the complete test suite with:

```bash
pytest tests/
```

For more detailed output:

```bash
pytest tests/ -v
```

The current test suite includes tests for both collection and watchlist functionality.

Watchlist tests cover:

* Successfully adding a film
* Attempting to add a nonexistent film
* Preventing duplicate entries
* Retrieving a populated watchlist

---

## My Contribution

CineLog began as an existing Flask codebase provided through CodePath. My work focused on implementing and refining the watchlist feature through a simulated professional code-review workflow.

### Watchlist Implementation

I worked on the feature that allows users to save films they want to watch later, separately from their collection of already-watched films.

The implementation includes:

* `WatchlistEntry` database model
* `add_to_watchlist(user_id, film_id)`
* `get_watchlist(user_id)`
* `POST /watchlist/<user_id>/add`
* `GET /watchlist/<user_id>`

### Duplicate Prevention

I added validation that prevents a user from adding the same film to their watchlist more than once.

Before creating an entry, the service checks whether a matching user and film combination already exists.

If it does, the service raises:

```python
AlreadyInWatchlistError
```

instead of creating a duplicate database row.

### Automated Testing

I created `tests/test_watchlist.py` based on the structure of the project's existing collection tests.

I added tests covering:

* Successful watchlist additions
* Invalid film IDs
* Duplicate prevention
* Watchlist retrieval

### UUID Migration

During development, the main branch migrated film identifiers from integers to UUIDs.

I rebased my watchlist branch onto the updated main branch, resolved the resulting model conflict, and updated the watchlist implementation and tests so film references use UUID-compatible values throughout the application.

### Watchlist Ordering

I changed watchlist retrieval to sort by:

```python
WatchlistEntry.date_added.desc()
```

instead of sorting alphabetically by film title.

This places recently saved films at the top of the watchlist.

### Default Visibility

I changed new watchlist entries to default to:

```python
public = False
```

This establishes privacy-oriented metadata at the model level.

The current API does not yet distinguish between an owner and another viewer when retrieving a watchlist, so the flag is groundwork for a future visibility system rather than complete access control.

---

## Debugging and Regression Fix

While manually testing the completed watchlist functionality, I discovered that retrieving a non-empty watchlist raised:

```text
AttributeError: 'WatchlistEntry' object has no attribute 'film'
```

The existing tests had not caught the problem because they did not exercise `get_watchlist()` end-to-end.

The service expected:

```python
entry.film
```

but `WatchlistEntry` did not define the required SQLAlchemy relationship.

I fixed the issue by adding:

```python
film = db.relationship("Film", backref="watchlist_entries")
```

I then added a regression test that retrieves a populated watchlist and verifies that the associated film information is returned correctly.

---

## Development Workflow

This project gave me experience working within an existing codebase instead of starting an application completely from scratch.

The development process included:

* Understanding an unfamiliar Flask codebase
* Following existing project conventions
* Working on a dedicated feature branch
* Responding to code-review feedback
* Implementing backend business logic
* Writing automated tests
* Rebasing against upstream changes
* Resolving a database-model conflict
* Debugging an integration issue
* Adding a regression test
* Documenting technical decisions and tradeoffs
* Using a pull-request workflow

Additional details about the review process and engineering decisions are documented in [`pr-response.md`](./pr-response.md).

---

## Project Background

CineLog originated from a starter repository provided through CodePath's AI Engineering curriculum for a simulated code-review exercise.

The starter project already included the Flask application structure, film catalog, collection functionality, database models, and collection tests.

My contribution focused specifically on implementing and refining the watchlist feature, addressing review feedback, writing tests, adapting the feature to an upstream UUID migration, and fixing an integration bug discovered during verification.

This repository remains linked to the original starter repository so its development history and attribution remain visible.
