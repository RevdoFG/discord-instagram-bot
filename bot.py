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

        # -----------------------------
        # STEP 1: PRE-CHECK METADATA
        # -----------------------------
        base_opts = {
            'cookiefile': 'cookies.txt',
            'quiet': True,
            'skip_download': True
        }

        try:
            with yt_dlp.YoutubeDL(base_opts) as ydl:
                info = ydl.extract_info(url, download=False)

            # Detect if likely video or image post
            is_video = False

            if info.get("ext") == "mp4":
                is_video = True

            if "formats" in info:
                for f in info["formats"]:
                    if f.get("vcodec") != "none":
                        is_video = True
                        break

        except Exception:
            is_video = False  # fallback assumption

        # -----------------------------
        # STEP 2: VIDEO PATH
        # -----------------------------
        if is_video:
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

                if 'entries' in info:
                    info = info['entries'][0]

                filename = ydl.prepare_filename(info)

                if os.path.exists(filename):
                    size = os.path.getsize(filename)

                    if size <= 8 * 1024 * 1024:
                        await message.channel.send(file=discord.File(filename))
                        os.remove(filename)
                        return

            except Exception:
                pass  # fall through to images

        # -----------------------------
        # STEP 3: IMAGE / CAROUSEL PATH
        # -----------------------------
        image_opts = {
            'outtmpl': 'image.%(ext)s',
            'format': 'best',
            'cookiefile': 'cookies.txt',
            'quiet': True
        }

        try:
            with yt_dlp.YoutubeDL(image_opts) as ydl:
                info = ydl.extract_info(url, download=True)

            entries = info.get('entries', [info])
            files = []

            for entry in entries:
                filename = ydl.prepare_filename(entry)

                if os.path.exists(filename):
                    files.append(discord.File(filename))
                    os.remove(filename)

            if files:
                await message.channel.send(files=files)
                return

        except Exception:
            pass

        # -----------------------------
        # STEP 4: FINAL FALLBACK
        # -----------------------------
        await message.channel.send(
            "⚠️ Couldn’t fully process this Instagram post. Here’s the link instead:\n" + url
        )

client.run(TOKEN)
