import os, json, asyncio
from pathlib import Path
from datetime import datetime, timezone
from dotenv import load_dotenv
from telethon import TelegramClient
from app.database import initialize, insert_post

load_dotenv()

async def collect():
    api_id, api_hash = os.getenv("TELEGRAM_API_ID"), os.getenv("TELEGRAM_API_HASH")
    if not api_id or not api_hash:
        raise RuntimeError("Set TELEGRAM_API_ID and TELEGRAM_API_HASH in local .env")
    cfg = json.loads(Path("config/channels.json").read_text(encoding="utf-8"))
    channels = [c for c in cfg.get("channels", [])
                if c.get("username") and not c["username"].startswith("REPLACE_")]
    limit = int(os.getenv("COLLECT_LIMIT_PER_CHANNEL", "100"))
    initialize()
    session_path = os.getenv("TELETHON_SESSION_PATH", "data/legion_osint_user")
    Path(session_path).parent.mkdir(parents=True, exist_ok=True)
    client = TelegramClient(session_path, int(api_id), api_hash)
    await client.start()
    try:
        for ch in channels:
            username = ch["username"].lstrip("@")
            try:
                entity = await client.get_entity(username)
                async for msg in client.iter_messages(entity, limit=limit):
                    if not msg.message:
                        continue
                    published = msg.date.astimezone(timezone.utc).isoformat() if msg.date else None
                    insert_post({
                        "channel_username": username, "channel_id": str(entity.id),
                        "message_id": msg.id, "published_at": published,
                        "collected_at": datetime.now(timezone.utc).isoformat(),
                        "text": msg.message[:12000],
                        "source_url": f"https://t.me/{username}/{msg.id}",
                        "language": ch.get("language", "unknown"),
                        "priority_region": ch.get("priority", "global")
                    })
                print("Collected public channel @" + username)
            except Exception as exc:
                print(f"Skipped @{username}: {type(exc).__name__}: {exc}")
    finally:
        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(collect())
