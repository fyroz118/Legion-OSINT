"""Scheduled collector process for a persistent Linux host."""
import asyncio
import logging
import os
from zoneinfo import ZoneInfo
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv
from app.collector import collect

load_dotenv()
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
log = logging.getLogger("legion.worker")

async def main():
    interval = max(15, int(os.getenv("COLLECT_INTERVAL_MINUTES", "60")))
    timezone_name = os.getenv("REPORT_TIMEZONE", "Asia/Dhaka")
    scheduler = AsyncIOScheduler(timezone=ZoneInfo(timezone_name))
    log.info("Starting Legion-OSINT collector; interval=%s minutes", interval)

    # Run once at startup, then on the configured interval.
    try:
        await collect()
    except Exception:
        log.exception("Initial collection failed; scheduler will retry at next interval")

    scheduler.add_job(
        collect,
        trigger="interval",
        minutes=interval,
        id="public_channel_collection",
        max_instances=1,
        coalesce=True,
        misfire_grace_time=300,
    )
    scheduler.start()
    try:
        while True:
            await asyncio.sleep(3600)
    finally:
        scheduler.shutdown(wait=False)

if __name__ == "__main__":
    asyncio.run(main())
