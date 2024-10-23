from datetime import datetime, timedelta, timezone
from dateutil import tz
from disnake import Guild
from disnake.ext import commands, tasks
from tools.text_managers import read_yaml
import mysql.connector
from config import DB_host, DB_username, DB_password, DB_name

def get_db_connection():
    try:
        connection = mysql.connector.connect(
            host=DB_host,
            user=DB_username,
            password=DB_password,
            database=DB_name,
            charset= 'utf8mb4',  # Specify the charset
            collation= 'utf8mb4_general_ci',  # Specify a compatible collation
            connection_timeout=10  # Set a reasonable timeout value
        )
        return connection
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None

class ActiveThreadsManager:
    def __init__(self, bot):
        self.bot = bot
        self.guild = self.bot.guilds[0]
        self.settings = self.read_settings()
        self.channel_to_update = self.bot.get_channel(941250672811212810)
        self.date = datetime.now(tz=timezone.utc)
        self.threads = []
        self.channels_and_threads_dictionaries = []
        self.instructions = ''
        self.messages = ['']
        self.api_call_count = 0
        self.refresh_open_threads_list.start()

    @staticmethod
    def read_settings():
        return read_yaml('config/active_threads.yml')


##### LEVEL 0
    @tasks.loop(hours=1)
    async def refresh_open_threads_list(self):
        self.initialize_run()
        await self.collect_channels_and_threads()
        self.build_message_list()
        await self.update_active_threads_channel()

        print(f"API Calls made: {self.api_call_count}")
        self.api_call_count = 0
    
    @tasks.loop(hours=168)  # Run once a week
    async def delete_old_messages_from_db(self):
        db = get_db_connection()
        if not db:
            print("Failed to connect to the database.")
            return
        cursor = db.cursor()
        try:
            query = """
            DELETE FROM messages
            WHERE message_time < NOW() - INTERVAL 2 MONTH;
            """
            cursor.execute(query)
            db.commit()  # Commit the changes to the database
            print("Deleted messages older than 2 months.")
        except mysql.connector.Error as err:
            print(f"Database error: {err}")
        finally:
            cursor.close()
            db.close()

##### LEVEL 1
    def initialize_run(self):
        self.date = datetime.now(tz=timezone.utc)
        self.settings = self.read_settings()

    async def collect_channels_and_threads(self):
        await self.get_threads_info()
        await self.count_messages_last_6_hours()
        self.build_channels_and_threads_list()

    def build_message_list(self):
        self.update_instructions_string()
        self.messages = [self.instructions]
        # Include channels
        for channel_and_threads in self.channels_and_threads_dictionaries:
            self.add_channel_and_threads_to_messages(channel_and_threads)
        # Optionally, sort by message count
        self.channels_and_threads_dictionaries.sort(key=lambda x: x.get("message_count", 0), reverse=True)

    async def update_active_threads_channel(self):
        await self.delete_old_messages()
        await self.send_new_messages()

##### LEVEL 2
    async def get_threads_info(self):
        self.threads = []
        threads_raw = await self.guild.active_threads()
        self.api_call_count += 1  
        for thread in threads_raw:
            thread_dict = {
                "channel": thread.parent,
                "mention": thread.mention,
                "id": thread.id,
                "creation_date": thread.created_at,
                "up_date": thread.archive_timestamp,
                "archive_date": await self.get_thread_archive_date(thread)
            }
            thread_dict["is_dead"] = thread_dict["archive_date"] < datetime.now(tz=timezone.utc)
            thread_dict["excluded"] = thread.parent_id == 1218292569209831514
            self.threads.append(thread_dict)

    async def count_messages_last_6_hours(self):
        db = get_db_connection()
        if not db:
            print("Failed to connect to the database.")
            return

        cursor = db.cursor()
        try:
            # Query to count messages for both channels and threads in the last 6 hours
            query = """
            SELECT channel_id, COUNT(*) AS message_count
            FROM messages
            WHERE message_time >= UTC_TIMESTAMP() - INTERVAL 6 HOUR
            GROUP BY channel_id;
            """
            cursor.execute(query)
            result = cursor.fetchall()

            if not result:
                print("No messages found in the last 6 hours.")

            # Map message counts to the corresponding channels/threads
            message_counts = {row[0]: row[1] for row in result}

            # Update message counts for threads
            for thread in self.threads:
                thread_id = thread["id"]
                thread["message_count"] = message_counts.get(thread_id, 0)

            # Get channels and their message counts
            for channel in self.guild.text_channels:
                channel_id = channel.id
                if channel_id not in message_counts:
                    continue
                channel_dict = {
                    "channel": channel,
                    "mention": channel.mention,
                    "id": channel_id,
                    "message_count": message_counts[channel_id]
                }
                self.channels_and_threads_dictionaries.append(channel_dict)

        except mysql.connector.Error as err:
            print(f"Database error: {err}")
        finally:
            cursor.close()
            db.close()

    def build_channels_and_threads_list(self):
        self.channels_and_threads_dictionaries = []
        while self.threads:
            channel = self.threads[0]["channel"]
            threads_channel = [thread for thread in self.threads if thread["channel"] == channel]
            channel_dictionary = {
                "channel": channel,
                "threads": [thread for thread in threads_channel if not thread["is_dead"] and not thread["excluded"]]
            }

            if len(channel_dictionary["threads"]) > 0:
                self.channels_and_threads_dictionaries.append(channel_dictionary)

            for thread in threads_channel:
                self.threads.remove(thread)

    def add_channel_and_threads_to_messages(self, channel_and_threads):
        self.complete_last_message('\n\n\n')
        self.complete_last_message(channel_and_threads["channel"].mention)

        # If there are threads, handle them
        if "threads" in channel_and_threads:
            for thread in channel_and_threads["threads"]:
                self.add_thread_to_messages(thread)
        else:
            # Handle channel message count
            message_count = channel_and_threads.get("message_count", 0)   #NOT WORKING!!
            if message_count > 0:
                self.complete_last_message(f" ({message_count})")

    async def delete_old_messages(self):
        async for message in self.channel_to_update.history(limit=None):
            self.api_call_count += 1  
            await message.delete()

    async def send_new_messages(self):
        for message in self.messages:
            await self.channel_to_update.send(message)

