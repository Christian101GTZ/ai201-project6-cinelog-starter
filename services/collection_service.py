"""
services/collection_service.py — CineLog

SUMMARY (in plain terms):
This file holds the LOGIC for a user's film collection — the films they've
already watched. It sits between the web routes and the database: the routes
call these functions, and these functions read/write the tables in models.py.

What it provides:
  - Three error types (film not found / already added / not in collection) so
    callers can react to each problem clearly instead of the app crashing.
  - add_to_collection(...)      : log a film as watched (blocks duplicates)
  - remove_from_collection(...) : un-log a film
  - get_collection(...)         : list a user's watched films, newest first

All functions follow the project's verb_to_noun naming convention.
"""

from app import db  # the shared database connection/session
from models import Film, CollectionEntry  # the two tables this file works with


# --- Custom error types ---
# These let this service "raise" a clear, specific error. The web layer can
# then catch each one and return the right HTTP response instead of crashing.

class FilmNotFoundError(Exception):
    """Raised when a film_id does not exist in the database."""
    pass


class AlreadyInCollectionError(Exception):
    """Raised when a film is already in the user's collection."""
    pass


class NotInCollectionError(Exception):
    """Raised when trying to remove a film that isn't in the collection."""
    pass


def add_to_collection(user_id, film_id, rating=None):
    """
    Add a film to a user's collection (i.e., mark it as watched).

    Args:
        user_id (str): UUID of the user.
        film_id (str): UUID of the film.
        rating (int, optional): Rating from 1–5. May be added later.

    Returns:
        CollectionEntry: The newly created entry.

    Raises:
        FilmNotFoundError: If film_id does not exist.
        AlreadyInCollectionError: If the film is already in the user's collection.
    """
    # 1. Look up the film by its ID. If it doesn't exist, stop here.
    film = db.session.get(Film, film_id)
    if film is None:
        raise FilmNotFoundError(f"No film found with id '{film_id}'")

    # 2. Check whether this user already has this film logged.
    existing = CollectionEntry.query.filter_by(
        user_id=user_id, film_id=film_id
    ).first()
    if existing:
        raise AlreadyInCollectionError(
            f"Film '{film_id}' is already in this user's collection"
        )

    # 3. Create the new entry, add it to the session, and save (commit) to the DB.
    entry = CollectionEntry(user_id=user_id, film_id=film_id, rating=rating)
    db.session.add(entry)
    db.session.commit()
    return entry


def remove_from_collection(user_id, film_id):
    """
    Remove a film from a user's collection.

    Args:
        user_id (str): UUID of the user.
        film_id (str): UUID of the film.

    Returns:
        bool: True if the entry was removed.

    Raises:
        NotInCollectionError: If the film is not in the user's collection.
    """
    # Find this user's entry for this film. .first() returns None if there isn't one.
    entry = CollectionEntry.query.filter_by(
        user_id=user_id, film_id=film_id
    ).first()
    if entry is None:
        raise NotInCollectionError(
            f"Film '{film_id}' is not in this user's collection"
        )

    # Delete the entry and save the change.
    db.session.delete(entry)
    db.session.commit()
    return True


def get_collection(user_id):
    """
    Return all films in a user's collection, sorted by date added (newest first).

    Args:
        user_id (str): UUID of the user.

    Returns:
        list[dict]: List of film dicts (not CollectionEntry objects) with
                    the date_added and rating from the entry attached.
    """
    # Get all of this user's entries, ordered newest-added first (.desc()).
    entries = (
        CollectionEntry.query
        .filter_by(user_id=user_id)
        .order_by(CollectionEntry.date_added.desc())
        .all()
    )

    # Build the response: start from each film's data, then attach the
    # entry-specific extras (when it was added, and the user's rating).
    result = []
    for entry in entries:
        film_dict = entry.film.to_dict()  # entry.film works via the DB relationship
        film_dict["date_added"] = entry.date_added.isoformat()
        film_dict["rating"] = entry.rating
        result.append(film_dict)

    return result
