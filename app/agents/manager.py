from app.core.logger import logger
from app.agents.base import BaseAgent
from typing import Dict


class AgentManager:
    def __init__(self):
        self.agents: Dict[str, BaseAgent] = {}
        logger.info("Agent Manager initialized")

    async def run_agent(self, task_description: str) -> dict:
        logger.info(f"Agent Manager running task: {task_description}")
        return {"status": "success", "result": f"Completed task: {task_description}"}

    def add(self, agent: BaseAgent):
        self.agents[agent.name] = agent

    def get(self, name: str):
        return self.agents.get(name)

    async def connect_all(self):
        """Connect every registered agent on startup."""
        for agent in self.agents.values():
            try:
                await agent.connect()
                logger.info(f"Agent '{agent.name}' connected successfully.")
            except Exception as e:
                logger.warning(f"Agent '{agent.name}' failed to connect: {e}")

    async def disconnect_all(self):
        """Gracefully disconnect every registered agent on shutdown."""
        for agent in self.agents.values():
            try:
                await agent.disconnect()
                logger.info(f"Agent '{agent.name}' disconnected.")
            except Exception as e:
                logger.warning(f"Agent '{agent.name}' failed to disconnect cleanly: {e}")

    async def health(self):
        """Return health status of all registered agents."""
        result = []
        for agent in self.agents.values():
            result.append(await agent.health())
        return result


agent_manager = AgentManager()
