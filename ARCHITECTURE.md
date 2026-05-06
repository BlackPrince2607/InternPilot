# InternPilot Architecture

This document is the architecture source of truth for the current repository state.

If routes, storage, env vars, data flow, or major service behavior changes, update this file in the same change.

## 1. Product Scope (Current)

InternPilot is a full-stack internship assistant with:

- A React + Vite frontend in `frontend/`
- A FastAPI backend in `backend/`
- Supabase for Auth, Postgres, and Storage
- Groq LLM calls for resume parsing and cold-email generation
- A scheduled ingestion pipeline for live job data

Primary user journey:

1. Sign up/sign in with Supabase
2. Upload and parse a PDF resume
3. Save role/location/domain/stipend preferences
4. View ranked internship matches from live job records
5. Generate and track cold emails
6. Track outreach counters (applications + emails)

## 2. Runtime Architecture

```text
Browser
  |
  v
React + Vite (frontend)
  |
  | Supabase JS (auth session)
  |-----------------------------> Supabase Auth
  |
  | Bearer token in Authorization header
  v
FastAPI (backend)
  |
  |--> Supabase Postgres tables
  |--> Supabase Storage bucket (resumes)
  |--> Groq API (resume parse + cold email generation)
  |
  |--> APScheduler (periodic ingestion)
         |--> Multi-source scrapers
         |--> Cleaning + dedupe + embeddings + persistence
```

## 3. Technology Stack In Use

### Frontend

- React 19
- Vite 8
- React Router
- Tailwind CSS v4
- Framer Motion
- Axios
- Supabase JS client

### Backend

- FastAPI
- Uvicorn
- Pydantic v2
- Supabase Python client
- pdfplumber
- Groq SDK
- httpx
- APScheduler
- sentence-transformers (semantic retrieval/matching)
- BeautifulSoup (career/contact crawl)
- Playwright (scraper dependency set)

## 4. Repository Layout

```text
InternPilot/
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── context/AuthContext.jsx
│   │   ├── lib/{api.js,supabase.js}
│   │   ├── components/
│   │   │   ├── Home.jsx
│   │   │   ├── ResumeUploader.jsx
│   │   │   ├── Matches.jsx
│   │   │   ├── ColdEmail.jsx
│   │   │   ├── Tracker.jsx
│   │   │   ├── preferences.jsx
│   │   │   └── layout/{AppLayout.jsx,Navbar.jsx}
│   │   └── pages/{Onboarding.jsx,Preferences.jsx,Images.jsx}
│   └── package.json
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── scheduler.py
│   │   ├── core/api_response.py
│   │   ├── dependencies/supabase.py
│   │   ├── api/v1/
│   │   │   ├── auth.py
│   │   │   ├── resumes.py
│   │   │   ├── preferences.py
│   │   │   ├── jobs.py
│   │   │   ├── matches.py
│   │   │   ├── cold_email.py
│   │   │   ├── tracker.py
│   │   │   ├── admin.py
│   │   │   └── images.py
│   │   ├── services/
│   │   │   ├── resume_parser.py
│   │   │   ├── email_generator.py
│   │   │   ├── job_pipeline.py
│   │   │   ├── scheduler.py
│   │   │   ├── match_engine.py
│   │   │   ├── retrieval_engine.py
│   │   │   └── schema_guard.py
│   │   └── scraper/
│   │       ├── career_crawler.py
│   │       ├── db.py
│   │       ├── parser.py
│   │       └── sources/{adzuna,greenhouse,lever,remotive}.py
│   ├── migrations/{001_add_new_tables.sql,002_group2_backend_fixes.sql}
│   └── requirements.txt
├── ARCHITECTURE.md
└── CONTEXT.md
```

## 5. Backend Architecture

### 5.1 App Bootstrap

Entry: `backend/app/main.py`

Responsibilities:

- Loads backend env from `backend/.env`
- Enforces required env vars at startup:
  - `SUPABASE_URL`
  - `SUPABASE_KEY`
  - `GROQ_API_KEY`
  - `SUPABASE_RESUMES_BUCKET`
- Validates required schema/bucket via `validate_required_schema()`
- Warms embedding model on startup (best effort)
- Starts/stops APScheduler lifecycle
- Registers all API routers under `/api/v1`
- Wraps responses with global exception handlers

CORS:

