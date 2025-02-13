import mysql.connector
import logging
from config import DB_host, DB_username, DB_password, DB_name
from datetime import datetime, timezone

# Initialize the logger
logger = logging.getLogger("bot")

# Function to connect to the database
def get_db_connection():
    try:
        db = mysql.connector.connect(
            host=DB_host,
            user=DB_username,
            password=DB_password,
            database=DB_name,
            charset= 'utf8mb4',  # Specify the charset
            collation= 'utf8mb4_general_ci',  # Specify a compatible collation
            connection_timeout=10  # Set a reasonable timeout value
        )
        return db
    except mysql.connector.Error as err:
        logger.error(f"Failed to connect to the database: {err}")
        print(f"Error: {err}")
        return None


# Function to set up the database schema if necessary
def setup_database():
    db = get_db_connection()
    if db is None:
        logger.error("Database connection failed.")
        return

    try:
        cursor = db.cursor()

        # Check if the 'messages' table exists
        cursor.execute("""
        SELECT COUNT(*)
        FROM information_schema.tables
        WHERE table_name = 'messages'
        AND table_schema = DATABASE();
        """)
        result = cursor.fetchone()

        if result[0] == 0:
            # Create the 'messages' table if it doesn't exist
            cursor.execute("""
            CREATE TABLE messages (
                message_id BIGINT PRIMARY KEY,
                author_id BIGINT,
                author_username VARCHAR(255),
                channel_id BIGINT,
                channel_name VARCHAR(255),
                thread_id BIGINT NULL,
                thread_name VARCHAR(255) NULL,
                message_time DATETIME,
                emoji_count INT DEFAULT 0
            )
            """)
            db.commit()
            logger.info("Table 'messages' created successfully.")
        else:
            logger.info("Table 'messages' already exists. Skipping creation.")

    except mysql.connector.Error as e:
        logger.error(f"Failed to set up the database: {e}")
    finally:
        cursor.close()
        db.close()


# Insert a new message into the database
def insert_message(message_id, author_id, author_username, channel_id, channel_name, thread_id, thread_name, message_time):
    db = get_db_connection()
    if db is None:
        logger.error("Database connection failed.")
        return

    try:
        cursor = db.cursor()

         # Convert message_time to UTC
        if message_time.tzinfo is None:
            message_time = message_time.replace(tzinfo=timezone.utc)  # If naive, set it as UTC
        else:
            message_time = message_time.astimezone(timezone.utc)  # Convert to UTC if it has timezone info

        # Insert message data into the database
        query = """
        INSERT INTO messages (message_id, author_id, author_username, channel_id, channel_name, thread_id, thread_name, message_time, emoji_count)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (message_id, author_id, author_username, channel_id, channel_name, thread_id, thread_name, message_time, 0))
        db.commit()
        logger.info(f"Message {message_id} inserted into the database.")
        
    except mysql.connector.Error as e:
        logger.error(f"Failed to insert message: {e}")
    finally:
        cursor.close()
        db.close()


# Update the emoji count of a message
def update_emoji_count(message_id):
    db = get_db_connection()
    if db is None:
        logger.error("Database connection failed.")
        return

    try:
        cursor = db.cursor()

        # Update the emoji count for the message
        query = "UPDATE messages SET emoji_count = emoji_count + 1 WHERE message_id = %s"
        cursor.execute(query, (message_id,))
        db.commit()
        logger.info(f"Emoji count updated for message {message_id}.")
        
    except mysql.connector.Error as e:
        logger.error(f"Failed to update emoji count: {e}")
    finally:
        cursor.close()
        db.close()
