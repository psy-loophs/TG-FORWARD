async def forward_all_messages(client, source_channel, target_groups, reply_to=None):
    
    if reply_to:
        await reply_to.respond("🚀 Starting to copy all old messages (including albums, media)...")

    processed_albums = set()

    async for message in client.iter_messages(source_channel, reverse=True):
        try:
            if message.grouped_id:
                if message.grouped_id in processed_albums:
                    continue

                # collect album messages
                msgs = []
                async for m in client.iter_messages(source_channel, reverse=True):
                    if m.grouped_id == message.grouped_id:
                        msgs.append(m)

                msgs = list(reversed(msgs))  # keep original order

                # Use the **first non-empty caption** for the album
                album_caption = next((m.message for m in msgs if m.message), "")

                for target in target_groups:
                    await client.send_message(
                        target,
                        message=album_caption,
                        file=[m.media for m in msgs if m.media]
                    )
                
                processed_albums.add(message.grouped_id)  # prevent duplicate albums

            else:
                # normal single message
                for target in target_groups:
                    await client.send_message(
                        target,
                        message=message.message or "",
                        file=message.media or None
                    )

        except Exception as e:
            pass


# forward.py
import asyncio
import importlib

# Keep your existing forward_all_messages function as-is
# ... (your existing forward_all_messages code)

# Optional: global set to share processed albums with monitor
processed_albums_global = set()

async def forward_and_monitor(client, source_channel, target_groups, reply_to=None):
    # Step 1: Forward all old messages
    await forward_all_messages(client, source_channel, target_groups, reply_to)
    
    # Step 2: Update global processed albums (optional if you want to skip duplicates)
    global processed_albums_global
    # processed_albums_global = processed_albums from forward_all_messages if needed

    # Step 3: Dynamically import and start monitor.py
    monitor = importlib.import_module("monitor")  # make sure monitor.py is in same folder
    await monitor.monitor_new_messages(client, source_channel, target_groups)
