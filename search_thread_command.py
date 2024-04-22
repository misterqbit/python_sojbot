from disnake import Embed, Guild, ApplicationCommandInteraction, TextChannel
from disnake.abc import GuildChannel
from disnake.ext import commands
from copy import copy
from tools.message_splitter import MessageSplitter

async def search_thread(interaction: ApplicationCommandInteraction, bot, expression: str, excluded_category_id: int = None):
    print("search_thread on")

    """
    Search for threads within the server based on the given expression,
    excluding channels and threads from the specified category (if provided).
    """
    user = interaction.author
    # result_channel = interaction.channel
    result_channel = await bot.fetch_channel(1001036859952070667)
    guild = interaction.guild

    # Fetch all channels and active threads within the server
    channels = await guild.fetch_channels()
    active_threads = await guild.active_threads()

    all_threads = []
    # Iterate through all channels
    for channel in channels:
        # Exclude channels from the specified category, if provided
        if excluded_category_id and channel.category_id == excluded_category_id:
            continue

        # Add active threads from the channel
        all_threads.extend([x for x in active_threads if x.parent == channel])

        # Add archived threads from text channels
        if isinstance(channel, TextChannel):
            try:
                async for thread in channel.archived_threads(limit=None):
                    all_threads.append(thread)
            except:
                pass

    # Filter threads based on the search expression
    filtered_list = copy(all_threads)
    search_words = expression.lower().split(' ')
    for word in search_words:
        filtered_list = [x for x in filtered_list if word in x.name.lower()]
    result_nb = len(filtered_list)

    # Handle the results
    if result_nb > 10:
        message = f"{user.mention} il y a trop de résultats ({result_nb}) pour '**{expression}**', essaie d'affiner ta recherche."
        result = await result_channel.send(message)
        temporary_message = await interaction.channel.send(f"Trop de résultats pour '**{expression}**' : {result.jump_url}")
    elif result_nb == 0:
        message = f"{user.mention} désolé, pas de résultat pour '**{expression}**'. À toi de créer ce fil ;-)"
        result = await result_channel.send(message)
        temporary_message = await interaction.channel.send(f"Pas de résultat pour '**{expression}**' : {result.jump_url}")
    else:
        message = f"{user.mention} tu trouveras '**{expression}**' dans :"
        embed_text = '\n'.join([f"{x.parent.name} > [#{x.name}]({x.jump_url})" for x in filtered_list])
        embed_text_splitter = MessageSplitter(embed_text)
        texts = embed_text_splitter.get_message_split()

        result = await result_channel.send(message, embed=Embed(description=texts[0]))
        texts = texts[1:]
        while texts:
            await result_channel.send(embed=Embed(description=texts[0]))
            texts = texts[1:]
        temporary_message = await interaction.channel.send(f"Tes résultats pour '**{expression}**' sont ici : {result.jump_url}")

    await temporary_message.delete(delay=5)
    print("search_thread done")

    return


