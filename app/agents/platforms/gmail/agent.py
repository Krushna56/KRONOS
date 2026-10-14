"""
Gmail Agent — Module 10
Google Gmail API integration (OAuth2):
  - Authenticates using a credentials file (or token file) via google-auth
  - Polls for unread emails in a background loop (no push webhook needed)
  - Normalises email threads → Conversation + Message models
  - Routes inbound emails through the ReplyOrchestrator
  - Provides send_message() to dispatch AI-generated email replies
"""

import asyncio
import base64
import email as email_lib
import json
from typing import Optional
from email.mime.text import MIMEText

from app.agents.base import BaseAgent
from app.agents.schemas import AgentHealth
from app.agents.enums import AgentState
from app.core.logger import logger
from app.core.config import settings

# How often to poll Gmail for new messages (seconds)
POLL_INTERVAL_SECONDS = 60


class GmailAgent(BaseAgent):
    """
    Production Gmail Agent.

    Authentication: OAuth2 via google-auth / google-api-python-client.
    - If GMAIL_TOKEN_JSON is set in .env, loads token from that path.
    - Falls back gracefully if credentials are not configured.

    Polling: a background asyncio task checks for unread messages every
    POLL_INTERVAL_SECONDS seconds.
    """

    def __init__(self, name: str):
        super().__init__(name)
        self._service = None          # Gmail API resource object
        self._poll_task: Optional[asyncio.Task] = None
        self._user_email: Optional[str] = None

    # ──────────────────────────────────────────────
    #  Lifecycle
    # ──────────────────────────────────────────────

    async def connect(self):
        """Authenticate with Gmail and start the polling loop."""
        token_path = getattr(settings, "GMAIL_TOKEN_JSON", None)
        creds_path = getattr(settings, "GMAIL_CREDENTIALS_JSON", None)

        if not token_path and not creds_path:
            logger.warning(
                "[GmailAgent] GMAIL_TOKEN_JSON / GMAIL_CREDENTIALS_JSON not set — "
                "agent will be registered but inactive."
            )
            self.state = AgentState.ERROR
            return

        try:
            service = await asyncio.to_thread(self._build_service, token_path, creds_path)
            if service is None:
                self.state = AgentState.ERROR
                return

            self._service = service

            # Get the authenticated user's email address
            profile = await asyncio.to_thread(
                lambda: service.users().getProfile(userId="me").execute()
            )
            self._user_email = profile.get("emailAddress", "unknown")
            self.state = AgentState.CONNECTED

            logger.info(f"[GmailAgent] Authenticated as {self._user_email}")

            # Start background polling loop
            self._poll_task = asyncio.create_task(
                self._polling_loop(),
                name="gmail_poll_task"
            )
            logger.info(
                f"[GmailAgent] Polling for new emails every {POLL_INTERVAL_SECONDS}s."
            )

        except ImportError:
            logger.error(
                "[GmailAgent] Google API client not installed. "
                "Run: pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib"
            )
            self.state = AgentState.ERROR
        except Exception as e:
            logger.error(f"[GmailAgent] Connection failed: {e}")
            self.state = AgentState.ERROR

    def _build_service(self, token_path: Optional[str], creds_path: Optional[str]):
        """Synchronous helper — build the Gmail API service object."""
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from google.auth.transport.requests import Request
        from googleapiclient.discovery import build
        import os

        SCOPES = [
            "https://www.googleapis.com/auth/gmail.readonly",
            "https://www.googleapis.com/auth/gmail.send",
            "https://www.googleapis.com/auth/gmail.modify",
        ]

        creds = None

        # Load saved token
        if token_path and os.path.exists(token_path):
            creds = Credentials.from_authorized_user_file(token_path, SCOPES)

        # Refresh or run OAuth flow
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            elif creds_path and os.path.exists(creds_path):
                flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
                creds = flow.run_local_server(port=0)
            else:
                logger.warning("[GmailAgent] No valid credentials found.")
                return None

            # Persist refreshed token
            if token_path:
                with open(token_path, "w") as f:
                    f.write(creds.to_json())

        return build("gmail", "v1", credentials=creds)

    async def disconnect(self):
        """Cancel the polling loop."""
        if self._poll_task and not self._poll_task.done():
            self._poll_task.cancel()
        self.state = AgentState.STOPPED
        logger.info("[GmailAgent] Disconnected.")

    # ──────────────────────────────────────────────
    #  Polling loop
    # ──────────────────────────────────────────────

    async def _polling_loop(self):
        """Periodically fetch unread emails and process them."""
        while True:
            try:
                await self.listen()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[GmailAgent] Polling error: {e}")
            await asyncio.sleep(POLL_INTERVAL_SECONDS)

    async def listen(self, raw_message=None):
        """
        Fetch unread emails from Gmail inbox and push them through the
        ReplyOrchestrator. If raw_message is provided, process only that one.
        """
        if self._service is None:
            return

        try:
            if raw_message:
                messages_data = [raw_message]
            else:
                # List unread messages in INBOX
                result = await asyncio.to_thread(
                    lambda: self._service.users().messages().list(
                        userId="me",
                        labelIds=["INBOX", "UNREAD"],
                        maxResults=10
                    ).execute()
                )
                messages_data = result.get("messages", [])

            if not messages_data:
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

                # Ensure our Gmail account is registered
                account = await acc_service.create_account(
                    user_id=1,
                    platform_name="gmail",
                    platform_user_id=self._user_email,
                    username=self._user_email,
                    display_name="Gmail Bot",
                    email=self._user_email,
                )

                orchestrator = ReplyOrchestrator(db)

                for msg_ref in messages_data:
                    msg_id = msg_ref["id"]
                    try:
                        await self._process_one_email(
                            msg_id=msg_id,
                            account=account,
                            acc_service=acc_service,
                            conv_service=conv_service,
                            msg_service=msg_service,
                            orchestrator=orchestrator,
                        )
                        # Mark as read to avoid reprocessing
                        await asyncio.to_thread(
                            lambda: self._service.users().messages().modify(
                                userId="me",
                                id=msg_id,
                                body={"removeLabelIds": ["UNREAD"]}
                            ).execute()
                        )
                    except Exception as e:
                        logger.error(f"[GmailAgent] Failed to process email {msg_id}: {e}")

        except Exception as e:
            logger.error(f"[GmailAgent] Error in listen(): {e}")

    async def _process_one_email(
        self,
        msg_id: str,
        account,
        acc_service,
        conv_service,
        msg_service,
        orchestrator,
    ):
        """Fetch a single email, normalise it, and push to orchestrator."""
        raw = await asyncio.to_thread(
            lambda: self._service.users().messages().get(
                userId="me", id=msg_id, format="full"
            ).execute()
        )

        headers = {h["name"]: h["value"] for h in raw.get("payload", {}).get("headers", [])}
        subject = headers.get("Subject", "(no subject)")
        sender  = headers.get("From", "unknown")
        thread_id = raw.get("threadId", msg_id)

        # Extract plain-text body
        body = self._extract_body(raw.get("payload", {}))

        if not body:
            return  # Skip empty or non-text emails

        # Each Gmail thread is a Conversation
        conversation = await conv_service.get_or_create_conversation(
            platform_name="gmail",
            account_id=account.id,
            external_id=thread_id,
            title=subject,
            conversation_type="email_thread",
        )

        # Store the message
        inbound = await msg_service.create_message(
            conversation_id=conversation.id,
            external_id=msg_id,
            sender_id=sender,
            content=body,
            is_outgoing=False,
        )

        logger.info(
            f"[GmailAgent] Inbound email from {sender}: '{subject[:60]}'"
        )

        await orchestrator.handle_inbound(
            conversation_id=conversation.id,
            inbound_message_id=inbound.id,
        )

    def _extract_body(self, payload: dict) -> Optional[str]:
        """Recursively extract the plain-text part from a Gmail payload."""
        mime_type = payload.get("mimeType", "")
        body_data = payload.get("body", {}).get("data")

        if mime_type == "text/plain" and body_data:
            return base64.urlsafe_b64decode(body_data).decode("utf-8", errors="replace")

        for part in payload.get("parts", []):
            result = self._extract_body(part)
            if result:
                return result

        return None

    # ──────────────────────────────────────────────
    #  Sending
    # ──────────────────────────────────────────────

    async def send_message(self, destination: str, message: str):
        """
        Send an email reply.

        Args:
            destination: Recipient email address.
            message:     Plain-text email body.
        """
        if self._service is None:
            logger.warning("[GmailAgent] Cannot send — not connected.")
            return

        try:
            mime_msg = MIMEText(message)
            mime_msg["to"]      = destination
            mime_msg["from"]    = self._user_email
            mime_msg["subject"] = "Re: AI Clone Reply"

            raw_bytes = base64.urlsafe_b64encode(mime_msg.as_bytes()).decode("utf-8")

            await asyncio.to_thread(
                lambda: self._service.users().messages().send(
                    userId="me",
                    body={"raw": raw_bytes}
                ).execute()
            )
            logger.info(f"[GmailAgent] Email sent to {destination}: {message[:60]}")

        except Exception as e:
            logger.error(f"[GmailAgent] Failed to send email: {e}")

    # ──────────────────────────────────────────────
    #  Health
    # ──────────────────────────────────────────────

    async def health(self) -> AgentHealth:
        connected = (
            self._service is not None
            and self.state == AgentState.CONNECTED
        )
        return AgentHealth(
            name=self.name,
            state=self.state,
            connected=connected,
        )