"""
Local pipeline — reads .eml files directly from data/samples/ and runs the
full analyzer on each one. Populates results.db identically to the IMAP
pipeline, but without needing Mailtrap credentials or rate limits.

Usage:
    python3 pipeline_local.py            # process all files
    python3 pipeline_local.py --limit 50 # process first N files
"""

import argparse
import glob
import os
from email import message_from_bytes

from analyzer import analyse
from database import init_db, insert_result
from alerts import send_alert

SAMPLES_DIR = os.path.join(os.path.dirname(__file__), "data", "samples")


def _extract_raw_header(raw_bytes):
    text = raw_bytes.decode("utf-8", errors="replace")
    blank = text.find("\r\n\r\n")
    if blank == -1:
        blank = text.find("\n\n")
    return text[:blank] if blank != -1 else text


def run(limit=None):
    init_db()

    files = sorted(glob.glob(os.path.join(SAMPLES_DIR, "*.eml")))
    if limit:
        files = files[:limit]

    if not files:
        print(f"[pipeline_local] No .eml files in {SAMPLES_DIR}")
        return

    print(f"[pipeline_local] Processing {len(files)} samples...")
    done = failed = 0

    for path in files:
        try:
            with open(path, "rb") as f:
                raw = f.read()

            raw_header = _extract_raw_header(raw)
            result = analyse(raw_header)

            parsed  = result["parsed"]
            checks  = result["checks"]
            score   = result["score"]
            verdict = result["verdict"]

            insert_result(parsed, checks, score, verdict)

            sender = parsed.get("from_email") or os.path.basename(path)
            print(f"  [{verdict[:1]}] {sender} — score {score}")
            done += 1

            if score >= 55:
                send_alert(parsed, score, verdict)

        except Exception as e:
            print(f"  [!] {os.path.basename(path)}: {e}")
            failed += 1

    print(f"\n[pipeline_local] Done — {done} analysed, {failed} failed")
    print(f"[pipeline_local] Open http://localhost:5000/dashboard to see results")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None, help="Max samples to process")
    args = parser.parse_args()
    run(limit=args.limit)
