"""
LLM Service — Gemini AI Integration
Provides a unified async interface for generating AI responses.
Uses Google Gemini (primary) with graceful fallback logging.
"""

import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# ── Gemini SDK lazy import ──────────────────────────────────────────────────
_GEMINI_AVAILABLE = False
try:
    import google.generativeai as genai
    _GEMINI_AVAILABLE = True
except ImportError:
    logger.warning(
        "[LLMService] 'google-generativeai' not installed. "
        "Run: pip install google-generativeai"
    )


class LLMService:
    """
    Async LLM service backed by Google Gemini Flash.

    Model: gemini-2.0-flash (fast, low-cost, high quality)
    Fallback: Returns a polite error string if the API is unavailable.
    """

    MODEL_NAME = "gemini-3.8-flash"

    def __init__(self, api_key: Optional[str] = None):
        # Prefer explicit key → settings → env var
        if api_key:
            self.api_key = api_key
        else:
            try:
                from app.core.config import settings
                self.api_key = settings.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY", "")
            except Exception:
                self.api_key = os.getenv("GEMINI_API_KEY", "")
        self._model = None

        if _GEMINI_AVAILABLE and self.api_key:
            try:
                genai.configure(api_key=self.api_key)
                self._model = genai.GenerativeModel(self.MODEL_NAME)
                logger.info(
                    f"[LLMService] Gemini '{self.MODEL_NAME}' initialized."
                )
            except Exception as e:
                logger.error(f"[LLMService] Failed to initialize Gemini model: {e}")
        elif not self.api_key:
            logger.warning(
                "[LLMService] GEMINI_API_KEY not set — LLM will return fallback responses."
            )

    async def generate_response(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> str:
        """
        Generate a response from Gemini.

        Args:
            prompt:        The user / conversation turn content.
            system_prompt: Optional system/persona instructions.
            temperature:   Creativity dial (0.0 = deterministic, 1.0 = creative).
            max_tokens:    Maximum output tokens.

        Returns:
            AI-generated response string.
        """
        if not self._model:
            logger.warning("[LLMService] No model available — returning fallback.")
            return (
                "I'm currently unable to process that request. "
                "Please ensure the GEMINI_API_KEY is configured."
            )

        try:
            # Build the full prompt: system + user
            full_prompt = ""
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n---\n\n"
            full_prompt += prompt

            generation_config = genai.types.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
            )

            # Gemini async API
            response = await self._model.generate_content_async(
                full_prompt,
                generation_config=generation_config,
            )

            text = response.text.strip() if response.text else ""
            if not text:
                logger.warning("[LLMService] Gemini returned empty response.")
                return "I didn't have a response for that. Could you rephrase?"

            logger.info(
                f"[LLMService] Generated {len(text)} chars via Gemini."
            )
            return text

        except Exception as e:
            logger.error(f"[LLMService] Generation error: {e}")
            return (
                "I encountered an error while generating a response. "
                "Please try again shortly."
            )


# ── Global singleton ────────────────────────────────────────────────────────
llm_service = LLMService()
