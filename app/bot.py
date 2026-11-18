import asyncio
import os
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update
from telegram.constants import ChatType
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CallbackQueryHandler, CommandHandler
from app.database import initialize, count_posts, search_posts, source_mix_counts
from app.gemini_assistant import ask
from app.report_builder import build_report_draft
from app.research import (run_research, get_research_leads, get_research_coverage,
                          review_queue, review_lead, link_reviewed_lead_to_incident,
                          extract_event_candidates, suggest_duplicate_candidates)

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
            "Commands: /status /daily /bangladesh /search /ask /research /briefs /leads /coverage /report /help"
        )


async def help_cmd(update, context):
    if await gate(update):
        await update.message.reply_text(
            "/status — database status\n"
            "/daily — recent collected Telegram posts\n"
            "/bangladesh — recent Bangladesh posts\n"
            "/search <terms> — search collected text\n"
            "/ask <question> — ask Gemini about stored records\n"
            "/research YYYY-MM-DD — run expanded public-web discovery (default 60 queries)\n"
            "/briefs YYYY-MM-DD [limit] — display individual source-lead briefs (default 60, max 100)\n"
            "/leads YYYY-MM-DD — show stored candidate links\n"
            "/coverage YYYY-MM-DD — show regional query coverage and failures\n"
            "/reviewqueue YYYY-MM-DD — analyst review queue with one-tap decisions\n"
            "/candidates YYYY-MM-DD [limit] — conservative event candidates and duplicate suggestions\n"
            "/reviewlead ID reviewed|rejected|duplicate [source_class] [duplicate_ID] — record review\n            /linklead LEAD_ID INCIDENT_ID [lead|corroboration|contradiction] — link reviewed provenance\n            /report YYYY-MM-DD — consolidated ten-section draft from reviewed incident ledger"
        )


