"""
services/watchlist_service.py — CineLog (feature/watchlist branch)

SUMMARY (in plain terms):
This file holds the LOGIC for a user's watchlist — films they want to watch
LATER (as opposed to the collection, which is films already watched). Like the
collection service, it sits between the web routes and the database.

What it provides:
  - add_to_watchlist(...)  : add a film to the watchlist (blocks duplicates)
  - get_watchlist(...)     : list a user's saved films, sorted A–Z by title

It reuses FilmNotFoundError from the collection service rather than defining
its own copy.
"""

from app import db  # the shared database connection/session
from models import Film, WatchlistEntry  # the two tables this file works with
# Reuse the same "film doesn't exist" error the collection service defines,
# instead of creating a second, duplicate one.
from services.collection_service import FilmNotFoundError


class AlreadyInWatchlistError(Exception):
    """Raised when a film is already on the user's watchlist."""
    pass


def add_to_watchlist(user_id, film_id):
    """
    Save a film to a user's watchlist.

    Args:
        user_id (str): UUID of the user.
        film_id (int): ID of the film. (Note: integer — pre-refactor)

    Returns:
        WatchlistEntry: The newly created entry.

    Raises:
        FilmNotFoundError: If film_id does not exist.
        AlreadyInWatchlistError: If the film is already on the user's watchlist.
    """
    # Look up the film by its ID. If it doesn't exist, stop here.
    film = db.session.get(Film, film_id)
    if film is None:
        raise FilmNotFoundError(f"No film found with id '{film_id}'")

    # Check whether this user already has this film on their watchlist.
    # .first() returns the existing row, or None if there isn't one.
    existing = WatchlistEntry.query.filter_by(
        user_id=user_id, film_id=film_id
    ).first()
    if existing:
        raise AlreadyInWatchlistError(
            f"Film '{film_id}' is already on this user's watchlist"
        )

    # Create the watchlist entry and save it.
    entry = WatchlistEntry(user_id=user_id, film_id=film_id)
    db.session.add(entry)
    db.session.commit()
    return entry


def get_watchlist(user_id):
    """
    Return all films on a user's watchlist.

    Args:
        user_id (str): UUID of the user.

    Returns:
        list[dict]: List of film dicts with watchlist metadata attached.
    """
    # Get all of this user's watchlist entries. .join(Film) links each entry
    # to its film so we can sort by film title alphabetically (.asc()).
    entries = (
        WatchlistEntry.query
        .filter_by(user_id=user_id)
        .join(Film)
        .order_by(Film.title.asc())
        .all()
    )

    # Build the response: start from each film's data, then attach the
    # watchlist extras (when it was added, and whether it's public).
    result = []
    for entry in entries:
        film_dict = entry.film.to_dict()  # entry.film works via the DB relationship
        film_dict["date_added"] = entry.date_added.isoformat()
        film_dict["public"] = entry.public
        result.append(film_dict)

    return result
