# 🏙️ SustainCity AI

> **Building Smarter, Greener, and More Accountable Indian Cities using Artificial Intelligence**

A full-stack AI-powered urban civic intelligence platform that bridges the communication gap between citizens and local government authorities. Citizens report infrastructure issues via image upload; the backend uses Google Gemini 2.5 Flash to visually classify the issue, calculate severity, auto-route complaints to the correct municipal department, and generate a contextual description — all in real time.

Built as part of the **1M1B AI for Sustainability Virtual Internship** in collaboration with **IBM SkillsBuild & AICTE**.

---

## 📋 Table of Contents

- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Database Schema](#-database-schema)
- [Getting Started](#-getting-started)
- [Environment Variables](#-environment-variables)
- [Routes Reference](#-routes-reference)
- [AI Pipeline](#-ai-pipeline)
- [SDG Alignment](#-sdg-alignment)
- [Production Notes](#-production-notes)

---

## ✨ Features

- **Live Gemini vision pipeline** — uploaded images are sent directly to Gemini 2.5 Flash via `types.Part.from_bytes`, which returns structured JSON with issue type, confidence score, severity, department ID, and a contextual abstract
- **Dual location input** — citizens choose between manual Indian address entry or live GPS coordinates via the browser Geolocation API
- **Auto-routing to departments** — complaints are automatically assigned to Roads, Water Supply, Garbage & Sanitation, or Streetlights & Electricity based on AI output
- **Public transparency dashboard** — real-time civic metrics: total incidents, urgent open issues, water saved, and landfill waste prevented
- **Department management panel** — session-gated staff workspace to review and update complaint status (Pending → Assigned → In Progress → Resolved)
- **Civic AI knowledge assistant** — live Gemini-powered chat for citizen questions on waste segregation, water conservation, and municipal guidelines
- **Secure configuration** — all secrets (API key, DB credentials, Flask secret) loaded from `.env` via `python-dotenv`
- **WSGI-ready** — includes `wsgi.py` for deployment on Gunicorn or any WSGI server

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Backend framework | Python Flask |
| Database | MySQL (`sustaincity_db`) |
| AI engine | Google Gemini 2.5 Flash (`google-genai` SDK) |
| Frontend | HTML5, CSS3, Vanilla JS, Jinja2 templates |
| File handling | Werkzeug `secure_filename` |
| Session management | Flask session (server-side) |
| Config management | `python-dotenv` (.env file) |
| Geolocation | Browser `navigator.geolocation` API |
| Deployment | `wsgi.py` (Gunicorn-compatible) |

---

## 📁 Project Structure

```
SustainCity-AI/
│
├── app.py                        # Main backend — all routes, live AI pipeline, DB helpers
├── wsgi.py                       # WSGI entry point for production deployment
├── schema.sql                    # MySQL table definitions + department seed data
├── requirements.txt              # Python dependencies
├── .env                          # Secret config (never commit this to Git)
│
├── static/
│   ├── css/
│   │   └── style.css             # Global Green Tech design skin
│   └── uploads/                  # Citizen-submitted images (auto-created on startup)
│
└── templates/
    ├── index.html                # Landing page — nav cards & project overview
    ├── complaint.html            # Citizen intake form — image + location
    ├── knowledge_assistant.html  # Civic AI chat interface
    ├── public_dashboard.html     # Public transparency analytics
    ├── login.html                # Department staff authentication
    └── department_panel.html     # Staff incident management workspace
```

---

## 🗄️ Database Schema

### `departments`
| Field | Type | Notes |
|---|---|---|
| id | INT AUTO_INCREMENT | Primary key |
| dept_username | VARCHAR(50) | Unique login credential |
| dept_password | VARCHAR(255) | ⚠️ Plaintext — hash before production |
| dept_name | VARCHAR(100) | Display name shown in panel header |

### `complaints`
| Field | Type | Notes |
|---|---|---|
| id | INT AUTO_INCREMENT | Primary key |
| image_filename | VARCHAR(255) | Saved in `static/uploads/` |
| full_address | TEXT NULL | Manual address entry — NULL if GPS used |
| latitude | DECIMAL(10,8) | Browser GPS lat — NULL if manual |
| longitude | DECIMAL(11,8) | Browser GPS lng — NULL if manual |
| detected_issue | VARCHAR(100) | Gemini output e.g. "Pothole", "Sewage Overflow" |
| confidence_score | INT | AI confidence 0–100 |
| severity | ENUM | `Low` / `Medium` / `High` |
| assigned_department_id | INT (FK) | → `departments.id` ON DELETE SET NULL |
| complaint_abstract | TEXT | Gemini-generated contextual description |
| status | ENUM | `Pending` / `Assigned` / `In Progress` / `Resolved` |
| created_at | TIMESTAMP | AUTO — set on insert |

### Seeded departments

| Department | Username | Default Password |
|---|---|---|
| Potholes & Roads | `roads_admin` | `roads2026` |
| Water Supply & Sewage | `water_admin` | `water2026` |
| Garbage & Sanitation | `sanitation_admin` | `clean2026` |
| Streetlights & Electricity | `electric_admin` | `power2026` |

---

## 🚀 Getting Started

### Prerequisites

- Python 3.9+
- MySQL Server running locally
- A Google Gemini API key from [Google AI Studio](https://aistudio.google.com/)

### 1. Clone the repository

```bash
git clone https://github.com/your-username/sustaincity-ai.git
cd sustaincity-ai
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv
source venv/bin/activate        # macOS/Linux
venv\Scripts\activate           # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up the database

```bash
mysql -u root -p < schema.sql
```

### 5. Create your `.env` file

```bash
cp .env.example .env   # or create it manually (see below)
```

Fill in your values — see [Environment Variables](#-environment-variables).

### 6. Run the development server

```bash
python app.py
```

Visit `http://127.0.0.1:5000` in your browser.

### 7. Run with Gunicorn (production)

```bash
gunicorn --bind 0.0.0.0:8000 wsgi:app
```

---

## 🔐 Environment Variables

Create a `.env` file in the project root. **Never commit this file to Git.**

```env
# Flask
FLASK_SECRET_KEY=your_random_secret_key_here

# Google Gemini
GEMINI_API_KEY=your_gemini_api_key_here

# MySQL Database
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=sustaincity_db
```

Add `.env` to your `.gitignore`:

```gitignore
.env
static/uploads/
__pycache__/
venv/
```

---

## 🔌 Routes Reference

| Method | Route | Description | Auth |
|---|---|---|---|
| GET | `/` | Landing page | None |
| GET | `/complaint` | Renders complaint form | None |
| POST | `/complaint` | Saves image, runs Gemini pipeline, writes to DB | None |
| GET | `/public-dashboard` | Live civic analytics + full complaints log | None |
| GET | `/login` | Renders staff login form | None |
| POST | `/login` | Authenticates department, sets session | None |
| GET | `/department-panel` | Staff incident management workspace | Session |
| POST | `/update-status` | Updates complaint status (dept-owned only) | Session |
| GET | `/logout` | Clears session, redirects to login | Session |
| GET | `/knowledge-assistant` | Renders AI chat interface | None |
| POST | `/api/chat` | Live Gemini civic chat endpoint (JSON) | None |
| GET | `/admin` | Admin view of all complaints | None |

---

## 🤖 AI Pipeline

### Complaint classification (`POST /complaint`)

```
Citizen uploads image + location
        │
        ▼
secure_filename → saved to static/uploads/
        │
        ▼
run_live_gemini_analysis(image_path, location_context)
        │
        ├── Reads image bytes
        ├── Sends types.Part.from_bytes + structured prompt to gemini-2.5-flash
        ├── Requests response_mime_type = "application/json"
        └── Returns parsed JSON:
              {
                "detected_issue": "Pothole",
                "confidence_score": 95,
                "severity": "High",
                "assigned_department_id": 1,
                "complaint_abstract": "..."
              }
        │
        ▼
INSERT INTO complaints (all AI fields + location + filename)
        │
        ▼
Redirect → /public-dashboard
```

**Department ID mapping used in the Gemini prompt:**

| ID | Department |
|---|---|
| 1 | Potholes & Roads |
| 2 | Water Supply & Sewage |
| 3 | Garbage & Sanitation |
| 4 | Streetlights & Electricity |

### Knowledge assistant (`POST /api/chat`)

Receives `{ "message": "..." }` → calls `gemini-2.5-flash` with a civic sustainability system instruction → returns `{ "reply": "..." }`. Stateless per request (no conversation history stored).

---

## 🌍 SDG Alignment

| SDG | Goal | How SustainCity AI contributes |
|---|---|---|
| **SDG 11** | Sustainable Cities & Communities | Faster complaint resolution reduces urban infrastructure hazards; public dashboard provides transparency |
| **SDG 6** | Clean Water & Sanitation | Water leakage complaints routed to Water Supply dept; dashboard tracks litres saved |
| **SDG 12** | Responsible Consumption & Production | Garbage complaints aggregated into waste-diversion metrics (5.1 Tons tracked) |

---

## ⚠️ Production Notes

**1. Plaintext passwords in DB**
Passwords are stored as raw strings. Before any deployment:
```python
from werkzeug.security import generate_password_hash, check_password_hash
# Hash on insert, check_password_hash on login
```

**2. Non-unique image filenames**
`secure_filename` preserves original names — two uploads of `photo.jpg` overwrite each other. Fix:
```python
import uuid
filename = uuid.uuid4().hex + "_" + secure_filename(file.filename)
```

**3. Missing `admin_dashboard.html`**
The `/admin` route calls `render_template('admin_dashboard.html')` but that template is not in the project. Visiting `/admin` will raise a `TemplateNotFound` error until the template is created.

**4. No CSRF protection**
Forms have no CSRF tokens. Add `flask-wtf` for production:
```bash
pip install flask-wtf
```

**5. Plaintext password comparison in login**
The login route compares passwords directly via SQL. Once hashing is added to the DB, update the login query to fetch by username only, then use `check_password_hash`.

**6. Debug mode on in production**
`app.run(debug=True)` exposes the Werkzeug debugger publicly. Use `debug=False` or let `wsgi.py` handle startup instead.

---

## 📄 License

This project was created for educational purposes as part of the 1M1B AI for Sustainability Virtual Internship (IBM SkillsBuild & AICTE).

---

*SustainCity AI © 2026 • Made in India for Sustainable Municipal Development*
