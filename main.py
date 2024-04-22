import disnake
from disnake.ext import commands
from config import DISCORD_BOT_TOKEN
import small_commands
import small_commands_with_db
import search_thread_command
from active_threads_command import ActiveThreadsManager
import welcome_message_command
import logging  # Importing logging module
import search_review_command


# Set up basic configuration for logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

default_intents = disnake.Intents.default()
default_intents.members = True
default_intents.presences = True
default_intents.message_content = True

# bot = commands.InteractionBot()
# bot = commands.Bot("!")
bot = commands.Bot(command_prefix=commands.when_mentioned, intents=default_intents)

@bot.event
async def on_ready():
    print("Le bot est prêt")
    logging.info(f'Logged in as {bot.user}')
    active_threads_manager = ActiveThreadsManager(bot)
    logging.info('ActiveThreadsManager instance created.')

@bot.event
async def on_member_join(member: disnake.Member):
    print("on_member_join done")
    await welcome_message_command.send_welcome_message(member)

@bot.listen("on_thread_create")
async def adding_modos(thread):
    await small_commands.adding_modos(thread, bot)


# Register commands from small_commands.py
@bot.slash_command(
    name="randomdle",
    description="Nul besoin de jouer pour gagner!"
)
async def randomdle_command(inter: disnake.ApplicationCommandInteraction):
    await small_commands.randomdle(inter)


@bot.slash_command(
    name="build_the_list",
    description="Qui pourra remplacer le besoin par l'envie"
)
async def buildthelist_command(inter: disnake.ApplicationCommandInteraction):
    await small_commands.buildthelist(inter)


@bot.slash_command(
    name="up",
    description="Aller au 1er message de ce fil"
)
async def up_command(inter: disnake.ApplicationCommandInteraction):
    await small_commands.up(inter, bot)


@bot.slash_command(
    name="dice", 
    description="Lancer x dés à y faces."
)
async def roll_dice_command(inter, dés: int, faces: int):
    await small_commands.roll_dice(inter, dés, faces)


@bot.slash_command(
    name="achievement",
    description="Offrir un succès"
)
async def achievement(ctx: disnake.ApplicationCommandInteraction, text: str):
    await small_commands.achievement(ctx, text)


@bot.slash_command(
    name="count_members",
    description="Compter le nombre de membres du serveur"
)
async def member_count_command(inter: disnake.ApplicationCommandInteraction):
    await small_commands.member_count(inter)


@bot.slash_command(
    name="pin_toggle", 
    description="Pin or Unpin a message by its ID, only for SOJ_GO role"
)
async def pin_toggle(ctx: disnake.ApplicationCommandInteraction, message_id: str):
    await small_commands.togglepin_message(ctx, message_id)


# Register commands from search_thread_command.py
@bot.slash_command(
    name="search", 
    description="Search for threads, reviews, or episodes."
)
async def search(inter: disnake.ApplicationCommandInteraction):
    pass

@search.sub_command(    
    name="thread",
    description="Recherche d'un fil"
)
async def search_thread(inter: disnake.ApplicationCommandInteraction, expression: str):
    await search_thread_command.search_thread(inter, bot, expression)


# Command to search reviews
@search.sub_command(
    name="review",
    description="Pour trouver un test dans des magazines d'antan"
)
async def search_review(inter: disnake.ApplicationCommandInteraction, expression: str):
    await search_review_command.review_search(inter, expression)


# Register commands from small_commands_with_db.py
@bot.slash_command(
    name="deaf_test_infinite",
    description="Afficher l'image d'un jeu"
)
async def dti_command(inter: disnake.ApplicationCommandInteraction):
    await small_commands_with_db.display_image(inter, bot)

@bot.listen("on_button_click")
async def dti_button(inter: disnake.ApplicationCommandInteraction):
    await small_commands_with_db.button_callback(inter, bot)



# #############################################################################################
bot.run(DISCORD_BOT_TOKEN)
