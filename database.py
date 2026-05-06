import sqlite3
from datetime import datetime, timedelta

DB_PATH = "results.db"


def _conn():
    return sqlite3.connect(DB_PATH)


def init_db():
    with _conn() as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS results (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp  TEXT,
                sender     TEXT,
                domain     TEXT,
                spf        TEXT,
                dkim       TEXT,
                dmarc      TEXT,
                reply_to   TEXT,
                disp_name  TEXT,
                ip_flag    TEXT,
                score      INTEGER,
                verdict    TEXT
            )
        """)


def _status(check_status, kind):
    s = check_status.get("status", "pass")
    if kind == "binary":
        return "PASS" if s == "pass" else "FAIL" if s == "fail" else "NONE"
    if kind == "reply_to":
        return "MATCH" if s == "pass" else "MISMATCH" if s == "fail" else "N/A"
    if kind == "disp_name":
        return "SPOOFED" if s == "fail" else "OK"
    if kind == "ip_flag":
        return "SUSPICIOUS" if s == "fail" else "NORMAL"
    return "NONE"


def insert_result(parsed, checks, score, verdict):
    row = (
        datetime.utcnow().isoformat(timespec="seconds"),
        parsed.get("from_email", ""),
        parsed.get("from_domain", ""),
        _status(checks.get("spf", {}),          "binary"),
        _status(checks.get("dkim", {}),         "binary"),
        _status(checks.get("dmarc", {}),        "binary"),
        _status(checks.get("reply_to", {}),     "reply_to"),
        _status(checks.get("display_name", {}), "disp_name"),
        _status(checks.get("sending_ip", {}),   "ip_flag"),
        score,
        verdict,
    )
    with _conn() as con:
        con.execute(
            "INSERT INTO results (timestamp,sender,domain,spf,dkim,dmarc,reply_to,disp_name,ip_flag,score,verdict) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            row,
        )


def get_stats():
    with _conn() as con:
        con.row_factory = sqlite3.Row
        cur = con.cursor()

        cur.execute("SELECT COUNT(*) AS n FROM results")
        total = cur.fetchone()["n"]

        cur.execute("SELECT COUNT(*) AS n FROM results WHERE verdict='LIKELY PHISHING'")
        phishing = cur.fetchone()["n"]

        cur.execute("SELECT COUNT(*) AS n FROM results WHERE verdict='SUSPICIOUS'")
        suspicious = cur.fetchone()["n"]

        cur.execute("SELECT COUNT(*) AS n FROM results WHERE verdict='LIKELY LEGITIMATE'")
        legitimate = cur.fetchone()["n"]

        detection_rate = round((phishing + suspicious) / total * 100, 1) if total else 0.0

        # emails per day last 7 days
        emails_per_day = []
        for i in range(6, -1, -1):
            day = (datetime.utcnow() - timedelta(days=i)).strftime("%Y-%m-%d")
            cur.execute("SELECT COUNT(*) AS n FROM results WHERE timestamp LIKE ?", (day + "%",))
            emails_per_day.append({"date": day, "count": cur.fetchone()["n"]})

        phishing_pct  = round(phishing  / total * 100, 1) if total else 0.0
        suspicious_pct = round(suspicious / total * 100, 1) if total else 0.0
        legitimate_pct = round(legitimate / total * 100, 1) if total else 0.0

        check_failures = {}
        for col in ("spf", "dkim", "dmarc"):
            cur.execute(f"SELECT COUNT(*) AS n FROM results WHERE {col} IN ('FAIL','NONE')")
            check_failures[col] = cur.fetchone()["n"]
        cur.execute("SELECT COUNT(*) AS n FROM results WHERE reply_to='MISMATCH'")
        check_failures["reply_to"] = cur.fetchone()["n"]
        cur.execute("SELECT COUNT(*) AS n FROM results WHERE disp_name='SPOOFED'")
        check_failures["disp_name"] = cur.fetchone()["n"]
        cur.execute("SELECT COUNT(*) AS n FROM results WHERE ip_flag='SUSPICIOUS'")
        check_failures["ip_flag"] = cur.fetchone()["n"]

    return {
        "total": total,
        "phishing": phishing,
        "suspicious": suspicious,
        "legitimate": legitimate,
        "detection_rate": detection_rate,
        "emails_per_day": emails_per_day,
        "verdict_split": {
            "phishing_pct": phishing_pct,
            "suspicious_pct": suspicious_pct,
            "legitimate_pct": legitimate_pct,
        },
        "check_failures": check_failures,
    }


def get_recent(n=20):
    with _conn() as con:
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        cur.execute("SELECT * FROM results ORDER BY id DESC LIMIT ?", (n,))
        return [dict(row) for row in cur.fetchall()]
