from app.agents.base import BaseAgent
from app.agents.schemas import AgentHealth
from app.agents.enums import AgentState

class LinkedInAgent(BaseAgent):
    async def connect(self):
        self.state = AgentState.CONNECTED
        
    async def disconnect(self):
        self.state = AgentState.STOPPED

    async def listen(self):
        pass

    async def send_message(self, destination, message):
        print(f"LinkedIn agent sending to {destination}: {message}")
    
    async def health(self):
        return AgentHealth(
            name = self.name,
            state = self.state,
            connected = self.state == AgentState.CONNECTED
        )
