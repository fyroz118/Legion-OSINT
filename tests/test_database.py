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
        }

    def test_insert_and_count(self):
        database.insert_post(self.sample())
        self.assertEqual(database.count_posts(), 1)

    def test_duplicate_message_is_ignored(self):
        database.insert_post(self.sample())
        database.insert_post(self.sample())
        self.assertEqual(database.count_posts(), 1)

    def test_search_and_region_filter(self):
        database.insert_post(self.sample())
        self.assertEqual(len(database.search_posts(query="demonstration")), 1)
        self.assertEqual(len(database.search_posts(region="bangladesh")), 1)
        self.assertEqual(len(database.search_posts(region="europe")), 0)

    def test_new_records_start_unverified(self):
        database.insert_post(self.sample())
        rows = database.search_posts()
        self.assertEqual(rows[0]["evidence_status"], "UNVERIFIED")


if __name__ == "__main__":
    unittest.main()
