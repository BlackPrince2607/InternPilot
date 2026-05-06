# InternPilot Context

This document is a practical implementation context for contributors and coding agents.

It is intentionally code-grounded. If this file and runtime behavior disagree, treat source code as final and update this file.

## 1. What Exists Today

InternPilot currently delivers:

- Supabase-authenticated user flows
- Resume upload and Groq-powered structured resume parsing
- Preferences capture (roles, locations, domains, stipend, remote)
- Live job listing retrieval from DB
- Embedding-assisted match ranking with strict/near-match behavior
- Cold email generation and sent-state tracking
- Activity tracker counters
- Scheduler-driven job ingestion and company contact crawling
- Prompt-based image generation endpoint (currently placeholder provider by default)

## 2. Product Flow (Current End-to-End)

1. User signs in via Supabase on frontend
2. Frontend syncs backend user via `GET /api/v1/auth/me`
3. User uploads PDF resume via `/api/v1/resumes/upload`
4. User triggers parse via `/api/v1/resumes/parse/{resume_id}`
5. User saves preferences via `/api/v1/preferences/save`
6. User opens matches via `/api/v1/matches/`
7. User can track apply actions via `/api/v1/tracker/record-apply`
8. User can generate cold email via `/api/v1/cold-email/generate`
9. User can mark email sent via `/api/v1/cold-email/record-sent`
10. User views tracker stats via `/api/v1/tracker/stats`

## 3. Frontend Reality Snapshot

### 3.1 Route Map

- Public routes:
  - `/` landing page
  - `/login`
  - `/signup`
- Protected app routes:
  - `/app`
  - `/preferences`
  - `/matches`
  - `/cold-email`
  - `/tracker`
  - `/images`

### 3.2 Frontend Structure

- Auth provider: `frontend/src/context/AuthContext.jsx`
- API client: `frontend/src/lib/api.js`
- Supabase client: `frontend/src/lib/supabase.js`
- App shell: `frontend/src/components/layout/AppLayout.jsx`

### 3.3 Frontend Data Contract

Backend returns success/error envelopes.
Axios interceptors unwrap success payloads automatically:

- UI code generally consumes `res.data.<field>` where `res.data` already maps to backend `data`.

### 3.4 Feature Components in Active Use

- `ResumeUploader.jsx`: upload + parse flow with status UI
- `preferences.jsx`: role/location/domain/stipend/remote preferences
- `Matches.jsx`: fetch, filter, and action matches
- `ColdEmail.jsx`: generate/regenerate/history/mark-sent
- `Tracker.jsx`: applied and sent counters
- `Images.jsx`: prompt-based generator UI

## 4. Backend Reality Snapshot

### 4.1 Router Surface (All Mounted Under `/api/v1`)

- `GET /auth/me`
- `POST /resumes/upload`
- `POST /resumes/parse/{resume_id}`
- `GET /resumes/{resume_id}`
- `POST /preferences/save`
- `GET /preferences/me`
- `GET /jobs/`
- `GET /matches/`
- `GET /matches`
- `GET /matches/debug/stats`
- `POST /cold-email/generate`
- `POST /cold-email/record-sent`
- `GET /cold-email/history`
- `POST /tracker/record-apply`
- `GET /tracker/stats`
- `POST /admin/trigger-scrape`
- `GET /admin/scraper-status`
- `POST /images/generate`

### 4.2 Auth and User Provisioning

- Auth uses Supabase bearer token validation server-side.
- Any authenticated request ensures/upserts a corresponding row in `users`.

### 4.3 Resume Parsing Details

- PDF text extraction uses `pdfplumber`.
- Parsing uses Groq chat completion with JSON response format.
- Parsed payload is normalized to stable keys before persistence.

### 4.4 Matching Details

Matching is no longer a tiny static dataset flow.
It now combines:

- profile-building from parsed resume + preferences
- candidate job fetching from `jobs`
- domain/role/location prefiltering
- embedding-based retrieval stage
- final scoring via match engine
- strict and near-match outputs
- optional stipend filtering
- score persistence back to jobs table

### 4.5 Job Ingestion and Freshness

- Scheduler periodically runs ingestion cycle.
- Sources include Internshala, Greenhouse, Lever, Remotive, optional Adzuna.
- Jobs are cleaned, deduplicated, skill-extracted, embedded, and upserted.
- Stale jobs are deactivated by policy.
- Career crawler enriches companies with likely contact emails.

## 5. Data Model Expectations

The backend expects these tables for full functionality:

- `users`
- `resumes`
- `preferences`
- `companies`
- `jobs`
- `cold_emails`
- `user_activity`
- `user_interactions`

Optional but supported:

- `generated_images` (absence does not block API startup)

Important compatibility columns used by current logic:

- `resumes.storage_path`
- `resumes.resume_embedding`
- `preferences.preferred_domains`
- `preferences.stipend_min`
- `cold_emails.tone`
- `cold_emails.metadata`

## 6. Environment Variables

### 6.1 Backend (Required)

- `SUPABASE_URL`
- `SUPABASE_KEY`
- `GROQ_API_KEY`
- `SUPABASE_RESUMES_BUCKET`

### 6.2 Backend (Common Optional/Operational)

- `APP_CORS_ORIGINS`
- `SCRAPER_INTERVAL_HOURS`
- `SCRAPER_INITIAL_DELAY_MINUTES`
- `ADMIN_EMAIL`
- `IMAGE_GENERATION_ENABLED`
- `IMAGE_PROVIDER`
- `IMAGE_PROVIDER_API_KEY`
- `ADZUNA_APP_ID`
- `ADZUNA_APP_KEY`

### 6.3 Frontend

- `VITE_SUPABASE_URL`
- `VITE_SUPABASE_ANON_KEY`
- `VITE_API_BASE_URL`

## 7. Deployment and Runtime Notes

- Startup runs schema guard checks and will fail fast if required tables/bucket are missing.
- Scheduler starts automatically in app lifespan; avoid unintentionally running multiple scheduler instances.
- CORS defaults to localhost Vite dev origin unless overridden.
- Frontend signs out user when backend returns 401.

## 8. Known Product State Clarifications

- Tracker currently exposes aggregate counters, not full Kanban state management.
- Image generation endpoint currently returns placeholder image output by default provider settings.
- Architecture and behavior are significantly beyond early MVP docs that referenced only static job matching.

## 9. Contributor Guidance

When adding or changing features:

1. Update route docs in this file and `ARCHITECTURE.md`.
2. Keep migration files aligned with runtime column usage.
3. Preserve the API envelope contract unless a coordinated frontend change is included.
4. Validate whether schema guard requires updates for new required tables/columns.
