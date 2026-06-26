from app.modules.startup_profiles.agent import StartupProfileAgentService
from app.modules.startup_profiles.schemas import (
    StartupProfileAgentOutput,
    StartupEvaluationScore,
    StartupEvaluationOutput,
    StartupAssessmentResult,
)
from app.services.ai import MockAIGateway


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


def test_build_evaluation_prompt_contains_required_fields():
    service = StartupProfileAgentService(None)

    class Startup:
        startup_name = "AI Power Solutions"
        problem_statement = "Inefficient energy storage in grid systems."
        solution_summary = "AI-based software optimization for battery packs."
        target_market = "Green energy providers"
        stage = "MVP"
        business_model = "SaaS"
        traction_summary = "3 pilots active"
        funding_status = "Pre-seed"

    class Context:
        startup = Startup()

    prompt = service.build_evaluation_prompt(Context())

    assert isinstance(prompt, str)
    assert "AI Power Solutions" in prompt
    assert "Inefficient energy storage in grid systems." in prompt
    assert "AI-based software optimization for battery packs." in prompt
    assert "Green energy providers" in prompt
    assert "SaaS" in prompt
    assert "3 pilots active" in prompt
    assert "Pre-seed" in prompt


def test_build_evaluation_prompt_handles_missing_fields_gracefully():
    service = StartupProfileAgentService(None)

    class Startup:
        pass

    class Context:
        startup = Startup()

    prompt = service.build_evaluation_prompt(Context())
    assert isinstance(prompt, str)
    assert "Not specified" in prompt


def test_build_evaluation_prompt_rubric_and_contract():
    service = StartupProfileAgentService(None)

    class Startup:
        startup_name = "AI Power Solutions"
        problem_statement = "Inefficient energy storage in grid systems."
        solution_summary = "AI-based software optimization for battery packs."
        target_market = "Green energy providers"
        stage = "MVP"
        business_model = "SaaS"
        traction_summary = "3 pilots active"
        funding_status = "Pre-seed"

    class Context:
        startup = Startup()

    prompt = service.build_evaluation_prompt(Context())

    # 1. Prompt contains evaluator role
    assert "You are a startup evaluator for TIDES IIT Roorkee." in prompt

    # 2. Prompt contains scoring rubric
    assert "Innovation (0-10)" in prompt
    assert "Novelty" in prompt
    assert "Technical differentiation" in prompt
    assert "Defensibility" in prompt
    assert "Market Potential (0-10)" in prompt
    assert "Market size" in prompt
    assert "Customer clarity" in prompt
    assert "Scalability" in prompt
    assert "Execution Readiness (0-10)" in prompt
    assert "Business model maturity" in prompt
    assert "Traction" in prompt
    assert "Funding readiness" in prompt

    # 3. Prompt contains JSON contract
    assert "Output Contract JSON:" in prompt
    assert '"executive_summary":' in prompt
    assert '"innovation_score":' in prompt
    assert '"market_score":' in prompt
    assert '"execution_score":' in prompt
    assert '"overall_score":' in prompt
    assert '"strengths":' in prompt
    assert '"weaknesses":' in prompt
    assert '"recommendations":' in prompt


# ---------------------------------------------------------------------------
# evaluate_startup_with_ai tests
# ---------------------------------------------------------------------------

_FIXED_AI_RESPONSE = {
    "executive_summary": "A strong AI startup addressing grid storage.",
    "innovation_score": 8,
    "market_score": 7,
    "execution_score": 6,
    "overall_score": 21,
    "strengths": ["Clear solution", "Defined market"],
    "weaknesses": ["No traction data"],
    "recommendations": ["Run a pilot"],
}


class _FullStartup:
    startup_name = "GridAI"
    problem_statement = "Grid storage is expensive."
    solution_summary = "AI-driven battery analytics."
    target_market = "Industrial energy users"
    stage = "MVP"
    business_model = "SaaS"
    traction_summary = None
    funding_status = "Pre-seed"


class _FullContext:
    startup = _FullStartup()


def _make_service_with_mock(fixed_response=None):
    """Create a StartupProfileAgentService whose gateway is a MockAIGateway."""
    service = StartupProfileAgentService.__new__(StartupProfileAgentService)
    service.db = None
    service.gateway = MockAIGateway(
        fixed_response=fixed_response or _FIXED_AI_RESPONSE,
    )
    return service


