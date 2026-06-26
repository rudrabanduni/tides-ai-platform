import pytest
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from app.modules.intelligence.events import dispatcher
from app.modules.evaluation.expert_agent import ExpertAgent
from app.modules.evaluation.registry import (
    ExpertMetadata,
    AgentRegistry,
    discover_and_register_experts,
    DuplicateRegistrationError,
    InvalidMetadataError,
    DisabledExpertError
)

# Dummy test implementations of ExpertAgent for testing registry functions
class DummyExpertOne(ExpertAgent):
    metadata = ExpertMetadata(
        expert_name="DummyExpertOne",
        domain="dummy1",
        version="1.0.0",
        description="First dummy expert agent",
        supported_claims=["claim1"],
        supported_evidence_types=["evidence1"],
        prompt_name="dummy_one",
        prompt_version="1.0.0",
        agent_version="1.0.0",
        enabled=True,
        tags=["dummy", "one"]
    )

    def get_domain_key(self) -> str:
        return "dummy1"

    def get_agent_version(self) -> str:
        return "1.0.0"

    def validate_inputs(self, profile: Any, claims: list, evidence: list, conflicts: list, metadata: dict) -> bool:
        return True


class DummyExpertTwo(ExpertAgent):
    metadata = ExpertMetadata(
        expert_name="DummyExpertTwo",
        domain="dummy2",
        version="1.1.0",
        description="Second dummy expert agent",
        supported_claims=["claim2"],
        supported_evidence_types=["evidence2"],
        prompt_name="dummy_two",
        prompt_version="1.1.0",
        agent_version="1.1.0",
        enabled=True,
        tags=["dummy", "two"]
    )

    def get_domain_key(self) -> str:
        return "dummy2"

    def get_agent_version(self) -> str:
        return "1.1.0"

    def validate_inputs(self, profile: Any, claims: list, evidence: list, conflicts: list, metadata: dict) -> bool:
        return True


def test_registry_registration_and_get() -> None:
    registry = AgentRegistry()
    
    # Assert initial empty state
    assert not registry.exists("DummyExpertOne")
    assert "DummyExpertOne" not in registry.list()

    # Register successfully
    registry.register(DummyExpertOne)
    assert registry.exists("DummyExpertOne")
    assert registry.get("DummyExpertOne") is DummyExpertOne
    
    # Read snapshot is immutable copy
    snapshot = registry.list()
    assert snapshot["DummyExpertOne"] is DummyExpertOne
    snapshot["DummyExpertOne"] = None # modify copy
    assert registry.get("DummyExpertOne") is DummyExpertOne # check original unaffected

    # List enabled
    enabled = registry.list_enabled()
    assert DummyExpertOne in enabled


def test_registry_duplicate_rejection() -> None:
    registry = AgentRegistry()
    registry.register(DummyExpertOne)

    # Creating another class with same expert_name
    class DuplicateDummy(ExpertAgent):
        metadata = ExpertMetadata(
            expert_name="DummyExpertOne", # Duplicate name
            domain="duplicate",
            version="2.0.0",
            description="duplicate description",
            prompt_name="dup",
            prompt_version="1.0.0",
            agent_version="1.0.0"
        )
        def get_domain_key(self) -> str: return "dup"
        def get_agent_version(self) -> str: return "1.0.0"
        def validate_inputs(self, *args, **kwargs) -> bool: return True

    with pytest.raises(DuplicateRegistrationError, match="is already registered"):
        registry.register(DuplicateDummy)


def test_registry_unregister() -> None:
    registry = AgentRegistry()
    registry.register(DummyExpertOne)
    assert registry.exists("DummyExpertOne")

    registry.unregister("DummyExpertOne")
    assert not registry.exists("DummyExpertOne")

    # Unregistering non-existent expert should raise KeyError
    with pytest.raises(KeyError, match="not registered"):
        registry.unregister("DummyExpertOne")


def test_registry_metadata_validation() -> None:
    registry = AgentRegistry()

    # Class missing metadata attribute
    class NoMetadataAgent(ExpertAgent):
        def get_domain_key(self) -> str: return "dummy"
        def get_agent_version(self) -> str: return "1.0"
        def validate_inputs(self, *args, **kwargs) -> bool: return True

    with pytest.raises(InvalidMetadataError, match="does not define a 'metadata' attribute"):
        registry.register(NoMetadataAgent)

    # Class with metadata as invalid type
    class InvalidMetadataTypeAgent(ExpertAgent):
        metadata = "not-metadata-object"  # type: ignore
        def get_domain_key(self) -> str: return "dummy"
        def get_agent_version(self) -> str: return "1.0"
        def validate_inputs(self, *args, **kwargs) -> bool: return True

    with pytest.raises(InvalidMetadataError, match="must be an instance of ExpertMetadata or a dict"):
        registry.register(InvalidMetadataTypeAgent)

    # Class with empty required fields
    class EmptyNameAgent(ExpertAgent):
        metadata = ExpertMetadata(
            expert_name="", # empty
            domain="dummy",
            version="1.0.0",
            description="desc",
            prompt_name="dummy",
            prompt_version="1.0.0",
            agent_version="1.0.0"
        )
        def get_domain_key(self) -> str: return "dummy"
        def get_agent_version(self) -> str: return "1.0"
        def validate_inputs(self, *args, **kwargs) -> bool: return True

    with pytest.raises(InvalidMetadataError, match="expert_name"):
        registry.register(EmptyNameAgent)


