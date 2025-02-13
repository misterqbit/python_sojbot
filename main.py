import disnake
from disnake.ext import commands, tasks
from config import DISCORD_BOT_TOKEN
from config import DB_host, DB_username, DB_password, DB_name
import small_commands
import deaftest_infinite
import sojdle
#import openai_quiz
import search_thread_command
import search_review_command
import search_episode_command
from active_threads_command import ActiveThreadsManager
from readers_digest import handle_reaction_add
import welcome_message_command
import birthday_checker
from ecrans_forum_import import import_forum_data
# import discord_static_map
# Import event handlers and database setup from separate modules
from db import setup_database
from events import register_events
#import podcast
#from twitch import app, disnake_client
import requests
import time
import logging  # Importing logging module
from logging.handlers import RotatingFileHandler
import plots
import pandas as pd


###################################### Configure logging to file only (no console)
log_handler = RotatingFileHandler('bot.log', maxBytes=5*1024*1024, backupCount=5)
log_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
log_handler.setFormatter(formatter)

logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.handlers = []  # Clear existing handlers (removes console handler)
logger.addHandler(log_handler)
################################################################################


##################################### Bot initialization
default_intents = disnake.Intents.default()
default_intents.members = True
default_intents.presences = True
default_intents.message_content = True
default_intents.messages = True
default_intents.reactions = True

bot = commands.Bot(command_prefix=commands.when_mentioned, intents=default_intents)
################################################################################

@bot.event
async def on_ready():
    print("Le bot est prêt")
    logging.info(f'Logged in as {bot.user}')
    setup_database()  # Ensure database is set up when the bot is ready
    register_events(bot) # Register event handlers

    active_threads_manager = ActiveThreadsManager(bot)
    logging.info('ActiveThreadsManager instance created.')

    logging.info('Readers Digest instance created.')    

    if not birthday_greetings_task.is_running():
        birthday_greetings_task.start()


@bot.event
async def on_reaction_add(reaction, user):
    await handle_reaction_add(bot, reaction, user)


@bot.event
async def on_member_join(member: disnake.Member):
    try:
        print("on_member_join triggered")
        
        # Call the send_welcome_message function
        await send_welcome_message(member)
        logging.info(f"A welcome message has been sent to {member.name} ({member.id}).")

    except disnake.Forbidden:
        logging.warning(f"Cannot send welcome DM to {member.name} ({member.id}): DMs are disabled.")
    except Exception as e:
        logging.error(f"Error in on_member_join for {member.name} ({member.id}): {e}")


##################################### Register commands from small_commands.py
@bot.listen("on_thread_create")
async def adding_modos(thread):
    await small_commands.adding_modos(thread, bot)
    logging.info(f"A thread has been created and modos have been added")


@bot.slash_command(
    name="randomdle",
    description="Nul besoin de jouer pour gagner!")
async def randomdle_command(ctx: disnake.ApplicationCommandInteraction):
    await small_commands.randomdle(ctx)
    logging.info(f"Command 'randomdle' invoked by {ctx.author} in {ctx.guild}/{ctx.channel}")     


@bot.slash_command(
    name="build_the_list",
    description="Qui pourra remplacer le besoin par l'envie")
async def buildthelist_command(ctx: disnake.ApplicationCommandInteraction):
    await small_commands.buildthelist(ctx)
    logging.info(f"Command 'build_the_list' invoked by {ctx.author} in {ctx.guild}/{ctx.channel}")


@bot.slash_command(
    name="début",
    description="Aller au tout 1er message de ce fil")
async def up_command(ctx: disnake.ApplicationCommandInteraction):
    await small_commands.up(ctx, bot)
    logging.info(f"Command 'début' invoked by {ctx.author} in {ctx.guild}/{ctx.channel}")


@bot.slash_command(
    name="dé", 
    description="Lancer x dés à y faces.")
async def roll_dice_command(ctx, dés: int, faces: int):
    await small_commands.roll_dice(ctx, dés, faces)
    logging.info(f"Command 'dé' invoked by {ctx.author} in {ctx.guild}/{ctx.channel}")


