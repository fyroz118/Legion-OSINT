"""Recall-oriented multilingual Muslim-targeted rights-monitoring triage.

This module surfaces public-source leads. It does not determine motive, guilt,
religious identity, legality, or whether an allegation is true.
"""
import re
import unicodedata

HATEWATCH_VERSION = 2

# Target references are deliberately explicit. Rohingya/Palestinian identity alone
# is not treated as proof of Muslim targeting or religious motive.
TARGETS = {
    "en": ["muslim", "muslims", "islamic", "islamophobia", "mosque", "masjid", "rohingya muslim", "muslim community", "muslim family", "muslim women", "muslim students"],
    "bn": ["মুসলিম", "মুসলমান", "ইসলামবিদ্বেষ", "মসজিদ", "রোহিঙ্গা মুসলিম", "মুসলিম সম্প্রদায়", "মুসলমান সম্প্রদায়"],
    "hi": ["मुस्लिम", "मुसलमान", "इस्लामोफोबिया", "मस्जिद", "मुस्लिम समुदाय", "मुसलमान समुदाय"],
    "ur": ["مسلم", "مسلمان", "اسلاموفوبیا", "مسجد", "مسلم کمیونٹی", "مسلمانوں کی آبادی"],
}

ACTIONS = {
    "en": ["attack", "attacked", "assault", "assaulted", "lynch", "lynched", "killed", "murder", "murdered", "shot", "stabbed", "beaten", "beating", "torture", "tortured", "burned", "burnt", "torched", "set on fire", "vandal", "demolish", "demolished", "bulldoz", "evict", "forcibly removed", "abduct", "kidnap", "raped", "sexual violence", "threatened", "threat", "mob violence", "mob attack", "police firing", "displaced"],
    "bn": ["হামলা", "আক্রমণ", "হত্যা", "খুন", "গুলি", "গুলিবিদ্ধ", "পিটিয়ে", "মারধর", "নির্যাতন", "অত্যাচার", "আগুন", "অগ্নিসংযোগ", "ভাঙচুর", "বুলডোজার", "উচ্ছেদ", "জোরপূর্বক", "অপহরণ", "ধর্ষণ", "হুমকি", "আটক", "গ্রেপ্তার", "গ্রেফতার", "বাড়িঘর ভাঙা", "বাস্তুচ্যুত"],
    "hi": ["हमला", "हमले", "हत्या", "मार डाला", "गोली", "पीटा", "मारपीट", "यातना", "प्रताड़ना", "आग लगा", "तोड़फोड़", "बुलडोजर", "उजाड़", "बेदखल", "अपहरण", "बलात्कार", "धमकी", "गिरफ्तार", "हिरासत", "विस्थापित"],
    "ur": ["حملہ", "قتل", "گولی", "مارا پیٹا", "تشدد", "ظلم", "آگ لگا", "توڑ پھوڑ", "بلڈوزر", "بے دخل", "اغوا", "زیادتی", "دھمکی", "گرفتار", "حراست", "بے گھر"],
}

DISCRIMINATION = {
    "en": ["discriminat", "denied", "barred", "ban on", "banned", "excluded", "exclusion", "demolition", "bulldozer", "eviction", "citizenship", "voter list", "employment", "housing", "school", "hijab ban", "religious freedom", "state policy", "government order", "arbitrary detention", "mass arrest", "police violence", "state repression", "collective punishment", "mass expulsion", "crackdown", "police raid"],
    "bn": ["বৈষম্য", "বঞ্চিত", "নিষিদ্ধ", "বের করে", "উচ্ছেদ", "বুলডোজার", "নাগরিকত্ব", "ভোটার তালিকা", "চাকরি", "শিক্ষা", "হিজাব", "সরকারি নির্দেশ", "নীতিমালা", "বিনা বিচারে আটক", "গণগ্রেপ্তার", "পুলিশি নির্যাতন", "রাষ্ট্রীয় দমন", "সমষ্টিগত শাস্তি", "গণউচ্ছেদ"],
    "hi": ["भेदभाव", "वंचित", "प्रतिबंध", "बेदखल", "बुलडोजर", "नागरिकता", "मतदाता सूची", "नौकरी", "शिक्षा", "हिजाब", "सरकारी आदेश", "नीति", "मनमानी हिरासत", "सामूहिक गिरफ्तारी", "पुलिस हिंसा", "राज्य दमन", "सामूहिक सजा", "सामूहिक निष्कासन"],
    "ur": ["امتیاز", "محروم", "پابندی", "بے دخل", "بلڈوزر", "شہریت", "ووٹر فہرست", "ملازمت", "تعلیم", "حجاب", "سرکاری حکم", "پالیسی", "غیر قانونی حراست", "اجتماعی گرفتاریاں", "پولیس تشدد", "ریاستی جبر", "اجتماعی سزا", "اجتماعی بے دخلی"],
}

