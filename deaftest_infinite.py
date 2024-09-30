import disnake

import random
# deaf test infinite
from random import randint
import requests
from disnake import ButtonStyle
from disnake.ui import Button, ActionRow

def get_random_int(min_val, max_val):
    return random.randint(min_val, max_val)

############################################## Function to update value in file
def update_value_in_file(name, new_value):
    with open('deaftestinfinite_localvalues.txt', 'r+') as file:
        lines = file.readlines()
        file.seek(0)
        for line in lines:
            parts = line.split(':')
            if parts[0].strip() == name:
                file.write(f"{name}: {new_value}\n")
            else:
                file.write(line)
        file.truncate()

############################################## Function to read value from file
def read_value_from_file(name):
    with open('deaftestinfinite_localvalues.txt', 'r') as file:
        for line in file:
            parts = line.split(':')
            if parts[0].strip() == name:
                return parts[1].strip()


# ############################################################################# DEAF TEST INFINITE!
# DEAF TEST INFINITE
your_specified_thread_channel_id_1 = 928370783603028018  # deaf test cpc power infinite
your_specified_thread_channel_id_2 = 953642125931708486  # deaf test tgdb infinite

async def display_image(inter: disnake.ApplicationCommandInteraction, bot):
    temporary_message = await inter.channel.send(
        f"Le bot cherche un jeu")

    user = inter.author
    print(f"deaftestinfinite on by {user}")
    MinGame1 = 1
    MaxGame1 = 3698
    MinGame2 = 1
    MaxGame2 = 90000

    if not (inter.channel_id == your_specified_thread_channel_id_1 or inter.channel_id == your_specified_thread_channel_id_2):
        await inter.edit_original_response(content="Cette commande est à utiliser dans les fils Deaf Test Infinite")
        return

    global random_game_number_cpc
    global random_game_number_tgdb

    if inter.channel_id == your_specified_thread_channel_id_2:
        x = 0
        while True:
            random_game_number_tgdb = randint(MinGame2, MaxGame2)   # Generate a random number
            image_url = f"https://cdn.thegamesdb.net/images/original/screenshot/{random_game_number_tgdb}-1.jpg"   # Format the URL with the random number
            answer_image_url = f"https://cdn.thegamesdb.net/images/original/boxart/front/{random_game_number_tgdb}-1.jpg"
            response = requests.head(image_url)  # Send a HEAD request to check if the URL exists
            x = x + 1
            print(x)
            if response.status_code == 200:  # If the URL exists (status code 200 OK)
                update_value_in_file('random_game_number_tgdb', random_game_number_tgdb)
                break  # Exit the loop
    else:
        while True:
            random_game_number_cpc = randint(MinGame1, MaxGame1)   # Generate a random number
            image_url = f"https://www.cpc-power.com/extra_lire_fichier.php?extra=cpcold&fiche={random_game_number_cpc}&slot=2&part=A&type=.png"   # Format the URL with the random number
            answer_image_url = f"https://www.cpc-power.com/extra_lire_fichier.php?extra=cpcold&fiche={random_game_number_cpc}&slot=1&part=A&type=.png"
            response = requests.head(image_url)  # Send a HEAD request to check if the URL exists

            if response.status_code == 200:  # If the URL exists (status code 200 OK)
                response_answer = requests.head(answer_image_url)  # Send a HEAD request to check if the URL exists
                if response_answer.status_code == 200:  # If the URL exists (status code 200 OK)
                    update_value_in_file('random_game_number_cpc', random_game_number_cpc)
                    break  # Exit the loop

    embed = disnake.Embed()
    embed.set_image(url=image_url)

    button1 = Button(
        style=ButtonStyle.success,
        label="Afficher la solution",
        custom_id="show_image_button_1"
    )

    row = ActionRow(button1)  # Use ActionRow from disnake.ui

    await temporary_message.delete()
    await inter.response.send_message(content="Voici un autre jeu:", embed=embed, components=[row])


async def button_callback(inter, bot):
        user = inter.author
        print(f"solution button for deaftestinfinite on by {user}")

        if inter.channel_id == your_specified_thread_channel_id_2:
            random_game_number_tgdb = read_value_from_file('random_game_number_tgdb')
            answer_image_url = f"https://cdn.thegamesdb.net/images/original/boxart/front/{random_game_number_tgdb}-1.jpg"
            answer_game_url = f"https://thegamesdb.net/game.php?id={random_game_number_tgdb}"
        else:
            random_game_number_cpc = read_value_from_file('random_game_number_cpc')
            answer_image_url = f"https://www.cpc-power.com/extra_lire_fichier.php?extra=cpcold&fiche={random_game_number_cpc}&slot=1&part=A&type=.png"
            answer_game_url = f"https://www.cpc-power.com/index.php?page=detail&num={random_game_number_cpc}"

        if inter.component.custom_id == "show_image_button_1":
            embed = disnake.Embed()
            embed.set_image(url=answer_image_url)
            message = f"Voici l'écran de titre du jeu {answer_game_url} :"
            await inter.send(content=message, embed=embed)

            # Add a button to run display_image again
            button2 = Button(
                style=ButtonStyle.primary,
                label="Afficher un autre jeu",
                custom_id="show_image_button_2"
            )

            await inter.edit_original_message(components=[ActionRow(button2)])

        elif inter.component.custom_id == "show_image_button_2":
            # Run display_image command again
            await display_image(inter, bot)       


