import streamlit as st
import uuid
from datetime import datetime
from sqlalchemy import text

def init_db(conn):
    """Initializes the database and creates the ratings table if it doesn't exist."""
    with conn.session as s:
        # Check if table exists with old schema
        result = s.execute(text("""
            SELECT sql FROM sqlite_master 
            WHERE type='table' AND name='ratings'
        """)).fetchone()
        
        if result and 'INTEGER' in result[0]:
            # Migration needed - convert old INTEGER ratings to REAL scale
            migrate_ratings_scale(conn)
        
        s.execute(text("""
            CREATE TABLE IF NOT EXISTS ratings (
                id TEXT PRIMARY KEY,
                image_id TEXT NOT NULL,
                rating REAL NOT NULL,
                user_identifier TEXT NOT NULL,
                timestamp DATETIME NOT NULL
            );
        """))
        s.commit()

def migrate_ratings_scale(conn):
    """Migrates existing ratings from 1-100 scale to 1-10 scale."""
    with conn.session as s:
        # Create new table with REAL type
        s.execute(text("""
            CREATE TABLE IF NOT EXISTS ratings_new (
                id TEXT PRIMARY KEY,
                image_id TEXT NOT NULL,
                rating REAL NOT NULL,
                user_identifier TEXT NOT NULL,
                timestamp DATETIME NOT NULL
            );
        """))
        
        # Convert and copy data: divide positive ratings by 10, keep special values (-1, -2)
        s.execute(text("""
            INSERT INTO ratings_new (id, image_id, rating, user_identifier, timestamp)
            SELECT id, image_id, 
                   CASE 
                       WHEN rating > 0 THEN ROUND(rating / 10.0, 1)
                       ELSE rating 
                   END as rating,
                   user_identifier, timestamp
            FROM ratings
        """))
        
        # Replace old table
        s.execute(text("DROP TABLE ratings"))
        s.execute(text("ALTER TABLE ratings_new RENAME TO ratings"))
        s.commit()

def save_rating(conn, image_id, rating, user_identifier):
    """Saves a new rating to the database using the provided connection."""
    with conn.session as s:
        s.execute(
            text("INSERT INTO ratings (id, image_id, rating, user_identifier, timestamp) VALUES (:id, :image_id, :rating, :user_identifier, :timestamp)"),
            params=dict(
                id=str(uuid.uuid4()),
                image_id=image_id,
                rating=rating,
                user_identifier=user_identifier,
                timestamp=datetime.now()
            )
        )
        s.commit()

def get_rated_images(conn, user_identifier):
    """
    Fetches a list of image IDs that have already been rated or skipped 
    by a specific user.
    """
    with conn.session as s:
        result = s.execute(
            text("SELECT image_id FROM ratings WHERE user_identifier = :user_identifier"),
            params=dict(user_identifier=user_identifier)
        ).fetchall()
    return [row.image_id for row in result]

def get_all_ratings(conn):
    """Fetches all ratings from the database."""
    with conn.session as s:
        result = s.execute(text("SELECT * FROM ratings ORDER BY timestamp DESC")).fetchall()
    return result

def get_flagged_images(conn):
    """Fetches all images that have been flagged (rating = -2)."""
    with conn.session as s:
        result = s.execute(text("SELECT DISTINCT image_id FROM ratings WHERE rating = -2")).fetchall()
    return [row.image_id for row in result]

def get_image_statistics(conn):
    """Get statistics for each image including average rating, count, and controversy score."""
    with conn.session as s:
        result = s.execute(text("""
            SELECT 
                image_id,
                COUNT(*) as total_ratings,
                COUNT(CASE WHEN rating > 0 THEN 1 END) as valid_ratings,
                COUNT(CASE WHEN rating = -1 THEN 1 END) as skips,
                COUNT(CASE WHEN rating = -2 THEN 1 END) as flags,
                AVG(CASE WHEN rating > 0 THEN rating END) as avg_rating,
                MIN(CASE WHEN rating > 0 THEN rating END) as min_rating,
                MAX(CASE WHEN rating > 0 THEN rating END) as max_rating
            FROM ratings 
            GROUP BY image_id
            ORDER BY total_ratings DESC
        """)).fetchall()
    return result

