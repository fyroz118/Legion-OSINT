"""Publish a bounded, read-only feed of public Telegram and RSS source leads.

The feed contains public source material only. Analyst notes, decisions, incident
drafts, private identifiers and credentials are never published.
"""
import csv
import hashlib
import json
import re
from datetime import datetime, timezone, date, timedelta
from zoneinfo import ZoneInfo
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "output"
DEST = ROOT / "docs" / "feed" / "latest.json"
ARCHIVE_DIR = ROOT / "docs" / "feed" / "archive"
MAX_POSTS = 1800
MAX_ARCHIVE_POSTS = 5000  # Bound the public feed; collection workflow publishes from main only.
MAX_TEXT = 3000

# Bangladesh's 64 administrative districts. Mentions are text matches only,
# never proof that an incident occurred in that district.
BANGLADESH_DISTRICTS = [
    "Bagerhat", "Bandarban", "Barguna", "Barishal", "Bhola", "Bogura",
    "Brahmanbaria", "Chandpur", "Chattogram", "Chuadanga", "Cox's Bazar",
    "Cumilla", "Dhaka", "Dinajpur", "Faridpur", "Feni", "Gaibandha",
    "Gazipur", "Gopalganj", "Habiganj", "Jamalpur", "Jashore", "Jhalokati",
    "Jhenaidah", "Joypurhat", "Khagrachhari", "Khulna", "Kishoreganj",
    "Kurigram", "Kushtia", "Lakshmipur", "Lalmonirhat", "Madaripur",
    "Magura", "Manikganj", "Meherpur", "Moulvibazar", "Munshiganj",
    "Mymensingh", "Naogaon", "Narail", "Narayanganj", "Narsingdi",
    "Natore", "Netrokona", "Nilphamari", "Noakhali", "Pabna", "Panchagarh",
    "Patuakhali", "Pirojpur", "Rajbari", "Rajshahi", "Rangamati",
    "Rangpur", "Satkhira", "Shariatpur", "Sherpur", "Sirajganj",
    "Sunamganj", "Sylhet", "Tangail", "Thakurgaon"
]


def read_csv(path):
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def normalize_row(row, platform):
    username = (row.get("channel_username") or row.get("source_id") or "").strip().lstrip("@")
    message_id = str(row.get("message_id") or row.get("id") or "").strip()
    text = " ".join((row.get("text") or "").split())
    source_url = (row.get("source_url") or row.get("url") or "").strip()
    if not username or not message_id or not text or not source_url.startswith("https://"):
        return None
    source_platform = row.get("platform") or platform
    publisher_name = row.get("publisher_name") or username
    display_source = ("RSS: " + publisher_name) if source_platform == "RSS/Atom" else username
    return {
        "id": username + ":" + message_id,
        "channel_username": display_source,
        "publisher_name": publisher_name,
        "platform": source_platform,
        "published_at": row.get("published_at") or None,
        "collected_at": row.get("collected_at") or None,
        "text": text[:MAX_TEXT],
        "source_url": source_url,
        "language": row.get("language") or "unknown",
        "priority_region": row.get("priority_region") or "global",
        "source_class": row.get("source_class") or "unknown",
        "source_type": row.get("source_type") or platform.lower(),
        "source_affiliation": row.get("source_affiliation") or "unknown",
        "monitoring_weight": row.get("monitoring_weight") or "standard",
        "evidence_status": "UNVERIFIED",
    }




# Conservative, transparent triage rules. These identify relevant source material,
# not verified events, perpetrators, motives, or risk levels.
# Precision-first rules: category relevance and event-action evidence are separate.
# Broad words such as "military", "army", "war", "attack" or "arrested" alone
# are deliberately insufficient to classify a source post as an incident.
RELEVANCE_RULES = {
    "armed_conflict_security": [
        "armed conflict", "armed attack", "attack on civilians", "attack on police",
        "attack on village", "attack on convoy", "attack on infrastructure",
        "airstrike", "air strike", "drone strike", "shelling", "artillery strike",
        "missile strike", "missiles hit", "missile hit", "strike hit", "bombed the", "bombed a", "bombed in", "bombed near", "struck the", "struck a", "struck in", "drone hit", "was hit by a missile", "was hit by a drone", "explosion", "military operation",
        "border clash", "cross-border attack", "clashes between troops",
        "troops killed", "soldiers killed", "civilians killed", "civilian casualties",
        "missile launch preparation", "strike preparation", "ready for a possible launch",
        "missiles inbound", "cruise missiles inbound"
    ],
    "political_security": [
        "political violence", "political assassination", "assassination attempt",
        "state of emergency", "declared curfew", "imposed curfew",
        "mass arrest", "political activists arrested", "opposition activists detained",
        "security forces raided", "police raid", "crackdown on protesters",
        "political prisoner", "police arrested", "security forces arrested", "activists arrested", "threatened retaliation", "threat of attack", "threatened an attack", "threatened to attack"
    ],
    "civil_unrest_labour": [
        "protesters blocked", "workers blocked", "road blockade", "blocked the road",
        "staged a protest", "held a protest", "announced protest",
        "protest programme", "protest programmes", "workers began a protest",
        "protest and blockade", "blockade over unpaid wages", "clashed with police",
        "police fired", "tear gas", "dispersed protesters", "riot broke out",
        "demonstrators marched", "protesters marched", "workers' strike",
        "workers strike", "general strike", "hartal", "violent protest"
    ],
    "communal_identity": [
        "communal violence", "sectarian violence", "religious violence",
        "mob attack", "lynching", "hate crime", "minority attack",
        "temple attack", "mosque attack", "church attack", "ethnic violence",
        "identity-based attack", "attacked because of religion"
    ],
    "humanitarian_displacement": [
        "mass displacement", "displaced civilians", "refugee camp attacked",
        "internally displaced", "humanitarian crisis", "civilian casualties",
        "mass casualties", "forced evacuation", "shelter destroyed",
        "aid convoy attacked", "humanitarian aid blocked"
    ],
    "infrastructure_disruption": [
        "power outage", "blackout", "power plant attacked", "water supply disrupted",
        "hospital attacked", "school attacked", "bridge destroyed", "railway attacked",
        "airport attacked", "port attacked", "fuel depot attacked",
        "critical infrastructure attacked", "communications outage",
        "internet shutdown", "bank branch attacked", "factory attacked",
        "transport disrupted"
    ],
    "public_health_emergency": [
        "disease outbreak", "epidemic", "cholera outbreak", "dengue outbreak",
        "measles outbreak", "public health emergency", "mass poisoning",
        "hospital overwhelmed", "health facility attacked", "vaccine emergency"
    ],
    "disaster_environment": [
        "cyclone", "earthquake", "landslide", "flash flood", "flooding",
        "wildfire", "industrial fire", "chemical spill", "dam failure",
        "storm surge", "heat emergency", "disaster response"
    ]
}

