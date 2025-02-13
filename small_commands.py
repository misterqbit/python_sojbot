import disnake
from disnake.ext import commands

import random
# randomdle and dice
from random import randrange

# achievement
from io import BytesIO
import requests
from PIL import Image, ImageDraw, ImageFont

# dice
from tools.message_splitter import MessageSplitter

# add_modos on thread creation
import asyncio

# top images
from datetime import datetime, timedelta


def get_random_int(min_val, max_val):
    return random.randint(min_val, max_val)


# ######################################################################################## RANDOMDLE!
async def randomdle(inter: disnake.ApplicationCommandInteraction):
    user = inter.author
    print(f"ramdomdle on by {user}")

    wordle_width = randrange(5, 9)
    wordle_height = randrange(2, 6)
    wordle_attempts = wordle_height + 1
    wordle_day = randrange(1, 365)
    line = f'Randomdle     #{wordle_day}     {wordle_attempts}/7\n\n'

    for j in range(wordle_height):
        for i in range(wordle_width):
            square_color_nbr = randrange(1, 10)
            if square_color_nbr in [1, 2]:
                line += ':green_square:'
            elif square_color_nbr in [3, 4, 5]:
                line += ':orange_square:'
            elif square_color_nbr in [6, 7, 8, 9, 10]:
                line += ':black_medium_square:'
        line += '\n'

    for i in range(wordle_width):
        line += ':green_square:'
    line += '\n'

    await inter.response.send_message(line)

    print("Randomdle done")



# ############################################################################# UP!
async def up(inter: disnake.ApplicationCommandInteraction, bot):
    user = inter.author
    print(f"up on by {user}")    
    await inter.response.defer()
    # Check if the channel is a thread
    if isinstance(inter.channel, disnake.Thread):
        # Get the thread
        thread = inter.channel

        # Get the owner of the thread
        owner_id = thread.owner_id
        owner = await bot.fetch_user(owner_id)

        if owner:
            # Search for the oldest message from the owner within the thread
            oldest_message = None
            messages = await thread.history(limit=None).flatten()
            for message in reversed(messages):
                if message.author.id == owner.id:
                    oldest_message = message
                    break

            if oldest_message:
                message_url = oldest_message.jump_url
                # await inter.send(f'Voici le lien vers le début de ce fil: {message_url}')
                await inter.edit_original_response(content=f'Voici le lien vers le début de ce fil: {message_url}')

            else:
                # await inter.send('No message found from the thread owner in the thread.')
                await inter.edit_original_response(content="No message found from the thread owner in the thread.")


        else:
            # await inter.send('Failed to fetch the thread owner.')
            await inter.edit_original_response(content="Failed to fetch the thread owner.")


    else:
        await inter.edit_original_response(content="Ceci n'est pas un fil.")
        # await inter.send('You are not in a thread.')

    print("up done")


# ############################################################################ BUILD THE LIST!
async def buildthelist(inter: disnake.ApplicationCommandInteraction):
    user = inter.author
    print(f"buildthelist on by {user}")    
    await inter.response.defer()
    # Check if the channel name includes "LISTE" in capital letters
    if "LISTE" in inter.channel.name:
        # If "LISTE" is present, execute the following

        # Fetching the current channel
        channel = inter.channel

        # Setting flag value for avoiding the edit of the original message
        flag = 0

        # Dictionary to store the sum of heart emojis for each message
        hearts_sum = {}

        async for message in channel.history(limit=None):
            heart_count = sum(reaction.count for reaction in message.reactions if reaction.emoji == '❤️')
            if heart_count > 0:
                hearts_sum[message.id] = heart_count

        # Sort messages based on the sum of heart emojis (descending order)
        sorted_messages = sorted(hearts_sum.items(), key=lambda x: x[1], reverse=True)

        # Create a summary message with sorted messages
        summary = ""
        for message_id, heart_count in sorted_messages:
            message = await channel.fetch_message(message_id)
            new_entry = f"❤️ x {heart_count}  : {message.content}\n"

            # Check if adding the new entry exceeds the message length limit
            if len(summary) + len(new_entry) <= 2000:
                summary += new_entry
            else:
                # Send the current summary and reset it for the next message
                if flag == 0:
                    await inter.edit_original_response(content=f"{summary}")
                    flag = 1
                else:
                    await channel.send(f"{summary}")
                summary = new_entry


        # Send the final summary if not empty
        if summary:
            if flag == 0:
                await inter.edit_original_response(content=f"{summary}")
            else:
                await channel.send(f"{summary}")

    else:
        # await inter.send("Cette commande ne peut servir que dans un fil LISTE")
        await inter.edit_original_response(content="Cette commande ne peut servir que dans un fil LISTE")


    print("buildthelist done")



