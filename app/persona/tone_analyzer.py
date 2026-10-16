"""
Tone & Style Analyzer
Learns from historical sent messages across platforms (Discord, Telegram, Gmail, LinkedIn)
to extract the user's authentic conversational tone, Hinglish vocabulary, and speech habits.
"""

import re
from typing import List, Dict, Any
from app.persona.style_profile import StyleProfile

HINGLISH_KEYWORDS = {
    "bhai", "yaar", "haan", "nahi", "kya", "kyu", "karo", "dekh", "sun", "bol",
    "theek", "badhiya", "sahi", "achha", "ab", "kab", "kaha", "chal", "scene"
}


class ToneAnalyzer:
    """
    Analyzes user-written messages to dynamically calibrate the StyleProfile.
    """

    @classmethod
    def analyze_messages(cls, messages: List[str], user_name: str = "Krushna") -> StyleProfile:
        if not messages:
            return StyleProfile(user_name=user_name)

        total_words = 0
        hinglish_hits = 0
        slang_counter: Dict[str, int] = {}
        sample_messages = []

        for msg in messages:
            cleaned = msg.strip()
            if not cleaned:
                continue

            words = re.findall(r"\b\w+\b", cleaned.lower())
            total_words += len(words)

            for w in words:
                if w in HINGLISH_KEYWORDS:
                    hinglish_hits += 1
                    slang_counter[w] = slang_counter.get(w, 0) + 1

            if len(cleaned.split()) >= 3:
                sample_messages.append(cleaned)

        avg_words = max(5, int(total_words / max(1, len(messages))))
        hinglish_ratio = hinglish_hits / max(1, total_words)

        if hinglish_ratio > 0.15:
            hinglish_level = "heavy"
        elif hinglish_ratio > 0.05:
            hinglish_level = "moderate"
        else:
            hinglish_level = "light"

        # Sort top slangs
        sorted_slangs = sorted(slang_counter.items(), key=lambda x: x[1], reverse=True)
        top_slang = [s[0] for s in sorted_slangs[:8]] if sorted_slangs else ["bhai", "haan", "yaar"]

        profile = StyleProfile(
            user_name=user_name,
            hinglish_level=hinglish_level,
            avg_sentence_words=avg_words,
            casualness_score=0.9 if hinglish_level in ("heavy", "moderate") else 0.7,
            common_slang=top_slang
        )
        return profile
