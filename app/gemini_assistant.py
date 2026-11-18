import os
from dotenv import load_dotenv
from google import genai
from app.database import search_posts

load_dotenv()
RULES = """Answer only from supplied public-source records. Treat social posts as claims, not verified facts.
Repetition is not independent corroboration. Do not invent dates, locations, identities, casualty counts,
or attribution. State gaps and uncertainty; cite source URLs. Do not provide doxxing, private-person
profiling, targeting, or operational instructions that could facilitate violence. Focus on public events
and aggregate information. If evidence is insufficient, say so."""
def ask(question):
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        return "Gemini is not configured. Add GEMINI_API_KEY to local .env."
    rows = search_posts(limit=40)
    if not rows:
        return "No collected source records are available yet."
    context = "\n\n".join(
        f"Status: {r['evidence_status']} | Region: {r['priority_region']} | "
        f"Published: {r['published_at']} | Source: {r['source_url']}\n{r['text'][:1500]}"
        for r in rows)
    client = genai.Client(api_key=key)
    result = client.models.generate_content(
        model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
        contents=f"{RULES}\n\nRECORDS:\n{context}\n\nQUESTION:\n{question}")
    return result.text or "No answer returned."
