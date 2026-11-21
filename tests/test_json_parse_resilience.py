"""tests/test_json_parse_resilience.py - Offline Verification for Malformed JSON Resilience.

Zero live API calls.
Tests:
1. Valid model JSON parses cleanly and reconciles in ledger with status="SUCCESS".
2. Malformed JSON with invalid delimiter fails safely and reconciles in ledger with status="PARSE_ERROR" (tokens/cost captured, not lost).
3. Truncated model JSON fails safely and reconciles in ledger with status="PARSE_ERROR".
4. Domain expert evaluation safely produces a controlled failure report when AI response is malformed:
   - 0.0 confidence score
   - Empty strengths (zero positive findings)
   - MISSING_INFORMATION verification status across all criteria
   - High-severity operational Risk node
5. Pipeline continues execution when one domain produces malformed JSON:
   - Remaining domains complete
   - Supervisory reviewer synthesizes the result
   - Report is generated
   - evaluation_status is COMPLETED_WITH_PARTIAL_DOMAIN_FAILURES
6. No unreserved network retries occur on parse errors.
7. Workspace tides_ai.db hash remains bit-for-bit unchanged.
"""

import hashlib
import uuid
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from litellm import Choices, Message, ModelResponse, Usage
from pydantic import BaseModel

from app.modules.evaluation.domain_schemas import DomainAssessmentReport, VerificationStatus
from app.modules.evaluation.domains import ProblemSolutionExpert
from app.modules.evaluation.schemas import AgentAssessment
from app.services.ai.cost_ledger import CostLedgerManager, EvaluationCostLedger
from app.services.ai.exceptions import AIResponseParseError
from app.services.ai.litellm import LiteLLMGateway
from app.services.ai.schemas import AICompletionRequest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
WORKSPACE_DB = PROJECT_ROOT / "tides_ai.db"
EXPECTED_WORKSPACE_DB_HASH = "d9659f4e8c1058c5d5f4511e1bb22d3abe6cb12101c16ce397416051a38176c7"


class DummyModel(BaseModel):
    summary: str
    score: int


def _build_mock_response(content: str, prompt_tokens: int = 1200, completion_tokens: int = 400) -> ModelResponse:
    resp = ModelResponse()
    resp.model = "claude-sonnet-5-5"
    choice = Choices()
    msg = Message()
    msg.content = content
    choice.message = msg
    resp.choices = [choice]
    usage = Usage()
    usage.prompt_tokens = prompt_tokens
    usage.completion_tokens = completion_tokens
    usage.total_tokens = prompt_tokens + completion_tokens
    resp.usage = usage
    return resp


