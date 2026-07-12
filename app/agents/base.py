from abc import ABC, abstractmethod
from .enums import AgentState

class BaseAgent(ABC):

    def __init__(self, name: str):
        self.name = name
        self.state = AgentState.IDLE
    
    @abstractmethod
    async def connect(self):
        pass

    @abstractmethod
    async def disconnect(self):
        pass

    @abstractmethod
    async def listen(self):
        pass
    
    @abstractmethod
    async def send_message(
        self,
        destination,
        message
    ):
        pass

    @abstractmethod
    async def health(self):
        pass