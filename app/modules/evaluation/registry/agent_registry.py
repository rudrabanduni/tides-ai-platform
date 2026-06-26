import threading
from typing import Type, Dict, List
from app.modules.evaluation.expert_agent import ExpertAgent
from app.modules.evaluation.registry.metadata import ExpertMetadata
from app.modules.evaluation.registry.exceptions import (
    DuplicateRegistrationError,
    InvalidMetadataError,
    DisabledExpertError
)
from app.modules.evaluation.events import (
    publish_expert_registered,
    publish_expert_unregistered
)

class AgentRegistry:
    """A thread-safe registry for managing and retrieving expert agents."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._experts: Dict[str, Type[ExpertAgent]] = {}

    def register(self, expert: Type[ExpertAgent]) -> None:
        """Registers a new expert agent subclass in the registry.

        Raises:
            InvalidMetadataError: If metadata is missing or invalid.
            DuplicateRegistrationError: If an expert with the same name is already registered.
        """
        if not hasattr(expert, "metadata") or expert.metadata is None:
            raise InvalidMetadataError("Expert class does not define a 'metadata' attribute")

        metadata = expert.metadata

        # Ensure metadata is an instance of ExpertMetadata (or can be validated as such)
        if not isinstance(metadata, ExpertMetadata):
            try:
                # If it's a dict or other object, try to construct ExpertMetadata
                if isinstance(metadata, dict):
                    metadata = ExpertMetadata(**metadata)
                    expert.metadata = metadata
                else:
                    raise InvalidMetadataError("Metadata must be an instance of ExpertMetadata or a dict")
            except Exception as e:
                raise InvalidMetadataError(f"Invalid metadata structure: {e}") from e

        # Validate mandatory fields
        if not metadata.expert_name:
            raise InvalidMetadataError("Metadata field 'expert_name' cannot be empty")
        if not metadata.domain:
            raise InvalidMetadataError("Metadata field 'domain' cannot be empty")
        if not metadata.version:
            raise InvalidMetadataError("Metadata field 'version' cannot be empty")

        with self._lock:
            if metadata.expert_name in self._experts:
                raise DuplicateRegistrationError(
                    f"An expert named '{metadata.expert_name}' is already registered."
                )
            self._experts[metadata.expert_name] = expert

        publish_expert_registered(metadata.expert_name, metadata.domain)

    def unregister(self, expert_name: str) -> None:
        """Removes an expert agent from the registry."""
        with self._lock:
            if expert_name not in self._experts:
                raise KeyError(f"Expert '{expert_name}' is not registered")
            self._experts.pop(expert_name)

        publish_expert_unregistered(expert_name)

    def get(self, expert_name: str) -> Type[ExpertAgent]:
        """Retrieves a registered expert class by name.

        Raises:
            KeyError: If the expert is not registered.
            DisabledExpertError: If the expert is disabled.
        """
        with self._lock:
            if expert_name not in self._experts:
                raise KeyError(f"Expert '{expert_name}' is not registered")
            expert = self._experts[expert_name]
            
            # Check if enabled
            if not getattr(expert.metadata, "enabled", True):
                raise DisabledExpertError(f"Expert '{expert_name}' is disabled and cannot be retrieved for execution")
            
            return expert

    def list(self) -> Dict[str, Type[ExpertAgent]]:
        """Returns an immutable read-only snapshot (copy) of the current registry contents."""
        with self._lock:
            return dict(self._experts)

    def list_enabled(self) -> List[Type[ExpertAgent]]:
        """Returns a list of all enabled expert agent classes."""
        with self._lock:
            return [exp for exp in self._experts.values() if getattr(exp.metadata, "enabled", True)]

    def exists(self, expert_name: str) -> bool:
        """Checks whether an expert agent is registered (regardless of enabled/disabled state)."""
        with self._lock:
            return expert_name in self._experts
