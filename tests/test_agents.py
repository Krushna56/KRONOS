import unittest
import asyncio
from app.agents.manager import AgentManager
from app.agents.enums import AgentState
from app.agents.platforms.discord.agent import DiscordAgent
from app.agents.platforms.telegram.agent import TelegramAgent
from app.agents.platforms.gmail.agent import GmailAgent
from app.agents.platforms.linkedin.agent import LinkedInAgent


class TestAgentFramework(unittest.IsolatedAsyncioTestCase):
    async def test_agent_registration_and_health(self):
        manager = AgentManager()
        discord = DiscordAgent("discord")
        telegram = TelegramAgent("telegram")
        gmail = GmailAgent("gmail")
        linkedin = LinkedInAgent("linkedin")

        manager.add(discord)
        manager.add(telegram)
        manager.add(gmail)
        manager.add(linkedin)

        self.assertEqual(len(manager.agents), 4)
        self.assertIsNotNone(manager.get("discord"))
        self.assertIsNotNone(manager.get("telegram"))

        # Connect agents
        await discord.connect()
        await telegram.connect()
        self.assertEqual(discord.state, AgentState.CONNECTED)
        self.assertEqual(telegram.state, AgentState.CONNECTED)

        # Health check
        health_results = await manager.health()
        self.assertEqual(len(health_results), 4)
        discord_health = next(h for h in health_results if h.name == "discord")
        self.assertTrue(discord_health.connected)

        # Disconnect all
        await manager.disconnect_all()
        self.assertEqual(discord.state, AgentState.STOPPED)
        self.assertEqual(telegram.state, AgentState.STOPPED)


if __name__ == "__main__":
    unittest.main()
