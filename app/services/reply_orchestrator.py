"""
Reply Orchestrator - Modules 11 & 12

Cognitive loop that:
1. Receives inbound social messages
2. Retrieves tone context & memory
3. Generates AI-powered draft reply
4. Executes the correct reply mode:
   - AUTO: send immediately via agent
   - SUGGEST/APPROVAL: save draft for your review
   - MANUAL: notify you, do nothing
5. Simulates human typing delay (anti-bot safety)
"""

import asyncio
import random
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import logger
from app.core.enums import ReplyMode
from app.models.message import Message
from app.models.conversation import Conversation
from app.services.social_services import MessageService, ConversationService
from app.services.ai.llm_service import llm_service
from app.services.ai.prompt_builder import PromptBuilder
from app.repositories.social_repositories import MessageRepository, ConversationRepository
from app.agents.manager import agent_manager


class ReplyOrchestrator:
    """
    Orchestrates the full reply lifecycle for an inbound social message.

    Improvements integrated:
    - Context-aware ReplyMode selection based on conversation's reply_mode setting
    - Human simulation delay (anti-ban / anti-bot safety)
    - Persona + memory prompt enrichment
    - Draft saved to DB for SUGGEST/APPROVAL mode
    """

    TYPING_SPEED_CHARS_PER_SECOND = 8  # ~8 chars/sec = average human typing
    MIN_JITTER_SECONDS = 3
    MAX_JITTER_SECONDS = 12

    def __init__(self, db: AsyncSession):
        self.db = db
        self.msg_service = MessageService(db)
        self.conv_service = ConversationService(db)
        self.msg_repo = MessageRepository(db)
        self.conv_repo = ConversationRepository(db)

    async def handle_inbound(
        self,
        conversation_id: int,
        inbound_message_id: int
    ) -> Optional[Message]:
        """
        Main entry point. Call this whenever a new inbound message arrives.
        Returns the sent/draft reply Message, or None for MANUAL mode.
        """
        # 1. Load the conversation and inbound message
        conversation = await self.conv_repo.get_with_relations(conversation_id)
        if not conversation:
            logger.error(f"Orchestrator: Conversation {conversation_id} not found.")
            return None

        inbound_msg = await self.msg_repo.get(inbound_message_id)
        if not inbound_msg:
            logger.error(f"Orchestrator: Inbound message {inbound_message_id} not found.")
            return None

        logger.info(f"Orchestrator: Handling inbound message {inbound_message_id} for conversation {conversation_id}")

        # 2. Retrieve last N messages for conversational context
        history = await self.msg_service.list_messages_in_thread(
            conversation_id, skip=0, limit=10
        )
        history_text = self._format_history(history)

        # 3. Determine effective ReplyMode from conversation setting
        try:
            reply_mode = ReplyMode(conversation.reply_mode)
        except ValueError:
            reply_mode = ReplyMode.SUGGEST  # Safe default
            logger.warning(f"Unknown reply_mode '{conversation.reply_mode}', defaulting to SUGGEST")

        # 4. MANUAL mode: just log/notify, do nothing
        if reply_mode == ReplyMode.MANUAL:
            logger.info(
                f"[MANUAL] New message on {conversation.platform.name if conversation.platform else 'unknown'}: "
                f"'{inbound_msg.content[:60]}...'. Awaiting your manual response."
            )
            return None

        # 5. Generate AI draft
        draft_content = await self._generate_draft(
            platform_name=conversation.platform.name if conversation.platform else "general",
            conversation_type=conversation.conversation_type,
            inbound_content=inbound_msg.content,
            history_text=history_text
        )

        logger.info(f"Orchestrator: Draft generated ({len(draft_content)} chars) in mode={reply_mode.value}")

        # 6. Execute based on ReplyMode
        if reply_mode == ReplyMode.AUTO:
            return await self._send_with_human_delay(
                conversation=conversation,
                conversation_id=conversation_id,
                draft_content=draft_content
            )

        elif reply_mode in (ReplyMode.SUGGEST, ReplyMode.APPROVAL):
            # Save as a draft outgoing message (sender_id = "AI_DRAFT")
            draft_msg = await self.msg_service.create_message(
                conversation_id=conversation_id,
                external_id=f"draft_{inbound_message_id}_{random.randint(1000, 9999)}",
                sender_id="AI_DRAFT",
                content=draft_content,
                is_outgoing=True,
                reply_to_external_id=inbound_msg.external_id
            )
            logger.info(
                f"[{reply_mode.value.upper()}] Draft saved (id={draft_msg.id}). "
                f"Awaiting your approval via /api/social/drafts/{draft_msg.id}/send"
            )
            return draft_msg

        return None

    async def send_draft(
        self,
        draft_message_id: int,
        conversation_id: int
    ) -> Optional[Message]:
        """
        Called when you approve a SUGGEST/APPROVAL draft.
        Sends it via the platform agent with human delay.
        """
        draft_msg = await self.msg_repo.get(draft_message_id)
        if not draft_msg:
            logger.error(f"Draft message {draft_message_id} not found.")
            return None

        conversation = await self.conv_repo.get_with_relations(conversation_id)
        if not conversation:
            return None

        return await self._send_with_human_delay(
            conversation=conversation,
            conversation_id=conversation_id,
            draft_content=draft_msg.content
        )

    async def _send_with_human_delay(
        self,
        conversation: Conversation,
        conversation_id: int,
        draft_content: str
    ) -> Message:
        """
        Simulates human typing delay before saving and 'sending' the message.
        Delay = (word count / typing speed) + random jitter.
        """
        word_count = len(draft_content.split())
        char_count = len(draft_content)
        typing_seconds = char_count / self.TYPING_SPEED_CHARS_PER_SECOND
        jitter = random.uniform(self.MIN_JITTER_SECONDS, self.MAX_JITTER_SECONDS)
        total_delay = typing_seconds + jitter

        platform_name = conversation.platform.name if conversation.platform else "unknown"
        logger.info(
            f"[HUMAN DELAY] Waiting {total_delay:.1f}s before sending "
            f"({char_count} chars to {platform_name})"
        )

        await asyncio.sleep(total_delay)

        sent_msg = await self.msg_service.create_message(
            conversation_id=conversation_id,
            external_id=f"out_{conversation_id}_{random.randint(10000, 99999)}",
            sender_id="AI_CLONE",
            content=draft_content,
            is_outgoing=True
        )

        # Call the real platform agent if registered
        agent = agent_manager.get(platform_name.lower())
        if agent:
            try:
                destination = conversation.external_id
                await agent.send_message(destination, draft_content)
                logger.info(f"Dispatched message via {platform_name} agent to {destination}")
            except Exception as exc:
                logger.error(f"Failed to dispatch via {platform_name} agent: {exc}")

        logger.info(
            f"[SENT] Message delivered on {platform_name}: '{draft_content[:60]}...'"
        )

        return sent_msg

    async def _generate_draft(
        self,
        platform_name: str,
        conversation_type: str,
        inbound_content: str,
        history_text: str
    ) -> str:
        """
        Builds a persona-aware prompt and calls the LLM service.
        """
        # Tone rules per platform
        tone_rules = {
            "gmail": "Professional, formal. Use complete sentences and proper salutations.",
            "linkedin": "Professional, warm. Concise and goal-oriented.",
            "discord": "Casual and friendly. Short responses, conversational tone.",
            "telegram": "Casual. Can use brief replies. Emojis acceptable."
        }
        tone = tone_rules.get(platform_name.lower(), "Natural and conversational.")

        system_prompt = PromptBuilder.build_system_prompt("Krushna")
        system_prompt += f"\n\nPlatform: {platform_name.upper()} | Conversation Type: {conversation_type}"
        system_prompt += f"\nTone Rules: {tone}"

        user_prompt = PromptBuilder.build_user_prompt(
            user_query=inbound_content,
            context=f"Recent conversation history:\n{history_text}"
        )

        return await llm_service.generate_response(
            prompt=user_prompt,
            system_prompt=system_prompt
        )

    def _format_history(self, messages: list) -> str:
        """Formats message history into a readable prompt context."""
        if not messages:
            return "(No previous messages)"
        lines = []
        for msg in messages[-5:]:  # Last 5 messages for context
            role = "AI_CLONE" if msg.is_outgoing else "THEM"
            lines.append(f"[{role}]: {msg.content}")
        return "\n".join(lines)