PHYSICAL_INCIDENT_TERMS = [
    "armed attack", "attack on civilians", "attack on police", "attack on village",
    "attack on convoy", "attack on infrastructure", "airstrike", "air strike",
    "drone strike", "shelling", "artillery strike", "missile strike", "bombing",
    "explosion", "blast", "shot dead", "shot and killed", "shooting",
    "fired on civilians", "civilians killed", "soldiers killed", "troops killed",
    "wounded civilians", "civilians injured", "mass casualties", "lynching",
    "mob attack", "hospital attacked", "school attacked", "bridge destroyed",
    "airport attacked", "port attacked", "factory attacked", "power plant attacked",
    "arson attack", "set fire to", "torched"
]
UNREST_ACTION_TERMS = [
    "staged a protest", "held a protest", "protesters blocked", "workers blocked",
    "workers began a protest", "protest and blockade", "blockade over unpaid wages",
    "road blockade", "blocked the road", "clashed with police", "clashed with",
    "police fired", "tear gas", "dispersed protesters", "riot broke out",
    "demonstrators marched", "protesters marched", "workers' strike",
    "workers strike", "general strike", "hartal", "violent protest"
]
SECURITY_ACTION_TERMS = [
    "police arrested", "police detained", "security forces arrested",
    "security forces detained", "activists arrested", "opposition activists detained",
    "mass arrest", "police raid", "security forces raided", "abducted",
    "kidnapped", "forcibly disappeared"
]
THREAT_TERMS = [
    "threatened to attack", "threatened an attack", "threat of attack", "vowed retaliation",
    "threatened retaliation", "warned of attack", "threatened violence",
    "called for an attack", "called for violence"
]
PREPARATION_TERMS = [
    "preparing for a strike", "strike preparation", "preparing a launch",
    "ready for a possible launch", "possible launch", "missiles inbound",
    "cruise missiles inbound", "may launch", "could launch", "plans to strike",
    "planned strike", "possible attack", "possible military action",
    "considering military action", "not rushing into a decision", "anticipated arsenal"
]
NON_EVENT_CONTEXT_TERMS = [
    "call of duty", "video game", "gaming", "gameplay", "video games",
    "film award", "film awards", "movie award", "movie awards",
    "film festival", "actor wins", "actress wears", "fashion shoot",
    "fashion week", "football game", "cricket match", "sports match",
    "book launch", "album launch", "concert", "music award", "music awards",
    "weighs new strikes", "considering a new round of strikes", "considering new strikes",
    "not rushing into a decision", "tehran summit", "at a seminar", "military analysis",
    "analyst discusses", "political commentary"
]


# Bangladesh recall layer: bilingual phrase triggers. These indicate review leads only.
RELEVANCE_RULES["civil_unrest_labour"] += ["বিক্ষোভ", "প্রতিবাদ", "অবরোধ", "ধর্মঘট", "হরতাল", "শ্রমিক আন্দোলন", "ধাওয়া-পাল্টাধাওয়া", "ধাওয়া-পাল্টা ধাওয়া", "সংঘর্ষ", "পুলিশের সঙ্গে সংঘর্ষ"]
RELEVANCE_RULES["political_security"] += ["রাজনৈতিক সংঘর্ষ", "রাজনৈতিক হামলা", "গ্রেপ্তার", "গ্রেফতার", "আটক", "পুলিশি অভিযান", "গুলি চালানো", "গুলিবিদ্ধ", "নিহত", "আহত"]
RELEVANCE_RULES["communal_identity"] += ["সাম্প্রদায়িক হামলা", "সাম্প্রদায়িক হামলা", "মন্দিরে হামলা", "মসজিদে হামলা", "গির্জায় হামলা", "গির্জায় হামলা", "সংখ্যালঘুদের ওপর হামলা", "ধর্মীয় উপাসনালয়ে হামলা"]
RELEVANCE_RULES["infrastructure_disruption"] += ["বিদ্যুৎ বিচ্ছিন্ন", "বিদ্যুৎ সরবরাহ বন্ধ", "সড়ক অবরোধ", "রেল চলাচল বন্ধ"]
PHYSICAL_INCIDENT_TERMS += ["missiles hit", "missile hit", "strike hit", "bombed the", "bombed a", "bombed in", "bombed near", "struck the", "struck a", "struck in", "drone hit", "was hit by a missile", "was hit by a drone", "হামলা চালিয়েছে", "হামলা চালায়", "হামলা করেছে", "আক্রমণ করেছে", "গুলি চালিয়েছে", "গুলি চালায়", "গুলিতে নিহত", "গুলিবিদ্ধ", "বিস্ফোরণ ঘটেছে", "বোমা বিস্ফোরণ", "অগ্নিসংযোগ করেছে", "ভাঙচুর করেছে", "সংঘর্ষে নিহত", "সংঘর্ষে আহত"]
UNREST_ACTION_TERMS += ["বিক্ষোভ করেছে", "বিক্ষোভ করেন", "বিক্ষোভ শুরু", "সড়ক অবরোধ", "রাস্তা অবরোধ", "অবরোধ করেছে", "অবরোধ করেন", "ধাওয়া-পাল্টাধাওয়া", "ধাওয়া-পাল্টা ধাওয়া", "সংঘর্ষে জড়ায়", "সংঘর্ষে জড়ায়", "পুলিশের সঙ্গে সংঘর্ষ", "শ্রমিকদের বিক্ষোভ"]
SECURITY_ACTION_TERMS += ["গ্রেপ্তার করেছে", "গ্রেফতার করেছে", "আটক করেছে", "অভিযানে গ্রেপ্তার", "পুলিশ গ্রেপ্তার", "নিরাপত্তা বাহিনী গ্রেপ্তার"]
THREAT_TERMS += ["হামলার হুমকি", "আক্রমণের হুমকি"]
PREPARATION_TERMS += ["হামলার প্রস্তুতি", "আক্রমণের প্রস্তুতি", "হামলা চালানোর প্রস্তুতি"]

