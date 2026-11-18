import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler
from app.database import initialize, count_posts, search_posts
from app.gemini_assistant import ask

load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
ALLOWED = {x.strip() for x in os.getenv("TELEGRAM_ALLOWED_USER_IDS", "").split(",") if x.strip()}

def allowed(update):
    return bool(update.effective_user and str(update.effective_user.id) in ALLOWED)

async def gate(update):
    if not allowed(update):
        await update.effective_message.reply_text("Access denied. Private development bot.")
        return False
    return True

async def start(update, context):
    if await gate(update):
        await update.message.reply_text("Legion-OSINT. Commands: /status /daily /bangladesh /search <terms> /ask <question> /help")

async def help_cmd(update, context):
    if await gate(update):
        await update.message.reply_text("/status database count\n/daily recent global posts\n/bangladesh Bangladesh posts\n/search <terms>\n/ask <question>")

async def status(update, context):
    if await gate(update):
        await update.message.reply_text(f"Stored posts: {count_posts()} | Collector: one-shot/manual")

async def display(update, region=None, query=""):
    rows = search_posts(query=query, region=region, limit=10)
    if not rows:
        await update.message.reply_text("No matching collected records.")
        return
    body = "\n\n".join(f"[UNVERIFIED] {' '.join(r['text'].split())[:180]}\n{r['source_url']}" for r in rows)
    await update.message.reply_text(body[:3900], disable_web_page_preview=True)

async def daily(update, context):
    if await gate(update): await display(update)

async def bangladesh(update, context):
    if await gate(update): await display(update, region="bangladesh")

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
        else:
            await update.message.reply_text(ask(q)[:3900], disable_web_page_preview=True)

def main():
    if not TOKEN: raise RuntimeError("Set TELEGRAM_BOT_TOKEN in local .env")
    if not ALLOWED: raise RuntimeError("Set TELEGRAM_ALLOWED_USER_IDS before starting the bot")
    initialize()
    app = Application.builder().token(TOKEN).build()
    for name, fn in [("start", start), ("help", help_cmd), ("status", status),
                     ("daily", daily), ("bangladesh", bangladesh),
                     ("search", search_cmd), ("ask", ask_cmd)]:
        app.add_handler(CommandHandler(name, fn))
    app.run_polling()

if __name__ == "__main__":
    main()
