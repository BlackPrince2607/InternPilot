# InternPilot Architecture

This file is the living architecture reference for the current `InternPilot` repository.

It is meant to stay aligned with the code that actually exists in this repo today. When we change routes, services, data flow, env vars, or major components, this file should be updated in the same change.

## 1. Current System Overview

InternPilot is a two-part application:

- A React + Vite frontend in `frontend/`
- A FastAPI backend in `backend/`

The app helps a user:

1. Sign up or log in with Supabase Auth
2. Upload a PDF resume
3. Parse the resume into structured data with Groq
4. Save job preferences
5. View internship matches scored against parsed resume data and preferences

## 2. Runtime Architecture

```text
Browser
  |
  v
React + Vite frontend
  |
  |  Supabase Auth SDK
  |------------------------------> Supabase Auth
  |
  |  Bearer token in Authorization header
  v
FastAPI backend
  |
  |--> Supabase auth validation
  |--> Supabase Postgres tables
  |--> Supabase Storage bucket for resumes
  |
  |--> Groq LLM for resume parsing
```

## 3. Tech Stack In Use

### Frontend

- React 19
- Vite
- React Router
- TailwindCSS
- Framer Motion
- Axios
- Supabase JS client

### Backend

- FastAPI
- Uvicorn
- Pydantic
- python-dotenv
- Supabase Python client
- pdfplumber
- Groq Python SDK
- httpx

## 4. Repository Layout

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
│   │   └── main.py
│   ├── requirements.txt
│   └── .env
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Home.jsx
│   │   │   ├── Login.jsx
│   │   │   ├── Matches.jsx
│   │   │   ├── ProtectedRoute.jsx
│   │   │   ├── ResumeUploader.jsx
│   │   │   ├── Signup.jsx
│   │   │   └── preferences.jsx
│   │   ├── context/
│   │   │   └── AuthContext.jsx
│   │   ├── lib/
│   │   │   ├── api.js
│   │   │   └── supabase.js
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── package.json
│   └── .env
└── ARCHITECTURE.md
```

## 5. Frontend Architecture

### 5.1 Entry and Routing

The frontend boots in `frontend/src/main.jsx`, which wraps the app in `AuthProvider`.

Routing lives in `frontend/src/App.jsx`.

Current routes:

- `/login` -> login screen
- `/signup` -> signup screen
- `/` -> protected home page
- `/matches` -> protected matches page

### 5.2 Auth Model

Auth state is managed in `frontend/src/context/AuthContext.jsx`.

Responsibilities:

- Load the current Supabase session on app start
- Subscribe to Supabase auth state changes
- Expose `user`, `session`, `loading`, and `isAuthenticated`
- Expose `signUp`, `signIn`, and `signOut`

`ProtectedRoute.jsx` blocks protected screens until auth state is known and redirects unauthenticated users to `/login`.

### 5.3 Frontend API Layer

`frontend/src/lib/supabase.js`

- Creates the Supabase browser client
- Requires `VITE_SUPABASE_URL`
- Requires `VITE_SUPABASE_ANON_KEY`

`frontend/src/lib/api.js`

- Creates an Axios client pointed at `VITE_API_URL`
- Adds the current Supabase access token to the `Authorization` header

This is the bridge between the frontend session and backend protected routes.

### 5.4 Frontend Screens

`Login.jsx`

- Uses Supabase password sign-in
- Redirects to `/` on success

`Signup.jsx`

- Uses Supabase sign-up
- Redirects to `/` if a session is returned immediately
- Otherwise redirects to `/login` with a confirmation message

`Home.jsx`

- Combines resume upload and preference management
- Links to matches page

`ResumeUploader.jsx`

- Provides a drag-and-drop upload area with file-picker fallback
- Uploads a PDF to the backend with upload progress feedback
- Triggers resume parsing after upload
- Shows animated idle, uploading, parsing, success, and error states
- Displays returned structured data in sectioned UI cards

`preferences.jsx`

- Loads current preferences from the backend
- Saves preferred roles, locations, and remote preference
- Now shares the same dark Tailwind-based visual system as the home page

`Matches.jsx`

- Calls the backend to fetch scored internship matches
- Renders score and reasoning for each match

## 6. Backend Architecture

### 6.1 App Bootstrap

`backend/app/main.py`

Responsibilities:

- Loads env vars via `load_dotenv()`
- Creates the FastAPI app
- Configures CORS for `http://localhost:5173`
- Registers API routers under `/api/v1`

Root route:

- `GET /` -> health-style message: `"InternPilot API is running"`

### 6.2 Dependency Layer

`backend/app/dependencies/supabase.py`

Responsibilities:

- Reads `SUPABASE_URL` and `SUPABASE_KEY`
- Creates a cached Supabase client
- Fails fast if env vars are missing

### 6.3 Auth Flow

`backend/app/api/v1/auth.py`

Responsibilities:

- Accept bearer tokens via `HTTPBearer`
- Validate the token through Supabase
- Normalize the user payload
- Ensure the authenticated user exists in the app-level `users` table

Important behavior:

- Backend auth trusts Supabase-issued access tokens from the frontend
- Protected routes depend on `get_current_user`
- On successful auth, the backend upserts the user into `users`

Current auth route:

- `GET /api/v1/auth/me`

### 6.4 Resume Flow

`backend/app/api/v1/resumes.py`

Responsibilities:

- Accept PDF uploads from authenticated users
- Store files in Supabase Storage
- Create resume records in the `resumes` table
- Parse stored resumes on demand
- Persist parsed JSON back to the database

Current routes:

- `POST /api/v1/resumes/upload`
- `POST /api/v1/resumes/parse/{resume_id}`
- `GET /api/v1/resumes/{resume_id}`

