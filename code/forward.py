import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,  # INFO level logs everything important
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)


async def forward_all_messages(client, source_channel, target_groups, reply_to=None):
    """
    Forward all old messages from source_channel to target_groups.
    reply_to: message object to reply with start/done notifications
    """
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

                # Use the first non-empty caption for the album
                album_caption = next((m.message for m in msgs if m.message), "")

                for target in target_groups:
                    await client.send_message(
                        target,
                        message=album_caption,
                        file=[m.media for m in msgs if m.media]
                    )
                logger.info(f"📸 Copied album {message.grouped_id}")
                processed_albums.add(message.grouped_id)

            else:
                # normal single message
                for target in target_groups:
                    await client.send_message(
                        target,
                        message=message.message or "",
                        file=message.media or None
                    )
                logger.info(f"✅ Copied message {message.id}")

        except Exception as e:
            logger.error(f"❌ Failed at {message.id}: {e}")

    if reply_to:
        await reply_to.respond("🎉 Done copying all messages!")
