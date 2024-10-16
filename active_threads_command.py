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

    async def collect_channels_and_threads(self):
        await self.get_threads_info()
        self.build_channels_and_threads_list()
    
    async def get_threads_info(self):
        self.threads = []
        threads_raw = await self.guild.active_threads()
        for thread in threads_raw:
            thread_dict = {}  # Define thread_dict here
            thread_id = str(thread.id)  # Convert thread ID to string
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

