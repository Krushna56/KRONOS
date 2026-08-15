from typing import Dict, Type
from app.agents.base import BaseAgent


class Agentregistry:

    def __init__(self):
        self.registry: Dict[str, Type[BaseAgent]] = {}

    def register(
        self,
        name,
        cls
    ):
        self.registry[name] = cls

    def get(self, name):
        return self.registry.get(name)

    
