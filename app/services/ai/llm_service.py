from app.core.logger import logger

class LLMService:
    def __init__(self, api_key: str = None):
        self.api_key = api_key

    async def generate_response(self, prompt: str, system_prompt: str = None) -> str:
        """Mock generate response from LLM."""
        logger.info(f"Generating LLM response for prompt: '{prompt}'")
        return f"Mock response for prompt: '{prompt}'"

llm_service = LLMService()
