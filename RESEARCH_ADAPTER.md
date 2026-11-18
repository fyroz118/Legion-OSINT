# Public-web research adapter

Legion-OSINT uses the Tavily Search API as its first configurable public-web discovery provider.

## What this layer does
- Builds a reporting-date query plan, with Bangladesh searches first.
- Searches news-indexed public web sources for the supplied date.
- Stores result title, URL, domain, provider publication date, snippet, query and region in SQLite.
- Records successful and failed queries so source coverage can be audited.
- Deduplicates repeated URLs for a reporting date.

## What it does not do
- It does not search every website or every post on X, Facebook, YouTube or Telegram.
- Public social posts are returned only when indexed and surfaced by the provider; direct platform API adapters are separate work.
- Search date filters use provider publication dates; known timestamps are normalized to Asia/Dhaka for the reporting-day check. A publication date still does not prove the incident happened on that date. Undated results are retained but their date remains unknown.
- Search ranking is not verification. Search results are leads, not incidents or facts.
- It does not automatically upgrade evidence status, assign confidence or produce a verified report.

## Configuration
Set these private environment variables on the deployment host:
- TAVILY_API_KEY — required.
- TAVILY_SEARCH_DEPTH — basic by default; advanced may use more credits.
- RESEARCH_MAX_QUERIES — defaults to 12, maximum 20.

Do not commit .env or share API keys in chat. The code uses the official Tavily API endpoint https://api.tavily.com/search with bearer authentication and date filters. It does not request generated answers or raw page content.

## Commands
- /research YYYY-MM-DD — run the configured date-specific discovery plan.
- /leads YYYY-MM-DD — list stored candidate links for analyst review.
- /coverage YYYY-MM-DD — show which regional queries succeeded or failed.

A research run is not a daily intelligence report. Review candidate links, establish incident dates, group duplicates, attach independent sources, and enter reviewed events into the incident ledger before generating /report YYYY-MM-DD.