def test_evaluate_startup_with_ai_returns_evaluation_output():
    service = _make_service_with_mock()

    result = service.evaluate_startup_with_ai(_FullContext())

    assert isinstance(result, StartupEvaluationOutput)
    assert result.innovation_score == 8
    assert result.market_score == 7
    assert result.execution_score == 6
    assert result.overall_score == 70
    assert result.executive_summary == "A strong AI startup addressing grid storage."
    assert "Clear solution" in result.strengths
    assert "No traction data" in result.weaknesses
    assert "Run a pilot" in result.recommendations


def test_evaluate_startup_with_ai_gateway_is_called():
    captured_requests = []

    def capturing_factory(req):
        captured_requests.append(req)
        return _FIXED_AI_RESPONSE

    service = StartupProfileAgentService.__new__(StartupProfileAgentService)
    service.db = None
    service.gateway = MockAIGateway(response_factory=capturing_factory)

    service.evaluate_startup_with_ai(_FullContext())

    assert len(captured_requests) == 1, "Gateway should have been called exactly once"


def test_evaluate_startup_with_ai_prompt_is_passed_correctly():
    captured_requests = []

    def capturing_factory(req):
        captured_requests.append(req)
        return _FIXED_AI_RESPONSE

    service = StartupProfileAgentService.__new__(StartupProfileAgentService)
    service.db = None
    service.gateway = MockAIGateway(response_factory=capturing_factory)

    service.evaluate_startup_with_ai(_FullContext())

    req = captured_requests[0]
    # system_prompt must carry the evaluator role
    assert "TIDES IIT Roorkee" in req.system_prompt
    # user_prompt must contain all key startup fields
    assert "GridAI" in req.user_prompt
    assert "Grid storage is expensive." in req.user_prompt
    assert "AI-driven battery analytics." in req.user_prompt
    assert "Industrial energy users" in req.user_prompt
    assert "Pre-seed" in req.user_prompt


# ---------------------------------------------------------------------------
# assess_startup tests
# ---------------------------------------------------------------------------


def test_assess_startup_returns_assessment_result():
    service = _make_service_with_mock()

    result = service.assess_startup(_FullContext())

    assert isinstance(result, StartupAssessmentResult)


def test_assess_startup_profile_field_is_populated():
    service = _make_service_with_mock()

    result = service.assess_startup(_FullContext())

    assert isinstance(result.profile, StartupProfileAgentOutput)
    # generate_profile embeds the startup name in the executive summary
    assert "GridAI" in result.profile.executive_summary


def test_assess_startup_rule_based_score_field_is_populated():
    service = _make_service_with_mock()

    result = service.assess_startup(_FullContext())

    assert isinstance(result.rule_based_score, StartupEvaluationScore)
    # _FullStartup has solution_summary → +3, target_market → +3,
    # business_model → +2, funding_status → +1; traction_summary is None
    assert result.rule_based_score.innovation_score == 3
    assert result.rule_based_score.market_score == 3
    assert result.rule_based_score.execution_score == 3   # business_model(2) + funding_status(1)
    assert result.rule_based_score.overall_score == 9


def test_assess_startup_ai_evaluation_field_is_populated():
    service = _make_service_with_mock()

    result = service.assess_startup(_FullContext())

    assert isinstance(result.ai_evaluation, StartupEvaluationOutput)
    # values come from _FIXED_AI_RESPONSE
    assert result.ai_evaluation.innovation_score == 8
    assert result.ai_evaluation.market_score == 7
    assert result.ai_evaluation.execution_score == 6
    assert result.ai_evaluation.overall_score == 70


def test_assess_startup_contains_all_three_components():
    service = _make_service_with_mock()

    result = service.assess_startup(_FullContext())

    # All three top-level components must be present
    assert result.profile is not None
    assert result.rule_based_score is not None
    assert result.ai_evaluation is not None


# ---------------------------------------------------------------------------
# Document-Aware Evaluation Prompt Tests
# ---------------------------------------------------------------------------


class _MockDoc:
    def __init__(self, doc_type, filename, text, status, file_path="some_path", stored_filename="stored_file", id="some_uuid"):
        self.document_type = doc_type
        self.original_filename = filename
        self.parsed_text = text
        self.processing_status = status
        self.file_path = file_path
        self.stored_filename = stored_filename
        self.id = id


