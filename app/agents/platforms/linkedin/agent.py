"""
LinkedIn Agent — Module 10
LinkedIn API integration (OAuth2 / OpenID Connect):
  - Authenticates via access token (LinkedIn OAuth2)
  - Polls messaging inbox for new conversation threads
  - Normalises LinkedIn messages → Conversation + Message models
  - Routes inbound messages through the ReplyOrchestrator
  - Provides send_message() to dispatch AI-generated replies
  - Tracks recruiter outreach and job-related messages separately

NOTE: LinkedIn's Messaging API access requires approval under the
      "Marketing Developer Platform" or "Partner Program".
      For personal/compliant use, access tokens are obtained via
      the standard OAuth 2.0 Authorization Code Flow.
"""

import asyncio
from typing import Optional

import httpx

from app.agents.base import BaseAgent
from app.agents.schemas import AgentHealth
from app.agents.enums import AgentState
from app.core.logger import logger
from app.core.config import settings

# Polling interval (LinkedIn rate limits are strict — 60s is safe)
POLL_INTERVAL_SECONDS = 120

LINKEDIN_API_BASE = "https://api.linkedin.com/v2"


class LinkedInAgent(BaseAgent):
    """
    Production LinkedIn Agent.

    Authentication: Bearer access token set via LINKEDIN_ACCESS_TOKEN in .env.
    Polling: background asyncio task checks messaging inbox every 2 minutes.
    """

    def __init__(self, name: str):
        super().__init__(name)
        self._access_token: Optional[str] = None
        self._profile_id: Optional[str] = None
        self._poll_task: Optional[asyncio.Task] = None
        self._http: Optional[httpx.AsyncClient] = None

    # ──────────────────────────────────────────────
    #  Lifecycle
    # ──────────────────────────────────────────────

    async def connect(self):
        """Validate the LinkedIn access token and start polling."""
        token = getattr(settings, "LINKEDIN_ACCESS_TOKEN", None)
        if not token:
            logger.warning(
                "[LinkedInAgent] LINKEDIN_ACCESS_TOKEN not set in .env — "
                "agent will be registered but inactive."
            )
            self.state = AgentState.ERROR
            return

        self._access_token = token
        self._http = httpx.AsyncClient(
            headers={
                "Authorization": f"Bearer {token}",
                "X-Restli-Protocol-Version": "2.0.0",
                "Content-Type": "application/json",
            },
            timeout=30.0,
        )

        try:
            # Validate token by fetching own profile
            profile = await self._get_own_profile()
            if not profile:
                self.state = AgentState.ERROR
                return

            self._profile_id = profile.get("id")
            display_name = (
                profile.get("localizedFirstName", "")
                + " "
                + profile.get("localizedLastName", "")
            ).strip()

            self.state = AgentState.CONNECTED
            logger.info(
                f"[LinkedInAgent] Authenticated as {display_name} "
                f"(id={self._profile_id})"
            )

            # Start polling loop
            self._poll_task = asyncio.create_task(
                self._polling_loop(),
                name="linkedin_poll_task"
            )
            logger.info(
                f"[LinkedInAgent] Polling inbox every {POLL_INTERVAL_SECONDS}s."
            )

        except Exception as e:
            logger.error(f"[LinkedInAgent] Connection failed: {e}")
            self.state = AgentState.ERROR

    async def disconnect(self):
        """Cancel the polling loop and close the HTTP client."""
        if self._poll_task and not self._poll_task.done():
            self._poll_task.cancel()
        if self._http:
            await self._http.aclose()
        self.state = AgentState.STOPPED
        logger.info("[LinkedInAgent] Disconnected.")

    # ──────────────────────────────────────────────
    #  Profile helpers
    # ──────────────────────────────────────────────

    async def _get_own_profile(self) -> Optional[dict]:
        """Fetch the authenticated user's LinkedIn profile."""
        try:
            resp = await self._http.get(f"{LINKEDIN_API_BASE}/me")
            if resp.status_code == 200:
                return resp.json()
            logger.error(
                f"[LinkedInAgent] Profile fetch failed: "
                f"{resp.status_code} — {resp.text}"
            )
            return None
        except Exception as e:
            logger.error(f"[LinkedInAgent] Error fetching profile: {e}")
            return None

    # ──────────────────────────────────────────────
    #  Polling loop
    # ──────────────────────────────────────────────

    async def _polling_loop(self):
        """Periodically call listen() to check for new LinkedIn messages."""
        while True:
            try:
                await self.listen()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[LinkedInAgent] Polling error: {e}")
            await asyncio.sleep(POLL_INTERVAL_SECONDS)

    async def listen(self, raw_data=None):
        """
        Fetch LinkedIn inbox conversations and process new messages.

        Uses the LinkedIn Messaging API v2/conversations endpoint.
        """
        if self._http is None or self._access_token is None:
            return

        try:
            # Fetch the inbox (most recent 10 conversations)
            resp = await self._http.get(
                f"{LINKEDIN_API_BASE}/conversations",
                params={
                    "keyVersion": "LEGACY_INBOX",
                    "q": "participants",
                    "start": 0,
                    "count": 10,
                }
            )

            if resp.status_code == 403:
                logger.warning(
                    "[LinkedInAgent] 403 Forbidden — Messaging API access "
                    "may require LinkedIn Partner approval. "
                    "Tracking jobs/recruiter metadata only."
                )
                return

            if resp.status_code != 200:
                logger.warning(
                    f"[LinkedInAgent] Inbox fetch returned {resp.status_code}"
                )
                return

            data = resp.json()
            conversations = data.get("elements", [])

            if not conversations:
                return

            from app.db.session import AsyncSessionLocal
            from app.services.social_services import (
                SocialAccountService,
                ConversationService,
                MessageService,
            )
            from app.services.reply_orchestrator import ReplyOrchestrator

            async with AsyncSessionLocal() as db:
                acc_service  = SocialAccountService(db)
                conv_service = ConversationService(db)
                msg_service  = MessageService(db)

                # Ensure our LinkedIn account is registered
                account = await acc_service.create_account(
                    user_id=1,
                    platform_name="linkedin",
                    platform_user_id=self._profile_id,
                    username=self._profile_id,
                    display_name="LinkedIn Bot",
                )

                orchestrator = ReplyOrchestrator(db)

                for conv_data in conversations:
                    await self._process_conversation(
                        conv_data=conv_data,
                        account=account,
                        conv_service=conv_service,
                        msg_service=msg_service,
                        orchestrator=orchestrator,
                    )

        except Exception as e:
            logger.error(f"[LinkedInAgent] Error in listen(): {e}")

    async def _process_conversation(
        self,
        conv_data: dict,
        account,
        conv_service,
        msg_service,
        orchestrator,
    ):
        """Process a single LinkedIn conversation, handling new messages."""
        try:
            entity_urn = conv_data.get("entityUrn", "")
            conv_id = entity_urn.split(":")[-1] if entity_urn else str(id(conv_data))

            # Extract conversation title (first participant's name)
            participants = conv_data.get("participants", [])
            title = "LinkedIn Conversation"
            if participants:
                p = participants[0]
                title = (
                    p.get("com.linkedin.voyager.messaging.MessagingMember", {})
                     .get("miniProfile", {})
                     .get("firstName", "Unknown")
                )

            conversation = await conv_service.get_or_create_conversation(
                platform_name="linkedin",
                account_id=account.id,
                external_id=conv_id,
                title=title,
                conversation_type="direct",
            )

            # Fetch messages for this conversation
            msg_resp = await self._http.get(
                f"{LINKEDIN_API_BASE}/conversations/{conv_id}/events",
                params={"start": 0, "count": 5}
            )
            if msg_resp.status_code != 200:
                return

            events = msg_resp.json().get("elements", [])
            for event in events:
                body = (
                    event.get("eventContent", {})
                         .get("com.linkedin.voyager.messaging.event.MessageEvent", {})
                         .get("attributedBody", {})
                         .get("text", "")
                )
                if not body:
                    continue

                event_urn = event.get("entityUrn", "")
                msg_external_id = event_urn.split(":")[-1] if event_urn else str(id(event))
                sender_urn = event.get("from", {}).get("com.linkedin.voyager.messaging.MessagingMember", {})
                sender_id = str(sender_urn.get("miniProfile", {}).get("publicIdentifier", "unknown"))

                # Skip messages sent by us
                if sender_id == self._profile_id:
                    continue

                inbound = await msg_service.create_message(
                    conversation_id=conversation.id,
                    external_id=msg_external_id,
                    sender_id=sender_id,
                    content=body,
                    is_outgoing=False,
                )

                logger.info(
                    f"[LinkedInAgent] Inbound from {sender_id} "
                    f"in conv {conv_id}: {body[:60]}"
                )

                await orchestrator.handle_inbound(
                    conversation_id=conversation.id,
                    inbound_message_id=inbound.id,
                )

        except Exception as e:
            logger.error(f"[LinkedInAgent] Error processing conversation: {e}")

    # ──────────────────────────────────────────────
    #  Sending
    # ──────────────────────────────────────────────

    async def send_message(self, destination: str, message: str):
        """
        Send a LinkedIn message.

        Args:
            destination: LinkedIn conversation ID or profile URN.
            message:     Text content to send.
        """
        if self._http is None:
            logger.warning("[LinkedInAgent] Cannot send — not connected.")
            return

        try:
            payload = {
                "eventCreate": {
                    "value": {
                        "com.linkedin.voyager.messaging.create.MessageCreate": {
                            "attributedBody": {
                                "text": message,
                                "attributes": [],
                            },
                            "attachments": [],
                        }
                    }
                }
            }
            resp = await self._http.post(
                f"{LINKEDIN_API_BASE}/conversations/{destination}/events",
                json=payload,
            )
            if resp.status_code in (200, 201):
                logger.info(
                    f"[LinkedInAgent] Sent to conversation {destination}: {message[:60]}"
                )
            else:
                logger.error(
                    f"[LinkedInAgent] Send failed {resp.status_code}: {resp.text}"
                )
        except Exception as e:
            logger.error(f"[LinkedInAgent] Failed to send message: {e}")

    # ──────────────────────────────────────────────
    #  Job / Recruiter tracking (Module 10 — LinkedIn specific)
    # ──────────────────────────────────────────────

    async def get_job_recommendations(self) -> list:
        """
        Fetch LinkedIn's job recommendations for the authenticated user.
        Returns a list of job title + company pairs for tracking.
        """
        if self._http is None:
            return []
        try:
            resp = await self._http.get(
                f"{LINKEDIN_API_BASE}/jobPostings",
                params={"q": "relevantJobsForMember", "start": 0, "count": 10}
            )
            if resp.status_code == 200:
                jobs = resp.json().get("elements", [])
                result = []
                for job in jobs:
                    result.append({
                        "id": job.get("jobPostingId"),
                        "title": job.get("title", "Unknown"),
                        "company": job.get("companyName", "Unknown"),
                        "location": job.get("formattedLocation", ""),
                    })
                logger.info(f"[LinkedInAgent] Fetched {len(result)} job recommendations.")
                return result
            logger.warning(f"[LinkedInAgent] Job fetch returned {resp.status_code}")
            return []
        except Exception as e:
            logger.error(f"[LinkedInAgent] Error fetching jobs: {e}")
            return []

    # ──────────────────────────────────────────────
    #  Health
    # ──────────────────────────────────────────────

    async def health(self) -> AgentHealth:
        connected = (
            self._access_token is not None
            and self.state == AgentState.CONNECTED
        )
        return AgentHealth(
            name=self.name,
            state=self.state,
            connected=connected,
        )
