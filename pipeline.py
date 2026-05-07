import imaplib
import os
import time
from email import message_from_bytes
from dotenv import load_dotenv

from analyzer import analyse
from database import init_db, insert_result
from alerts import send_alert

load_dotenv()

POLL_INTERVAL = 300  # 5 minutes


def _extract_raw_header(raw_bytes):
    text = raw_bytes.decode("utf-8", errors="replace")
    # Headers are everything before the first blank line
    blank = text.find("\r\n\r\n")
    if blank == -1:
        blank = text.find("\n\n")
    return text[:blank] if blank != -1 else text


def poll():
    host     = os.getenv("MAILTRAP_IMAP_HOST", "sandbox.imap.mailtrap.io")
    user     = os.getenv("MAILTRAP_IMAP_USER")
    password = os.getenv("MAILTRAP_IMAP_PASSWORD")

    if not all([user, password]):
        print("[pipeline] Missing IMAP credentials in .env — cannot poll")
        return

    try:
        mail = imaplib.IMAP4_SSL(host)
        mail.login(user, password)
        mail.select("INBOX")

        _, data = mail.search(None, "UNSEEN")
        ids = data[0].split()

        if not ids:
            print(f"[pipeline] No new messages")
            mail.logout()
            return

        for uid in ids:
            _, msg_data = mail.fetch(uid, "(RFC822)")
            raw = msg_data[0][1]

            raw_header = _extract_raw_header(raw)
            result = analyse(raw_header)

            parsed  = result["parsed"]
            checks  = result["checks"]
            score   = result["score"]
            verdict = result["verdict"]

            insert_result(parsed, checks, score, verdict)

            print(f"[pipeline] {parsed.get('from_email','?')} | score={score} | {verdict}")

            if score >= 55:
                send_alert(parsed, score, verdict)

            mail.store(uid, "+FLAGS", "\\Seen")

        mail.logout()

    except Exception as e:
        print(f"[pipeline] Error: {e}")


def main():
    init_db()
    print("[pipeline] Started — polling every 5 minutes")
    while True:
        poll()
        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
