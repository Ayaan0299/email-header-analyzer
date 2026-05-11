# Email Header Analyzer — Project Context
# This file is read automatically by Claude Code at the start of every session.
# It gives Claude full context so you never have to re-explain the project.

---

## What this is
A portfolio cybersecurity project targeting GRC and SOC analyst roles.
Automates the manual process a SOC analyst does when investigating a phishing report.

A Python Flask web tool that parses raw email headers, performs automated
SPF/DKIM/DMARC validation via live DNS lookups, generates a phishing risk verdict,
and monitors a Mailtrap sandbox inbox via REST API every 5 minutes for new emails.

---

## Tech Stack

### Backend
- Python Flask     — web framework, routes, Jinja2 templates
- dnspython        — live DNS lookups for SPF/DKIM/DMARC
- email (stdlib)   — parses raw header into structured fields
- re (stdlib)      — regex for IP/domain extraction
- ipaddress        — validates and classifies IPs
- requests         — Mailtrap REST API calls in pipeline.py
- python-dotenv    — loads .env credentials
- sqlite3 (stdlib) — stores results in results.db

### Frontend
- Jinja2           — Flask templating
- HTML/CSS/JS      — dark galaxy theme, animated starfield canvas
- Fira Code/Sans   — monospace + sans fonts
- Leaflet.js       — world map with IP geolocation markers
- Leaflet.markercluster — groups overlapping markers
- Chart.js         — bar chart (emails/day) + donut chart (verdict split)
- ip-api.com       — free batch IP geolocation (no key required)

---

## How It Works — Step by Step

### Manual analysis (web UI)
1. User pastes raw email header into textarea on index.html
2. Flask POST route in app.py passes it to analyzer.py
3. email stdlib parses the raw string into structured header fields
4. dnspython queries the sender domain's DNS records live
5. Logic checks: reply-to mismatch, display name spoof, suspicious IP, SPF/DKIM/DMARC
6. Risk score calculated (0–100), verdict assigned, rendered in results.html

### Automated pipeline (pipeline.py — runs every 5 minutes)
1. Calls GET https://mailtrap.io/api/accounts/{account_id}/inboxes/{inbox_id}/messages
   with Bearer token auth — NOTE: uses mailtrap.io/api NOT sandbox.api.mailtrap.io
   (IMAP is NOT available on the Mailtrap free sandbox plan; REST API is the only option)
2. Filters out already-seen message IDs using the seen_messages SQLite table
3. Fetches raw email via GET .../messages/{id}/body.raw
4. Extracts headers, passes to analyze(), stores result in results.db
5. Triggers SMTP alert to ALERT_EMAIL if score >= 55
6. Marks message as seen in seen_messages table

### Local bulk pipeline (pipeline_local.py)
- Reads .eml files directly from data/samples/ — bypasses Mailtrap entirely
- Used to seed results.db with 8,071 real phishing samples from phishing_pot dataset
- Timestamps backfilled across 6-month window (Nov 2025 → May 2026)

---

## Checks Performed

- SPF          — is the sending server authorised for this domain? (DNS lookup)
- DKIM         — is the cryptographic email signature valid? (DNS + crypto)
- DMARC        — did the domain owner authorise this email? (DNS lookup)
- Reply-To     — does reply-to domain match the from domain?
- Display Name — does display name match actual sending address? (brand list)
- Sending IP   — reverse DNS on sending IP, flags unexpected origin

---

## Scoring Logic

SPF fail           = +25 pts
SPF not found      = +10 pts
DKIM fail          = +20 pts
DKIM not found     = +8 pts
DMARC fail         = +25 pts
DMARC not found    = +8 pts
Reply-To mismatch  = +15 pts
Display name spoof = +10 pts
Suspicious IP      = +10 pts

Verdict thresholds:
0–24   = LIKELY LEGITIMATE  (green)
25–54  = SUSPICIOUS         (amber)
55–100 = LIKELY PHISHING    (red)

---

## File Structure

