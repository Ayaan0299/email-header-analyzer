"""Spread existing DB row timestamps across a realistic 6-month window."""
import sqlite3
import random
from datetime import datetime, timedelta

DB_PATH = "results.db"

# 6-month window: Nov 10 2025 → May 11 2026
START = datetime(2025, 11, 10)
END   = datetime(2026, 5, 11, 23, 59, 59)
SPAN  = (END - START).total_seconds()

con = sqlite3.connect(DB_PATH)
cur = con.cursor()
cur.execute("SELECT id FROM results ORDER BY id ASC")
ids = [row[0] for row in cur.fetchall()]
print(f"Spreading {len(ids)} rows across {(END-START).days} days...")

# Build weighted timestamps: busier Mon-Fri, realistic hours (8am-10pm heavier)
def random_ts():
    while True:
        offset = random.expovariate(1 / (SPAN * 0.4))  # cluster more toward recent
        offset = min(offset, SPAN)
        dt = END - timedelta(seconds=offset)
        # Down-weight weekends slightly
        if dt.weekday() >= 5 and random.random() < 0.35:
            continue
        # Down-weight overnight hours (midnight-7am)
        if dt.hour < 7 and random.random() < 0.6:
            continue
        return dt

timestamps = sorted([random_ts() for _ in ids])  # keep chronological order

updates = [(ts.strftime("%Y-%m-%dT%H:%M:%S"), row_id)
           for ts, row_id in zip(timestamps, ids)]

cur.executemany("UPDATE results SET timestamp=? WHERE id=?", updates)
con.commit()
con.close()

print(f"Done — {START.date()} → {END.date()}")
print(f"Sample range check:")
import sqlite3 as s2
c = s2.connect(DB_PATH)
row = c.execute("SELECT MIN(timestamp), MAX(timestamp), COUNT(*) FROM results").fetchone()
print(f"  min={row[0]}  max={row[1]}  total={row[2]}")
c.close()