def _phrase_hits(body, terms):
    """Match whole phrases and avoid substring errors such as 'war' in 'award'."""
    hits = []
    for term in terms:
        pattern = r"(?<!\w)" + r"\s+".join(re.escape(part) for part in term.lower().split()) + r"(?!\w)"
        if re.search(pattern, body):
            hits.append(term)
    return hits

def triage_source_post(item):
    """Return multi-label source-claim indicators; never verify an incident."""
    body = " ".join(str(item.get("text") or "").lower().split())
    non_event_context = _phrase_hits(body, NON_EVENT_CONTEXT_TERMS)
    matched = []
    for category, terms in RELEVANCE_RULES.items():
        hits = _phrase_hits(body, terms)
        if hits:
            matched.append((category, hits[:4]))
    physical_hits = _phrase_hits(body, PHYSICAL_INCIDENT_TERMS)
    unrest_hits = _phrase_hits(body, UNREST_ACTION_TERMS)
    security_hits = _phrase_hits(body, SECURITY_ACTION_TERMS)
    threat_hits = _phrase_hits(body, THREAT_TERMS)
    preparation_hits = _phrase_hits(body, PREPARATION_TERMS)

    # Explicit entertainment/sport contexts suppress incidental keyword hits,
    # unless a strong, distinct real-world event phrase is also present.
    strong_real_world = any(term in physical_hits for term in (
        "attack on civilians", "attack on police", "attack on village",
        "attack on convoy", "civilians killed", "shot dead", "lynching"
    ))
    if non_event_context and not strong_real_world:
        matched = []
        physical_hits = []
        unrest_hits = []
        security_hits = []
        threat_hits = []
        preparation_hits = []

    # Preserve all supported claim types. Preparation language must not erase
    # a separate alleged completed/ongoing physical event in the same post.
    claim_types = []
    if physical_hits:
        claim_types.append("physical_incident_claim")
    if unrest_hits:
        claim_types.append("civil_unrest_claim")
    if security_hits:
        claim_types.append("security_action_claim")
    if threat_hits or preparation_hits:
        claim_types.append("threat_or_preparation_claim")

    if physical_hits:
        record_type = "physical_incident_lead"
    elif unrest_hits:
        record_type = "civil_unrest_event_lead"
    elif security_hits:
        record_type = "security_action_lead"
    elif threat_hits or preparation_hits:
        record_type = "threat_or_mobilisation_lead"
    elif any(category == "civil_unrest_labour" for category, _ in matched):
        record_type = "protest_or_mobilisation_notice"
    elif any(category == "political_security" for category, _ in matched):
        record_type = "political_security_development"
    elif matched:
        record_type = "general_relevant_development"
    else:
        record_type = "low_relevance"

    all_event_hits = list(dict.fromkeys(physical_hits + unrest_hits + security_hits))
    score = min(10, len(matched) * 2 + min(len(all_event_hits), 3) * 2)
    incident_candidate = bool(matched and all_event_hits)
    return {
        "relevant": bool(matched),
        "score": score,
        "categories": [x[0] for x in matched],
        "reasons": [term for _, hits in matched for term in hits][:8],
        "event_indicators": all_event_hits[:8],
        "physical_event_indicators": physical_hits[:8],
        "unrest_action_indicators": unrest_hits[:8],
        "security_action_indicators": security_hits[:8],
        "threat_indicators": threat_hits[:8],
        "preparation_indicators": preparation_hits[:8],
        "commentary_context_indicators": non_event_context[:6],
        "claim_types": claim_types,
        "non_event_context_indicators": non_event_context[:4],
        "record_type": record_type,
        "incident_candidate": incident_candidate
    }

def district_mentions(text):
    body = " " + str(text or "").lower() + " "
    found = []
    for district in BANGLADESH_DISTRICTS:
        pattern = r"(?<![a-z])" + re.escape(district.lower()) + r"(?![a-z])"
        if re.search(pattern, body):
            found.append(district)
    return found


def source_identity(item):
    platform = str(item.get("platform") or "").strip().lower()
    publisher = str(item.get("publisher_name") or item.get("channel_username") or "unknown").strip().lower()
    return platform + ":" + re.sub(r"\s+", " ", publisher)


def build_repost_clusters(posts, report_post):
    groups = {}
    for item in posts:
        body = str(item.get("text") or "").lower()
        normalized = re.sub(r"\W+", " ", body, flags=re.UNICODE).strip()
        if len(normalized) >= 100:
            groups.setdefault(normalized, []).append(item)
    clusters = []
    for normalized, items in groups.items():
        if len(items) < 2:
            continue
        identities = sorted(set(source_identity(x) for x in items))
        names = sorted(set(str(x.get("publisher_name") or x.get("channel_username") or "unknown") for x in items))
        clusters.append({
            "repost_count": len(items),
            "distinct_source_count": len(identities),
            "source_names": names[:20],
            "source_groups": identities[:20],
            "repetition_type": "cross-source text repetition; independence unassessed" if len(identities) > 1 else "same-source repetition",
            "text_excerpt": normalized[:280],
            "source_records": [report_post(x) for x in sorted(items, key=lambda x: str(x.get("published_at") or ""), reverse=True)[:12]]
        })
    clusters.sort(key=lambda x: (x["distinct_source_count"], x["repost_count"]), reverse=True)
    return clusters[:50]


def build_candidate_groups(posts, report_post):
    """Group exact repeated candidate text; this is not semantic incident deduplication."""
    groups = {}
    for item in posts:
        triage = triage_source_post(item)
        if not triage["incident_candidate"]:
            continue
        body = str(item.get("text") or "").lower()
        normalized = re.sub(r"\W+", " ", body, flags=re.UNICODE).strip()
        if len(normalized) >= 80:
            groups.setdefault(normalized, []).append(item)
    output = []
    for normalized, items in groups.items():
        if len(items) < 2:
            continue
        identities = sorted(set(source_identity(item) for item in items))
        output.append({
            "group_id": "exact-candidate-" + str(len(output) + 1),
            "grouping_basis": "exact normalized text only",
            "source_post_count": len(items),
            "distinct_source_count": len(identities),
            "independence_assessment": "not assessed; repeated text is not corroboration",
            "source_records": [report_post(item) for item in items]
        })
    output.sort(key=lambda group: group["source_post_count"], reverse=True)
    return output[:100]


