"""
Google Calendar Service for KRONOS
Fetches live events, meetings, and daily schedules using Google Calendar API v3.
"""

import os
import json
import logging
import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

from app.core.config import settings
from app.core.logger import logger

SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]


class GoogleCalendarService:
    """
    Manages Google Calendar API authentication and event fetching.
    """

    def __init__(self):
        self._service = None

    def _resolve_path(self, path_str: str) -> Optional[Path]:
        """Resolve a path relative to the project root or absolute."""
        if not path_str or not path_str.strip():
            return None
        cleaned = path_str.strip()
        p = Path(cleaned)
        if p.is_absolute() and p.exists():
            return p
        # Check relative to cwd
        p_cwd = Path.cwd() / cleaned
        if p_cwd.exists():
            return p_cwd
        # Try default locations (Credintials.json / credentials.json)
        for candidate in ["Credintials.json", "credentials.json", "calendar_token.json"]:
            if (Path.cwd() / candidate).exists() and candidate.lower() in cleaned.lower():
                return Path.cwd() / candidate
        return p_cwd if p.is_absolute() else (Path.cwd() / cleaned)

    def is_configured(self) -> bool:
        """Check whether credentials file or token file exists."""
        creds_path = self._resolve_path(getattr(settings, "GOOGLE_CALENDAR_CREDENTIALS_JSON", "Credintials.json"))
        token_path = self._resolve_path(getattr(settings, "GOOGLE_CALENDAR_TOKEN_JSON", "calendar_token.json"))
        return (token_path and token_path.exists()) or (creds_path and creds_path.exists())

    def get_credentials(self, interactive: bool = False):
        """
        Load or refresh OAuth2 credentials.
        If interactive is True and credentials file exists without a valid token,
        it launches a local browser for the user to authorize.
        """
        try:
            from google.oauth2.credentials import Credentials
            from google.auth.transport.requests import Request
            from google_auth_oauthlib.flow import InstalledAppFlow
        except ImportError:
            logger.error("[Calendar] Google OAuth libraries not installed.")
            return None

        creds = None
        token_path = self._resolve_path(getattr(settings, "GOOGLE_CALENDAR_TOKEN_JSON", "calendar_token.json"))
        creds_path = self._resolve_path(getattr(settings, "GOOGLE_CALENDAR_CREDENTIALS_JSON", "Credintials.json"))

        # 1. First check if token_path has valid token
        for candidate in [token_path, creds_path, Path.cwd() / "calendar_token.json", Path.cwd() / "Credintials.json"]:
            if candidate and candidate.exists():
                try:
                    with open(candidate, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    # If this file contains an authorized user token dict (has "token" or "refresh_token")
                    if "token" in data or "refresh_token" in data:
                        creds = Credentials.from_authorized_user_file(str(candidate), SCOPES)
                        if creds:
                            break
                except Exception:
                    pass

        # 2. Refresh or start OAuth flow
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    logger.info("[Calendar] Refreshing expired Google Calendar token...")
                    creds.refresh(Request())
                    save_path = token_path or (Path.cwd() / "calendar_token.json")
                    with open(save_path, "w", encoding="utf-8") as token_file:
                        token_file.write(creds.to_json())
                    return creds
                except Exception as e:
                    logger.warning(f"[Calendar] Token refresh failed: {e}")

            # If interactive authorization requested
            if interactive and creds_path and creds_path.exists():
                try:
                    logger.info(f"[Calendar] Initiating OAuth consent flow with {creds_path}...")
                    flow = InstalledAppFlow.from_client_secrets_file(str(creds_path), SCOPES)
                    creds = flow.run_local_server(port=0)
                    save_path = token_path or (Path.cwd() / "calendar_token.json")
                    with open(save_path, "w", encoding="utf-8") as token_file:
                        token_file.write(creds.to_json())
                    logger.info(f"[Calendar] New token saved successfully to {save_path}")
                    return creds
                except Exception as e:
                    logger.error(f"[Calendar] OAuth authorization flow failed: {e}")
                    return None

        return creds

    def get_service(self, interactive: bool = False):
        """Build and cache the Google Calendar v3 service object."""
        creds = self.get_credentials(interactive=interactive)
        if not creds or not creds.valid:
            return None

        try:
            from googleapiclient.discovery import build
            return build("calendar", "v3", credentials=creds)
        except Exception as e:
            logger.error(f"[Calendar] Failed to build Google Calendar service: {e}")
            return None

    def get_today_events(self) -> List[Dict[str, Any]]:
        """
        Fetch all events scheduled for today (local time) across all user calendars.
        Returns a list of clean event dictionaries.
        """
        service = self.get_service(interactive=False)
        if not service:
            return []

        try:
            # Calculate today's start and end in local timezone converted to RFC3339 UTC
            now = datetime.datetime.now().astimezone()
            start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0).astimezone(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            end_of_day = now.replace(hour=23, minute=59, second=59, microsecond=0).astimezone(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

            # Get all user calendar IDs
            calendar_ids = ["primary"]
            try:
                cals = service.calendarList().list().execute().get("items", [])
                calendar_ids = [c["id"] for c in cals if not c.get("hidden", False)]
            except Exception:
                pass

            events = []
            seen_ids = set()

            for cal_id in calendar_ids:
                try:
                    events_result = service.events().list(
                        calendarId=cal_id,
                        timeMin=start_of_day,
                        timeMax=end_of_day,
                        singleEvents=True,
                        orderBy="startTime"
                    ).execute()

                    items = events_result.get("items", [])
                    for item in items:
                        item_id = item.get("id")
                        if item_id in seen_ids:
                            continue
                        seen_ids.add(item_id)

                        start_raw = item.get("start", {})
                        end_raw = item.get("end", {})

                        start_str = start_raw.get("dateTime") or start_raw.get("date")
                        end_str = end_raw.get("dateTime") or end_raw.get("date")

                        formatted_start = self._format_event_time(start_str)
                        formatted_end = self._format_event_time(end_str)

                        summary = item.get("summary", "Untitled Event").strip()
                        description = (item.get("description") or "").strip()
                        location = (item.get("location") or item.get("hangoutLink") or "").strip()

                        events.append({
                            "id": item_id,
                            "summary": summary,
                            "start": formatted_start,
                            "end": formatted_end,
                            "location": location,
                            "description": description,
                            "htmlLink": item.get("htmlLink", "")
                        })
                except Exception:
                    continue

            return events
        except Exception as e:
            logger.error(f"[Calendar] Error fetching today's events: {e}")
            return []

    def get_upcoming_events(self, days: int = 7) -> List[Dict[str, Any]]:
        """
        Fetch upcoming events for the next N days.
        """
        service = self.get_service(interactive=False)
        if not service:
            return []

        try:
            now = datetime.datetime.now().astimezone()
            start_time = now.astimezone(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            end_time = (now + datetime.timedelta(days=days)).astimezone(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

            events_result = service.events().list(
                calendarId="primary",
                timeMin=start_time,
                timeMax=end_time,
                maxResults=15,
                singleEvents=True,
                orderBy="startTime"
            ).execute()

            items = events_result.get("items", [])
            events = []
            for item in items:
                start_raw = item.get("start", {})
                start_str = start_raw.get("dateTime") or start_raw.get("date")
                formatted_start = self._format_event_time(start_str, include_date=True)

                summary = item.get("summary", "Untitled Event").strip()
                location = (item.get("location") or item.get("hangoutLink") or "").strip()

                events.append({
                    "id": item.get("id"),
                    "summary": summary,
                    "start": formatted_start,
                    "location": location
                })
            return events
        except Exception as e:
            logger.error(f"[Calendar] Error fetching upcoming events: {e}")
            return []

    def get_today_summary(self) -> str:
        """
        Generate a conversational Hinglish summary of today's plans
        specifically crafted for KRONOS persona voice output.
        """
        creds = self.get_credentials(interactive=False)
        if not creds or not creds.valid:
            return (
                "Bhai, Google Calendar abhi connect nahi hai. "
                "Ek baar browser me http://127.0.0.1:8000/api/calendar/auth pe click karke authorize kar lo, "
                "fir main live plans bata paunga."
            )

        events = self.get_today_events()

        if not events:
            # Check upcoming events in the next few days to provide a helpful update
            upcoming = self.get_upcoming_events(days=3)
            if upcoming:
                upcoming_summary = ", ".join([f"{u['summary']} ({u['start']})" for u in upcoming[:2]])
                return (
                    f"Bhai aaj calendar ekdum free hai, koi meeting ya plans scheduled nahi hain! "
                    f"Lekin aane wale dino me ye plans hain: {upcoming_summary}."
                )
            return "Bhai aaj calendar ekdum chill hai! Aaj ke liye koi bhi meetings ya plans scheduled nahi hain. Poora din free hai."

        count = len(events)
        plan_word = "plan" if count == 1 else "plans"
        event_lines = []
        for i, ev in enumerate(events, 1):
            time_part = f"{ev['start']}" if ev['start'] else ""
            summary = ev['summary']
            loc_part = f" ({ev['location']})" if ev['location'] else ""
            event_lines.append(f"{i}) {time_part} - {summary}{loc_part}")

        schedule_str = ", ".join(event_lines)
        return f"Bhai aaj calendar me {count} {plan_word} hain: {schedule_str}. Baaki time sorted hai!"

    def _format_event_time(self, iso_string: Optional[str], include_date: bool = False) -> str:
        """Convert ISO date/datetime string into human-friendly time like '11:30 AM' or 'Tomorrow, 11:30 AM'."""
        if not iso_string:
            return ""
        try:
            if "T" in iso_string:
                dt = datetime.datetime.fromisoformat(iso_string)
                time_str = dt.strftime("%I:%M %p").lstrip("0")
                if include_date:
                    date_str = dt.strftime("%a %d %b")
                    return f"{date_str} at {time_str}"
                return time_str
            else:
                # All day event (YYYY-MM-DD)
                if include_date:
                    dt = datetime.date.fromisoformat(iso_string)
                    return f"{dt.strftime('%a %d %b')} (All Day)"
                return "All Day"
        except Exception:
            return iso_string


calendar_service = GoogleCalendarService()
