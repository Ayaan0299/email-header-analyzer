# Email Header Analyzer — Project Context
# Read automatically by Claude Code every session.
# Full context so you never have to re-explain the project.

---

## What This Project Is
# NOT just a SOC tool. Frames across three roles:
#
# SOC Analyst      — automates manual phishing email triage
# GRC              — validates email authentication controls (ISO 27001 Annex A.13)
# Cybersecurity    — threat detection pipeline with IOC extraction and risk scoring
#
# Two modes:
# 1. Manual    — user pastes raw header into web UI, gets verdict instantly
# 2. Pipeline  — automated, monitors Mailtrap inbox, analyses emails without human input

A Python Flask web application and automated detection pipeline that:
- Parses raw email headers
- Performs live SPF/DKIM/DMARC DNS validation
- Extracts IOCs (IPs, domains, mismatches)
- Scores phishing risk 0-100
- Logs every result to SQLite
- Displays metrics on a real-time dashboard
- Monitors a Mailtrap inbox automatically via IMAP

---

## UI/UX Skill — REQUIRED FOR ALL UI WORK
# This project uses the ui-ux-pro-max skill for all frontend design.
# Before touching ANY HTML, CSS, or UI code, run this first:
#
# STEP 1 — Install the skill (one time only):
#   npx uipro init --ai claude
#   OR manually clone: git clone https://github.com/nextlevelbuilder/ui-ux-pro-max-skill.git
#   Then copy .claude/skills/ui-ux-pro-max/ into your project's .claude/skills/
#
# STEP 2 — Before building any UI page, generate the design system:
#   python3 skills/ui-ux-pro-max/scripts/search.py "cybersecurity phishing detection dashboard dark mode" --design-system -p "Email Header Analyzer"
#
# STEP 3 — For specific pages, run domain searches:
#   python3 skills/ui-ux-pro-max/scripts/search.py "dashboard analytics security" --domain style
#   python3 skills/ui-ux-pro-max/scripts/search.py "dark mode terminal monospace" --domain color
#   python3 skills/ui-ux-pro-max/scripts/search.py "form input validation verdict" --domain ux
#
# STEP 4 — Use the generated design system to implement all UI
#   Read design-system/MASTER.md before writing any code
#   Check design-system/pages/<page-name>.md if it exists
#
# Stack: HTML + CSS + JS (no framework) — specify this when running the skill
# Dark terminal aesthetic is the base — skill should enhance it, not replace it
#
# DO NOT build or redesign any UI without running the skill first
# DO NOT use generic AI-looking UI — the skill prevents this

---

## Current UI State
# A working prototype exists: ayaan-email-analyzer.html
# Dark terminal aesthetic — IBM Plex Mono + IBM Plex Sans, bg #07080d
# Ayaan wants a UI redesign — cleaner, more professional, same dark theme
# DO NOT redesign until explicitly asked
# WHEN asked to redesign: run the ui-ux-pro-max skill first (see above), then implement

---

## How the Pipeline Works
# Core automated flow — no human input after setup

# STEP 1 — Data source: phishing_pot dataset
# Real anonymised phishing .eml files from:
# https://github.com/rf-peixoto/phishing_pot
# Downloaded into data/samples/ folder

# STEP 2 — sender.py reads each .eml file
# Extracts raw headers from the file
# Sends to Mailtrap inbox via SMTP
# Headers stay 100% intact — Mailtrap doesn't rewrite anything
# This is why we use Mailtrap not Gmail — Gmail rewrites spoofed From addresses

# STEP 3 — pipeline.py monitors Mailtrap inbox via IMAP
# Runs in background forever
# Wakes up every 5 minutes
# Connects to Mailtrap like an email app would
# Fetches all UNSEEN emails
# Extracts raw header from each one

# STEP 4 — analyzer.py runs all 6 checks on each header
# Same logic as manual mode — no difference
# Returns score + verdict + per-check results

# STEP 5 — database.py saves result to SQLite
# One row per email — timestamp, sender, domain, SPF, DKIM, DMARC, score, verdict

# STEP 6 — alerts.py triggers if score >= 55
# Sends alert to real inbox via SMTP

# STEP 7 — dashboard reads SQLite and shows live metrics
# http://localhost:5000/dashboard

---