@bot.slash_command(
    name="achievement",
    description="Offrir un succès")
async def achievement(ctx: disnake.ApplicationCommandInteraction, text: str):
    await small_commands.achievement(ctx, text)
    logging.info(f"Command 'achievement' invoked by {ctx.author} in {ctx.guild}/{ctx.channel}")


@bot.slash_command(
    name="compter_membres",
    description="Compter le nombre de membres du serveur")
async def member_count_command(ctx: disnake.ApplicationCommandInteraction):
    await small_commands.member_count(ctx)
    logging.info(f"Command 'compter_membres' invoked by {ctx.author} in {ctx.guild}/{ctx.channel}")


@bot.slash_command(
    name="pin_toggle", 
    description="Pin or Unpin a message by its ID, only for SOJ_GO role",
    permissions="SOJ_GO")
async def pin_toggle(ctx: disnake.ApplicationCommandInteraction, message_id: str):
    await small_commands.togglepin_message(ctx, message_id)
    logging.info(f"Command 'pin_toggle' invoked by {ctx.author} in {ctx.guild}/{ctx.channel}")

################################################################################

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
@bot.slash_command(name="startpodcast", description="Start playing the podcast", permissions="Modération")
async def startpodcast(ctx):
    await podcast.play(ctx)
"""
##################################### Register commands from birthday_checker.py
# Register the add_birthday slash command
@bot.slash_command(name="anniversaire", description="Enregistrez votre anniversaire (format : MM-JJ)")
async def add_birthday(ctx: disnake.ApplicationCommandInteraction, birthday: str):
    await birthday_checker.add_birthday_command(ctx, birthday)
    logging.info(f"Command 'anniversaire' invoked by {ctx.author} in {ctx.guild}/{ctx.channel}")


# Task that runs every day to check and greet users
@tasks.loop(hours=24)
async def birthday_greetings_task():
    await birthday_checker.send_birthday_greetings(bot)
################################################################################

##################################### Register commands from search_thread_command.py
@bot.slash_command(
    name="chercher", 
    description="Search for threads, reviews, or episodes.")
async def search(inter: disnake.ApplicationCommandInteraction):
    pass


# Command to search threads
@search.sub_command(    
    name="fil",
    description="Recherche d'un fil")
async def search_thread(ctx: disnake.ApplicationCommandInteraction, expression: str):
    await search_thread_command.search_thread(ctx, bot, expression)
    logging.info(f"Command 'chercher fil' invoked by {ctx.author} in {ctx.guild}/{ctx.channel}")


# Command to search reviews
@search.sub_command(
    name="test",
    description="Recherche d'un test de jv dans des magazines d'antan (tilt, etc.)")
async def search_review(ctx: disnake.ApplicationCommandInteraction, expression: str):
    await search_review_command.review_search(ctx, expression)
    logging.info(f"Command 'chercher test retro' invoked by {ctx.author} in {ctx.guild}/{ctx.channel}")


# Command to search for a music of video game in ddmd
@search.sub_command(
    name="musique",
    description="Recherche d'une musique de jv dans les démons du midi")
async def search_music(ctx, game_title: str):
    await search_episode_command.search_music(ctx, game_title)
    logging.info(f"Command 'chercher musique' invoked by {ctx.author} in {ctx.guild}/{ctx.channel}")

# Command to search for a video game in soj
@search.sub_command(
    name="episode",
    description="Recherche d'un épisode de Silence On Joue!")
async def search_soj(ctx, game_title: str):
    await search_episode_command.search_soj(ctx, game_title)
    logging.info(f"Command 'chercher episode' invoked by {ctx.author} in {ctx.guild}/{ctx.channel}")


################################################################################


##################################### Register commands from deaftest_infinite.py
@bot.slash_command(
    name="deaf_test_infinite",
    description="Afficher l'image d'un jeu")
async def dti_command(inter: disnake.ApplicationCommandInteraction):
    await deaftest_infinite.display_image(inter, bot)


@bot.listen("on_button_click")
async def dti_button(ctx: disnake.ApplicationCommandInteraction):
    await deaftest_infinite.button_callback(ctx, bot)
    logging.info(f"Command 'dti button' invoked by {ctx.author} in {ctx.guild}/{ctx.channel}")
################################################################################


##################################### SOJDLE command from sojdle.py
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
    logging.info(f"Command 'sojdle' invoked by {ctx.author} in {ctx.guild}/{ctx.channel}")
################################################################################

##################################### 6128 command from amstrad_game.py
# Slash command to start/reset the game
@bot.slash_command(name="6128", description="")
async def start_game(inter: disnake.ApplicationCommandInteraction):
    from amstrad_game import start_game_logic
    await start_game_logic(inter)

# Handle button interactions
@bot.event
async def on_button_click(inter: disnake.MessageInteraction):
    try:
        # Debugging: Check if custom_id exists
        #print(dir(inter))  # List all attributes of the MessageInteraction object
        #print(f"Interaction data: {inter.data}")  # Check what data is present
        custom_id = inter.data.get("custom_id")  # Safely get custom_id
        #print(f"Custom ID: {custom_id}")  # Debugging

        if not custom_id:
            await inter.response.send_message(
                "Error: Button interaction does not have a custom_id.",
                ephemeral=True
            )
            return

        if custom_id.startswith("game_"):  # Game-specific button
            from amstrad_game import handle_game_button_interactions
            await handle_game_button_interactions(inter)
        else:
            print("This button action is not related to the game.")

    except Exception as e:
        print(f"Error in on_button_click: {e}")


################################################################################


##################################### CARTE command from discord_static_map.py
# @bot.slash_command(name="carte", description="Générer une carte visuelle des salons et fils du serveur Discord.")
# async def carte_serveur(inter):
#     await discord_static_map.generate_map(inter)
################################################################################


##################################### command from openai_quiz.py
#@bot.slash_command(description="Démarrez un quiz sur la culture et l'histoire des jeux vidéo !")
#async def sojquiz(ctx: disnake.ApplicationCommandInteraction)
   # await openai_quiz.quiz(ctx)
################################################################################

##################################### command from forum_ecrans_import.py
@bot.slash_command(description="Import topics and messages from a file",
    permissions="Modération")
async def import_forum(ctx):
    await ctx.send("Starting the import task...")
    
    # Call the import function
    result = await import_forum_data(bot)
    
    # Send the result of the import task back to the channel
    await ctx.send(result)


################################################################################


##################################### Data_soj command from plots.py
@bot.slash_command(name="data_soj", description="Trace un diagramme basé sur les données des épisodes de SOJ!",
    permissions="Modération")
async def generate_plot(
    interaction: disnake.ApplicationCommandInteraction, 
    plot_type: str = disnake.Option(name="type_de_diagramme", description="a(écart-type de la durée des ep), b(ep par chron), c(durée moy des ep), d(nbre ep par mois)"), 
    start_season: int = disnake.Option(name="saison_de_début", description="À partir de 1"), 
    end_season: int = disnake.Option(name="saison_de_fin", description="Jusqu'à 18")
):
    # Defer the response to give the bot time to process the request
    await interaction.response.defer()
    
    # Set defaults for start_season and end_season
    start_season = start_season if start_season is not None else 1
    end_season = end_season if end_season is not None else 18
    
    if start_season < 1:
        start_season = 1
    if end_season > 18:
        end_season = 18
    if start_season > end_season:
        end_season = start_season

    # Default plot type if not specified
    VALID_PLOT_TYPES = ["a", "b", "c"]
    if plot_type is None or plot_type not in VALID_PLOT_TYPES:
        plot_type = "a"  # Default to "a" if plot_type is invalid or not provided

    # Load your CSV data
    data = pd.read_csv('search_episode_soj.csv')
    
    # Handle the selected plot type
    if plot_type == "a":
        await plots.plot_duration_over_time(interaction, data, start_season, end_season)
    elif plot_type == "b":
        await plots.plot_episodes_per_chroniqueur(interaction, data, start_season, end_season)
    elif plot_type == "c":
        await plots.plot_episodes_per_month(interaction, data, start_season, end_season)

################################################################################


bot.run(DISCORD_BOT_TOKEN)