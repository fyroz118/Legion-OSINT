"""High-volume, date-scoped public-web discovery. Search results remain unverified leads."""
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
MAX_QUERIES = 100
REGION_QUERIES = [
    # region, language scope, unofficial/local query, official query, rumour query
    ("Bangladesh", "bn+en", "বাংলাদেশ আজ সংঘর্ষ হামলা বিক্ষোভ রাজনৈতিক সহিংসতা শ্রমিক আন্দোলন জেলা উপজেলা স্থানীয় সাংবাদিক প্রত্যক্ষদর্শী", "Bangladesh police government election commission ministry district administration official statement incident", "বাংলাদেশ গুজব দাবি ভাইরাল ভিডিও অযাচাইকৃত খবর হামলার দাবি"),
    ("Bangladesh", "bn+en", "বাংলাদেশ সাম্প্রদায়িক হামলা সংখ্যালঘু মব সহিংসতা প্রত্যক্ষদর্শী স্থানীয় সংবাদ", "Bangladesh human rights commission minority affairs official communal violence statement", "বাংলাদেশ সংখ্যালঘু হামলার গুজব সাম্প্রদায়িক উত্তেজনা যাচাই"),
    ("Bangladesh", "bn+en", "Bangladesh political party student politics clash rally blockade arrest local reporter", "Bangladesh political party police court government official protest statement", "Bangladesh rumour alleged attack political clash viral claim"),
    ("Bangladesh", "bn+en", "Bangladesh border incident trafficking firing local eyewitness news", "Bangladesh BGB coast guard border official incident statement", "Bangladesh border firing rumour unconfirmed claim"),
    ("Bangladesh", "bn+en", "Bangladesh misinformation disinformation fact check viral social media claim", "Bangladesh official fact check government public advisory misinformation", "বাংলাদেশ গুজব ভুয়া খবর মিথ্যা দাবি সামাজিক মাধ্যমে ছড়ানো"),
    ("South Asia", "en+hi+ur+ne+si", "India Pakistan Nepal Sri Lanka Afghanistan Bhutan Maldives local journalist eyewitness protest violence unrest", "South Asia government police military election commission official incident statement", "South Asia unverified rumour viral claim alleged attack communal tension"),
    ("India", "en+hi", "India state district local reporter eyewitness communal violence protest mob attack political clash", "India police state government court official security incident statement", "India rumour viral claim alleged communal attack unverified"),
    ("Pakistan", "en+ur", "Pakistan local journalist eyewitness protest militant violence sectarian attack political unrest", "Pakistan police government military provincial official incident statement", "Pakistan rumour unverified attack viral claim sectarian tension"),
    ("Afghanistan", "en+fa+ps", "Afghanistan local reporter eyewitness security incident protest rights violence", "Afghanistan UNAMA government ministry official security statement", "Afghanistan rumour unverified incident viral claim"),
    ("Nepal and Sri Lanka", "en+ne+si", "Nepal Sri Lanka local news eyewitness protest political violence communal incident", "Nepal Sri Lanka police government official security statement", "Nepal Sri Lanka rumour viral unverified claim"),
    ("MENA", "en+ar+he+fa+tr", "Middle East North Africa local journalists eyewitness conflict civilian harm protest unrest communal violence", "MENA UN agencies government ministries police official conflict security statement", "Middle East rumour unverified strike casualty claim viral video"),
    ("MENA", "en+ar+he+fa", "Gaza West Bank Israel Lebanon Syria Iraq Yemen local reporting clashes displacement attacks", "OCHA UNIFIL WHO government official humanitarian security update Middle East", "Gaza Lebanon Syria rumour alleged attack unconfirmed casualty claim"),
    ("MENA", "en+ar+fa+tr", "Iran Iraq Turkey Gulf North Africa protest political violence labour unrest local reporters", "Iran Iraq Turkey Gulf North Africa official ministry police court statement", "MENA rumour coup protest attack viral claim unverified"),
    ("Europe", "en+fr+de+ru+uk", "Europe local journalists eyewitness protest far right violence communal unrest sabotage incident", "Europe police government EU OSCE official security incident statement", "Europe rumour viral claim alleged attack disinformation"),
    ("Sub-Saharan Africa", "en+fr+sw+ar", "Africa local journalist eyewitness communal violence conflict coup protest displacement", "Africa AU UN regional government police official incident statement", "Africa rumour unverified coup attack casualty claim"),
    ("East and Southeast Asia", "en+zh+id+th+my+ko", "East Southeast Asia local journalist eyewitness protest political violence communal unrest", "East Southeast Asia government police ASEAN UN official security statement", "Asia rumour viral claim alleged clash attack unverified"),
    ("Americas", "en+es+pt", "Americas local journalists eyewitness political violence protest communal unrest police incident", "Americas government police OAS UN official security incident statement", "Americas rumour viral claim alleged attack election violence unverified"),
    ("Global", "en+local", "independent journalists eyewitness civil society monitors emerging conflict incident report", "UN agencies international organizations official global security humanitarian update", "global rumour watch unverified claims viral footage conflict protest alleged incident"),
    ("Global misinformation", "en+bn+ar+hi+es", "fact check debunk recycled footage misinformation conflict protest violence social media", "independent newsroom fact check public safety misinformation investigation", "viral rumour unverified allegation recycled video false claim fact check"),
]

