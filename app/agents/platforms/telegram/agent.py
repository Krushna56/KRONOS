"""
Telegram Agent — Module 10
Full python-telegram-bot integration:
  - Connects via Bot API long polling in a background task
  - Handles text messages, commands, and group messages
  - Routes inbound messages through the ReplyOrchestrator
  - Provides send_message() to dispatch AI replies
"""

import asyncio
from typing import Optional

from app.agents.base import BaseAgent
from app.agents.schemas import AgentHealth
from app.agents.enums import AgentState
from app.core.logger import logger
from app.core.config import settings


class TelegramAgent(BaseAgent):
    """
    Production Telegram Agent using python-telegram-bot (v20+, async).

    Uses Application-based long polling so it runs alongside FastAPI
    inside the same asyncio event loop.
    """

    def __init__(self, name: str):
        super().__init__(name)
        self._application = None
        self._poll_task: Optional[asyncio.Task] = None

    # ──────────────────────────────────────────────
    #  Lifecycle
    # ──────────────────────────────────────────────

    async def connect(self):
        """Initialize the Telegram bot and start long polling in background."""
        token = getattr(settings, "TELEGRAM_BOT_TOKEN", None)
        if not token:
            logger.warning(
                "[TelegramAgent] TELEGRAM_BOT_TOKEN not set in .env — "
                "agent will be registered but inactive."
            )
            self.state = AgentState.ERROR
            return

        try:
            from telegram.ext import (
                ApplicationBuilder,
                MessageHandler,
                filters,
            )
            from telegram import Update

            app = (
                ApplicationBuilder()
                .token(token)
                .build()
            )
            self._application = app

            # Register message handler
            app.add_handler(
                MessageHandler(filters.TEXT & ~filters.COMMAND, self._on_message)
            )

            # Initialize and start polling in a background task
            self.state = AgentState.CONNECTING
            self._poll_task = asyncio.create_task(
                self._run_polling(app),
                name="telegram_poll_task"
            )
            logger.info("[TelegramAgent] Long polling task started.")

        except ImportError:
            logger.error(
                "[TelegramAgent] 'python-telegram-bot' is not installed. "
                "Run: pip install python-telegram-bot"
            )
            self.state = AgentState.ERROR
        except Exception as e:
            logger.error(f"[TelegramAgent] Unexpected error during connect: {e}")
            self.state = AgentState.ERROR

    async def _run_polling(self, app):
        """Run bot in polling mode (runs inside asyncio event loop)."""
        try:
            await app.initialize()
            await app.start()
            self.state = AgentState.CONNECTED
            me = await app.bot.get_me()
            logger.info(
                f"[TelegramAgent] Bot online: @{me.username} (id={me.id})"
            )
            await app.updater.start_polling(drop_pending_updates=True)
            # Keep alive — updater blocks until stop() is called
            await app.updater.idle()
        except asyncio.CancelledError:
            pass
        except Exception as e:
            self.state = AgentState.ERROR
            logger.error(f"[TelegramAgent] Polling error: {e}")
        finally:
            try:
                await app.updater.stop()
                await app.stop()
                await app.shutdown()
            except Exception:
                pass

    async def disconnect(self):
        """Gracefully shut down the Telegram bot."""
        try:
            if self._poll_task and not self._poll_task.done():
                self._poll_task.cancel()
                await asyncio.sleep(0.5)
            if self._application:
                try:
                    await self._application.updater.stop()
                    await self._application.stop()
                    await self._application.shutdown()
                except Exception:
                    pass
            logger.info("[TelegramAgent] Bot stopped.")
        except Exception as e:
            logger.warning(f"[TelegramAgent] Error during disconnect: {e}")
        finally:
            self.state = AgentState.STOPPED

    # ──────────────────────────────────────────────
    #  Message handling
    # ──────────────────────────────────────────────

    async def _on_message(self, update, context):
        """Internal callback called by python-telegram-bot on new messages."""
        if update.message is None:
            return
        await self.listen(update)

    async def listen(self, update=None):
        """
        Normalise a Telegram update and push it through the ReplyOrchestrator.
        """
        if update is None:
            return

        message = update.message
        if not message or not message.text:
            return

        try:
            from app.db.session import AsyncSessionLocal
            from app.services.social_services import (
                SocialAccountService,
                ConversationService,
                MessageService,
            )
            from app.services.reply_orchestrator import ReplyOrchestrator

            # Determine conversation type
            chat_type = message.chat.type  # "private", "group", "supergroup", "channel"
            conv_type = "direct" if chat_type == "private" else "group"

            async with AsyncSessionLocal() as db:
                acc_service  = SocialAccountService(db)
                conv_service = ConversationService(db)
                msg_service  = MessageService(db)

                # Get bot info for the account record
                bot_user = await self._application.bot.get_me()

                # 1. Ensure SocialAccount exists for this bot
                account = await acc_service.create_account(
                    user_id=1,
                    platform_name="telegram",
                    platform_user_id=str(bot_user.id),
                    username=bot_user.username or str(bot_user.id),
                    display_name=bot_user.full_name,
                )

                # 2. Get or create conversation (keyed by Telegram chat_id)
                conversation = await conv_service.get_or_create_conversation(
                    platform_name="telegram",
                    account_id=account.id,
                    external_id=str(message.chat_id),
                    title=message.chat.title or message.chat.full_name or str(message.chat_id),
                    conversation_type=conv_type,
                )

                # 3. Store inbound message
                inbound = await msg_service.create_message(
                    conversation_id=conversation.id,
                    external_id=str(message.message_id),
                    sender_id=str(message.from_user.id),
                    content=message.text,
                    is_outgoing=False,
                )

                logger.info(
                    f"[TelegramAgent] Inbound from @{message.from_user.username or message.from_user.id} "
                    f"in chat {message.chat_id}: {message.text[:60]}"
                )

                # 4. Route to orchestrator
                orchestrator = ReplyOrchestrator(db)
                await orchestrator.handle_inbound(
                    conversation_id=conversation.id,
                    inbound_message_id=inbound.id,
                )

        except Exception as e:
            logger.error(f"[TelegramAgent] Error handling inbound message: {e}")

    async def send_message(self, destination: str, message: str):
        """
        Send a text message to a Telegram chat.

        Args:
            destination: Telegram chat_id (as string).
            message:     Text to send.
        """
        if not self._application:
            logger.warning("[TelegramAgent] Cannot send — bot not connected.")
            return

        try:
            await self._application.bot.send_message(
                chat_id=int(destination),
                text=message,
            )
            logger.info(
                f"[TelegramAgent] Sent to chat {destination}: {message[:60]}"
            )
        except Exception as e:
            logger.error(f"[TelegramAgent] Failed to send message: {e}")

    # ──────────────────────────────────────────────
    #  Health
    # ──────────────────────────────────────────────

    async def health(self) -> AgentHealth:
        connected = (
            self._application is not None
            and self.state == AgentState.CONNECTED
        )
        return AgentHealth(
            name=self.name,
            state=self.state,
            connected=connected,
        )