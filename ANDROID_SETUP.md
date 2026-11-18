# Legion-OSINT: Android setup (beginner guide)

This guide is for running the first local prototype on Android. It is not a 24/7 hosting solution.

## What you need
- Android device with a stable internet connection.
- Pydroid 3 installed from Google Play.
- Your Telegram API ID and API hash.
- Your Telegram bot token from @BotFather.
- Your Gemini API key.
- Your numeric Telegram user ID.

**Never paste credentials into ChatGPT, GitHub, screenshots, or public messages.** Put them only in a private local `.env` file. If a key was exposed, assume it may be misused and rotate it when practical.

## A. Install Pydroid 3
Install [Pydroid 3 from Google Play](https://play.google.com/store/apps/details?id=ru.iiec.pydroid3). Open it once and allow its first-time setup to finish.

## B. Get the project files
1. Open the [Legion-OSINT GitHub repository](https://github.com/fyroz118/Legion-OSINT).
2. Download the ZIP using **Code → Download ZIP**.
3. Extract it with your Android file manager into a folder named `Legion-OSINT`.
4. In Pydroid 3, open the file browser and open `app/setup_check.py` from that extracted folder.

## C. Install Python packages
Open Pydroid's terminal and run:

```bash
pip install -r /storage/emulated/0/Download/Legion-OSINT/requirements.txt
```

The exact path depends on where you extracted the folder. If it differs, use the file manager to locate the folder. Do not guess the path.

Some Android devices/Pydroid builds may fail to install a dependency. If that happens, stop and record the exact error; do not repeatedly install random packages.

## D. Create the private environment file
Inside the project folder, create a text file named `.env` (not `.env.txt`) beside `requirements.txt`. Copy the template from `.env.example` and fill it locally:

- `TELEGRAM_API_ID`: your Telegram API ID
- `TELEGRAM_API_HASH`: your Telegram API hash
- `TELEGRAM_BOT_TOKEN`: token from @BotFather
- `TELEGRAM_ALLOWED_USER_IDS=1569000384`
- `GEMINI_API_KEY`: your Gemini key
- Leave the other defaults unchanged initially.

Do not upload `.env`. The repository's `.gitignore` excludes it.

## E. Run the preflight check
In Pydroid, open and run `app/setup_check.py`. It checks package presence and whether required environment variables are set. It never prints secret values.

## F. First test
Do not start collection until `config/channels.json` contains a small, reviewed allowlist of accessible public channels. Never scrape private groups or bypass access controls.

After configuration:
1. Run `python -m app.collector` once.
2. If it completes, run `python -m app.bot`.
3. Open your Telegram bot and send `/start`, then `/status`.

The collector may require an interactive Telegram login on first use. Keep the resulting Telethon session file private; never upload it.

## Android limitations
Android may suspend background apps, terminate long-running processes, or restrict network activity. Pydroid is for initial testing only. For reliable daily collection, move the validated project to an always-on Linux host later.

## Troubleshooting rule
If anything fails, share the error text with API keys, phone numbers, session strings, and tokens removed. Never share your `.env` or Telethon session file.
