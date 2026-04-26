import discord
import yt_dlp
import os
import re

TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# Detect Instagram links
INSTAGRAM_REGEX = r"(https?://(www\.)?instagram\.com/[^\s]+)"

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    match = re.search(INSTAGRAM_REGEX, message.content)
    if not match:
        return

    url = match.group(0)

    await message.channel.send("📥 Downloading Reel...")

    try:
        ydl_opts = {
            'outtmpl': 'video.%(ext)s',
            'format': 'bestvideo[height<=720]+bestaudio/best[height<=720]',
            'cookiefile': 'cookies.txt',
            'quiet': True,
            'merge_output_format': 'mp4'
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        # Ensure file is mp4
        if not filename.endswith(".mp4"):
            filename = filename.rsplit(".", 1)[0] + ".mp4"

        # Check file size
        file_size = os.path.getsize(filename)

        if file_size > 8 * 1024 * 1024:
            await message.channel.send(
                "video too large:\n" + url
            )
        else:
            await message.channel.send(file=discord.File(filename))

        # Cleanup file
        os.remove(filename)

    except Exception as e:
        await message.channel.send(f"❌ Error: {str(e)}")

client.run(TOKEN)