async def status(update, context):
    if await gate(update):
        mix = source_mix_counts()
        mix_text = ", ".join(f"{name}: {count}" for name, count in sorted(mix.items())) or "no source metadata yet"
        await update.message.reply_text(
            f"Stored Telegram posts: {count_posts()}\nPost source mix: {mix_text}\n"
            "Public-web research runs are separate; use /coverage YYYY-MM-DD."
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


async def research_cmd(update, context):
    if not await gate(update):
        return
    if len(context.args) != 1:
        await update.message.reply_text("Usage: /research YYYY-MM-DD")
        return
    report_date = context.args[0]
    try:
        datetime.strptime(report_date, "%Y-%m-%d")
    except ValueError:
        await update.message.reply_text("Invalid date. Use YYYY-MM-DD.")
        return
    await update.message.reply_text(
        f"Starting expanded discovery for {report_date} (Asia/Dhaka): default 60 queries, up to 10 results each. "
        "Bangladesh, South Asia and MENA are prioritized. Rumour-watch leads are included but remain unverified."
    )
    try:
        result = await asyncio.to_thread(run_research, report_date)
        await update.message.reply_text(
            f"Research complete for {report_date}.\n"
            f"Queries: {result['queries_succeeded']}/{result['queries_attempted']} succeeded.\n"
            f"Query focus: {result['unofficial_focus_queries']} unofficial/local; "
            f"{result['official_focus_queries']} official/institutional.\n"
            f"Unique source leads: {result['unique_leads_for_date']}.\n"
            "Use /briefs, /leads and /coverage. These are unverified source leads, not verified incidents."
        )
    except Exception as exc:
        await update.message.reply_text(f"Research unavailable ({type(exc).__name__}). Check provider configuration.")


async def briefs_cmd(update, context):
    if not await gate(update):
        return
    if len(context.args) not in (1, 2):
        await update.message.reply_text("Usage: /briefs YYYY-MM-DD [limit]")
        return
    report_date = context.args[0]
    try:
        datetime.strptime(report_date, "%Y-%m-%d")
        limit = int(context.args[1]) if len(context.args) == 2 else 60
        if limit < 1 or limit > 100:
            raise ValueError
        rows = get_research_leads(report_date, limit=limit)
    except ValueError:
        await update.message.reply_text("Invalid date or limit. Use /briefs YYYY-MM-DD [1-100].")
        return
    if not rows:
        await update.message.reply_text("No source leads stored for this date. Run /research first.")
        return
    await update.message.reply_text(
        f"Individual source-lead briefs: {len(rows)} returned for {report_date}. "
        "These are source-specific leads, not necessarily unique incidents. All new leads are UNVERIFIED."
    )
    rendered = []
    for index, row in enumerate(rows, 1):
        title = (row.get("title") or "Untitled source result").replace("<", "‹").replace(">", "›")
        snippet = " ".join((row.get("snippet") or "No snippet supplied by provider.").split())[:500]
        focus = row.get("source_focus") or "unknown"
        claim = row.get("claim_type") or "EVENT_NEWS"
        rendered.append(
            f"BRIEF {index:02d} | {claim}" + (" — UNVERIFIED RUMOUR" if claim == "RUMOUR_WATCH" else "") + "\\n"
            f"Region: {row.get('region') or 'Unknown'}\\n"
            f"Source: {title}\\n"
            f"Published: {row.get('published_date') or 'Unknown'}\\n"
            f"Source class: {row.get('source_class') or 'unknown'} (review required)\\n"
            f"Search focus: {focus}\\n"
            f"Status: UNVERIFIED — source claim only\\n"
            f"Summary: {snippet}\\n"
            f"Original: {row['source_url']}"
        )
    # Batch several individual briefs per Telegram message to avoid flooding the chat.
    batch = ""
    for brief in rendered:
        candidate = f"{batch}\\n\\n{brief}" if batch else brief
        if len(candidate) > 3500 and batch:
            await update.effective_message.reply_text(batch, disable_web_page_preview=True)
            batch = brief
        else:
            batch = candidate
    if batch:
        await update.effective_message.reply_text(batch, disable_web_page_preview=True)


async def leads_cmd(update, context):
    if await gate(update):
        if len(context.args) != 1:
            await update.message.reply_text("Usage: /leads YYYY-MM-DD")
            return
        try:
            rows = get_research_leads(context.args[0], limit=100)
        except ValueError:
            await update.message.reply_text("Invalid date. Use YYYY-MM-DD.")
            return
        if not rows:
            await update.message.reply_text("No stored research leads for that date.")
            return
        body = "\n\n".join(
            f"[{row['region']}] {row.get('title') or 'Untitled result'}\n"
            f"Published: {row.get('published_date') or 'unknown'} | "
            f"{row.get('claim_type', 'EVENT_NEWS')} | UNVERIFIED\n{row['source_url']}"
            for row in rows
        )
        for start in range(0, len(body), 3800):
            await update.message.reply_text(body[start:start + 3800], disable_web_page_preview=True)


async def coverage_cmd(update, context):
    if await gate(update):
        if len(context.args) != 1:
            await update.message.reply_text("Usage: /coverage YYYY-MM-DD")
            return
        try:
            rows = get_research_coverage(context.args[0])
        except ValueError:
            await update.message.reply_text("Invalid date. Use YYYY-MM-DD.")
            return
        if not rows:
            await update.message.reply_text("No research coverage log for that date.")
            return
        body = "\n".join(
            f"{row['region']}: {row['status']} — {row['query_count']} queries, {row['result_count'] or 0} results"
            for row in rows
        )
        await update.message.reply_text(f"Research coverage — {context.args[0]}\n{body}")


async def reviewqueue_cmd(update, context):
    if not await gate(update):
        return
    if len(context.args) != 1:
        await update.message.reply_text("Usage: /reviewqueue YYYY-MM-DD")
        return
    try:
        rows = review_queue(context.args[0], limit=50)
    except ValueError:
        await update.message.reply_text("Invalid date. Use YYYY-MM-DD.")
        return
    if not rows:
        await update.message.reply_text("No unreviewed leads for that date.")
        return
    await update.message.reply_text("Review queue: each item is an unverified lead, not an established incident.")
    for row in rows:
        title = (row.get("title") or "Untitled").replace("<", "‹").replace(">", "›")
        snippet = " ".join((row.get("snippet") or "").split())[:260]
        msg = (f"Lead ID: {row['id']} | {row['region']} | {row['claim_type']}\n"
               f"{title}\n{snippet}\nSource: {row['source_url']}\n"
               "Review with /reviewlead ID reviewed|rejected|duplicate [source_class] [duplicate_lead_id]")
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("Reviewed (not verified)", callback_data=f"leadreview:{row['id']}:REVIEWED"),
            InlineKeyboardButton("Reject lead", callback_data=f"leadreview:{row['id']}:REJECTED")
        ]])
        await update.effective_message.reply_text(
            msg[:3500], reply_markup=keyboard, disable_web_page_preview=True
        )


async def reviewlead_cmd(update, context):
    if not await gate(update):
        return
    if len(context.args) < 2 or len(context.args) > 4:
        await update.message.reply_text(
            "Usage: /reviewlead ID reviewed|rejected|duplicate [source_class] [duplicate_lead_id]\n"
            "Source classes: unofficial, independent_media, civil_society, official_media, "
            "official_government, intergovernmental, research_academic, other, unknown"
        )
        return
    try:
        lead_id = int(context.args[0])
        status_value = context.args[1].upper()
        source_class = context.args[2] if len(context.args) >= 3 else None
        duplicate_of = int(context.args[3]) if len(context.args) == 4 else None
        review_lead(lead_id, status_value, source_class=source_class,
                    duplicate_of=duplicate_of)
    except (ValueError, TypeError) as exc:
        await update.message.reply_text(f"Review not saved: {exc}")
        return
    await update.message.reply_text(
        f"Lead {lead_id} marked {status_value}. This does not verify the underlying claim "
        "or create an incident record."
    )