def read_json_file(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return {}


def build_temporal_comparison(report_date, current_posts, archive_dir, timezone_name="Asia/Dhaka"):
    current_triage = [(item, triage_source_post(item)) for item in current_posts]
    current_relevant = [item for item, triage in current_triage if triage["relevant"]]
    current_candidates = [item for item, triage in current_triage if triage["incident_candidate"]]
    current_bd = [item for item in current_relevant if str(item.get("priority_region") or "").lower() == "bangladesh"]
    collected_stamps = sorted(str(item.get("collected_at") or "").strip() for item in current_posts if str(item.get("collected_at") or "").strip())
    try:
        local_today = datetime.now(ZoneInfo(timezone_name)).date().isoformat()
    except Exception:
        local_today = datetime.now(timezone.utc).date().isoformat()
    current_status = "partial_day" if report_date == local_today else "calendar_day_elapsed_completeness_unverified"
    result = [{
        "date": report_date,
        "collected_posts": len(current_posts),
        "relevant_source_posts": len(current_relevant),
        "incident_candidate_posts": len(current_candidates),
        "bangladesh_relevant_posts": len(current_bd),
        "collection_window_start": collected_stamps[0] if collected_stamps else None,
        "collection_window_end": collected_stamps[-1] if collected_stamps else None,
        "reporting_day_status": current_status,
        "comparison_eligible": False,
        "comparison_status": "partial current day; not directly comparable with a full-day archive" if current_status == "partial_day" else "calendar day elapsed; archive completeness unverified"
    }]
    try:
        base = date.fromisoformat(report_date)
    except ValueError:
        return result
    for offset in range(1, 8):
        prior_day = (base - timedelta(days=offset)).isoformat()
        payload = read_json_file(archive_dir / (prior_day + ".json"))
        prior_posts = payload.get("posts", []) if isinstance(payload, dict) else []
        prior_triage = [(item, triage_source_post(item)) for item in prior_posts]
        relevant = [item for item, triage in prior_triage if triage["relevant"]]
        candidates = [item for item, triage in prior_triage if triage["incident_candidate"]]
        bangladesh = [item for item in relevant if str(item.get("priority_region") or "").lower() == "bangladesh"]
        archive_exists = (archive_dir / (prior_day + ".json")).exists()
        result.append({
            "date": prior_day,
            "collected_posts": len(prior_posts),
            "relevant_source_posts": len(relevant),
            "incident_candidate_posts": len(candidates),
            "bangladesh_relevant_posts": len(bangladesh),
            "reporting_day_status": "archive_completeness_unknown" if archive_exists else "missing_archive",
            "comparison_eligible": False,
            "comparison_status": "archive available; collection completeness unverified" if archive_exists else "no archive available; not a zero-event day"
        })
    return result


def main():
    folders = sorted(p for p in OUTPUT.iterdir() if p.is_dir()) if OUTPUT.exists() else []
    if not folders:
        raise SystemExit("No collection output directory exists; refusing to publish an empty feed.")
    folder = folders[-1]
    telegram_file = folder / "telegram_posts.csv"
    telegram_summary_file = folder / "collection_summary.json"
    if not telegram_file.exists() or not telegram_summary_file.exists():
        raise SystemExit(f"Missing Telegram collection outputs in {folder}")
    telegram_rows = read_csv(telegram_file)
    with telegram_summary_file.open("r", encoding="utf-8") as handle:
        telegram_summary = json.load(handle)
    rss_rows = read_csv(folder / "news_articles.csv")
    rss_summary = {}
    if (folder / "news_collection_summary.json").exists():
        with (folder / "news_collection_summary.json").open("r", encoding="utf-8") as handle:
            rss_summary = json.load(handle)

    posts = []
    for row in telegram_rows:
        item = normalize_row(row, "Telegram")
        if item:
            posts.append(item)
    for row in rss_rows:
        item = normalize_row(row, "RSS/Atom")
        if item:
            posts.append(item)
    unique = {}
    for post in posts:
        unique[post["id"]] = post
    posts = sorted(unique.values(), key=lambda p: p.get("published_at") or "", reverse=True)[:MAX_POSTS]

    diagnostics = telegram_summary.get("channel_diagnostics") or {}
    errors = telegram_summary.get("collection_errors") or []
    channels = telegram_summary.get("configured_channels") or []
    rss_diagnostics = rss_summary.get("source_diagnostics") or {}
    summary = {
        "report_date": telegram_summary.get("report_date"),
        "timezone": telegram_summary.get("timezone", "Asia/Dhaka"),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "collection_methods": [telegram_summary.get("collection_method"), rss_summary.get("collection_method")],
        "configured_telegram_channels": len(channels),
        "configured_channels": len(channels),  # backward-compatible TBC status/coverage field
        "channels_with_diagnostics": len(diagnostics),
        "telegram_channels_with_diagnostics": len(diagnostics),
        "telegram_posts_in_snapshot": sum(1 for p in posts if p["platform"] == "Telegram"),
        "configured_rss_sources": len(rss_summary.get("configured_sources") or []),
        "rss_sources_with_diagnostics": len(rss_diagnostics),
        "rss_articles_in_snapshot": sum(1 for p in posts if p["platform"] == "RSS/Atom"),
        "posts_in_snapshot": len(posts),
        "telegram_collection_errors": len(errors),
        "collection_errors": len(errors),  # backward-compatible TBC status/coverage field
        "rss_source_errors": sum(1 for d in rss_diagnostics.values() if d.get("status") == "error"),
        "channel_diagnostics": diagnostics,
        "rss_source_diagnostics": rss_diagnostics,
        "limitations": (telegram_summary.get("limitations") or []) + (rss_summary.get("limitations") or []),
        "notice": "Public Telegram preview posts and public RSS/Atom headlines/excerpts only. All items are unverified source leads; publication time is not incident time. Repeated coverage is not independent corroboration. This feed excludes analyst notes and incident decisions.",
    }
    payload = {"schema_version": 2, "generated_at": summary["generated_at"], "summary": summary, "posts": posts}
    DEST.parent.mkdir(parents=True, exist_ok=True)
    temporary = DEST.with_suffix(".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    temporary.replace(DEST)

    # Maintain a per-day archive by merging each scheduled collection run.
    # This preserves posts collected earlier in the same day instead of
    # replacing the archive with only the newest two-hour collection window.
    report_date = str(summary.get("report_date") or "")
    timezone_name = str(summary.get("timezone") or "Asia/Dhaka")
    try:
        date.fromisoformat(report_date)
        archive_path = ARCHIVE_DIR / (report_date + ".json")
        archived_posts = {}
        if archive_path.exists():
            try:
                previous = json.loads(archive_path.read_text(encoding="utf-8"))
                for item in previous.get("posts", []):
                    if item.get("id"):
                        archived_posts[item["id"]] = item
            except (OSError, ValueError, TypeError):
                print("Warning: previous daily archive could not be read; rebuilding from current collection.")
        try:
            local_tz = ZoneInfo(timezone_name)
        except Exception:
            local_tz = ZoneInfo("Asia/Dhaka")
        for item in posts:
            stamp = str(item.get("published_at") or "").strip()
            if not stamp:
                continue
            try:
                parsed_stamp = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
                if parsed_stamp.tzinfo is None:
                    parsed_stamp = parsed_stamp.replace(tzinfo=timezone.utc)
                item_day = parsed_stamp.astimezone(local_tz).date().isoformat()
            except (ValueError, TypeError, OverflowError):
                continue
            if item_day == report_date:
                archived_posts[item["id"]] = item
        day_posts = sorted(archived_posts.values(), key=lambda item: item.get("published_at") or "")[-MAX_ARCHIVE_POSTS:]
        archive_summary = dict(summary)
        archive_summary.update({
            "archive_date": report_date,
            "archive_timezone": timezone_name,
            "archive_posts": len(day_posts),
            "archive_notice": "Daily rolling archive merged from scheduled public-source collection runs. Coverage is bounded by public preview/RSS access and collector limits; this is not a complete record of all posts or news."
        })
        archive_payload = {"schema_version": 1, "generated_at": summary["generated_at"], "summary": archive_summary, "posts": day_posts}
        ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
        archive_tmp = archive_path.with_suffix(".tmp")
        archive_tmp.write_text(json.dumps(archive_payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        archive_tmp.replace(archive_path)

        # Publish small page-sized files for chatbots with response-size/time limits.
        # TBC fetches only one page (20 records) instead of downloading the full multi-MB archive.
        page_dir = ARCHIVE_DIR / report_date
        page_dir.mkdir(parents=True, exist_ok=True)
        page_size = 20
        total_pages = max(1, (len(day_posts) + page_size - 1) // page_size)
        for page_number in range(1, total_pages + 1):
            page_posts = day_posts[(page_number - 1) * page_size:page_number * page_size]
            page_summary = dict(archive_summary)
            page_summary.update({
                "page": page_number,
                "total_pages": total_pages,
                "page_size": page_size,
                "page_records": len(page_posts),
                "total_records": len(day_posts)
            })
            page_payload = {
                "schema_version": 1,
                "generated_at": summary["generated_at"],
                "summary": page_summary,
                "posts": page_posts
            }
            page_path = page_dir / ("page-" + str(page_number) + ".json")
            page_tmp = page_path.with_suffix(".tmp")
            page_tmp.write_text(json.dumps(page_payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
            page_tmp.replace(page_path)

        # Build a compact, deterministic daily source-activity summary for TBC.
        # Topic labels are keyword indicators, not verified incident classifications.
        topic_terms = {
            "Politics and governance": ["election", "government", "parliament", "minister", "political", "party", "court", "policy", "cabinet", "vote"],
            "Conflict and security": ["attack", "armed", "military", "soldier", "clash", "explosion", "bomb", "security", "killed", "airstrike", "war"],
            "Protests and labour unrest": ["protest", "demonstration", "strike", "rally", "march", "workers", "student movement", "shutdown", "hartal"],
            "Communal and social violence": ["communal", "religious violence", "mob", "lynching", "riot", "sectarian", "arson", "vandalism"],
            "Public health": ["outbreak", "disease", "health ministry", "hospital", "epidemic", "infection", "cholera", "dengue", "measles", "vaccination"],
            "Disasters and environment": ["flood", "cyclone", "earthquake", "landslide", "fire", "storm", "heatwave", "drought", "pollution"],
            "Economy and essential services": ["inflation", "price", "economy", "fuel", "power", "electricity", "blackout", "bank", "currency", "trade"]
        }
        topic_matches = {label: [] for label in topic_terms}
        region_counts = {}
        source_class_counts = {}
        platform_counts = {"Telegram": 0, "RSS/Atom": 0}
        for item in day_posts:
            body = str(item.get("text") or "").lower()
            platform = str(item.get("platform") or "Unknown")
            region = str(item.get("priority_region") or "global")
            source_class = str(item.get("source_class") or "unknown")
            platform_counts[platform] = platform_counts.get(platform, 0) + 1
            region_counts[region] = region_counts.get(region, 0) + 1
            source_class_counts[source_class] = source_class_counts.get(source_class, 0) + 1
            for label, terms in topic_terms.items():
                if any(term in body for term in terms):
                    topic_matches[label].append(item)
        topic_indicators = []
        for label, matches in topic_matches.items():
            if matches:
                topic_indicators.append({
                    "topic": label,
                    "matching_source_posts": len(matches),
                    "representative_posts": [{
                        "publisher_name": p.get("publisher_name"),
                        "channel_username": p.get("channel_username"),
                        "platform": p.get("platform"),
                        "published_at": p.get("published_at"),
                        "priority_region": p.get("priority_region"),
                        "source_class": p.get("source_class"),
                        "text": str(p.get("text") or "")[:500],
                        "source_url": p.get("source_url")
                    } for p in matches[:3]]
                })
        topic_indicators.sort(key=lambda x: x["matching_source_posts"], reverse=True)
        summary_posts = sorted(day_posts, key=lambda p: (str(p.get("monitoring_weight", "")).lower() == "high", str(p.get("published_at") or "")), reverse=True)[:12]
        daily_summary = {
            "schema_version": 1,
            "generated_at": summary["generated_at"],
            "report_date": report_date,
            "timezone": timezone_name,
            "total_source_posts": len(day_posts),
            "platform_counts": platform_counts,
            "region_counts": region_counts,
            "source_class_counts": source_class_counts,
            "topic_indicators": topic_indicators,
            "representative_posts": [{
                "publisher_name": p.get("publisher_name"),
                "channel_username": p.get("channel_username"),
                "platform": p.get("platform"),
                "published_at": p.get("published_at"),
                "priority_region": p.get("priority_region"),
                "source_class": p.get("source_class"),
                "text": str(p.get("text") or "")[:500],
                "source_url": p.get("source_url")
            } for p in summary_posts],
            "notice": "Automated keyword-based source-activity summary, not an AI-verified event synthesis. Topic matches can be false positives or miss relevant posts. Posts are unverified; repeated posts are not independent corroboration; publication time is not incident time; empty categories do not mean no events occurred."
        }
        summary_path = page_dir / "summary.json"
        summary_tmp = summary_path.with_suffix(".tmp")
        summary_tmp.write_text(json.dumps(daily_summary, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        summary_tmp.replace(summary_path)

        # Build a relevance-filtered, Bangladesh-priority daily OSINT triage report.
        # Rule-based labels are transparent review aids, not incident verification or risk forecasts.
        region_labels = {
            "bangladesh": "Bangladesh", "south asia": "South Asia", "myanmar": "Myanmar",
            "mena": "MENA", "europe": "Europe and Ukraine", "sub-saharan africa": "Sub-Saharan Africa",
            "americas": "Americas", "east/southeast asia": "East and Southeast Asia",
            "global": "Global / unassigned"
        }
        region_posts = {}
        for item in day_posts:
            region_key = str(item.get("priority_region") or "global").strip().lower()
            region_posts.setdefault(region_key, []).append(item)

        def report_post(item):
            triage = triage_source_post(item)
            districts = district_mentions(item.get("text", "")) if str(item.get("priority_region") or "").lower() == "bangladesh" else []
            return {
                "id": item.get("id"),
                "publisher_name": item.get("publisher_name"),
                "channel_username": item.get("channel_username"),
                "platform": item.get("platform"),
                "published_at": item.get("published_at"),
                "priority_region": item.get("priority_region"),
                "source_class": item.get("source_class"),
                "source_affiliation": item.get("source_affiliation"),
                "monitoring_weight": item.get("monitoring_weight"),
                "evidence_status": "UNVERIFIED",
                "publication_datetime": item.get("published_at"),
                "monitoring_region": item.get("priority_region"),
                "event_location_status": "not independently geolocated; place names are text mentions only",
                "record_type": triage["record_type"],
                "claim_types": triage["claim_types"],
                "preparation_indicators": triage["preparation_indicators"],
                "physical_event_indicators": triage["physical_event_indicators"],
                "unrest_action_indicators": triage["unrest_action_indicators"],
                "security_action_indicators": triage["security_action_indicators"],
                "threat_indicators": triage["threat_indicators"],
                "relevance_score": triage["score"],
                "relevance_categories": triage["categories"],
                "relevance_reasons": triage["reasons"],
                "incident_candidate": triage["incident_candidate"],
                "provisional_incident_id": ("PL-" + str(report_date) + "-" + hashlib.sha256(str(item.get("id") or item.get("source_url") or "").encode("utf-8")).hexdigest()[:10].upper()) if triage["incident_candidate"] else None,
                "incident_group_status": "unresolved single-source lead; not a unique verified incident" if triage["incident_candidate"] else None,
                "incident_grouping_basis": "unique source-post identifier; no automatic cross-post incident merge" if triage["incident_candidate"] else None,
                "district_mentions": districts,
                "text": str(item.get("text") or "")[:900],
                "source_url": item.get("source_url")
            }

        triaged_posts = [(item, triage_source_post(item)) for item in day_posts]
        relevant_posts = [item for item, triage in triaged_posts if triage["relevant"]]
        incident_candidates = [item for item, triage in triaged_posts if triage["incident_candidate"]]
        threat_preparation_posts = [item for item, triage in triaged_posts if (triage["threat_indicators"] or triage["preparation_indicators"]) and not triage["incident_candidate"]]
        excluded_posts = len(day_posts) - len(relevant_posts)

        # Select relevant records with Bangladesh first, then regional round-robin coverage.
        relevant_region_posts = {}
        for item in relevant_posts:
            region_key = str(item.get("priority_region") or "global").strip().lower()
            relevant_region_posts.setdefault(region_key, []).append(item)
        for key in relevant_region_posts:
            relevant_region_posts[key].sort(key=lambda p: str(p.get("published_at") or ""), reverse=True)
        region_order = sorted(relevant_region_posts, key=lambda key: (key != "bangladesh", -len(relevant_region_posts[key]), key))
        selected_report_posts = []
        seen_ids = set()
        max_records = 100
        for index in range(100):
            for region_key in region_order:
                candidates = relevant_region_posts.get(region_key, [])
                if index < len(candidates):
                    item = candidates[index]
                    if item.get("id") not in seen_ids and len(selected_report_posts) < max_records:
                        selected_report_posts.append(item)
                        seen_ids.add(item.get("id"))
        if len(selected_report_posts) < max_records:
            for item in sorted(relevant_posts, key=lambda p: str(p.get("published_at") or ""), reverse=True):
                if item.get("id") not in seen_ids:
                    selected_report_posts.append(item)
                    seen_ids.add(item.get("id"))
                if len(selected_report_posts) >= max_records:
                    break

        report_buckets = {}
        for item in relevant_posts:
            triage = triage_source_post(item)
            for category in triage["categories"]:
                report_buckets.setdefault(category, []).append(item)
        bucket_results = []
        category_labels = {
            "armed_conflict_security": "Armed conflict and security",
            "political_security": "Political-security developments",
            "civil_unrest_labour": "Protests, labour and civil unrest",
            "communal_identity": "Communal and identity-related risk",
            "humanitarian_displacement": "Humanitarian and displacement",
            "infrastructure_disruption": "Infrastructure and essential-service disruption",
            "public_health_emergency": "Public-health emergencies",
            "disaster_environment": "Disasters and environment"
        }
        for category, matches in report_buckets.items():
            bucket_results.append({
                "section": category_labels.get(category, category),
                "matching_source_posts": len(matches),
                "source_records": [report_post(p) for p in sorted(matches, key=lambda p: str(p.get("published_at") or ""), reverse=True)[:20]]
            })
        bucket_results.sort(key=lambda x: x["matching_source_posts"], reverse=True)

        region_sections = []
        all_region_order = list(region_labels.keys()) + sorted(set(region_posts) - set(region_labels))
        for region_key in all_region_order:
            records = relevant_region_posts.get(region_key, [])
            region_sections.append({
                "region": region_labels.get(region_key, region_key.replace("_", " ").title()),
                "source_post_count": len(region_posts.get(region_key, [])),
                "relevant_source_post_count": len(records),
                "source_records": [report_post(p) for p in records[:30]]
            })

        bangladesh_posts = relevant_region_posts.get("bangladesh", [])
        bangladesh_all_posts = region_posts.get("bangladesh", [])
        bangladesh_excluded_posts = [item for item in bangladesh_all_posts if not triage_source_post(item)["relevant"]]
        bangladesh_excluded_posts.sort(key=lambda item: str(item.get("collected_at") or item.get("published_at") or ""), reverse=True)
        bangladesh_audit = {
            "total_source_posts": len(bangladesh_all_posts),
            "relevant_source_posts": len(bangladesh_posts),
            "excluded_source_posts": len(bangladesh_excluded_posts),
            "excluded_sample_limit": 30,
            "excluded_sample_count": min(30, len(bangladesh_excluded_posts)),
            "excluded_sample_notice": "Review sample of excluded Bangladesh posts to audit possible false negatives; not a statistically representative sensitivity estimate.",
            "language_review": "Bengali and English phrase triggers enabled for Bangladesh; human review remains mandatory.",
            "sensitivity_estimate": None,
            "excluded_sample_records": [report_post(item) for item in bangladesh_excluded_posts[:30]]
        }
        bangladesh_category_counts = {}
        bangladesh_district_counts = {}
        for item in bangladesh_posts:
            triage = triage_source_post(item)
            for category in triage["categories"]:
                bangladesh_category_counts[category] = bangladesh_category_counts.get(category, 0) + 1
            for district in district_mentions(item.get("text", "")):
                bangladesh_district_counts[district] = bangladesh_district_counts.get(district, 0) + 1

        # Exact normalized text groups are repost indicators, never incident deduplication.
        duplicate_text_clusters = build_repost_clusters(day_posts, report_post)
        candidate_groups = build_candidate_groups(incident_candidates, report_post)
        bangladesh_relevant_count = len(bangladesh_posts)
        temporal_comparison = build_temporal_comparison(report_date, day_posts, ARCHIVE_DIR, timezone_name)

        intelligence_report = {
            "schema_version": 3,
            "report_version": 12,
            "triage_version": 12,
            "report_date": report_date,
            "timezone": timezone_name,
            "generated_at": summary["generated_at"],
            "title": "Legion-OSINT V12 Bangladesh Recall and Claim-Precision Validation Report",
            "classification": "Open-Source Intelligence — unverified source-lead assessment",
            "executive_assessment": {
                "source_posts_in_daily_archive": len(day_posts),
                "relevant_source_posts": len(relevant_posts),
                "excluded_as_low_relevance": excluded_posts,
                "incident_candidate_source_posts": len(incident_candidates),
                "threat_preparation_source_posts": len(threat_preparation_posts),
                "threat_preparation_claim_source_posts": sum(1 for _, triage in triaged_posts if triage["threat_indicators"] or triage["preparation_indicators"]),
                "selected_source_records_displayed": min(100, len(selected_report_posts)),
                "selected_source_records_omitted": max(0, len(relevant_posts) - min(100, len(selected_report_posts))),
                "incident_candidate_records_displayed": min(100, len(incident_candidates)),
                "incident_candidate_records_omitted_from_register": max(0, len(incident_candidates) - 100),
                "incident_candidate_exact_text_groups": len(candidate_groups),
                "bangladesh_total_source_posts": len(region_posts.get("bangladesh", [])),
                "bangladesh_relevant_source_posts": bangladesh_relevant_count,
                "telegram_posts": platform_counts.get("Telegram", 0),
                "rss_articles": platform_counts.get("RSS/Atom", 0),
                "regions_represented": len(region_posts),
                "regions_with_relevant_leads": len(relevant_region_posts),
                "regional_source_post_total_check": sum(len(values) for values in region_posts.values()),
                "regional_counts_reconcile_to_archive": sum(len(values) for values in region_posts.values()) == len(day_posts),
                "source_classes": source_class_counts,
                "exact_duplicate_text_clusters": len(duplicate_text_clusters),
                "cross_source_text_repetition_clusters": sum(1 for x in duplicate_text_clusters if x["distinct_source_count"] > 1),
                "key_caveat": "Relevance filtering is deterministic keyword triage. Counts describe source posts, not unique incidents. No claim is verified, and source repetition does not establish independent corroboration."
            },
            "report_sections": [
                {
                    "heading": "1. Executive assessment and collection picture",
                    "text": "V12 adds Bengali-language Bangladesh review triggers and commentary-context suppression. Keyword matches remain review leads, not verified events; counts are source posts, not incidents.",
                    "metrics": {
                        "collected_posts": len(day_posts),
                        "relevant_source_posts": len(relevant_posts),
                        "excluded_low_relevance_posts": excluded_posts,
                        "incident_candidate_source_posts": len(incident_candidates),
                        "bangladesh_relevant_source_posts": bangladesh_relevant_count
                    }
                },
                {
                    "heading": "2. Bangladesh political-security and communal-risk watch",
                    "text": "Bangladesh leads are prioritised. Political violence, communal targeting, labour unrest, security operations, ordinary crime and public disorder must be distinguished through source review. District names below are text mentions only, not verified geolocation. No motive or affiliation is inferred.",
                    "bangladesh_total_posts": len(region_posts.get("bangladesh", [])),
                    "bangladesh_relevant_posts": len(bangladesh_posts),
                    "category_counts": bangladesh_category_counts,
                    "district_name_mentions": bangladesh_district_counts,
                    "false_negative_audit": bangladesh_audit,
                    "source_records": [report_post(p) for p in bangladesh_posts[:60]]
                },
                {
                    "heading": "3. Regional and international conflict monitoring",
                    "text": "Only relevance-filtered records are shown in regional lead lists. Regional assignment comes from source metadata and is not independent geolocation. Reposts and syndicated reporting are not independent corroboration.",
                    "regions": region_sections,
                    "all_regions_displayed": True,
                    "region_display_note": "All configured monitoring regions are shown, including regions with zero relevant leads."
                },
                {
                    "heading": "4. Communal violence and hate-crime review queue",
                    "text": "These are keyword-triggered review leads only. Establish protected-group targeting, motive, location, incident date and credible evidence before classifying an event as communal violence or a hate crime.",
                    "source_records": [report_post(p) for p in bangladesh_posts if "communal_identity" in triage_source_post(p)["categories"]][:40]
                },
                {
                    "heading": "5. Social-media OSINT and source diversity",
                    "text": "Public Telegram preview posts and unofficial accounts are leads, not verified facts. Prioritise original upload checks, geolocation, chronology, media provenance, publisher identity and independent corroboration. A second publisher repeating a claim is not automatically independent.",
                    "source_records": [report_post(p) for p in selected_report_posts if p.get("platform") == "Telegram"][:60]
                },
                {
                    "heading": "6. Topic and narrative indicators",
                    "text": "Counts are overlapping relevance-category matches. They are not unique events, proof of coordination, or evidence of motive.",
                    "topic_buckets": bucket_results
                },
                {
                    "heading": "7. Incident register — candidate source leads",
                    "text": "Candidates require analyst review and incident-level grouping. Multiple posts may describe one event; one post may contain multiple claims. Candidate total is shown separately from the 100-record display cap. Political statements, generic military commentary and threats are not completed physical incidents unless an explicit event-action phrase is present. The system does not promote these records to verified incidents.",
                    "candidate_records": [report_post(p) for p in sorted(incident_candidates, key=lambda p: (str(p.get("priority_region") or "").lower() != "bangladesh", str(p.get("published_at") or "")), reverse=True)[:100]],
                    "candidate_groups": candidate_groups,
                    "threat_preparation_records": [report_post(p) for p in sorted(threat_preparation_posts, key=lambda p: str(p.get("published_at") or ""), reverse=True)[:100]],
                    "candidate_grouping_notice": "Groups use exact normalized text only. Paraphrased claims are not automatically merged; analyst review is required."
                },
                {
                    "heading": "8. Repost and cross-source repetition analysis",
                    "text": "Exact normalized text clusters identify repeated text only. Cross-source repetition is a corroboration lead, not proof of independent sourcing. Same-source repetition is not corroboration.",
                    "clusters": duplicate_text_clusters
                },
                {
                    "heading": "9. Temporal source-activity comparison",
                    "text": "Daily counts compare collected and relevance-filtered posts in available rolling archives. These are reporting-volume indicators, not violence trends or forecasts. Missing archives are not zero-event days.",
                    "daily_counts": temporal_comparison
                },
                {
                    "heading": "10. Early-warning indicators and overall judgement",
                    "text": "Automated collection cannot assign defensible risk ratings or forecast violence. Analysts should compare verified incidents over time and assess actor capability, intent indicators, target selection, geographic spread, response measures and protective factors.",
                    "watch_indicators": [
                        "New independently corroborated fatalities or mass-casualty claims",
                        "Repeated attacks on transport, health, energy or communications infrastructure",
                        "Threats or mobilisation linked to identifiable targets",
                        "Cross-district spread supported by independently sourced incidents",
                        "Retaliatory mobilisation, communal targeting or displacement",
                        "Arrests, curfews, emergency deployments and restrictions with verified scope"
                    ]
                },
                {
                    "heading": "11. Sources, bias and coverage limitations",
                    "text": "Source class and affiliation are descriptive metadata and may be incomplete. Public Telegram previews and RSS/Atom feeds are bounded; absence of a post is not evidence of no event. Publication time is not incident time. Relevance filtering can miss local-language reports or match unrelated text."
                }
            ],
            "incident_candidate_groups": candidate_groups,
            "incident_candidate_group_count": len(candidate_groups),
            "incident_candidate_grouping_notice": "Exact normalized text groups are repost indicators only. Each candidate receives a stable provisional lead ID; no cross-post merge is made without validated incident-time and event-location evidence.",
            "bangladesh_false_negative_audit": bangladesh_audit,
            "temporal_comparability_notice": "Current partial-day totals are not directly comparable with full-day archives. Historical archive availability does not prove complete collection.",
            "bangladesh_total_source_posts": len(region_posts.get("bangladesh", [])),
            "bangladesh_relevant_source_posts": bangladesh_relevant_count,
            "duplicate_text_clusters": duplicate_text_clusters,
            "duplicate_text_cluster_notice": "Repeated text is not incident deduplication and does not establish independent corroboration.",
            "source_records_selected": len(selected_report_posts),
            "source_records_available": len(day_posts),
            "region_collection_counts": [{"region": region_labels.get(key, key.replace("_", " ").title()), "source_post_count": len(values), "relevant_source_post_count": len(relevant_region_posts.get(key, []))} for key, values in sorted(region_posts.items())],
            "relevant_source_records_available": len(relevant_posts),
            "incident_candidate_records_available": len(incident_candidates),
            "minimum_target_met": len(relevant_posts) >= 50,
            "source_records": [report_post(p) for p in selected_report_posts],
            "temporal_comparison": temporal_comparison,
            "notice": "UNVERIFIED SOURCE LEADS. Precision-first deterministic phrase triage only; not AI-generated or independently verified event synthesis. Generic military/political terms alone do not establish an incident. No inference of guilt, central direction, religious motive or imminent violence. Monitoring-region metadata is not event geolocation; district names are text mentions only. Verify original sources before reporting."
        }
        intelligence_path = page_dir / "intelligence_report.json"
        intelligence_tmp = intelligence_path.with_suffix(".tmp")
        intelligence_tmp.write_text(json.dumps(intelligence_report, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        intelligence_tmp.replace(intelligence_path)
    except ValueError:
        raise SystemExit("Invalid report_date; refusing to publish a daily archive.")

    print(json.dumps({"feed": str(DEST), "posts": len(posts), "daily_archive": str(archive_path), "daily_archive_posts": len(day_posts), "telegram_posts": summary["telegram_posts_in_snapshot"], "rss_articles": summary["rss_articles_in_snapshot"], "telegram_errors": len(errors), "rss_errors": summary["rss_source_errors"], "generated_at": summary["generated_at"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
