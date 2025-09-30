# monitor.py
processed_albums = set()  # track forwarded albums

async def monitor_new_messages(client, source_channel, target_groups):
    from telethon import events

    @client.on(events.NewMessage(chats=source_channel))
    async def handler(event):
        message = event.message
        try:
            if message.grouped_id:
                if message.grouped_id in processed_albums:
                    return  # skip already processed album

                # collect album messages
                msgs = []
                async for m in client.iter_messages(source_channel, reverse=True):
                    if m.grouped_id == message.grouped_id:
                        msgs.append(m)

                msgs = list(reversed(msgs))
                album_caption = next((m.message for m in msgs if m.message), "")

                for target in target_groups:
                    await client.send_message(
                        target,
                        message=album_caption,
                        file=[m.media for m in msgs if m.media]
                    )

                processed_albums.add(message.grouped_id)
            else:
                for target in target_groups:
                    await client.send_message(
                        target,
                        message=message.message or "",
                        file=message.media or None
                    )

        except Exception as e:
            print(f"Error forwarding new message: {e}")

    # Keep running
    from asyncio import Event
    stop_event = Event()
    await stop_event.wait()  # keep monitor alive