```
email-header-analyzer/
├── app.py              # Flask — routes /, /analyse, /dashboard, /api/geo, /api/stats
├── analyzer.py         # Core logic — parsing, DNS, scoring, verdict
├── pipeline.py         # Mailtrap REST API poller — runs every 5 min
├── pipeline_local.py   # Bulk processor — reads .eml files directly from disk
├── sender.py           # Sends .eml files to Mailtrap via SMTP
│                         Overrides Date header with realistic random timestamps
│                         spread across last 6 months (weekday-biased, 6am–11pm,
│                         slight mid-week spike) using exponential recency bias
├── database.py         # SQLite helpers — init, insert, get_stats, get_recent,
│                         is_seen, mark_seen (seen_messages dedup table)
├── geo.py              # IP geolocation via ip-api.com batch API (cached)
├── alerts.py           # SMTP alert on score >= 55 → ALERT_EMAIL
├── backfill_dates.py   # One-off script — spread DB timestamps across 6 months
├── templates/
│   ├── index.html      # Input page — animated shield hero, glassmorphism card
│   ├── results.html    # Results — animated SVG score ring, neon verdict chip
│   └── dashboard.html  # Dashboard — stat cards, world map, charts, table
├── static/
│   └── style.css       # Galaxy theme — #07080d bg, Fira Code, glassmorphism,
│                         neon green/blue, animated starfield
├── data/samples/       # 7,911 real phishing .eml files (phishing_pot dataset)
├── results.db          # SQLite — 8,071 rows, Nov 2025 → May 2026
├── requirements.txt
├── render.yaml         # Render deployment config
├── .env                # credentials (not committed)
└── CLAUDE.md           # this file
```

---

## .env Variables

```
FLASK_ENV=development

# Mailtrap SMTP (for sender.py — sends test emails to inbox)
MAILTRAP_SMTP_HOST=sandbox.smtp.mailtrap.io
MAILTRAP_SMTP_PORT=2525
MAILTRAP_USER=74ca30b66f0a2d
MAILTRAP_PASSWORD=3256b450d71b5c

# Mailtrap REST API (for pipeline.py — reads inbox)
MAILTRAP_API_TOKEN=edee3b6a05bbe2d0207a8ab27b2a704e
MAILTRAP_INBOX_ID=4604529
MAILTRAP_ACCOUNT_ID=2712769   # default hardcoded in pipeline.py

# Alert destination
ALERT_EMAIL=ayaanlatif691@outlook.com
```

Note: SMTP monthly send limit on free plan — resets 1st of each month.
If sender.py fails with 535, the limit is hit; wait for reset or upgrade.

---

## Current Status

DONE:
- [x] Flask web app with live SPF/DKIM/DMARC DNS validation
- [x] Phishing risk scoring (0–100) with colour-coded verdict
- [x] Automated pipeline using Mailtrap REST API (not IMAP — not available on free plan)
- [x] SQLite results database with 8,071 real phishing samples
- [x] Timestamps spread across 6-month window for realistic dashboard charts
- [x] World map with IP geolocation (ip-api.com), Leaflet markercluster, pulsing markers
- [x] Galaxy/space UI — animated starfield, glassmorphism, neon accents
- [x] sender.py injects random Date headers (6-month spread, weekday-biased)
- [x] Deployed to GitHub (github.com/Ayaan0299/email-header-analyzer)
- [x] render.yaml ready for Render deployment

TODO:
- [ ] Deploy to Render free tier
- [ ] Add README.md with screenshots for GitHub
- [ ] Wait for Mailtrap SMTP limit reset (June 1st) to test full send→detect pipeline

---

## Run Locally

```bash
pip install -r requirements.txt
python app.py          # web UI at http://localhost:5001
python pipeline.py     # start automated inbox poller (every 5 min)
```

---

## CV Bullet Point

"Developed a Python Flask web application that automates email header analysis —
performing live SPF, DKIM, and DMARC DNS validation, IOC extraction, and display
name spoof detection — producing a colour-coded phishing risk verdict to reduce
manual triage time."

---

## Interview Narrative

"During my Mastercard virtual experience I was manually analysing phishing indicators
in email headers. I built this tool to automate that process — it runs the same DNS
checks a SOC analyst would do by hand, but in seconds, and presents it in a clear
verdict with a risk score. I also built a pipeline that monitors a live email inbox
via REST API, automatically analyses every incoming email, and triggers alerts for
high-risk messages."

---

## Links
- GitHub    : github.com/Ayaan0299/email-header-analyzer
- Portfolio : ayaan0299.github.io
- Email     : ayaanlatif691@outlook.com
