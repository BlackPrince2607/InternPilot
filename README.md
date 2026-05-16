<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=6c63ff&height=200&section=header&text=InternPilot%20AI&fontSize=72&fontColor=ffffff&fontAlignY=38&desc=Upload%20resume.%20Discover%20matches.%20Send%20the%20perfect%20cold%20email.&descAlignY=60&descSize=16&animation=fadeIn" />

<br/>

[![Live Demo](https://img.shields.io/badge/🚀%20Live%20Demo-internpilot.vercel.app-6c63ff?style=for-the-badge&logoColor=white)](https://internpilot.vercel.app)
[![Backend Status](https://img.shields.io/badge/Backend-Railway-0B0D0E?style=for-the-badge&logo=railway&logoColor=white)](https://railway.app)
[![Frontend](https://img.shields.io/badge/Frontend-Vercel-000000?style=for-the-badge&logo=vercel&logoColor=white)](https://vercel.com)
[![Powered by Claude](https://img.shields.io/badge/AI-Claude%20API-cc785c?style=for-the-badge&logo=anthropic&logoColor=white)](https://anthropic.com)

<br/>

> **InternPilot AI** is a full-stack SaaS platform that helps CSE students land internships faster.  
> Upload your resume → get matched to live opportunities → generate a personalized cold email in one click.

<br/>

![Users](https://img.shields.io/badge/Users-100%2B-43e97b?style=flat-square)
![Emails Generated](https://img.shields.io/badge/Emails%20Generated-500%2B-6c63ff?style=flat-square)
![Tech Stack](https://img.shields.io/badge/Stack-FastAPI%20·%20Next.js%20·%20Supabase-ff6584?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-facc6d?style=flat-square)

</div>

---

## ✦ What is InternPilot AI?

The internship hunt is broken. Students send generic applications to dozens of roles, hear nothing back, and burn weeks in the process.

**InternPilot AI fixes that.**

It parses your resume with AI, extracts your skills and experience, then continuously scrapes live internship listings and scores each one against your profile. When you find a match you love, it writes you a tailored cold email — in your tone, referencing your actual projects — ready to send in seconds.

This isn't a job board. It's an **AI-powered internship co-pilot**.

---

## ✦ Feature Overview

<table>
<tr>
<td width="50%" valign="top">

### 🧠 AI Resume Parser
Upload your PDF resume. Claude API extracts your skills, tech stack, projects, and experience level — structured and ready for matching.

### 🔍 Smart Job Matching
A scoring engine compares your parsed profile against live job listings and returns a ranked match score (0–100%) for every role.

### ✉️ One-Click Email Generator
Select a job. Pick a tone — Professional, Casual, or Concise. Claude generates a personalized cold email referencing your real skills and projects.

</td>
<td width="50%" valign="top">

### 📋 Kanban Application Tracker
Track your entire pipeline in a 5-column drag-and-drop board: Shortlisted → Emailed → Replied → Interviewing → Closed.

### 🕷️ Auto Job Scraper
A background cron job scrapes internship listings daily and populates the database — keeping opportunities always fresh.

### 🔐 Auth & Profiles
Supabase-powered authentication. Every user gets a persistent profile, parsed resume data, and preference settings.

</td>
</tr>
</table>

---

## ✦ Tech Stack

<div align="center">

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Frontend** | Next.js 14 · TypeScript · Tailwind CSS | React-based UI with SSR and app router |
| **Backend** | FastAPI · Python 3.11 · Pydantic | REST API with async request handling |
| **Database** | Supabase (PostgreSQL) | Auth + persistent storage + RLS policies |
| **AI Layer** | Claude API (Anthropic) | Resume parsing · match scoring · email generation |
| **Scraper** | BeautifulSoup4 · httpx | Daily internship data harvesting |
| **Scheduler** | APScheduler | Cron-based background job runner |
| **File Parsing** | PyMuPDF (fitz) | PDF resume extraction |
| **Deploy — Backend** | Railway | Containerised FastAPI hosting + cron |
| **Deploy — Frontend** | Vercel | Next.js edge deployment |
| **Email (optional)** | Resend | User digest email delivery |
| **State Management** | Zustand | Lightweight React global state |
| **DnD** | @dnd-kit | Accessible drag-and-drop for Kanban |

</div>

---

## Repository Layout

```text
InternPilot/
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── context/AuthContext.jsx
│   │   ├── lib/{api.js,supabase.js}
│   │   ├── components/
│   │   └── pages/
│   └── package.json
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── scheduler.py
│   │   ├── api/v1/
│   │   ├── services/
│   │   ├── scraper/
│   │   └── dependencies/
│   ├── migrations/
│   └── requirements.txt
├── ARCHITECTURE.md
└── CONTEXT.md
```

## Main Features

### Resume Upload and Parsing

- Upload PDF resumes to Supabase Storage
- Extract text using pdfplumber
- Parse structured candidate data with Groq
- Persist extracted payload in the resumes table

### Preference-Aware Matching

- Save role, location, domain, and stipend preferences
- Retrieve active jobs from the jobs table
- Rank with profile scoring + semantic retrieval
- Return strict matches and near matches

### Cold Email Assistant

- Generate personalized cold emails from resume + job context
- Choose tone: professional, friendly, confident, casual
- Save generated emails and mark sent status
- View history in reverse chronological order

### Tracker

- Record application actions
- Aggregate jobs applied count
- Aggregate emails sent count

### Job Ingestion and Scheduler

- Periodic ingestion pipeline using APScheduler
- Multi-source scraping and cleaning pipeline
- Deduplication, domain classification, and embeddings
- Company contact crawl for likely email enrichment

### Image Generation Endpoint

- Prompt-based image generation endpoint exists
- Current default provider path returns placeholder image data URIs
- Can persist metadata when generated_images table is present

## API Routes (Current)

All routes are mounted under /api/v1.

### Auth

- GET /auth/me

### Resumes

- POST /resumes/upload
- POST /resumes/parse/{resume_id}
- GET /resumes/{resume_id}

### Preferences

- POST /preferences/save
- GET /preferences/me

### Jobs and Matches

- GET /jobs/
- GET /matches/
- GET /matches
- GET /matches/debug/stats

### Cold Email

- POST /cold-email/generate
- POST /cold-email/record-sent
- GET /cold-email/history

### Tracker

- POST /tracker/record-apply
- GET /tracker/stats

### Admin

- POST /admin/trigger-scrape
- GET /admin/scraper-status

### Images

- POST /images/generate

## Local Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- A Supabase project
- A Groq API key

### 1. Install backend dependencies

```bash
cd backend
python -m venv .venv

# PowerShell
.\.venv\Scripts\Activate.ps1

pip install -r requirements.txt
```

### 2. Configure backend environment

Create backend/.env with at least:

```env
SUPABASE_URL=...
SUPABASE_KEY=...
GROQ_API_KEY=...
SUPABASE_RESUMES_BUCKET=resumes
```

Optional backend envs:

```env
APP_CORS_ORIGINS=http://localhost:5173
SCRAPER_INTERVAL_HOURS=6
SCRAPER_INITIAL_DELAY_MINUTES=10
ADMIN_EMAIL=
IMAGE_GENERATION_ENABLED=true
IMAGE_PROVIDER=placeholder
IMAGE_PROVIDER_API_KEY=
ADZUNA_APP_ID=
ADZUNA_APP_KEY=
```

### 3. Run migrations in Supabase

Run SQL from:

- backend/migrations/001_add_new_tables.sql
- backend/migrations/002_group2_backend_fixes.sql

### 4. Start backend

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

Backend health check:

- GET http://localhost:8000/

### 5. Install frontend dependencies

```bash
cd frontend
npm install
```

### 6. Configure frontend environment

Create frontend/.env with:

```env
VITE_SUPABASE_URL=...
VITE_SUPABASE_ANON_KEY=...
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

### 7. Start frontend

```bash
cd frontend
npm run dev
```

Open:

- http://localhost:5173

## Architecture and Context Docs

For deeper implementation details, see:

- ARCHITECTURE.md
- CONTEXT.md

These two files are intended to stay synchronized with the actual code.

## Known Product Notes

- Tracker currently provides aggregate counts, not a full Kanban state board.
- Image generation currently defaults to placeholder output unless provider integration is enabled.
- Scheduler runs inside backend app lifespan; deploy with care to avoid duplicate scheduler instances.

## Contributing

1. Keep README, ARCHITECTURE.md, and CONTEXT.md in sync with behavior changes.
2. Add or update migration SQL when backend schema assumptions change.
3. Preserve API response envelope shape unless frontend changes are included.

## License

No license file is currently included in this repository.
