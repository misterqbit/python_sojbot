from disnake import AllowedMentions, Member, TextChannel, Role
from tools.message_splitter import MessageSplitter
from tools.text_managers import read_text

async def send_welcome_message(member: Member):
    print("welcome_message on")

    text = read_text("config/welcome_message.txt")
    text = text.replace('${member}', member.mention)
    text_split = MessageSplitter(text).get_message_split()

    try:
        # Send welcome message to the new member
        for message in text_split:
            await member.send(message, suppress_embeds=True, allowed_mentions=AllowedMentions(users=False))
            print("welcome_message done")

        # Post message in a specific thread
        channel_id = 919246510238076988  # ID of the channel where the message is posted
        channel = member.guild.get_channel(channel_id)
        if isinstance(channel, TextChannel):
            thread_message = f"Message de bienvenue envoyé à {member.name}"  # Include the username
            await channel.send(thread_message)

        # Check if the member is in the monitored list and notify moderators with the reason
        monitored, reason = is_monitored_user(member.id)
        if monitored:
            await notify_moderators(member, reason)

    except Exception as e:
        print(f"Failed to send welcome message to {member.mention}: {e}")

# Function to check if the user is in the monitored list and return the reason if they are
def is_monitored_user(user_id: int) -> tuple[bool, str]:
    try:
        # Read user IDs and reasons from a file (format: user_id, reason)
        with open("config/monitored_users.txt", "r") as file:
            for line in file:
                parts = line.strip().split(",", 1)  # Split by the first comma (user_id, reason)
                if len(parts) == 2:
                    monitored_id = int(parts[0].strip())
                    reason = parts[1].strip()
                    if user_id == monitored_id:
                        return True, reason
        return False, ""
    except Exception as e:
        print(f"Error reading monitored users file: {e}")
        return False, ""

# Function to notify moderators
async def notify_moderators(member: Member, reason: str):
    try:
        # Define the channel ID where the message should be sent
        channel_id = 902498718673162251  # Replace with the actual channel ID where you want to send the notification
        channel = member.guild.get_channel(channel_id)

        # Define the moderator role ID
        moderator_role_id = 902501987415900170  # Replace with the actual moderator role ID
        moderator_role = member.guild.get_role(moderator_role_id)

        if isinstance(channel, TextChannel) and isinstance(moderator_role, Role):
            # Compose the message mentioning the moderator role and including the reason
            message = f"Attention {moderator_role.mention}, un compte surveillé (ID: {member.id}) a rejoint le serveur SOJ sous le nom {member.name}. Raison de la surveillance : {reason}"
            
            # Send the message to the specified channel
            await channel.send(message, allowed_mentions=AllowedMentions(roles=True))  # Allow mentioning the role
            print(f"Notification sent to channel {channel.name} with moderator role ping.")

    except Exception as e:
        print(f"Failed to notify moderators: {e}")
        


