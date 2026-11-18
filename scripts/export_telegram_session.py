"""Create a Telethon StringSession for a private GitHub Actions secret.

Run locally in a trusted terminal. The printed session string is a credential:
never paste it into chat, commit it, or save it in a public file.
"""
import os
from telethon.sync import TelegramClient
from telethon.sessions import StringSession

def main():
    api_id = os.getenv("TELEGRAM_API_ID") or input("Telegram API ID: ").strip()
    api_hash = os.getenv("TELEGRAM_API_HASH") or input("Telegram API hash: ").strip()
    if not api_id or not api_hash:
        raise SystemExit("Both Telegram API ID and API hash are required.")
    with TelegramClient(StringSession(), int(api_id), api_hash) as client:
        print("\nTELETHON_SESSION_STRING (store only as a private GitHub Actions secret):\n")
        print(client.session.save())
        print("\nTreat this string like your Telegram account password. Revoke it if exposed.")

if __name__ == "__main__":
    main()
