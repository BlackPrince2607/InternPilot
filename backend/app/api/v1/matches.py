from fastapi import APIRouter, HTTPException
from supabase import create_client
import os

router = APIRouter(prefix="/matches", tags=["matches"])

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

# 🔥 Temporary Job Dataset (replace later with scraper)
JOBS = [
    {
        "title": "Backend Intern",
        "company": "Razorpay",
        "location": "Bangalore",
        "skills_required": ["Python", "FastAPI", "SQL"]
    },
    {
        "title": "ML Intern",
        "company": "CRED",
        "location": "Bangalore",
        "skills_required": ["Python", "TensorFlow", "Pandas"]
    },
    {
        "title": "Frontend Intern",
        "company": "Swiggy",
        "location": "Remote",
        "skills_required": ["React", "JavaScript", "CSS"]
    }
]

# 🧠 Helper Functions

def flatten_skills(skills_dict):
    return (
        skills_dict.get("languages", []) +
        skills_dict.get("frameworks", []) +
        skills_dict.get("tools", []) +
        skills_dict.get("databases", [])
    )

def skill_score(user_skills, job_skills):
    user_skills = [s.lower() for s in user_skills]
    job_skills = [s.lower() for s in job_skills]

    matches = len(set(user_skills) & set(job_skills))
    return matches / len(job_skills) if job_skills else 0

def role_score(preferred_roles, job_title):
    return 1 if job_title in preferred_roles else 0

def location_score(preferred_locations, job_location, remote_ok):
    if job_location in preferred_locations:
        return 1
    if job_location == "Remote" and remote_ok:
        return 1
    return 0

def calculate_match(user, job):
    s_score = skill_score(user["skills"], job["skills_required"])
    r_score = role_score(user["roles"], job["title"])
    l_score = location_score(user["locations"], job["location"], user["remote_ok"])

    final = (s_score * 0.6) + (r_score * 0.2) + (l_score * 0.2)
    return round(final * 100, 2)


# 🚀 Main Endpoint

@router.get("/{user_id}")
async def get_matches(user_id: str):
    try:
        # 1️⃣ Get resume (latest one)
        resume_res = supabase.table("resumes") \
            .select("*") \
            .eq("user_id", user_id) \
            .limit(1) \
            .execute()

        if not resume_res.data:
            raise HTTPException(404, "Resume not found")

        resume_data = resume_res.data[0]["extracted_data"]
        if not resume_data:
            raise HTTPException(400, "Resume not parsed yet")

        # 2️⃣ Get preferences
        pref_res = supabase.table("preferences") \
            .select("*") \
            .eq("user_id", user_id) \
            .execute()

        if not pref_res.data:
            raise HTTPException(404, "Preferences not found")

        prefs = pref_res.data[0]

        # 3️⃣ Prepare user profile
        user = {
            "skills": flatten_skills(resume_data.get("skills", {})),
            "roles": prefs.get("preferred_roles", []),
            "locations": prefs.get("preferred_locations", []),
            "remote_ok": prefs.get("remote_ok", False)
        }

        # 4️⃣ Calculate matches
        results = []

        for job in JOBS:
            score = calculate_match(user, job)

            results.append({
                "title": job["title"],
                "company": job["company"],
                "location": job["location"],
                "score": score
            })

        # 5️⃣ Sort by score
        results = sorted(results, key=lambda x: x["score"], reverse=True)

        return {"matches": results}

    except Exception as e:
        raise HTTPException(500, f"Matching failed: {str(e)}")