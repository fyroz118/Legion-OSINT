"""Discover public Telegram channels from public search-index RSS.
No Telegram login, private groups, or authenticated scraping are used.
"""
import html
import json
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UA = "Legion-OSINT-public-source-discovery/1.0"
QUERIES = [
    '"site:t.me/s" Bangladesh news Telegram',
    '"site:t.me/s" Bangladesh journalist OR news OR monitor',
    '"site:t.me/s" India regional news Telegram',
    '"site:t.me/s" India political party OR civil society Telegram',
    '"site:t.me/s" Myanmar news OR ethnic OR conflict',
    '"site:t.me/s" South Asia OSINT conflict',
    '"site:t.me/s" Middle East conflict news OSINT',
    '"site:t.me/s" Africa regional news monitor',
    '"site:t.me/s" Ukraine Europe OSINT news',
]
URL_RE = re.compile(r'https?://(?:t\.me|telegram\.me)/(?:s/)?([A-Za-z][A-Za-z0-9_]{3,31})', re.I)
NEWS_WORDS = ("news", "media", "journal", "press", "tv", "radio", "report", "agency", "broadcast")
ACTOR_WORDS = ("party", "bjp", "congress", "awami", "bnp", "jamaat", "student", "youth", "activist", "movement")
REGION_HINTS = {
    "bangladesh": ("Bangladesh", "bn"), "india": ("India", "en"),
    "myanmar": ("Myanmar", "my"), "burma": ("Myanmar", "my"),
    "ukraine": ("Ukraine", "uk"), "middle east": ("MENA", "ar"),
    "africa": ("Africa", "en"), "south asia": ("South Asia", "en"),
}

class Links(HTMLParser):
    def __init__(self):
        super().__init__(); self.hrefs=[]
    def handle_starttag(self, tag, attrs):
        if tag == "a":
            d=dict(attrs)
            if d.get("href"): self.hrefs.append(d["href"])

def fetch(url, timeout=18):
    req=urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")

def search():
    found={}
    for query in QUERIES:
        url="https://news.google.com/rss/search?q="+urllib.parse.quote(query)+"&hl=en&gl=US&ceid=US:en"
        try:
            root=ET.fromstring(fetch(url))
            for item in root.findall(".//item"):
                blob=" ".join([(item.findtext("title") or ""), (item.findtext("description") or ""), (item.findtext("link") or "")])
                parser=Links(); parser.feed(blob)
                urls=[item.findtext("link") or ""] + parser.hrefs
                for raw in urls:
                    for m in URL_RE.finditer(html.unescape(raw)):
                        username=m.group(1)
                        found.setdefault(username.lower(), {"username":username,"discovery_query":query,"search_result":item.findtext("link") or ""})
        except Exception as exc:
            print("search query failed:", query, str(exc)[:180], flush=True)
    return list(found.values())