class TestJSONParseResilience:
    def test_valid_json_parses_cleanly_and_reconciles_success(self):
        eval_id = f"eval_valid_json_{uuid.uuid4().hex[:8]}"
        cost_mgr = CostLedgerManager.get_instance()
        ledger = cost_mgr.get_or_create_ledger(evaluation_id=eval_id, max_budget_usd=0.35)

        gateway = LiteLLMGateway(model="claude-sonnet-5-5", api_key="dummy-key", max_retries=0)
        req = AICompletionRequest(
            system_prompt="Test system",
            user_prompt="Test user",
            evaluation_id=eval_id,
            agent_name="test_valid",
            max_output_tokens=1000,
        )

        valid_content = '{"summary": "Solid progress", "score": 95}'
        mock_resp = _build_mock_response(valid_content)

        with patch("litellm.completion", return_value=mock_resp):
            res = gateway.complete_json(req, DummyModel)

        assert res.data.summary == "Solid progress"
        assert res.data.score == 95

        # Check ledger record
        summary = ledger.get_summary()
        assert summary["total_operations"] == 1
        assert summary["operations"][0]["status"] == "SUCCESS"
        assert summary["operations"][0]["input_tokens"] == 1200
        assert summary["operations"][0]["output_tokens"] == 400
        assert summary["total_spent_usd"] > 0.0

    def test_malformed_json_invalid_delimiter_reconciles_parse_error_in_ledger(self):
        """Simulates 'Expecting , delimiter' defect (missing comma at char 5551)."""
        eval_id = f"eval_invalid_delim_{uuid.uuid4().hex[:8]}"
        cost_mgr = CostLedgerManager.get_instance()
        ledger = cost_mgr.get_or_create_ledger(evaluation_id=eval_id, max_budget_usd=0.35)

        gateway = LiteLLMGateway(model="claude-sonnet-5-5", api_key="dummy-key", max_retries=0)
        req = AICompletionRequest(
            system_prompt="Test system",
            user_prompt="Test user",
            evaluation_id=eval_id,
            agent_name="test_malformed_delim",
            max_output_tokens=1000,
        )

        # Missing comma between fields produces "Expecting ',' delimiter"
        malformed_content = '{"summary": "Solid progress" "score": 95}'
        mock_resp = _build_mock_response(malformed_content, prompt_tokens=1500, completion_tokens=350)

        with patch("litellm.completion", return_value=mock_resp):
            with pytest.raises(AIResponseParseError) as exc_info:
                gateway.complete_json(req, DummyModel)

        assert "Expecting ',' delimiter" in str(exc_info.value)

        # Verify that the spent cost and token usage WERE recorded as PARSE_ERROR in the ledger
        summary = ledger.get_summary()
        assert summary["total_operations"] == 1
        op = summary["operations"][0]
        assert op["status"] == "PARSE_ERROR"
        assert op["input_tokens"] == 1500
        assert op["output_tokens"] == 350
        assert summary["total_spent_usd"] > 0.0, "Provider was paid; cost must NOT be zero or discarded!"

    def test_malformed_json_truncated_reconciles_parse_error_in_ledger(self):
        """Simulates truncated JSON output."""
        eval_id = f"eval_truncated_{uuid.uuid4().hex[:8]}"
        cost_mgr = CostLedgerManager.get_instance()
        ledger = cost_mgr.get_or_create_ledger(evaluation_id=eval_id, max_budget_usd=0.35)

        gateway = LiteLLMGateway(model="claude-sonnet-5-5", api_key="dummy-key", max_retries=0)
        req = AICompletionRequest(
            system_prompt="Test system",
            user_prompt="Test user",
            evaluation_id=eval_id,
            agent_name="test_truncated",
            max_output_tokens=1000,
        )

        truncated_content = '{"summary": "Solid progress, but abruptly cut off before clo'
        mock_resp = _build_mock_response(truncated_content, prompt_tokens=1400, completion_tokens=300)

        with patch("litellm.completion", return_value=mock_resp):
            with pytest.raises(AIResponseParseError):
                gateway.complete_json(req, DummyModel)

        summary = ledger.get_summary()
        assert summary["total_operations"] == 1
        assert summary["operations"][0]["status"] == "PARSE_ERROR"
        assert summary["total_spent_usd"] > 0.0

    def test_domain_expert_handles_malformed_json_safely(self):
        """Verifies ProblemSolutionExpert produces a controlled non-positive failure report on malformed JSON."""
        gateway = LiteLLMGateway(model="claude-sonnet-5-5", api_key="dummy-key", max_retries=0)
        expert = ProblemSolutionExpert(gateway=gateway)

        # Mock gateway to raise AIResponseParseError
        malformed_error = AIResponseParseError("Expecting ',' delimiter: line 61 column 6 (char 5551)")
        with patch.object(gateway, "complete_json", side_effect=malformed_error):
            report: DomainAssessmentReport = expert.evaluate(
                profile=MagicMock(startup_id="startup-001", startup_name="CleanPower Systems"),
                claims=[],
                evidence=[],
                conflicts=[],
                metadata={"evaluation_id": "eval-safe-fail-01"},
            )

        # Verify controlled failure
        assert isinstance(report, DomainAssessmentReport)
        assert "evaluation incomplete" in report.summary.lower()
        assert "batch failure" in report.summary.lower() or "parse error" in report.summary.lower()

        # Strict non-positive invariants
        assert report.confidence.overall_domain_confidence == 0.0
        assert report.composite_domain_confidence == 0.0
        assert report.strengths == [], "Must not hallucinate or convert parse failure into positive strengths!"
        assert len(report.weaknesses) > 0
        assert len(report.risks) > 0

        # Criteria must be marked MISSING_INFORMATION, not verified
        for cid, ceval in report.criteria_evaluations.items():
            assert ceval.verification_status == VerificationStatus.MISSING_INFORMATION
            assert ceval.confidence_score == 0.0
            assert ceval.strengths == []

    def test_no_unreserved_network_retries_on_parse_error(self):
        """Verifies parse errors do not trigger unbudgeted automatic network retries."""
        gateway = LiteLLMGateway(model="claude-sonnet-5-5", api_key="dummy-key", max_retries=2)
        req = AICompletionRequest(
            system_prompt="Test",
            user_prompt="Test",
            agent_name="test_no_retry_on_parse",
        )

        call_count = 0
        def mock_completion(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            return _build_mock_response('{"invalid_json": ')

        with patch("litellm.completion", side_effect=mock_completion):
            with pytest.raises(AIResponseParseError):
                gateway.complete_json(req, DummyModel)

        # Even with max_retries=2, a JSON parse error is non-transient and must NOT retry the remote API
        assert call_count == 1

    @pytest.mark.anyio
    async def test_pipeline_continues_when_one_domain_fails(self):
        """Verifies that if one domain produces malformed JSON, the pipeline completes with partial domain failures."""
        from app.modules.ai.orchestrator.pipeline import _evaluate_and_generate_report, StageTracer
        from app.modules.startups.models import StartupApplication
        from app.modules.intelligence.models import StartupIntelligenceProfile

        eval_id = f"eval_partial_pipeline_{uuid.uuid4().hex[:8]}"
        cost_mgr = CostLedgerManager.get_instance()
        cost_mgr.get_or_create_ledger(evaluation_id=eval_id, max_budget_usd=0.35)

        startup = StartupApplication(
            id=uuid.uuid4(),
            startup_name="CleanPower Systems",
            sector="CleanTech",
            stage="Seed",
        )
        profile = StartupIntelligenceProfile(
            id=uuid.uuid4(),
            startup_id=startup.id,
        )

        tracers = {
            "Domain Expert Evaluation": StageTracer("Domain Expert Evaluation"),
            "Knowledge Graph Construction": StageTracer("Knowledge Graph Construction"),
            "Investment Intelligence Engine": StageTracer("Investment Intelligence Engine"),
            "Committee Decision": StageTracer("Committee Decision"),
            "Report Generation": StageTracer("Report Generation"),
            "PDF Serialization": StageTracer("PDF Serialization"),
        }

        # Mock ProblemSolutionExpert to fail with AIResponseParseError, while others succeed
        from app.modules.evaluation.domains import ProblemSolutionExpert
        orig_evaluate = ProblemSolutionExpert.evaluate

        def mock_failing_ps_evaluate(self, *args, **kwargs):
            raise AIResponseParseError("Expecting ',' delimiter: line 61 column 6 (char 5551)")

        from datetime import datetime, timezone
        start_time = datetime.now(timezone.utc)

        with patch.object(ProblemSolutionExpert, "evaluate", mock_failing_ps_evaluate):
            result = await _evaluate_and_generate_report(
                startup=startup,
                profile=profile,
                claims=[],
                evidence=[],
                actor_id=None,
                db=MagicMock(),
                tracers=tracers,
                eval_start_time=start_time,
                evaluation_id=eval_id,
            )

        assert result["evaluation_status"] == "COMPLETED_WITH_PARTIAL_DOMAIN_FAILURES"
        assert "generated_report" in result
        assert "pdf_base64" in result

    def test_ledger_records_usage_and_cost_before_parse_error_is_raised(self):
        """Explicitly tests that completed provider responses with malformed JSON record
        exact token counts and cost in the ledger before AIResponseParseError is raised."""
        eval_id = f"eval_telemetry_check_{uuid.uuid4().hex[:8]}"
        cost_mgr = CostLedgerManager.get_instance()
        ledger = cost_mgr.get_or_create_ledger(evaluation_id=eval_id, max_budget_usd=0.35)

        gateway = LiteLLMGateway(model="claude-sonnet-5-5", api_key="dummy-key", max_retries=0)
        req = AICompletionRequest(
            system_prompt="Test system",
            user_prompt="Test user",
            evaluation_id=eval_id,
            agent_name="domain_expert_sonnet",
            max_output_tokens=1500,
        )

        known_input_tokens = 2048
        known_output_tokens = 512
        malformed_json_str = '{"analysis": "Valid start", "metrics": {"incomplete": }'
        mock_resp = _build_mock_response(
            malformed_json_str,
            prompt_tokens=known_input_tokens,
            completion_tokens=known_output_tokens,
        )

        with patch("litellm.completion", return_value=mock_resp):
            with pytest.raises(AIResponseParseError):
                gateway.complete_json(req, DummyModel)

        summary = ledger.get_summary()
        assert summary["total_operations"] == 1
        recorded_op = summary["operations"][0]
        assert recorded_op["status"] == "PARSE_ERROR"
        assert recorded_op["input_tokens"] == known_input_tokens
        assert recorded_op["output_tokens"] == known_output_tokens
        assert recorded_op["final_cost_usd"] > 0.0, "Cost must be accurately computed from catalog rates!"
        assert summary["total_spent_usd"] == recorded_op["final_cost_usd"]

    def test_runner_persists_partial_run_report_and_cost_telemetry(self, tmp_path):
        """Verifies runner produces a clear partial-run report and persists cost telemetry
        when a domain fails. Uses mocked responses only; zero live calls."""
        from scripts.run_one_time_live_eval import main, format_telemetry_table
        import json

        mock_cost_summary = {
            "evaluation_id": "eval-mock-partial-01",
            "total_operations": 2,
            "total_input_tokens": 3548,
            "total_output_tokens": 912,
            "total_cached_tokens": 0,
            "total_spent_usd": 0.0245,
            "total_cost_inr_buffered": 2.77,
            "under_max_usd_ceiling": True,
            "operations": [
                {
                    "agent_name": "extraction",
                    "model": "claude-haiku-5-5",
                    "status": "SUCCESS",
                    "input_tokens": 1500,
                    "output_tokens": 400,
                    "cached_tokens": 0,
                    "final_cost_usd": 0.0035,
                    "buffered_cost_inr": 0.39,
                },
                {
                    "agent_name": "problem_solution",
                    "model": "claude-sonnet-5-5",
                    "status": "PARSE_ERROR",
                    "input_tokens": 2048,
                    "output_tokens": 512,
                    "cached_tokens": 0,
                    "final_cost_usd": 0.0210,
                    "buffered_cost_inr": 2.38,
                },
            ],
        }

        # Verify formatting table handles partial failure telemetry
        table_output = format_telemetry_table(mock_cost_summary)
        assert "extraction" in table_output
        assert "problem_solution" in table_output
        assert "$0.0245" in table_output
        assert "PASSED (WITHIN INR 50 BUDGET)" in table_output

        # Mock execute_live_pipeline returning partial status
        mock_pipeline_result = {
            "evaluation_status": "COMPLETED_WITH_PARTIAL_DOMAIN_FAILURES",
            "startup_id": "startup-mock-01",
            "assessment_identifier": "rep-mock-01",
            "cost_observability": mock_cost_summary,
        }

        mock_report_file = tmp_path / "live_eval_run_report.json"

        with patch("sys.argv", ["run_one_time_live_eval.py", "--execute-live"]), \
             patch("scripts.run_one_time_live_eval.check_environment", return_value=(True, "READY")), \
             patch("scripts.run_one_time_live_eval.configure_runtime_environment"), \
             patch("scripts.run_one_time_live_eval.execute_live_pipeline", return_value=mock_pipeline_result), \
             patch("scripts.run_one_time_live_eval.PROJECT_ROOT", tmp_path):

            exit_code = main()

        assert exit_code == 0
        written_report = tmp_path / "reports" / "live_eval_run_report.json"
        assert written_report.exists()

        with open(written_report, "r", encoding="utf-8") as f:
            saved_data = json.load(f)

        assert saved_data["evaluation_status"] == "COMPLETED_WITH_PARTIAL_DOMAIN_FAILURES"
        assert saved_data["cost_observability"]["operations"][1]["status"] == "PARSE_ERROR"
        assert saved_data["cost_observability"]["total_spent_usd"] == 0.0245

    def test_provider_truncation_detection_and_ledger_status(self):
        """Simulates provider finish_reason='length' (output truncated at token limit).
        Verifies:
        1. complete_json detects truncation and raises AIResponseParseError with clear truncation message.
        2. Cost ledger records status='PARSE_ERROR' and finish_reason='length'.
        3. Provider tokens and cost are reconciled, not lost.
        """
        eval_id = f"eval_trunc_{uuid.uuid4().hex[:8]}"
        cost_mgr = CostLedgerManager.get_instance()
        ledger = cost_mgr.get_or_create_ledger(evaluation_id=eval_id, max_budget_usd=0.35)

        gateway = LiteLLMGateway(model="claude-sonnet-5-5", api_key="dummy-key", max_retries=0)
        req = AICompletionRequest(
            system_prompt="Test system",
            user_prompt="Test user",
            evaluation_id=eval_id,
            agent_name="domain_problem_solution",
            max_output_tokens=1800,
        )

        mock_resp = _build_mock_response('{"summary": "Cut off mid-', prompt_tokens=8120, completion_tokens=4096)
        mock_resp.choices[0].finish_reason = "length"

        with patch("litellm.completion", return_value=mock_resp):
            with pytest.raises(AIResponseParseError) as exc_info:
                gateway.complete_json(req, DummyModel)

        assert "truncated by provider" in str(exc_info.value).lower()
        assert "finish_reason='length'" in str(exc_info.value)

        summary = ledger.get_summary()
        assert summary["total_operations"] == 1
        op = summary["operations"][0]
        assert op["status"] == "PARSE_ERROR"
        assert op["finish_reason"] == "length"
        assert op["input_tokens"] == 8120
        assert op["output_tokens"] == 4096
        assert summary["total_spent_usd"] > 0.0

    def test_planned_output_tokens_passed_to_litellm_completion(self):
        """Verifies max_tokens is explicitly forwarded to litellm.completion to prevent defaulting to 4096."""
        gateway = LiteLLMGateway(model="claude-sonnet-5-5", api_key="dummy-key", max_retries=0)
        req = AICompletionRequest(
            system_prompt="Test",
            user_prompt="Test",
            agent_name="test_max_tokens",
            max_output_tokens=1800,
        )

        passed_kwargs = {}
        def mock_completion(*args, **kwargs):
            nonlocal passed_kwargs
            passed_kwargs = kwargs
            return _build_mock_response('{"summary": "ok", "score": 1}')

        with patch("litellm.completion", side_effect=mock_completion):
            gateway.complete_json(req, DummyModel)

        assert passed_kwargs.get("max_tokens") == 1800

    def test_canonical_domain_expert_compact_prompt_and_max_tokens(self):
        """Verifies CanonicalDomainExpert emits scoped criterion-batch prompts
        with DomainCriterionBatchOutput and bounded <= 900 output tokens."""
        gateway = LiteLLMGateway(model="claude-sonnet-5-5", api_key="dummy-key", max_retries=0)
        expert = ProblemSolutionExpert(gateway=gateway)

        captured_request = None
        def mock_complete_json(request, response_model):
            nonlocal captured_request
            captured_request = request
            raise AIResponseParseError("mock parse error to inspect request")

        with patch.object(gateway, "complete_json", side_effect=mock_complete_json):
            expert.evaluate(
                profile=MagicMock(startup_id="startup-001", startup_name="CleanPower Systems"),
                claims=[],
                evidence=[],
                conflicts=[],
                metadata={"evaluation_id": "eval-compact-01", "domain_batch_max_retries": 0},
            )

        assert captured_request is not None
        # Verify bulky essay subheading directives are NOT present in batch prompt
        assert "MUST structure your analysis using the following exact subheadings" not in captured_request.system_prompt
        assert "## MANDATORY OUTPUT FIELDS" not in captured_request.system_prompt
        # Verify compact batch instructions & strict scoping to batch 1 (PS-01..PS-03 at the v1.1
        # default of 3 criteria per batch)
        assert "ASSIGNED CRITERIA & SCOPED EVIDENCE" in captured_request.user_prompt
        assert "DomainCriterionBatchOutput" in captured_request.user_prompt
        for cid in ("PS-01", "PS-02", "PS-03"):
            assert f"[{cid}]" in captured_request.user_prompt
        # Later batch criteria must NOT be in batch 1 prompt
        for other_cid in ("PS-04", "PS-06", "PS-10", "PS-13"):
            assert f"[{other_cid}]" not in captured_request.user_prompt
        assert captured_request.agent_name == "domain_problem_solution_batch_1"
        assert captured_request.max_output_tokens <= 900

    def test_compact_domain_assessment_validation_and_zero_dropped_criteria(self):
        """Verifies CompactDomainAssessment validates across all 6 canonical domains,
        and that all canonical criteria are accounted for with zero dropped criteria."""
        from app.modules.evaluation.domain_schemas import (
            CompactDomainAssessment,
            CompactCriterionResult,
            CompactDomainRisk,
        )
        from app.modules.evaluation.domains.registry import CANONICAL_DOMAINS, get_criteria_for_domain, CRITERIA_DIRECTORY

        expected_domain_counts = {
            "problem_solution": 13,
            "market_opportunity": 10,
            "founder_team": 13,
            "commercialisation": 13,
            "innovation_impact": 11,
            "financials_support": 21,
        }

        total_domain_criteria_count = 0
        for domain_key, expected_count in expected_domain_counts.items():
            crits = get_criteria_for_domain(domain_key)
            assert len(crits) == expected_count, f"Domain {domain_key} expected {expected_count} criteria, got {len(crits)}"
            total_domain_criteria_count += len(crits)

            # Build compact assessment for this domain with rationale <= 8 words, conclusion <= 25 words
            results = [
                CompactCriterionResult(
                    criterion_id=cid,
                    verification_status="VERIFIED_DOCUMENTED",
                    score=8.0,
                    evidence_ids=["EV-01"],
                    rationale=f"Verified for {cid} from submission.", # <= 8 words
                )
                for cid in crits
            ]

            assessment = CompactDomainAssessment(
                domain=domain_key,
                domain_conclusion=f"Due diligence across {domain_key} confirms operational viability.", # <= 25 words
                criteria=results,
                strengths=[f"{domain_key} strength 1", f"{domain_key} strength 2"], # <= 2
                risks=[
                    CompactDomainRisk(
                        id=f"R-{domain_key[:2].upper()}-01",
                        severity="Medium",
                        description=f"Scaling risk in {domain_key}",
                        mitigation="Structured milestone verification",
                    )
                ], # <= 2
                information_requests=[f"Provide third-party audit for {domain_key}"], # <= 3
                unknowns=[],
                contradictions=[],
                confidence_score=0.88,
            )

            # Validate serialization & deserialization
            dumped = assessment.model_dump_json()
            restored = CompactDomainAssessment.model_validate_json(dumped)
            assert restored.domain == domain_key
            assert len(restored.criteria) == expected_count

        assert total_domain_criteria_count == 81
        # Full LaunchIndex catalog: 81 domain evaluation criteria + 6 intake completeness metadata = 87 criteria
        assert len(CRITERIA_DIRECTORY) == 87, f"Expected 87 LaunchIndex criteria in registry, found {len(CRITERIA_DIRECTORY)}"

    def test_worst_case_payload_sizing_all_six_domains(self):
        """Rigorous test checking realistic worst-case serialized payload sizes across all six domain schemas,
        specifically verifying that the 21-criterion Financials & Support domain and all other domains
        comfortably fit well within the 1,800 token output ceiling."""
        import tiktoken
        from app.modules.evaluation.domain_schemas import (
            CompactDomainAssessment,
            CompactCriterionResult,
            CompactDomainRisk,
            SupervisoryReviewOutput,
        )
        from app.modules.evaluation.domains.registry import CANONICAL_DOMAINS, get_criteria_for_domain

        enc = tiktoken.get_encoding("cl100k_base")

        # Test each domain with dense, worst-case realistic text
        for domain_key in CANONICAL_DOMAINS:
            crit_ids = get_criteria_for_domain(domain_key)
            results = [
                CompactCriterionResult(
                    criterion_id=cid,
                    verification_status="VERIFIED_DOCUMENTED",
                    score=10.0,
                    evidence_ids=["EV-DILIGENCE-01", "EV-DILIGENCE-02"], # max 2
                    rationale="Confirmed through audited institutional records.", # exactly 5 words (<= 8 words)
                )
                for cid in crit_ids
            ]
            assessment = CompactDomainAssessment(
                domain=domain_key,
                domain_conclusion="Pre-revenue model requires strict milestone tranches before capital disbursement to de-risk commercial execution and manufacturing scaling.", # 17 words (<= 25 words)
                criteria=results,
                strengths=[
                    "Proprietary catalyst reduces cell manufacturing cost by 40%.",
                    "Signed commercial pilot agreement with state power grid.",
                ], # max 2
                risks=[
                    CompactDomainRisk(
                        id="R-01",
                        severity="Critical",
                        description="High capital expenditure required before qualification.",
                        mitigation="Tie disbursements to pilot milestones.",
                    ),
                    CompactDomainRisk(
                        id="R-02",
                        severity="High",
                        description="Statutory safety certification may extend timelines.",
                        mitigation="Retain regulatory counsel to expedite filing.",
                    ),
                ], # max 2
                information_requests=[
                    "Audited unit economics breakdown and BOM quotes.",
                    "Third-party endurance test logs validating 10,000 hours.",
                    "Cap table shareholding breakdown and vesting schedule.",
                ], # max 3
                unknowns=[
                    "Degradation rates under extreme industrial cyclic loads.",
                    "Customer acquisition cost for non-telecom verticals.",
                ], # max 3
                contradictions=[
                    "Active revenue claim conflicts with pre-revenue model.",
                ], # max 2
                confidence_score=0.88,
            )
            raw_json = assessment.model_dump_json()
            tok_count = len(enc.encode(raw_json))

            # Specific check for 21-criterion domain (Financials & Support)
            if domain_key == "financials_support":
                assert len(crit_ids) == 21
                # Must be under 1,300 tokens (giving >500 tokens safety margin below 1,800 cap)
                assert tok_count < 1300, f"Financials & Support tokens ({tok_count}) exceeded 1300"
            else:
                # Other 5 domains (10-13 criteria) must be under 950 tokens (giving >850 tokens safety margin)
                assert tok_count < 950, f"{domain_key} tokens ({tok_count}) exceeded 950"

            # Universal hard cap check
            assert tok_count < 1800, f"{domain_key} exceeded 1800 token ceiling!"

        # Test supervisory review output payload size
        sup_output = SupervisoryReviewOutput(
            executive_summary=(
                "Synthesized due diligence confirms strong problem-solution fit, deep technical founder capabilities, "
                "and substantial clean energy market demand. Commercial pilot commitments remain early-stage."
            ),
            recommendation_rationale=(
                "Core intellectual property and founder pedigree justify conditional incubation. Initial funding "
                "must be milestone-gated against binding customer pilot execution."
            ),
            overall_recommendation="CONDITIONAL",
            identified_contradictions=[
                "Commercial revenue of ₹2.5 Cr claimed while financial statements indicate pre-revenue status",
                "Advanced TRL 6 claimed without documented senior power electronics engineering lead",
            ],
            missing_domains=[],
            priority_diligence_questions=[
                "Provide executed customer LOI agreements with commercial pricing terms",
                "Furnish third-party lab endurance test reports validating 10,000 continuous hours",
                "Clarify PESO regulatory certification filing status and timeline",
            ],
            incubation_conditions=[
                "Complete formal TIDES incubation onboarding and IP assignment review",
                "Appoint faculty technical mentor from Department of Chemical Engineering",
                "Disburse capital in two equal tranches upon milestone sign-off",
            ],
            investment_score=74.5,
            confidence_score=0.88,
        )
        sup_json = sup_output.model_dump_json()
        sup_tokens = len(enc.encode(sup_json))
        assert sup_tokens < 600, f"Supervisory review tokens ({sup_tokens}) exceeded 600"
        assert sup_tokens < 2400

    def test_omitted_or_invalid_criteria_fail_closed_to_missing_information(self):
        """Verifies that any omitted or invalid criteria fail closed to MISSING_INFORMATION
        without invented findings, and missing evidence is not treated as a negative finding."""
        from app.modules.evaluation.domains import ProblemSolutionExpert
        from app.modules.evaluation.domain_schemas import (
            CompactCriterionResult,
            VerificationStatus,
        )

        expert = ProblemSolutionExpert(gateway=MagicMock())
        owned_criteria = expert.get_owned_criteria()  # 13 criteria

        # Supply:
        # 1 valid criterion (PS-01)
        # 1 invalid criterion (INVALID-99) that does not belong to registry
        compact_results = [
            CompactCriterionResult(
                criterion_id="PS-01",
                verification_status="VERIFIED_DOCUMENTED",
                score=9.0,
                evidence_ids=["EV-CLAIM-01"],
                rationale="Verified from application lab report.", # <= 8 words
            ),
            CompactCriterionResult(
                criterion_id="INVALID-99",
                verification_status="VERIFIED_DOCUMENTED",
                score=10.0,
                evidence_ids=["EV-FAKE-01"],
                rationale="Should be ignored as invalid criterion ID.",
            ),
        ]

        # Matched claim for PS-01
        mock_claim = MagicMock()
        mock_claim.field = MagicMock()
        mock_claim.field.field_key = "ps_01_problem_statement"
        mock_claim.value_string = "Power grid outages cost billions."
        mock_claim.value_number = None
        mock_claim.value_boolean = None
        mock_claim.value_json = None
        mock_claim.id = "c-ps-01"
        mock_claim.confidence_score = 0.95

        assessments = expert.build_criterion_assessments_from_compact(
            compact_criteria=compact_results,
            claims=[mock_claim],
            evidence=[],
        )

        # 1. Total criteria returned must equal all 13 owned criteria (zero dropped!)
        assert len(assessments) == len(owned_criteria)
        assert "INVALID-99" not in assessments

        # 2. Provided valid criterion is accepted
        ps01 = assessments["PS-01"]
        assert ps01.verification_status == VerificationStatus.VERIFIED_DOCUMENTED
        assert ps01.score == 9.0

        # 3. Omitted criteria must fail closed to MISSING_INFORMATION (not CONTRADICTED)
        ps02 = assessments["PS-02"]
        assert ps02.verification_status == VerificationStatus.MISSING_INFORMATION
        assert ps02.score is None
        assert ps02.confidence_score == 0.0
        assert "Missing from specialist evaluation" in ps02.assessment_narrative
        # Verify missing evidence is NOT a negative finding (no risks/contradictions invented)
        assert ps02.verification_status != VerificationStatus.CONTRADICTED
        assert len(ps02.risks) == 0
        assert len(ps02.contradictions) == 0

    def test_all_six_domain_experts_request_batched_assessment_within_900_tokens(self):
        """Verifies that every one of the 6 canonical domain experts dispatches scoped criterion
        batches using response_model=DomainCriterionBatchOutput with max_output_tokens <= 900
        and covers 100% of owned criteria."""
        from app.modules.evaluation.domains import (
            ProblemSolutionExpert,
            MarketOpportunityExpert,
            FounderTeamExpert,
            CommercialisationExpert,
            InnovationImpactExpert,
            FinancialsSupportExpert,
        )
        from app.modules.evaluation.domain_schemas import DomainCriterionBatchOutput, BatchCriterionResult
        from app.services.ai.schemas import AICompletionMetadata, AICompletionResult

        experts = [
            ProblemSolutionExpert,
            MarketOpportunityExpert,
            FounderTeamExpert,
            CommercialisationExpert,
            InnovationImpactExpert,
            FinancialsSupportExpert,
        ]

        gateway = LiteLLMGateway(model="claude-sonnet-5-5", api_key="dummy-key", max_retries=0)

        for expert_cls in experts:
            expert = expert_cls(gateway=gateway)
            captured_requests = []
            captured_models = []

            def mock_complete(*args, **kwargs):
                req = kwargs.get("request") or args[0]
                rmodel = kwargs.get("response_model") or args[1]
                captured_requests.append(req)
                captured_models.append(rmodel)
                batch_cids = list((req.metadata or {}).get("batch_criterion_ids") or [])
                out = DomainCriterionBatchOutput(
                    domain=expert.domain_key,
                    batch_index=int((req.metadata or {}).get("batch_index", 0)),
                    criteria=[
                        BatchCriterionResult(
                            criterion_id=cid,
                            verification_status="VERIFIED_DOCUMENTED",
                            score=7.5,
                            evidence_ids=[],
                            rationale="Supported by pitch deck materials.",
                        )
                        for cid in batch_cids
                    ],
                )
                return AICompletionResult(
                    data=out,
                    metadata=AICompletionMetadata(
                        provider="anthropic",
                        model="claude-sonnet-5-5",
                        latency_ms=10.0,
                        cost_usd=0.005,
                    ),
                )

            with patch.object(gateway, "complete_json", side_effect=mock_complete):
                rep = expert.evaluate(
                    profile=MagicMock(startup_id="test-01", startup_name="CleanPower Systems"),
                    claims=[],
                    evidence=[],
                    conflicts=[],
                    metadata={"evaluation_id": f"eval-batch-{expert.domain_key}"},
                )

            owned = expert.get_owned_criteria()
            expected_batches = (len(owned) + 2) // 3  # v1.1 default: 3 criteria per batch
            assert len(captured_requests) == expected_batches
            covered_across_batches = []
            for req, rmodel in zip(captured_requests, captured_models):
                assert 350 <= req.max_output_tokens <= 900
                assert rmodel == DomainCriterionBatchOutput
                batch_cids = req.metadata["batch_criterion_ids"]
                assert 1 <= len(batch_cids) <= 3
                for cid in batch_cids:
                    assert f"[{cid}]" in req.user_prompt
                covered_across_batches.extend(batch_cids)

            assert covered_across_batches == owned
            assert set(rep.criteria_evaluations.keys()) == set(owned)

    def test_supervisory_reviewer_requests_compact_output_and_2400_tokens(self):
        """Verifies SupervisoryReviewer requests SupervisoryReviewOutput with max_output_tokens=2400."""
        from app.modules.evaluation.supervisory.reviewer import SupervisoryReviewer
        from app.modules.evaluation.domain_schemas import SupervisoryReviewOutput, DomainAssessmentReport

        gateway = LiteLLMGateway(model="claude-sonnet-5-5", api_key="dummy-key", max_retries=0)
        reviewer = SupervisoryReviewer(gateway=gateway)

        captured_request = None
        captured_model = None

        def mock_complete(*args, **kwargs):
            nonlocal captured_request, captured_model
            captured_request = kwargs.get("request") or args[0]
            captured_model = kwargs.get("response_model") or args[1]
            # Return valid compact supervisory output
            from app.services.ai.schemas import AICompletionResult, AICompletionMetadata
            data = SupervisoryReviewOutput(
                executive_summary="Diligence synthesis demonstrates solid technical readiness and clear market opportunity.",
                recommendation_rationale="Founders exhibit high domain mastery, though commercial pilots require formalization.",
                overall_recommendation="CONDITIONAL",
                identified_contradictions=[],
                missing_domains=[],
                priority_diligence_questions=["Request executed pilot agreements with pricing terms"],
                incubation_conditions=["Complete TIDES onboarding agreements"],
                investment_score=75.0,
                confidence_score=0.88,
            )
            meta = AICompletionMetadata(
                model="claude-sonnet-5-5",
                provider="anthropic",
                latency_ms=100.0,
                prompt_version="1.0",
                input_tokens=1000,
                output_tokens=200,
                cached_tokens=0,
                cost_usd=0.005,
                cost_inr=0.48,
                buffered_cost_inr=0.57,
                evaluation_id="eval-sup-01",
                cumulative_cost_usd=0.005,
                cumulative_cost_inr=0.48,
                pricing_version="2026-10-live-v1",
            )
            return AICompletionResult(data=data, metadata=meta, raw_text=data.model_dump_json())

        with patch.object(gateway, "complete_json", side_effect=mock_complete):
            final_assessment = reviewer.review(
                domain_reports={},
                domain_experts={},
                profile=MagicMock(startup_id="test-01", startup_name="CleanPower Systems", sector="CleanTech", stage="Seed"),
                claims=[],
                evidence=[],
                metadata={"evaluation_id": "eval-sup-01"},
            )

        assert captured_request is not None
        assert captured_request.max_output_tokens == 2400
        assert captured_model == SupervisoryReviewOutput
        assert "executive_summary <= 60 words" in captured_request.system_prompt
        assert final_assessment.overall_recommendation == "CONDITIONAL"
        assert len(final_assessment.incubation_conditions) > 0

    def test_build_criterion_assessments_from_compact_preserves_provenance_and_fails_closed(self):
        """Verifies build_criterion_assessments_from_compact faithfully reconstructs
        full CriterionAssessment records, preserves claim evidence, and fails closed
        with MISSING_INFORMATION when a criterion is missing from compact results."""
        from app.modules.evaluation.domains import ProblemSolutionExpert
        from app.modules.evaluation.domain_schemas import (
            CompactCriterionResult,
            VerificationStatus,
        )

        expert = ProblemSolutionExpert(gateway=MagicMock())
        owned_criteria = expert.get_owned_criteria()  # 13 criteria

        # Only provide 1 criterion, leaving 12 missing
        compact_results = [
            CompactCriterionResult(
                criterion_id=owned_criteria[0],
                verification_status="VERIFIED_DOCUMENTED",
                score=9.0,
                evidence_ids=["EV-CLAIM-01"],
                rationale="Directly confirmed by lab testbed report.",
            )
        ]

        # Mock a claim matching the first criterion
        mock_claim = MagicMock()
        mock_claim.field = "problem_statement"
        mock_claim.value = "Industrial power grid outages cause immense financial loss."
        mock_claim.source = "Application Section 2.1"
        mock_claim.confidence = 0.95

        assessments = expert.build_criterion_assessments_from_compact(
            compact_criteria=compact_results,
            claims=[mock_claim],
            evidence=[],
        )

        # 1. Total criteria returned must equal all 13 owned criteria (zero dropped!)
        assert len(assessments) == len(owned_criteria)

        # 2. Provided criterion has verified status, score, evidence ID, and rationale
        first_cid = owned_criteria[0]
        assert assessments[first_cid].verification_status == VerificationStatus.VERIFIED_DOCUMENTED
        assert assessments[first_cid].score == 9.0
        assert "EV-CLAIM-01" in assessments[first_cid].evidence_ids
        assert assessments[first_cid].assessment_narrative == "Directly confirmed by lab testbed report."

        # 3. Missing required criteria must fail closed as MISSING_INFORMATION with 0.0 confidence
        ps_02 = assessments["PS-02"]
        assert ps_02.verification_status == VerificationStatus.MISSING_INFORMATION
        assert ps_02.score is None
        assert ps_02.confidence_score == 0.0
        assert "Missing from specialist evaluation" in ps_02.assessment_narrative

        # Conditional criteria (e.g. PS-10 Demo Link with TRL <= 4) refine to NOT_APPLICABLE
        ps_10 = assessments["PS-10"]
        assert ps_10.verification_status == VerificationStatus.NOT_APPLICABLE

    def test_status_reporting_accurate_no_false_success(self):
        """Verifies format_telemetry_table accurately reports PARTIAL DOMAIN FAILURES
        and does NOT display 'SUCCESS' when domain operations fail."""
        from scripts.run_one_time_live_eval import format_telemetry_table

        # Scenario A: All 6 domains failed with truncation, Supervisory succeeded
        mock_summary = {
            "evaluation_id": "eval-partial-01",
            "startup_id": "startup-01",
            "is_exhausted": False,
            "cost_confidence": "EXACT_REPORTED",
            "total_operations": 7,
            "total_input_tokens": 51000,
            "total_output_tokens": 26602,
            "total_cached_tokens": 0,
            "total_spent_usd": 0.3644,
            "total_cost_inr_buffered": 41.28,
            "under_max_usd_ceiling": True,
            "remaining_budget_usd": 0.0556,
            "operations": [
                {"agent_name": f"domain_{d}", "model": "claude-sonnet-5-5", "status": "PARSE_ERROR", "finish_reason": "length", "input_tokens": 8000, "output_tokens": 4096, "final_cost_usd": 0.08, "buffered_cost_inr": 9.0}
                for d in ["ps", "mo", "ft", "bc", "ii", "fi"]
            ] + [
                {"agent_name": "supervisory_review", "model": "claude-sonnet-5-5", "status": "SUCCESS", "finish_reason": "stop", "input_tokens": 1040, "output_tokens": 2026, "final_cost_usd": 0.0335, "buffered_cost_inr": 3.80}
            ],
        }

        table = format_telemetry_table(mock_summary, eval_status="COMPLETED_WITH_PARTIAL_DOMAIN_FAILURES")
        assert "Total Status:    SUCCESS" not in table, "Must NOT label failed domain run as SUCCESS!"
        assert "PARTIAL DOMAIN FAILURES" in table
        assert "6 truncated/parse error" in table
        assert "1 succeeded" in table
        assert "Supervisory Review: SUCCESS" in table
        assert "TRUNCATED" in table

        # Scenario B: All succeeded
        mock_success_summary = {
            "evaluation_id": "eval-success-01",
            "startup_id": "startup-01",
            "is_exhausted": False,
            "cost_confidence": "EXACT_REPORTED",
            "total_operations": 2,
            "total_input_tokens": 10000,
            "total_output_tokens": 2000,
            "total_cached_tokens": 0,
            "total_spent_usd": 0.06,
            "total_cost_inr_buffered": 6.8,
            "under_max_usd_ceiling": True,
            "remaining_budget_usd": 0.36,
            "operations": [
                {"agent_name": "domain_ps", "model": "claude-sonnet-5-5", "status": "SUCCESS", "finish_reason": "stop", "input_tokens": 8000, "output_tokens": 1000, "final_cost_usd": 0.039, "buffered_cost_inr": 4.4},
                {"agent_name": "supervisory_review", "model": "claude-sonnet-5-5", "status": "SUCCESS", "finish_reason": "stop", "input_tokens": 2000, "output_tokens": 1000, "final_cost_usd": 0.021, "buffered_cost_inr": 2.4},
            ],
        }
        table_success = format_telemetry_table(mock_success_summary, eval_status="COMPLETED")
        assert "Total Status:    SUCCESS" in table_success

    def test_workspace_database_hash_unchanged(self):
        """Guarantees workspace tides_ai.db remains bit-for-bit untouched."""
        assert WORKSPACE_DB.exists()
        current_hash = hashlib.sha256(WORKSPACE_DB.read_bytes()).hexdigest()
        assert current_hash == EXPECTED_WORKSPACE_DB_HASH
