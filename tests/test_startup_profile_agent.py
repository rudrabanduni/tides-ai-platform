from app.modules.startup_profiles.agent import StartupProfileAgentService
from app.modules.startup_profiles.schemas import StartupProfileAgentOutput, StartupEvaluationScore


def test_agent_service_can_be_created():
    service = StartupProfileAgentService(None)

    assert service is not None


def test_generate_profile_returns_output():
    service = StartupProfileAgentService(None)

    class Startup:
        startup_name = "Demo Startup"
        stage = "Idea"
        problem_statement = "Food waste"
        solution_summary = "AI food redistribution"
        target_market = "Restaurants"
        business_model = "Subscription"
        traction_summary = None
        funding_status = None

    class Context:
        startup = Startup()

    result = service.generate_profile(Context())

    assert isinstance(result, StartupProfileAgentOutput)


def test_generate_profile_contains_startup_name():
    service = StartupProfileAgentService(None)

    class Startup:
        startup_name = "TIDES AI"
        stage = "Idea"
        problem_statement = "Startup evaluation inefficiency"
        solution_summary = "AI-powered startup evaluation"
        target_market = "Incubators"
        business_model = "SaaS"
        traction_summary = None
        funding_status = None

    class Context:
        startup = Startup()

    result = service.generate_profile(Context())

    assert "TIDES AI" in result.executive_summary


def test_evaluate_startup_successful_scoring():
    service = StartupProfileAgentService(None)

    class Startup:
        solution_summary = "AI-powered food redistribution"
        target_market = "Restaurants and groceries"
        business_model = "SaaS subscription"
        traction_summary = "10 active pilots"
        funding_status = "Pre-seed"

    class Context:
        startup = Startup()

    result = service.evaluate_startup(Context())

    assert isinstance(result, StartupEvaluationScore)
    assert result.innovation_score == 3
    assert result.market_score == 3
    assert result.execution_score == 5
    assert result.overall_score == 11
    assert "Has solution summary (+3 innovation)" in result.rationale
    assert "Has target market (+3 market)" in result.rationale
    assert "Has business model (+2 execution)" in result.rationale
    assert "Has traction summary (+2 execution)" in result.rationale
    assert "Has funding status (+1 execution)" in result.rationale


def test_evaluate_startup_missing_data_reduces_scores():
    service = StartupProfileAgentService(None)

    class Startup:
        solution_summary = None
        target_market = None
        business_model = None
        traction_summary = None
        funding_status = None

    class Context:
        startup = Startup()

    result = service.evaluate_startup(Context())

    assert isinstance(result, StartupEvaluationScore)
    assert result.innovation_score == 0
    assert result.market_score == 0
    assert result.execution_score == 0
    assert result.overall_score == 0
    assert "Missing solution summary (0 innovation)" in result.rationale
    assert "Missing target market (0 market)" in result.rationale
    assert "Missing business model (0 execution)" in result.rationale
    assert "Missing traction summary (0 execution)" in result.rationale
    assert "Missing funding status (0 execution)" in result.rationale


def test_evaluate_startup_overall_score_calculation():
    service = StartupProfileAgentService(None)

    class Startup:
        solution_summary = "Innovative batteries"
        target_market = None
        business_model = "B2B licensing"
        traction_summary = None
        funding_status = "Self-funded"

    class Context:
        startup = Startup()

    result = service.evaluate_startup(Context())

    assert isinstance(result, StartupEvaluationScore)
    assert result.innovation_score == 3
    assert result.market_score == 0
    assert result.execution_score == 2 + 1
    assert result.overall_score == result.innovation_score + result.market_score + result.execution_score
    assert result.overall_score == 6
    assert "Has solution summary (+3 innovation)" in result.rationale
    assert "Missing target market (0 market)" in result.rationale
    assert "Has business model (+2 execution)" in result.rationale
    assert "Missing traction summary (0 execution)" in result.rationale
    assert "Has funding status (+1 execution)" in result.rationale