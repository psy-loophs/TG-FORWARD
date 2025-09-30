import os
import asyncio
from fastapi import FastAPI, Request
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

# Serve dummy favicon to avoid 404
@app.get("/favicon.ico")
@app.head("/favicon.ico")
async def favicon():
    return b"", 204

# Uptime monitor compatible root
@app.get("/")
@app.head("/")
async def home(request: Request):
    return {"status": "running"}

# === Telegram Client ===
client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

OWNER_ID = None
forwarding_started = False

# === Telegram Handlers ===
@client.on(events.NewMessage(pattern=r"^!start$"))
async def start_handler(event):
    global forwarding_started, OWNER_ID

    # Only allow owner
    if OWNER_ID is None:
        await event.respond("⚠️ Owner not detected yet. Please try again in a few seconds.")
        return

    if event.sender_id != OWNER_ID:
        await event.respond("❌ You are not the owner!")
        return

    if forwarding_started:
        await event.respond("⚠️ Forwarding already started!")
        return

    forwarding_started = True
    await event.respond("🚀 Forwarding started... copying old messages.")
    asyncio.create_task(forward_all_messages(client, SOURCE_CHANNEL, TARGET_GROUPS))

# === Initialize owner ID ===
async def init_owner():
    global OWNER_ID
    me = await client.get_me()
    OWNER_ID = me.id
    print(f"✅ Detected owner ID: {OWNER_ID}")

# === Run Telethon + FastAPI together ===
async def start_services():
    # Start Telegram client and detect owner before listening
    await client.start()
    await init_owner()
    print("✅ Telegram client started and owner detected.")

    # Start FastAPI (uvicorn) in the same event loop
    import uvicorn
    config = uvicorn.Config(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)), log_level="info")
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == "__main__":
    asyncio.run(start_services())
