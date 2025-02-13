import disnake
from disnake.ext import commands
import mysql.connector
from config import DB_host, DB_username, DB_password, DB_name


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
    except mysql.connector.Error as e:
        print(f"[ERROR] Database connection failed: {e}")
        return None

# Database functions
def add_reaction(message_id, user_id):
    """Add a reaction record to the database."""
    db = get_db_connection()
    if not db:
        print("[ERROR] Failed to connect to the database.")
        return

    try:
        cursor = db.cursor()
        query = """
        INSERT IGNORE INTO reactions (message_id, user_id) VALUES (%s, %s)
        """
        cursor.execute(query, (message_id, user_id))
        db.commit()
    except mysql.connector.Error as e:
        print(f"[ERROR] Failed to add reaction: {e}")
    finally:
        cursor.close()
        db.close()

def count_unique_reactors(message_id):
    """Count unique reactors for a given message."""
    db = get_db_connection()
    if not db:
        print("[ERROR] Failed to connect to the database.")
        return 0

    try:
        cursor = db.cursor()
        query = """
        SELECT COUNT(DISTINCT user_id) FROM reactions WHERE message_id = %s
        """
        cursor.execute(query, (message_id,))
        result = cursor.fetchone()
        return result[0] if result else 0
    except mysql.connector.Error as e:
        print(f"[ERROR] Failed to count unique reactors: {e}")
        return 0
    finally:
        cursor.close()
        db.close()

def has_message_been_reposted(message_id):
    """Check if a message has already been reposted."""
    db = get_db_connection()
    if not db:
        print("[ERROR] Failed to connect to the database.")
        return True  # Assume true to prevent reposting

    try:
        cursor = db.cursor()
        query = """
        SELECT reposted FROM messages WHERE message_id = %s
        """
        cursor.execute(query, (message_id,))
        result = cursor.fetchone()
        return result[0] if result else False
    except mysql.connector.Error as e:
        print(f"[ERROR] Failed to check if message was reposted: {e}")
        return True
    finally:
        cursor.close()
        db.close()

def mark_message_as_reposted(message_id):
    """Mark a message as reposted in the database."""
    db = get_db_connection()
    if not db:
        print("[ERROR] Failed to connect to the database.")
        return

    try:
        cursor = db.cursor()
        query = """
        UPDATE messages SET reposted = TRUE WHERE message_id = %s
        """
        cursor.execute(query, (message_id,))
        db.commit()
    except mysql.connector.Error as e:
        print(f"[ERROR] Failed to mark message as reposted: {e}")
    finally:
        cursor.close()
        db.close()

# Reposting logic
async def repost_message(bot, message):
    REPOST_CHANNEL_ID = 1316021589573107822  # Replace with your target repost channel ID
    repost_channel = bot.get_channel(REPOST_CHANNEL_ID)

    if not repost_channel:
        print(f"[ERROR] Repost channel with ID {REPOST_CHANNEL_ID} not found.")
        return

    try:
        # Prepare the embed
        embed = disnake.Embed(
            #title="Message Populaire 🎉",
            title="Message : ",
            description=message.content or "[Pas de texte]",
            color=disnake.Color.gold(),
            timestamp=message.created_at,
        )
        #embed.add_field(name="Channel", value=message.channel.name, inline=True)
        #embed.add_field(name="Auteurice", value=message.author.name, inline=True)
        embed.add_field(
            name="Lien du Message : ",
            value=f"https://discord.com/channels/{message.guild.id}/{message.channel.id}/{message.id}",
            inline=False,
        )
        embed.set_footer(text="🚀")

        # Send the embed to the repost channel
        print(f"[TRY] Message ID {message.id} is going to be reposted.")
        await repost_channel.send(embed=embed)
        print(f"[SUCCESS] Message ID {message.id} reposted successfully.")
    except Exception as e:
        print(f"[ERROR] Failed to repost message ID {message.id}: {e}")

# Event handler for reactions
async def handle_reaction_add(bot, reaction, user):
    # Skip reactions by bots or in excluded channels
    EXCLUDED_CHANNELS = [930843194063716402, 902492905904693288]
    if reaction.message.channel.id in EXCLUDED_CHANNELS:
        return

    try:
        # Update the reactions table for tracking unique reactors
        add_reaction(reaction.message.id, user.id)

        # Count the number of unique reactors for this message
        reactor_count = count_unique_reactors(reaction.message.id)

        # Check if the threshold (7 unique reactors) is met ###############################################################
        if reactor_count >= 7:
            # Prevent duplicate reposts
            if has_message_been_reposted(reaction.message.id):
                print(f"[INFO] Message ID {reaction.message.id} has already been reposted.")
                return

            # Mark the message as reposted
            mark_message_as_reposted(reaction.message.id)

            # Repost the message
            await repost_message(bot, reaction.message)

    except Exception as e:
        print(f"[ERROR] Failed to handle reaction add: {e}")
