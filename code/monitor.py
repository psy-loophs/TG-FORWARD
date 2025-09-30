# continue.py
import asyncio
from telethon import events

processed_albums = set()  # keep track of albums already forwarded

async def monitor_new_messages(client, source_channel, target_groups, reply_to=None):
    """
    Monitor new messages in `source_channel` and forward them to `target_groups`.
    Handles albums, single messages, and captions.
    """
    if reply_to:
        await reply_to.respond("👀 Monitoring new messages from the source channel...")

    @client.on(events.NewMessage(chats=source_channel))
    async def handler(event):
        message = event.message

        try:
            if message.grouped_id:
                # prevent duplicate albums
                if message.grouped_id in processed_albums:
                    return

                # collect all messages in the album
                msgs = []
                async for m in client.iter_messages(source_channel, reverse=True):
                    if m.grouped_id == message.grouped_id:
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
                # single message
                for target in target_groups:
                    await client.send_message(
                        target,
                        message=message.message or "",
                        file=message.media or None
                    )

        except Exception as e:
            print(f"Error forwarding message: {e}")

    # Keep the client running
    await client.run_until_disconnected()
