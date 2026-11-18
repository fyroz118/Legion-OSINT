"""Safe preflight checks for Legion-OSINT. Does not print secret values."""
import importlib.util
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

REQUIRED = {
    "telegram": "telegram",
    "telethon": "telethon",
    "google-genai": "google.genai",
    "python-dotenv": "dotenv",
}

def module_available(module):
    try:
        return importlib.util.find_spec(module) is not None
    except (ImportError, ModuleNotFoundError, ValueError):
        return False

def main():
    print("\n=== LEGION-OSINT SETUP CHECK ===")
    print(f"Python: {sys.version.split()[0]}")
    missing = []
    for package, module in REQUIRED.items():
        ok = module_available(module)
        print(f"[{'OK' if ok else 'MISSING'}] {package}")
        if not ok:
            missing.append(package)

    required_env = [
        "TELEGRAM_API_ID", "TELEGRAM_API_HASH",
        "TELEGRAM_BOT_TOKEN", "TELEGRAM_ALLOWED_USER_IDS",
        "GEMINI_API_KEY",
    ]
    absent = []
    for key in required_env:
        present = bool(os.getenv(key, "").strip())
        print(f"[{'SET' if present else 'NEEDS CONFIG'}] {key}")
        if not present:
            absent.append(key)

    allowed = os.getenv("TELEGRAM_ALLOWED_USER_IDS", "")
    if allowed and "1569000384" not in {x.strip() for x in allowed.split(",")}:
        print("[WARNING] The configured allowlist does not include your Telegram user ID.")

    channel_file = ROOT / "config" / "channels.json"
    print(f"[{'OK' if channel_file.exists() else 'MISSING'}] config/channels.json")

    print("\nResult:")
    if missing:
        print("Install missing packages using ANDROID_SETUP.md.")
    if absent:
        print("Complete the private .env configuration. Never send secrets in chat or commit .env.")
    if not missing and not absent:
        print("Basic local configuration looks complete. This is not a live connection test.")
        print("Next: run the collector once, then start the bot.")
    print("\nNo API key, hash, or bot token has been displayed.")

if __name__ == "__main__":
    main()