def build_query_plan(report_date, max_queries=None):
    datetime.strptime(report_date, "%Y-%m-%d")
    raw_limit = max_queries if max_queries is not None else os.getenv("RESEARCH_MAX_QUERIES", DEFAULT_MAX_QUERIES)
    limit = max(1, min(int(raw_limit), MAX_QUERIES))
    plan = []
    # Each region contributes paired discovery perspectives. Unofficial/local is a search focus,
    # not an assertion about the class of results returned by the provider.
    for region, language, unofficial, official, rumour in REGION_QUERIES:
        plan.extend([
            {"region": region, "language_scope": language, "query": unofficial,
             "source_focus": "unofficial_public", "claim_type": "EVENT_NEWS"},
            {"region": region, "language_scope": language, "query": official,
             "source_focus": "official_institutional", "claim_type": "EVENT_NEWS"},
            {"region": region, "language_scope": language, "query": rumour,
             "source_focus": "unofficial_public", "claim_type": "RUMOUR_WATCH"},
        ])
    # 19 regions/topics x 3 = 57; add three Bangladesh-specific local-language searches.
    plan.extend([
        {"region": "Bangladesh", "language_scope": "bn", "query": "বাংলাদেশ আজ জেলা উপজেলা স্থানীয় সংঘর্ষ বিক্ষোভ হামলা প্রত্যক্ষদর্শী সংবাদ",
         "source_focus": "unofficial_public", "claim_type": "EVENT_NEWS"},
        {"region": "Bangladesh", "language_scope": "bn", "query": "বাংলাদেশ আজ গুজব ভাইরাল দাবি যাচাই স্থানীয় সংবাদ",
         "source_focus": "unofficial_public", "claim_type": "RUMOUR_WATCH"},
        {"region": "Bangladesh", "language_scope": "bn+en", "query": "Bangladesh district upazila official police administration incident update",
         "source_focus": "official_institutional", "claim_type": "EVENT_NEWS"},
    ])
    for index, item in enumerate(plan[:limit]):
        item["report_date"] = report_date
        item["topic"] = "news"
        item["query_number"] = index + 1
    return plan[:limit]

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
        columns = {row["name"] for row in db.execute("PRAGMA table_info(research_leads)")}
        migrations = {
            "source_focus": "TEXT NOT NULL DEFAULT 'unknown'",
            "claim_type": "TEXT NOT NULL DEFAULT 'EVENT_NEWS'",
            "source_class": "TEXT NOT NULL DEFAULT 'unknown'",
            "review_status": "TEXT NOT NULL DEFAULT 'UNREVIEWED'",
            "publication_date_dhaka": "TEXT",
        }
        for name, declaration in migrations.items():
            if name not in columns:
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

def _parse_publication_date(value):
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        try:
            parsed = parsedate_to_datetime(str(value))
        except (TypeError, ValueError, OverflowError):
            return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=ZoneInfo("Asia/Dhaka"))
    return parsed.astimezone(ZoneInfo("Asia/Dhaka"))

def _publication_date_matches(value, report_date):
    parsed = _parse_publication_date(value)
    return parsed is None or parsed.date().isoformat() == report_date

def run_research(report_date, max_queries=None, max_results=10, search_fn=None):
    """Run high-volume date-scoped discovery and persist leads without verifying them."""
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
                    pub = result.get("published_date") or result.get("publishedDate")
                    parsed = _parse_publication_date(pub)
                    db.execute("""INSERT INTO research_leads (
                        report_date, query, region, title, source_url, domain, published_date,
                        snippet, relevance_score, provider, collected_at, source_focus,
                        claim_type, source_class, review_status, publication_date_dhaka
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'tavily', ?, ?, ?, 'unknown', 'UNREVIEWED', ?)
                    ON CONFLICT(report_date, source_url) DO UPDATE SET
                        query=excluded.query, region=excluded.region, title=excluded.title,
                        domain=excluded.domain, published_date=excluded.published_date,
                        snippet=excluded.snippet, relevance_score=excluded.relevance_score,
                        source_focus=excluded.source_focus, claim_type=excluded.claim_type,
                        collected_at=excluded.collected_at""",
                    (report_date, item["query"], item["region"], result.get("title"), url,
                     domain, pub, result.get("content") or result.get("snippet"),
                     result.get("score"), now, item["source_focus"], item["claim_type"],
                     parsed.isoformat() if parsed else None))
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

def get_research_leads(report_date, limit=100):
    datetime.strptime(report_date, "%Y-%m-%d")
    initialize_research_tables()
    with connect() as db:
        return [dict(row) for row in db.execute(
            """SELECT * FROM research_leads WHERE report_date=?
            ORDER BY CASE region WHEN 'Bangladesh' THEN 0
                     WHEN 'South Asia' THEN 1
                     WHEN 'India' THEN 2 WHEN 'Pakistan' THEN 3
                     WHEN 'MENA' THEN 4 ELSE 5 END,
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
               GROUP BY region, status ORDER BY region, status""", (report_date,)
        ).fetchall()
    return [dict(row) for row in rows]
