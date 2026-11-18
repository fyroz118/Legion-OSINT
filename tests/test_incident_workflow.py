import tempfile
import unittest
from pathlib import Path
from app import database
from app.research import run_research, review_lead, get_research_leads
from app.incident_workflow import (
    create_incident_draft_from_lead, set_incident_workflow_status,
    get_approved_report_incidents, get_incident_workflow_queue
)
from app.report_builder import build_report_draft


class IncidentWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.original_path = database.DB_PATH
        database.DB_PATH = str(Path(self.temp_dir.name) / "workflow.sqlite3")
        database.initialize()

    def tearDown(self):
        database.DB_PATH = self.original_path
        self.temp_dir.cleanup()

    def seed_lead(self):
        def fake_search(query, report_date, max_results=10):
            return {"results": [{
                "title": "Independent local report about a public demonstration",
                "url": "https://local.example.org/report",
                "content": "The outlet reports a public demonstration; details require corroboration.",
                "published_date": report_date,
            }]}
        run_research("2026-11-18", max_queries=1, search_fn=fake_search)
        return get_research_leads("2026-11-18")[0]["id"]

    def test_only_reviewed_classified_leads_can_create_drafts(self):
        lead_id = self.seed_lead()
        with self.assertRaises(ValueError):
            create_incident_draft_from_lead(
                lead_id, "BD-001", "Bangladesh", "civil_unrest",
                "A reported demonstration", independence_group="local-outlet"
            )
        review_lead(lead_id, "REVIEWED", source_class="independent_media")
        with self.assertRaises(ValueError):
            create_incident_draft_from_lead(
                lead_id, "BD-001", "Bangladesh", "civil_unrest",
                "A reported demonstration"
            )
        create_incident_draft_from_lead(
            lead_id, "BD-001", "Bangladesh", "civil_unrest",
            "A reported demonstration", independence_group="local-outlet"
        )
        self.assertEqual(get_approved_report_incidents("2026-11-18"), [])
        queue = get_incident_workflow_queue("2026-11-18")
        self.assertEqual(queue[0]["status"], "DRAFT")
        self.assertEqual(queue[0]["verification_status"], "UNVERIFIED")

    def test_approval_is_separate_from_verification_and_gates_report(self):
        lead_id = self.seed_lead()
        review_lead(lead_id, "REVIEWED", source_class="independent_media")
        create_incident_draft_from_lead(
            lead_id, "BD-002", "Bangladesh", "civil_unrest",
            "A reported demonstration", independence_group="local-outlet"
        )
        with self.assertRaises(ValueError):
            set_incident_workflow_status("BD-002", "APPROVED")
        set_incident_workflow_status(
            "BD-002", "APPROVED", "Reviewed event details and source provenance for inclusion."
        )
        approved = get_approved_report_incidents("2026-11-18")
        self.assertEqual(len(approved), 1)
        self.assertEqual(approved[0]["verification_status"], "UNVERIFIED")
        report = build_report_draft("2026-11-18")
        self.assertIn("A reported demonstration", report)
        self.assertIn("approval permits report inclusion but does not mean verification", report)

    def test_rejected_incident_is_excluded(self):
        lead_id = self.seed_lead()
        review_lead(lead_id, "REVIEWED", source_class="independent_media")
        create_incident_draft_from_lead(
            lead_id, "BD-003", "Bangladesh", "civil_unrest",
            "A rejected claim", independence_group="local-outlet"
        )
        set_incident_workflow_status("BD-003", "REJECTED", "Evidence insufficient.")
        self.assertEqual(get_approved_report_incidents("2026-11-18"), [])


if __name__ == "__main__":
    unittest.main()
