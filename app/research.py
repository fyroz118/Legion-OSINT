"""High-volume, date-scoped public-web discovery. Results remain unverified source leads."""
import json
import os
import urllib.error
import urllib.request
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
from email.utils import parsedate_to_datetime
from app.database import connect

API_URL = "https://api.tavily.com/search"
DEFAULT_MAX_QUERIES = 60
MAX_QUERIES_HARD_LIMIT = 100

# Search allocation is an attention target, not a claim about source credibility.
# 70% of planned queries seek unofficial/local reporting and public eyewitness leads;
# 30% seek official/institutional statements. Source class remains unknown until reviewed.
REGIONS = [
    ("Bangladesh", "bn+en", 12),
    ("South Asia", "en+hi+ur+ne+si+ps", 10),
    ("Middle East and North Africa", "en+ar+fa+he+tr", 10),
    ("Europe", "en+fr+de+ru+uk", 6),
    ("Sub-Saharan Africa", "en+fr+sw+ar", 6),
    ("East and Southeast Asia", "en+zh+id+th+my+ko", 6),
    ("Americas", "en+es+pt", 6),
    ("Central Asia and Caucasus", "en+ru+fa+tr", 4),
]

UNOFFICIAL_TERMS = [
    "local journalists eyewitnesses independent reporters public social media posts",
    "local news reports community monitors civil society field reports",
    "unconfirmed reports rumours claims viral posts fact check verification",
    "district local-language reporting eyewitness accounts independent media",
    "protest clashes violence security incidents local reporters",
]
OFFICIAL_TERMS = [
    "official government police court emergency agency institutional statements",
    "official ministry public safety humanitarian agency situation updates",
    "government election commission parliament public authority announcements",
]


def build_query_plan(report_date, max_queries=None):
    datetime.strptime(report_date, "%Y-%m-%d")
    requested = max_queries if max_queries is not None else os.getenv("RESEARCH_MAX_QUERIES", DEFAULT_MAX_QUERIES)
    limit = max(1, min(int(requested), MAX_QUERIES_HARD_LIMIT))
    planned = []
    for region, language, count in REGIONS:
        for index in range(count):
            if region == "Bangladesh":
                themes = [
                    "রাজনৈতিক সহিংসতা সংঘর্ষ বিক্ষোভ হামলা গ্রেপ্তার",
                    "সাম্প্রদায়িক হামলা সংখ্যালঘু মব সহিংসতা",
                    "শ্রমিক আন্দোলন আইনশৃঙ্খলা সীমান্ত ঘটনা",
                    "জেলা উপজেলা স্থানীয় সংবাদ প্রত্যক্ষদর্শী",
                    "গুজব অযাচাইকৃত দাবি ভাইরাল ভিডিও তথ্য যাচাই",
                    "Bangladesh political mobilisation student politics party clashes",
                    "Bangladesh communal violence mob attack minority community",
                    "Bangladesh police arrests law enforcement protest labour unrest",
                    "Bangladesh border security Rohingya displacement humanitarian",
                    "Bangladesh court government election institutional developments",
                    "Bangladesh local journalists eyewitness public social posts incident",
                    "Bangladesh official police ministry disaster agency statements",
                ]
            elif region == "South Asia":
                themes = [
                    "political violence protests clashes arrests",
                    "communal religious ethnic violence mob attacks",
                    "border security insurgency conflict displacement",
                    "elections political mobilisation constitutional developments",
                    "rumours unverified claims viral video misinformation fact checks",
                    "local journalists eyewitness community reports security incidents",
                    "India Pakistan Kashmir Afghanistan Nepal Sri Lanka Bhutan Maldives",
                    "official police government court election commission statements",
                    "labour unrest attacks on journalists civil society",
                    "humanitarian emergencies cross-border developments",
                ]
            elif region == "Middle East and North Africa":
                themes = [
                    "armed conflict civilian harm displacement ceasefire developments",
                    "political unrest protests arrests communal sectarian violence",
                    "border incidents security developments humanitarian access",
                    "rumours unverified claims viral footage misinformation verification",
                    "local journalists eyewitness public posts independent monitors",
                    "official government military police UN humanitarian statements",
                    "Israel Palestine Gaza West Bank Lebanon Syria",
                    "Iran Iraq Yemen Gulf states",
                    "North Africa Libya Sudan Egypt Tunisia Algeria Morocco",
                    "attacks on journalists civil society labour protests",
                ]
            else:
                themes = [
                    "political violence protests communal unrest security incidents",
                    "armed conflict civilian harm displacement humanitarian situation",
                    "rumours unverified claims viral media misinformation fact checks",
                    "local journalists eyewitness independent monitors public social posts",
                    "official government police election humanitarian agency statements",
                    "elections coups constitutional crises attacks on journalists",
                ]
            theme = themes[index % len(themes)]
            unofficial = (len(planned) % 10) < 7
            focus = "unofficial_public" if unofficial else "official_institutional"
            source_terms = UNOFFICIAL_TERMS[index % len(UNOFFICIAL_TERMS)] if unofficial else OFFICIAL_TERMS[index % len(OFFICIAL_TERMS)]
            query = f"{region} {theme} {source_terms}"
            planned.append({
                "report_date": report_date, "region": region, "language_scope": language,
                "query": query, "topic": "news", "source_focus": focus,
                "claim_type": "RUMOUR_WATCH" if ("rumour" in theme or "গুজব" in theme or "unverified claims" in theme) else "EVENT_NEWS",
            })
    # Stable 70:30 attention split across the full plan, without asserting source identity.
    planned.sort(key=lambda item: (item["source_focus"] != "unofficial_public",))
    return planned[:limit]


