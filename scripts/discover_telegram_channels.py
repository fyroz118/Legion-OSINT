#!/usr/bin/env python3
"""Discover candidate public Telegram channels from public web indexes.
No Telegram account, bot token, API credentials, or paid search API is used.
Candidates are unreviewed and are never auto-enabled for intelligence collection.
"""
import csv, json, re, time
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse, parse_qs, unquote, urlencode
from urllib.request import Request, urlopen

OUT = Path("discovery")
UA = "Mozilla/5.0 (compatible; LegionOSINT-Discovery/1.0)"
QUERIES = [
    ("Bangladesh","bn","site:t.me Bangladesh local news journalist district সংবাদ"),
    ("Bangladesh","bn","site:t.me বাংলাদেশ জেলা সংবাদ সাংবাদিক"),
    ("Bangladesh","bn","site:t.me বাংলাদেশ মানবাধিকার পর্যবেক্ষক"),
    ("Bangladesh","en","site:t.me Bangladesh eyewitness monitoring"),
    ("India","hi","site:t.me India regional news पत्रकार"),
    ("India","en","site:t.me India independent journalist local news"),
    ("Pakistan","ur","site:t.me Pakistan local news صحافی"),
    ("Pakistan","en","site:t.me Pakistan independent journalist"),
    ("Afghanistan","fa","site:t.me Afghanistan local news خبرنگار"),
    ("Myanmar","my","site:t.me Myanmar independent news journalist"),
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
]

class AnchorParser(HTMLParser):
    def __init__(self):
        super().__init__(); self.links=[]
    def handle_starttag(self, tag, attrs):
        if tag == "a":
            href = dict(attrs).get("href")
            if href: self.links.append(href)

class MetaParser(HTMLParser):
    def __init__(self):
        super().__init__(); self.meta={}
    def handle_starttag(self, tag, attrs):
        if tag == "meta":
            a=dict(attrs); key=a.get("property") or a.get("name")
            if key and a.get("content"): self.meta[key]=a["content"]

def get(url, timeout=20):
    req=Request(url, headers={"User-Agent":UA})
    with urlopen(req, timeout=timeout) as r:
        return r.read(3_000_000).decode(r.headers.get_content_charset() or "utf-8","replace")

def unwrap(href):
    if href.startswith("//"): href="https:"+href
    p=urlparse(href)
    if "duckduckgo.com" in (p.netloc or ""):
        q=parse_qs(p.query); href=q.get("uddg",[href])[0]
    return unquote(href)

def channel_username(href):
    try:
        p=urlparse(unwrap(href))
        if p.netloc.lower().split(":")[0] not in ("t.me","www.t.me","telegram.me","www.telegram.me"): return None
        bits=[x for x in p.path.split("/") if x]
        if not bits: return None
        if bits[0] == "s": bits=bits[1:]
        if not bits or bits[0] in ("joinchat","addstickers","proxy","iv","share","c","faq","blog"): return None
        name=bits[0].lstrip("@")
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{3,31}",name): return None
        return name
    except Exception: return None

def inspect_preview(username):
    try:
        html=get("https://t.me/s/"+username, timeout=15)
        m=MetaParser(); m.feed(html)
        title=m.meta.get("og:title") or m.meta.get("twitter:title") or ""
        desc=m.meta.get("og:description") or ""
        if not title and "tgme_page" not in html: return {"accessible":False,"title":"","description":""}
        return {"accessible":True,"title":title[:300],"description":desc[:500]}
    except Exception as e:
        return {"accessible":False,"title":"","description":"","error":type(e).__name__}

