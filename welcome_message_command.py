from disnake import AllowedMentions, Member
from tools.message_splitter import MessageSplitter
from tools.text_managers import read_text

async def send_welcome_message(member: Member):
    print("welcome_message on")

    text = read_text("config/welcome_message.txt")
    text = text.replace('${member}', member.mention)
    text_split = MessageSplitter(text).get_message_split()

    try:
        for message in text_split:
            await member.send(message, suppress_embeds=True, allowed_mentions=AllowedMentions(users=False))
            print("welcome_message done")

    except Exception as e:
        print(f"Failed to send welcome message to {member.mention}: {e}")

