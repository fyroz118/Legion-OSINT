"""Hatewatch v3: conservative multilingual triage for Muslim-targeted rights leads.

This is a source-post screening aid, not an automated hate-crime adjudicator.
It never infers a person's religion, motive, perpetrator identity, legality,
or whether an allegation is true.
"""
import re
import unicodedata
from collections import Counter

HATEWATCH_VERSION = 3

# Explicit community/target references only. "Islamic" is intentionally absent:
# it often describes organisations (e.g. IRGC or Islamic State), not Muslim victims.
TARGETS = {
    "en": ["muslim", "muslims", "muslim family", "muslim families",
           "muslim community", "muslim communities", "muslim residents",
           "muslim students", "muslim worshippers", "mosque", "masjid",
           "rohingya muslim", "rohingya muslims"],
    "bn": ["মুসলিম", "মুসলমান", "মুসলিম পরিবার", "মুসলমান পরিবার",
           "মুসলিম সম্প্রদায়", "মুসলমান সম্প্রদায়", "মুসলিম শিক্ষার্থী",
           "মসজিদ", "রোহিঙ্গা মুসলিম"],
    "hi": ["मुस्लिम", "मुसलमान", "मुस्लिम परिवार", "मुसलमान परिवार",
           "मुस्लिम समुदाय", "मस्जिद", "रोहिंग्या मुस्लिम"],
    "ur": ["مسلم", "مسلمان", "مسلم خاندان", "مسلمان خاندان",
           "مسلم برادری", "مسجد", "روہنگیا مسلمان"],
}

ACTIONS = {
    "en": ["attacked", "attack on", "assaulted", "assault", "lynched", "lynching",
           "killed", "murdered", "shot dead", "stabbed", "beaten", "beating",
           "tortured", "torture", "burned", "burnt", "torched", "set on fire",
           "vandalised", "vandalized", "demolished", "demolition", "bulldozed",
           "bulldozer", "evicted", "eviction", "forcibly removed", "abducted",
           "kidnapped", "raped", "sexual violence", "threatened", "threat",
           "displaced", "arson", "mob violence", "police firing"],
    "bn": ["হামলা", "আক্রমণ", "হত্যা", "খুন", "গুলি", "গুলিবিদ্ধ", "পিটিয়ে",
           "মারধর", "নির্যাতন", "অত্যাচার", "অগ্নিসংযোগ", "আগুন", "ভাঙচুর",
           "বুলডোজার", "গুঁড়িয়ে", "গুঁড়িয়ে", "উচ্ছেদ", "জোরপূর্বক",
           "অপহরণ", "ধর্ষণ", "হুমকি", "আটক", "গ্রেপ্তার", "গ্রেফতার",
           "বাড়িঘর ভাঙা", "বাস্তুচ্যুত"],
    "hi": ["हमला", "हमले", "हत्या", "मार डाला", "गोली", "पीटा", "मारपीट",
           "यातना", "प्रताड़ना", "आग लगा", "तोड़फोड़", "बुलडोजर", "उजाड़",
           "बेदखल", "अपहरण", "बलात्कार", "धमकी", "गिरफ्तार", "हिरासत",
           "विस्थापित"],
    "ur": ["حملہ", "قتل", "گولی", "مارا پیٹا", "تشدد", "ظلم", "آگ لگا",
           "توڑ پھوڑ", "بلڈوزر", "بے دخل", "اغوا", "زیادتی", "دھمکی",
           "گرفتار", "حراست", "بے گھر"],
}

