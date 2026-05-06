import os
import smtplib
import glob
from email import message_from_file
from dotenv import load_dotenv

load_dotenv()

SAMPLES_DIR = os.path.join(os.path.dirname(__file__), "data", "samples")
DUMMY_RECIPIENT = "test@mailtrap.io"


def send_samples():
    host     = os.getenv("MAILTRAP_SMTP_HOST", "smtp.mailtrap.io")
    port     = int(os.getenv("MAILTRAP_SMTP_PORT", 587))
    user     = os.getenv("MAILTRAP_USER")
    password = os.getenv("MAILTRAP_PASSWORD")

    if not all([user, password]):
        print("[sender] Missing SMTP credentials in .env")
        return

    files = glob.glob(os.path.join(SAMPLES_DIR, "*.eml"))

    if not files:
        print(
            "[sender] No .eml files found in data/samples/\n"
            "Download real phishing samples from:\n"
            "  https://github.com/rf-peixoto/phishing_pot\n"
            "Then place the .eml files into data/samples/ and re-run."
        )
        return

    with smtplib.SMTP(host, port) as server:
        server.starttls()
        server.login(user, password)

        for path in files:
            try:
                with open(path, "r", errors="replace") as f:
                    msg = message_from_file(f)

                from_addr = msg.get("From", user)
                server.sendmail(from_addr, DUMMY_RECIPIENT, msg.as_string())
                print(f"[sender] Sent: {os.path.basename(path)}")
            except Exception as e:
                print(f"[sender] Failed {os.path.basename(path)}: {e}")


if __name__ == "__main__":
    send_samples()
