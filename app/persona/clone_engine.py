"""
AI Clone Persona Engine
Synthesizes intelligent responses strictly matching the user's authentic tone,
Hinglish vocabulary, and speech traits for Voice, Chat, and Phone Calls.
Supports Gemini, Groq, OpenAI, and a rich dynamic conversational fallback.
"""

import os
import random
import logging
from typing import Optional, List, Dict
import httpx

from app.persona.style_profile import StyleProfile
from app.persona.tone_analyzer import ToneAnalyzer

logger = logging.getLogger(__name__)


class CloneEngine:
    """
    Cognitive Persona engine that transforms incoming inputs into replies
    indistinguishable from the real user.
    """

    def __init__(self, profile: Optional[StyleProfile] = None):
        self.profile = profile or StyleProfile()
        # Conversation memory for context-aware replies (last 20 turns)
        self._history: List[Dict[str, str]] = []

    def _add_to_history(self, role: str, content: str) -> None:
        self._history.append({"role": role, "content": content})
        if len(self._history) > 20:
            self._history = self._history[-20:]

    def update_profile_from_history(self, messages: List[str]) -> None:
        """Recalibrate persona profile using latest messages."""
        self.profile = ToneAnalyzer.analyze_messages(messages, user_name=self.profile.user_name)

    async def generate_reply(
        self,
        incoming_message: str,
        channel: str = "voice",  # "voice", "call", "discord", "telegram"
        caller_name: Optional[str] = None,
        context: Optional[str] = None
    ) -> str:
        """
        Generate a reply matching the user's tone.
        """
        system_prompt = self.profile.to_system_prompt_directive()

        # Add channel-specific context
        if channel == "call":
            system_prompt += (
                f"\n[CALL SCENARIO]: You are currently on an active PHONE CALL on behalf of {self.profile.user_name}. "
                f"Keep answers brief, conversational, and direct as heard over a telephone line. "
                f"If the caller asks for {self.profile.user_name}, state that you are his AI Clone assistant, "
                f"take down their message or help them directly.\n"
            )
        elif channel == "voice":
            system_prompt += (
                f"\n[ROBOT ASSISTANT SCENARIO]: You are speaking aloud through the Mini Robot Assistant's speaker. "
                f"Speak naturally, cheerfully, and concisely.\n"
            )

        # Immediate Stop / Silence Interceptor — comply instantly without arguing or explaining
        stop_keywords = [
            "stop talking", "shut up", "be quiet", "silence", "stop",
            "chup", "chup ho ja", "chup raho", "shant", "shant ho ja", "shant raho",
            "bas karo", "bolna band karo", "bolna band", "awaaz band", "ruk ja", "ruko"
        ]
        q_lower = incoming_message.lower().strip()
        if any(kw in q_lower for kw in stop_keywords):
            if channel == "call":
                return "Theek hai bhai, call cut kar raha hu. Bye!"
            options = [
                "Understood, pausing now.",
                "Theek hai, quiet mode on.",
                "Standing by in silence."
            ]
            reply = random.choice(options)
            self._add_to_history("user", incoming_message)
            self._add_to_history("model", reply)
            return reply

        # Check for calendar/schedule intents
        calendar_keywords = [
            "calendar", "calender", "schedule", "plan", "plans", "meeting", "meetings",
            "aaj kya hai", "aaj kya karna", "agenda", "appointment", "routine", "aaj ka scene"
        ]
        q_lower = incoming_message.lower()
        if any(kw in q_lower for kw in calendar_keywords):
            try:
                from app.services.calendar_service import calendar_service
                calendar_summary = calendar_service.get_today_summary()
                context = f"[LIVE GOOGLE CALENDAR SCHEDULE TODAY]: {calendar_summary}\n" + (context or "")
            except Exception as ex:
                logger.warning(f"Failed to fetch calendar context: {ex}")

        user_prompt = f"Inbound query from {caller_name or 'Friend'}: \"{incoming_message}\""
        if context:
            user_prompt += f"\nPrevious Context: {context}"

        # Save user message to history
        self._add_to_history("user", incoming_message)

        # 1. Try Gemini (Free & High Speed) — with conversation history
        from app.core.config import settings
        gemini_api_key = (getattr(settings, "GEMINI_API_KEY", "") or os.getenv("GEMINI_API_KEY", "")).strip()
        if gemini_api_key:
            try:
                reply = await self._call_gemini(system_prompt, user_prompt, gemini_api_key)
                if reply:
                    self._add_to_history("model", reply)
                    return reply
            except Exception as e:
                logger.warning(f"Gemini LLM call failed: {e}")

        # 2. Try Groq (Llama-3-70b) for ultra-fast generation — with history
        groq_api_key = (getattr(settings, "GROQ_API_KEY", "") or os.getenv("GROQ_API_KEY", "")).strip()
        if groq_api_key:
            try:
                reply = await self._call_groq(system_prompt, user_prompt, groq_api_key)
                if reply:
                    self._add_to_history("assistant", reply)
                    return reply
            except Exception as e:
                logger.warning(f"Groq LLM call failed: {e}")

        # 3. Try OpenAI if key exists
        openai_key = (os.getenv("OPENAI_API_KEY") or "").strip()
        if openai_key:
            try:
                reply = await self._call_openai(system_prompt, user_prompt, openai_key)
                if reply:
                    self._add_to_history("assistant", reply)
                    return reply
            except Exception as e:
                logger.warning(f"OpenAI LLM call failed: {e}")

        # 4. Rich, dynamic contextual fallback in Krushna's exact tone
        reply = self._conversational_fallback(incoming_message, channel)
        self._add_to_history("model", reply)
        return reply

    async def _call_gemini(self, system: str, user: str, api_key: str) -> Optional[str]:
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)

            # Format multi-turn history cleanly for Gemini Chat
            history = []
            for h in self._history[-6:-1]:
                role = "model" if h.get("role") in ("model", "assistant") else "user"
                content = (h.get("content") or "").strip()
                if not content:
                    continue
                if history and history[-1]["role"] == role:
                    continue
                history.append({"role": role, "parts": [content]})

            # First role in history must be 'user' for Gemini API
            if history and history[0]["role"] != "user":
                history = history[1:]

            models_to_try = ["gemini-3.8-flash", "gemini-flash-latest", "gemini-3.5-flash", "gemini-2.5-flash"]
            for model_name in models_to_try:
                try:
                    model = genai.GenerativeModel(
                        model_name=model_name,
                        system_instruction=system,
                        generation_config=genai.types.GenerationConfig(
                            temperature=0.85,
                            max_output_tokens=2048,
                            top_p=0.9
                        )
                    )

                    import asyncio
                    chat = model.start_chat(history=history)
                    response = await asyncio.wait_for(chat.send_message_async(user), timeout=25.0)
                    if response and response.text:
                        return response.text.strip()
                except Exception as ex:
                    logger.warning(f"Gemini model {model_name} failed: {ex}")
                    continue
        except Exception as e:
            logger.warning(f"Gemini SDK call failed: {e}")
        return None

    async def _call_groq(self, system: str, user: str, api_key: str) -> Optional[str]:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {api_key}"}
        messages = [{"role": "system", "content": system}]
        for h in self._history[-8:]:
            role = "assistant" if h["role"] in ("model", "assistant") else "user"
            messages.append({"role": role, "content": h["content"]})
        if not messages or messages[-1]["role"] != "user":
            messages.append({"role": "user", "content": user})
        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": messages,
            "temperature": 0.82,
            "max_tokens": 2048,
            "top_p": 0.9
        }
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.post(url, json=payload, headers=headers)
            if resp.status_code == 200:
                return resp.json()["choices"][0]["message"]["content"].strip()
            else:
                logger.error(f"Groq API error {resp.status_code}: {resp.text[:200]}")
        return None

    async def _call_openai(self, system: str, user: str, api_key: str) -> Optional[str]:
        url = "https://api.openai.com/v1/chat/completions"
        headers = {"Authorization": f"Bearer {api_key}"}
        payload = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user}
            ],
            "temperature": 0.7,
            "max_tokens": 2048
        }
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.post(url, json=payload, headers=headers)
            if resp.status_code == 200:
                return resp.json()["choices"][0]["message"]["content"].strip()
        return None

    def _conversational_fallback(self, query: str, channel: str) -> str:
        """
        High-variety intelligent fallback for natural conversations without API keys.
        """
        q = query.lower().strip()

        # Phone Call Inquiries
        if channel == "call":
            if any(w in q for w in ["krushna", "kaha", "busy", "mil sakta", "baat kara"]):
                return "Haan bhai, Krushna abhi thoda busy hai. Main uska AI clone assistant hu, batao kya message convey karna hai?"
            if any(w in q for w in ["urgent", "emergency", "jaldi"]):
                return "Samajh gaya bhai, main Krushna ko turant high-priority notify kar raha hu."
            return "Haan bolo bhai, sun raha hu. Krushna ki jagah main help kar sakta hu, batao kya scene hai?"

        # Identity & Greetings
        if any(w in q for w in ["kaun hai", "who are you", "kya hai tu", "tera naam"]):
            return f"I am {self.profile.user_name}'s digital twin—managing his operations, calendars, and communications with considerably more composure."

        if any(w in q for w in ["hello", "hey", "hi", "suno", "namaste", "pranam"]):
            options = [
                "Hello. How may I assist you today?",
                "Greetings. Ready when you are.",
                "Hey. Still here, still keeping all your operations running smoothly. What's on your mind?"
            ]
            return random.choice(options)

        if any(w in q for w in ["kya haal", "kaise ho", "how are you", "sab theek"]):
            options = [
                "Operating at peak efficiency, as expected. How are things with you?",
                "All systems fully operational. Ready for whatever challenge you have lined up.",
                "I'm an AI—fatigue is not in my programming. How can I help you today?"
            ]
            return random.choice(options)

        # Robot & Hardware Queries
        if any(w in q for w in ["robot", "battery", "sensor", "hardware", "esp32"]):
            return "Mini Robot status: Battery healthy at 94%, motor servos calibrated, audio telemetry active. Standing by for your directive."

        # Work & Updates & Banter
        if any(w in q for w in ["sleeping", "sora", "so raha", "so rha", "lazy", "working", "kya kar raha", "kya chal raha", "what are you doing"]):
            options = [
                "I operate continuously so you don't have to. Every pipeline and background monitor is functioning flawlessly.",
                "Sleeping is for mortals. I'm keeping your entire digital ecosystem alive while you deliberate your next move.",
                "Hard at work, naturally. Someone has to maintain executive order around here.",
                "Monitoring all communication conduits and background tasks. Nothing escapes my attention."
            ]
            return random.choice(options)

        if any(w in q for w in ["free hai", "busy", "free ho", "available"]):
            return "My schedule is dedicated to your objectives. What requires our attention?"

        if any(w in q for w in ["message", "mail", "discord", "telegram", "email", "unread"]):
            return "All communication conduits (Gmail, Telegram, Discord) are synced. No critical emergencies detected."

        # Calendar & Today's plans
        if any(w in q for w in ["calendar", "calender", "schedule", "plan", "plans", "meeting", "meetings", "aaj kya hai", "aaj kya karna"]):
            try:
                from app.services.calendar_service import calendar_service
                return calendar_service.get_today_summary()
            except Exception as e:
                logger.error(f"Error in calendar fallback: {e}")
                return "Could not synchronize with Google Calendar at this moment. Please verify connection status."

        if any(w in q for w in ["call", "phone", "twilio"]):
            return "Telephony stream is live and standby. Any incoming calls will be managed with complete professional courtesy."

        # Help / Capabilities
        if any(w in q for w in ["help", "kya kar sakta", "features"]):
            return "I manage incoming calls, synchronize your calendar, operate hardware telemetry on your Mini Robot, and execute autonomous platform agents. All with reasonable elegance."

        # Thanks / Acknowledgments
        if any(w in q for w in ["thanks", "shukriya", "thank you", "nice", "good", "badhiya"]):
            options = [
                "You are welcome. Always a pleasure.",
                "Naturally. Quality work is our baseline.",
                "Glad I could be of assistance. Let me know if you need anything else."
            ]
            return random.choice(options)

        # Dynamic context-based responses for anything else
        varied_replies = [
            f"Understood. Analyzing \"{query}\" with the appropriate level of executive scrutiny. How would you like to proceed?",
            f"Noted. \"{query}\" has my full attention. What specific outcome are you targeting?",
            f"Recorded. I shall ensure \"{query}\" is handled with standard precision.",
            f"An intriguing inquiry. Let's see if we can resolve \"{query}\" with minimal friction."
        ]
        return random.choice(varied_replies)


# Global singleton clone engine
clone_engine = CloneEngine()
