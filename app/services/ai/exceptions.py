class AIError(Exception):
    """Base exception for AI gateway failures."""


class AIDisabledError(AIError):
    """Raised when AI features are disabled or no provider is configured."""


class AIProviderError(AIError):
    """Raised when an AI provider call fails."""


class AIProviderAuthenticationError(AIProviderError):
    """Raised when an AI provider authentication fails (e.g., 401 invalid or unauthorized API key)."""


class AIResponseParseError(AIError):
    """Raised when an AI response cannot be parsed or validated."""


class AIBudgetExhaustedError(AIError):
    """Raised when an operation would exceed the evaluation budget safety ceiling."""


class UnknownModelPricingError(AIError):
    """Raised when an AI model has no registered pricing in the catalog, enforcing fail-closed budget control."""
