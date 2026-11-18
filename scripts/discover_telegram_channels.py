#!/usr/bin/env python3
"""Discover candidate public Telegram channels from several public web indexes.

No Telegram account, bot token, Telegram API credentials, Gemini key or paid API
is required. Discovery is not verification; candidates are never auto-enabled.
"""
import csv
import html
import json
import re
import time
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse, parse_qs, unquote, urlencode
from urllib.request import Request, urlopen

OUT = Path("discovery")
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36"
MAX_PREVIEW_CHECKS = 250
QUERIES = [
    ("Bangladesh","bn","site:t.me/s/ বাংলাদেশ জেলা সংবাদ সাংবাদিক"),
    ("Bangladesh","bn","site:t.me বাংলাদেশ স্থানীয় সংবাদ জেলা প্রতিনিধি"),
    ("Bangladesh","bn","site:t.me বাংলাদেশ মানবাধিকার পর্যবেক্ষক"),
    ("Bangladesh","bn","site:t.me বাংলাদেশ প্রত্যক্ষদর্শী সংবাদ"),
    ("Bangladesh","en","site:t.me Bangladesh local journalist district news"),
    ("Bangladesh","en","site:t.me Bangladesh eyewitness monitor civil society"),
    ("India","hi","site:t.me India regional news पत्रकार जिला"),
    ("India","en","site:t.me India independent journalist local news"),
    ("Pakistan","ur","site:t.me Pakistan local news صحافی شہر"),
    ("Pakistan","en","site:t.me Pakistan independent journalist monitor"),
    ("Afghanistan","fa","site:t.me Afghanistan local news خبرنگار"),
    ("Myanmar","my","site:t.me Myanmar independent news journalist"),
    ("Myanmar","en","site:t.me Myanmar local eyewitness monitoring"),
    ("Sri Lanka","si","site:t.me Sri Lanka local news journalist"),
    ("Nepal","ne","site:t.me Nepal local news journalist"),
    ("Middle East","ar","site:t.me فلسطين صحفي محلي أخبار"),
    ("Middle East","ar","site:t.me سوريا مراسل أخبار محلية"),
    ("Middle East","ar","site:t.me السودان صحفي أخبار"),
    ("Middle East","ar","site:t.me اليمن صحفي أخبار"),
    ("Middle East","en","site:t.me Lebanon local journalist monitor"),
    ("Ukraine/Russia","uk","site:t.me Україна місцеві новини журналіст"),
    ("Ukraine/Russia","ru","site:t.me независимый журналист новости регионы"),
    ("Europe","en","site:t.me local journalist protest monitor Europe"),
    ("Africa","am","site:t.me Ethiopia local news journalist"),
    ("Africa","ar","site:t.me السودان دارفور أخبار مراسل"),
    ("Africa","en","site:t.me Sudan local monitor journalist"),
    ("Africa","fr","site:t.me Sahel journaliste actualités locales"),
    ("Africa","en","site:t.me DRC local news journalist"),
    ("East/Southeast Asia","my","site:t.me Myanmar local eyewitness news"),
    ("East/Southeast Asia","id","site:t.me Indonesia local news journalist"),
    ("East/Southeast Asia","th","site:t.me Thailand local news journalist"),
    ("Americas","es","site:t.me Venezuela periodista noticias locales"),
    ("Americas","es","site:t.me Haiti journaliste actualités locales"),
    ("Global","en","site:t.me OSINT independent conflict monitor journalist"),
    ("Global","en","site:t.me local eyewitness conflict monitoring"),
    ("Global","en","site:t.me civil society conflict monitor"),
    ("Bangladesh","bn","site:t.me গাজীপুর নারায়ণগঞ্জ পোশাক শ্রমিক স্থানীয় সংবাদ"),
    ("Bangladesh","bn","site:t.me চট্টগ্রাম কক্সবাজার পার্বত্য চট্টগ্রাম সংবাদ প্রতিনিধি"),
    ("Bangladesh","bn","site:t.me বরিশাল খুলনা রাজশাহী সিলেট জেলা সংবাদ"),
    ("Bangladesh","bn","site:t.me রংপুর ময়মনসিংহ জেলা সাংবাদিক সংবাদ"),
    ("Bangladesh","bn","site:t.me বাংলাদেশ মানবাধিকার পর্যবেক্ষক শ্রমিক অধিকার"),
    ("Bangladesh","en","site:t.me Bangladesh district correspondent local eyewitness reporter"),
    ("Bangladesh","en","site:t.me Bangladesh labour rights monitor civil society"),
    ("Myanmar","my","site:t.me ရခိုင် ဒေသခံ သတင်း သတင်းထောက်"),
    ("Myanmar","my","site:t.me ကချင် ရှမ်း ကရင် ဒေသခံ သတင်း"),
    ("Myanmar","my","site:t.me စစ်ကိုင်း မကွေး ဒေသခံ သတင်း သတင်းထောက်"),
    ("Myanmar","en","site:t.me Rakhine Kachin Karen Shan local independent reporter"),
    ("Myanmar","en","site:t.me Myanmar civil society human rights field monitor"),
    ("India","bn","site:t.me Assam Tripura West Bengal local news reporter"),
    ("India","hi","site:t.me मणिपुर असम स्थानीय पत्रकार समाचार"),
    ("Pakistan","ur","site:t.me بلوچستان خیبر پختونخوا مقامی صحافی خبر"),
    ("South Asia","en","site:t.me South Asia local eyewitness independent monitor"),
    ("Middle East","ar","site:t.me غزة صحفي محلي مراسل ميداني أخبار"),
    ("Middle East","ar","site:t.me الضفة الغربية القدس مراسل محلي أخبار"),
    ("Middle East","ar","site:t.me السودان دارفور كردفان مراسل محلي"),
    ("Middle East","ar","site:t.me لبنان سوريا اليمن صحفي مستقل أخبار محلية"),
    ("Africa","am","site:t.me አማራ ትግራይ ኦሮሚያ የአካባቢ ዜና"),
    ("Africa","fr","site:t.me RDC Kivu journaliste local société civile"),
    ("Ukraine/Russia","uk","site:t.me Харків Херсон Запоріжжя місцевий журналіст"),
    ("Ukraine/Russia","ru","site:t.me независимый местный корреспондент Украина Россия"),
    ("Global","en","site:t.me independent local newsroom eyewitness public monitor conflict"),
]

class AnchorParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
    def handle_starttag(self, tag, attrs):
        if tag == "a":
            values = dict(attrs)
            href = values.get("href")
            if href:
                self.links.append(href)

class MetaParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.meta = {}
    def handle_starttag(self, tag, attrs):
        if tag == "meta":
            values = dict(attrs)
            key = values.get("property") or values.get("name")
            if key and values.get("content"):
                self.meta[key] = values["content"]

def get(url, timeout=20):
    request = Request(url, headers={"User-Agent": UA, "Accept-Language": "en-US,en;q=0.9"})
    with urlopen(request, timeout=timeout) as response:
        body = response.read(3_000_000)
        return body.decode(response.headers.get_content_charset() or "utf-8", "replace")

def unwrap(href):
    href = html.unescape(href)
    if href.startswith("//"):
        href = "https:" + href
    parsed = urlparse(href)
    host = (parsed.netloc or "").lower().split(":")[0]
    if host.endswith("duckduckgo.com"):
        href = parse_qs(parsed.query).get("uddg", [href])[0]
    elif host.endswith("google.com") and parsed.path == "/url":
        href = parse_qs(parsed.query).get("q", [href])[0]
    elif host.endswith("bing.com") and parsed.path == "/ck/a":
        href = parse_qs(parsed.query).get("u", [href])[0]
        if href.startswith("a1"):
            import base64
            try:
                href = base64.urlsafe_b64decode(href[2:] + "==").decode("utf-8", "ignore")
            except Exception:
                pass
    return unquote(href)

def channel_username(href):
    try:
        parsed = urlparse(unwrap(href))
        host = (parsed.netloc or "").lower().split(":")[0]
        if host not in ("t.me", "www.t.me", "telegram.me", "www.telegram.me"):
            return None
        bits = [part for part in parsed.path.split("/") if part]
        if bits and bits[0] == "s":
            bits = bits[1:]
        if not bits or bits[0] in ("joinchat","addstickers","proxy","iv","share","c","faq","blog"):
            return None
        name = bits[0].lstrip("@")
        return name if re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{3,31}", name) else None
    except Exception:
        return None

def extract_candidates(page_html):
    parser = AnchorParser()
    parser.feed(page_html)
    found = set()
    for href in parser.links:
        username = channel_username(href)
        if username:
            found.add(username)
    return found

def search_url(provider, query):
    if provider == "duckduckgo":
        return "https://html.duckduckgo.com/html/?" + urlencode({"q": query})
    if provider == "bing":
        return "https://www.bing.com/search?" + urlencode({"q": query, "count": "30"})
    if provider == "google":
        return "https://www.google.com/search?" + urlencode({"q": query, "num": "30"})
    raise ValueError(provider)