def test_build_evaluation_prompt_parsed_documents_included():
    service = StartupProfileAgentService(None)

    class Startup:
        startup_name = "BatteryX"
        problem_statement = "expensive grid storage"
        solution_summary = "battery analytics"
        target_market = "industrial users"
        stage = "MVP"
        business_model = "SaaS"
        traction_summary = "2 pilots"
        funding_status = "Pre-seed"

    doc = _MockDoc("pitch_deck", "deck.pdf", "Detailed pitch deck content.", "parsed")

    class Context:
        startup = Startup()
        documents = [doc]

    prompt = service.build_evaluation_prompt(Context())

    # Check that parsed documents are included correctly
    assert "Supporting Documents" in prompt
    assert "Document Type: pitch_deck" in prompt
    assert "Original Filename: deck.pdf" in prompt
    assert "Parsed Text: Detailed pitch deck content." in prompt

    # Verify we do NOT leak internal IDs, paths or stored filenames
    assert "some_path" not in prompt
    assert "stored_file" not in prompt
    assert "some_uuid" not in prompt


def test_build_evaluation_prompt_non_parsed_documents_excluded():
    service = StartupProfileAgentService(None)

    class Startup:
        startup_name = "BatteryX"

    doc1 = _MockDoc("pitch_deck", "deck.pdf", "Pitch deck text.", "uploaded")
    doc2 = _MockDoc("founder_resume", "resume.pdf", "Resume text.", "failed")
    doc3 = _MockDoc("company_document", "doc.pdf", "Company doc text.", "parsed")

    class Context:
        startup = Startup()
        documents = [doc1, doc2, doc3]

    prompt = service.build_evaluation_prompt(Context())

    # Check that parsed document is included
    assert "Document Type: company_document" in prompt
    assert "Parsed Text: Company doc text." in prompt

    # Check that non-parsed documents are excluded
    assert "pitch_deck" not in prompt
    assert "founder_resume" not in prompt
    assert "Pitch deck text" not in prompt
    assert "Resume text" not in prompt


def test_build_evaluation_prompt_truncation_behavior():
    service = StartupProfileAgentService(None)

    class Startup:
        startup_name = "BatteryX"

    # Per-document limit is 3,000 characters. Let's make text 3,500 characters.
    long_text = "A" * 3500
    doc = _MockDoc("pitch_deck", "deck.pdf", long_text, "parsed")

    class Context:
        startup = Startup()
        documents = [doc]

    prompt = service.build_evaluation_prompt(Context())

    # Per-document limit check
    expected_truncated_text = "A" * 3000 + "... [TRUNCATED]"
    assert expected_truncated_text in prompt
    assert "A" * 3001 not in prompt

    # Total context limit is 10,000 characters.
    doc1 = _MockDoc("pitch_deck", "deck1.pdf", "B" * 3000, "parsed")
    doc2 = _MockDoc("pitch_deck", "deck2.pdf", "C" * 3000, "parsed")
    doc3 = _MockDoc("pitch_deck", "deck3.pdf", "D" * 3000, "parsed")
    doc4 = _MockDoc("pitch_deck", "deck4.pdf", "E" * 3000, "parsed")

    class TotalContext:
        startup = Startup()
        documents = [doc1, doc2, doc3, doc4]

    prompt2 = service.build_evaluation_prompt(TotalContext())

    # Check that total context size control limits the documents section
    idx = prompt2.find("Supporting Documents:")
    docs_part = prompt2[idx:]
    assert "Document Type: pitch_deck" in docs_part
    assert "E" * 3000 not in docs_part


def test_build_evaluation_prompt_multiple_documents_included():
    service = StartupProfileAgentService(None)

    class Startup:
        startup_name = "BatteryX"

    doc1 = _MockDoc("pitch_deck", "deck.pdf", "Pitch deck content.", "parsed")
    doc2 = _MockDoc("business_plan", "plan.pdf", "Business plan content.", "parsed")

    class Context:
        startup = Startup()
        documents = [doc1, doc2]

    prompt = service.build_evaluation_prompt(Context())

    assert "Document Type: pitch_deck" in prompt
    assert "Original Filename: deck.pdf" in prompt
    assert "Parsed Text: Pitch deck content." in prompt
    assert "Document Type: business_plan" in prompt
    assert "Original Filename: plan.pdf" in prompt
    assert "Parsed Text: Business plan content." in prompt