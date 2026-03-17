"""
models.py — CineLog

SUMMARY (in plain terms):
This file defines the shape of the app's DATABASE. Each class below is one
table, and each attribute inside it is one column. Using SQLAlchemy, we get to
work with database rows as if they were normal Python objects.

The four tables:
  - User            : a person using the app
  - Film            : a movie in the system
  - CollectionEntry : a film a user has ALREADY WATCHED (with an optional rating)
  - WatchlistEntry  : a film a user wants to watch LATER

Film IDs use UUIDs throughout (post-refactor state on main — integer IDs were
migrated to UUIDs), so every id / film_id column is a 36-char UUID string.
"""

import uuid
from datetime import datetime, timezone
from app import db  # 'db' is our SQLAlchemy database helper (created in app.py)


# Makes a random ID string like "3f2504e0-4f89-...". Used as the default ID
# for rows so we don't have to set one by hand.
def generate_uuid():
    return str(uuid.uuid4())


# Each class below is one database TABLE. Each attribute is one COLUMN.
# SQLAlchemy lets us treat table rows like regular Python objects.


# A person who uses the app.
class User(db.Model):
    # Unique ID for this user. A random UUID string (36 characters).
    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    # Login name. Must be unique and can't be empty.
    username = db.Column(db.String(64), unique=True, nullable=False)
    # Email address. Must be unique and can't be empty.
    email = db.Column(db.String(120), unique=True, nullable=False)
    # When the account was created. Defaults to the current UTC time.
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Shortcut link: user.collection_entries gives all films this user logged.
    # (backref="user" also lets us do entry.user to go the other way.)
    collection_entries = db.relationship("CollectionEntry", backref="user", lazy=True)

    # Turns this user into a plain dictionary — handy for sending back as JSON.
    def to_dict(self):
        return {"id": self.id, "username": self.username, "email": self.email}


# A movie in the system.
class Film(db.Model):
    # Unique ID for this film. A random UUID string — migrated from integer in
    # commit "refactor: migrate film IDs from integer to UUID".
    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    # Movie title. Required.
    title = db.Column(db.String(200), nullable=False)
    # The rest are optional (nullable=True), so they can be left blank.
    year = db.Column(db.Integer, nullable=True)
    director = db.Column(db.String(200), nullable=True)
    genre = db.Column(db.String(100), nullable=True)
    poster_url = db.Column(db.String(500), nullable=True)
    # Average of all user ratings. Starts at 0.0.
    average_rating = db.Column(db.Float, default=0.0)

    # Shortcut link: film.collection_entries gives everyone who logged this film.
    collection_entries = db.relationship("CollectionEntry", backref="film", lazy=True)

    # Turns this film into a plain dictionary (for JSON responses).
    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "year": self.year,
            "director": self.director,
            "genre": self.genre,
            "poster_url": self.poster_url,
            "average_rating": self.average_rating,
        }


class CollectionEntry(db.Model):
    """Represents a film a user has already watched and logged."""
    # Unique ID for this log entry (random UUID string).
    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    # Which user logged it. Points to a row in the User table.
    user_id = db.Column(db.String(36), db.ForeignKey("user.id"), nullable=False)
    # Which film was logged. Points to a row in the Film table (UUID string).
    film_id = db.Column(db.String(36), db.ForeignKey("film.id"), nullable=False)
    # When it was logged. Defaults to now.
    date_added = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    rating = db.Column(db.Integer, nullable=True)  # 1–5, optional

    # Rule: a user can only log the same film once (no duplicate rows).
    __table_args__ = (
        db.UniqueConstraint("user_id", "film_id", name="unique_user_film_collection"),
    )

    # Turns this entry into a plain dictionary (for JSON responses).
    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "film_id": self.film_id,
            "date_added": self.date_added.isoformat(),
            "rating": self.rating,
        }


class WatchlistEntry(db.Model):
    """Represents a film a user wants to watch (saved for later)."""
    # Unique ID for this watchlist entry (random UUID string).
    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    # Which user saved it. Points to a row in the User table.
    user_id = db.Column(db.String(36), db.ForeignKey("user.id"), nullable=False)
    # Which film was saved. Points to a row in the Film table (UUID string).
    film_id = db.Column(db.String(36), db.ForeignKey("film.id"), nullable=False)
    # When it was saved. Defaults to now.
    date_added = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    # Whether other people can see this watchlist item. Defaults to visible.
    public = db.Column(db.Boolean, default=True)

    # Turns this entry into a plain dictionary (for JSON responses).
    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "film_id": self.film_id,
            "date_added": self.date_added.isoformat(),
            "public": self.public,
        }
