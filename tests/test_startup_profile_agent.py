from app.modules.startup_profiles.agent import StartupProfileAgentService


def test_agent_service_can_be_created():
    service = StartupProfileAgentService(None)

    assert service is not None