PROPAGANDA = {
    "en": ["love jihad", "bhagwa love trap", "saffron love trap", "anti-muslim", "anti muslim", "islamophobic", "islamophobia", "boycott muslim", "boycott muslims", "expel muslim", "drive muslims out", "muslims are invaders", "muslims are terrorists", "genocide call", "kill muslim", "hate speech", "dehumaniz", "conspiracy against muslim"],
    "bn": ["লাভ জিহাদ", "ভগবা লাভ ট্র্যাপ", "মুসলিমবিদ্বেষ", "মুসলিম বিরোধী", "মুসলমান বিরোধী", "মুসলিমদের বয়কট", "মুসলমানদের বয়কট", "মুসলিমদের তাড়াও", "মুসলমানদের দেশ থেকে বের", "ঘৃণাত্মক বক্তব্য", "গণহত্যার ডাক", "মুসলিমদের হত্যা"],
    "hi": ["लव जिहाद", "भगवा लव ट्रैप", "मुस्लिम विरोधी", "मुसलमान विरोधी", "मुसलमानों का बहिष्कार", "मुसलमानों को निकालो", "नफरत भरा भाषण", "नरसंहार का आह्वान", "मुसलमानों को मारो"],
    "ur": ["لو جہاد", "بھگوا لو ٹریپ", "مسلم مخالف", "مسلمان مخالف", "مسلمانوں کا بائیکاٹ", "مسلمانوں کو نکالو", "نفرت انگیز تقریر", "نسل کشی کی اپیل", "مسلمانوں کو مارو"],
}

TENSION = {
    "en": ["communal tension", "communal clash", "religious tension", "mosque threatened", "mosque vandal", "anti-muslim rally", "anti-muslim slogan", "threat against muslim", "threat against mosque", "communal violence", "religious procession", "mob gathered", "hate rally"],
    "bn": ["সাম্প্রদায়িক উত্তেজনা", "সাম্প্রদায়িক সংঘর্ষ", "ধর্মীয় উত্তেজনা", "মসজিদে হুমকি", "মসজিদ ভাঙচুর", "মুসলিমবিরোধী সমাবেশ", "মুসলিমবিরোধী স্লোগান", "মুসলিমদের হুমকি", "সাম্প্রদায়িক সহিংসতা", "উত্তেজনা ছড়ায়"],
    "hi": ["सांप्रदायिक तनाव", "सांप्रदायिक झड़प", "धार्मिक तनाव", "मस्जिद को धमकी", "मुस्लिम विरोधी रैली", "मुस्लिम विरोधी नारे", "मुसलमानों को धमकी", "सांप्रदायिक हिंसा"],
    "ur": ["فرقہ وارانہ کشیدگی", "فرقہ وارانہ جھڑپ", "مذہبی کشیدگی", "مسجد کو دھمکی", "مسلم مخالف ریلی", "مسلم مخالف نعرے", "مسلمانوں کو دھمکی", "فرقہ وارانہ تشدد"],
}