##### LEVEL 3
    async def get_thread_archive_date(self, thread):
        up_timestamp = thread.archive_timestamp
        self.api_call_count += 1  
        try:
            last_message = await self.get_thread_last_message_date(thread)
        except:
            last_message = up_timestamp
        last_activity = max(last_message, up_timestamp)
        return last_activity + timedelta(minutes=thread.auto_archive_duration)


    def complete_last_message(self, string_to_add):
        last_message_length = len(self.messages[-1])
        string_to_add_length = len(string_to_add)

        if last_message_length + string_to_add_length <= self.settings["max_message_length"]:
            self.messages[-1] += string_to_add
        else:
            self.messages.append(string_to_add)

    def add_thread_to_messages(self, thread):
        thread_string = f"\n> {thread['mention']}"
        thread_string += self.add_new_emoji_if_required(thread)
        thread_string += self.add_up_emoji_if_required(thread)
        thread_string += self.add_dying_emoji_if_required(thread)
        thread_string += self.add_message_count_if_required(thread)
        self.complete_last_message(thread_string)


##### LEVEL 4
    async def get_thread_last_message_date(self, thread):
        message_list = []
        async for item in thread.history(limit=1):
            self.api_call_count += 1  
            message_list.append(item)
        last_message = message_list[0] if message_list else None
        return last_message.created_at if last_message else thread.archive_timestamp

    def add_new_emoji_if_required(self, thread):
        parameters = self.settings["new"]
        hours_since_creation = (self.date - thread["creation_date"]).total_seconds() / 3600
        hours_for_emoji = parameters["hours"]
        return f" :{parameters['emoji']}:" if hours_since_creation < hours_for_emoji else ""

    def add_up_emoji_if_required(self, thread):
        parameters = self.settings["up"]
        thread_is_new = thread["up_date"] + timedelta(minutes=-5) < thread["creation_date"]
        hours_since_up = (self.date - thread["up_date"]).total_seconds() / 3600
        hours_for_emoji = parameters["hours"]
        return f" :{parameters['emoji']}:" if hours_since_up < hours_for_emoji and not thread_is_new else ""

    def add_dying_emoji_if_required(self, thread):
        parameters = self.settings["dying"]
        hours_until_archive = (thread["archive_date"] - self.date).total_seconds() / 3600
        hours_for_emoji = parameters["hours"]
        return f" :{parameters['emoji']}:" if hours_until_archive < hours_for_emoji else ""

    def add_message_count_if_required(self, thread):
        message_count = thread.get("message_count", 0)
        if message_count > 30:
            return " :fire: (30+)"
        elif message_count > 0:
            return f" ({message_count})"
        return ""

##### LEVEL 2
    def update_instructions_string(self):
        self.instructions = f"""
        Au {self.date.astimezone(tz=tz.gettz('Europe/Paris')).strftime("%d/%m/%Y, %H:%M:%S")} (heure de Paris), voici la liste des fils actifs sur ce serveur Discord.

        **__Légende :__**
        > :{self.settings["new"]["emoji"]}: = {self.settings["new"]["description"]}
        > :{self.settings["up"]["emoji"]}: = {self.settings["up"]["description"]}
        > :{self.settings["dying"]["emoji"]}: = {self.settings["dying"]["description"]}
        > (nombre de messages écrits dans les 6 dernières heures)
        """
