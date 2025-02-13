import json
import random
import re
import unicodedata
import disnake


# File paths
GAMES_FILE = 'sojdle_games.csv'  # The file containing the game titles
LOCAL_VALUES_FILE = 'sojdle_localvalues.txt'  # The file to store the active game ID
SCORES_FILE = 'sojdle_scores.json'  # The file to store user scores

# Function to load game titles from the CSV file
def get_game_titles(filename):
    games = {}
    with open(filename, 'r', encoding='utf-8') as file:
        # Read each line, skipping the header
        for line in file.readlines()[1:]:
            # Unpack the line into two variables: game_id and title
            game_id, title = line.strip().split(',', 1)
            games[int(game_id)] = title.lower()  # Store titles in lowercase for consistency
    return games


# Function to get active game ID, guess counter, and revealed letters from the local values file
def get_game_state(filename):
    game_id, total_guesses, revealed_letters = None, 0, []
    with open(filename, 'r') as file:
        content = file.read()
        
        # Extract game ID
        game_id_match = re.search(r'sojdle_gameid: (\d+)', content)
        if game_id_match:
            game_id = int(game_id_match.group(1))

        # Extract total guess counter
        guesses_match = re.search(r'total_guesses: (\d+)', content)
        if guesses_match:
            total_guesses = int(guesses_match.group(1))

        # Extract revealed letters
        letters_match = re.search(r'revealed_letters: ([\w,]*)', content)
        if letters_match:
            revealed_letters = letters_match.group(1).split(',')

    return game_id, total_guesses, revealed_letters

# Function to update the game state (ID, guess counter, revealed letters) in the local values file
def update_game_state(filename, game_id, total_guesses, revealed_letters):
    with open(filename, 'w') as file:
        file.write(f'sojdle_gameid: {game_id}\n')
        file.write(f'total_guesses: {total_guesses}\n')
        file.write(f'revealed_letters: {",".join(revealed_letters)}\n')


# Function to update the active game ID to a new random game ID
def set_random_game_id(filename, games, revealed_letters, total_guesses):
    new_game_id = random.choice(list(games.keys()))
    # Update game state in the file
    update_game_state(LOCAL_VALUES_FILE, new_game_id, total_guesses, revealed_letters)
        
    return new_game_id


