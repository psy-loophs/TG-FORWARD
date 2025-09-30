# continue.py
import asyncio
from telethon import events
from forward import forward_all_messages  # import your existing function

async def monitor_and_forward(client, source_channel, target_groups, reply_to=None):
    """
    Forward all existing messages first, then continuously forward new messages.
    """
    # Step 1: Forward all existing messages
    if reply_to:
        await reply_to.respond("🚀 Starting to copy all old messages (including albums, media)...")
    await forward_all_messages(client, source_channel, target_groups, reply_to)

    # Step 2: Listen for new messages
    processed_albums = set()  # track albums already forwarded

    @client.on(events.NewMessage(chats=source_channel))
    async def new_message_handler(event):
        message = event.message
        try:
            if message.grouped_id:
                if message.grouped_id in processed_albums:
                    return  # avoid duplicate albums

                # Collect all messages in the album that might have arrived simultaneously
                msgs = [message]
                async for m in client.iter_messages(source_channel, min_id=message.id - 1, reverse=True):
                    if m.grouped_id == message.grouped_id and m.id != message.id:
                        msgs.append(m)
                msgs = list(reversed(msgs))  # keep original order

                album_caption = next((m.message for m in msgs if m.message), "")

                for target in target_groups:
                    await client.send_message(
                        target,
                        message=album_caption,
                        file=[m.media for m in msgs if m.media]
                    )

                processed_albums.add(message.grouped_id)

            else:
                # Normal single message
                for target in target_groups:
                    await client.send_message(
                        target,
                        message=message.message or "",
                        file=message.media or None
                    )

        except Exception:
            pass

    # Keep the script alive
    while True:
        await asyncio.sleep(10)


# Example usage:
# if __name__ == "__main__":
#     import os
#     from telethon import TelegramClient
#     from dotenv import load_dotenv
#     load_dotenv()
# 
#     API_ID = int(os.getenv("API_ID"))
#     API_HASH = os.getenv("API_HASH")
#     SESSION_STRING = os.getenv("SESSION_STRING")
#     SOURCE_CHANNEL = int(os.getenv("SOURCE_CHANNEL"))
#     TARGET_GROUPS = [int(x) for x in os.getenv("TARGET_GROUPS", "").split(",")]
# 
#     client = TelegramClient("session", API_ID, API_HASH)
# 
#     async def main():
#         await client.start(phone=lambda: input("Enter your phone: "))
#         await monitor_and_forward(client, SOURCE_CHANNEL, TARGET_GROUPS)
# 
#     asyncio.run(main())
