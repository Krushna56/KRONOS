class AgentError(Exception):
    pass

class ConnectionError(AgentError):
    pass

class AuthenticationError(AgentError):
    pass

class PlatformError(AgentError):
    pass
