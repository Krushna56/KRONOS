import unittest
from app.services.ai.prompt_builder import PromptBuilder
from app.services.ai.llm_service import LLMService


class TestAIEngine(unittest.IsolatedAsyncioTestCase):
    async def test_prompt_builder(self):
        sys_prompt = PromptBuilder.build_system_prompt("KRONOS")
        self.assertIn("KRONOS", sys_prompt)

        user_prompt = PromptBuilder.build_user_prompt("Hello", context="TestContext")
        self.assertIn("Hello", user_prompt)
        self.assertIn("TestContext", user_prompt)

    async def test_llm_service_generation(self):
        service = LLMService()
        response = await service.generate_response(prompt="Status report", system_prompt="System instructions")
        self.assertIsInstance(response, str)
        self.assertTrue(len(response) > 0)


if __name__ == "__main__":
    unittest.main()