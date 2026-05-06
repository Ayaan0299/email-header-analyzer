import smtplib
import os
from email.mime.text import MIMEText
from dotenv import load_dotenv

load_dotenv()


def send_alert(parsed, score, verdict):
    host     = os.getenv("MAILTRAP_SMTP_HOST", "smtp.mailtrap.io")
    port     = int(os.getenv("MAILTRAP_SMTP_PORT", 587))
    user     = os.getenv("MAILTRAP_USER")
    password = os.getenv("MAILTRAP_PASSWORD")
    to_addr  = os.getenv("ALERT_EMAIL")

    if not all([user, password, to_addr]):
        print("[alerts] Missing SMTP credentials in .env — skipping alert")
        return

    body = (
        f"PHISHING ALERT\n"
        f"{'='*40}\n"
        f"Sender  : {parsed.get('from_email', 'unknown')}\n"
        f"Domain  : {parsed.get('from_domain', 'unknown')}\n"
        f"IP      : {parsed.get('sending_ip', 'unknown')}\n"
        f"Score   : {score}/100\n"
        f"Verdict : {verdict}\n"
    )

    msg = MIMEText(body)
    msg["Subject"] = f"ALERT: Phishing Detected — score {score}"
    msg["From"]    = user
    msg["To"]      = to_addr

    try:
        with smtplib.SMTP(host, port) as server:
            server.starttls()
            server.login(user, password)
            server.sendmail(user, to_addr, msg.as_string())
        print(f"[alerts] Alert sent to {to_addr}")
    except Exception as e:
        print(f"[alerts] Failed to send alert: {e}")
