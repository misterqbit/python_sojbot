import disnake
from flask import Flask, request, jsonify
from config import TWITCH_CLIENT_ID, DISCORD_BOT_TOKEN

app = Flask(__name__)

# Discord channel ID
DISCORD_CHANNEL_ID = 1236779578748567613  # Your Discord channel ID

# Set up Disnake client
disnake_client = disnake.Client()

@disnake_client.event
async def on_ready():
    print(f'Logged in as {disnake_client.user}')

@app.route('/twitch/webhook', methods=['POST'])
def twitch_webhook():
    # Verify the request
    challenge = request.json.get('challenge')
    if challenge:
        return jsonify({'challenge': challenge})

    # Handle notification
    data = request.json
    event_type = request.headers.get('Twitch-Eventsub-Message-Type')
    if event_type == 'stream.online':
        channel_name = data['event']['broadcaster_user_name']
        if channel_name in ['origatwitch', 'silenceonjoue', 'origatwitch', 'kocobe', 'ellenreplay']:
            stream_title = data['event']['title']
            send_discord_message(f"{channel_name} vient de démarrer son stream sur Twitch! {stream_title}")
    
    return jsonify({'status': 'ok'})

def send_discord_message(message):
    # Code to send a message to Discord goes here
    channel = disnake_client.get_channel(DISCORD_CHANNEL_ID)
    disnake.loop.create_task(channel.send(message))


"""
import disnake
import asyncio
import requests
from config import TWITCH_CLIENT_ID, DISCORD_BOT_TOKEN

# Twitch channel ID
TWITCH_CHANNEL_IDS = ['silenceonjoue', 'origatwitch', 'kocobe', 'ellenreplay']

# Discord channel ID
DISCORD_CHANNEL_ID = "1236779578748567613"  # Your Discord channel ID

# Function to check if a Twitch channel is live
async def check_twitch(channel_id):
    url = f'https://api.twitch.tv/helix/streams?user_login={channel_id}'
    headers = {'Client-ID': TWITCH_CLIENT_ID}
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        data = response.json()
        if data['data']:
            return True
    return False

# Function to post a message in Discord
async def post_message(channel_id):
    channel = disnake.utils.get(disnake.ext.commands.Bot.get_all_channels(), id=DISCORD_CHANNEL_ID)
    await channel.send(f"Hey! {channel_id} is live now! Go check it out!")

# Main function
async def main():
    await disnake.login(DISCORD_BOT_TOKEN)
    while True:
        for channel_id in TWITCH_CHANNEL_IDS:
            if await check_twitch(channel_id):
                await post_message(channel_id)
        await asyncio.sleep(300)  # Check every 5 minutes

# Run the main function
if __name__ == "__main__":
    asyncio.run(main())
"""
