import discord
import yt_dlp
import os
import re

TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

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

    async with message.channel.typing():

        # -------------------------
        # 1. TRY VIDEO DOWNLOAD
        # -------------------------
        video_opts = {
            'outtmpl': 'video.%(ext)s',
            'format': 'best[height<=720]/best',
            'cookiefile': 'cookies.txt',
            'quiet': True,
            'merge_output_format': 'mp4'
        }

        try:
            with yt_dlp.YoutubeDL(video_opts) as ydl:
                info = ydl.extract_info(url, download=True)

            file_path = None

            if 'entries' in info:
                info = info['entries'][0]

            file_path = ydl.prepare_filename(info)

            if os.path.exists(file_path):
                size = os.path.getsize(file_path)

                if size <= 8 * 1024 * 1024:
                    await message.channel.send(file=discord.File(file_path))
                    os.remove(file_path)
                    return

        except Exception:
            pass  # video failed → try images next

        # -------------------------
        # 2. TRY IMAGE DOWNLOAD
        # -------------------------
        image_opts = {
            'outtmpl': 'image.%(ext)s',
            'format': 'best',
            'cookiefile': 'cookies.txt',
            'quiet': True
        }

        try:
            with yt_dlp.YoutubeDL(image_opts) as ydl:
                info = ydl.extract_info(url, download=True)

            files = []

            entries = info.get('entries', [info])

            for entry in entries:
                filename = ydl.prepare_filename(entry)

                if os.path.exists(filename):
                    files.append(discord.File(filename))
                    os.remove(filename)

            if files:
                await message.channel.send(files=files)
                return

        except Exception:
            pass  # image failed → fallback

        # -------------------------
        # 3. FINAL FALLBACK
        # -------------------------
        await message.channel.send(
            "⚠️ Couldn’t fully process this Instagram post. Here’s the link instead:\n" + url
        )

client.run(TOKEN)
