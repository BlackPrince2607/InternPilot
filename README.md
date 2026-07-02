<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=6c63ff&height=200&section=header&text=InternPilot%20AI&fontSize=72&fontColor=ffffff&fontAlignY=38&desc=Upload%20resume.%20Discover%20matches.%20Send%20the%20perfect%20cold%20email.&descAlignY=60&descSize=16&animation=fadeIn" />

<br/>

[![Live Demo](https://img.shields.io/badge/Live%20Demo-internpilot.vercel.app-6c63ff?style=for-the-badge&logoColor=white)](https://internpilot.vercel.app)
[![Backend Status](https://img.shields.io/badge/Backend-Railway-0B0D0E?style=for-the-badge&logo=railway&logoColor=white)](https://railway.app)
[![Frontend](https://img.shields.io/badge/Frontend-Vercel-000000?style=for-the-badge&logo=vercel&logoColor=white)](https://vercel.com)
[![AI](https://img.shields.io/badge/AI-Groq%20Llama%203.3-orange?style=for-the-badge)](https://groq.com)

<br/>

> **InternPilot AI** is a full-stack internship assistant for students.
> Upload your resume, get ranked against live listings, generate tailored cold emails, and track outreach — all in one place.

<br/>

![Tech Stack](https://img.shields.io/badge/Stack-FastAPI%20%C2%B7%20React%20%C2%B7%20Vite%20%C2%B7%20Supabase-ff6584?style=flat-square)
![Repo](https://img.shields.io/badge/GitHub-BlackPrince2607%2FInternPilot-6c63ff?style=flat-square)

</div>

---

## What is InternPilot AI?

The internship hunt is broken. Students send generic applications to dozens of roles, hear nothing back, and burn weeks in the process.

**InternPilot AI fixes that.**

It parses your resume with Groq (Llama 3.3), extracts skills and experience, ingests live internship listings from multiple sources, and ranks each role against your profile using semantic retrieval plus rule-based scoring. When you find a match you love, it writes a tailored cold email — in your tone, referencing your actual projects — ready to send in seconds.

This isn't a job board. It's an **AI-powered internship co-pilot**.

---

## Feature Overview

<table>
<tr>
<td width="50%" valign="top">

### AI Resume Parser
Upload a PDF resume. Groq extracts skills, tech stack, projects, and experience level into structured data ready for matching.

### Preference-Aware Matching
Save role, location, domain, and stipend preferences. The engine retrieves active jobs and returns strict matches and near matches with score breakdowns.

### One-Click Cold Email
Pick a job and a tone — professional, friendly, confident, or casual. Groq generates a personalized email referencing your real skills and projects.

</td>
<td width="50%" valign="top">

### Application Tracker
Record apply events and view aggregate stats — jobs applied and emails sent — to stay on top of your pipeline.

### Live Job Ingestion
APScheduler runs a multi-source scraping pipeline on a configurable interval. Jobs are cleaned, deduplicated, classified, and embedded for semantic retrieval.

### Image Generation (experimental)
Prompt-based image endpoint with a placeholder provider by default. Metadata is persisted when the `generated_images` table is present.

</td>
</tr>
</table>

---

## Tech Stack

<div align="center">

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Frontend** | React 19 · Vite · Tailwind CSS 4 · React Router | SPA deployed on Vercel |
| **Backend** | FastAPI · Python · Pydantic v2 | REST API with async handlers |
| **Database** | Supabase (Postgres) | Auth, storage, RLS |
| **AI Layer** | Groq (Llama 3.3) + sentence-transformers | Resume parsing · cold email · semantic match |
| **Ingestion** | httpx · BeautifulSoup · Playwright · APScheduler | Multi-source job harvesting |
| **File Parsing** | pdfplumber | PDF resume text extraction |
| **Deploy — Backend** | Railway | Containerised FastAPI + in-process scheduler |
| **Deploy — Frontend** | Vercel | Static SPA |

</div>

---

## System Architecture

```text
┌─────────────────────────────────────────────────────────────┐
│                      INTERNPILOT AI                          │
│                                                             │
│  ┌──────────────┐        ┌─────────────────────────────┐   │
│  │  React+Vite  │◄──────►│   FastAPI API (Railway)      │   │
│  │  (Vercel)    │  REST  │   - 9 /api/v1/* routers      │   │
│  └──────────────┘        │   - APScheduler (6h default) │   │
│         │                └──────────┬──────────────────┘   │
│         │                           │                       │
│         │                  ┌────────┼────────┐              │
│         │                  ▼        ▼        ▼              │
│         │              Supabase  Groq LLM  Embeddings        │
│         │              (DB+Auth+          (sentence-         │
│         │               Storage)          transformers)      │
└─────────────────────────────────────────────────────────────┘
```

See [ARCHITECTURE.md](ARCHITECTURE.md) and [CONTEXT.md](CONTEXT.md) for the live implementation reference.

---

## Project Structure

```text
InternPilot/
├── frontend/
│   ├── src/
│   │   ├── App.jsx                  # Routes: onboarding, matches, cold-email, tracker, images
│   │   ├── components/              # Matches, ColdEmail, Tracker, ResumeUploader, …
│   │   ├── components/layout/       # AppLayout, Navbar
│   │   ├── context/AuthContext.jsx
│   │   ├── lib/{api.js,supabase.js}
│   │   └── pages/                   # Onboarding, Preferences, Images
│   └── package.json
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI entry + CORS + scheduler lifespan
│   │   ├── scheduler.py             # APScheduler ingestion cycle
│   │   ├── api/v1/                  # 9 route modules
│   │   ├── services/                # match_engine, retrieval, resume_parser, …
│   │   ├── scraper/                 # sources + career_crawler
│   │   └── dependencies/
│   ├── migrations/                  # 001, 002 SQL files
│   └── requirements.txt
├── ARCHITECTURE.md
└── CONTEXT.md
```

---

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- A Supabase project
- A Groq API key

### 1. Clone

```bash
git clone https://github.com/BlackPrince2607/InternPilot.git
cd InternPilot
```

### 2. Backend

```bash
cd backend
python -m venv .venv

# macOS / Linux
source .venv/bin/activate

# Windows PowerShell
.\.venv\Scripts\Activate.ps1

pip install -r requirements.txt
```

Create `backend/.env`:

```env
SUPABASE_URL=...
SUPABASE_KEY=...
GROQ_API_KEY=...
SUPABASE_RESUMES_BUCKET=resumes
APP_CORS_ORIGINS=http://localhost:5173
SCRAPER_INTERVAL_HOURS=6
```

Apply migrations in the Supabase SQL editor:

- `backend/migrations/001_add_new_tables.sql`
- `backend/migrations/002_group2_backend_fixes.sql`

Start the API:

```bash
uvicorn app.main:app --reload --port 8000
```

Health check: `GET http://localhost:8000/`

### 3. Frontend

```bash
cd frontend
npm install
```

Create `frontend/.env`:

```env
VITE_SUPABASE_URL=...
VITE_SUPABASE_ANON_KEY=...
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

```bash
npm run dev
```

Open [http://localhost:5173](http://localhost:5173).

---

## Environment Variables

### Backend (required)

| Variable | Description |
|----------|-------------|
| `SUPABASE_URL` | Supabase project URL |
| `SUPABASE_KEY` | Supabase **service-role** key (backend only) |
| `GROQ_API_KEY` | Groq API key |
| `SUPABASE_RESUMES_BUCKET` | Storage bucket name for resumes (default: `resumes`) |

### Backend (optional)

| Variable | Description |
|----------|-------------|
| `APP_CORS_ORIGINS` | Comma-separated allowed origins |
| `SCRAPER_INTERVAL_HOURS` | Ingestion interval (default: `6`) |
| `SCRAPER_INITIAL_DELAY_MINUTES` | Delay before first scrape |
| `ADMIN_EMAIL` | Admin user email for scrape triggers |
| `IMAGE_GENERATION_ENABLED` | Enable image endpoint |
| `IMAGE_PROVIDER` | Image provider (`placeholder` by default) |
| `ADZUNA_APP_ID` / `ADZUNA_APP_KEY` | Adzuna job source credentials |

### Frontend

| Variable | Description |
|----------|-------------|
| `VITE_SUPABASE_URL` | Supabase project URL |
| `VITE_SUPABASE_ANON_KEY` | Supabase anon/public key |
| `VITE_API_BASE_URL` | Backend API base URL |

---

## Key API Endpoints

All routes live under `/api/v1`. Protected routes require a Supabase Auth bearer token.

```text
GET  /api/v1/auth/me                    Current user profile

POST /api/v1/resumes/upload             Upload PDF resume
POST /api/v1/resumes/parse/{resume_id}  Parse PDF with Groq
GET  /api/v1/resumes/{resume_id}        Fetch parsed resume

POST /api/v1/preferences/save           Save preferences
GET  /api/v1/preferences/me             Get preferences

GET  /api/v1/jobs/                      List active jobs
GET  /api/v1/matches                    Ranked internship matches
GET  /api/v1/matches/debug/stats        Match pipeline debug stats

POST /api/v1/cold-email/generate        Generate tailored cold email
POST /api/v1/cold-email/record-sent     Mark email as sent
GET  /api/v1/cold-email/history         Email history

POST /api/v1/tracker/record-apply       Record an application
GET  /api/v1/tracker/stats              Aggregate tracker stats

POST /api/v1/admin/trigger-scrape       Trigger manual scrape (admin)
GET  /api/v1/admin/scraper-status       Scraper status (admin)

POST /api/v1/images/generate            Prompt-based image generation

GET  /                                    API liveness
```

---

## Deployment

### Backend → Railway

```bash
# Procfile in backend/
web: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Connect the repo to Railway, set the backend env vars, and deploy from the `backend/` directory.

> **Note:** The scheduler runs inside the API process lifespan. Run a single backend instance in production to avoid duplicate scrape jobs.

### Frontend → Vercel

Connect [BlackPrince2607/InternPilot](https://github.com/BlackPrince2607/InternPilot) to Vercel, set the root directory to `frontend/`, add the `VITE_*` env vars, and deploy.

---

## Known Product Notes

- Tracker currently provides aggregate counts, not a full Kanban board.
- Image generation defaults to placeholder output unless a provider is configured.
- Scheduler runs inside the backend app lifespan — avoid running multiple API replicas with the scheduler enabled.

---

## Contributing

Pull requests are welcome. For major changes, open an issue first.

```bash
git checkout -b feature/your-feature-name
git commit -m "feat: describe your change"
git push origin feature/your-feature-name
```

Keep [README.md](README.md), [ARCHITECTURE.md](ARCHITECTURE.md), and [CONTEXT.md](CONTEXT.md) in sync with behavior changes.

---

## License

No license file is currently included in this repository.

---

<div align="center">

**Built with intention. Shipped with pride.**

[![GitHub](https://img.shields.io/badge/GitHub-BlackPrince2607-6c63ff?style=social)](https://github.com/BlackPrince2607/InternPilot)

<img src="https://capsule-render.vercel.app/api?type=waving&color=6c63ff&height=120&section=footer" />

</div>
