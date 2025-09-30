async def forward_all_messages(client, source_channel, target_groups, owner_id):
    """
    Forward all old messages from source_channel to target_groups.
    Notifications (start/done) are sent only to owner_id (Saved Messages).
    Skips protected media and service messages, and logs skipped messages.
    """
    # Notify start
    await client.send_message(owner_id, "🚀 Starting to copy all old messages (including albums, media)...")

    processed_albums = set()
    skipped_messages = []

    async for message in client.iter_messages(source_channel, reverse=True):
        try:
            # Skip service messages
            if message.service:
                skipped_messages.append(f"Service message {message.id}")
                continue

            # Skip messages with media that cannot be forwarded
            if message.media and getattr(message.media, "restricted", False):
                skipped_messages.append(f"Protected media {message.id}")
                continue

            if message.grouped_id:
                if message.grouped_id in processed_albums:
                    continue

                # collect album messages
                msgs = []
                async for m in client.iter_messages(source_channel, reverse=True):
                    if m.grouped_id == message.grouped_id:
                        # Skip service messages inside album
                        if m.service:
                            skipped_messages.append(f"Service message in album {m.id}")
                            continue
                        # Skip restricted media inside album
                        if m.media and getattr(m.media, "restricted", False):
                            skipped_messages.append(f"Protected media in album {m.id}")
                            continue
                        msgs.append(m)

                if not msgs:
                    skipped_messages.append(f"Skipped empty album {message.grouped_id}")
                    continue  # skip empty albums

                msgs = list(reversed(msgs))  # keep original order

                # Use the first non-empty caption for the album
                album_caption = next((m.message for m in msgs if m.message), "")

                for target in target_groups:
                    await client.send_message(
                        target,
                        message=album_caption,
                        file=[m.media for m in msgs if m.media]
                    )
                processed_albums.add(message.grouped_id)

            else:
                # normal single message
                for target in target_groups:
                    await client.send_message(
                        target,
                        message=message.message or "",
                        file=message.media or None
                    )

        except Exception:
            skipped_messages.append(f"Failed to forward {message.id}")

    # Notify done
    await client.send_message(owner_id, "🎉 Done copying all messages!")

    # Log skipped messages to owner_id
    if skipped_messages:
        skipped_text = "⚠️ Skipped messages:\n" + "\n".join(skipped_messages)
        # Telegram messages have a 4096 char limit, split if needed
        for i in range(0, len(skipped_text), 4000):
            await client.send_message(owner_id, skipped_text[i:i+4000])