## Why Mailtrap (not Gmail)
# Gmail rewrites spoofed From headers — breaks all the checks
# Mailtrap is a sandboxed fake inbox built for developers
# Accepts any headers exactly as sent — spoofed From, Reply-To, display name all intact
# Free tier: 1000 emails/month — more than enough
# Supports SMTP (sending) and IMAP (reading)
# Sign up: mailtrap.io

---

## Why phishing_pot Dataset
# Real anonymised phishing emails from the wild — not fake generated ones
# 1000+ .eml files — PayPal, Apple, banking, HMRC, Amazon spoofs
# Headers are real — SPF fails, DKIM fails, DMARC fails, mismatched Reply-To
# More credible than synthetic data
# Interview quote: "tested against real world phishing samples"
# Source: https://github.com/rf-peixoto/phishing_pot

---

## Tech Stack
# Backend
- Python Flask     — web framework, routes, renders templates
- dnspython        — live DNS lookups for SPF/DKIM/DMARC
- email (stdlib)   — parses raw .eml files and header strings
- imaplib (stdlib) — connects to Mailtrap inbox, fetches UNSEEN emails
- smtplib (stdlib) — sends .eml files to Mailtrap + sends alerts
- sqlite3 (stdlib) — logs every result to results.db
- re (stdlib)      — regex extracts IPs, domains from headers
- python-dotenv    — loads Mailtrap credentials from .env

# Frontend
- Jinja2           — Flask templating
- HTML/CSS/JS      — dark terminal aesthetic (redesign pending — use ui-ux-pro-max skill)
- Chart.js         — bar chart, donut chart on dashboard

---

## The 6 Checks
# Points added per failed check, score capped at 100

- SPF          — DNS: is sending server authorised for this domain?    +25 fail / +10 none
- DKIM         — DNS + crypto: is email signature valid?               +20 fail / +8 none
- DMARC        — DNS: did domain owner authorise this email?           +25 fail / +8 none
- Reply-To     — string: does reply-to domain match from domain?       +15 mismatch
- Display Name — brand list: does display name match sending address?  +10 spoof
- Sending IP   — reverse DNS: is sending IP suspicious?                +10 suspicious

# Verdict thresholds
0  - 24  = LIKELY LEGITIMATE  (green)
25 - 54  = SUSPICIOUS         (amber)
55 - 100 = LIKELY PHISHING    (red)

---

## Dashboard Metrics
# /dashboard — reads SQLite in real time

# Stat cards
- Total Analysed    — total rows in results table
- Phishing Detected — count where verdict = LIKELY PHISHING
- Suspicious        — count where verdict = SUSPICIOUS
- Legitimate        — count where verdict = LIKELY LEGITIMATE
- Detection Rate %  — (phishing + suspicious) / total * 100

# Charts
- Emails per day    — bar chart, last 7 days
- Verdict split     — donut chart, phishing vs suspicious vs legitimate %
- Failing checks    — bar chart, which checks fail most often

# Recent activity table
- Last 20 results — timestamp, sender, domain, score, verdict
- Colour coded rows — red / amber / green

---

## SQLite Schema

```sql
CREATE TABLE results (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp  TEXT,
    sender     TEXT,
    domain     TEXT,
    spf        TEXT,     -- PASS / FAIL / NONE
    dkim       TEXT,     -- PASS / FAIL / NONE
    dmarc      TEXT,     -- PASS / FAIL / NONE
    reply_to   TEXT,     -- MATCH / MISMATCH / N/A
    disp_name  TEXT,     -- OK / SPOOFED
    ip_flag    TEXT,     -- NORMAL / SUSPICIOUS
    score      INTEGER,  -- 0-100
    verdict    TEXT      -- LIKELY LEGITIMATE / SUSPICIOUS / LIKELY PHISHING
);
```

---

## File Structure

```
email-header-analyzer/
├── app.py              # Flask — web UI routes + /dashboard route
├── analyzer.py         # Core — header parsing, DNS lookups, scoring, verdict
├── pipeline.py         # IMAP monitor — polls Mailtrap every 5 mins
├── sender.py           # Sends phishing_pot .eml files to Mailtrap via SMTP
├── database.py         # SQLite — create table, insert result, query stats
├── alerts.py           # Alert sender — triggers on score >= 55
├── templates/
│   ├── index.html      # Manual input page — textarea + analyse button
│   ├── results.html    # Results page — verdict, checks, bar chart
│   └── dashboard.html  # Metrics dashboard — stat cards, charts, table
├── static/
│   └── style.css       # Styling — dark terminal aesthetic (redesign pending)
├── data/
│   └── samples/        # phishing_pot .eml files go here
├── .claude/
│   └── skills/
│       └── ui-ux-pro-max/  # UI/UX skill — install before any UI work
├── requirements.txt    # flask, dnspython, python-dotenv
├── .env                # Mailtrap credentials — NOT committed to git
├── .gitignore          # excludes .env, __pycache__, venv, results.db, data/
├── README.md           # GitHub readme with screenshots + metrics
└── CLAUDE.md           # this file
```