def test_disabled_expert_behavior() -> None:
    registry = AgentRegistry()

    class DisabledAgent(ExpertAgent):
        metadata = ExpertMetadata(
            expert_name="DisabledAgent",
            domain="disabled",
            version="1.0.0",
            description="A disabled expert for testing",
            prompt_name="disabled",
            prompt_version="1.0.0",
            agent_version="1.0.0",
            enabled=False # Disabled
        )
        def get_domain_key(self) -> str: return "disabled"
        def get_agent_version(self) -> str: return "1.0.0"
        def validate_inputs(self, *args, **kwargs) -> bool: return True

    registry.register(DisabledAgent)
    
    assert registry.exists("DisabledAgent") is True
    assert "DisabledAgent" in registry.list()
    assert DisabledAgent not in registry.list_enabled()

    # Get should raise DisabledExpertError when requesting execution
    with pytest.raises(DisabledExpertError, match="is disabled"):
        registry.get("DisabledAgent")


def test_registry_thread_safety() -> None:
    registry = AgentRegistry()

    def register_worker(index: int) -> None:
        class ThreadedAgent(ExpertAgent):
            metadata = ExpertMetadata(
                expert_name=f"ThreadedAgent_{index}",
                domain=f"threaded_{index}",
                version="1.0.0",
                description="Threaded test agent",
                prompt_name="threaded",
                prompt_version="1.0.0",
                agent_version="1.0.0"
            )
            def get_domain_key(self) -> str: return "threaded"
            def get_agent_version(self) -> str: return "1.0.0"
            def validate_inputs(self, *args, **kwargs) -> bool: return True
        registry.register(ThreadedAgent)

    # Perform registrations in parallel
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = [executor.submit(register_worker, i) for i in range(100)]
        for fut in futures:
            fut.result()

    assert len(registry.list()) == 100
    for i in range(100):
        assert registry.exists(f"ThreadedAgent_{i}")
        assert registry.get(f"ThreadedAgent_{i}") is not None


def test_registry_event_publishing() -> None:
    registry = AgentRegistry()
    events_received = []

    def log_event(evt: Any) -> None:
        events_received.append(evt)

    dispatcher.register("ExpertRegistered", log_event)
    dispatcher.register("ExpertUnregistered", log_event)

    try:
        registry.register(DummyExpertOne)
        assert len(events_received) == 1
        assert events_received[0].event_name == "ExpertRegistered"
        assert events_received[0].payload["expert_name"] == "DummyExpertOne"
        assert events_received[0].payload["domain"] == "dummy1"

        registry.unregister("DummyExpertOne")
        assert len(events_received) == 2
        assert events_received[1].event_name == "ExpertUnregistered"
        assert events_received[1].payload["expert_name"] == "DummyExpertOne"

    finally:
        dispatcher.unregister("ExpertRegistered", log_event)
        dispatcher.unregister("ExpertUnregistered", log_event)


def test_dynamic_discovery_and_events() -> None:
    registry = AgentRegistry()
    events_received = []

    def log_event(evt: Any) -> None:
        events_received.append(evt)

    dispatcher.register("ExpertDiscoveryStarted", log_event)
    dispatcher.register("ExpertDiscoveryCompleted", log_event)
    dispatcher.register("ExpertDiscoveryFailed", log_event)

    try:
        count = discover_and_register_experts(registry)
        
        # Verify both FounderExpert and ProductExpert were discovered and registered
        assert count >= 2
        assert registry.exists("FounderExpert")
        assert registry.exists("ProductExpert")

        # Verify discovery events were dispatched correctly
        assert len(events_received) == 2
        assert events_received[0].event_name == "ExpertDiscoveryStarted"
        assert "package_path" in events_received[0].payload
        assert events_received[1].event_name == "ExpertDiscoveryCompleted"
        assert events_received[1].payload["discovered_count"] == count

    finally:
        dispatcher.unregister("ExpertDiscoveryStarted", log_event)
        dispatcher.unregister("ExpertDiscoveryCompleted", log_event)
        dispatcher.unregister("ExpertDiscoveryFailed", log_event)


def test_dynamic_discovery_failed_event() -> None:
    registry = AgentRegistry()
    events_received = []

    def log_event(evt: Any) -> None:
        events_received.append(evt)

    dispatcher.register("ExpertDiscoveryFailed", log_event)

    # We force a discovery failure by passing an invalid registry object (e.g. None)
    # which will cause an AttributeError inside discovery logic
    try:
        with pytest.raises(AttributeError):
            discover_and_register_experts(None)  # type: ignore

        assert len(events_received) == 1
        assert events_received[0].event_name == "ExpertDiscoveryFailed"
        assert "error" in events_received[0].payload
        assert "'NoneType' object" in events_received[0].payload["error"]

    finally:
        dispatcher.unregister("ExpertDiscoveryFailed", log_event)
