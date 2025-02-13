import disnake
import json

# Constants
GAME_MAP_FILE = "amstrad_game_map.json"
GAME_SAVE_FILE = "amstrad_game_saves.json"
WINNING_ROOMS = {3654, 5654, 4644, 4256, 5062}  # IDs of rooms required to win

# Load map data from JSON
def load_map():
    with open(GAME_MAP_FILE, 'r') as f:
        return json.load(f)["map"]

# Save game states to a JSON file
def save_game_states(states):
    # Convert sets to lists for JSON serialization
    for state in states.values():
        state["visited_winning_rooms"] = list(state["visited_winning_rooms"])
    with open(GAME_SAVE_FILE, "w") as f:
        json.dump(states, f, indent=4)

# Load game states from a JSON file
def load_game_states():
    try:
        with open(GAME_SAVE_FILE, "r") as f:
            states = json.load(f)
            # Convert lists back to sets for internal use
            for state in states.values():
                state["visited_winning_rooms"] = set(state["visited_winning_rooms"])
            return states
    except FileNotFoundError:
        return {}

# Initialize game states
game_states = load_game_states()

# Start/reset the game
async def start_game_logic(inter: disnake.ApplicationCommandInteraction):
    user_id = str(inter.user.id)

    # Initialize the game state for this user
    game_states[user_id] = {
        "player_position": 5252,  # Starting room ID
        "inventory": [],
        "puzzles_solved": [],
        "visited_winning_rooms": set()  # Track only winning rooms visited
    }
    save_game_states(game_states)

    # Create a private thread for the user
    thread_name = f"Partie de {inter.user.display_name}"
    thread = await inter.channel.create_thread(name=thread_name, type=disnake.ChannelType.public_thread)

    # Inform the user and display the starting room
    await thread.send(f"{inter.user.mention}, votre partie commence ici !")
    await display_room(thread, user_id, 5246)

# Display the current room
async def display_room(channel, user_id, room_id):
    map_data = load_map()
    room = next((r for r in map_data if r["id"] == room_id), None)

    if not room:
        await channel.send("Pièce introuvable !")
        return

    embed = disnake.Embed(title=f"{room['name']}")
    embed.set_image(url=room["image_url"])

    # Items in the room
    if room["items"]:
        items = "\n".join([f"- {item['name']}" for item in room["items"]])
        embed.add_field(name="Objets", value=items, inline=False)

    # Puzzles in the room
    if room["puzzle"]:
        embed.add_field(name="Énigme", value=room["puzzle"]["question"], inline=False)

    # Buttons for interactions
    view = disnake.ui.View()

    # Add movement buttons if there are connections
    if room["connections"]:
        for direction in room["connections"]:
            view.add_item(
                disnake.ui.Button(label=direction.capitalize(), custom_id=f"game_move_{user_id}_{direction}")
            )
    else:
        # If no connections, user loses the game and we give them a button to restart
        view.add_item(
            disnake.ui.Button(label="Recommencer l'aventure", custom_id=f"game_restart_{user_id}")
        )
        await channel.send(f"{channel.guild.get_member(int(user_id)).mention}, vous avez perdu !", embed=embed, view=view)
        return

    # Add interaction buttons for items and puzzles
    if room["items"]:
        view.add_item(disnake.ui.Button(label="Ramasser les objets", custom_id=f"game_pick_items_{user_id}"))
    if room["puzzle"]:
        view.add_item(disnake.ui.Button(label="Résoudre l'énigme", custom_id=f"game_solve_puzzle_{user_id}"))

    await channel.send(embed=embed, view=view)

# Handle game-specific button interactions
async def handle_game_button_interactions(inter: disnake.MessageInteraction):
    user_id = str(inter.user.id)
    if user_id not in game_states:
        await inter.response.send_message("Aucune partie en cours trouvée pour vous. Veuillez lancer une nouvelle partie.", ephemeral=True)
        return

    custom_id = inter.data.get("custom_id")
    if not custom_id:
        await inter.response.send_message("Erreur : Aucun custom_id trouvé pour cette interaction.", ephemeral=True)
        return

    game_state = game_states[user_id]
    map_data = load_map()
    room_id = game_state["player_position"]
    room = next((r for r in map_data if r["id"] == room_id), None)

    if not room:
        await inter.response.send_message("Erreur : Données de la pièce introuvables.", ephemeral=True)
        return

    if custom_id.startswith(f"game_move_{user_id}_"):
        direction = custom_id.split("_")[-1]
        if direction in room["connections"]:
            new_room_id = room["connections"][direction]
            game_state["player_position"] = new_room_id

            # Check if the new room is a winning room
            if new_room_id in WINNING_ROOMS:
                game_state["visited_winning_rooms"].add(new_room_id)

            save_game_states(game_states)

            # Check if the user has won the game
            if set(game_state["visited_winning_rooms"]) == WINNING_ROOMS:
                await inter.channel.send(
                    f"\ud83c\udf89 Félicitations, {inter.user.mention} ! Vous avez gagné le jeu en visitant toutes les salles spéciales ! \ud83c\udf89"
                )
                await inter.channel.edit(archived=True, locked=True)  # Lock the thread (optional)
                return

            # Display the new room
            await inter.response.defer()
            await display_room(inter.channel, user_id, new_room_id)
        else:
            await inter.response.send_message("Vous ne pouvez pas aller dans cette direction !", ephemeral=True)

    elif custom_id == f"game_pick_items_{user_id}":
        if room["items"]:
            for item in room["items"]:
                game_state["inventory"].append(item["name"])
            room["items"] = []  # Remove items from the room
            save_game_states(game_states)
            await inter.response.send_message("Objets ramassés et ajoutés à votre inventaire !", ephemeral=True)
        else:
            await inter.response.send_message("Aucun objet à ramasser ici !", ephemeral=True)

    elif custom_id == f"game_solve_puzzle_{user_id}":
        puzzle = room["puzzle"]
        if puzzle and puzzle["question"] not in game_state["puzzles_solved"]:
            await inter.response.send_message(f"Énigme : {puzzle['question']}")
            # Add reactions for answers
            message = await inter.send("Réagissez avec l'emoji correspondant à la bonne réponse !")
            for answer in puzzle["answers"]:
                await message.add_reaction(answer["emoji"])

            def check(reaction, user):
                return user == inter.user and reaction.emoji in [a["emoji"] for a in puzzle["answers"]]

            reaction, _ = await inter.bot.wait_for("reaction_add", check=check)

            # Check if the selected emoji is correct
            if any(a["emoji"] == str(reaction.emoji) and a["correct"] for a in puzzle["answers"]):
                game_state["puzzles_solved"].append(puzzle["question"])
                save_game_states(game_states)
                await inter.followup.send("Bonne réponse ! Énigme résolue !")
            else:
                await inter.followup.send("Mauvaise réponse. Réessayez !")
        else:
            await inter.response.send_message("Aucune énigme à résoudre ici ou déjà résolue !", ephemeral=True)

    elif custom_id == f"game_restart_{user_id}":
        # Restart the adventure by setting the player back to the starting room (5246)
        game_states[user_id]["player_position"] = 5246
        game_states[user_id]["inventory"] = []
        game_states[user_id]["puzzles_solved"] = []
        game_states[user_id]["visited_winning_rooms"] = set()

        # Save the updated game state
        save_game_states(game_states)

        # Send the user back to the starting room
        await inter.response.send_message(f"Vous avez recommencé l'aventure, {inter.user.mention} ! Bienvenue dans la salle de départ.", ephemeral=True)

        # Redisplay the starting room
        await display_room(inter.channel, user_id, 5246)
