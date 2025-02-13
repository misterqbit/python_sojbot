import disnake
from disnake.ext import commands
import openai
import json
import os

# Initialize bot
bot = commands.Bot(command_prefix="/")

# OpenAI API Setup
openai.api_key = "your-openai-api-key"

# Leaderboard file
LEADERBOARD_FILE = "leaderboard.json"

# Ensure leaderboard file exists
if not os.path.exists(LEADERBOARD_FILE):
    with open(LEADERBOARD_FILE, "w") as f:
        json.dump({}, f)

def load_leaderboard():
    """Load leaderboard from file."""
    with open(LEADERBOARD_FILE, "r") as f:
        return json.load(f)

def save_leaderboard(leaderboard):
    """Save leaderboard to file."""
    with open(LEADERBOARD_FILE, "w") as f:
        json.dump(leaderboard, f)

async def quiz(inter):
    """Starts the quiz with a question generated dynamically in French."""
    await inter.response.defer()

    # Prompt for the GPT model
    prompt = """
    Crée une question à choix multiple sur la culture et l'histoire des jeux vidéo, en français et avec une touche d'humour. 
    Le format de sortie doit être :
    Question : <question>
    Options : <option1>, <option2>, <option3>, <option4>
    Réponse : <bonne option>
    """

    try:
        # Call OpenAI GPT-3.5-turbo for question generation
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "system", "content": "Tu es un générateur de quiz amusant."},
                      {"role": "user", "content": prompt}],
            max_tokens=200,
            temperature=0.7
        )
        output = response['choices'][0]['message']['content'].strip()

        # Parse the response
        lines = output.split("\n")
        question = lines[0].replace("Question : ", "").strip()
        options = lines[1].replace("Options : ", "").split(", ")
        answer = lines[2].replace("Réponse : ", "").strip()

        # Validate the response
        if not question or not options or len(options) != 4 or not answer:
            raise ValueError("Format de question invalide de GPT.")

        # Display the question and options to the users
        embed = disnake.Embed(title="🎮 Quiz Jeux Vidéo 🎮", description=question)
        for i, option in enumerate(options, start=1):
            embed.add_field(name=f"Option {i}", value=option, inline=False)
        await inter.followup.send(embed=embed)

        # Save the correct answer for validation
        bot.correct_answer = answer

    except Exception as e:
        await inter.followup.send(f"Erreur lors de la génération du quiz : {e}")

@bot.slash_command(description="Soumettez une réponse au quiz !")
async def reponse(inter, option: str):
    """Submit an answer to the quiz."""
    leaderboard = load_leaderboard()

    try:
        # Ensure a quiz is active
        if not hasattr(bot, "correct_answer") or bot.correct_answer is None:
            await inter.response.send_message("Aucun quiz actif en ce moment !")
            return

        # Check the user's answer
        user_id = str(inter.author.id)
        if option.lower() == bot.correct_answer.lower():
            await inter.response.send_message("✅ Bonne réponse ! Bravo !")

            # Update leaderboard
            leaderboard[user_id] = leaderboard.get(user_id, 0) + 1
            save_leaderboard(leaderboard)
        else:
            await inter.response.send_message(f"❌ Mauvaise réponse ! La bonne réponse était : **{bot.correct_answer}**")

    except Exception as e:
        await inter.response.send_message(f"Erreur lors de la vérification de la réponse : {e}")

@bot.slash_command(description="Consultez le classement du quiz !")
async def classement(inter):
    """Displays the leaderboard."""
    leaderboard = load_leaderboard()
    if not leaderboard:
        await inter.response.send_message("Le classement est actuellement vide.")
        return

    # Sort leaderboard by scores
    sorted_leaderboard = sorted(leaderboard.items(), key=lambda x: x[1], reverse=True)
    embed = disnake.Embed(title="🎮 Classement Quiz 🎮")
    for user_id, score in sorted_leaderboard:
        user = await bot.fetch_user(int(user_id))
        embed.add_field(name=user.name, value=f"Score : {score}", inline=False)

    await inter.response.send_message(embed=embed)

# Run bot
bot.run("your-bot-token")
