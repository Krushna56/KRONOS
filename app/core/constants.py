from enum import Enum

class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"
    SYSTEM = "system"

class WSMessageType(str, Enum):
    CHAT_MESSAGE = "chat_message"
    SYSTEM_NOTIFICATION = "system_notification"
    AGENT_STATUS = "agent_status"
    ERROR = "error"

DEFAULT_SYSTEM_PROMPT = (
    "You are Antigravity, an advanced personal AI assistant. "
    "Your goal is to help the user manage tasks, search for jobs, automate workflows, "
    "and answer complex technical and casual queries with elite-level precision and reasoning."
)
