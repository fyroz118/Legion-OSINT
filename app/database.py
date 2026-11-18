import os
import sqlite3
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
DB_PATH = os.getenv("DATABASE_PATH", "data/legion_osint.sqlite3")

SOURCE_COLUMNS = {
    "source_class": "TEXT NOT NULL DEFAULT 'unknown'",
    "source_type": "TEXT NOT NULL DEFAULT 'unknown'",
    "source_affiliation": "TEXT NOT NULL DEFAULT 'unknown'",
    "monitoring_weight": "TEXT NOT NULL DEFAULT 'standard'",
    "publisher_name": "TEXT NOT NULL DEFAULT ''",
    "platform": "TEXT NOT NULL DEFAULT 'Telegram'",
}


def connect():
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(DB_PATH, timeout=30)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA busy_timeout = 30000")
    return db


def initialize():
    with connect() as db:
        db.execute("""CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            channel_username TEXT NOT NULL,
            channel_id TEXT,
            message_id TEXT NOT NULL,
            published_at TEXT,
            collected_at TEXT NOT NULL,
            text TEXT NOT NULL,
            source_url TEXT,
            language TEXT DEFAULT 'unknown',
            priority_region TEXT DEFAULT 'global',
            evidence_status TEXT NOT NULL DEFAULT 'UNVERIFIED',
            UNIQUE(channel_username, message_id)
        )""")
        existing = {row["name"] for row in db.execute("PRAGMA table_info(posts)")}
        for name, declaration in SOURCE_COLUMNS.items():
            if name not in existing:
                db.execute(f"ALTER TABLE posts ADD COLUMN {name} {declaration}")
        db.execute("PRAGMA journal_mode = WAL")


def insert_post(p):
    with connect() as db:
        db.execute("""INSERT OR IGNORE INTO posts
        (channel_username, channel_id, message_id, published_at, collected_at, text,
         source_url, language, priority_region, evidence_status, source_class,
         source_type, source_affiliation, monitoring_weight, publisher_name, platform)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'UNVERIFIED', ?, ?, ?, ?, ?, ?)""",
        (p["channel_username"], p.get("channel_id"), str(p["message_id"]),
         p.get("published_at"), p["collected_at"], p["text"], p.get("source_url"),
         p.get("language", "unknown"), p.get("priority_region", "global"),
         p.get("source_class", "unknown"), p.get("source_type", "unknown"),
         p.get("source_affiliation", "unknown"), p.get("monitoring_weight", "standard"),
         p.get("publisher_name", ""), p.get("platform", "Telegram")))


def search_posts(query="", region=None, limit=30, source_class=None):
    sql, args = "SELECT * FROM posts WHERE 1=1", []
    if query:
        sql += " AND lower(text) LIKE ?"
        args.append("%" + query.lower() + "%")
    if region:
        sql += " AND priority_region = ?"
        args.append(region)
    if source_class:
        sql += " AND source_class = ?"
        args.append(source_class)
    sql += " ORDER BY collected_at DESC LIMIT ?"
    args.append(limit)
    with connect() as db:
        return [dict(r) for r in db.execute(sql, args).fetchall()]


def source_mix_counts():
    with connect() as db:
        rows = db.execute(
            "SELECT source_class, COUNT(*) AS post_count FROM posts GROUP BY source_class"
        ).fetchall()
    return {row["source_class"]: row["post_count"] for row in rows}


def count_posts():
    with connect() as db:
        return db.execute("SELECT COUNT(*) FROM posts").fetchone()[0]
