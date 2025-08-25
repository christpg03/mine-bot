"""
Migration script to add username column to users table.
Run this script once to update your existing database schema.
"""

import sqlite3
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def migrate_database():
    """
    Add username column to users table if it doesn't exist.
    """
    # Database path
    db_path = Path(__file__).parent / "mine_bot.db"

    if not db_path.exists():
        logger.warning(
            f"Database file {db_path} doesn't exist. This migration will be applied when the database is first created."
        )
        return

    conn = None
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check if username column already exists
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]

        if "username" in columns:
            logger.info(
                "Username column already exists in users table. Migration not needed."
            )
        else:
            logger.info("Adding username column to users table...")

            # Add username column
            cursor.execute(
                """
                ALTER TABLE users 
                ADD COLUMN username VARCHAR(255) DEFAULT NULL
            """
            )

            # Create index on username for performance
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_users_username 
                ON users(username)
            """
            )

            conn.commit()
            logger.info(
                "✅ Successfully added username column and index to users table."
            )

        conn.close()

    except sqlite3.Error as e:
        logger.error(f"Database error during migration: {e}")
        if conn:
            try:
                conn.rollback()
                conn.close()
            except:
                pass
        raise
    except Exception as e:
        logger.error(f"Unexpected error during migration: {e}")
        if conn:
            try:
                conn.close()
            except:
                pass
        raise


if __name__ == "__main__":
    migrate_database()
