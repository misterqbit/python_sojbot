from datetime import datetime, timedelta, timezone
from dateutil import tz
from disnake import Guild
from disnake.ext import commands, tasks
from tools.text_managers import read_yaml

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
        self.api_call_count = 0  # Initialize the API call counter here
        self.refresh_open_threads_list.start()

    @staticmethod
    def read_settings():
        return read_yaml('config/active_threads.yml')

    def initialize_run(self):
        self.date = datetime.now(tz=timezone.utc)
        self.settings = self.read_settings()

############################################################### Main function with 1 hour recurrent call
    @tasks.loop(hours=2)
    async def refresh_open_threads_list(self):
        self.initialize_run()
        await self.collect_channels_and_threads()
        self.build_message_list()
        await self.update_active_threads_channel()

        # Print performance and API call count to the console
        print(f"API Calls made: {self.api_call_count}")
        self.api_call_count = 0  # Reset counter after reporting
        
##############################################################

    async def collect_channels_and_threads(self):
        await self.get_threads_info()
        self.build_channels_and_threads_list()

    async def get_threads_info(self):
        self.threads = []
        threads_raw = await self.guild.active_threads()
        self.api_call_count += 1  # Increment API call count
        for thread in threads_raw:
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

    async def get_thread_archive_date(self, thread):
        up_timestamp = thread.archive_timestamp
        self.api_call_count += 1  # Increment API call count
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
            self.api_call_count += 1  # Increment API call count
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
        """

    def add_channel_and_threads_to_messages(self, channel_and_threads):
        # self.complete_last_message('\n\n\n')
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
            self.api_call_count += 1  # Increment API call count
            await message.delete()

    async def send_new_messages(self):
        for message in self.messages:
            await self.channel_to_update.send(message)
