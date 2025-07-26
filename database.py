import streamlit as st
import uuid
from datetime import datetime
from sqlalchemy import text

def init_db(conn):
    """Initializes the database and creates the ratings table if it doesn't exist."""
    with conn.session as s:
        s.execute(text("""
            CREATE TABLE IF NOT EXISTS ratings (
                id TEXT PRIMARY KEY,
                image_id TEXT NOT NULL,
                rating INTEGER NOT NULL,
                session_id TEXT NOT NULL,
                timestamp DATETIME NOT NULL
            );
        """))
        s.commit()

def save_rating(conn, image_id, rating, session_id):
    """Saves a new rating to the database using the provided connection."""
    with conn.session as s:
        s.execute(
            text("INSERT INTO ratings (id, image_id, rating, session_id, timestamp) VALUES (:id, :image_id, :rating, :session_id, :timestamp)"),
            params=dict(
                id=str(uuid.uuid4()),
                image_id=image_id,
                rating=rating,
                session_id=session_id,
                timestamp=datetime.now()
            )
        )
        s.commit()

def get_rated_images(conn, session_id):
    """
    Fetches a list of image IDs that have already been rated or skipped 
    by a specific session.
    """
    with conn.session as s:
        result = s.execute(
            text("SELECT image_id FROM ratings WHERE session_id = :session_id"),
            params=dict(session_id=session_id)
        ).fetchall()
    return [row.image_id for row in result]

def get_all_ratings(conn):
    """Fetches all ratings from the database."""
    with conn.session as s:
        result = s.execute(text("SELECT * FROM ratings ORDER BY timestamp DESC")).fetchall()
    return result 