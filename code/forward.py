async def forward_all_messages(client, source_channel, target_groups, reply_to=None):
    
    if reply_to:
        await reply_to.respond("🚀 Starting to copy all old messages (including albums, media)...")

    processed_albums = set()

    async for message in client.iter_messages(source_channel, reverse=True):
        try:
            if message.grouped_id:
                if message.grouped_id in processed_albums:
                    continue

                
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
            print(e)