DISCRIMINATION = {
    "en": ["discriminated", "discrimination", "denied", "barred", "banned",
           "excluded", "exclusion", "demolished", "demolition", "bulldozer",
           "eviction", "citizenship", "voter list", "employment", "housing",
           "school ban", "hijab ban", "religious freedom", "government order",
           "arbitrary detention", "mass arrest", "police violence",
           "state repression", "collective punishment", "mass expulsion",
           "crackdown", "police raid"],
    "bn": ["বৈষম্য", "বঞ্চিত", "নিষিদ্ধ", "উচ্ছেদ", "বুলডোজার", "নাগরিকত্ব",
           "ভোটার তালিকা", "চাকরি", "শিক্ষা", "হিজাব", "সরকারি নির্দেশ",
           "বিনা বিচারে আটক", "গণগ্রেপ্তার", "পুলিশি নির্যাতন", "রাষ্ট্রীয় দমন",
           "সমষ্টিগত শাস্তি", "গণউচ্ছেদ"],
    "hi": ["भेदभाव", "वंचित", "प्रतिबंध", "बेदखल", "बुलडोजर", "नागरिकता",
           "मतदाता सूची", "नौकरी", "शिक्षा", "हिजाब", "सरकारी आदेश",
           "मनमानी हिरासत", "सामूहिक गिरफ्तारी", "पुलिस हिंसा", "राज्य दमन"],
    "ur": ["امتیاز", "محروم", "پابندی", "بے دخل", "بلڈوزر", "شہریت",
           "ووٹر فہرست", "ملازمت", "تعلیم", "حجاب", "سرکاری حکم",
           "غیر قانونی حراست", "اجتماعی گرفتاریاں", "پولیس تشدد", "ریاستی جبر"],
}

PROPAGANDA = {
    "en": ["love jihad", "bhagwa love trap", "saffron love trap",
           "anti-muslim", "anti muslim", "islamophobic", "islamophobia",
           "boycott muslim", "boycott muslims", "expel muslim", "drive muslims out",
           "muslims are invaders", "muslims are terrorists", "genocide call",
           "kill muslim", "hate speech", "dehumaniz", "conspiracy against muslim"],
    "bn": ["লাভ জিহাদ", "ভগবা লাভ ট্র্যাপ", "মুসলিমবিদ্বেষ", "মুসলিম বিরোধী",
           "মুসলমান বিরোধী", "মুসলিমদের বয়কট", "মুসলমানদের বয়কট",
           "মুসলিমদের তাড়াও", "ঘৃণাত্মক বক্তব্য", "গণহত্যার ডাক"],
    "hi": ["लव जिहाद", "भगवा लव ट्रैप", "मुस्लिम विरोधी", "मुसलमान विरोधी",
           "मुसलमानों का बहिष्कार", "मुसलमानों को निकालो", "नफरत भरा भाषण"],
    "ur": ["لو جہاد", "بھگوا لو ٹریپ", "مسلم مخالف", "مسلمان مخالف",
           "مسلمانوں کا بائیکاٹ", "مسلمانوں کو نکالو", "نفرت انگیز تقریر"],
}

TENSION = {
    "en": ["communal tension", "communal clash", "religious tension",
           "mosque threatened", "mosque vandal", "anti-muslim rally",
           "anti-muslim slogan", "threat against muslim", "threat against mosque",
           "communal violence", "hate rally"],
    "bn": ["সাম্প্রদায়িক উত্তেজনা", "সাম্প্রদায়িক সংঘর্ষ", "ধর্মীয় উত্তেজনা",
           "মসজিদে হুমকি", "মসজিদ ভাঙচুর", "মুসলিমবিরোধী সমাবেশ",
           "মুসলিমবিরোধী স্লোগান", "মুসলিমদের হুমকি", "সাম্প্রদায়িক সহিংসতা"],
    "hi": ["सांप्रदायिक तनाव", "सांप्रदायिक झड़प", "धार्मिक तनाव",
           "मस्जिद को धमकी", "मुस्लिम विरोधी रैली", "मुसलमानों को धमकी"],
    "ur": ["فرقہ وارانہ کشیدگی", "فرقہ وارانہ جھڑپ", "مذہبی کشیدگی",
           "مسجد کو دھمکی", "مسلم مخالف ریلی", "مسلمانوں کو دھمکی"],
}