def inspect(candidate):
    username=candidate["username"]
    page=fetch("https://t.me/s/"+username)
    low=page.lower()
    title=re.search(r'<meta property="og:title" content="([^"]*)"',page,re.I)
    desc=re.search(r'<meta property="og:description" content="([^"]*)"',page,re.I)
    text=html.unescape((title.group(1) if title else "")+" "+(desc.group(1) if desc else ""))
    parser=Links(); parser.feed(page)
    external=[u for u in parser.hrefs if u.startswith("http") and "t.me/" not in u and "telegram.me/" not in u]
    verified=("verified" in low and ("tgme_page_extra" in low or "tgme_channel_info" in low))
    actor=any(w in (username+" "+text).lower() for w in ACTOR_WORDS)
    newsroom=any(w in (username+" "+text).lower() for w in NEWS_WORDS)
    crosslink=bool(external)
    if actor:
        category="political_or_community_actor"
        source_class="political_actor"
    elif newsroom:
        category="news_or_media_channel"
        source_class="independent_media"
    else:
        category="unknown_or_specialist_channel"
        source_class="unknown"
    # Full-autonomy policy: every accessible public channel preview is activated.
    # Classification records uncertainty; it does not block collection.
    auto=True
    region="Global"; language="und"
    hay=(candidate.get("discovery_query","")+" "+username+" "+text).lower()
    for hint, values in REGION_HINTS.items():
        if hint in hay: region,language=values; break
    return {
        "username":username, "region":region, "language":language,
        "candidate_category":category, "source_class":source_class,
        "source_affiliation":"unverified_public_channel_identity",
        "source_identity_status":"Telegram public preview inspected; external affiliation not fully established",
        "discovery_notes":("Public preview title/description: "+text[:500]+"; external links: "+", ".join(external[:3]))[:900],
        "seed_source_url":"https://t.me/s/"+username,
        "discovery_query":candidate.get("discovery_query",""),
        "search_result_url":candidate.get("search_result",""),
        "verified_marker_observed":verified, "external_link_observed":crosslink,
        "review_status":"AUTO_ACTIVATED" if auto else "UNREVIEWED_CANDIDATE",
        "enabled_for_collection":auto,
        "discovered_at":datetime.now(timezone.utc).isoformat()
    }, auto

def main():
    active_path=ROOT/"config/channels.json"
    seed_path=ROOT/"discovery/seed_candidates.json"
    active=json.loads(active_path.read_text(encoding="utf-8"))
    seed=json.loads(seed_path.read_text(encoding="utf-8"))
    active_map={x["username"].lower():x for x in active.get("channels",[]) if x.get("username")}
    seed_map={x["username"].lower():x for x in seed.get("candidates",[]) if x.get("username")}
    discoveries=[]; activated=[]; errors=[]
    for item in search():
        key=item["username"].lower()
        if key in active_map or key in seed_map: continue
        try:
            record, auto=inspect(item)
            if auto:
                channel={
                    "username":record["username"], "priority":record["region"].lower().replace(" ","_"),
                    "language":record["language"], "source_type":record["candidate_category"],
                    "source_affiliation":record["source_affiliation"],
                    "default_evidence_status":"UNVERIFIED", "enabled":True,
                    "notes":record["discovery_notes"]+" Automatically activated because the public Telegram preview was accessible. Source identity/editorial independence may be uncertain; classify accordingly and treat posts as UNVERIFIED.",
                    "source_class":record["source_class"], "monitoring_weight":"standard",
                    "discovery_source_url":record["seed_source_url"], "discovered_at":record["discovered_at"]
                }
                active["channels"].append(channel); active_map[key]=channel
                record["enabled_for_collection"]=True
                activated.append(record["username"])
            else:
                seed["candidates"].append(record); seed_map[key]=record
            discoveries.append(record)
        except Exception as exc:
            errors.append({"username":item["username"],"error":str(exc)[:240]})
    seed["candidates"]=seed.get("candidates",[])
    now=datetime.now(timezone.utc).isoformat()
    report={
        "generated_at":now,"method":"Google News public RSS search results + unauthenticated Telegram public preview checks",
        "queries_run":len(QUERIES),"new_channels_found":len(discoveries),
        "auto_activated":activated,"review_required":[],"activation_policy":"FULL_AUTOMATIC_PUBLIC_CHANNEL_ACTIVATION",
        "errors":errors,"limitations":["Not Telegram global search; search-index coverage is incomplete.",
        "Only public channel previews are inspected; no private groups or Telegram login.",
        "All accessible public Telegram channels are activated automatically, including political, community and unknown sources; classifications are descriptive, not endorsements.",
        "All collected posts remain UNVERIFIED until incident-level corroboration."],
        "discoveries":discoveries
    }
    active_path.write_text(json.dumps(active,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    seed_path.write_text(json.dumps(seed,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    (ROOT/"discovery/latest.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:report[k] for k in ("generated_at","new_channels_found","auto_activated","review_required","errors","activation_policy")},ensure_ascii=False),flush=True)

if __name__=="__main__": main()