- `APP_CORS_ORIGINS` (comma-separated), default `http://localhost:5173`

Health route:

- `GET /` -> success envelope with message

### 5.2 API Response Contract

`backend/app/core/api_response.py` defines a unified envelope:

- Success: `{ success: true, data: <payload>, error: null }`
- Error: `{ success: false, data: null, error: <message> }`

Frontend Axios interceptor in `frontend/src/lib/api.js` unwraps `data` when `success === true`.

### 5.3 Authentication and User Provisioning

`backend/app/api/v1/auth.py`:

- Validates bearer JWT via `supabase.auth.get_user(jwt=token)`
- Normalizes user payload
- Upserts user into app `users` table on each authenticated access

Route:

- `GET /api/v1/auth/me`

### 5.4 Resume Upload and Parsing

`backend/app/api/v1/resumes.py`:

- Accepts PDF uploads only
- Stores file in Supabase Storage under `<user_id>/<uuid>.pdf`
- Persists resume metadata in `resumes`
- Supports private-bucket signed URL + path-based download fallback
- Parses PDF text with `pdfplumber`
- Sends extracted text to Groq for structured JSON output
- Stores parsed payload in `resumes.extracted_data`

Routes:

- `POST /api/v1/resumes/upload`
- `POST /api/v1/resumes/parse/{resume_id}`
- `GET /api/v1/resumes/{resume_id}`

### 5.5 Preferences

`backend/app/api/v1/preferences.py` stores matching constraints:

- `preferred_roles` (array)
- `preferred_locations` (array)
- `preferred_domains` (array, normalized/capped)
- `stipend_min` (non-negative int)
- `remote_ok` (bool)

Routes:

- `POST /api/v1/preferences/save`
- `GET /api/v1/preferences/me`

### 5.6 Job Listing Endpoint

`backend/app/api/v1/jobs.py` returns active jobs joined with company details.

Route:

- `GET /api/v1/jobs/`

### 5.7 Match Engine and Retrieval

`backend/app/api/v1/matches.py` is the core ranking pipeline:

- Loads latest parsed resume
- Loads preferences (with column-existence compatibility checks)
- Builds user profile and domain signal
- Fetches candidate jobs from DB (domain-aware broadening)
- Prefilters by role/location/remote relevance
- Retrieves semantically relevant subset (embeddings)
- Evaluates each candidate with `MatchEngine`
- Produces strict matches and near matches
- Applies adaptive promotion if strict count is too low
- Optionally filters by stipend threshold
- Persists updated job scores in batch (RPC fallback supported)

Routes:

- `GET /api/v1/matches/`
- `GET /api/v1/matches` (same handler)
- `GET /api/v1/matches/debug/stats`

### 5.8 Cold Email Generation

`backend/app/api/v1/cold_email.py`:

- Uses latest parsed resume and optional job context
- Resolves/creates company record
- Optionally auto-selects recipient from `companies.contact_emails`
- Generates subject/body via Groq (`email_generator.py`)
- Stores generated email in `cold_emails`
- Supports tone modes: `professional`, `friendly`, `confident`, `casual`
- Supports sent-state recording + history retrieval

Routes:

- `POST /api/v1/cold-email/generate`
- `POST /api/v1/cold-email/record-sent`
- `GET /api/v1/cold-email/history`

### 5.9 Tracker

`backend/app/api/v1/tracker.py`:

- Records apply interactions (best effort into `user_interactions`)
- Increments aggregate counters in `user_activity`
- Returns stats for dashboard

Routes:

- `POST /api/v1/tracker/record-apply`
- `GET /api/v1/tracker/stats`

### 5.10 Admin + Scheduler Control

`backend/app/api/v1/admin.py`:

- Manual scrape trigger (background task)
- Scheduler status endpoint
- Optional email-based admin gate (`ADMIN_EMAIL`)

Routes:

- `POST /api/v1/admin/trigger-scrape`
- `GET /api/v1/admin/scraper-status`

### 5.11 Images Feature

`backend/app/api/v1/images.py`:

- Prompt-based generation endpoint
- Currently defaults to placeholder SVG data URI generator
- Optional provider settings are feature-flagged
- Persists metadata to `generated_images` when table exists

Route:

- `POST /api/v1/images/generate`

## 6. Ingestion and Crawling Architecture

### 6.1 Scheduler

