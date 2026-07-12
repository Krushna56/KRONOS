import time
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db

router = APIRouter()

@router.get("")
@router.get("/")
async def health_check(db: AsyncSession = Depends(get_db)):
    """System status and deep dependency health check (Database connectivity check)."""
    start_time = time.time()
    
    # Check Database connection
    db_status = "unhealthy"
    db_latency = 0.0
    try:
        db_start = time.time()
        await db.execute(text("SELECT 1"))
        db_latency = round((time.time() - db_start) * 1000, 2)
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    total_latency = round((time.time() - start_time) * 1000, 2)

    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "timestamp": time.time(),
        "total_latency_ms": total_latency,
        "dependencies": {
            "database": {
                "status": db_status,
                "latency_ms": db_latency
            }
        }
    }
