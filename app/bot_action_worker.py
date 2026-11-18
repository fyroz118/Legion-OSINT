"""One-shot Telegram polling worker for GitHub Actions.

GitHub-hosted runners are ephemeral. The workflow restores the small data/ state
cache, processes one Telegram getUpdates batch, then saves the state again.
"""
import asyncio
import json
import os
import sqlite3
from pathlib import Path

from telegram import Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler

from app import bot as commands

DATA_DIR = Path(os.getenv("LEGION_BOT_DATA_DIR", "data"))
OFFSET_FILE = DATA_DIR / "telegram_update_offset.json"


def build_application():
    app = Application.builder().token(commands.TOKEN).build()
    handlers = [
        ("start", commands.start), ("help", commands.help_cmd),
        ("status", commands.status), ("daily", commands.daily),
        ("bangladesh", commands.bangladesh), ("search", commands.search_cmd),
        ("ask", commands.ask_cmd), ("report", commands.report_cmd),
        ("research", commands.research_cmd), ("briefs", commands.briefs_cmd),
        ("leads", commands.leads_cmd), ("coverage", commands.coverage_cmd),
        ("reviewqueue", commands.reviewqueue_cmd), ("candidates", commands.candidates_cmd),
        ("reviewlead", commands.reviewlead_cmd), ("incidentdraft", commands.incidentdraft_cmd),
        ("incidentqueue", commands.incidentqueue_cmd),
        ("approveincident", commands.approveincident_cmd),
        ("linklead", commands.linklead_cmd),
    ]
    for name, callback in handlers:
        app.add_handler(CommandHandler(name, callback))
    app.add_handler(CallbackQueryHandler(
        commands.review_button_callback,
        pattern=r"^leadreview:[0-9]+:(REVIEWED|REJECTED)$",
    ))
    return app


def read_offset():
    try:
        return int(json.loads(OFFSET_FILE.read_text(encoding="utf-8")).get("offset", 0))
    except (FileNotFoundError, ValueError, TypeError, json.JSONDecodeError):
        return 0


def write_offset(offset):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    temp = OFFSET_FILE.with_suffix(".tmp")
    temp.write_text(json.dumps({"offset": offset}), encoding="utf-8")
    temp.replace(OFFSET_FILE)


def checkpoint_database():
    db_path = Path(os.getenv("DATABASE_PATH", "data/legion_osint.sqlite3"))
    if db_path.exists():
        with sqlite3.connect(db_path, timeout=20) as db:
            db.execute("PRAGMA wal_checkpoint(TRUNCATE)")


async def run():
    if not commands.TOKEN:
        raise RuntimeError("Missing TELEGRAM_BOT_TOKEN secret.")
    if not commands.ALLOWED:
        raise RuntimeError("Missing TELEGRAM_ALLOWED_USER_IDS secret.")
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    commands.initialize()
    app = build_application()
    await app.initialize()
    await app.start()
    processed = 0
    try:
        offset = read_offset()
        # This bot is intentionally hosted only by this GitHub Actions worker.
        # Telegram webhooks and getUpdates polling are mutually exclusive.
        # Remove any stale webhook but preserve queued updates.
        await app.bot.delete_webhook(drop_pending_updates=False)
        # One bounded batch per scheduled run. Telegram retains unacknowledged
        # updates, and the next scheduled run continues from the saved offset.
        updates = await app.bot.get_updates(
            offset=offset, limit=100, timeout=0,
            read_timeout=15, connect_timeout=15, pool_timeout=15,
        )
        for update in updates:
            await app.process_update(update)
            offset = update.update_id + 1
            write_offset(offset)
            processed += 1
    finally:
        await app.stop()
        await app.shutdown()
        checkpoint_database()
    print(f"Telegram action worker completed; processed_updates={processed}")


if __name__ == "__main__":
    asyncio.run(run())
