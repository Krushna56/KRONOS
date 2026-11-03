"""
Google Calendar API Routes
Endpoints to inspect today's events, sync status, and authorize Google Calendar.
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from app.services.calendar_service import calendar_service
from app.core.logger import logger

router = APIRouter(prefix="/api/calendar", tags=["Calendar"])


@router.get("/status")
async def get_calendar_status():
    """
    Check if Google Calendar credentials and token exist.
    """
    configured = calendar_service.is_configured()
    creds = calendar_service.get_credentials(interactive=False)
    authenticated = bool(creds and creds.valid)
    return {
        "configured": configured,
        "authenticated": authenticated
    }


@router.get("/today")
async def get_today_calendar():
    """
    Fetch today's events from Google Calendar.
    """
    events = calendar_service.get_today_events()
    summary = calendar_service.get_today_summary()
    return {
        "status": "success",
        "count": len(events),
        "events": events,
        "summary": summary
    }


@router.get("/auth")
def authorize_calendar():
    """
    Initiate OAuth authorization flow via browser.
    """
    try:
        creds = calendar_service.get_credentials(interactive=True)
        if creds and creds.valid:
            return HTMLResponse("""
            <html>
                <body style="font-family: sans-serif; text-align: center; padding: 50px; background: #0f172a; color: #f8fafc;">
                    <h1 style="color: #22c55e;">🎉 Google Calendar Connected!</h1>
                    <p>KRONOS ab aapke calendar ke live plans aur schedule dekh sakta hai.</p>
                    <p><a href="/api/calendar/today" style="color: #38bdf8; text-decoration: underline;">View Today's Events</a></p>
                </body>
            </html>
            """)
        else:
            raise HTTPException(status_code=400, detail="Failed to authorize Google Calendar.")
    except Exception as e:
        logger.exception(f"Error authorizing calendar: {e}")
        return HTMLResponse(f"""
        <html>
            <body style="font-family: sans-serif; text-align: center; padding: 50px; background: #0f172a; color: #f8fafc;">
                <h1 style="color: #ef4444;">❌ Authorization Error</h1>
                <p>{str(e)}</p>
                <p>Ensure Credintials.json exists and Google Calendar API is enabled in Google Cloud Console.</p>
            </body>
        </html>
        """, status_code=500)

