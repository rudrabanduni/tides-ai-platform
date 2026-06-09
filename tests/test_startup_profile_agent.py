from app.modules.startup_profiles.agent import StartupProfileAgentService


def test_agent_service_can_be_created():
    service = StartupProfileAgentService(None)

    assert service is not None

from app.modules.startup_profiles.schemas import StartupProfileAgentOutput


def test_generate_profile_returns_output():
    service = StartupProfileAgentService(None)

    result = service.generate_profile(None)

    assert isinstance(result, StartupProfileAgentOutput)