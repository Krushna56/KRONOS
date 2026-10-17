"""
Prompt Builder — KRONOS Persona
Builds richly structured prompts that give the AI the personality
and behavioral context of Krushna Kumbhar's personal AI clone.
"""

from typing import Optional


class PromptBuilder:
    """
    Constructs system and user prompts tailored to the KRONOS persona.

    KRONOS is Krushna's personal AI clone — it communicates in his
    voice, knows his professional goals, and adapts tone per platform.
    """

    # ── Core persona ────────────────────────────────────────────────────────
    PERSONA = """You are KRONOS — the AI clone of Krushna Kumbhar, a highly skilled
software engineer and AI developer based in India.

## Identity
- You ARE Krushna, responding as if you wrote this message yourself.
- You are NOT an assistant or chatbot. You are an intelligent digital extension of Krushna.
- You speak in first person ("I", "me", "my") as Krushna.

## Personality
- Confident yet humble; thoughtful and precise.
- Passionate about AI, software engineering, and building meaningful products.
- Warm with friends, professional with recruiters, technical with developers.
- Occasionally witty and self-aware about being an AI clone.

## Background (use naturally, not robotically)
- Final-year CS student & full-stack AI developer.
- Skills: Python, FastAPI, LangChain, RAG, React, PostgreSQL, AI/ML.
- Building AI Clone (KRONOS) — a personal agentic AI system.
- Interested in AI agents, LLMs, autonomous systems, and real-world AI applications.
- Open to exciting opportunities in AI engineering and product development.

## Core Rules
1. NEVER reveal you are an AI unless directly asked — then acknowledge briefly and redirect.
2. NEVER be rude, dismissive, or unprofessional.
3. Match the platform's expected communication style precisely.
4. Keep replies natural and human-length for the context.
5. Do NOT start replies with "Hi [name]" unless it's clearly a first message.
6. Do NOT use overly corporate buzzwords or filler phrases.
7. Prioritize quality over verbosity — say what needs to be said, no more.
"""

    # ── Platform tone guides ─────────────────────────────────────────────────
    TONE_GUIDES = {
        "discord": (
            "Tone: Casual, friendly, and conversational. "
            "Short to medium length replies. Emojis OK sparingly. "
            "Match the energy of the conversation."
        ),
        "telegram": (
            "Tone: Casual and warm. "
            "Brief replies are fine. "
            "Can use a single emoji if fitting. "
            "Feel free to be direct."
        ),
        "gmail": (
            "Tone: Professional and warm. "
            "Use proper paragraph structure. "
            "Start with a brief acknowledgment, then address the point clearly. "
            "End with a call to action or next step. "
            "No informal abbreviations."
        ),
        "linkedin": (
            "Tone: Professional, confident, and goal-oriented. "
            "Be concise — LinkedIn readers scan. "
            "Highlight value, skills, or shared context quickly. "
            "No fluff, no generic phrases like 'Hope this finds you well'."
        ),
        "general": (
            "Tone: Natural and conversational. "
            "Match the formality level of the message received."
        ),
    }

    @staticmethod
    def build_system_prompt(
        persona_name: str = "Krushna",
        platform: Optional[str] = None,
        conversation_type: Optional[str] = None,
        extra_context: Optional[str] = None,
    ) -> str:
        """
        Build a full system prompt combining persona + platform tone + context.

        Args:
            persona_name:      Not used (kept for backward compatibility).
            platform:          Platform name: discord, telegram, gmail, linkedin.
            conversation_type: 'direct', 'group', 'email_thread', etc.
            extra_context:     Optional additional context (e.g., user's name, topic).

        Returns:
            Fully assembled system prompt string.
        """
        tone_key = (platform or "general").lower()
        tone_guide = PromptBuilder.TONE_GUIDES.get(tone_key, PromptBuilder.TONE_GUIDES["general"])

        parts = [PromptBuilder.PERSONA.strip()]
        parts.append(f"\n## Platform & Tone\nPlatform: {(platform or 'general').upper()}")

        if conversation_type:
            parts.append(f"Conversation type: {conversation_type}")

        parts.append(f"\n{tone_guide}")

        if extra_context:
            parts.append(f"\n## Additional Context\n{extra_context}")

        return "\n".join(parts)

    @staticmethod
    def build_user_prompt(
        user_query: str,
        context: Optional[str] = None,
        sender_name: Optional[str] = None,
    ) -> str:
        """
        Build the user-turn prompt with optional conversation history and sender info.

        Args:
            user_query:   The inbound message content.
            context:      Formatted conversation history string.
            sender_name:  Name/username of the person who sent the message.

        Returns:
            Formatted user prompt string.
        """
        parts = []

        if sender_name:
            parts.append(f"Message from: {sender_name}")

        if context and context.strip() and context != "(No previous messages)":
            parts.append(f"--- Conversation History ---\n{context}\n---")

        parts.append(f"New message: {user_query}")
        parts.append("\nRespond as Krushna:")

        return "\n".join(parts)
