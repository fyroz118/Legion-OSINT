import os
import sqlite3
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
DB_PATH = os.getenv("DATABASE_PATH", "data/legion_osint.sqlite3")

def connect():
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
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

def insert_post(p):
    with connect() as db:
        db.execute("""INSERT OR IGNORE INTO posts
        (channel_username, channel_id, message_id, published_at, collected_at, text,
         source_url, language, priority_region, evidence_status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'UNVERIFIED')""",
        (p["channel_username"], p.get("channel_id"), str(p["message_id"]),
         p.get("published_at"), p["collected_at"], p["text"], p.get("source_url"),
         p.get("language", "unknown"), p.get("priority_region", "global")))

def search_posts(query="", region=None, limit=30):
    sql, args = "SELECT * FROM posts WHERE 1=1", []
    if query:
        sql += " AND lower(text) LIKE ?"
        args.append("%" + query.lower() + "%")
    if region:
        sql += " AND priority_region = ?"
        args.append(region)
    sql += " ORDER BY collected_at DESC LIMIT ?"
    args.append(limit)
    with connect() as db:
        return [dict(r) for r in db.execute(sql, args).fetchall()]

def count_posts():
    with connect() as db:
        return db.execute("SELECT COUNT(*) FROM posts").fetchone()[0]
