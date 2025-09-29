import asyncio
from telethon import TelegramClient
from telethon.tl.types import InputPeerChannel

# ANSI COLORS
class C:
    GREEN = "\033[92m"
    RED = "\033[91m"
    BLUE = "\033[94m"
    YELLOW = "\033[93m"
    RESET = "\033[0m"

# Forwarding control
forwarding_task = None
stop_forwarding_flag = False

async def forward_messages(client: TelegramClient, source_channel: int, target_groups: list):
    global stop_forwarding_flag
    stop_forwarding_flag = False
    print(f"{C.BLUE}🚀 Starting to copy all messages...{C.RESET}", flush=True)
    
    processed_albums = set()
    all_messages = [m async for m in client.iter_messages(source_channel)]
    all_messages.sort(key=lambda m: m.date)

    for message in all_messages:
        if stop_forwarding_flag:
            print(f"{C.YELLOW}⏹ Forwarding stopped by command.{C.RESET}", flush=True)
            break

        try:
            # Handle albums
            if message.grouped_id:
                if message.grouped_id in processed_albums:
                    continue

                album_msgs = [m for m in all_messages if m.grouped_id == message.grouped_id]
                album_msgs.sort(key=lambda m: m.id)
                media_list = [m.media for m in album_msgs if m.media]
                captions = [m.message or "" for m in album_msgs if m.media]

                for target in target_groups:
                    if len(media_list) > 1:
                        await client.send_file(
                            target,
                            files=media_list,
                            caption=captions[0] if captions else ""
                        )
                    else:
                        await client.send_file(
                            target,
                            files=media_list[0],
                            caption=captions[0] if captions else ""
                        )
                    print(f"{C.BLUE}📸 Copied Album {message.grouped_id} → {target}{C.RESET}", flush=True)

                processed_albums.add(message.grouped_id)

            else:
                for target in target_groups:
                    await client.send_message(
                        target,
                        message=message.message or "",
                        file=message.media or None
                    )
                    print(f"{C.GREEN}✅ Copied Message {message.id} → {target}{C.RESET}", flush=True)

        except Exception as e:
            print(f"{C.RED}❌ Failed at {message.id}: {e}{C.RESET}", flush=True)

    print(f"{C.YELLOW}🎉 Finished forwarding messages!{C.RESET}", flush=True)

def stop_forwarding():
    global stop_forwarding_flag
    stop_forwarding_flag = True
