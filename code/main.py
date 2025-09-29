from telethon import TelegramClient
from telethon.sessions import StringSession
from dotenv import load_dotenv
import os
import asyncio
import socket

# === LOAD ENV VARIABLES ===
load_dotenv()

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
SESSION_STRING = os.getenv("SESSION_STRING")
SOURCE_CHANNEL = int(os.getenv("SOURCE_CHANNEL"))
TARGET_GROUPS = [int(x.strip()) for x in os.getenv("TARGET_GROUPS").split(",")]

# === CREATE CLIENT USING StringSession ===
client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

# === ANSI COLORS ===
class C:
    GREEN = "\033[92m"
    RED = "\033[91m"
    BLUE = "\033[94m"
    YELLOW = "\033[93m"
    RESET = "\033[0m"

# === DUMMY PORT FOR RENDER WEB SERVICE ===
PORT = int(os.getenv("PORT", 10000))
sock = socket.socket()
sock.bind(("0.0.0.0", PORT))
sock.listen(1)
print(f"{C.YELLOW}🔌 Listening on port {PORT} (dummy for Render){C.RESET}")

async def main():
    print(f"{C.BLUE}🚀 Starting to copy all old messages (including albums, media)...{C.RESET}")

    processed_albums = set()

    async for message in client.iter_messages(SOURCE_CHANNEL, reverse=True):
        try:
            # Detect message type
            msg_type = "Message"
            if message.grouped_id:
                msg_type = "Album"
            elif message.sticker:
                msg_type = "Sticker"
            elif message.gif:
                msg_type = "GIF"
            elif message.media:
                if message.audio or message.voice:
                    msg_type = "Audio"
                elif message.document:
                    msg_type = "File"
                elif message.photo:
                    msg_type = "Photo"
                else:
                    msg_type = "Media"
            elif message.message and any(char in message.message for char in "😀😂❤️"):
                msg_type = "Emoji"

            # Handle albums
            if message.grouped_id:
                if message.grouped_id in processed_albums:
                    continue

                album_msgs = []
                async for m in client.iter_messages(SOURCE_CHANNEL, reverse=True):
                    if m.grouped_id == message.grouped_id:
                        album_msgs.append(m)

                album_msgs = list(reversed(album_msgs))
                media_list = [m.media for m in album_msgs if m.media]
                captions = [m.message or "" for m in album_msgs if m.media]

                for target in TARGET_GROUPS:
                    if len(media_list) > 1:
                        await client.send_file(
                            target,
                            files=media_list,
                            caption=captions[0] if captions else ""
                        )
                    else:
                        await client.send_file(
                            target,
                            files=media_list[0],
                            caption=captions[0] if captions else ""
                        )
                    print(f"{C.BLUE}📸 Copied {msg_type} (Album) {message.grouped_id} → {target}{C.RESET}")

                processed_albums.add(message.grouped_id)

            else:
                for target in TARGET_GROUPS:
                    await client.send_message(
                        target,
                        message=message.message or "",
                        file=message.media or None
                    )
                    print(f"{C.GREEN}✅ Copied {msg_type} {message.id} → {target}{C.RESET}")

        except Exception as e:
            print(f"{C.RED}❌ Failed at {message.id}: {e}{C.RESET}")

    print(f"{C.YELLOW}🎉 Done copying all messages!{C.RESET}")

# run
async def run():
    await client.start()
    await main()

if __name__ == "__main__":
    asyncio.run(run())