---

## .env File
# Never commit to GitHub

```
MAILTRAP_USER=your-mailtrap-smtp-username
MAILTRAP_PASSWORD=your-mailtrap-smtp-password
MAILTRAP_IMAP_USER=your-mailtrap-imap-username
MAILTRAP_IMAP_PASSWORD=your-mailtrap-imap-password
MAILTRAP_IMAP_HOST=imap.mailtrap.io
MAILTRAP_SMTP_HOST=smtp.mailtrap.io
MAILTRAP_SMTP_PORT=587
ALERT_EMAIL=ayaanlatif691@outlook.com
```

---

## Requirements

```
flask
dnspython
python-dotenv
```
# All other libraries are Python stdlib — no extra install needed

---

## Run Locally

# Web UI (manual mode)
```bash
pip install -r requirements.txt
python app.py
# open http://localhost:5000
```

# Pipeline (automated mode) — separate terminal
```bash
python pipeline.py
# runs forever, polls Mailtrap every 5 minutes
```

# Send phishing_pot samples to Mailtrap — run once to populate data
```bash
python sender.py
# reads .eml files from data/samples/, sends to Mailtrap
```

---

## Current Status

DONE:
- [x] Frontend prototype (ayaan-email-analyzer.html) — UI with verdict, checks, bar chart
- [x] Scoring logic defined and tested
- [x] Pipeline architecture fully designed
- [x] Mailtrap chosen as sandboxed inbox
- [x] phishing_pot chosen as data source
- [x] CLAUDE.md written
- [x] README.md written

TODO:
- [ ] Install ui-ux-pro-max skill: npx uipro init --ai claude
- [ ] Build app.py + analyzer.py (Flask backend + core logic)
- [ ] Build pipeline.py (IMAP Mailtrap monitor)
- [ ] Build sender.py (sends phishing_pot .eml files to Mailtrap)
- [ ] Build database.py (SQLite helper)
- [ ] Build alerts.py (alert sender)
- [ ] Build dashboard.html (metrics + charts)
- [ ] Set up Mailtrap account + add credentials to .env
- [ ] Download phishing_pot samples into data/samples/
- [ ] Test full pipeline end to end
- [ ] UI REDESIGN — run ui-ux-pro-max skill first, then redesign all pages (do this last)
- [ ] Deploy to Render free tier
- [ ] Screenshot dashboard with real metrics for README + CV

---

## Role Framing

# SOC ANALYST — lead with automation, pipeline, real-time detection
"Automated phishing email triage pipeline — IMAP inbox monitoring, SPF/DKIM/DMARC
DNS validation, IOC extraction, SQLite logging, and real-time alert system.
Tested against 50+ real-world phishing samples from the phishing_pot dataset."

# GRC — lead with control validation, ISO 27001, compliance reporting
"Email authentication control validation tool — automates SPF/DKIM/DMARC policy
verification mapping to ISO 27001 Annex A.13, with risk scoring and a compliance
metrics dashboard showing control effectiveness over time."

# CYBERSECURITY ANALYST — lead with threat detection, IOC extraction, metrics
"Automated threat detection pipeline — parses raw email headers, performs live
DNS-based IOC extraction across 6 checks, scores risk 0-100, and surfaces
detection metrics on a real-time dashboard. Tested against real phishing datasets."

---

## Interview Narrative
"During my Mastercard virtual experience I was manually analysing phishing indicators
in email headers. I built this tool to automate that process — it runs the same DNS
checks a SOC analyst would do by hand but in seconds. I then extended it into a full
pipeline that monitors a live inbox via IMAP, uses real phishing samples from the
wild as test data, logs every result to a database, and surfaces detection metrics
on a dashboard — so you can see trends over time."

---

## Links
- GitHub    : github.com/Ayaan0299 — repo: email-header-analyzer
- Portfolio : ayaan0299.github.io
- Email     : ayaanlatif691@outlook.com
