import disnake
from disnake.ext import commands
from db import get_db_connection, insert_message, update_emoji_count

# Excluded channel IDs
EXCLUDED_CHANNELS = {1047156993665806386}  # Add any other channel IDs to exclude here


# Function to register events
def register_events(bot: commands.Bot):
    @bot.event
    async def on_message(message):
        # if message.author.bot:
        #     return

        # Skip processing messages only if they are from bots AND in excluded channels
        if message.author.bot and message.channel.id in EXCLUDED_CHANNELS:
            return

        # Get database connection (synchronous, no await)
        db = get_db_connection()

        if db is None:
            print("Database connection failed.")
            return

        # Insert the message data into the database
        insert_message(
            message.id,
            message.author.id,
            message.author.name,
            message.channel.id,
            message.channel.name,
            None,
            None,
            message.created_at
        )

        # Allow the bot to continue processing commands
        await bot.process_commands(message)

