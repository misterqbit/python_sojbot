from datetime import datetime, timedelta, timezone
from dateutil import tz
from disnake import Guild
from disnake.ext import commands, tasks
from tools.text_managers import read_yaml
import os
import json

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
        self.refresh_open_threads_list.start()
        #self.last_message_file = "last_message_dates.json"
        #self.last_message_dates = self.load_last_message_dates()

    @staticmethod
    def read_settings():
        return read_yaml('config/active_threads.yml')

    def initialize_run(self):
        self.date = datetime.now(tz=timezone.utc)
        self.settings = self.read_settings()

############################################################### Main function with 1 hour recurrent call
    @tasks.loop(hours=1)
    async def refresh_open_threads_list(self):
        self.initialize_run()
        await self.collect_channels_and_threads()
        self.build_message_list()
        await self.update_active_threads_channel()
##############################################################
#    def load_last_message_dates(self):
#        if os.path.exists(self.last_message_file):
#            with open(self.last_message_file, "r") as f:
#                try:
#                    last_message_dates = json.load(f)
#                    # Convert datetime strings back to datetime objects
#                    return {thread_id: datetime.fromisoformat(date_string) for thread_id, date_string in last_message_dates.items()}
#                except (json.decoder.JSONDecodeError, ValueError):
#                    # Handle empty or malformed JSON file
#                    print("Handle empty or malformed JSON file")
#
#                    return {}
#        else:
#            return {}

    """
    def load_last_message_dates(self):
        if os.path.exists(self.last_message_file):
            try:
                with open(self.last_message_file, "r") as f:
                    last_message_dates = json.load(f)
                    # Convert datetime strings back to datetime objects
                    return {thread_id: datetime.fromisoformat(date_string) for thread_id, date_string in last_message_dates.items()}
            except (json.decoder.JSONDecodeError, ValueError) as e:
                # Handle empty or malformed JSON file
                print(f"Error loading JSON data from file: {e}")
                return {}
            except (FileNotFoundError, PermissionError) as e:
                # Handle file-related errors
                print(f"Error accessing or reading file: {e}")
                return {}
        else:
            return {}
    """

    """
    def save_last_message_date(self, thread_id, last_message_date):
        self.last_message_dates[int(thread_id)] = last_message_date.isoformat() # Convert to ISO 8601 format
        with open(self.last_message_file, "w") as f:
            json.dump(self.last_message_dates, f, default=str)  # Use default=str to serialize datetimes as strings
    """


    async def collect_channels_and_threads(self):
        await self.get_threads_info()
        self.build_channels_and_threads_list()
    """
    async def get_threads_info(self):
        self.threads = []
        threads_raw = await self.guild.active_threads()

        for thread in threads_raw:
            thread_id = str(thread.id)

            last_message_date = self.last_message_dates.get(thread_id)

            if not last_message_date:
                last_message_date = await self.get_thread_last_message_date(thread)
                self.save_last_message_date(thread_id, last_message_date)
            else:
                messages_last_hour = await self.count_messages_last_hour(thread, last_message_date)
                # Add message count to thread dictionary
                thread_dict["messages_last_hour"] = messages_last_hour

            thread_dict = {
                "channel": thread.parent,
                #"channel_id": thread.parent_id,
                "mention": thread.mention,
                "creation_date": thread.created_at,
                "up_date": thread.archive_timestamp,
                "archive_date": await self.get_thread_archive_date(thread)
            }
            thread_dict["is_dead"] = thread_dict["archive_date"] < datetime.now(tz=timezone.utc)
            #parent_id = thread.parent_id
            thread_dict["excluded"] = thread.parent_id == 1218292569209831514 #Excluding threads of channel early-access-sojfest

            self.threads.append(thread_dict)
    """
    async def get_threads_info(self):
        self.threads = []
        threads_raw = await self.guild.active_threads()
        for thread in threads_raw:
            thread_dict = {}  # Define thread_dict here
            thread_id = str(thread.id)  # Convert thread ID to string

            """
            if thread_id in self.last_message_dates:
                last_message_date = self.last_message_dates[thread_id]
                messages_last_hour = await self.count_messages_last_hour(thread, last_message_date)
                                
                # Define the thread dictionary
                thread_dict = {
                    "channel": thread.parent,
                    "mention": thread.mention,
                    "creation_date": thread.created_at,
                    "up_date": thread.archive_timestamp,
                    "archive_date": await self.get_thread_archive_date(thread),
                    "messages_last_hour": messages_last_hour
                }
                thread_dict["is_dead"] = thread_dict["archive_date"] < datetime.now(tz=timezone.utc)
                thread_dict["excluded"] = thread.parent_id == 1218292569209831514 #Excluding threads of channel early-access-sojfest

                self.threads.append(thread_dict)
            else:
                print("Thread ID does not exist in last_message_dates dictionary")
                messages_last_hour = 0
                last_message_date = await self.get_thread_last_message_date(thread)
                self.save_last_message_date(thread_id, last_message_date)
                # Define the thread dictionary
                thread_dict = {
                    "channel": thread.parent,
                    "mention": thread.mention,
                    "creation_date": thread.created_at,
                    "up_date": thread.archive_timestamp,
                    "archive_date": await self.get_thread_archive_date(thread),
                    "messages_last_hour": messages_last_hour
                }
                thread_dict["is_dead"] = thread_dict["archive_date"] < datetime.now(tz=timezone.utc)
                thread_dict["excluded"] = thread.parent_id == 1218292569209831514 #Excluding threads of channel early-access-sojfest

                self.threads.append(thread_dict)
            """
            messages_last_hour = await self.count_messages_last_hour(thread)
            # Define the thread dictionary
            thread_dict = {
                "channel": thread.parent,
                "mention": thread.mention,
                "creation_date": thread.created_at,
                "up_date": thread.archive_timestamp,
                "archive_date": await self.get_thread_archive_date(thread),
                "messages_last_hour": messages_last_hour
                }
            thread_dict["is_dead"] = thread_dict["archive_date"] < datetime.now(tz=timezone.utc)
            thread_dict["excluded"] = thread.parent_id == 1218292569209831514 #Excluding threads of channel early-access-sojfest
            self.threads.append(thread_dict)

    """
    async def count_messages_last_hour(self, thread, last_message_date):
        # Count messages in the last hour
        messages_last_hour = int(0)
        previous_message_date = None
        previous_message_author = None
        # async for message in thread.history(after=last_message_date, limit=100):
        async for message in thread.history(limit=51):
            # Make the message's creation time timezone-aware (assuming it's in UTC)
            message_created_at = message.created_at.replace(tzinfo=timezone.utc)
            if message_created_at > (datetime.now(tz=timezone.utc) - timedelta(hours=6)):   # Messages des SIX (6) dernières heures
                current_message_date = message.created_at.replace(second=0, microsecond=0)  # Round down to the nearest minute
                current_message_author = message.author 
                if previous_message_author:
                    if previous_message_author != current_message_author:
                        pass
                    else:
                        if previous_message_date:
                            if current_message_date > previous_message_date:
                                pass
                            else:
                                continue
                        else:
                            previous_message_date = current_message_date
                else:
                    previous_message_author = current_message_author
                messages_last_hour += 1

        if messages_last_hour > 49:
            messages_last_hour = str("50+")
        return messages_last_hour
    """
    async def count_messages_last_hour(self, thread):
        # Count messages in the last hour
        messages_last_hour = int(0)
        previous_message_date = None
        previous_message_author = None
        async for message in thread.history(limit=51):
            # Make the message's creation time timezone-aware (assuming it's in UTC)
            message_created_at = message.created_at.replace(tzinfo=timezone.utc)
            if message_created_at > (datetime.now(tz=timezone.utc) - timedelta(hours=6)):   # Messages des SIX (6) dernières heures
                current_message_date = message.created_at.replace(second=0, microsecond=0)  # Round down to the nearest minute
                current_message_author = message.author 
                if previous_message_author:
                    if previous_message_author != current_message_author:
                        pass
                    else:
                        if previous_message_date:
                            if current_message_date > previous_message_date:
                                pass
                            else:
                                continue
                        else:
                            previous_message_date = current_message_date
                else:
                    previous_message_author = current_message_author
                messages_last_hour += 1

        #if messages_last_hour > 49:
        #    messages_last_hour = str("50+")
        return messages_last_hour

    async def get_thread_archive_date(self, thread):
        up_timestamp = thread.archive_timestamp
        try:
            last_message = await self.get_thread_last_message_date(thread)
        except:
            last_message = up_timestamp
        last_activity = max(last_message, up_timestamp)
        return last_activity + timedelta(minutes=thread.auto_archive_duration)

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

    async def get_thread_last_message_date(self, thread):
        message_list = []
        async for item in thread.history(limit=1):
            message_list.append(item)
        last_message = message_list[0]
        return last_message.created_at

    def build_message_list(self):
        self.update_instructions_string()
        self.messages = [self.instructions]
        for channel_and_threads in self.channels_and_threads_dictionaries:
            self.add_channel_and_threads_to_messages(channel_and_threads)

    def update_instructions_string(self):
        self.instructions = f"""
Au {self.date.astimezone(tz=tz.gettz('Europe/Paris')).strftime("%d/%m/%Y, %H:%M:%S")} (heure de Paris), voici la liste des fils actifs sur ce serveur Discord.

**__Légende :__**
> :{self.settings["new"]["emoji"]}: = {self.settings["new"]["description"]}
> :{self.settings["up"]["emoji"]}: = {self.settings["up"]["description"]}
> :{self.settings["dying"]["emoji"]}: = {self.settings["dying"]["description"]}
> (nombre de messages écrits dans les 6 dernières heures)
        """

    def add_channel_and_threads_to_messages(self, channel_and_threads):
        self.complete_last_message('\n\n\n')
        self.complete_last_message(channel_and_threads["channel"].mention)

        for thread in channel_and_threads["threads"]:
            self.add_thread_to_messages(thread)

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
        if "messages_last_hour" in thread:
            if thread['messages_last_hour'] > 0:
                if thread['messages_last_hour'] == 51:
                    thread_string += f" **(50+)** :fire:"
                else:    
                    thread_string += f" **({thread['messages_last_hour']})**"
        self.complete_last_message(thread_string)

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

    async def update_active_threads_channel(self):
        await self.delete_old_messages()
        await self.send_new_messages()

    async def delete_old_messages(self):
        async for message in self.channel_to_update.history(limit=None):
            await message.delete()

    async def send_new_messages(self):
        for message in self.messages:
            await self.channel_to_update.send(message)
