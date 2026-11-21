"""Multilingual Muslim-targeted hate/discrimination triage. Phrase matches are review leads only."""
import re
import unicodedata

HATEWATCH_VERSION = 1
RULES = {
 "hate_crime_incident": {
  "en":["attack on muslims","muslims attacked","mosque attacked","mosque vandalised","mosque vandalized","mosque set on fire","muslim homes attacked","anti-muslim violence","lynching of muslim"],
  "bn":["মুসলিমদের ওপর হামলা","মুসলমানদের ওপর হামলা","মসজিদে হামলা","মসজিদে আগুন","মসজিদ ভাঙচুর","মুসলিম বাড়িতে হামলা","মুসলমানদের হত্যা","ধর্মীয় কারণে হামলা"],
  "hi":["मुसलमानों पर हमला","मुस्लिमों पर हमला","मस्जिद पर हमला","मस्जिद में आग","मुस्लिम घरों पर हमला","मुसलमान की हत्या"],
  "ur":["مسلمانوں پر حملہ","مسجد پر حملہ","مسجد میں آگ","مسلمانوں کے گھروں پر حملہ","مسلمان کو قتل"]},
 "discrimination":{
  "en":["discrimination against muslims","muslims denied housing","muslims denied employment","anti-muslim discrimination","muslim students barred"],
  "bn":["মুসলিমদের প্রতি বৈষম্য","মুসলমানদের প্রতি বৈষম্য","মুসলিম শিক্ষার্থীদের নিষিদ্ধ","মুসলিমদের চাকরি থেকে বঞ্চিত"],
  "hi":["मुसलमानों के खिलाफ भेदभाव","मुस्लिम छात्रों पर प्रतिबंध"],
  "ur":["مسلمانوں کے خلاف امتیاز","مسلم طلبہ پر پابندی"]},
 "anti_muslim_propaganda":{
  "en":["anti-muslim hate","islamophobic propaganda","muslims are invaders","expel all muslims","boycott muslim businesses","kill muslims","muslims are terrorists","calls to drive muslims out"],
  "bn":["মুসলিম বিদ্বেষ","মুসলমান বিদ্বেষ","ইসলামবিদ্বেষ","মুসলিমদের বিতাড়িত","মুসলমানদের বয়কট","মুসলিমরা সন্ত্রাসী"],
  "hi":["मुस्लिम विरोधी नफरत","इस्लामोफोबिया","मुसलमानों को देश से निकालो","मुस्लिमों का बहिष्कार"],
  "ur":["مسلم مخالف نفرت","اسلاموفوبیا","مسلمانوں کو ملک سے نکالو","مسلمانوں کا بائیکاٹ"]},
 "communal_tension":{
  "en":["anti-muslim rally","anti-muslim slogan","threats against muslim community","threat against mosque","hate speech against muslims"],
  "bn":["মুসলিমবিরোধী স্লোগান","মুসলিমবিরোধী সমাবেশ","মুসলিম সম্প্রদায়ের বিরুদ্ধে হুমকি","মসজিদে হামলার হুমকি","মুসলিমদের বিরুদ্ধে উসকানি"],
  "hi":["मुस्लिम विरोधी नारे","मुसलमानों के खिलाफ धमकी","मस्जिद पर हमले की धमकी"],
  "ur":["مسلم مخالف نعرے","مسلمانوں کے خلاف دھمکی","مسجد پر حملے کی دھمکی"]}}
EXCLUSIONS=["fact check","fact-check","debunk","false claim","misinformation","condemns anti-muslim","against islamophobia","rejects islamophobia","হামলার প্রতিবাদ","বিদ্বেষের নিন্দা","गुमराह करने वाला दावा","فیکٹ چیک"]

def norm(value):
 return re.sub(r"\s+"," ",unicodedata.normalize("NFKC",str(value or "")).casefold()).strip()

def hits(text, phrases):
 found=[]
 for phrase in phrases:
  p=norm(phrase)
  pattern=r"(?<!\w)"+r"\s+".join(re.escape(x) for x in p.split())+r"(?!\w)"
  if re.search(pattern,text): found.append(phrase)
 return found

def classify_post(post):
 text=norm(post.get("text")); matched={}
 for category,langs in RULES.items():
  found=[]
  for phrases in langs.values(): found.extend(hits(text,phrases))
  if found: matched[category]=list(dict.fromkeys(found))[:8]
 context=hits(text,EXCLUSIONS)
 if context: matched.pop("anti_muslim_propaganda",None)
 cats=list(matched)
 return {"relevant":bool(cats),"categories":cats,"matched_phrases":matched,"context_indicators":context[:5],
  "classification_status":"context_review_required" if context and cats else ("unverified_review_lead" if cats else "not_flagged_by_starter_rules"),
  "evidence_status":"UNVERIFIED","review_note":"Phrase match only. Verify context, target, location, incident date and original evidence; do not infer identity or motive."}

def build_hatewatch(posts, report_post):
 cats=list(RULES); records={c:[] for c in cats}
 for post in posts:
  result=classify_post(post)
  if result["relevant"]:
   record=report_post(post); record["hatewatch"]=result
   for category in result["categories"]: records[category].append(record)
 return {"hatewatch_version":HATEWATCH_VERSION,"title":"Muslim-targeted hate, discrimination and communal-risk monitoring",
  "scope":"South Asia priority; only configured public Telegram previews and RSS/Atom sources.",
  "counts":{c:len(records[c]) for c in cats},"unique_flagged_source_posts":len({x.get("id") for group in records.values() for x in group}),
  "total_category_matches":sum(len(v) for v in records.values()),
  "categories":[{"category":c,"source_post_count":len(records[c]),"records":records[c][:100]} for c in cats],
  "notice":"Unverified source-post leads, not verified hate crimes or proof of motive. Categories overlap. Criticism of religion or debunking hate is not automatically propaganda. Coverage is bounded; zero matches do not mean zero incidents."}
