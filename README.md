<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=6c63ff&height=200&section=header&text=InternPilot%20AI&fontSize=72&fontColor=ffffff&fontAlignY=38&desc=Upload%20resume.%20Discover%20matches.%20Send%20the%20perfect%20cold%20email.&descAlignY=60&descSize=16&animation=fadeIn" />

<br/>

[![Live Demo](https://img.shields.io/badge/Live%20Demo-internpilot.vercel.app-6c63ff?style=for-the-badge&logoColor=white)](https://internpilot.vercel.app)
[![Backend Status](https://img.shields.io/badge/Backend-Railway-0B0D0E?style=for-the-badge&logo=railway&logoColor=white)](https://railway.app)
[![Frontend](https://img.shields.io/badge/Frontend-Vercel-000000?style=for-the-badge&logo=vercel&logoColor=white)](https://vercel.com)
[![AI](https://img.shields.io/badge/AI-Groq%20Llama%203.3-orange?style=for-the-badge)](https://groq.com)

<br/>

> **InternPilot AI** is a full-stack SaaS that helps students land internships faster.
> Upload your resume, get ranked against live internship listings using a personalized matching pipeline,
> and generate a tailored cold email in one click.

<br/>

![Tech Stack](https://img.shields.io/badge/Stack-FastAPI%20%C2%B7%20React%20%C2%B7%20Vite%20%C2%B7%20Supabase%20%C2%B7%20pgvector-ff6584?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-facc6d?style=flat-square)

</div>

---

## What is InternPilot AI?

The internship hunt is broken. Students send generic applications to dozens of roles, hear nothing back, and burn weeks in the process.

**InternPilot AI fixes that.**

It parses your resume with an LLM, extracts your skills and experience, continuously ingests live internship listings from 9+ sources, and ranks each one against your profile using a pgvector ANN retrieval pipeline plus a behavioral ranker. When you find a match you love, it writes you a tailored cold email — in your tone, referencing your actual projects — ready to send in seconds.

This isn't a job board. It's an **AI-powered internship co-pilot**.

---

## Feature Overview

<table>
<tr>
<td width="50%" valign="top">

### AI Resume Parser
Upload your PDF resume. Groq (Llama 3.3 70B) extracts your skills, tech stack, projects, and experience level — structured and ready for matching.

### Personalized Match Ranking
A multi-stage pipeline (pgvector ANN retrieval, MatchEngine scoring, MMR diversity, behavior re-rank) returns ranked internships with skill / project / experience / semantic-similarity breakdowns, missing-skill callouts, and a confidence tier.

### One-Click Cold Email Generator
Pick a job. Pick a tone — Professional, Casual, or Concise. Groq generates a personalized cold email referencing your real skills and projects.

</td>
<td width="50%" valign="top">

### Today Workspace
A daily dashboard with priority actions, overdue follow-ups, activation score, and an in-app notification bell for new match alerts.

### Application Tracker (Kanban)
Track your entire pipeline through Shortlisted → Applied → Interviewing → Offered → Rejected with timeline events and CRM insights.

### Live Job Ingestion + Worker
A separate worker process scrapes Internshala / LinkedIn / Wellfound and fetches Remotive / RemoteOK / YC / Greenhouse / Lever / Adzuna every 6 hours, dedupes them, and embeds them into pgvector for ANN retrieval.

</td>
</tr>
</table>

---

## Tech Stack

<div align="center">

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Frontend** | React 19 · Vite · Tailwind CSS 4 · TanStack Query | SPA with React Router 6 |
| **Backend** | FastAPI · Python 3.13 · Pydantic | REST API + worker process |
| **Database** | Supabase (Postgres + pgvector) | Auth, storage, RLS, ANN retrieval |
| **AI Layer** | Groq (Llama 3.3 70B) + sentence-transformers (`all-MiniLM-L6-v2`) | Resume parsing · cold email · AI coach · semantic match |
| **Ingestion** | httpx · BeautifulSoup · Playwright · APScheduler | 9+ sources, every 6h |
| **Ranking** | pgvector ANN · MMR diversity · behavior + negative profile | Personalized match scoring |
| **File Parsing** | pdfplumber | PDF resume extraction |
| **Deploy — Backend** | Railway / Docker (`api` + `worker`) | Split process model |
| **Deploy — Frontend** | Vercel | Static SPA (`vercel.json` rewrites) |
| **Billing** | Stripe | B2C Pro subscription with webhook idempotency |
| **Email** | Resend (optional) | Weekly digest, follow-up reminders, new-match alerts |
| **Analytics** | PostHog (optional) | Product events + funnels |
| **Error Tracking** | Sentry (optional) | Frontend + FastAPI integration |

</div>

---

## System Architecture

```text
┌──────────────────────────────────────────────────────────────┐
│                       INTERNPILOT AI                          │
│                                                              │
│  ┌──────────────┐        ┌──────────────────────────────┐    │
│  │  React+Vite  │◄──────►│   FastAPI API (Railway)       │    │
│  │  (Vercel)    │  REST  │   - 16 /api/v1/* routers      │    │
│  └──────────────┘        │   - Rate limits + plan tiers  │    │
│         │                └──────────┬────────────────────┘    │
│         │                           │                          │
│         │                  ┌────────┼────────────┐             │
│         │                  ▼        ▼            ▼             │
│         │            Supabase   Groq LLM    Stripe             │
│         │            (DB+Auth+                                 │
│         │             Storage+                                 │
│         │             pgvector)                                │
│         │                                                      │
│         │            ┌──────────────────────────────────┐      │
│         │            │  Worker (Railway / docker-compose)│      │
│         │            │  - APScheduler ingestion (6h)     │      │
│         │            │  - send_new_match_alerts          │      │
│         │            │  - Weekly digest (Resend)         │      │
│         │            │  - Follow-up reminders (Resend)   │      │
│         │            └──────────────────────────────────┘      │
└──────────────────────────────────────────────────────────────┘
```

See [ARCHITECTURE.md](ARCHITECTURE.md) for the live architecture reference.

---

## Project Structure

```text
InternPilot/
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI API entry + CORS + Sentry + middleware
│   │   ├── worker_main.py           # Worker entry (scheduler + digest loop)
│   │   ├── scheduler.py             # APScheduler ingestion + post-ingest hooks
│   │   ├── api/v1/                  # 16 route modules
│   │   ├── core/api_response.py     # success_response / error_response wrappers
│   │   ├── dependencies/supabase.py
│   │   ├── middleware/rate_limit.py
│   │   ├── scraper/                 # career_crawler, http_client, sources/
│   │   └── services/
│   │       ├── ranking/             # ranking_pipeline + diversity + negative_profile
│   │       ├── workflow/            # today_service + prioritizer + reminders + alerts
│   │       ├── scrapers/            # Internshala / LinkedIn / Wellfound
│   │       ├── match_engine.py
│   │       ├── vector_retrieval.py
│   │       ├── job_pipeline.py
│   │       └── ...
│   ├── migrations/                  # 001 ... 018 SQL files
│   ├── tests/
│   ├── Dockerfile
│   ├── Dockerfile.worker
│   ├── requirements.txt
│   └── .env.example
└── frontend/
    ├── src/
    │   ├── App.jsx                  # Route map (Today / Internships / Outreach / Tracker / Insights / Settings / Billing / Admin)
    │   ├── main.jsx                 # Providers: Auth, Toast, Paywall, QueryClient, Sentry, PostHog
    │   ├── components/
    │   │   ├── layout/DashboardLayout.jsx
    │   │   ├── NotificationBell.jsx
    │   │   └── ui/                  # Reusable primitives
    │   ├── pages/
    │   │   ├── dashboard/Dashboard.jsx
    │   │   ├── dashboard/InternshipsPage.jsx
    │   │   ├── dashboard/TrackerPage.jsx
    │   │   └── onboarding/OnboardingFlow.jsx
    │   ├── hooks/                   # useToday, useMatches, useNotifications
    │   ├── lib/                     # api.js, supabase.js, analytics.js, routes.js
    │   └── context/
    ├── package.json
    ├── vercel.json
    └── .env.example
```

---

## Getting Started

### Prerequisites

- Python 3.13+
- Node.js 20+
- A Supabase project, a Groq API key

### 1. Clone

```bash
git clone https://github.com/BlackPrince2607/InternPilot.git
cd InternPilot
```

### 2. Backend

```bash
cd backend

python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env              # fill in SUPABASE_URL, SUPABASE_KEY, GROQ_API_KEY at minimum
```

Apply migrations in Supabase (SQL editor) in numeric order — see [LAUNCH.md](LAUNCH.md) for the full sequence.

Run the API:

```bash
uvicorn app.main:app --reload
```

Run the worker (separate terminal) when you want live ingestion:

```bash
ENABLE_SCHEDULER=1 PLAYWRIGHT_ENABLED=1 python -m app.worker_main
```

### 3. Frontend

```bash
cd frontend

cp .env.example .env              # fill in VITE_SUPABASE_URL, VITE_SUPABASE_ANON_KEY, VITE_API_BASE_URL

npm install
npm run dev
```

Open `http://localhost:5173`.

---

## Environment Variables

Full lists with comments live in [backend/.env.example](backend/.env.example) and [frontend/.env.example](frontend/.env.example).

### Backend (required minimum)

| Variable | Description |
|----------|-------------|
| `SUPABASE_URL` | Your Supabase project URL |
| `SUPABASE_KEY` | Supabase **service-role** key (backend only — never expose to the browser) |
| `GROQ_API_KEY` | Groq API key |

### Backend (production)

`APP_CORS_ORIGINS`, `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, `STRIPE_PRICE_ID_PRO`, `RESEND_API_KEY`, `RESEND_FROM_EMAIL`, `REDIS_URL`, `SENTRY_DSN`, `ENABLE_SCHEDULER`, `PLAYWRIGHT_ENABLED`, `USE_PGVECTOR_RETRIEVAL`, `GREENHOUSE_BOARD_SLUGS`, `LEVER_BOARD_SLUGS`.

### Frontend

| Variable | Description |
|----------|-------------|
| `VITE_SUPABASE_URL` | Supabase project URL |
| `VITE_SUPABASE_ANON_KEY` | Supabase anon/public key |
| `VITE_API_BASE_URL` | Backend API base URL (e.g. `http://localhost:8000/api/v1`) |
| `VITE_POSTHOG_KEY` | (optional) PostHog project key |
| `VITE_POSTHOG_HOST` | (optional) PostHog host |
| `VITE_SENTRY_DSN` | (optional) Sentry DSN |

---

## Key API Endpoints

All endpoints live under `/api/v1`. A bearer token from Supabase Auth is required for protected routes.

```text
GET  /api/v1/auth/me                              Current user profile
POST /api/v1/resumes/upload                       Upload PDF resume
POST /api/v1/resumes/parse/{resume_id}            Parse PDF with Groq
GET  /api/v1/resumes/{resume_id}                  Fetch parsed resume
POST /api/v1/preferences/save                     Save role / location preferences
GET  /api/v1/preferences/me                       Get preferences
GET  /api/v1/matches                              Ranked internship matches
POST /api/v1/matches/feedback                     Up/down vote a match
GET  /api/v1/today                                Today workspace payload
GET  /api/v1/tracker/applications                 Application kanban
POST /api/v1/tracker/record-interaction           View / skip / click_apply event
GET  /api/v1/notifications                        Unread + recent notifications
POST /api/v1/notifications/{id}/read              Mark notification as read
POST /api/v1/cold-email/generate                  Tailored cold email
GET  /api/v1/companies/discover                   Company discovery
POST /api/v1/billing/checkout                     Stripe checkout session
POST /api/v1/billing/portal                       Stripe customer portal
POST /api/v1/billing/webhook                      Stripe webhook (idempotent)
POST /api/v1/account/export                       Export all user data
DELETE /api/v1/account                            Delete account
GET  /health                                      Liveness
GET  /ready                                       Readiness (1-row DB check)
```

---

## Deployment

### Backend → Railway / Docker

Two processes are deployed independently from the same repo:

| Service | Command | Image |
|---------|---------|-------|
| `api` | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` with `ENABLE_SCHEDULER=0` | `backend/Dockerfile` |
| `worker` | `python -m app.worker_main` with `ENABLE_SCHEDULER=1 PLAYWRIGHT_ENABLED=1` | `backend/Dockerfile.worker` |

`docker-compose.yml` brings both up locally.

### Frontend → Vercel

Connect the repo to Vercel, point at `frontend/`, add the `VITE_*` env vars, and deploy. `frontend/vercel.json` handles SPA rewrites.

See [LAUNCH.md](LAUNCH.md) for the full pre-production checklist (migrations, RLS, Stripe webhook, smoke tests).

---

## Testing

Backend tests use `pytest` and `fastapi.testclient.TestClient`:

```bash
cd backend
pytest -q
```

Covered:

- Match engine rules, retrieval, diversity, dedup, prioritizer (unit)
- HTTP contracts for `/auth/me`, `/matches`, `/today`, `/billing/webhook` idempotency, `/health`, `/ready` (integration)

Frontend lint + build:

```bash
cd frontend
npm run lint
npm run build
```

Run the backend and frontend checks locally before opening a PR.

---

## Roadmap

- [x] Resume PDF upload + Groq-powered parsing
- [x] Live internship ingestion with 9+ sources, dedup, quality filters
- [x] pgvector ANN retrieval + multi-stage personalized ranking pipeline
- [x] Match feedback + behavioral re-ranking + negative profile
- [x] Today workspace with priority actions, activation score, follow-up reminders
- [x] CRM tracker (applications, timeline, CRM insights)
- [x] In-app notification center + new-match alerts
- [x] Stripe Pro subscription with webhook idempotency
- [x] Personalized weekly digest (Resend)
- [x] Worker / API process split with Docker
- [x] FastAPI integration test suite + CI pipeline
- [ ] Email open-rate tracking
- [ ] Mobile-responsive UI polish across every page
- [ ] Browser extension for one-click applications
- [ ] Referral payouts + college-based cohorts
- [ ] Multi-region scraper fleet

---

## Contributing

Pull requests are welcome. For major changes, open an issue first to discuss.

```bash
git checkout -b feature/your-feature-name
git commit -m "feat: describe your change"
git push origin feature/your-feature-name
```

If your change touches architecture, update [ARCHITECTURE.md](ARCHITECTURE.md) in the same PR.

---

## License

MIT License — see [BlackPrince2607/InternPilot](https://github.com/BlackPrince2607/InternPilot) for usage terms.

---

<div align="center">

**Built with intention. Shipped with pride.**

<img src="https://capsule-render.vercel.app/api?type=waving&color=6c63ff&height=120&section=footer" />

</div>
