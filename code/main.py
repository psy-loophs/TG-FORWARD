import os
import asyncio
import threading
from fastapi import FastAPI
import uvicorn
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from dotenv import load_dotenv
from forward import forward_messages, stop_forwarding

# === LOAD ENV VARIABLES ===
load_dotenv()
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
SESSION_STRING = os.getenv("SESSION_STRING")
SOURCE_CHANNEL = int(os.getenv("SOURCE_CHANNEL"))
TARGET_GROUPS = [int(x.strip()) for x in os.getenv("TARGET_GROUPS").split(",")]
OWNER_ID = int(os.getenv("OWNER_ID"))  # Only owner can control the bot

client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

# === FASTAPI HEALTH SERVER ===
app = FastAPI()

@app.get("/")
async def root():
    return {"status": "ok", "message": "Userbot is alive"}

def run_health_server():
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

# === COMMAND HANDLING ===
forwarding_task = None

@client.on(events.NewMessage(pattern=r"^(/|!)forward$"))
async def start_forward(event):
    global forwarding_task

    if event.sender_id != OWNER_ID:
        return  # Ignore non-owner

    if event.chat_id not in TARGET_GROUPS:
        return  # Only respond in target groups

    if forwarding_task and not forwarding_task.done():
        await event.reply("⚠️ Forwarding is already running!")
        return

    await event.reply("🚀 Starting forwarding messages...")
    forwarding_task = asyncio.create_task(forward_messages(client, SOURCE_CHANNEL, TARGET_GROUPS))

@client.on(events.NewMessage(pattern=r"^(/|!)stop$"))
async def stop_forward(event):
    global forwarding_task
    if event.sender_id != OWNER_ID:
        return

    if event.chat_id not in TARGET_GROUPS:
        return

    if forwarding_task and not forwarding_task.done():
        stop_forwarding()
        await event.reply("⏹ Stopped forwarding messages.")
    else:
        await event.reply("⚠️ Forwarding is not running!")

# === START BOT ===
async def main():
    await client.start()
    print("🚀 Userbot is running...", flush=True)
    threading.Thread(target=run_health_server, daemon=True).start()
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
