class PromptBuilder:
    @staticmethod
    def build_system_prompt(persona_name: str = "Antigravity") -> str:
        return f"You are {persona_name}, a helpful personal assistant."

    @staticmethod
    def build_user_prompt(user_query: str, context: str = "") -> str:
        return f"Context: {context}\n\nQuery: {user_query}"
