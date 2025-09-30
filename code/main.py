import os
import asyncio
from fastapi import FastAPI
from dotenv import load_dotenv
from telethon import TelegramClient, events
from telethon.sessions import StringSession

from forward import forward_all_messages

# === Load environment variables ===
load_dotenv()

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
SESSION_STRING = os.getenv("SESSION_STRING")
SOURCE_CHANNEL = int(os.getenv("SOURCE_CHANNEL"))
TARGET_GROUPS = [int(x) for x in os.getenv("TARGET_GROUPS", "").split(",") if x]

# === FastAPI App ===
app = FastAPI()

# === Telegram Client ===
client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

OWNER_ID = None
forwarding_started = False


@app.api_route("/", methods=["GET", "HEAD"])
async def home():
    """Root endpoint for health check and status"""
    return {"status": "running"}


@client.on(events.NewMessage(pattern=r"^!start$"))
async def start_handler(event):
    global forwarding_started, OWNER_ID

    # Only allow owner
    if event.sender_id != OWNER_ID:
        return  

    if forwarding_started:
        await event.respond("⚠️ Forwarding already started!")
        return

    forwarding_started = True
    await event.respond("🚀 Forwarding started... copying old messages.")
    asyncio.create_task(forward_all_messages(client, SOURCE_CHANNEL, TARGET_GROUPS))


async def init_owner():
    """Detect the session owner automatically."""
    global OWNER_ID
    me = await client.get_me()
    OWNER_ID = me.id
    print(f"✅ Detected owner ID: {OWNER_ID}")


def main():
    async def runner():
        await client.start()
        await init_owner()

    loop = asyncio.get_event_loop()
    loop.run_until_complete(runner())

    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