def get_user_statistics(conn):
    """Get statistics for each user to identify potential data quality issues."""
    with conn.session as s:
        result = s.execute(text("""
            SELECT 
                user_identifier,
                COUNT(*) as total_submissions,
                COUNT(CASE WHEN rating > 0 THEN 1 END) as valid_ratings,
                COUNT(CASE WHEN rating = -1 THEN 1 END) as skips,
                COUNT(CASE WHEN rating = -2 THEN 1 END) as flags,
                AVG(CASE WHEN rating > 0 THEN rating END) as avg_rating,
                MIN(timestamp) as first_rating,
                MAX(timestamp) as last_rating
            FROM ratings 
            GROUP BY user_identifier
            ORDER BY total_submissions DESC
        """)).fetchall()
    return result

def get_top_and_bottom_images(conn):
    """Get the top 3 most popular and bottom 3 least popular images based on average ratings."""
    with conn.session as s:
        # Get top 3 most popular images
        top_result = s.execute(text("""
            SELECT 
                image_id,
                AVG(CASE WHEN rating > 0 THEN rating END) as avg_rating,
                COUNT(CASE WHEN rating > 0 THEN 1 END) as valid_ratings
            FROM ratings 
            WHERE rating > 0
            GROUP BY image_id
            HAVING COUNT(CASE WHEN rating > 0 THEN 1 END) >= 2
            ORDER BY avg_rating DESC
            LIMIT 3
        """)).fetchall()
        
        # Get bottom 3 least popular images
        bottom_result = s.execute(text("""
            SELECT 
                image_id,
                AVG(CASE WHEN rating > 0 THEN rating END) as avg_rating,
                COUNT(CASE WHEN rating > 0 THEN 1 END) as valid_ratings
            FROM ratings 
            WHERE rating > 0
            GROUP BY image_id
            HAVING COUNT(CASE WHEN rating > 0 THEN 1 END) >= 2
            ORDER BY avg_rating ASC
            LIMIT 3
        """)).fetchall()
        
    return top_result, bottom_result

def cleanup_test_users(conn, pattern, exact_match=False):
    """Admin function to clean up test users based on username pattern."""
    with conn.session as s:
        if exact_match:
            # Exact case-sensitive match
            users_to_delete = s.execute(
                text("SELECT DISTINCT user_identifier FROM ratings WHERE user_identifier = :pattern"),
                params=dict(pattern=pattern)
            ).fetchall()
            
            if users_to_delete:
                # Delete all ratings from exact matching users
                result = s.execute(
                    text("DELETE FROM ratings WHERE user_identifier = :pattern"),
                    params=dict(pattern=pattern)
                )
                s.commit()
                return len(users_to_delete), result.rowcount
            else:
                return 0, 0
        else:
            # Original case-insensitive pattern matching
            users_to_delete = s.execute(
                text("SELECT DISTINCT user_identifier FROM ratings WHERE user_identifier LIKE :pattern"),
                params=dict(pattern=f"%{pattern}%")
            ).fetchall()
            
            if users_to_delete:
                # Delete all ratings from matching users
                result = s.execute(
                    text("DELETE FROM ratings WHERE user_identifier LIKE :pattern"),
                    params=dict(pattern=f"%{pattern}%")
                )
                s.commit()
                return len(users_to_delete), result.rowcount
            else:
                return 0, 0

def get_all_users(conn):
    """Get all unique users for admin review."""
    with conn.session as s:
        result = s.execute(text("""
            SELECT 
                user_identifier,
                COUNT(*) as total_ratings,
                MIN(timestamp) as first_rating,
                MAX(timestamp) as last_rating
            FROM ratings 
            GROUP BY user_identifier
            ORDER BY first_rating DESC
        """)).fetchall()
    return result

def undo_last_rating(conn, user_identifier):
    """Undo the most recent rating by a specific user."""
    with conn.session as s:
        # Get the most recent rating by this user
        last_rating = s.execute(text("""
            SELECT id, image_id, rating FROM ratings 
            WHERE user_identifier = :user_identifier 
            ORDER BY timestamp DESC 
            LIMIT 1
        """), params=dict(user_identifier=user_identifier)).fetchone()
        
        if last_rating:
            # Delete the most recent rating
            s.execute(text("""
                DELETE FROM ratings WHERE id = :rating_id
            """), params=dict(rating_id=last_rating.id))
            s.commit()
            return last_rating.image_id, last_rating.rating
        else:
            return None, None 