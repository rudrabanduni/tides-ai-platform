class AssessmentValidationError(Exception):
    """Exception raised when an expert agent's assessment fails structural or semantic validations."""

    def __init__(self, message: str, errors: list[str] | None = None) -> None:
        super().__init__(message)
        self.errors = errors or []
