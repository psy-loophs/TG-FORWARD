import os
import asyncio
from fastapi import FastAPI
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from forward import forward_all_messages

load_dotenv()

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")  
SESSION_STRING = os.getenv("SESSION_STRING")
SOURCE_CHANNEL = int(os.getenv("SOURCE_CHANNEL"))
TARGET_GROUPS = [int(x) for x in os.getenv("TARGET_GROUPS", "").split(",") if x]


client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
OWNER_ID = None
forwarding_started = False


@client.on(events.NewMessage(pattern=r"^!start$"))
async def start_handler(event):
    global forwarding_started, OWNER_ID

    if OWNER_ID is None:
        await event.respond("⚠️ Owner not detected yet. Please try again in a few seconds.")
        return

    if event.sender_id != OWNER_ID:
        return

    if forwarding_started:
        await event.respond("⚠️ Forwarding already started!")
        return

    forwarding_started = True
    await event.respond("🚀 Forwarding started... copying old messages.")
    asyncio.create_task(forward_all_messages(client, SOURCE_CHANNEL, TARGET_GROUPS))


async def init_owner():
    global OWNER_ID
    me = await client.get_me()
    OWNER_ID = me.id
    print(f"✅ Detected owner ID: {OWNER_ID}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await client.start()
    await init_owner()
    print("✅ Telegram client started and owner detected.")
    yield
    await client.disconnect()

app = FastAPI(lifespan=lifespan)


@app.get("/favicon.ico")
@app.head("/favicon.ico")
async def favicon():
    return b"", 204


@app.get("/")
@app.head("/")
async def home():
    return {"status": "running"}


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, log_level="info")
