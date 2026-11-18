import tempfile
import unittest
from pathlib import Path
from app import database, incidents
from app.report_builder import build_report_draft


class ReportDraftTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.original_path = database.DB_PATH
        database.DB_PATH = str(Path(self.temp_dir.name) / "report.sqlite3")
        database.initialize()
        incidents.initialize_incident_tables()

    def tearDown(self):
        database.DB_PATH = self.original_path
        self.temp_dir.cleanup()

    def test_empty_report_is_explicitly_a_draft(self):
        report = build_report_draft("2026-11-18")
        self.assertIn("DRAFT FROM INCIDENT LEDGER", report)
        self.assertIn("Empty sections are not evidence", report)
        self.assertIn("## Overall Intelligence Judgment", report)

    def test_incident_appears_in_register(self):
        incidents.upsert_incident({
            "incident_id": "BD-001", "report_date": "2026-11-18",
            "country": "Bangladesh", "category": "civil_unrest",
            "description": "A demonstration reported by a public source."
        })
        report = build_report_draft("2026-11-18")
        self.assertIn("A demonstration reported by a public source.", report)
        self.assertIn("Bangladesh", report)


if __name__ == "__main__":
    unittest.main()
