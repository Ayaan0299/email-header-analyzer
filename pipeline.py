import os
import requests
from dotenv import load_dotenv

from analyzer import analyse
from database import init_db, insert_result, is_seen, mark_seen
from alerts import send_alert

load_dotenv()

BASE = "https://mailtrap.io/api"


def _headers():
    token = os.getenv("MAILTRAP_API_TOKEN")
    if not token:
        raise RuntimeError("MAILTRAP_API_TOKEN not set in .env")
    return {"Authorization": f"Bearer {token}"}


def _get_messages(account_id, inbox_id):
    r = requests.get(f"{BASE}/accounts/{account_id}/inboxes/{inbox_id}/messages", headers=_headers(), timeout=15)
    r.raise_for_status()
    return r.json()


def _get_raw_email(account_id, inbox_id, message_id):
    r = requests.get(f"{BASE}/accounts/{account_id}/inboxes/{inbox_id}/messages/{message_id}/body.raw", headers=_headers(), timeout=15)
    r.raise_for_status()
    return r.text


def _extract_raw_header(raw_email: str) -> str:
    blank = raw_email.find("\r\n\r\n")
    if blank == -1:
        blank = raw_email.find("\n\n")
    return raw_email[:blank] if blank != -1 else raw_email


def poll():
    account_id = os.getenv("MAILTRAP_ACCOUNT_ID", "2712769")
    inbox_id   = os.getenv("MAILTRAP_INBOX_ID")
    if not inbox_id:
        print("[pipeline] MAILTRAP_INBOX_ID not set in .env")
        return

    print(f"[pipeline] Polling inbox {inbox_id}...")
    try:
        messages = _get_messages(account_id, inbox_id)
        if not messages:
            print("[pipeline] No new messages")
            return

        new = [m for m in messages if not is_seen(str(m["id"]))]
        print(f"[pipeline] {len(new)} new message(s)")

        for msg in new:
            msg_id = str(msg["id"])
            try:
                raw        = _get_raw_email(account_id, inbox_id, msg_id)
                raw_header = _extract_raw_header(raw)
                result     = analyse(raw_header)

                parsed  = result["parsed"]
                checks  = result["checks"]
                score   = result["score"]
                verdict = result["verdict"]

                insert_result(parsed, checks, score, verdict)
                mark_seen(msg_id)

                sender = parsed.get("from_email") or msg.get("from_email", "unknown")
                print(f"[pipeline] {sender} | score={score} | {verdict}")

                if score >= 55:
                    send_alert(parsed, score, verdict)

            except Exception as e:
                print(f"[pipeline] Error processing {msg_id}: {e}")
                mark_seen(msg_id)

    except Exception as e:
        print(f"[pipeline] Poll error: {e}")


if __name__ == "__main__":
    import time
    init_db()
    print("[pipeline] Started — polling every 5 minutes")
    while True:
        poll()
        time.sleep(300)
