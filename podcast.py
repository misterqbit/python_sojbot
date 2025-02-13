import requests
import feedparser
from playsound import playsound


def get_podcast_info(rss_feed_url):
    # Parse the RSS feed
    feed = feedparser.parse(rss_feed_url)

    podcast_info = []
    # Extract MP3 links and extra information
    for entry in feed.entries:
        mp3_link = None
        duration = None
        title = None
        published = None

        # Extract MP3 link
        for link in entry.links:
            if link.type == "audio/mpeg":
                mp3_link = link.href

        # Extract other information
        if 'duration' in entry:
            duration = entry.duration
        if 'title' in entry:
            title = entry.title
        if 'published' in entry:
            published = entry.published

        # Append to the podcast_info list
        podcast_info.append({"title": title, "duration": duration, "published": published, "mp3_link": mp3_link})

    return podcast_info


async def play(ctx):
    voice_channel = ctx.author.voice.channel
    if voice_channel:
        try:
            await voice_channel.connect()
            rss_feed_url = "https://feeds.acast.com/public/shows/5b7ac427c6a58e726f576cff"
            podcast_info = get_podcast_info(rss_feed_url)
            for info in podcast_info:
                mp3_link = info["mp3_link"]
                if mp3_link:
                    response = requests.get(mp3_link)
                    with open("audio.mp3", "wb") as file:
                        file.write(response.content)

                    playsound("audio.mp3")

            await ctx.voice_client.disconnect()
        except Exception as e:
            print(e)
            await ctx.send("An error occurred while playing the audio.")
    else:
        await ctx.send("You need to be in a voice channel to use this command.")
