class AIError(Exception):
    """Base exception for AI gateway failures."""


class AIDisabledError(AIError):
    """Raised when AI features are disabled or no provider is configured."""


class AIProviderError(AIError):
    """Raised when an AI provider call fails."""


class AIResponseParseError(AIError):
    """Raised when an AI response cannot be parsed or validated."""