async def review_button_callback(update, context):
    query = update.callback_query
    if not await gate(update):
        return
    await query.answer()
    try:
        _, lead_id, status_value = query.data.split(":")
        review_lead(int(lead_id), status_value)
    except (ValueError, TypeError) as exc:
        await query.edit_message_reply_markup(reply_markup=None)
        await query.message.reply_text(f"Review not saved: {exc}")
        return
    await query.edit_message_reply_markup(reply_markup=None)
    await query.message.reply_text(
        f"Lead {lead_id} marked {status_value}. This is an analyst workflow decision, "
        "not verification of the underlying claim."
    )


async def candidates_cmd(update, context):
    if not await gate(update):
        return
    if len(context.args) not in (1, 2):
        await update.message.reply_text("Usage: /candidates YYYY-MM-DD [limit]")
        return
    try:
        report_date = context.args[0]
        limit = int(context.args[1]) if len(context.args) == 2 else 50
        rows = extract_event_candidates(report_date, limit=max(1, min(limit, 100)))
        suggestions = suggest_duplicate_candidates(report_date, limit=max(1, min(limit, 100)))
    except (ValueError, TypeError) as exc:
        await update.message.reply_text(f"Could not build candidates: {exc}")
        return
    if not rows:
        await update.message.reply_text("No source leads available for candidate extraction on that date.")
        return
    await update.message.reply_text(
        f"{len(rows)} unverified event candidates. Event dates, precise locations and actors "
        "remain unknown unless separately evidenced. Similar-title pairs are suggestions only."
    )
    for row in rows:
        summary = " ".join(row["summary"].split())[:240]
        message = (
            f"{row['candidate_id']} | {row['region']} | {row['claim_type']}\n"
            f"{row['title']}\n{summary}\n"
            f"Incident date: unknown | Location: unknown | Actors: unknown\n"
            f"Status: {row['candidate_status']} | Review: {row['review_status']}\n"
            f"Source: {row['source_url']}"
        )
        await update.effective_message.reply_text(message[:3500], disable_web_page_preview=True)
    if suggestions:
        await update.effective_message.reply_text(
            f"Possible duplicate-title pairs for human review: {len(suggestions)}"
        )
        for pair in suggestions[:20]:
            await update.effective_message.reply_text(
                f"Possible match: lead {pair['lead_id_a']} / lead {pair['lead_id_b']} "
                f"({pair['similarity']:.0%} title-token overlap)\n"
                f"A: {pair['title_a']}\nB: {pair['title_b']}\n"
                "This is not a duplicate determination."
            )


async def linklead_cmd(update, context):
    if not await gate(update):
        return
    if len(context.args) not in (2, 3):
        await update.message.reply_text("Usage: /linklead LEAD_ID EXISTING_INCIDENT_ID [lead|corroboration|contradiction]")
        return
    try:
        link_reviewed_lead_to_incident(
            int(context.args[0]), context.args[1],
            context.args[2] if len(context.args) == 3 else "lead"
        )
    except (ValueError, TypeError) as exc:
        await update.message.reply_text(f"Link not saved: {exc}")
        return
    await update.message.reply_text("Reviewed source provenance linked to the existing incident.")


async def report_cmd(update, context):
    if await gate(update):
        if len(context.args) != 1:
            await update.message.reply_text("Usage: /report YYYY-MM-DD")
            return
        try:
            report = build_report_draft(context.args[0])
        except ValueError:
            await update.message.reply_text("Invalid date. Use YYYY-MM-DD.")
            return
        for start in range(0, len(report), 3800):
            await update.message.reply_text(report[start:start + 3800], disable_web_page_preview=True)


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
        ("search", search_cmd), ("ask", ask_cmd), ("report", report_cmd),
        ("research", research_cmd), ("briefs", briefs_cmd), ("leads", leads_cmd), ("coverage", coverage_cmd),
        ("reviewqueue", reviewqueue_cmd), ("candidates", candidates_cmd), ("reviewlead", reviewlead_cmd), ("linklead", linklead_cmd)
    ]:
        app.add_handler(CommandHandler(name, fn))
    app.add_handler(CallbackQueryHandler(review_button_callback, pattern=r"^leadreview:[0-9]+:(REVIEWED|REJECTED)$"))
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
