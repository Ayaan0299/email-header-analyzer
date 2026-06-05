
<div align="center">

[![Typing SVG](https://readme-typing-svg.demolab.com?font=Fira+Code&size=32&duration=3000&pause=1000&color=448AFF&center=true&vCenter=true&width=800&lines=Email+Header+Analyst;Automated+Phishing+Detection;SPF+DKIM+DMARC+Validation;Built+for+SOC+Automation)](https://git.io/typing-svg)

<br/>

![Python](https://img.shields.io/badge/Python-3.10+-448aff?style=for-the-badge&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.x-00e676?style=for-the-badge&logo=flask&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-Database-ffab00?style=for-the-badge&logo=sqlite&logoColor=white)
![Security+](https://img.shields.io/badge/CompTIA-Security%2B-ff3d5a?style=for-the-badge&logo=comptia&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-448aff?style=for-the-badge)

<br/>

**Automated phishing detection tool**  
Paste a raw email header, get a risk verdict in seconds. Built to automate SOC triage work.

</div>

---

## 🎯 What This Project Does

When a suspicious email is reported, analysts manually inspect raw headers including SPF, DKIM, DMARC, sending IP and reply routes.

This tool automates that entire process.

### Modes
- Manual mode: paste raw email header and get instant analysis
- Pipeline mode: batch process phishing emails and store results in SQLite with dashboard metrics

---

## ✨ Features

- 🔍 SPF, DKIM and DMARC validation using DNS lookups  
- 🌍 IP geolocation mapping with world visualisation  
- 📊 Live dashboard with charts and detection stats  
- 🚨 Risk scoring system from 0 to 100  
- 🗄️ SQLite logging for all analysed emails  
- 📋 Protocol breakdown per email  
- 🎨 Space themed UI with animated background  

---

## 🔬 How It Works

```

User pastes email header
↓
Flask parses header fields
↓
DNS checks run (SPF, DKIM, DMARC)
↓
Header analysis rules applied
↓
Risk score generated (0 to 100)
↓
Verdict assigned
↓
Stored in SQLite database
↓
Dashboard updates in real time

````

---

## 🛡️ Security Checks

| Check | Method | Penalty |
|------|--------|--------|
| SPF | DNS authorisation check | High |
| DKIM | Signature validation | High |
| DMARC | Policy enforcement | High |
| Reply-To | Domain mismatch detection | Medium |
| Display Name | Spoof detection | Medium |
| Sending IP | Reverse DNS validation | Medium |

### Verdict Levels

| Score | Result |
|------|--------|
| 0 to 24 | Legitimate |
| 25 to 54 | Suspicious |
| 55 to 100 | Phishing |

---

## 🧰 Tech Stack

| Layer | Tech |
|------|------|
| Backend | Python, Flask |
| DNS | dnspython |
| Database | SQLite |
| Parsing | Python email library |
| Geolocation | ip-api |
| Frontend | HTML, CSS, JavaScript |
| Charts | Chart.js |
| Map | Leaflet.js |

---

## 🚀 Quick Start

### 1. Clone repo
```bash
git clone https://github.com/Ayaan0299/email-header-analyzer.git
cd email-header-analyzer
````

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Setup environment

```bash
cp .env.example .env
```

### 4. Run app

```bash
python3 app.py
```

### 5. Open browser

```
http://localhost:5000
```

### 6. Dashboard

```
http://localhost:5000/dashboard
```

---

## 📁 Project Structure

```
email-header-analyzer/
├── app.py
├── analyzer.py
├── database.py
├── alerts.py
├── sender.py
├── templates/
├── static/
├── data/
├── requirements.txt
├── .env.example
└── README.md
```

---

## 🧪 Testing Dataset

Uses phishing_pot dataset (real phishing emails)

```bash
git clone https://github.com/rf-peixoto/phishing_pot.git
cp phishing_pot/email/*.eml data/samples/
python3 sender.py
```

---

## 📊 Dashboard Metrics

* Total emails analysed
* Phishing detected
* Suspicious emails
* Detection rate
* World map of email origins
* SPF/DKIM/DMARC pass rates

---

## 📜 Environment Variables

```env
MAILTRAP_SMTP_HOST=sandbox.smtp.mailtrap.io
MAILTRAP_SMTP_PORT=2525
MAILTRAP_USER=your-user
MAILTRAP_PASSWORD=your-password

MAILTRAP_API_TOKEN=your-token
MAILTRAP_INBOX_ID=your-inbox

ALERT_EMAIL=your-email@gmail.com
```

---

## 🔗 Use Cases

| Role                   | Use                               |
| ---------------------- | --------------------------------- |
| SOC Analyst            | Automates phishing triage         |
| GRC Analyst            | Email security control validation |
| Cyber Security Analyst | Threat detection pipeline         |

---

```

