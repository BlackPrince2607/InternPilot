from fastapi import APIRouter, HTTPException
from fastapi import Depends
from app.api.v1.auth import get_current_user
from app.dependencies.supabase import get_supabase_client

router = APIRouter(prefix="/matches", tags=["matches"])

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
    skills_dict = skills_dict or {}
    return (
        skills_dict.get("languages", []) +
        skills_dict.get("frameworks", []) +
        skills_dict.get("tools", []) +
        skills_dict.get("databases", [])
    )

def skill_score(user_skills, job_skills):
    user_skills = [s.lower() for s in user_skills]
    job_skills = [s.lower() for s in job_skills]

    matched = list(set(user_skills) & set(job_skills))
    score = len(matched) / len(job_skills) if job_skills else 0

    return score, matched


def role_score(preferred_roles, job_title):
    return 1 if job_title in preferred_roles else 0


def location_score(preferred_locations, job_location, remote_ok):
    if job_location in preferred_locations:
        return 1
    if job_location == "Remote" and remote_ok:
        return 1
    return 0


def calculate_match(user, job):
    s_score, matched_skills = skill_score(user["skills"], job["skills_required"])
    r_score = role_score(user["roles"], job["title"])
    l_score = location_score(user["locations"], job["location"], user["remote_ok"])

    final_score = (s_score * 0.6) + (r_score * 0.2) + (l_score * 0.2)

    # 🔥 Explanation
    reasons = []

    if matched_skills:
        reasons.append(f"Matched skills: {', '.join(matched_skills)}")

    if r_score:
        reasons.append("Preferred role match")

    if l_score:
        reasons.append("Location match")

    return round(final_score * 100, 2), reasons


# 🚀 Main Endpoint

@router.get("/")
async def get_matches(current_user: dict = Depends(get_current_user)):
    user_id = current_user["id"]
    supabase = get_supabase_client()
    try:
        # 1️⃣ Get latest resume
        resume_res = supabase.table("resumes") \
            .select("*") \
            .eq("user_id", user_id) \
            .not_.is_("extracted_data", "null") \
            .limit(1) \
            .execute()

        if not resume_res.data:
            raise HTTPException(404, "Resume not found")

        resume_data = resume_res.data[0].get("extracted_data")

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
        skills_dict = (resume_data or {}).get("skills") or {}

        user_skills = flatten_skills(skills_dict)

        user = {
            "skills": user_skills,
            "roles": prefs.get("preferred_roles", []),
            "locations": prefs.get("preferred_locations", []),
            "remote_ok": prefs.get("remote_ok", False)
        }

        # DEBUG (optional)
        print("USER SKILLS:", user_skills)

        # 4️⃣ Calculate matches
        results = []

        for job in JOBS:
            score, reasons = calculate_match(user, job)

            # Optional: filter low scores
            if score < 20:
                continue

            results.append({
                "title": job["title"],
                "company": job["company"],
                "location": job["location"],
                "score": score,
                "why": reasons
            })

        # 5️⃣ Sort by score
        results = sorted(results, key=lambda x: x["score"], reverse=True)

        return {"matches": results}

    except HTTPException:
        raise
    except Exception as e:
        print("MATCH ERROR:", e)
        raise HTTPException(500, f"Matching failed: {str(e)}")
