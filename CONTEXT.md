# InternPilot Context

This file is the practical, code-grounded context reference for the current `InternPilot` repository.

It is written to help:

- new contributors understand the project quickly
- future AI/code assistants make accurate changes
- maintainers distinguish between the product vision and the implementation that actually exists today

If the code changes in a meaningful way, this file should be updated in the same change.

## 1. Project Summary

InternPilot is a full-stack internship matching application with:

- a React + Vite frontend in `frontend/`
- a FastAPI backend in `backend/`
- Supabase for authentication, database access, and resume file storage
- Groq as the active LLM provider for resume parsing

The current product flow is:

1. A user signs up or logs in with Supabase Auth
2. The user uploads a PDF resume
3. The backend stores the PDF in a Supabase Storage bucket
4. The backend downloads the PDF, extracts text with `pdfplumber`, and sends the text to Groq
5. The parsed resume JSON is saved in the `resumes` table
6. The user saves role/location preferences
7. The backend scores the user against a temporary hardcoded internship dataset
8. The frontend shows ranked matches and basic explanations

## 2. Important Reality Check

The repository contains product messaging that describes a larger SaaS platform, but the codebase currently implements a smaller MVP.

What exists today:

- auth via Supabase
- resume upload and parsing
- preference saving
- basic match scoring
- protected frontend routes

What is described in docs or UI but not actually implemented end-to-end here:

- Next.js frontend
- Claude/Anthropic integration
- live scraped internship data
- email generation backend
- kanban application tracker
- scheduler/cron-driven ingestion pipeline
- Zustand state management
- drag-and-drop board features

Treat `ARCHITECTURE.md` and the source code as the authoritative description of the current app. Treat the root `README.md` as aspirational product framing.

## 3. Repository Layout

```text
InternPilot/
├── backend/
│   ├── app/
│   │   ├── api/v1/
│   │   │   ├── auth.py
│   │   │   ├── matches.py
│   │   │   ├── preferences.py
│   │   │   └── resumes.py
│   │   ├── dependencies/
│   │   │   └── supabase.py
│   │   ├── services/
│   │   │   └── resume_parser.py
│   │   ├── __init__.py
│   │   └── main.py
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Home.jsx
│   │   │   ├── Login.jsx
│   │   │   ├── Matches.jsx
│   │   │   ├── preferences.jsx
│   │   │   ├── ProtectedRoute.jsx
│   │   │   ├── ResumeUploader.jsx
│   │   │   └── Signup.jsx
│   │   ├── context/
│   │   │   └── AuthContext.jsx
│   │   ├── lib/
│   │   │   ├── api.js
│   │   │   └── supabase.js
│   │   ├── App.jsx
│   │   ├── index.css
│   │   └── main.jsx
│   ├── package.json
│   └── vite.config.js
├── ARCHITECTURE.md
├── CONTEXT.md
└── README.md
```

## 4. Tech Stack Actually In Use

### Frontend

- React 19
- Vite
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
- `python-dotenv`
- `pdfplumber`
- Groq Python SDK
- `httpx`

### Infrastructure / External Services

- Supabase Auth
- Supabase Postgres
- Supabase Storage bucket named `resumes`
- Groq API for structured resume extraction

## 5. Frontend Architecture

### 5.1 Bootstrapping

Entry point: `frontend/src/main.jsx`

- mounts the React app
- wraps the app with `AuthProvider`

### 5.2 Routing

Routing lives in `frontend/src/App.jsx`.

Current routes:

- `/login` -> public login screen
- `/signup` -> public signup screen
- `/` -> protected dashboard/home screen
- `/matches` -> protected matches screen

### 5.3 Auth Model

Auth is managed in `frontend/src/context/AuthContext.jsx`.

Responsibilities:

- fetch current session on load
- subscribe to auth state changes
- expose `user`, `session`, `loading`, and `isAuthenticated`
- expose `signUp`, `signIn`, and `signOut`

`ProtectedRoute.jsx` blocks protected pages until auth state resolves and redirects unauthenticated users to `/login`.

### 5.4 Frontend API Layer

`frontend/src/lib/supabase.js`

- creates the browser Supabase client
- requires `VITE_SUPABASE_URL`
- requires `VITE_SUPABASE_ANON_KEY`

`frontend/src/lib/api.js`