CONTEXT = {
    "fact_check": ["fact check", "fact-check", "debunk", "false claim", "misinformation", "ভুয়া দাবি", "গুজব", "तथ्य जांच", "फैक्ट चेक", "جھوٹی خبر", "فیکٹ چیک"],
    "condemnation": ["condemns anti-muslim", "condemn anti-muslim", "rejects islamophobia", "against islamophobia", "বিদ্বেষের নিন্দা", "ঘৃণার প্রতিবাদ", "नफरत की निंदा", "اسلاموفوبیا کی مذمت"],
    "historical": ["in 2017", "in 2002", "years ago", "anniversary of", "২০১৭ সালে", "২০০২ সালে", "वर्षों पहले", "سنہ 2017"],
}

def norm(value):
    value = unicodedata.normalize("NFKC", str(value or "")).casefold()
    return re.sub(r"\s+", " ", value).strip()

def find_terms(body, groups):
    found = []
    if isinstance(groups, dict):
        iterable = groups.items()
    else:
        iterable = [("und", groups)]
    for language, terms in iterable:
        for term in terms:
            needle = norm(term)
            if needle and needle in body:
                found.append({"language": language, "term": term})
    return found

def has_any(body, groups):
    return bool(find_terms(body, groups))

def classify_post(post):
    body = norm(" ".join(str(post.get(k) or "") for k in ("text", "article_title", "article_summary")))
    targets = find_terms(body, TARGETS)
    action_hits = find_terms(body, ACTIONS)
    discrimination_hits = find_terms(body, DISCRIMINATION)
    propaganda_hits = find_terms(body, PROPAGANDA)
    tension_hits = find_terms(body, TENSION)
    context = {name: find_terms(body, terms) for name, terms in CONTEXT.items()}
    context = {name: hits for name, hits in context.items() if hits}

    # Incident/action and target can be expressed in any order. A target-only
    # mention is not an incident; an action-only mention is not Muslim-targeted.
    categories = []
    if targets and action_hits:
        categories.append("hate_crime_incident")
    if targets and discrimination_hits:
        categories.append("discrimination")
    if propaganda_hits:
        categories.append("anti_muslim_propaganda")
    if targets and tension_hits:
        categories.append("communal_tension")

    # Historical and fact-check context are surfaced, never silently discarded.
    # Propaganda references in reporting/debunking are marked for context review.
    propaganda_context_review = bool(propaganda_hits and (context.get("fact_check") or context.get("condemnation")))
    if not categories and targets and context.get("historical"):
        status = "historical_reference_review"
    elif categories and (propaganda_context_review or context.get("fact_check") or context.get("condemnation")):
        status = "context_review_required"
    elif categories:
        status = "unverified_review_lead"
    else:
        status = "not_flagged_by_rules"

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
        "classification_status": status,
        "evidence_status": "UNVERIFIED",
        "review_note": "Automated lexical lead only. Verify who is targeted, what occurred, event date and location, original evidence, source provenance and independent corroboration. Do not infer religious identity, motive, perpetrator or coordination.",
    }

def build_hatewatch(posts, report_post):
    categories = ["hate_crime_incident", "discrimination", "anti_muslim_propaganda", "communal_tension"]
    records = {category: [] for category in categories}
    for post in posts:
        result = classify_post(post)
        if not result["relevant"]:
            continue
        record = report_post(post)
        record["hatewatch"] = result
        for category in result["categories"]:
            records[category].append(record)
    unique = {}
    for group in records.values():
        for record in group:
            unique[record.get("id") or record.get("source_url")] = record
    return {
        "hatewatch_version": HATEWATCH_VERSION,
        "title": "Muslim-targeted hate, discrimination and communal-risk monitoring",
        "scope": "South Asia priority; expanded public RSS search feeds plus configured public Telegram previews. Coverage remains bounded and non-exhaustive.",
        "counts": {category: len(records[category]) for category in categories},
        "unique_flagged_source_posts": len(unique),
        "total_category_matches": sum(len(records[category]) for category in categories),
        "source_posts_screened": len(posts),
        "categories": [{"category": category, "source_post_count": len(records[category]), "records": records[category][:150]} for category in categories],
        "notice": "Unverified source-post leads, not verified hate crimes or proof of religious motive. Categories overlap. Historical, fact-checking and condemnation contexts require analyst review. A zero count does not mean zero incidents; configured source coverage is incomplete.",
    }
