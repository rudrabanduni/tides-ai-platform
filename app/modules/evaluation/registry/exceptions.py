class RegistryError(Exception):
    """Base exception class for all registry errors."""
    pass

class DuplicateRegistrationError(RegistryError):
    """Raised when registering an expert name that already exists in the registry."""
    pass

class InvalidMetadataError(RegistryError):
    """Raised when expert metadata is invalid or missing required fields."""
    pass

class DisabledExpertError(RegistryError):
    """Raised when requesting execution of a disabled expert."""
    pass