CONTEXT = {
    "fact_check": ["fact check", "fact-check", "debunk", "false claim",
                   "misinformation", "ভুয়া দাবি", "গুজব", "तथ्य जांच",
                   "फैक्ट चेक", "جھوٹی خبر", "فیکٹ چیک"],
    "condemnation": ["condemns anti-muslim", "condemn anti-muslim",
                     "rejects islamophobia", "against islamophobia",
                     "বিদ্বেষের নিন্দা", "ঘৃণার প্রতিবাদ", "नफरत की निंदा",
                     "اسلاموفوبیا کی مذمت"],
    "historical": ["in 2017", "in 2002", "years ago", "historical",
                   "anniversary", "survivors recount", "survivor testimony",
                   "testimony from", "court ruled", "icj ruling", "genocide convention",
                   "২০১৭ সালে", "২০০২ সালে", "বছর আগে", "ঐতিহাসিক",
                   "वर्षों पहले", "سنہ 2017"],
    "retrospective": ["what happened in", "looking back", "remembers",
                      "commemorates", "documentary", "archive footage",
                      "past violence", "historical account"],
}

# Mentions of these entities are not, by themselves, evidence that Muslims
# are the target. Explicit Muslim-community targets can still be reviewed.
ORGANISATION_CONTEXT = [
    "islamic revolutionary guard", "islamic revolutionary guard corps",
    "islamic state", "islamic state west africa", "islamic state - west africa",
    "islamic republic", "irgc", "iswap", "boko haram",
]

def norm(value):
    value = unicodedata.normalize("NFKC", str(value or "")).casefold()
    return re.sub(r"\s+", " ", value).strip()

def find_terms(body, groups):
    found = []
    iterable = groups.items() if isinstance(groups, dict) else [("und", groups)]
    for language, terms in iterable:
        for term in terms:
            needle = norm(term)
            if needle and needle in body:
                found.append({"language": language, "term": term})
    return found

def _event_time_status(body, context):
    if context.get("historical") or context.get("retrospective"):
        return "historical_or_retrospective"
    return "current_or_unspecified"

def _exact_fingerprint(post, body):
    # Exact-text/title duplicate grouping only. Similarity is not proof of same event.
    title = norm(post.get("article_title") or "")
    material = title if title else body
    return re.sub(r"[^\w]+", " ", material, flags=re.UNICODE).strip()

def classify_post(post):
    body = norm(" ".join(str(post.get(k) or "") for k in
                         ("text", "article_title", "article_summary")))
    targets = find_terms(body, TARGETS)
    action_hits = find_terms(body, ACTIONS)
    discrimination_hits = find_terms(body, DISCRIMINATION)
    propaganda_hits = find_terms(body, PROPAGANDA)
    tension_hits = find_terms(body, TENSION)
    context = {name: find_terms(body, terms) for name, terms in CONTEXT.items()}
    context = {name: hits for name, hits in context.items() if hits}
    organisation_hits = [term for term in ORGANISATION_CONTEXT if term in body]

    # No generic "Islamic" target token. Organisation-only violence is not
    # classified as anti-Muslim violence without an explicit community target.
    categories = []
    if targets and action_hits:
        categories.append("hate_crime_incident")
    if targets and discrimination_hits:
        categories.append("discrimination")
    if propaganda_hits:
        categories.append("anti_muslim_propaganda")
    if targets and tension_hits:
        categories.append("communal_tension")

    event_time_status = _event_time_status(body, context)
    context_review = bool(context.get("fact_check") or context.get("condemnation"))
    if event_time_status == "historical_or_retrospective":
        classification_status = "historical_reference_review" if categories else "historical_context_only"
    elif context_review and categories:
        classification_status = "context_review_required"
    elif categories:
        classification_status = "unverified_review_lead"
    else:
        classification_status = "not_flagged_by_rules"

    if not targets and organisation_hits:
        exclusion_reason = "organisation_or_state_reference_without_explicit_muslim_community_target"
    elif not categories and not targets:
        exclusion_reason = "no_explicit_target_and_action_or_narrative_combination"
    elif not categories:
        exclusion_reason = "target_mention_without_action_discrimination_or_narrative"
    else:
        exclusion_reason = None

    return {
        "relevant": bool(categories),
        "categories": categories,
        "matched": {
            "target_terms": targets[:12],
            "action_terms": action_hits[:12],
            "discrimination_terms": discrimination_hits[:12],
            "propaganda_terms": propaganda_hits[:12],
            "tension_terms": tension_hits[:12],
        },
        "context_indicators": context,
        "organisation_context_indicators": organisation_hits,
        "event_time_status": event_time_status,
        "classification_status": classification_status,
        "evidence_status": "UNVERIFIED",
        "exclusion_reason": exclusion_reason,
        "review_note": "Automated lexical lead only. Verify target, conduct, event date and location, source provenance, reported motive and independent corroboration. Do not infer religion, motive, perpetrator, legality or coordination.",
    }

