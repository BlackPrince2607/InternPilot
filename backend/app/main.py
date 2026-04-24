from contextlib import asynccontextmanager
from pathlib import Path
import asyncio
import logging
import os

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import admin, auth, cold_email, images, jobs, matches, preferences, resumes, tracker
from app.core.api_response import error_response, success_response
from app.scheduler import start_scheduler, stop_scheduler
from app.services.schema_guard import validate_required_schema

ENV_PATH = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(ENV_PATH)
logger = logging.getLogger(__name__)

allowed_origins = [
    origin.strip()
    for origin in os.getenv("APP_CORS_ORIGINS", "http://localhost:5173").split(",")
    if origin.strip()
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    validate_required_schema()
    from app.services.embedding_service import _get_model

    try:
        await asyncio.get_event_loop().run_in_executor(None, _get_model)
        logger.info("Embedding model loaded and ready")
    except Exception as e:
        logger.warning("Embedding model warm-up failed: %s", e)
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


@app.exception_handler(HTTPException)
async def handle_http_exception(_: Request, exc: HTTPException):
    message = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
    return JSONResponse(status_code=exc.status_code, content=error_response(message))


@app.exception_handler(Exception)
async def handle_unexpected_exception(_: Request, __: Exception):
    return JSONResponse(status_code=500, content=error_response("Internal server error"))

# Register routers
app.include_router(resumes.router, prefix="/api/v1")
app.include_router(auth.router, prefix="/api/v1")
app.include_router(preferences.router, prefix="/api/v1")
app.include_router(jobs.router, prefix="/api/v1")
app.include_router(matches.router, prefix="/api/v1")
app.include_router(cold_email.router, prefix="/api/v1")
app.include_router(tracker.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")
app.include_router(images.router, prefix="/api/v1")

@app.get("/")
def root():
    return success_response({"message": "InternPilot API is running"})
