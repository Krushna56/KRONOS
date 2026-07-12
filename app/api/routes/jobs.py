from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from app.api.routes.auth import get_current_user
from app.db.models.user import User

router = APIRouter()

@router.get("/search")
async def search_jobs(
    query: str = Query(..., description="Job title, keywords, or company"),
    location: Optional[str] = Query(None, description="Preferred location"),
    current_user: User = Depends(get_current_user)
):
    """Search for jobs matching keywords and location."""
    # Placeholder mock search results
    return [
        {
            "id": 1,
            "title": f"Senior {query} Developer",
            "company": "DeepMind Technologies",
            "location": location or "Remote",
            "salary": "$150,000 - $220,000",
            "description": f"Exciting opportunity for a skilled developer interested in {query} systems."
        },
        {
            "id": 2,
            "title": f"Lead AI Engineer ({query})",
            "company": "Antigravity Corp",
            "location": "San Francisco, CA",
            "salary": "$180,000 - $250,000",
            "description": "Build next generation agentic AI clone assistants using modern Python and agent frameworks."
        }
    ]


@router.post("/apply")
async def apply_job(
    job_id: int,
    resume_url: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Submit a job application."""
    return {
        "status": "success",
        "message": f"Successfully submitted application for Job ID {job_id}.",
        "applicant": current_user.username,
        "resume_submitted": resume_url or "Default Profile Resume"
    }
