import os
import pkgutil
import importlib
import inspect
from typing import Set, Type
import app.modules.evaluation
from app.modules.evaluation.expert_agent import ExpertAgent
from app.modules.evaluation.registry.agent_registry import AgentRegistry
from app.modules.evaluation.registry.exceptions import DuplicateRegistrationError
from app.modules.evaluation.events import (
    publish_expert_discovery_started,
    publish_expert_discovery_completed,
    publish_expert_discovery_failed
)

def discover_and_register_experts(registry: AgentRegistry) -> int:
    """Scans the app.modules.evaluation package, imports all modules to discover

    subclasses of ExpertAgent, and registers them.
    
    Returns:
        The number of successfully registered expert agents.
        
    Raises:
        Exception: If the discovery or registration process fails.
    """
    package = app.modules.evaluation
    package_path = os.path.dirname(package.__file__)
    
    publish_expert_discovery_started(package_path)
    
    try:
        # Walk and import all modules inside app.modules.evaluation
        for _, module_name, is_pkg in pkgutil.walk_packages(
            package.__path__,
            package.__name__ + "."
        ):
            # Skip registry itself to avoid circular references, and skip tests
            if "registry" in module_name or "tests" in module_name:
                continue
            importlib.import_module(module_name)
            
        # Recursive subclass search to find all subclasses of ExpertAgent
        def get_all_subclasses(cls: Type) -> Set[Type]:
            subclasses = set(cls.__subclasses__())
            for subclass in list(subclasses):
                subclasses.update(get_all_subclasses(subclass))
            return subclasses

        all_subclasses = get_all_subclasses(ExpertAgent)
        
        discovered_count = 0
        for subclass in all_subclasses:
            # Filter out abstract classes
            if inspect.isabstract(subclass):
                continue
                
            # Skip subclasses defined in test files/modules
            if "test" in subclass.__module__.lower() or subclass.__module__.startswith("tests"):
                continue

            # If the subclass does not have metadata defined, skip it (e.g. abstract helper classes)
            if not hasattr(subclass, "metadata") or subclass.metadata is None:
                continue
                
            try:
                registry.register(subclass)
                discovered_count += 1
            except DuplicateRegistrationError:
                # If already registered, we can skip it or log it. For dynamic discovery,
                # duplicate class finding can happen if discovery is called multiple times.
                # We skip and do not raise to prevent discovery crash on multiple runs.
                pass
            except Exception as e:
                # For any other registration failure (e.g., InvalidMetadataError),
                # we fail the discovery process.
                raise e
                
        publish_expert_discovery_completed(discovered_count)
        return discovered_count

    except Exception as e:
        publish_expert_discovery_failed(str(e))
        raise e
