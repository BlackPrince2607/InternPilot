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

## ✦ System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    INTERNPILOT AI                        │
│                                                         │
│  ┌──────────────┐        ┌──────────────────────────┐   │
│  │  Next.js 14  │◄──────►│    FastAPI Backend        │   │
│  │  (Vercel)    │  REST  │    (Railway)              │   │
│  └──────────────┘        └────────────┬─────────────┘   │
│         │                             │                  │
│         │                   ┌─────────┼─────────┐        │
│         │                   ▼         ▼         ▼        │
│         │             Supabase   Claude API  Scraper     │
│         │              (DB+Auth)  (Anthropic) (Cron)     │
│         │                   │         │                  │
│         └───────────────────┘         │                  │
│              Auth + Data              │                  │
│                                       │                  │
│         ┌─────────────────────────────┘                  │
│         ▼                                                │
│   AI Features:                                          │
│   → Resume parsing  (extract skills, experience)        │
│   → Job matching    (score each listing 0-100%)         │
│   → Email drafting  (tone-aware cold email generation)  │
└─────────────────────────────────────────────────────────┘
```

---

## ✦ Project Structure

```
internpilot/
├── internpilot-backend/
│   ├── app/
│   │   ├── main.py              # FastAPI entry point + CORS config
│   │   ├── config.py            # Settings and env vars
│   │   ├── database.py          # Supabase client setup
│   │   ├── models/
│   │   │   ├── user.py          # User + profile schemas
│   │   │   └── job.py           # Job listing schemas
│   │   ├── routers/
│   │   │   ├── auth.py          # /auth/* endpoints
│   │   │   ├── jobs.py          # /jobs/* endpoints
│   │   │   ├── resume.py        # /resume/* endpoints
│   │   │   └── email.py         # /email/generate endpoint
│   │   ├── services/
│   │   │   ├── claude_service.py    # Anthropic API calls
│   │   │   ├── match_engine.py      # Scoring algorithm
│   │   │   ├── resume_parser.py     # PDF → structured JSON
│   │   │   └── scraper.py           # Internship scraping logic
│   │   └── scheduler.py         # APScheduler cron jobs
│   ├── requirements.txt
│   └── Procfile                 # Railway deploy config
│
└── internpilot-frontend/
    ├── app/
    │   ├── layout.tsx           # Root layout + auth provider
    │   ├── page.tsx             # Landing page
    │   ├── onboarding/          # Resume upload + preferences
    │   ├── discover/            # Job listings + match scores
    │   ├── email/               # AI email generator UI
    │   ├── tracker/             # Kanban drag-drop board
    │   └── profile/             # User settings + re-upload
    ├── components/
    │   ├── ui/                  # Reusable UI primitives
    │   ├── JobCard.tsx          # Listing card with match score
    │   ├── EmailPreview.tsx     # Generated email display
    │   └── KanbanBoard.tsx      # DnD tracker component
    ├── lib/
    │   ├── supabase.ts          # Supabase client
    │   └── api.ts               # Backend API helpers
    └── .env.local               # Environment variables
```

---

## ✦ Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- pnpm (`npm install -g pnpm`)
- Accounts on: Supabase · Anthropic · Railway · Vercel

### 1. Clone the repositories

```bash
git clone https://github.com/yourusername/internpilot-backend.git
git clone https://github.com/yourusername/internpilot-frontend.git
```

### 2. Backend setup

```bash
cd internpilot-backend

# Create virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# → Fill in: SUPABASE_URL, SUPABASE_KEY, ANTHROPIC_API_KEY
```

### 3. Frontend setup

```bash
cd internpilot-frontend

# Install dependencies
pnpm install

# Configure environment variables
cp .env.example .env.local
# → Fill in: VITE_SUPABASE_URL, VITE_SUPABASE_ANON_KEY, VITE_API_BASE_URL
```

### 4. Run locally

```bash
# Terminal 1 — Backend
cd internpilot-backend
uvicorn app.main:app --reload --port 8000

# Terminal 2 — Frontend
cd internpilot-frontend
pnpm dev
```

Open `http://localhost:3000` — you should see the InternPilot landing page.

---

## ✦ Environment Variables

### Backend (`internpilot-backend/.env`)

