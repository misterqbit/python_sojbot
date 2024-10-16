import disnake
from disnake.ext import commands, tasks
from config import DISCORD_BOT_TOKEN
import small_commands
import deaftest_infinite
import sojdle
import search_thread_command
import search_review_command
import search_episode_command
from active_threads_command import ActiveThreadsManager
import welcome_message_command
import logging  # Importing logging module
import birthday_checker
#import podcast
from twitch import app, disnake_client

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
    if not birthday_greetings_task.is_running():
        birthday_greetings_task.start()

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
    name="début",
    description="Aller au tout 1er message de ce fil"
)
async def up_command(inter: disnake.ApplicationCommandInteraction):
    await small_commands.up(inter, bot)


@bot.slash_command(
    name="dé", 
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
    name="compter_membres",
    description="Compter le nombre de membres du serveur"
)
async def member_count_command(inter: disnake.ApplicationCommandInteraction):
    await small_commands.member_count(inter)


@bot.slash_command(
    name="pin_toggle", 
    description="Pin or Unpin a message by its ID, only for SOJ_GO role",
    permissions="SOJ_GO"
)
async def pin_toggle(ctx: disnake.ApplicationCommandInteraction, message_id: str):
    await small_commands.togglepin_message(ctx, message_id)

"""
@bot.slash_command(
    name="top_dt", 
    description="liste des meilleures deaf test de ce fil",
    permissions="Modération"
)
async def top_images(ctx: disnake.ApplicationCommandInteraction, thread_id: str, reaction_nbr_max: int, reaction_nbr_min: int):
    await small_commands.find_top_images(ctx, thread_id, bot, reaction_nbr_max, reaction_nbr_min)
"""

"""
@bot.slash_command(
    name="sojdle", 
    description="wordle des jeux chroniqués dans SOJ",
    permissions="Modération"
)
async def launch_sojdle(inter: disnake.ApplicationCommandInteraction, answer: str):
    await sojdle.sojdle(inter, answer, bot)
"""

"""
@bot.slash_command(name="startpodcast", description="Start playing the podcast", permissions="Modération")
async def startpodcast(ctx):
    await podcast.play(ctx)
"""
# from birthday_checker.py
# Register the add_birthday slash command
@bot.slash_command(name="anniversaire", description="Enregistrez votre anniversaire (format : MM-JJ)")
async def add_birthday(inter: disnake.ApplicationCommandInteraction, birthday: str):
    await birthday_checker.add_birthday_command(inter, birthday)

# Task that runs every day to check and greet users
@tasks.loop(hours=24)
async def birthday_greetings_task():
    await birthday_checker.send_birthday_greetings(bot)


# Register commands from search_thread_command.py
@bot.slash_command(
    name="chercher", 
    description="Search for threads, reviews, or episodes."
)
async def search(inter: disnake.ApplicationCommandInteraction):
    pass

@search.sub_command(    
    name="fil",
    description="Recherche d'un fil"
)
async def search_thread(inter: disnake.ApplicationCommandInteraction, expression: str):
    await search_thread_command.search_thread(inter, bot, expression)


# Command to search reviews
@search.sub_command(
    name="test",
    description="Recherche d'un test de jv dans des magazines d'antan (tilt, etc.)"
)
async def search_review(inter: disnake.ApplicationCommandInteraction, expression: str):
    await search_review_command.review_search(inter, expression)


# Command to search for a music of video game
@search.sub_command(
    name="musique",
    description="Recherche d'une musique de jv dans les démons du midi"
)
async def search_music(inter, game_title: str):
    await search_episode_command.search_music(inter, str)

# Register commands from small_commands_with_file.py
@bot.slash_command(
    name="deaf_test_infinite",
    description="Afficher l'image d'un jeu"
)
async def dti_command(inter: disnake.ApplicationCommandInteraction):
    await deaftest_infinite.display_image(inter, bot)

@bot.listen("on_button_click")
async def dti_button(inter: disnake.ApplicationCommandInteraction):
    await deaftest_infinite.button_callback(inter, bot)

# SOJDLE command from sojdle.py
@bot.slash_command(name="sojdle", description="wordle mais avec des titres de jv chroniqués ds SOJ")
async def sojdleguess(ctx: disnake.ApplicationCommandInteraction, titre: str):
    MAX_GUESS_LENGTH = 50  # Set a maximum guess length
    if len(titre) > MAX_GUESS_LENGTH:
        await ctx.send(f"⚠️ Votre proposition est trop longue! Merci de bien vouloir la limiter à {MAX_GUESS_LENGTH} caractères.")
        return
    else:
        if not (ctx.channel_id == 944567098502438932):
            await ctx.send(content="Cette commande est à utiliser dans le fil SOJDLE")
            return
        else: 
            await sojdle.guess(ctx, titre)

# #############################################################################################
bot.run(DISCORD_BOT_TOKEN)
