# Bulk Telegram channel intake

## What to send
Upload a plain-text file named `telegram_channel_candidates.txt` in this ChatGPT conversation. Put one public Telegram channel link per line.

Accepted:
- `https://t.me/channelusername`
- `https://t.me/s/channelusername`
- `@channelusername`

Also accepted: a CSV with columns `url`, `region`, `language`, `why_relevant` (optional).

Do not include private invite links, phone numbers, personal accounts, login codes, session strings, API credentials or private-group links.

## How to collect links in Telegram
1. Open Telegram and search for a topic, location or language, for example: Bangladesh district news, local journalists, independent monitors, labour rights, minority/community reporting, Myanmar local news, Sudan monitors, Palestine local journalists, Sahel security reporting.
2. Open a public channel and check that its profile has a public `t.me/...` link.
3. Use **Share → Copy Link** and paste the link into one running note in **Saved Messages** or a text file.
4. Repeat. Add the channel's region/language beside the link if you know it; otherwise leave it blank.
5. Export/copy the note as plain text, or upload the TXT/CSV directly here.

You do not need to add me to channels, create a bot, share your Telegram account, or provide any credentials.

## What happens after you send it
- Normalize and deduplicate usernames.
- Check public-page availability, recent activity, language and regional relevance.
- Label ownership/affiliation as unknown unless supported by evidence.
- Prioritise unofficial local journalists, eyewitness/community reporting, independent monitors, civil-society groups and specialist researchers.
- Keep official sources as a parallel comparison layer.
- Put unreviewed candidates in a staging queue; do not automatically activate them or treat them as reliable.
- Exclude private-person targeting, doxxing, incitement, and channels focused on actionable real-time targeting or tactical movements.
- Enable only candidates that pass the review gate.

## Recommended collection target
Aim for 1,200–1,500 candidate links so that inactive, duplicate, private, irrelevant or low-quality channels can be filtered and still leave a large active network. This is a candidate pool, not a promise that 1,000 channels will all be usable or monitored on every run.

Suggested balance:
- 60–70% unofficial/local/independent sources
- 20–30% independent media, civil society and specialist research
- 10–15% official and intergovernmental sources

Prioritise Bangladesh districts and upazilas, then South Asia, MENA, Sub-Saharan Africa, Europe/Ukraine, East/Southeast Asia and the Americas. Seek local-language channels, not just English aggregators.