def search_page(provider, query):
    page = get(search_url(provider, query), timeout=25)
    lowered = page.lower()
    blocked_markers = {
        "duckduckgo": ("anomaly-modal", "bots use duckduckgo", "select all squares"),
        "bing": ("verify you are human", "captcha", "unusual traffic"),
        "google": ("our systems have detected unusual traffic", "/sorry/"),
    }
    if any(marker in lowered for marker in blocked_markers[provider]):
        raise RuntimeError(provider + "_blocked_or_challenged")
    links = extract_candidates(page)
    # An empty result is not automatically an HTTP error, but it must be visible.
    return links, len(page), ("no_telegram_links" if not links else "ok")

def inspect_preview(username):
    try:
        page = get("https://t.me/s/" + username, timeout=15)
        meta = MetaParser()
        meta.feed(page)
        title = meta.meta.get("og:title") or meta.meta.get("twitter:title") or ""
        description = meta.meta.get("og:description") or ""
        accessible = bool(title or "tgme_page" in page)
        return {"accessible": accessible, "title": title[:300], "description": description[:500]}
    except Exception as exc:
        return {"accessible": False, "title": "", "description": "", "preview_error": type(exc).__name__}

def self_test():
    cases = {
        "https://t.me/example_channel": "example_channel",
        "https://t.me/s/example_channel/123": "example_channel",
        "https://duckduckgo.com/l/?uddg=https%3A%2F%2Ft.me%2Fexample_channel": "example_channel",
        "https://example.com/not-telegram": None,
        "https://t.me/joinchat/abcdef": None,
    }
    for url, expected in cases.items():
        actual = channel_username(url)
        assert actual == expected, (url, actual, expected)
    assert extract_candidates('<a href="https://t.me/example_channel">x</a>') == {"example_channel"}
    print("Discovery parser self-tests passed.")

