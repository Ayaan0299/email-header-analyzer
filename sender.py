import os
import smtplib
import glob
import time
import random
from datetime import datetime, timedelta
from email import message_from_bytes
from email.utils import formatdate
from dotenv import load_dotenv

load_dotenv()

SAMPLES_DIR     = os.path.join(os.path.dirname(__file__), "data", "samples")
DUMMY_RECIPIENT = "test@mailtrap.io"
DELAY           = 3.0  # seconds between sends

# 6-month window ending today
_END   = datetime(2026, 5, 11, 23, 59, 59)
_START = _END - timedelta(days=182)
_SPAN  = (_END - _START).total_seconds()


def _random_date() -> str:
    """Return a realistic Date header value spread across the last 6 months."""
    while True:
        # Exponential bias toward recent — more traffic near end of window
        offset = random.expovariate(1 / (_SPAN * 0.4))
        offset = min(offset, _SPAN)
        dt = _END - timedelta(seconds=offset)
        # Down-weight weekends
        if dt.weekday() >= 5 and random.random() < 0.4:
            continue
        # Business hours bias: 6am–11pm much more likely
        if dt.hour < 6 and random.random() < 0.75:
            continue
        if dt.hour >= 23 and random.random() < 0.6:
            continue
        # Mid-week spike (Tue/Wed/Thu slightly more emails)
        if dt.weekday() in (1, 2, 3) and random.random() < 0.15:
            continue  # accept faster — no skip
        return formatdate(dt.timestamp(), localtime=False)


def _make_server():
    host     = os.getenv("MAILTRAP_SMTP_HOST", "sandbox.smtp.mailtrap.io")
    port     = int(os.getenv("MAILTRAP_SMTP_PORT", 2525))
    user     = os.getenv("MAILTRAP_USER")
    password = os.getenv("MAILTRAP_PASSWORD")
    server   = smtplib.SMTP(host, port, timeout=20)
    server.starttls()
    server.login(user, password)
    return server


def send_samples():
    user     = os.getenv("MAILTRAP_USER")
    password = os.getenv("MAILTRAP_PASSWORD")

    if not all([user, password]):
        print("[sender] Missing SMTP credentials in .env")
        return

    files = sorted(glob.glob(os.path.join(SAMPLES_DIR, "*.eml")))
    if not files:
        print("[sender] No .eml files found in data/samples/")
        return

    limit = int(os.getenv("SENDER_LIMIT", 0))
    if limit:
        files = files[:limit]

    print(f"[sender] Sending {len(files)} samples with randomised dates ({DELAY}s intervals)...")
    sent = failed = 0
    server = _make_server()

    for i, path in enumerate(files):
        try:
            with open(path, "rb") as f:
                raw = f.read()

            msg = message_from_bytes(raw)

            # Override Date header with a realistic random timestamp
            if "Date" in msg:
                del msg["Date"]
            msg["Date"] = _random_date()

            # Resolve From address
            from_addr = msg.get("From", user)
            if "<" in from_addr and ">" in from_addr:
                from_addr = from_addr.split("<")[1].split(">")[0].strip()
            from_addr = from_addr.strip()

            server.sendmail(from_addr, DUMMY_RECIPIENT, msg.as_bytes())
            if (i + 1) % 10 == 0:
                print(f"[sender] {i + 1}/{len(files)} sent")
            sent += 1
            time.sleep(DELAY)

        except smtplib.SMTPException as e:
            print(f"[sender] SMTP error on {os.path.basename(path)}: {e}")
            failed += 1
            try: server.quit()
            except Exception: pass
            try:
                server = _make_server()
            except Exception as ce:
                print(f"[sender] Reconnect failed: {ce}")
                break
            time.sleep(DELAY)

        except Exception as e:
            print(f"[sender] Error on {os.path.basename(path)}: {e}")
            failed += 1

    try: server.quit()
    except Exception: pass
    print(f"\n[sender] Done — {sent} sent, {failed} failed")


if __name__ == "__main__":
    send_samples()