# ############################################################################# ROLL DICE!
async def roll_dice(inter, dés: int, faces: int):
    user = inter.author
    print(f"dice on by {user}")

    if dés < 1:
        await logger.log_message(f"""Le nombre de lancers ne peut pas être inférieur à 1.""")
        await logger.log_failure()
        return

    if faces < 1:
        await logger.log_message(f"""Le nombre de faces ne peut pas être inférieur à 1.""")
        await logger.log_failure()
        return

    text = f"🎲 {inter.author.mention} a lancé {dés} dés à {faces} faces:"
    for i in range(dés):
        text += f" {'|' if i > 0 else ''} **{randrange(1, faces + 1)}**"
    text_split: list[str] = MessageSplitter(text).get_message_split()
    for message in text_split:
        await inter.send(message)
    print("dice done")


# ############################################################################# ACHIEVEMENT!
async def achievement(inter: disnake.ApplicationCommandInteraction, text: str):
    """
    Generate an achievement image with the provided text.

    Args:
        inter (disnake.ApplicationCommandInteraction): The interaction object.
        text (str): The text to display on the achievement image.
    """
    user = inter.author
    print(f"Achievement sent by {user}")

    # Constants
    FONT_SIZE = 30
    MAX_LENGTH_1 = 34
    MAX_LENGTH_2 = 68
    TEXT_POSITION_1 = (185, 65)
    TEXT_POSITION_2 = (185, 95)

    # Load font
    font = ImageFont.truetype("arial.ttf", FONT_SIZE)

    # Load achievement image
    img_path = 'xbox-achievement-unlocked.png'

    try:
        img = Image.open(img_path)
    except Exception as e:
        print(f"Error loading image: {e}")
        return

    draw = ImageDraw.Draw(img)

    # Text wrapping and positioning
    if len(text) > MAX_LENGTH_2:
        text1 = text[:MAX_LENGTH_1].rsplit(' ', 1)[0]
        text2 = text[len(text1):MAX_LENGTH_2]
        text2 = text2.strip() if text2.startswith(' ') else text2  # Trim leading space if present
        text2 = text2[:MAX_LENGTH_1] + '...'

        draw.text(TEXT_POSITION_1, text1, font=font, fill=(255, 255, 255))
        draw.text(TEXT_POSITION_2, text2, font=font, fill=(255, 255, 255))

    elif len(text) > MAX_LENGTH_1 and len(text) <= MAX_LENGTH_2:
        text1 = text[:MAX_LENGTH_1].rsplit(' ', 1)[0]
        text2 = text[len(text1):MAX_LENGTH_2]
        text2 = text2.strip() if text2.startswith(' ') else text2  # Trim leading space if present

        if len(text2) > MAX_LENGTH_1:
            text2 = text2[:MAX_LENGTH_1] + '...'

        draw.text(TEXT_POSITION_1, text1, font=font, fill=(255, 255, 255))
        draw.text(TEXT_POSITION_2, text2, font=font, fill=(255, 255, 255))

    else:
        draw.text((185, 80), text, font=font, fill=(255, 255, 255))

    # Save image to buffer
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)

    # Send message with achievement image
    await inter.response.send_message(content=f"Succès offert par <@!{inter.author.id}> :",
                                      file=disnake.File(buffer, filename='achievement.png'))
    print("Achievement sent successfully")


# ############################################################################# MEMBER COUNT!
async def member_count(inter: disnake.ApplicationCommandInteraction):
    user = inter.author
    print(f"count_member on by {user}")

    guild = inter.guild

    if guild is None:
        await inter.response.send_message(content="Unable to retrieve guild information.")
        return

    # bot_count = len([x for x in guild.members if x.bot])
    bot_count = 7
    bot_string = 'bot' + ('s' if bot_count > 1 else '')

    member_count = guild.member_count - bot_count
    member_string = 'personne' + ('s' if member_count != 1 else '')

    # presence_count = sum(1 for member in guild.members if member.status != disnake.Status.offline and not member.bot)
    online_members = [member for member in guild.members if member.status != disnake.Status.offline]
    presence_count = len(online_members)
    presence_string = 'personne' + ('s' if presence_count != 1 else '')

    message = f"__Membres de **{guild.name}**__"
    message += f"\n👤 {member_count} {member_string}"
    message += f"\n🤖 {bot_count} {bot_string}"
    # message += f"\n\n🔌 {presence_count} {presence_string} en ligne"

    await inter.response.send_message(content=message)
    print("count_member done")