def build_hatewatch(posts, report_post):
    categories = ["hate_crime_incident", "discrimination",
                  "anti_muslim_propaganda", "communal_tension"]
    records = {category: [] for category in categories}
    historical_records = []
    context_records = []
    excluded = Counter()
    exact_groups = {}
    screened = 0

    for post in posts:
        screened += 1
        result = classify_post(post)
        record = report_post(post)
        if result["relevant"]:
            record["hatewatch"] = result
            record["incident_group_status"] = "unresolved; source-post lead is not a unique incident"
            fingerprint = _exact_fingerprint(post, norm(post.get("text") or ""))
            record["exact_duplicate_group"] = fingerprint[:180] if fingerprint else None
            if fingerprint:
                exact_groups.setdefault(fingerprint, []).append(record.get("id") or record.get("source_url"))
            for category in result["categories"]:
                records[category].append(record)
            if result["event_time_status"] == "historical_or_retrospective":
                historical_records.append(record)
            if result["classification_status"] == "context_review_required":
                context_records.append(record)
        else:
            excluded[result["exclusion_reason"] or "not_flagged"] += 1

    # Group identical text/title only. Similar but non-identical posts remain
    # separate unresolved leads for analyst review.
    exact_duplicate_groups = [
        {"fingerprint": key[:180], "source_post_ids": ids, "source_post_count": len(ids)}
        for key, ids in exact_groups.items() if len(ids) > 1
    ]
    unique_source_ids = set()
    for group in records.values():
        for record in group:
            unique_source_ids.add(record.get("id") or record.get("source_url"))

    return {
        "hatewatch_version": HATEWATCH_VERSION,
        "title": "Muslim-targeted hate, discrimination and communal-risk monitoring",
        "scope": "South Asia priority with bounded global discovery; public Telegram previews and configured public RSS/Atom feeds only.",
        "counts": {category: len(records[category]) for category in categories},
        "unique_flagged_source_posts": len(unique_source_ids),
        "total_category_matches": sum(len(records[category]) for category in categories),
        "source_posts_screened": screened,
        "historical_reference_source_posts": len({r.get("id") or r.get("source_url") for r in historical_records}),
        "context_review_source_posts": len({r.get("id") or r.get("source_url") for r in context_records}),
        "exact_duplicate_groups": exact_duplicate_groups,
        "excluded_reason_counts": dict(excluded),
        "unique_incident_count": None,
        "unique_incident_count_note": "Not automatically estimated. Source-post matching cannot establish event identity; analyst grouping requires event date, location, target and event details.",
        "categories": [{"category": category,
                        "source_post_count": len(records[category]),
                        "records": records[category][:150]} for category in categories],
        "review_queues": {
            "historical_reference_review": historical_records[:150],
            "context_review_required": context_records[:150],
        },
        "notice": "Counts describe source posts and overlapping category matches, not verified crimes or unique incidents. Historical references and fact-check/condemnation contexts are separated for review. Zero matches do not mean zero incidents; coverage is bounded and non-exhaustive.",
    }
