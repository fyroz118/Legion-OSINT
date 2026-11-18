import tempfile
import unittest
from pathlib import Path
from app import database, incidents


class IncidentLedgerTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.original_path = database.DB_PATH
        database.DB_PATH = str(Path(self.temp_dir.name) / "ledger.sqlite3")
        database.initialize()
        incidents.initialize_incident_tables()

    def tearDown(self):
        database.DB_PATH = self.original_path
        self.temp_dir.cleanup()

    def sample(self):
        return {
            "incident_id": "BD-2026-11-18-001", "report_date": "2026-11-18",
            "country": "Bangladesh", "admin1": "Dhaka", "category": "civil_unrest",
            "description": "A reported public demonstration; details pending corroboration.",
            "verification_status": "UNVERIFIED", "confidence": "Low", "risk_level": "Low"
        }

    def test_insert_and_retrieve_incident(self):
        incidents.upsert_incident(self.sample())
        rows = incidents.get_report_incidents("2026-11-18")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["verification_status"], "UNVERIFIED")
        self.assertEqual(rows[0]["country"], "Bangladesh")

    def test_source_provenance_is_attached(self):
        incidents.upsert_incident(self.sample())
        incidents.add_incident_source("BD-2026-11-18-001", {
            "source_url": "https://example.org/report", "source_name": "Example newsroom",
            "source_class": "independent_media", "source_role": "corroboration",
            "independence_group": "example-newsroom"
        })
        row = incidents.get_report_incidents("2026-11-18")[0]
        self.assertEqual(len(row["sources"]), 1)
        self.assertEqual(row["sources"][0]["source_role"], "corroboration")

    def test_invalid_verification_label_rejected(self):
        item = self.sample()
        item["verification_status"] = "CONFIRMED"
        with self.assertRaises(ValueError):
            incidents.upsert_incident(item)

    def test_invalid_date_rejected(self):
        item = self.sample()
        item["report_date"] = "18-11-2026"
        with self.assertRaises(ValueError):
            incidents.upsert_incident(item)

    def test_missing_incident_rejects_source(self):
        with self.assertRaises(ValueError):
            incidents.add_incident_source("missing", {"source_url": "https://example.org"})


if __name__ == "__main__":
    unittest.main()
