import asyncio
import json
import os
from telethon import TelegramClient

STATE_FILE = "forward_state.json"

# === COLORS ===
class C:
    GREEN = "\033[92m"
    RED = "\033[91m"
    BLUE = "\033[94m"
    YELLOW = "\033[93m"
    RESET = "\033[0m"

# === CONTROL FLAGS ===
stop_forwarding_flag = False


# === STATE MANAGEMENT ===
def load_state():
    """Load last forwarded message ID from file"""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}

def save_state(state):
    """Save last forwarded message ID to file"""
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)


# === FORWARDING LOGIC ===
async def forward_messages(client: TelegramClient, source_channel: int, target_groups: list):
    """
    Forward all new messages from source_channel → target_groups
    Resumes from last saved message ID if available.
    """
    global stop_forwarding_flag
    stop_forwarding_flag = False

    state = load_state()
    last_id = state.get(str(source_channel), 0)

    print(f"{C.BLUE}🚀 Starting forwarding from message ID > {last_id}{C.RESET}", flush=True)

    processed_albums = set()

    # Fetch all messages newer than last_id
    all_messages = [m async for m in client.iter_messages(source_channel, min_id=last_id)]
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

            # Save last processed ID
            state[str(source_channel)] = message.id
            save_state(state)

        except Exception as e:
            print(f"{C.RED}❌ Failed at {message.id}: {e}{C.RESET}", flush=True)

    print(f"{C.YELLOW}🎉 Finished forwarding messages!{C.RESET}", flush=True)


def stop_forwarding():
    """
    Set flag to stop forwarding loop.
    """
    global stop_forwarding_flag
    stop_forwarding_flag = True
