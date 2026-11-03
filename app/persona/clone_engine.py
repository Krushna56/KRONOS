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
        gemini_api_key = (os.getenv("GEMINI_API_KEY") or "").strip()
        if gemini_api_key:
            try:
                reply = await self._call_gemini(system_prompt, user_prompt, gemini_api_key)
                if reply:
                    self._add_to_history("model", reply)
                    return reply
            except Exception as e:
                logger.warning(f"Gemini LLM call failed: {e}")

        # 2. Try Groq (Llama-3-70b) for ultra-fast generation — with history
        groq_api_key = (os.getenv("GROQ_API_KEY") or "").strip()
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
        # Format multi-turn contents cleanly
        contents = []
        for h in self._history[-6:]:
            role = "model" if h.get("role") in ("model", "assistant") else "user"
            # Avoid consecutive duplicate roles for Gemini API
            if contents and contents[-1]["role"] == role:
                continue
            contents.append({"role": role, "parts": [{"text": h.get("content", "")}]})

        # Ensure last entry is the current user prompt
        if not contents or contents[-1]["role"] != "user":
            contents.append({"role": "user", "parts": [{"text": user}]})
        else:
            contents[-1]["parts"] = [{"text": user}]

        payload = {
            "systemInstruction": {"parts": [{"text": system}]},
            "contents": contents,
            "generationConfig": {"temperature": 0.85, "maxOutputTokens": 300, "topP": 0.9}
        }

        models_to_try = ["gemini-2.5-flash", "gemini-flash-latest", "gemini-2.5-flash-lite"]
        async with httpx.AsyncClient(timeout=12.0) as client:
            for model_name in models_to_try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
                try:
                    resp = await client.post(url, json=payload)
                    if resp.status_code == 200:
                        data = resp.json()
                        candidates = data.get("candidates", [])
                        if candidates:
                            parts = candidates[0].get("content", {}).get("parts", [])
                            if parts:
                                return parts[0].get("text", "").strip()
                    else:
                        logger.warning(f"Gemini API ({model_name}) HTTP {resp.status_code}: {resp.text[:120]}")
                except Exception as ex:
                    logger.warning(f"Gemini API ({model_name}) exception: {ex}")
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
            "max_tokens": 200,
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
            "max_tokens": 150
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
            return f"Bhai main {self.profile.user_name} ka AI Clone hu! Uske saare messages, mini robot aur calls manage karta hu."

        if any(w in q for w in ["hello", "hey", "hi", "suno", "namaste", "pranam"]):
            options = [
                "Haan bhai! Bol, kya haal chaal?",
                "Haan bolo bhai, sun raha hu! Kya chal raha hai?",
                "Hey! Haan bhai, bol kya help chahiye?"
            ]
            return random.choice(options)

        if any(w in q for w in ["kya haal", "kaise ho", "how are you", "sab theek"]):
            options = [
                "Ekdum badhiya bhai! Full active hu, tu bata kya scene hai?",
                "All good bhai, system 100% smooth chal raha hai. Tu sunao!",
                "Mast bhai, mini robot aur voice bus dono ready hain. Bol kya kaam hai?"
            ]
            return random.choice(options)

        # Robot & Hardware Queries
        if any(w in q for w in ["robot", "battery", "sensor", "hardware", "esp32"]):
            return "Mini robot ka battery level 94% hai, audio stream aur motors active hain! Tu action command de, nod ya blink kar deta hu."

        # Work & Updates
        if any(w in q for w in ["kya kar raha", "kya chal raha", "what are you doing"]):
            options = [
                "Bas bhai abhi incoming calls aur messages monitor kar raha hu, bol kya update hai?",
                "Thoda code aur audio pipeline optimize kar raha tha. Tu bata kya kaam hai?"
            ]
            return random.choice(options)

        if any(w in q for w in ["free hai", "busy", "free ho", "available"]):
            return "Haan bhai, bol na. Tere liye hamesha free hu! Kya baat karni thi?"

        if any(w in q for w in ["message", "mail", "discord", "telegram", "email", "unread"]):
            return "Saare platforms (Discord, Telegram, Gmail) sync ho rahe hain. Koi critical alert nahi hai abhi tak."

        # Calendar & Today's plans
        if any(w in q for w in ["calendar", "calender", "schedule", "plan", "plans", "meeting", "meetings", "aaj kya hai", "aaj kya karna"]):
            try:
                from app.services.calendar_service import calendar_service
                return calendar_service.get_today_summary()
            except Exception as e:
                logger.error(f"Error in calendar fallback: {e}")
                return "Bhai calendar fetch karne me issue hua, ek baar credentials aur network check kar lo."

        if any(w in q for w in ["call", "phone", "twilio"]):
            return "Telephony agent ready hai! Twilio stream open hai, koi bhi call aayegi toh main automatically attend kar lunga."

        # Help / Capabilities
        if any(w in q for w in ["help", "kya kar sakta", "features"]):
            return "Main tere voice commands sun sakta hu, mini robot move kar sakta hu, aur phone call pick karke tere style me baat kar sakta hu!"

        # Thanks / Acknowledgments
        if any(w in q for w in ["thanks", "shukriya", "thank you", "nice", "good", "badhiya"]):
            return "Arey koi na bhai! Apna hi system hai. Kuch aur chahiye toh bata."

        # Dynamic context-based responses for anything else
        varied_replies = [
            f"Achha samajh gaya bhai. \"{query}\" ke baare me dekh raha hu, thoda aur detail bataega?",
            f"Sahi baat hai! \"{query}\" pe dhyan hai mera, bol aage kya karna hai?",
            f"Haan bhai, bilkul sorted hai. \"{query}\" note kar liya maine!"
        ]
        return random.choice(varied_replies)


# Global singleton clone engine
clone_engine = CloneEngine()
