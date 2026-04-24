from contextlib import asynccontextmanager
from pathlib import Path
import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import admin, auth, cold_email, matches, preferences, resumes, tracker
from app.scheduler import start_scheduler, stop_scheduler
from app.services.schema_guard import validate_required_schema

ENV_PATH = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(ENV_PATH)

allowed_origins = [
    origin.strip()
    for origin in os.getenv("APP_CORS_ORIGINS", "http://localhost:5173").split(",")
    if origin.strip()
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    validate_required_schema()
    start_scheduler()
    yield
    stop_scheduler()


app = FastAPI(title="InternPilot API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(resumes.router, prefix="/api/v1")  # Add this line
app.include_router(auth.router, prefix="/api/v1")
app.include_router(preferences.router, prefix="/api/v1")
app.include_router(matches.router, prefix="/api/v1")
app.include_router(cold_email.router, prefix="/api/v1")
app.include_router(tracker.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")

@app.get("/")
def root():
    return {"message": "InternPilot API is running"}