Runtime flow:

1. Frontend sends multipart upload with bearer token
2. Backend stores PDF in Supabase Storage under `{user_id}/{uuid}.pdf`
3. Backend inserts a row in `resumes`
4. Frontend calls parse endpoint
5. Backend downloads the PDF from the stored public URL
6. Backend extracts text with `pdfplumber`
7. Backend sends the text to Groq
8. Backend stores normalized parsed JSON in `resumes.extracted_data`

### 6.5 Resume Parsing Service

`backend/app/services/resume_parser.py`

Responsibilities:

- Download the PDF from a URL
- Extract text from the PDF
- Send the text to Groq for structured parsing
- Normalize the parsed JSON into a stable schema

Current structured output shape:

- `name`
- `email`
- `phone`
- `college`
- `graduation_year`
- `skills`
  - `languages`
  - `frameworks`
  - `tools`
  - `databases`
- `projects`
- `experience`
- `github`
- `linkedin`

### 6.6 Preferences Flow

`backend/app/api/v1/preferences.py`

Responsibilities:

- Save authenticated user preferences
- Load authenticated user preferences

Current routes:

- `POST /api/v1/preferences/save`
- `GET /api/v1/preferences/me`

Stored preference fields:

- `preferred_roles`
- `preferred_locations`
- `remote_ok`

### 6.7 Match Flow

`backend/app/api/v1/matches.py`

Responsibilities:

- Load the latest parsed resume
- Load saved preferences
- Score a small in-code internship dataset
- Return sorted results with reasons

Current route:

- `GET /api/v1/matches/`

Current matching logic:

- Skill overlap contributes 60%
- Preferred role contributes 20%
- Location compatibility contributes 20%
- Results under 20% are filtered out

Current job source:

- Static `JOBS` list hardcoded in `matches.py`

This means the system is currently a prototype matching engine, not yet a live job ingestion pipeline.

## 7. Data Model Inferred From Code

The backend currently assumes these Supabase resources exist.

### Tables

`users`

- `id`

`resumes`

- `id`
- `user_id`
- `file_url`
- `extracted_data`

`preferences`

- `user_id`
- `preferred_roles`
- `preferred_locations`
- `remote_ok`

### Storage

Bucket expected:

- `resumes`

## 8. Environment Variables

### Backend

Defined in `backend/.env`:

- `SUPABASE_URL`
- `SUPABASE_KEY`
- `GROQ_API_KEY`

### Frontend

Defined in `frontend/.env`:

- `VITE_SUPABASE_URL`
- `VITE_SUPABASE_ANON_KEY`
- `VITE_API_URL`

## 9.1 Frontend Styling Direction

The frontend now uses TailwindCSS as its primary styling layer.

Current styling rules:

- Global frontend styling is dark-first
- New UI work should prefer Tailwind utility classes over inline styles
- Motion-heavy interactions use Framer Motion
- The upload/parsing experience is the current reference implementation for the design system

## 10. Local Runtime

### Backend

```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload
```

Default local backend URL:

- `http://127.0.0.1:8000`

### Frontend

```bash
cd frontend
npm run dev
```

Default local frontend URL:

- `http://localhost:5173`

## 11. Request Flow Summary

### Login / Session

1. User signs in via Supabase from the frontend
2. Supabase returns a session to the browser
3. Frontend stores session in `AuthContext`
4. Axios attaches the access token to backend requests
5. Backend validates that token via Supabase

### Resume Upload and Parse

1. User uploads a PDF in the frontend
2. Frontend calls `POST /resumes/upload`
3. Frontend renders animated upload progress from Axios progress events
4. Backend stores PDF in Supabase Storage and inserts a `resumes` row
5. Frontend calls `POST /resumes/parse/{resume_id}`
6. Frontend transitions into an animated parsing state
7. Backend downloads the PDF and extracts text
8. Backend asks Groq for structured JSON
9. Backend updates the stored resume row with `extracted_data`
10. Frontend shows parsed data in structured cards for personal info, skills, and projects

### Preferences and Matches

1. User saves preferences through the frontend
2. Backend upserts a `preferences` row for the authenticated user
3. User opens matches
4. Backend loads parsed resume + preferences
5. Backend scores the hardcoded jobs list
6. Frontend renders ranked matches and reasons

## 12. Known Architectural Constraints

These are true as of the current codebase and are worth keeping in mind while building.

- The root `README.md` does not match the current implementation and should not be treated as the source of truth.
- CORS is currently limited to `http://localhost:5173`.
- Match data is static and embedded in backend code.
- There is no background job system in the current repo.
- There is no email generation flow in the current repo.
- There is no explicit migrations or schema management layer in the current repo.
- The code assumes Supabase tables and storage are already created.
- Secrets currently live in local `.env` files only and are gitignored.
- `frontend/src/components/preferences.jsx` uses a lowercase filename while most other components use PascalCase.

## 13. Update Rules For This File

This file should be updated whenever any of the following changes:

- New route added, renamed, or removed
- New service or dependency added
- Auth flow changes
- Database table shape changes
- Storage bucket usage changes
- Matching logic changes materially
- Frontend page flow changes
- Environment variables change
- Deployment/runtime assumptions change

Recommended rule:

- If a PR changes architecture, it should update `ARCHITECTURE.md` in the same PR.

## 14. Immediate Next Improvements

High-value areas to improve next:

- Add schema documentation or SQL migrations for Supabase tables and bucket setup
- Replace hardcoded jobs with a real jobs data source
- Add backend tests for auth, resume, preferences, and matches flows
- Add error-state UX for auth/session expiration across the frontend
- Expand CORS and env config for deployed environments
- Introduce an `.env.example` for both frontend and backend
