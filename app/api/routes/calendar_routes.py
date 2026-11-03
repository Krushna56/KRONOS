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


@router.get("/debug")
async def debug_calendar():
    """
    Debug calendar list and all upcoming events to see what Google returns.
    """
    service = calendar_service.get_service()
    if not service:
        return {"error": "Service not initialized"}
    
    import datetime
    now_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()
    now_local = datetime.datetime.now().astimezone()
    
    # 1. Calendar list
    cals = service.calendarList().list().execute().get("items", [])
    calendars = [{"summary": c.get("summary"), "id": c.get("id"), "primary": c.get("primary", False)} for c in cals]
    
    # 2. Upcoming events on primary calendar (next 30 days)
    upcoming_res = service.events().list(
        calendarId="primary",
        timeMin=now_utc,
        maxResults=20,
        singleEvents=True,
        orderBy="startTime"
    ).execute()
    upcoming_events = upcoming_res.get("items", [])
    
    # 3. Any 10 most recent events without timeMin filter
    any_res = service.events().list(
        calendarId="primary",
        maxResults=10
    ).execute()
    any_events = any_res.get("items", [])

    return {
        "now_local": str(now_local),
        "now_utc": now_utc,
        "calendars": calendars,
        "upcoming_count": len(upcoming_events),
        "upcoming_events": upcoming_events,
        "any_events_count": len(any_events),
        "any_events": any_events
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