def initialize_research_tables():
    with connect() as db:
        db.execute("""CREATE TABLE IF NOT EXISTS research_queries (
            id INTEGER PRIMARY KEY AUTOINCREMENT, report_date TEXT NOT NULL,
            query TEXT NOT NULL, region TEXT NOT NULL, language_scope TEXT,
            provider TEXT NOT NULL, status TEXT NOT NULL,
            result_count INTEGER NOT NULL DEFAULT 0, error_type TEXT,
            searched_at TEXT NOT NULL, UNIQUE(report_date, query, provider)
        )""")
        db.execute("""CREATE TABLE IF NOT EXISTS research_leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT, report_date TEXT NOT NULL,
            query TEXT NOT NULL, region TEXT NOT NULL, title TEXT,
            source_url TEXT NOT NULL, domain TEXT, published_date TEXT,
            snippet TEXT, relevance_score REAL, provider TEXT NOT NULL,
            collected_at TEXT NOT NULL, UNIQUE(report_date, source_url)
        )""")
        existing = {row["name"] for row in db.execute("PRAGMA table_info(research_leads)")}
        for name, declaration in {
            "source_focus": "TEXT NOT NULL DEFAULT 'unknown'",
            "claim_type": "TEXT NOT NULL DEFAULT 'EVENT_NEWS'",
            "review_status": "TEXT NOT NULL DEFAULT 'UNREVIEWED'",
            "source_class": "TEXT NOT NULL DEFAULT 'unknown'",
        }.items():
            if name not in existing:
                db.execute(f"ALTER TABLE research_leads ADD COLUMN {name} {declaration}")
        db.execute("CREATE INDEX IF NOT EXISTS idx_research_leads_date ON research_leads(report_date)")