def main():
    OUT.mkdir(exist_ok=True)
    found = {}
    seed_path = OUT / "seed_candidates.json"
    seed_candidates = []
    if seed_path.exists():
        try:
            seed_candidates = json.loads(seed_path.read_text(encoding="utf-8")).get("candidates", [])
        except Exception:
            seed_candidates = []
    for seed in seed_candidates:
        username = str(seed.get("username", "")).strip().lstrip("@")
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{3,31}", username):
            continue
        key = username.lower()
        row = found.setdefault(key, {
            "username": username,
            "candidate_url": "https://t.me/" + username,
            "discovery_regions": [],
            "discovery_languages": [],
            "discovery_queries": [],
            "discovery_providers": [],
        })
        for field, value in (("discovery_regions", seed.get("region", "Bangladesh")),
                             ("discovery_languages", seed.get("language", "bn")),
                             ("discovery_queries", "TG Market public Bangladesh news directory"),
                             ("discovery_providers", "tgmarket_public_directory")):
            if value and value not in row[field]:
                row[field].append(value)
        row["discovery_notes"] = seed.get("discovery_notes", "Directory listing only; identity, role and reliability unverified.")
        row["seed_source_url"] = seed.get("seed_source_url", "https://tgmarket.io/countries/bd/news")
    provider_stats = {name: {"queries_attempted": 0, "queries_with_links": 0,
                             "links_found": 0, "errors": []}
                      for name in ("duckduckgo", "bing", "google")}
    for region, language, query in QUERIES:
        for provider in ("duckduckgo", "bing", "google"):
            stats = provider_stats[provider]
            stats["queries_attempted"] += 1
            try:
                usernames, page_bytes, status = search_page(provider, query)
                if usernames:
                    stats["queries_with_links"] += 1
                    stats["links_found"] += len(usernames)
                for username in usernames:
                    key = username.lower()
                    row = found.setdefault(key, {
                        "username": username,
                        "candidate_url": "https://t.me/" + username,
                        "discovery_regions": [],
                        "discovery_languages": [],
                        "discovery_queries": [],
                        "discovery_providers": [],
                    })
                    for field, value in (("discovery_regions", region),
                                         ("discovery_languages", language),
                                         ("discovery_queries", query),
                                         ("discovery_providers", provider)):
                        if value not in row[field]:
                            row[field].append(value)
                if status == "no_telegram_links":
                    stats.setdefault("empty_query_count", 0)
                    stats["empty_query_count"] += 1
            except Exception as exc:
                stats["errors"].append({"query": query, "error": type(exc).__name__,
                                        "detail": str(exc)[:180]})
            time.sleep(0.45)

    registry_path = OUT / "telegram_channel_candidates.json"
    prior = {}
    if registry_path.exists():
        try:
            old = json.loads(registry_path.read_text(encoding="utf-8"))
            for item in old.get("candidates", []):
                prior[item["username"].lower()] = item
        except Exception:
            prior = {}

    now = datetime.now(timezone.utc).isoformat()
    for key, row in found.items():
        previous = prior.get(key, {})
        row["first_seen_utc"] = previous.get("first_seen_utc", now)
        row["last_seen_utc"] = now
        for field in ("discovery_regions", "discovery_languages", "discovery_queries", "discovery_providers"):
            row[field] = sorted(set(previous.get(field, [])) | set(row.get(field, [])))
        for field in ("title", "description", "accessible", "source_class", "source_affiliation", "discovery_notes", "seed_source_url"):
            if field in previous:
                row[field] = previous[field]
        prior[key] = row

    candidates = sorted(prior.values(), key=lambda item: (
        -len(item.get("discovery_queries", [])), item["username"].lower()))
    for row in candidates[:MAX_PREVIEW_CHECKS]:
        row.update(inspect_preview(row["username"]))
        row["source_class"] = row.get("source_class") or "unknown"
        row["source_affiliation"] = row.get("source_affiliation") or "unassessed"
        row["review_status"] = "UNREVIEWED_CANDIDATE"
        row["enabled_for_collection"] = False
        time.sleep(0.2)
    for row in candidates[MAX_PREVIEW_CHECKS:]:
        row.setdefault("accessible", None)
        row.setdefault("title", "")
        row.setdefault("description", "")
        row["source_class"] = row.get("source_class") or "unknown"
        row["source_affiliation"] = row.get("source_affiliation") or "unassessed"
        row["review_status"] = "UNREVIEWED_CANDIDATE"
        row["enabled_for_collection"] = False

    providers_with_success = sum(1 for stats in provider_stats.values()
                                 if stats["queries_with_links"] > 0)
    total_query_errors = sum(len(stats["errors"]) for stats in provider_stats.values())
    stamp = datetime.now(timezone.utc).isoformat()
    limitations = [
        "Public search-engine indexes are incomplete, ranking-biased and may block automated requests.",
        "This does not access Telegram global search or private channels.",
        "Discovery does not establish source identity, independence, reliability or current activity.",
        "Only the first 250 candidates receive public preview checks per run.",
        "No candidate is automatically enabled in the active monitoring registry.",
    ]
    payload = {
        "generated_at_utc": stamp,
        "discovery_method": "Parallel public web-index search (DuckDuckGo, Bing, Google) for public t.me links",
        "queries_attempted_per_provider": len(QUERIES),
        "provider_diagnostics": provider_stats,
        "providers_returning_telegram_links": providers_with_success,
        "total_query_errors": total_query_errors,
        "new_candidates_this_run": len(found),
        "directory_seed_candidates_loaded": len(seed_candidates),
        "unique_candidates": len(candidates),
        "previews_checked_this_run": min(MAX_PREVIEW_CHECKS, len(candidates)),
        "limitations": limitations,
        "candidates": candidates,
    }
    (OUT / "telegram_channel_candidates.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    fields = ["username", "candidate_url", "title", "description", "accessible",
              "source_class", "source_affiliation", "review_status", "enabled_for_collection",
              "discovery_regions", "discovery_languages", "discovery_queries", "discovery_providers"]
    with (OUT / "telegram_channel_candidates.csv").open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in candidates:
            writer.writerow({**row,
                "discovery_regions": ";".join(row.get("discovery_regions", [])),
                "discovery_languages": ";".join(row.get("discovery_languages", [])),
                "discovery_queries": " | ".join(row.get("discovery_queries", [])),
                "discovery_providers": ";".join(row.get("discovery_providers", []))})
    summary = {key: value for key, value in payload.items() if key != "candidates"}
    (OUT / "discovery_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "new_candidates": len(found),
        "cumulative_candidates": len(candidates),
        "preview_checks": min(MAX_PREVIEW_CHECKS, len(candidates)),
        "providers_returning_links": providers_with_success,
        "query_errors": total_query_errors,
        "provider_diagnostics": provider_stats,
    }, ensure_ascii=False))
    # Fail loudly if all providers return zero links and no existing registry exists.
    if providers_with_success == 0 and not candidates:
        raise RuntimeError("No Telegram candidates found: all providers returned zero links. Inspect provider diagnostics; registry not considered successful.")

if __name__ == "__main__":
    self_test()
    main()