# ############################################################################# ADDING MODOS TO NEW THREADS!
async def adding_modos(thread, bot):
    EXCLUDED_CHANNEL_IDS = [1333853515348447243, 1333807091395068059]
    if thread.parent_id in EXCLUDED_CHANNEL_IDS :
        return  # Skip excluded channels

    random_user_pool = ['265376610763538452', '223447091706462208', '114863657787064321', '364861291254382603', '296380281311723542']  # Add your user IDs here

    # Specific user ID to always include
    specific_user_id = '864750688764559390'  # Replace with the actual user ID

    # Choose one random user ID from the pool
    random_user = random.sample(random_user_pool, 1)

    # Combine the specific user ID with the randomly selected user ID
    final_user_list = [specific_user_id] + random_user

    # Add a delay of 3 seconds
    await asyncio.sleep(3)
    
    # Add the users to the thread
    for user_id in final_user_list:
        user = await bot.fetch_user(user_id)
        await thread.add_user(user)


# ############################################################################# PIN or UNPIN messages - Only for SOJ_GO role
async def togglepin_message(ctx, message_id):
    # Check if the user has the required role
    required_role = disnake.utils.get(ctx.guild.roles, name="SOJ_GO")
    if required_role not in ctx.author.roles:
        await ctx.response.send_message("You don't have permission to use this command.", ephemeral=True)
        return

    try:
        message = await ctx.channel.fetch_message(message_id)
    except disnake.NotFound:
        await ctx.response.send_message("Message not found.", ephemeral=True)
        return

    if message.pinned:
        try:
            await message.unpin()
            await ctx.response.send_message(f"Message with ID {message_id} unpinned successfully! [Jump to message]({message.jump_url})", ephemeral=True)

        except disnake.Forbidden:
            await ctx.response.send_message("I don't have permission to unpin messages in this channel.", ephemeral=True)
        except disnake.HTTPException:
            await ctx.response.send_message("Failed to unpin the message. Please try again later.", ephemeral=True)
    else:
        try:
            await message.pin()
            await ctx.response.send_message(f"Message with ID {message_id} pinned successfully! [Jump to message]({message.jump_url})", ephemeral=True)

        except disnake.Forbidden:
            await ctx.response.send_message("I don't have permission to pin messages in this channel.", ephemeral=True)
        except disnake.HTTPException:
            await ctx.response.send_message("Failed to pin the message. Please try again later.", ephemeral=True)


# ############################################################################# GET IMAGES POSTS WITH MOST REACTION EMOJIS

async def find_top_images(ctx, thread_id: int, bot, reaction_nbr_max: int, reaction_nbr_min: int):
    thread = (bot.get_channel(thread_id) or await bot.fetch_channel(thread_id))
    print(thread_id)
    print(thread)
    if not thread:
        await ctx.send("Invalid thread ID or thread not found.")
        return
    # ID of the destination thread to post the result
    DESTINATION_THREAD_ID = 1236623516019720372
    top_messages = []
    message_count = 0
    message_nombre = 0
    # Calculate the datetime for one month ago
    x_months_ago = datetime.utcnow() - timedelta(days=300)

    await ctx.response.defer()

    #async for message in thread.history(limit=None, after=x_months_ago):
    async for message in thread.history(limit=None):

       
        if message_count >= 19:  # Check if reached the limit of 50 messages
            break

        if message.attachments:  # Check if message has attachments (images)
            total_reactions = sum(reaction.count for reaction in message.reactions)
            if reaction_nbr_min <= total_reactions <= reaction_nbr_max:  # Filter out messages with less than 20 total reactions
                top_messages.append((message, total_reactions))
                message_count += 1


    top_messages.sort(key=lambda x: x[1], reverse=True)  # Sort by reaction count

    if top_messages:
        result = "\n".join([f"<{message.jump_url}>: {reactions} reactions" for message, reactions in top_messages])
        destination_thread = bot.get_channel(DESTINATION_THREAD_ID)
        if destination_thread:
            await ctx.edit_original_response(content=f"Top posts with reactions in the thread (limited to top 20 messages):\n{result}")
        else:
            await ctx.edit_original_response(content="Destination thread not found.")
    else:
        await ctx.edit_original_response(content="No posts found in the thread.")
    print("top_dt done")


# #############################################################################

async def goodbye(inter: disnake.ApplicationCommandInteraction):
    await inter.response.send_message("Goodbye!")
