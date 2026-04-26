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

    try:
        # 👇 Typing indicator starts here
        async with message.channel.typing():

            ydl_opts = {
                'outtmpl': '%(title)s.%(ext)s',
                'format': 'best[height<=720]/best',
                'cookiefile': 'cookies.txt',
                'quiet': True,
                'merge_output_format': 'mp4'
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)

            files_to_send = []

            entries = info.get('entries', [info])

            for entry in entries:
                filename = ydl.prepare_filename(entry)

                if not os.path.exists(filename):
                    base = filename.rsplit(".", 1)[0]
                    for ext in ["mp4", "jpg", "jpeg", "png", "webp"]:
                        if os.path.exists(base + "." + ext):
                            filename = base + "." + ext
                            break

                if os.path.exists(filename):
                    files_to_send.append(filename)

            discord_files = []
            fallback_links = []

            for file in files_to_send:
                file_size = os.path.getsize(file)

                if file.endswith((".mp4", ".mov")) and file_size > 8 * 1024 * 1024:
                    fallback_links.append(url)
                    continue

                discord_files.append(discord.File(file))

        # 👇 Typing indicator stops BEFORE sending

        # Send in batches of 10
        for i in range(0, len(discord_files), 10):
            await message.channel.send(files=discord_files[i:i+10])

        if fallback_links:
            await message.channel.send(
                "Videos were too large " + url
            )

        # Cleanup
        for file in files_to_send:
            if os.path.exists(file):
                os.remove(file)

    except Exception as e:
        await message.channel.send(f"❌ Error: {str(e)}")

client.run(TOKEN)
