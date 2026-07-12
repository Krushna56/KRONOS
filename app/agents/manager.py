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

    def add(self, agent:BaseAgent):
        self.agents[agent.name] = agent
    
    def get(self, name):
        return self.agents.get(name)

    async def disconnect_all(self):
        
        for agent in self.agents.values():
            await agent.disconnect()
    
    async def health(self):
        result = []
        for agent in self.agents.values():
            result.append(
                await agent.health()
            )
        
        return result

        
    
    


agent_manager = AgentManager()
