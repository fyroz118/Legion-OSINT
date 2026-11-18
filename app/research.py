"""Date-scoped public-web research adapter. Results are leads, never automatic verification."""
import json
import os
import urllib.error
import urllib.request
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
from email.utils import parsedate_to_datetime
from app.database import connect

API_URL = "https://api.tavily.com/search"
DEFAULT_MAX_QUERIES = 12


def build_query_plan(report_date, max_queries=None):
    datetime.strptime(report_date, "%Y-%m-%d")
    limit = max(1, min(int(max_queries or os.getenv("RESEARCH_MAX_QUERIES", DEFAULT_MAX_QUERIES)), 20))
    planned = [
        ("Bangladesh", "bn+en", "Bangladesh political violence protest clash arrest mobilisation"),
        ("Bangladesh", "bn", "বাংলাদেশ সহিংসতা সংঘর্ষ বিক্ষোভ হামলা নিহত আহত"),
        ("Bangladesh", "bn+en", "বাংলাদেশ সাম্প্রদায়িক হামলা সংখ্যালঘু মব violence"),
        ("Bangladesh", "bn+en", "বাংলাদেশ শ্রমিক আন্দোলন আইনশৃঙ্খলা সীমান্ত ঘটনা"),
        ("Bangladesh", "bn+en", "Bangladesh misinformation fact check viral claim incident"),
        ("South Asia", "en+local", "South Asia political violence communal unrest border incident"),
        ("MENA", "en+ar", "Middle East North Africa conflict civilian security protest incident اشتباكات عنف سياسي احتجاجات"),
        ("Europe", "en+fr", "Europe political violence communal unrest protest security incident violences politiques manifestations"),
        ("Sub-Saharan Africa", "en+fr", "Africa conflict communal violence coup protest displacement incident violences communautaires conflit déplacement"),
        ("East and Southeast Asia", "en+id+th", "East Southeast Asia unrest political violence security incident kekerasan politik bentrokan unjuk rasa ความรุนแรงทางการเมือง"),
        ("Americas", "en+es+pt", "Americas political violence communal unrest protest security incident violencia política disturbios protestas violência política"),
        ("Global", "en+local", "fact check misinformation recycled video conflict violence protest"),
    ]
    return [
        {"report_date": report_date, "region": region, "language_scope": language,
         "query": query, "topic": "news"}
        for region, language, query in planned[:limit]
    ]


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
        db.execute("CREATE INDEX IF NOT EXISTS idx_research_leads_date ON research_leads(report_date)")


def _call_tavily(query, report_date, max_results=5):
    api_key = os.getenv("TAVILY_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("TAVILY_API_KEY is not configured")
    payload = {
        "query": query, "topic": "news",
        "search_depth": os.getenv("TAVILY_SEARCH_DEPTH", "basic"),
        "max_results": max(1, min(int(max_results), 10)),
        "start_date": report_date, "end_date": (datetime.strptime(report_date, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d"),
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


def run_research(report_date, max_queries=None, max_results=5, search_fn=None):
    """Run date-filtered discovery queries and persist source leads; no fact verification."""
    datetime.strptime(report_date, "%Y-%m-%d")
    initialize_research_tables()
    queries = build_query_plan(report_date, max_queries=max_queries)
    if search_fn is None and not os.getenv("TAVILY_API_KEY", "").strip():
        raise RuntimeError("TAVILY_API_KEY is not configured")
    search_fn = search_fn or _call_tavily
    summary = {"report_date": report_date, "provider": "tavily", "queries_attempted": 0,
               "queries_succeeded": 0, "leads_saved": 0, "errors": []}
    for item in queries:
        summary["queries_attempted"] += 1
        now = datetime.now(timezone.utc).isoformat()
        try:
            response = search_fn(item["query"], report_date, max_results=max_results)
            results = response.get("results", []) if isinstance(response, dict) else []
            results = [
                result for result in results
                if _publication_date_matches(
                    result.get("published_date") or result.get("publishedDate"), report_date
                )
            ]
            saved = 0
            with connect() as db:
                for result in results:
                    url = str(result.get("url") or "").strip()
                    if not url.startswith(("https://", "http://")):
                        continue
                    domain = url.split("/")[2] if "://" in url else None
                    db.execute("""INSERT INTO research_leads (
                        report_date, query, region, title, source_url, domain,
                        published_date, snippet, relevance_score, provider, collected_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'tavily', ?)
                    ON CONFLICT(report_date, source_url) DO UPDATE SET
                        query=excluded.query, region=excluded.region, title=excluded.title,
                        domain=excluded.domain, published_date=excluded.published_date,
                        snippet=excluded.snippet, relevance_score=excluded.relevance_score,
                        collected_at=excluded.collected_at""",
                    (report_date, item["query"], item["region"], result.get("title"), url,
                     domain, result.get("published_date") or result.get("publishedDate"),
                     result.get("content") or result.get("snippet"), result.get("score"), now))
                    saved += 1
                db.execute("""INSERT INTO research_queries (
                    report_date, query, region, language_scope, provider, status,
                    result_count, searched_at
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
                    report_date, query, region, language_scope, provider, status,
                    result_count, error_type, searched_at
                ) VALUES (?, ?, ?, ?, 'tavily', 'failed', 0, ?, ?)
                ON CONFLICT(report_date, query, provider) DO UPDATE SET
                    status='failed', error_type=excluded.error_type,
                    searched_at=excluded.searched_at""",
                (report_date, item["query"], item["region"], item["language_scope"], error_type, now))
    summary["unique_leads_for_date"] = len(get_research_leads(report_date, limit=1000))
    return summary


def get_research_leads(report_date, limit=30):
    datetime.strptime(report_date, "%Y-%m-%d")
    initialize_research_tables()
    with connect() as db:
        return [dict(row) for row in db.execute(
            """SELECT * FROM research_leads WHERE report_date=?
            ORDER BY CASE region WHEN 'Bangladesh' THEN 0 ELSE 1 END,
                     relevance_score DESC, collected_at DESC LIMIT ?""",
            (report_date, max(1, min(int(limit), 1000)))
        ).fetchall()]


def get_research_coverage(report_date):
    datetime.strptime(report_date, "%Y-%m-%d")
    initialize_research_tables()
    with connect() as db:
        rows = db.execute(
            """SELECT region, status, COUNT(*) AS query_count,
                      SUM(result_count) AS result_count
               FROM research_queries WHERE report_date=?
               GROUP BY region, status ORDER BY region, status""",
            (report_date,)
        ).fetchall()
    return [dict(row) for row in rows]
