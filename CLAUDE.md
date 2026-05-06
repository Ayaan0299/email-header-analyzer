

# Email Header Analyzer — Project Context
# This file is read automatically by Claude Code at the start of every session.
# It gives Claude full context so you never have to re-explain the project.

---

## What this is
# A portfolio cybersecurity project targeting GRC and SOC analyst roles.
# Automates the manual process a SOC analyst does when investigating a phishing report.
# Built with Python Flask — same stack as ClearRisk so familiar territory.

A Python Flask web tool that parses raw email headers, performs automated
SPF/DKIM/DMARC validation via live DNS lookups, and generates a phishing risk verdict.

---

## Tech Stack
# Backend — Python handles all parsing and DNS logic
- Python Flask        — web framework, handles routes and renders templates
- dnspython           — performs live DNS lookups for SPF/DKIM/DMARC records
- email (stdlib)      — built-in Python library, parses raw header into structured fields
- re (stdlib)         — regex, extracts IPs and domains from raw header strings
- ipaddress (stdlib)  — validates and classifies IPs found in headers
- python-dotenv       — loads environment variables from .env file

# Frontend — Jinja2 templates rendered by Flask
- Jinja2              — Flask's built-in templating, renders the results dashboard
- HTML/CSS/JS         — single page UI, input view switches to results on analyse
- IBM Plex Mono       — monospace font for labels, scores, code-style elements
- IBM Plex Sans       — sans-serif font for body text

---

## How It Works — Step by Step
# Core flow. Each step maps to a function in the codebase.

# 1 — User pastes raw email header into textarea on index.html
# 2 — Flask receives it via POST route in app.py, passes to analyzer.py
# 3 — email stdlib parses the raw string into structured header fields
# 4 — dnspython queries the sender domain's DNS records live
# 5 — Logic checks run: reply-to mismatch, display name spoof, suspicious IP
# 6 — Risk score calculated (0-100), verdict assigned, results rendered in results.html

---

## Checks Performed
# Each check has a point weight in the scoring system (see Scoring Logic)

- SPF          — is the sending server authorised for this domain? (DNS lookup)
- DKIM         — is the cryptographic email signature valid? (DNS + crypto)
- DMARC        — did the domain owner authorise this email? (DNS lookup)
- Reply-To     — does reply-to domain match the from domain? (string comparison)
- Display Name — does display name match actual sending address? (brand list check)
- Sending IP   — reverse DNS on sending IP, flags unexpected origin (DNS + regex)

---

## Scoring Logic
# Points added per failed check. Score capped at 100.
# Thresholds determine the final verdict shown to the user.

SPF fail           = +25 pts  # critical — server not authorised
SPF not found      = +10 pts  # warning  — no record published
DKIM fail          = +20 pts  # critical — signature invalid or tampered
DKIM not found     = +8 pts   # warning  — no key published
DMARC fail         = +25 pts  # critical — domain disowning this email
DMARC not found    = +8 pts   # warning  — no policy set
Reply-To mismatch  = +15 pts  # high     — classic phishing indicator
Display name spoof = +10 pts  # medium   — impersonating known brand
Suspicious IP      = +10 pts  # medium   — private range or suspicious TLD

# Verdict thresholds
0  - 24  = LIKELY LEGITIMATE  (green)
25 - 54  = SUSPICIOUS         (amber)
55 - 100 = LIKELY PHISHING    (red)

---

## Output
# What the user sees on the results page after hitting Analyse

- Verdict banner  — Legitimate / Suspicious / Likely Phishing with colour coding
- Risk score      — numeric score out of 100, colour matches verdict
- Meta cards      — From, Reply-To, Sending IP, Domain extracted from header
- Auth check list — SPF, DKIM, DMARC, Reply-To, Display Name, IP with pass/fail badges
- Bar chart       — animated horizontal bars showing risk % per check
- New Analysis    — button that resets UI back to the input view

---

## File Structure
# Where everything lives in the project folder

```
email-header-analyzer/
├── app.py              # Flask app — routes, POST handler, calls analyzer.py
├── analyzer.py         # Core logic — header parsing, DNS lookups, scoring, verdict
├── templates/
│   ├── index.html      # Input page — textarea + analyse button
│   └── results.html    # Results page — verdict, meta cards, checks, bar chart
├── static/
│   └── style.css       # All styling — dark terminal aesthetic, IBM Plex fonts
├── requirements.txt    # pip dependencies: flask, dnspython, python-dotenv
├── .env                # environment variables (not committed to git)
├── .gitignore          # excludes .env, __pycache__, venv
└── CLAUDE.md           # this file — project context for Claude Code
```

---

## Sample Data for Testing
# Use these to test the tool and take portfolio screenshots

- Real anonymised phishing .eml files : https://github.com/rf-peixoto/phishing_pot
- Paste-and-test sample headers        : https://mxtoolbox.com/EmailHeaders.aspx
- Own spam folder                      : Gmail → open email → ⋮ → Show Original → copy all

---

## Requirements
# Install with: pip install -r requirements.txt

```
flask
dnspython
python-dotenv
```

---

## Run Locally
```bash
pip install -r requirements.txt
python app.py
# open http://localhost:5000
```

---

## Current Status
# Tick off as you build

DONE:
- [x] Working frontend prototype (ayaan-email-analyzer.html) with full UI + bar chart
- [x] Scoring logic defined and tested
- [x] CLAUDE.md written

TODO:
- [ ] Convert frontend to Flask app (app.py + templates/)
- [ ] Move JS parsing logic into Python analyzer.py
- [ ] Replace simulated checks with real dnspython DNS lookups
- [ ] Deploy to Render free tier (same as ClearRisk)
- [ ] Add README.md with screenshot for GitHub

---

## CV Bullet Point
# Copy this exactly onto the CV

"Developed a Python Flask web application that automates email header analysis —
performing live SPF, DKIM, and DMARC DNS validation, IOC extraction, and display
name spoof detection — producing a colour-coded phishing risk verdict to reduce
manual triage time."

---

## Interview Narrative
# Say this when asked about the project in interviews

"During my Mastercard virtual experience I was manually analysing phishing indicators
in email headers. I built this tool to automate that process — it runs the same DNS
checks a SOC analyst would do by hand, but in seconds, and presents it in a clear
verdict with a risk score."

---

## Links
- GitHub    : github.com/Ayaan0299 — repo: email-header-analyzer (create this)
- Portfolio : ayaan0299.github.io
- Email     : ayaanlatif691@outlook.com