def _call_tavily(query, report_date, max_results=10):
    api_key = os.getenv("TAVILY_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("TAVILY_API_KEY is not configured")
    payload = {
        "query": query, "topic": "news",
        "search_depth": os.getenv("TAVILY_SEARCH_DEPTH", "basic"),
        "max_results": max(1, min(int(max_results), 10)),
        "start_date": report_date,
        "end_date": (datetime.strptime(report_date, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d"),
        "include_answer": False, "include_raw_content": False, "include_images": False,
        "include_published_date": True, "filter_by_published_date": False,
    }
    request = urllib.request.Request(
        API_URL, data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=45) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read(500).decode("utf-8", errors="replace")
        raise RuntimeError(f"Tavily HTTP {exc.code}: {body}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Tavily connection failed: {exc.reason}") from exc


def _publication_date_matches(value, report_date):
    if not value:
        return True
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        try:
            parsed = parsedate_to_datetime(str(value))
        except (TypeError, ValueError, OverflowError):
            return True
    if parsed.tzinfo is not None:
        parsed = parsed.astimezone(ZoneInfo("Asia/Dhaka"))
    return parsed.date().isoformat() == report_date


def run_research(report_date, max_queries=None, max_results=10, search_fn=None):
    """Run expanded discovery and persist every distinct URL as an unreviewed lead."""
    datetime.strptime(report_date, "%Y-%m-%d")
    initialize_research_tables()
    queries = build_query_plan(report_date, max_queries=max_queries)
    if search_fn is None and not os.getenv("TAVILY_API_KEY", "").strip():
        raise RuntimeError("TAVILY_API_KEY is not configured")
    search_fn = search_fn or _call_tavily
    summary = {"report_date": report_date, "provider": "tavily", "queries_attempted": 0,
               "queries_succeeded": 0, "leads_saved": 0, "errors": [],
               "unofficial_focus_queries": sum(x["source_focus"] == "unofficial_public" for x in queries),
               "official_focus_queries": sum(x["source_focus"] == "official_institutional" for x in queries)}
    for item in queries:
        summary["queries_attempted"] += 1
        now = datetime.now(timezone.utc).isoformat()
        try:
            response = search_fn(item["query"], report_date, max_results=max_results)
            results = response.get("results", []) if isinstance(response, dict) else []
            results = [r for r in results if _publication_date_matches(
                r.get("published_date") or r.get("publishedDate"), report_date)]
            saved = 0
            with connect() as db:
                for result in results:
                    url = str(result.get("url") or "").strip()
                    if not url.startswith(("https://", "http://")):
                        continue
                    domain = url.split("/")[2] if "://" in url else None
                    db.execute("""INSERT INTO research_leads (
                        report_date, query, region, title, source_url, domain, published_date,
                        snippet, relevance_score, provider, collected_at, source_focus, claim_type
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'tavily', ?, ?, ?)
                    ON CONFLICT(report_date, source_url) DO UPDATE SET
                        query=excluded.query, region=excluded.region, title=excluded.title,
                        domain=excluded.domain, published_date=excluded.published_date,
                        snippet=excluded.snippet, relevance_score=excluded.relevance_score,
                        collected_at=excluded.collected_at, source_focus=excluded.source_focus,
                        claim_type=excluded.claim_type""",
                    (report_date, item["query"], item["region"], result.get("title"), url,
                     domain, result.get("published_date") or result.get("publishedDate"),
                     result.get("content") or result.get("snippet"), result.get("score"), now,
                     item["source_focus"], item["claim_type"]))
                    saved += 1
                db.execute("""INSERT INTO research_queries (
                    report_date, query, region, language_scope, provider, status, result_count, searched_at
                ) VALUES (?, ?, ?, ?, 'tavily', 'success', ?, ?)
                ON CONFLICT(report_date, query, provider) DO UPDATE SET
                    status='success', result_count=excluded.result_count,
                    error_type=NULL, searched_at=excluded.searched_at""",
                (report_date, item["query"], item["region"], item["language_scope"], len(results), now))
            summary["queries_succeeded"] += 1
            summary["leads_saved"] += saved
        except Exception as exc:
            error_type = type(exc).__name__
            summary["errors"].append({"region": item["region"], "error": error_type, "detail": str(exc)[:300]})
            with connect() as db:
                db.execute("""INSERT INTO research_queries (
                    report_date, query, region, language_scope, provider, status, result_count, error_type, searched_at
                ) VALUES (?, ?, ?, ?, 'tavily', 'failed', 0, ?, ?)
                ON CONFLICT(report_date, query, provider) DO UPDATE SET
                    status='failed', error_type=excluded.error_type, searched_at=excluded.searched_at""",
                (report_date, item["query"], item["region"], item["language_scope"], error_type, now))
    summary["unique_leads_for_date"] = len(get_research_leads(report_date, limit=1000))
    return summary


def get_research_leads(report_date, limit=100):
    datetime.strptime(report_date, "%Y-%m-%d")
    initialize_research_tables()
    with connect() as db:
        return [dict(row) for row in db.execute(
            """SELECT * FROM research_leads WHERE report_date=?
            ORDER BY CASE region WHEN 'Bangladesh' THEN 0 WHEN 'South Asia' THEN 1
                     WHEN 'Middle East and North Africa' THEN 2 ELSE 3 END,
                     relevance_score DESC, collected_at DESC LIMIT ?""",
            (report_date, max(1, min(int(limit), 1000)))
        ).fetchall()]


def get_research_coverage(report_date):
    datetime.strptime(report_date, "%Y-%m-%d")
    initialize_research_tables()
    with connect() as db:
        rows = db.execute(
            """SELECT region, status, COUNT(*) AS query_count, SUM(result_count) AS result_count
               FROM research_queries WHERE report_date=?
               GROUP BY region, status ORDER BY region, status""", (report_date,)
        ).fetchall()
    return [dict(row) for row in rows]
