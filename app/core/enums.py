"""
Application-wide enums.
"""

from enum import Enum


class PlatformType(str, Enum):
    DISCORD = "discord"
    TELEGRAM = "telegram"
    GMAIL = "gmail"
    LINKEDIN = "linkedin"


class ConversationType(str, Enum):
    DIRECT = "direct"
    GROUP = "group"
    CHANNEL = "channel"
    EMAIL_THREAD = "email_thread"


class MessageType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    DOCUMENT = "document"
    SYSTEM = "system"


class AgentState(str, Enum):
    IDLE = "idle"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    LISTENING = "listening"
    ERROR = "error"
    STOPPED = "stopped"


class ReplyMode(str, Enum):
    MANUAL = "manual"
    SUGGEST = "suggest"
    APPROVAL = "approval"
    AUTO = "auto"