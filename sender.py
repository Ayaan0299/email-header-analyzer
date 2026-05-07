import os
import smtplib
import glob
import time
from email import message_from_bytes
from dotenv import load_dotenv

load_dotenv()

SAMPLES_DIR = os.path.join(os.path.dirname(__file__), "data", "samples")
DUMMY_RECIPIENT = "test@mailtrap.io"
DELAY = 1.2  # seconds between sends — stays under Mailtrap free tier rate limit


def _make_server():
    host     = os.getenv("MAILTRAP_SMTP_HOST", "sandbox.smtp.mailtrap.io")
    port     = int(os.getenv("MAILTRAP_SMTP_PORT", 2525))
    user     = os.getenv("MAILTRAP_USER")
    password = os.getenv("MAILTRAP_PASSWORD")
    server = smtplib.SMTP(host, port)
    server.starttls()
    server.login(user, password)
    return server


def send_samples():
    user     = os.getenv("MAILTRAP_USER")
    password = os.getenv("MAILTRAP_PASSWORD")

    if not all([user, password]):
        print("[sender] Missing SMTP credentials in .env")
        return

    files = glob.glob(os.path.join(SAMPLES_DIR, "*.eml"))

    if not files:
        print(
            "[sender] No .eml files found in data/samples/\n"
            "Download: https://github.com/rf-peixoto/phishing_pot"
        )
        return

    print(f"[sender] Sending {len(files)} samples...")
    sent = failed = 0
    server = _make_server()

    for i, path in enumerate(files):
        try:
            with open(path, "rb") as f:
                raw = f.read()

            msg = message_from_bytes(raw)
            from_addr = msg.get("From", user)
            # Strip angle brackets and whitespace from From if needed
            if "<" in from_addr and ">" in from_addr:
                from_addr = from_addr.split("<")[1].split(">")[0].strip()

            server.sendmail(from_addr, DUMMY_RECIPIENT, raw)
            print(f"[sender] Sent: {os.path.basename(path)}")
            sent += 1
            time.sleep(DELAY)

        except smtplib.SMTPException as e:
            print(f"[sender] Failed {os.path.basename(path)}: {e}")
            failed += 1
            # Reconnect on SMTP-level errors
            try:
                server.quit()
            except Exception:
                pass
            try:
                server = _make_server()
            except Exception as ce:
                print(f"[sender] Reconnect failed: {ce}")
                break
            time.sleep(DELAY)

        except Exception as e:
            print(f"[sender] Failed {os.path.basename(path)}: {e}")
            failed += 1

    try:
        server.quit()
    except Exception:
        pass

    print(f"\n[sender] Done — {sent} sent, {failed} failed")


if __name__ == "__main__":
    send_samples()
