# pyrefly: ignore [missing-import]
from pydantic import BaseModel
from .enums import AgentState

class AgentHealth(BaseModel):
    name : str
    state : AgentState
    connected: bool