| Variable | Description |
|----------|-------------|
| `SUPABASE_URL` | Your Supabase project URL |
| `SUPABASE_SERVICE_KEY` | Supabase service role key (not anon key) |
| `ANTHROPIC_API_KEY` | Claude API key from console.anthropic.com |
| `SCRAPE_INTERVAL_HOURS` | How often to scrape jobs (default: 24) |

### Frontend (`internpilot-frontend/.env.local`)

| Variable | Description |
|----------|-------------|
| `VITE_SUPABASE_URL` | Supabase project URL |
| `VITE_SUPABASE_ANON_KEY` | Supabase anon/public key |
| `VITE_API_BASE_URL` | Your backend API URL ending with `/api/v1` |

---

## ✦ Key API Endpoints

```
POST  /auth/signup              → Register new user
POST  /auth/login               → Authenticate + get session

POST  /resume/upload            → Upload PDF, parse with Claude AI
GET   /resume/{user_id}         → Fetch parsed resume data

GET   /jobs/matches/{user_id}   → Get ranked job matches for user
POST  /jobs/scrape              → Trigger manual scrape (admin)

POST  /email/generate           → Generate cold email for job+user
```

---

## ✦ Database Schema

```sql
-- Users table (extends Supabase auth.users)
profiles (id, email, resume_url, parsed_skills[], experience_level, preferences, created_at)

-- Jobs table
jobs (id, title, company, location, description, skills_required[], source_url, scraped_at)

-- Applications table (Kanban state)
applications (id, user_id, job_id, status, notes, created_at, updated_at)

-- Generated emails
emails (id, user_id, job_id, tone, body, created_at)
```

---

## ✦ Deployment

### Deploy Backend → Railway

```bash
# Create Procfile in backend root
echo "web: uvicorn app.main:app --host 0.0.0.0 --port \$PORT" > Procfile

# Push to GitHub → Railway auto-deploys
git add . && git commit -m "feat: add Procfile" && git push
```

Then: Railway → New Project → Deploy from GitHub → Add env vars in Variables tab.

### Deploy Frontend → Vercel

Connect your `internpilot-frontend` GitHub repo to Vercel. Add the three env vars. Click deploy. Done in ~2 minutes.

---

## ✦ Roadmap

- [x] Resume PDF upload & Claude-powered parsing
- [x] Automated internship scraper with cron scheduling
- [x] AI match scoring engine (keyword-based v1)
- [x] Claude-powered cold email generator with tone selection
- [x] Kanban application tracker with drag-and-drop
- [x] Supabase auth + persistent user profiles
- [x] Full deployment on Railway + Vercel
- [ ] Semantic matching with Claude embeddings (v2)
- [ ] Email open-rate tracking integration
- [ ] Mobile-responsive UI polish
- [ ] Browser extension for one-click applications
- [ ] Referral system and college-based cohorts

---

## ✦ Why This Project Matters (for Recruiters)

This isn't a tutorial clone. This is a **production-grade SaaS** built from scratch:

- **End-to-end ownership** — database schema, API design, AI integration, frontend, CI/CD, and launch strategy were all designed and implemented independently
- **Real users** — 100+ signups, 500+ emails generated, validated with real college students
- **AI at the core** — Claude API is used for three distinct AI tasks (parsing, scoring, generation), not just bolted on as a gimmick
- **System thinking** — background cron jobs, RLS policies, CORS configuration, proper environment management — the fundamentals that separate serious projects from demos

> Resume line: *"Built and launched InternPilot AI — a full-stack SaaS (FastAPI + Next.js + Claude API) that matches CSE students to internships and generates personalized cold emails. 100+ users, 500+ emails generated."*

---

## ✦ Contributing

Pull requests are welcome. For major changes, open an issue first to discuss what you'd like to change.

```bash
# Fork the repo, create your feature branch
git checkout -b feature/your-feature-name

# Commit your changes
git commit -m "feat: describe your change"

# Push and open a PR
git push origin feature/your-feature-name
```

---

## ✦ License

Distributed under the MIT License. See `LICENSE` for more information.

---

<div align="center">

**Built with intention. Shipped with pride.**

[![GitHub stars](https://img.shields.io/github/stars/yourusername/internpilot?style=social)](https://github.com/yourusername/internpilot)
[![Twitter Follow](https://img.shields.io/twitter/follow/yourusername?style=social)](https://twitter.com/yourusername)

<br/>

<img src="https://capsule-render.vercel.app/api?type=waving&color=6c63ff&height=120&section=footer" />

</div>
