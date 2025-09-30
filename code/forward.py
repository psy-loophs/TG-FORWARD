async def forward_all_messages(client, source_channel, target_groups):
    print("🚀 Starting to copy all old messages (including albums, media)...")

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

                for target in target_groups:
                    await client.send_message(
                        target,
                        message=msgs[0].message or "",
                        file=[m.media for m in msgs if m.media]
                    )
                print(f"📸 Copied album {message.grouped_id}")
                processed_albums.add(message.grouped_id)

            else:
                # normal single message
                for target in target_groups:
                    await client.send_message(
                        target,
                        message=message.message or "",
                        file=message.media or None
                    )
                print(f"✅ Copied message {message.id}")

        except Exception as e:
            print(f"❌ Failed at {message.id}: {e}")

    print("🎉 Done copying all messages!")
