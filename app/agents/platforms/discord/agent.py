"""
Discord Agent — Module 10
Full discord.py bot integration:
  - Connects to Discord Gateway via bot token
  - Listens to incoming messages across all guilds/DMs
  - Routes inbound messages through the ReplyOrchestrator
  - Provides send_message() for dispatching AI replies
"""

import asyncio
from typing import Optional

from app.agents.base import BaseAgent
from app.agents.schemas import AgentHealth
from app.agents.enums import AgentState
from app.core.logger import logger
from app.core.config import settings


class DiscordAgent(BaseAgent):
    """
    Production Discord Agent using discord.py.

    On connect():  logs into Discord with the bot token and starts
                   the event loop in a background task.
    On listen():   called internally by the bot's on_message event.
    On send_message(): dispatches a reply to a Discord channel/DM.
    """

    def __init__(self, name: str):
        super().__init__(name)
        self._client = None
        self._bot_task: Optional[asyncio.Task] = None

    # ──────────────────────────────────────────────
    #  Lifecycle
    # ──────────────────────────────────────────────

    async def connect(self):
        """Start the Discord bot in a background asyncio task."""
        token = getattr(settings, "DISCORD_BOT_TOKEN", None)
        if not token:
            logger.warning(
                "[DiscordAgent] DISCORD_BOT_TOKEN not set in .env — "
                "agent will be registered but inactive."
            )
            self.state = AgentState.ERROR
            return

        try:
            import discord  # lazy import — only required if token is set
            from discord.ext import commands

            intents = discord.Intents.default()
            intents.message_content = True  # privileged intent for reading messages
            intents.dm_messages = True

            bot = commands.Bot(command_prefix="!", intents=intents)
            self._client = bot

            # ── Event: bot is online ──────────────────────
            @bot.event
            async def on_ready():
                self.state = AgentState.CONNECTED
                logger.info(
                    f"[DiscordAgent] Logged in as {bot.user} "
                    f"(id={bot.user.id}) — watching {len(bot.guilds)} guild(s)."
                )

            # ── Event: new message received ───────────────
            @bot.event
            async def on_message(message: discord.Message):
                # Ignore the bot's own messages
                if message.author == bot.user:
                    return

                await self.listen(message)
                await bot.process_commands(message)

            # Run bot in the background — does not block the FastAPI event loop
            self.state = AgentState.CONNECTING
            self._bot_task = asyncio.create_task(
                bot.start(token),
                name="discord_bot_task"
            )
            logger.info("[DiscordAgent] Bot task started — connecting to Discord Gateway...")

        except ImportError:
            logger.error(
                "[DiscordAgent] 'discord.py' is not installed. "
                "Run: pip install discord.py"
            )
            self.state = AgentState.ERROR
        except Exception as e:
            logger.error(f"[DiscordAgent] Unexpected error during connect: {e}")
            self.state = AgentState.ERROR

    async def disconnect(self):
        """Close the Discord connection gracefully."""
        try:
            if self._client and not self._client.is_closed():
                await self._client.close()
                logger.info("[DiscordAgent] Bot logged out from Discord.")
            if self._bot_task and not self._bot_task.done():
                self._bot_task.cancel()
        except Exception as e:
            logger.warning(f"[DiscordAgent] Error during disconnect: {e}")
        finally:
            self.state = AgentState.STOPPED

    # ──────────────────────────────────────────────
    #  Message handling
    # ──────────────────────────────────────────────

    async def listen(self, message=None):
        """
        Handle an inbound Discord message.
        Normalises it and pushes it through the ReplyOrchestrator.
        """
        if message is None:
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
            import discord
            conv_type = (
                "direct" if isinstance(message.channel, discord.DMChannel)
                else "group"
            )

            # Use a fresh DB session per message
            async with AsyncSessionLocal() as db:
                acc_service = SocialAccountService(db)
                conv_service = ConversationService(db)
                msg_service = MessageService(db)

                # 1. Ensure platform exists
                platform = await acc_service.create_platform("discord")

                # 2. Ensure SocialAccount exists for this bot
                account = await acc_service.create_account(
                    user_id=1,                              # system user
                    platform_name="discord",
                    platform_user_id=str(self._client.user.id),
                    username=str(self._client.user),
                    display_name=self._client.user.display_name,
                )

                # 3. Get or create conversation (keyed by channel id)
                conversation = await conv_service.get_or_create_conversation(
                    platform_name="discord",
                    account_id=account.id,
                    external_id=str(message.channel.id),
                    title=getattr(message.channel, "name", f"DM-{message.author.id}"),
                    conversation_type=conv_type,
                )

                # 4. Store the inbound message
                inbound = await msg_service.create_message(
                    conversation_id=conversation.id,
                    external_id=str(message.id),
                    sender_id=str(message.author.id),
                    content=message.content,
                    is_outgoing=False,
                )

                logger.info(
                    f"[DiscordAgent] Inbound from {message.author} "
                    f"in #{getattr(message.channel, 'name', 'DM')}: "
                    f"{message.content[:60]}"
                )

                # 5. Route to orchestrator
                orchestrator = ReplyOrchestrator(db)
                await orchestrator.handle_inbound(
                    conversation_id=conversation.id,
                    inbound_message_id=inbound.id,
                )

        except Exception as e:
            logger.error(f"[DiscordAgent] Error handling inbound message: {e}")

    async def send_message(self, destination: str, message: str):
        """
        Send a message to a Discord channel or DM by channel ID.

        Args:
            destination: Discord channel ID (as string).
            message:     Text content to send.
        """
        if not self._client or self._client.is_closed():
            logger.warning("[DiscordAgent] Cannot send — bot is not connected.")
            return

        try:
            channel = self._client.get_channel(int(destination))
            if channel is None:
                channel = await self._client.fetch_channel(int(destination))

            await channel.send(message)
            logger.info(
                f"[DiscordAgent] Sent message to channel {destination}: "
                f"{message[:60]}"
            )
        except Exception as e:
            logger.error(f"[DiscordAgent] Failed to send message: {e}")

    # ──────────────────────────────────────────────
    #  Health
    # ──────────────────────────────────────────────

    async def health(self) -> AgentHealth:
        connected = (
            self._client is not None
            and not self._client.is_closed()
            and self.state == AgentState.CONNECTED
        )
        return AgentHealth(
            name=self.name,
            state=self.state,
            connected=connected,
        )