# InternPilot

InternPilot is a full-stack internship assistant that helps students:

- upload and parse resumes
- discover ranked internship matches from live ingested jobs
- generate tailored cold emails
- track outreach activity

This repository contains both frontend and backend code.

## Current Stack

### Frontend

- React 19
- Vite
- React Router
- Tailwind CSS v4
- Framer Motion
- Supabase JS client
- Axios

### Backend

- FastAPI
- Uvicorn
- Supabase Python client
- Pydantic v2
- pdfplumber
- Groq SDK
- APScheduler
- sentence-transformers
- BeautifulSoup + httpx

### Infrastructure

- Supabase Auth
- Supabase Postgres
- Supabase Storage (resume files)

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
