import sqlite3
import tempfile
import unittest
from pathlib import Path

from app import database


class DatabaseTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.original_path = database.DB_PATH
        database.DB_PATH = str(Path(self.temp_dir.name) / "test.sqlite3")
        database.initialize()

    def tearDown(self):
        database.DB_PATH = self.original_path
        self.temp_dir.cleanup()

    def sample(self, message_id="101", text="Public report of a peaceful demonstration"):
        return {
            "channel_username": "reviewed_public_source",
            "channel_id": "12345",
            "message_id": message_id,
            "published_at": "2026-11-18T08:00:00+00:00",
            "collected_at": "2026-11-18T08:05:00+00:00",
            "text": text,
            "source_url": "https://t.me/reviewed_public_source/101",
            "language": "en",
            "priority_region": "bangladesh",
            "source_class": "unofficial",
            "source_type": "local_journalist",
            "source_affiliation": "independent",
            "monitoring_weight": "high",
        }

    def test_insert_and_count(self):
        database.insert_post(self.sample())
        self.assertEqual(database.count_posts(), 1)

    def test_duplicate_message_is_ignored(self):
        database.insert_post(self.sample())
        database.insert_post(self.sample())
        self.assertEqual(database.count_posts(), 1)

    def test_search_region_and_source_class(self):
        database.insert_post(self.sample())
        self.assertEqual(len(database.search_posts(query="demonstration")), 1)
        self.assertEqual(len(database.search_posts(region="bangladesh")), 1)
        self.assertEqual(len(database.search_posts(source_class="unofficial")), 1)
        self.assertEqual(len(database.search_posts(source_class="official")), 0)

    def test_source_metadata_is_preserved(self):
        database.insert_post(self.sample())
        row = database.search_posts()[0]
        self.assertEqual(row["source_class"], "unofficial")
        self.assertEqual(row["source_type"], "local_journalist")
        self.assertEqual(row["monitoring_weight"], "high")

    def test_new_records_start_unverified(self):
        database.insert_post(self.sample())
        self.assertEqual(database.search_posts()[0]["evidence_status"], "UNVERIFIED")

    def test_legacy_database_schema_is_migrated(self):
        legacy_path = str(Path(self.temp_dir.name) / "legacy.sqlite3")
        with sqlite3.connect(legacy_path) as db:
            db.execute("""CREATE TABLE posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT, channel_username TEXT NOT NULL,
                channel_id TEXT, message_id TEXT NOT NULL, published_at TEXT,
                collected_at TEXT NOT NULL, text TEXT NOT NULL, source_url TEXT,
                language TEXT DEFAULT 'unknown', priority_region TEXT DEFAULT 'global',
                evidence_status TEXT NOT NULL DEFAULT 'UNVERIFIED',
                UNIQUE(channel_username, message_id))""")
        database.DB_PATH = legacy_path
        database.initialize()
        with sqlite3.connect(legacy_path) as db:
            cols = {row[1] for row in db.execute("PRAGMA table_info(posts)")}
        self.assertTrue({"source_class", "source_type", "source_affiliation", "monitoring_weight"} <= cols)


if __name__ == "__main__":
    unittest.main()
