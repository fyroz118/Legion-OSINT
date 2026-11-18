"""Structured incident and evidence ledger for date-driven reporting."""
from datetime import datetime, timezone
from app.database import connect

VERIFICATION_STATUSES = {"VERIFIED", "CREDIBLE LEAD", "DISPUTED", "UNVERIFIED", "MISLEADING-FALSE"}
CONFIDENCE_LEVELS = {"High", "Moderate", "Low"}
RISK_LEVELS = {"Low", "Moderate", "High", "Critical"}


def initialize_incident_tables():
    with connect() as db:
        db.execute("""CREATE TABLE IF NOT EXISTS incidents (
            incident_id TEXT PRIMARY KEY, report_date TEXT NOT NULL,
            incident_datetime TEXT, publication_datetime TEXT, country TEXT NOT NULL,
            admin1 TEXT, admin2 TEXT, location_text TEXT, category TEXT NOT NULL,
            actors TEXT, description TEXT NOT NULL, casualties TEXT, trigger_context TEXT,
            verification_status TEXT NOT NULL DEFAULT 'UNVERIFIED',
            confidence TEXT NOT NULL DEFAULT 'Low', risk_level TEXT NOT NULL DEFAULT 'Low',
            significance TEXT, analyst_rationale TEXT, created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )""")
        db.execute("""CREATE TABLE IF NOT EXISTS incident_sources (
            id INTEGER PRIMARY KEY AUTOINCREMENT, incident_id TEXT NOT NULL,
            source_url TEXT NOT NULL, source_name TEXT,
            source_class TEXT NOT NULL DEFAULT 'unknown', source_type TEXT, language TEXT,
            published_at TEXT, collected_at TEXT NOT NULL,
            source_role TEXT NOT NULL DEFAULT 'lead', independence_group TEXT,
            claim_summary TEXT, FOREIGN KEY (incident_id) REFERENCES incidents(incident_id),
            UNIQUE(incident_id, source_url)
        )""")
        db.execute("CREATE INDEX IF NOT EXISTS idx_incidents_report_date ON incidents(report_date)")
        db.execute("CREATE INDEX IF NOT EXISTS idx_incident_sources_incident ON incident_sources(incident_id)")


def _required(payload, key):
    value = str(payload.get(key, "")).strip()
    if not value:
        raise ValueError(f"{key} is required")
    return value


def upsert_incident(payload):
    """Insert/update an incident. Evidence status is explicit and never auto-upgraded."""
    initialize_incident_tables()
    incident_id = _required(payload, "incident_id")
    report_date = _required(payload, "report_date")
    datetime.strptime(report_date, "%Y-%m-%d")
    country = _required(payload, "country")
    category = _required(payload, "category")
    description = _required(payload, "description")
    status = payload.get("verification_status", "UNVERIFIED")
    confidence = payload.get("confidence", "Low")
    risk = payload.get("risk_level", "Low")
    if status not in VERIFICATION_STATUSES:
        raise ValueError("Invalid verification_status")
    if confidence not in CONFIDENCE_LEVELS:
        raise ValueError("Invalid confidence")
    if risk not in RISK_LEVELS:
        raise ValueError("Invalid risk_level")
    now = datetime.now(timezone.utc).isoformat()
    values = (
        incident_id, report_date, payload.get("incident_datetime"),
        payload.get("publication_datetime"), country, payload.get("admin1"),
        payload.get("admin2"), payload.get("location_text"), category,
        payload.get("actors"), description, payload.get("casualties"),
        payload.get("trigger_context"), status, confidence, risk,
        payload.get("significance"), payload.get("analyst_rationale"), now, now
    )
    with connect() as db:
        db.execute("""INSERT INTO incidents (
            incident_id, report_date, incident_datetime, publication_datetime, country,
            admin1, admin2, location_text, category, actors, description, casualties,
            trigger_context, verification_status, confidence, risk_level, significance,
            analyst_rationale, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(incident_id) DO UPDATE SET
            report_date=excluded.report_date, incident_datetime=excluded.incident_datetime,
            publication_datetime=excluded.publication_datetime, country=excluded.country,
            admin1=excluded.admin1, admin2=excluded.admin2, location_text=excluded.location_text,
            category=excluded.category, actors=excluded.actors, description=excluded.description,
            casualties=excluded.casualties, trigger_context=excluded.trigger_context,
            verification_status=excluded.verification_status, confidence=excluded.confidence,
            risk_level=excluded.risk_level, significance=excluded.significance,
            analyst_rationale=excluded.analyst_rationale, updated_at=excluded.updated_at""", values)


def add_incident_source(incident_id, source):
    url = _required(source, "source_url")
    collected_at = source.get("collected_at") or datetime.now(timezone.utc).isoformat()
    with connect() as db:
        exists = db.execute("SELECT 1 FROM incidents WHERE incident_id=?", (incident_id,)).fetchone()
        if not exists:
            raise ValueError("incident_id does not exist")
        db.execute("""INSERT INTO incident_sources (
            incident_id, source_url, source_name, source_class, source_type, language,
            published_at, collected_at, source_role, independence_group, claim_summary
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(incident_id, source_url) DO UPDATE SET
            source_name=excluded.source_name, source_class=excluded.source_class,
            source_type=excluded.source_type, language=excluded.language,
            published_at=excluded.published_at, collected_at=excluded.collected_at,
            source_role=excluded.source_role, independence_group=excluded.independence_group,
            claim_summary=excluded.claim_summary""",
        (incident_id, url, source.get("source_name"), source.get("source_class", "unknown"),
         source.get("source_type"), source.get("language"), source.get("published_at"),
         collected_at, source.get("source_role", "lead"), source.get("independence_group"),
         source.get("claim_summary")))


def get_report_incidents(report_date):
    datetime.strptime(report_date, "%Y-%m-%d")
    initialize_incident_tables()
    with connect() as db:
        incidents = [dict(r) for r in db.execute(
            "SELECT * FROM incidents WHERE report_date=? ORDER BY country, category, incident_id",
            (report_date,)
        ).fetchall()]
        for item in incidents:
            item["sources"] = [dict(r) for r in db.execute(
                "SELECT * FROM incident_sources WHERE incident_id=? ORDER BY source_role, source_name",
                (item["incident_id"],)
            ).fetchall()]
    return incidents
