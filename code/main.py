from telethon import TelegramClient
from dotenv import load_dotenv
import os
import asyncio

# === LOAD ENV VARIABLES ===
load_dotenv()

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
SESSION_STRING = os.getenv("SESSION_STRING")  # your saved session string
SOURCE_CHANNEL = int(os.getenv("SOURCE_CHANNEL"))

# multiple target groups separated by comma in .env
TARGET_GROUPS = [int(x.strip()) for x in os.getenv("TARGET_GROUPS").split(",")]

# === CREATE CLIENT FROM SESSION STRING ===
client = TelegramClient.from_string(SESSION_STRING, API_ID, API_HASH)

async def main():
    print("🚀 Starting to copy all old messages (including albums, media)...")

    processed_albums = set()  # track albums

    async for message in client.iter_messages(SOURCE_CHANNEL, reverse=True):
        try:
            # handle albums
            if message.grouped_id:
                if message.grouped_id in processed_albums:
                    continue  # already sent this album

                # collect all messages in the album
                album_msgs = []
                async for m in client.iter_messages(SOURCE_CHANNEL, reverse=True):
                    if m.grouped_id == message.grouped_id:
                        album_msgs.append(m)

                album_msgs = list(reversed(album_msgs))  # original order

                # prepare media + captions for album
                media_list = [m.media for m in album_msgs if m.media]
                captions = [m.message or "" for m in album_msgs if m.media]

                # send album to all target groups
                for target in TARGET_GROUPS:
                    if len(media_list) > 1:
                        # send as grouped media (album)
                        await client.send_file(
                            target,
                            files=media_list,
                            caption=captions[0]  # only the first caption appears as album caption
                        )
                    else:
                        # single media with its caption
                        await client.send_file(
                            target,
                            files=media_list[0],
                            caption=captions[0] if captions else ""
                        )
                    print(f"📸 Copied album {message.grouped_id} to {target}")

                processed_albums.add(message.grouped_id)

            else:
                # single message
                for target in TARGET_GROUPS:
                    await client.send_message(
                        target,
                        message=message.message or "",
                        file=message.media or None
                    )
                    print(f"✅ Copied message {message.id} to {target}")

        except Exception as e:
            print(f"❌ Failed at {message.id}: {e}")

    print("🎉 Done copying all messages!")

# run
async def run():
    await client.start()  # uses session string
    await main()

if __name__ == "__main__":
    asyncio.run(run())
