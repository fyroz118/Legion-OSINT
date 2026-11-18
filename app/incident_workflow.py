"""Human-gated incident drafting and publication approval.

Approval means an analyst permits inclusion in the report; it does NOT mean
that an event or claim is verified.
"""
from datetime import datetime, timezone
from app.database import connect
from app.incidents import upsert_incident, add_incident_source, get_report_incidents
from app.research import initialize_research_tables


def initialize_workflow_tables():
    with connect() as db:
        db.execute("""CREATE TABLE IF NOT EXISTS incident_workflow (
            incident_id TEXT PRIMARY KEY,
            status TEXT NOT NULL DEFAULT 'DRAFT'
                CHECK(status IN ('DRAFT','APPROVED','REJECTED')),
            approval_note TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (incident_id) REFERENCES incidents(incident_id)
        )""")
        now = datetime.now(timezone.utc).isoformat()
        db.execute("""INSERT OR IGNORE INTO incident_workflow
            (incident_id, status, created_at, updated_at)
            SELECT incident_id, 'DRAFT', ?, ? FROM incidents""", (now, now))


def create_incident_draft_from_lead(lead_id, incident_id, country, category,
                                    description, incident_datetime=None,
                                    location_text=None, independence_group=None):
    """Create a DRAFT only from a reviewed and manually classified source lead."""
    initialize_research_tables()
    initialize_workflow_tables()
    with connect() as db:
        lead = db.execute("SELECT * FROM research_leads WHERE id=?", (int(lead_id),)).fetchone()
    if not lead:
        raise ValueError("Lead not found")
    if lead["review_status"] != "REVIEWED":
        raise ValueError("Only REVIEWED leads can seed an incident draft")
    if lead["source_class"] == "unknown":
        raise ValueError("Assign a reviewed source class before drafting an incident")
    if not independence_group or not str(independence_group).strip():
        raise ValueError("independence_group is required; use the original publisher/outlet group")
    upsert_incident({
        "incident_id": incident_id, "report_date": lead["report_date"],
        "incident_datetime": incident_datetime, "publication_datetime": lead["published_date"],
        "country": country, "location_text": location_text, "category": category,
        "description": description, "verification_status": "UNVERIFIED",
        "confidence": "Low", "risk_level": "Low",
        "analyst_rationale": "Draft created from one analyst-reviewed source lead; event facts remain unverified."
    })
    add_incident_source(incident_id, {
        "source_url": lead["source_url"], "source_name": lead["title"],
        "source_class": lead["source_class"], "source_type": "public_web",
        "published_at": lead["published_date"], "source_role": "lead",
        "independence_group": str(independence_group).strip(),
        "claim_summary": lead["snippet"]
    })
    now = datetime.now(timezone.utc).isoformat()
    with connect() as db:
        db.execute("""INSERT INTO incident_workflow
            (incident_id, status, created_at, updated_at) VALUES (?, 'DRAFT', ?, ?)
            ON CONFLICT(incident_id) DO UPDATE SET status='DRAFT', approval_note=NULL,
            updated_at=excluded.updated_at""", (incident_id, now, now))
    return incident_id


def set_incident_workflow_status(incident_id, status, approval_note=None):
    if status not in {"APPROVED", "REJECTED"}:
        raise ValueError("Status must be APPROVED or REJECTED")
    if not approval_note or not approval_note.strip():
        raise ValueError("An analyst rationale is required")
    initialize_workflow_tables()
    now = datetime.now(timezone.utc).isoformat()
    with connect() as db:
        exists = db.execute("SELECT 1 FROM incidents WHERE incident_id=?", (incident_id,)).fetchone()
        if not exists:
            raise ValueError("Incident not found")
        db.execute("""INSERT INTO incident_workflow
            (incident_id, status, approval_note, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(incident_id) DO UPDATE SET status=excluded.status,
            approval_note=excluded.approval_note, updated_at=excluded.updated_at""",
            (incident_id, status, approval_note.strip(), now, now))
    return True


def get_incident_workflow_queue(report_date):
    initialize_workflow_tables()
    with connect() as db:
        rows = db.execute("""SELECT i.incident_id, i.country, i.category, i.description,
            i.verification_status, w.status, w.approval_note
            FROM incidents i JOIN incident_workflow w USING(incident_id)
            WHERE i.report_date=? ORDER BY w.status, i.incident_id""", (report_date,)).fetchall()
    return [dict(row) for row in rows]


def get_approved_report_incidents(report_date):
    initialize_workflow_tables()
    return [item for item in get_report_incidents(report_date)
            if _is_approved(item["incident_id"])]


def _is_approved(incident_id):
    with connect() as db:
        row = db.execute("SELECT status FROM incident_workflow WHERE incident_id=?",
                         (incident_id,)).fetchone()
    return bool(row and row["status"] == "APPROVED")