- creates an Axios client
- defaults `baseURL` to `http://127.0.0.1:8000/api/v1`
- injects the current Supabase access token into the `Authorization` header

### 5.5 Frontend Screens

`Login.jsx`

- signs in with Supabase email/password auth
- redirects to `/` on success

`Signup.jsx`

- signs up with Supabase email/password auth
- redirects to `/` if a session is returned immediately
- otherwise redirects to `/login` with a confirmation message

`Home.jsx`

- acts as the main authenticated dashboard
- combines resume upload and preferences in a single page
- links to `/matches`

`ResumeUploader.jsx`

- validates PDF-only uploads
- uploads the file to the backend
- triggers parsing after upload
- manages UI phases: idle, uploading, parsing, success, error
- renders extracted personal info, skills, and projects from parsed resume data

`preferences.jsx`

- loads existing preferences from the backend
- saves preferred roles, locations, and remote preference

`Matches.jsx`

- fetches ranked internship matches from the backend
- shows score, company, location, and match reasons
- currently includes a placeholder "Generate Email" button with no real flow behind it

## 6. Backend Architecture

### 6.1 App Bootstrap

Entry point: `backend/app/main.py`

Responsibilities:

- loads environment variables via `load_dotenv()`
- creates the FastAPI app
- configures CORS
- registers API routers

Current CORS configuration:

- only allows `http://localhost:5173`

Registered route groups:

- `/api/v1/auth`
- `/api/v1/resumes`
- `/api/v1/preferences`
- `/api/v1/matches`

Root route:

- `GET /` -> `{ "message": "InternPilot API is running" }`

### 6.2 Supabase Dependency Layer

`backend/app/dependencies/supabase.py`

- reads `SUPABASE_URL`
- reads `SUPABASE_KEY`
- creates a cached Supabase client
- raises immediately if env vars are missing

### 6.3 Auth Flow

`backend/app/api/v1/auth.py`

Key behavior:

- uses `HTTPBearer`
- validates the bearer token with `supabase.auth.get_user(jwt=token)`
- normalizes the user payload
- ensures the authenticated user also exists in the app-level `users` table

Current route:

- `GET /api/v1/auth/me`

Important note:

- backend trust is based on Supabase-issued access tokens from the frontend session

### 6.4 Resume Upload and Parse Flow

`backend/app/api/v1/resumes.py`

Routes:

- `POST /api/v1/resumes/upload`
- `POST /api/v1/resumes/parse/{resume_id}`
- `GET /api/v1/resumes/{resume_id}`

Upload flow:

1. Frontend sends multipart form data with bearer token
2. Backend rejects non-PDF files
3. Backend uploads the file to Supabase Storage under `{user_id}/{uuid}.pdf`
4. Backend writes a row to the `resumes` table with `user_id` and `file_url`

Parse flow:

1. Backend fetches the user-owned resume row
2. Backend downloads the PDF from the stored public URL using `httpx`
3. Backend extracts text using `pdfplumber`
4. Backend sends the text to Groq with a strict JSON-only prompt
5. Backend normalizes the returned structure
6. Backend stores the parsed JSON in `resumes.extracted_data`

Expected parsed structure includes:

- `name`
- `email`
- `phone`
- `college`
- `graduation_year`
- `skills.languages`
- `skills.frameworks`
- `skills.tools`
- `skills.databases`
- `projects`
- `experience`
- `github`
- `linkedin`

### 6.5 Preferences Flow

`backend/app/api/v1/preferences.py`

Routes:

- `POST /api/v1/preferences/save`
- `GET /api/v1/preferences/me`

Stored preference fields:

- `preferred_roles`
- `preferred_locations`
- `remote_ok`

The save endpoint uses `upsert(..., on_conflict="user_id")`.

### 6.6 Match Flow

`backend/app/api/v1/matches.py`

Current behavior:

- fetches the latest parsed resume for the current user
- fetches the user’s preferences
- flattens skills across language/framework/tool/database buckets
- scores the user against a hardcoded `JOBS` array

Score composition:

- skill overlap: 60%
- role match: 20%
- location match: 20%

The route filters out scores below `20` and sorts descending.

Current route:

- `GET /api/v1/matches/`

Important note:

- there is no live jobs table or scraper-backed pipeline yet
- matching currently depends on the temporary in-memory dataset declared in `matches.py`

