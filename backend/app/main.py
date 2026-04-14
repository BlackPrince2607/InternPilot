from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from app.api.v1 import resumes  # Add this import
from app.api.v1 import resumes, preferences, matches

load_dotenv()

app = FastAPI(title="InternPilot API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(resumes.router, prefix="/api/v1")  # Add this line

@app.get("/")
def root():
    return {"message": "InternPilot API is running"}

app.include_router(preferences.router, prefix="/api/v1")
app.include_router(matches.router, prefix="/api/v1")