# Function to load scores from the JSON file
def load_scores():
    try:
        with open(SCORES_FILE, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return {}


# Function to save scores to the JSON file
def save_scores(scores):
    with open(SCORES_FILE, 'w') as file:
        json.dump(scores, file)


# Function to display the top ten users on the leaderboard
async def display_leaderboard(ctx):
    scores = load_scores()
    if not scores:
        await ctx.send("No scores yet!")
        return

    # Sort scores in descending order and get the top ten
    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    leaderboard_text = "🏆 **Top 10 Leaderboard** 🏆\n"
    count = 0

    for user_id, score in sorted_scores:
        if count >= 10:
            break  # Stop once we have ten valid entries

        try:
            # Fetch the user by ID
            user = await ctx.guild.fetch_member(int(user_id))
            user_name = user.display_name
            leaderboard_text += f"> {count + 1}. {user_name}: {score} point(s)\n"
            count += 1  # Increment count only for valid entries

        except disnake.NotFound:
            continue  # Skip missing users

    if count == 0:
        leaderboard_text += "No valid users on the leaderboard."
        
    await ctx.channel.send(leaderboard_text)
    #await ctx.edit_original_response(content=' '.join(leaderboard_text))


def remove_accents(input_str):
    # Normalize the string to 'NFD' (Normalization Form Decomposition), separating accents
    nfkd_form = unicodedata.normalize('NFD', input_str)

    # Remove characters that are combining marks (accents) and keep base characters
    return ''.join([char for char in nfkd_form if not unicodedata.combining(char)])


# Command handler for the "guess" command
async def guess(ctx, guess: str):

    await ctx.response.defer()
    
    games = get_game_titles(GAMES_FILE)  # Load the game titles from the CSV
    
    # Get current game state from local values
    active_game_id, total_guesses, revealed_letters = get_game_state(LOCAL_VALUES_FILE)

    if active_game_id is None or active_game_id not in games:
        await ctx.edit_original_response("No active game selected or invalid game ID.")
        return

    video_game_title = games[active_game_id]  # Select the active game title using the game ID
    video_game_title_without_accents = remove_accents(video_game_title)
    #video_game_title = re.sub(r'[^\w\s]', '', video_game_title_without_accents)
    video_game_title = video_game_title_without_accents.lower()

    guess_without_accents = remove_accents(guess)
    #normalized_guess = re.sub(r'[^\w\s]', '', guess_without_accents)  # Remove non-alphanumeric characters
    lowercase_guess = guess_without_accents.lower()

    # Increment the total guess counter
    total_guesses += 1

    text = []  # Initialize the list to build the response
    answer = list(video_game_title)  # Create a mutable list to track correct guesses
    for i in range(len(video_game_title)):
        if i < len(lowercase_guess):
            if (lowercase_guess[i] == video_game_title[i]):
                answer[i] = None  # Mark this letter as used to prevent duplicate checks

    # Check if a hint should be given (after every 5 guesses)
    if total_guesses % 5 == 0:
        # Find the first hidden letter to reveal
        for i in range(len(video_game_title)):
            if video_game_title[i] != ' ' and video_game_title[i] not in revealed_letters:
                revealed_letters.append(video_game_title[i])
                break

    text.append('>')
    # Display the typed guess as emojis
    for char in lowercase_guess:
        if char == ' ':
            text.append(':blue_square:')
        elif char == ':':
            text.append('<:regional_two_points:1289598863585316926>')  # Custom emoji for colon
        elif char == "'":
            text.append('<:regional_apostrophe:1289600486214729748>')  # Custom emoji for apostrophe
        elif char == "!":
            text.append(':grey_exclamation:')  # Custom emoji for exclamation
        elif char == "-":
            text.append(':heavy_minus_sign:')  # Custom emoji for minus
        elif char == "+":
            text.append(':heavy_plus_sign:')  # Custom emoji for plus            
        elif char.isalpha():
            text.append(f':regional_indicator_{char}:')
        else:
            emoji_mapping = {
                '0': ':zero:', '1': ':one:', '2': ':two:', '3': ':three:', '4': ':four:',
                '5': ':five:', '6': ':six:', '7': ':seven:', '8': ':eight:', '9': ':nine:'
            }
            text.append(emoji_mapping.get(char, ':x:'))
    text.append('\n')  # Newline to separate the typed guess from the results
    text.append('>')

    # Iterate over the game title length to check each character in the guess
    for i in range(len(video_game_title)):
        if i < len(lowercase_guess):
            char = lowercase_guess[i]
            if video_game_title[i] == ' ':
                text.append(':blue_square:')  # Mark spaces as blue squares
            elif video_game_title[i] in revealed_letters:
                text.append(f':regional_indicator_{video_game_title[i]}:')  # Revealed letters are shown
            #elif video_game_title[i] == ':':
            #    text.append('<:regional_two_points:1289598863585316926>')  # Custom emoji for colon
            #elif video_game_title[i] == "'":
            #    text.append('<:regional_apostrophe:1289600486214729748>')  # Custom emoji for apostrophe
            #elif video_game_title[i] == "!":
            #    text.append(':grey_exclamation:')  # Custom emoji for exclamation
            #elif video_game_title[i] == "-":
            #    text.append(':heavy_minus_sign:')  # Custom emoji for minus
            #elif video_game_title[i] == "+":
            #    text.append(':heavy_plus_sign:')  # Custom emoji for plus
            else:
                # If the character is in the correct position, mark it green and remove it from the answer
                if char == video_game_title[i]:
                    text.append(':green_square:')
                elif char in video_game_title:
                    if char in answer:
                        text.append(':orange_square:')  # Letter is correct but in the wrong position
                        answer[answer.index(char)] = None  # Mark this letter as used
                    else:
                        text.append(':red_square:')  # Letter not in answer anymore
                else:
                    text.append(':red_square:')  # Letter not in title at all
        else:
            if video_game_title[i] == ' ':
                text.append(':blue_square:')  # Blue square for spaces
            elif video_game_title[i] == ':':
                text.append('<:regional_two_points:1289598863585316926>')  # Custom emoji for colon
            elif video_game_title[i] == "'":
                text.append('<:regional_apostrophe:1289600486214729748>')  # Custom emoji for apostrophe
            elif char == "!":
                text.append(':grey_exclamation:')  # Custom emoji for exclamation
            elif char == "-":
                text.append(':heavy_minus_sign:')  # Custom emoji for minus
            elif char == "+":
                text.append(':heavy_plus_sign:')  # Custom emoji for plus
            else:
                text.append(':grey_question:')  # Question mark for other characters
            
    # Handle any excess characters in the guess
    if len(lowercase_guess) > len(video_game_title):
        text.extend([':x:' for _ in range(len(lowercase_guess) - len(video_game_title))])

    # Send the response to the Discord channel
    await ctx.edit_original_response(content=' '.join(text))

    # Check if the guess is correct
    if lowercase_guess == video_game_title:
        # Update the user's score
        scores = load_scores()
        user_id = str(ctx.author.id)
        scores[user_id] = scores.get(user_id, 0) + 1
        save_scores(scores)

        bravotext = f"🎉 Bravo {ctx.author.display_name}! C'est la bonne réponse! 🎉 Vous avez maintenant {scores[user_id]} point(s)."
        await ctx.send(content=' '.join(bravotext))

        # Display the leaderboard
        await display_leaderboard(ctx)

        revealed_letters.clear()    # Reset the revealed letters for the new game
        total_guesses = 0           # Reset the total guess counter
        new_game_id = set_random_game_id(LOCAL_VALUES_FILE, games, revealed_letters, total_guesses)  # Set a new random game ID and store local values

        new_game_title = games[new_game_id]
        new_game_title_without_accents = remove_accents(new_game_title)
        #new_game_title = re.sub(r'[^\w\s]', '', new_game_title_without_accents)



        # Display the question marks and blue squares representing the new game title to guess
        new_title_display = []
        new_title_display.append("Essayez de deviner le titre de ce jeu vidéo chroniqué ds SOJ! 🔍")
        new_title_display.append('\n')
        for char in new_game_title:
            if char == ' ':
                new_title_display.append(':blue_square:')  # Blue square for spaces
            elif char == ':':
                new_title_display.append('<:regional_two_points:1289598863585316926>')  # Custom emoji for colon
            elif char == "'":
                new_title_display.append('<:regional_apostrophe:1289600486214729748>')  # Custom emoji for apostrophe
            elif char == "!":
                new_title_display.append(':grey_exclamation:')  # Custom emoji for exclamation
            elif char == "-":
                new_title_display.append(':heavy_minus_sign:')  # Custom emoji for minus
            elif char == "+":
                new_title_display.append(':heavy_plus_sign:')  # Custom emoji for plus
            else:
                new_title_display.append(':grey_question:')  # Question mark for other characters

        await ctx.channel.send(' '.join(new_title_display))  # Send the display for the new game title
    else:
            update_game_state(LOCAL_VALUES_FILE, active_game_id, total_guesses, revealed_letters)
            