`backend/app/scheduler.py`:

- Runs `run_all_scrapers()` at interval
- Tracks scheduler state:
  - last run time
  - status
  - last error
  - next run

Config:

- `SCRAPER_INTERVAL_HOURS` (default `6`)
- `SCRAPER_INITIAL_DELAY_MINUTES` (default `10`)

### 6.2 Job Ingestion Pipeline

`backend/app/services/job_pipeline.py`:

Pipeline stages:

1. Scrape from sources (`Internshala`, `Greenhouse`, `Lever`, `Remotive`, optional `Adzuna`)
2. Normalize + clean payloads
3. Reject low-information items
4. De-duplicate jobs
5. Extract/normalize skills
6. Domain-classify and drop non-technical roles
7. Generate embeddings for semantic retrieval
8. Upsert jobs and company links through repository layer

### 6.3 Career Crawler

`backend/app/scraper/career_crawler.py`:

- Finds or probes careers/contact pages
- Extracts likely contact emails
- Updates `companies.contact_emails` and crawl timestamps

## 7. Frontend Architecture

### 7.1 App Shell and Routing

Entry: `frontend/src/main.jsx` with `AuthProvider`.

Routes in `frontend/src/App.jsx`:

- Public:
  - `/` -> `LandingPage`
  - `/login` -> `Login`
  - `/signup` -> `Signup`
- Protected (wrapped by `ProtectedRoute` + `AppLayout`):
  - `/app` -> onboarding/home
  - `/preferences`
  - `/matches`
  - `/cold-email`
  - `/tracker`
  - `/images`

### 7.2 Auth Model

`frontend/src/context/AuthContext.jsx`:

- Loads current Supabase session on boot
- Listens to auth state changes
- Syncs user with backend via `/auth/me`
- Exposes `signUp`, `signIn`, `signOut`, auth state flags

### 7.3 API Client

`frontend/src/lib/api.js`:

- Base URL from `VITE_API_BASE_URL` (fallback `http://localhost:8000/api/v1`)
- Attaches Supabase bearer token for non-OPTIONS requests
- Unwraps backend success envelope
- Signs out on backend `401`

### 7.4 Key UI Feature Modules

- `Home` / `ResumeUploader` / `preferences` for onboarding
- `Matches` for ranking + filtering + apply tracking
- `ColdEmail` for generation, regenerate, copy, sent-mark, history
- `Tracker` for aggregate activity metrics
- `Images` for prompt-based image generation (provider-aware placeholder flow)

## 8. Data Model (Implemented)

Backed by migrations in `backend/migrations/`.

Core tables:

- `users`
- `resumes`
- `preferences`
- `companies`
- `jobs`
- `cold_emails`
- `user_activity`
- `user_interactions`
- `generated_images`

Notable columns introduced for current behavior:

- `resumes.storage_path`, `resumes.resume_embedding`
- `preferences.preferred_domains`, `preferences.stipend_min`
- `cold_emails.tone`, `cold_emails.metadata`

Utility DB function:

- `bulk_update_job_scores(p_job_ids uuid[], p_scores double precision[])`

## 9. Environment Variables

### 9.1 Required for Backend Startup

- `SUPABASE_URL`
- `SUPABASE_KEY`
- `GROQ_API_KEY`
- `SUPABASE_RESUMES_BUCKET`

### 9.2 Common Backend Runtime Variables

- `APP_CORS_ORIGINS`
- `SCRAPER_INTERVAL_HOURS`
- `SCRAPER_INITIAL_DELAY_MINUTES`
- `ADMIN_EMAIL`
- `IMAGE_GENERATION_ENABLED`
- `IMAGE_PROVIDER`
- `IMAGE_PROVIDER_API_KEY`
- `ADZUNA_APP_ID` / `ADZUNA_APP_KEY` (optional source enablement)

### 9.3 Frontend Variables

- `VITE_SUPABASE_URL`
- `VITE_SUPABASE_ANON_KEY`
- `VITE_API_BASE_URL`

## 10. Operational Notes

- Schema guard enforces required DB tables and storage bucket at startup.
- The `generated_images` table is optional; image generation still works (non-persistent) without it.
- API handlers include compatibility fallbacks for partially migrated schemas.
- Scheduler runs in the API process lifecycle; deployment should ensure one intended scheduler instance.