def main():
    OUT.mkdir(exist_ok=True)
    found={}
    query_errors=[]
    for region,lang,q in QUERIES:
        try:
            url="https://html.duckduckgo.com/html/?"+urlencode({"q":q})
            html=get(url)
            parser=AnchorParser(); parser.feed(html)
            for href in parser.links:
                username=channel_username(href)
                if not username: continue
                key=username.lower()
                row=found.setdefault(key,{"username":username,"candidate_url":"https://t.me/"+username,
                    "discovery_regions":[],"discovery_languages":[],"discovery_queries":[]})
                if region not in row["discovery_regions"]: row["discovery_regions"].append(region)
                if lang not in row["discovery_languages"]: row["discovery_languages"].append(lang)
                if q not in row["discovery_queries"]: row["discovery_queries"].append(q)
        except Exception as e:
            query_errors.append({"query":q,"error":type(e).__name__,"detail":str(e)[:160]})
        time.sleep(1.2)
    # Merge discoveries into a persistent candidate pool; never auto-enable a source.
    registry_path=OUT/"telegram_channel_candidates.json"
    prior={}
    if registry_path.exists():
        try:
            for item in json.loads(registry_path.read_text(encoding="utf-8")).get("candidates",[]):
                prior[item["username"].lower()]=item
        except Exception:
            prior={}
    now=datetime.now(timezone.utc).isoformat()
    for key,row in found.items():
        previous=prior.get(key,{})
        row["first_seen_utc"]=previous.get("first_seen_utc",now)
        row["last_seen_utc"]=now
        for field in ("discovery_regions","discovery_languages","discovery_queries"):
            row[field]=sorted(set(previous.get(field,[])) | set(row.get(field,[])))
        for field in ("title","description","accessible","source_class","source_affiliation","review_status","enabled_for_collection"):
            if field in previous: row[field]=previous[field]
        prior[key]=row
    candidates=sorted(prior.values(),key=lambda x:(-len(x.get("discovery_queries",[])),x["username"].lower()))
    # Recheck up to 250 candidates on each run, including previously discovered sources.
    for row in candidates[:250]:
        meta=inspect_preview(row["username"])
        row.update(meta)
        row["source_class"]=row.get("source_class") or "unknown"
        row["source_affiliation"]=row.get("source_affiliation") or "unassessed"
        row["review_status"]="UNREVIEWED_CANDIDATE"
        row["enabled_for_collection"]=False
        time.sleep(.25)
    for row in candidates[250:]:
        row.setdefault("accessible",None)
        row.setdefault("title","")
        row.setdefault("description","")
        row["source_class"]=row.get("source_class") or "unknown"
        row["source_affiliation"]=row.get("source_affiliation") or "unassessed"
        row["review_status"]="UNREVIEWED_CANDIDATE"
        row["enabled_for_collection"]=False
    stamp=datetime.now(timezone.utc).isoformat()
    payload={"generated_at_utc":stamp,"discovery_method":"DuckDuckGo public HTML index queries for public t.me links",
      "queries_attempted":len(QUERIES),"unique_candidates":len(candidates),
      "previews_checked":min(250,len(candidates)),"query_errors":query_errors,
      "limitations":["Search-engine indexing is incomplete and ranking-biased.",
        "This does not access Telegram global search or private channels.",
        "Candidate discovery does not establish source identity, independence, reliability or current activity.",
        "Only first 250 candidates have public preview checks in this run.",
        "No candidate is automatically enabled in the active monitoring registry."],
      "candidates":candidates}
    (OUT/"telegram_channel_candidates.json").write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding="utf-8")
    fields=["username","candidate_url","title","description","accessible","source_class","source_affiliation",
            "review_status","enabled_for_collection","discovery_regions","discovery_languages","discovery_queries"]
    with (OUT/"telegram_channel_candidates.csv").open("w",newline="",encoding="utf-8-sig") as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction="ignore"); w.writeheader()
        for r in candidates:
            w.writerow({**r,"discovery_regions":";".join(r["discovery_regions"]),
                "discovery_languages":";".join(r["discovery_languages"]),
                "discovery_queries":" | ".join(r["discovery_queries"])})
    (OUT/"discovery_summary.json").write_text(json.dumps({k:v for k,v in payload.items() if k!="candidates"},
        ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({"unique_candidates":len(candidates),"preview_checks":min(250,len(candidates)),
        "query_errors":len(query_errors),"outputs":["telegram_channel_candidates.csv",
        "telegram_channel_candidates.json","discovery_summary.json"]},ensure_ascii=False))

if __name__=="__main__": main()
