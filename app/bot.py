import asyncio
import os
from dotenv import load_dotenv
from telegram import Update
from telegram.constants import ChatType
from telegram.ext import Application, CommandHandler
from app.database import initialize, count_posts, search_posts, source_mix_counts
from app.gemini_assistant import ask

load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
ALLOWED = {x.strip() for x in os.getenv("TELEGRAM_ALLOWED_USER_IDS", "").split(",") if x.strip()}

def allowed(update):
    user_ok = bool(update.effective_user and str(update.effective_user.id) in ALLOWED)
    chat_ok = bool(update.effective_chat and update.effective_chat.type == ChatType.PRIVATE)
    return user_ok and chat_ok

async def gate(update):
    if not allowed(update):
        if update.effective_message:
            await update.effective_message.reply_text("Access denied. This is a private development bot.")
        return False
    return True

async def start(update, context):
    if await gate(update):
        await update.message.reply_text(
            "Legion-OSINT private assistant.\n"
            "Commands: /status /daily /bangladesh /search <terms> /ask <question> /help"
        )

async def help_cmd(update, context):
    if await gate(update):
        await update.message.reply_text(
            "/status — database status\n"
            "/daily — recent collected global posts\n"
            "/bangladesh — recent Bangladesh posts\n"
            "/search <terms> — search collected text\n"
            "/ask <question> — ask Gemini about stored records"
        )

async def status(update, context):
    if await gate(update):
        mix = source_mix_counts()
        mix_text = ", ".join(f"{name}: {count}" for name, count in sorted(mix.items())) or "no source metadata yet"
        await update.message.reply_text(
            f"Stored posts: {count_posts()}\n"
            f"Post source mix: {mix_text}\n"
            "Collector: scheduled worker (when deployed) or manual run"
        )

async def display(update, region=None, query=""):
    rows = search_posts(query=query, region=region, limit=10)
    if not rows:
        await update.message.reply_text("No matching collected records.")
        return
    body = "\n\n".join(
        f"[{r['evidence_status']}] {' '.join(r['text'].split())[:220]}\n"
        f"Published: {r['published_at'] or 'unknown'}\n{r['source_url'] or 'Source URL unavailable'}"
        for r in rows
    )
    await update.message.reply_text(body[:3900], disable_web_page_preview=True)

async def daily(update, context):
    if await gate(update):
        await display(update)

async def bangladesh(update, context):
    if await gate(update):
        await display(update, region="bangladesh")

async def search_cmd(update, context):
    if await gate(update):
        q = " ".join(context.args).strip()
        if not q:
            await update.message.reply_text("Usage: /search <terms>")
        else:
            await display(update, query=q)

async def ask_cmd(update, context):
    if await gate(update):
        q = " ".join(context.args).strip()
        if not q:
            await update.message.reply_text("Usage: /ask <question>")
            return
        await update.message.reply_text("Reviewing collected records…")
        try:
            answer = await asyncio.to_thread(ask, q)
        except Exception as exc:
            answer = f"Gemini request failed ({type(exc).__name__}). Check service configuration and logs."
        await update.message.reply_text(answer[:3900], disable_web_page_preview=True)

def main():
    if not TOKEN:
        raise RuntimeError("Set TELEGRAM_BOT_TOKEN in private .env or deployment environment")
    if not ALLOWED:
        raise RuntimeError("Set TELEGRAM_ALLOWED_USER_IDS before starting the bot")
    initialize()
    app = Application.builder().token(TOKEN).build()
    for name, fn in [
        ("start", start), ("help", help_cmd), ("status", status),
        ("daily", daily), ("bangladesh", bangladesh),
        ("search", search_cmd), ("ask", ask_cmd)
    ]:
        app.add_handler(CommandHandler(name, fn))
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