## 7. Data Model Assumptions

The backend code assumes the following Supabase resources already exist.

### Tables

`users`

- `id`

Purpose:

- stores application-level user presence
- populated automatically when a valid auth token is first seen by the backend

`resumes`

- `id`
- `user_id`
- `file_url`
- `extracted_data`

Purpose:

- stores uploaded resume metadata and parsed resume JSON

`preferences`

- `user_id`
- `preferred_roles`
- `preferred_locations`
- `remote_ok`

Purpose:

- stores targeting criteria used by the match engine

### Storage

Bucket:

- `resumes`

Purpose:

- stores uploaded PDF resumes

## 8. Environment Variables

### Backend

Expected by code:

- `SUPABASE_URL`
- `SUPABASE_KEY`
- `GROQ_API_KEY`

### Frontend

Expected by code:

- `VITE_SUPABASE_URL`
- `VITE_SUPABASE_ANON_KEY`
- `VITE_API_URL`

Defaults:

- `VITE_API_URL` falls back to `http://127.0.0.1:8000/api/v1`

## 9. Local Development

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Backend runs on:

- `http://127.0.0.1:8000`

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend dev server runs on:

- `http://localhost:5173`

## 10. Key User Journey

For a healthy happy-path demo, the system should behave like this:

1. User signs up or signs in from the frontend
2. Supabase session becomes available in `AuthContext`
3. Protected home route renders
4. User uploads a PDF in `ResumeUploader`
5. Frontend calls `/resumes/upload`
6. Frontend calls `/resumes/parse/{resume_id}`
7. Parsed JSON returns and is rendered into profile cards
8. User selects roles and locations in `preferences.jsx`
9. Frontend saves preferences with `/preferences/save`
10. User opens `/matches`
11. Frontend calls `/matches`
12. Backend returns scored matches with reasons

## 11. Known Limitations and Risks

These are the most important implementation caveats to remember before extending the project.

- The root `README.md` does not match the actual implementation in several places.
- The frontend `README.md` is just the default Vite template and is not project-specific.
- Matching uses a hardcoded `JOBS` list instead of persisted or scraped data.
- The current match query uses `.limit(1)` without an explicit ordering rule, so "latest resume" is implied rather than guaranteed.
- CORS currently only allows `http://localhost:5173`, which may need expansion for deployed environments.
- Resume parsing depends on a public file URL returned by Supabase Storage.
- There is no backend endpoint for email generation despite UI/product references to that feature.
- The matches page still uses inline style objects and is visually less evolved than the home page.
- There are no visible tests in the current repository for backend routes, parser normalization, or frontend flows.
- File validation checks for `.pdf` filename/type only and does not deeply validate file contents.

## 12. Recommended Rules for Future Contributors or AI Agents

- Do not assume the marketing docs are accurate; verify behavior against source files first.
- Preserve the current auth contract: frontend gets Supabase session, backend trusts Supabase bearer tokens.
- Keep parsed resume output backward-compatible unless frontend rendering is updated in the same change.
- If adding real jobs ingestion, replace the hardcoded `JOBS` array with a persistent source before changing scoring logic.
- If adding deployment support, update CORS and environment documentation together.
- If renaming routes or changing payload shape, update `ARCHITECTURE.md`, `CONTEXT.md`, and the frontend callers in the same PR.

## 13. Best Next Steps for the Project

If someone wants to move this from MVP toward product-ready, the highest-leverage next steps are:

1. Add database schema documentation or migrations for `users`, `resumes`, and `preferences`
2. Replace hardcoded matches with a real `jobs` table and ingestion pipeline
3. Add tests for auth, resume parsing normalization, and match scoring
4. Standardize the frontend UI so `Matches`, `Login`, and `Signup` match the newer dashboard styling
5. Add an actual email generation flow or remove placeholder references until it exists
6. Align the root `README.md` with the current codebase or explicitly split "vision" from "current implementation"

## 14. Short One-Paragraph Mental Model

InternPilot is currently an authenticated resume-to-match MVP: the frontend uses Supabase auth, uploads a PDF resume through a FastAPI backend, the backend stores and parses that resume with Groq into structured candidate data, the user saves internship preferences, and a simple rules-based engine scores the user against a temporary set of internship roles and returns ranked matches.
