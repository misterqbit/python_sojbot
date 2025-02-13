import disnake
from disnake.ext import commands
import csv

# Load CSV data once when the bot starts
def load_csv_data(filename):
    games = []
    with open(filename, mode='r', encoding='utf-8-sig') as file:
        reader = csv.DictReader(file)
        for row in reader:
            games.append(row)
    return games

# Load the games data from CSV
ddmd_data = load_csv_data("search_episode_tracklist ddmd.csv")
soj_data = load_csv_data("search_episode_soj.csv")


async def search_music(inter, game_title: str):
    # Find results where the game title appears
    results = [row for row in ddmd_data if game_title.lower() in row['Jeu'].lower()]

    # Use a set to track unique episodes
    unique_episodes = []
    seen_episodes = set()

    for row in results:
        if row['Episode'] not in seen_episodes:
            unique_episodes.append(row)
            seen_episodes.add(row['Episode'])
    
    # Count total unique results
    total_results = len(unique_episodes)

    # Limit to top 10 unique episodes
    top_results = unique_episodes[:10]

    if top_results:
        embed = disnake.Embed(
            title=f"{total_results} résultats pour **{game_title}** dans le podcast Les Démons du Midi",
            description=f"{inter.author.display_name}, vous trouverez des musiques de ce jeu dans les épisodes suivants:",
            color=disnake.Color.blue()
        )

        # Add each unique episode, title, and other fields to the embed
        for row in top_results:
            # Create the value string, adding fields conditionally
            value = f"Titre : **{row['Titre']}**\n"
            value += f"[Écouter ici]({row['URL']})\n"

            if row['Auteurs']:  # Check if authors exist
                value += f"Auteurs : **{row['Auteurs']}**\n"
            if row['Liens web']:  # Check if web links exist
                value += f"[Liens web]({row['Liens web']})\n"
            if row['Deezer']:  # Check if Deezer links exist
                value += f"[Écouter sur Deezer]({row['Deezer']})\n"
            #print(value)
            # Add a separator after each answer (e.g., `—` or a newline)
            value += "\n—\n"  # Separator

            # Add the field to the embed
            embed.add_field(
                name=f"Épisode {row['Episode']}",
                value=value,
                inline=False
            )

        # Send the embed
        await inter.response.send_message(embed=embed)
    else:
        await inter.response.send_message(f"Aucun résultat trouvé pour le jeu **{game_title}** dans le podcast Les Démons du Midi.")

##########################################################################################

async def search_soj(inter, game_title: str):
    # Find results where the game title appears
    results = [row for row in soj_data if game_title.lower() in row['themesminor'].lower()]

    # Use a set to track unique episodes
    unique_episodes = []
    seen_episodes = set()

    for row in results:
        if row['titre'] not in seen_episodes:
            unique_episodes.append(row)
            seen_episodes.add(row['titre'])

    # Count total unique results
    total_results = len(unique_episodes)

    # Limit to top 10 unique episodes
    top_results = unique_episodes[:10]

    if top_results:
        embed = disnake.Embed(
            title=f"{total_results} résultats pour **{game_title}** dans le podcast Silence On Joue!",
            description=f"{inter.author.display_name}, vous trouverez ces chroniques dans les épisodes suivants:",
            color=disnake.Color.blue()
        )

        # Add each unique episode, title, and other fields to the embed
        for row in top_results:
            # Create the value string, adding fields conditionally
            value = f"Titre : **{row['titre']}**\n"
            value += f"[Écouter ici]({row['weburl']})\n"

            if row['date']:  # Check if authors exist
                value += f"Date : {row['date']}\n"
            if row['duree']:  # Check if web links exist
                value += f"Durée : {row['duree']}\n"
            if row['statschroniqueurs']:  # Check if Deezer links exist
                value += f"Chroniqueureuses : {row['statschroniqueurs']}\n"
            #print(value)
            # Add a separator after each answer (e.g., `—` or a newline)
            value += "\n—\n"  # Separator

            # Add the field to the embed
            embed.add_field(
                name=f"Épisode #{row['episode']}",
                value=value,
                inline=False
            )

        # Send the embed
        await inter.response.send_message(embed=embed)
    else:
        await inter.response.send_message(f"Aucun résultat trouvé pour le jeu **{game_title}** dans le podcast Silence On Joue!")
