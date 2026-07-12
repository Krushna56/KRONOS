from enum import Enum


class AgentState(str, Enum):

    IDLE = "idle"

    CONNECTING = "connecting"

    CONNECTED = "connected"

    LISTENING = "listening"

    STOPPED = "stopped"

    ERROR = "error"