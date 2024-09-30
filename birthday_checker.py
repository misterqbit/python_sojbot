# birthday_checker.py
from datetime import datetime
import csv
import disnake

BIRTHDAYS_CSV = 'birthdays.csv'


def read_birthdays():
    """Reads the birthday CSV file and returns a dictionary of user IDs and birthdays."""
    birthdays = {}
    try:
        with open(BIRTHDAYS_CSV, mode='r') as file:
            reader = csv.reader(file)
            for row in reader:
                if len(row) == 2:
                    user_id, birthday = row
                    birthdays[user_id] = birthday.strip()  # Stripping spaces to avoid format issues
    except FileNotFoundError:
        print(f"{BIRTHDAYS_CSV} introuvable. Création d'un nouveau fichier.")
    return birthdays


def check_today_birthdays():
    """Checks which users have their birthday today based on the current month and day."""
    today = datetime.now().strftime('%m-%d')  # Format today's date as MM-DD
    birthdays = read_birthdays()
    today_birthday_users = [user_id for user_id, birthday in birthdays.items() if birthday == today]
    
    # Debugging output to check dates
    print(f"Aujourd'hui: {today}, Anniversaires trouvés: {today_birthday_users}")
    
    return today_birthday_users


async def send_birthday_greetings(bot):
    """Sends birthday greetings to users in a specific channel."""
    channel_id = 1137338580788846592  # Remplacez par l'ID de votre canal
    channel = bot.get_channel(channel_id)
    if not channel:
        print("Canal introuvable !")
        return

    today_birthday_users = check_today_birthdays()
    if today_birthday_users:
        for user_id in today_birthday_users:
            user = await bot.fetch_user(int(user_id))
            if user:
                await channel.send(f"🎉 Joyeux anniversaire, {user.mention} ! 🎂🥳")
    else:
        print("Pas d'anniversaires aujourd'hui.")


#################################################################################################

BIRTHDAYS_CSV = 'birthdays.csv'

def write_birthdays(birthdays):
    """Writes the birthdays dictionary back to the CSV file."""
    with open(BIRTHDAYS_CSV, mode='w', newline='') as file:
        writer = csv.writer(file)
        for user_id, birthday in birthdays.items():
            writer.writerow([user_id, birthday])


def add_or_update_birthday(user_id, birthday):
    """Adds or updates a user's birthday in the CSV file."""
    birthdays = read_birthdays()
    birthdays[user_id] = birthday
    write_birthdays(birthdays)

async def add_birthday_command(inter: disnake.ApplicationCommandInteraction, birthday: str):
    """Slash command to add a user's birthday. Format: MM-DD"""
    user_id = str(inter.author.id)
    try:
        # Validate date format
        datetime.strptime(birthday, '%m-%d')
        add_or_update_birthday(user_id, birthday)
        await inter.response.send_message(f"Anniversaire ajouté pour {inter.author.mention} le {birthday} !")
    except ValueError:
        await inter.response.send_message("Format de date invalide. Veuillez utiliser MM-JJ.", ephemeral=True)

