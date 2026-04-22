import discord
import re
import yt_dlp
import os
import time

import os
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

REEL_REGEX = r"(https?://(www\.)?instagram\.com/reel/[^\s]+)"

# simple cooldown to avoid rate limits
last_download_time = 0
COOLDOWN_SECONDS = 10

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")

@client.event
async def on_message(message):
    global last_download_time

    if message.author == client.user:
        return

    match = re.search(REEL_REGEX, message.content)
    if not match:
        return

    # cooldown protection
    now = time.time()
    if now - last_download_time < COOLDOWN_SECONDS:
        await message.channel.send("⏳ Slow down a bit — Instagram rate limit protection active.")
        return

    last_download_time = now

    url = match.group(0)
    await message.channel.send("faggot")

    ydl_opts = {
        'outtmpl': 'video.%(ext)s',
        'format': 'mp4',
        'cookiefile': 'cookies.txt',
        'quiet': True
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        # find downloaded file
        for file in os.listdir():
            if file.startswith("video"):
                await message.channel.send(file=discord.File(file))
                os.remove(file)
                break

    except Exception as e:
        await message.channel.send(f"❌ Error: {e}")

client.run(TOKEN)