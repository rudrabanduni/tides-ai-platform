"""Offline unit & integration tests for deterministic criterion-batched domain evaluation.

Verifies:
1. Canonical registry-driven batching (`batch_criteria`) & configurable batch sizes
2. Scoped compact batch prompts (no full-profile/all-criteria bloat or cross-batch leakage)
3. Deterministic local merge (`merge_domain_criterion_batches`) rejecting unknown,
   duplicate, missing, or cross-batch mismatched criteria while preserving >2 evidence IDs
4. Deterministic Python summary synthesis + ReportValidator compliance
5. Selective per-batch retry, checkpoint preservation, partial recovery without
   rerunning succeeded batches, and fail-closed budget-insufficient handling
6. Simulated PETREVOLT-scale 6-domain run (19 bounded batches <= 900 tokens) under $0.35
"""

from __future__ import annotations

import uuid
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.modules.ai.orchestrator.pipeline import coordinate_evaluation_pipeline
from app.modules.ai.orchestrator.startup_profile_extraction import (
    CompetitorEntry,
    FounderEntry,
    KeyFeatureBenefit,
    PatentEntry,
    PilotAgreementEntry,
    StartupProfileExtraction,
    ThreeYearMetric,
)
from app.modules.evaluation.domain_schemas import (
    BatchCriterionResult,
    DomainAssessmentReport,
    DomainCriterionBatchOutput,
    SupervisoryReviewOutput,
    VerificationStatus,
)
from app.modules.evaluation.domains import (
    CommercialisationExpert,
    FinancialsSupportExpert,
    FounderTeamExpert,
    InnovationImpactExpert,
    MarketOpportunityExpert,
    ProblemSolutionExpert,
)
from app.modules.evaluation.domains.batching import (
    batch_criteria,
    build_domain_batch_prompts,
    get_domain_batch_checkpoint_path,
    merge_domain_criterion_batches,
    resolve_domain_batch_output_token_limit,
    build_batch_evidence_handles,
    resolve_evidence_references,
)
from app.modules.evaluation.domains.registry import (
    CANONICAL_DOMAINS,
    get_criteria_for_domain,
    get_criterion_metadata,
)
from app.modules.evaluation.graph.graph_builder import ObservationGraphBuilder
from app.modules.evaluation.report.report_engine import DueDiligenceReportEngine
from app.modules.evaluation.report.report_validator import ReportValidator
from app.services.ai.cost_ledger import CostLedgerManager
from app.services.ai.exceptions import AIResponseParseError
from app.services.ai.pricing import get_pricing_catalog
from app.services.ai.schemas import AICompletionMetadata, AICompletionResult


def _make_claim(cid_uuid: str, field_key: str, value: str, conf: float = 0.9):
    return SimpleNamespace(
        id=cid_uuid,
        field=SimpleNamespace(field_key=field_key),
        field_name=field_key,
        value_string=value,
        value_number=None,
        value_boolean=None,
        value_json=None,
        confidence_score=conf,
    )


def _make_evidence(ev_id: str, claim_id: str, section: str, page: int, snippet: str):
    return SimpleNamespace(
        id=ev_id,
        evidence_id=ev_id,
        claim_id=claim_id,
        section_name=section,
        page_number=page,
        evidence_snippet=snippet,
        source_document_id="pitch_deck.pdf",
    )


def _known_evidence():
    """Real evidence records backing the EV-01..EV-03 IDs cited by the mocked specialist.

    v1.1 evidence guard: cited evidence IDs must exist in the startup's evidence set;
    unknown references are rejected instead of being copied into the report.
    """
    return [
        _make_evidence("EV-01", "cl-known", "Problem Slide", 3, "Documented problem statement."),
        _make_evidence("EV-02", "cl-known", "Solution Slide", 5, "Documented solution."),
        _make_evidence("EV-03", "cl-known", "Market Slide", 8, "Documented market sizing."),
    ]


def test_registry_driven_batch_criteria_sizes_and_order():
    expected_batch_counts = {
        "problem_solution": [5, 5, 3],
        "market_opportunity": [5, 5],
        "founder_team": [5, 5, 3],
        "commercialisation": [5, 5, 3],
        "innovation_impact": [5, 5, 1],
        "financials_support": [5, 5, 5, 5, 1],
    }

    total_batches = 0
    for domain_key in CANONICAL_DOMAINS:
        criteria = get_criteria_for_domain(domain_key)
        batches = batch_criteria(criteria, max_criteria_per_call=5)
        assert [len(b) for b in batches] == expected_batch_counts[domain_key]
        flattened = [cid for b in batches for cid in b]
        assert flattened == criteria
        # Every item retains valid registry metadata
        for cid in flattened:
            meta = get_criterion_metadata(cid)
            assert meta["domain"] == domain_key
        total_batches += len(batches)

    assert total_batches == 19

    # Configurable alternative batch size (4 criteria per call)
    fi_batches_4 = batch_criteria(get_criteria_for_domain("financials_support"), max_criteria_per_call=4)
    assert [len(b) for b in fi_batches_4] == [4, 4, 4, 4, 4, 1]
    assert [c for b in fi_batches_4 for c in b] == get_criteria_for_domain("financials_support")

    # Token cap helper stays <= configured 900 cap
    # v1.1 sizing: 80-token envelope + 220 tokens/criterion, floor 350 (the old 180/criterion
    # allowance truncated every live 5-criterion batch at 900 tokens).
    assert resolve_domain_batch_output_token_limit(5, 900) == 900
    assert resolve_domain_batch_output_token_limit(3, 900) == 740
    assert resolve_domain_batch_output_token_limit(1, 900) == 350

    with pytest.raises(ValueError, match="max_criteria_per_call"):
        batch_criteria(["PS-01"], max_criteria_per_call=0)


def test_scoped_batch_prompt_excludes_other_batches_and_scopes_external_research():
    ps_criteria = get_criteria_for_domain("problem_solution")
    batches = batch_criteria(ps_criteria, max_criteria_per_call=5)

    claims = [
        _make_claim("cl-ps01", "ps_01_problem_statement", "Waste PET bottlenecks sodium anode supply."),
        _make_claim("cl-ps07", "ps_07_unique_value_proposition", "Proprietary PET solvolysis lowers BOM 30%."),
        _make_claim("cl-fi01", "fi_01_revenue_forecast", "Year 3 projection 12 Cr INR."),
    ]
    evidence = [
        _make_evidence("EV-PS-01", "cl-ps01", "Problem Slide", 3, "65% cost bottleneck in imported hard carbon."),
        _make_evidence("EV-PS-07", "cl-ps07", "UVP Slide", 7, "Solvolysis process reduces precursor cost."),
        _make_evidence("EV-FI-01", "cl-fi01", "Financials", 15, "INR 12 Cr forecast in FY29."),
    ]
    conflicts = [
        SimpleNamespace(field_key="ps_01_problem_statement", claim_a_id="cl-ps01", description="PS-01 cost figure conflict"),
        SimpleNamespace(field_key="ps_07_unique_value_proposition", claim_a_id="cl-ps07", description="PS-07 BOM conflict"),
    ]

    sys_p0, usr_p0 = build_domain_batch_prompts(
        domain_key="problem_solution",
        domain_title="Problem & Solution",
        company_name="PETREVOLT",
        batch_index=0,
        total_batches=len(batches),
        batch_criterion_ids=batches[0],
        claims=claims,
        evidence=evidence,
        conflicts=conflicts,
    )

    for cid in batches[0]:
        assert f"[{cid}]" in usr_p0
    for other in batches[1] + batches[2]:
        assert f"[{other}]" not in usr_p0

    # Evidence is shown via short per-batch handles (E1..En) that map back to real evidence IDs.
    handles = build_batch_evidence_handles(batches[0], claims, evidence)
    assert {h: ev.evidence_id for h, ev in handles.items()} == {"E1": "EV-PS-01"}
    assert "Evidence [E1]" in usr_p0
    assert "65% cost bottleneck" in usr_p0
    assert "EV-PS-01" not in usr_p0  # raw UUID-style IDs are not spent as output tokens
    assert "PS-01 cost figure conflict" in usr_p0
    assert "Solvolysis process reduces precursor cost" not in usr_p0
    assert "INR 12 Cr forecast" not in usr_p0
    resolved, rejected = resolve_evidence_references(["E1", "E9", "EV-FAKE"], handles, {"EV-PS-01"})
    assert resolved == ["EV-PS-01"]
    assert rejected == ["E9", "EV-FAKE"]
    assert "PS-07 BOM conflict" not in usr_p0
    assert "MUST structure your analysis" not in sys_p0

    # Market Opportunity external research scoping across MO batches 0 and 1
    mo_batches = batch_criteria(get_criteria_for_domain("market_opportunity"), max_criteria_per_call=5)
    ext_items = [
        {"title": "TAM Benchmark Report", "source": "iea.org", "snippet": "India ESS TAM", "criteria": ["MO-01", "MO-04"]},
        {"title": "Competitor Filing", "source": "competitor.com", "snippet": "Rival cell maker", "criteria": ["MO-07", "MO-08"]},
    ]
    _, mo_usr0 = build_domain_batch_prompts(
        domain_key="market_opportunity",
        domain_title="Market Opportunity",
        company_name="PETREVOLT",
        batch_index=0,
        total_batches=len(mo_batches),
        batch_criterion_ids=mo_batches[0],
        claims=[],
        evidence=[],
        conflicts=[],
        external_research_items=ext_items,
    )
    _, mo_usr1 = build_domain_batch_prompts(
        domain_key="market_opportunity",
        domain_title="Market Opportunity",
        company_name="PETREVOLT",
        batch_index=1,
        total_batches=len(mo_batches),
        batch_criterion_ids=mo_batches[1],
        claims=[],
        evidence=[],
        conflicts=[],
        external_research_items=ext_items,
    )
    assert "TAM Benchmark Report" in mo_usr0
    assert "Competitor Filing" not in mo_usr0
    assert "Competitor Filing" in mo_usr1
    assert "TAM Benchmark Report" not in mo_usr1


def test_deterministic_local_merge_validation_and_evidence_preservation():
    ps_criteria = get_criteria_for_domain("problem_solution")
    batches = batch_criteria(ps_criteria, max_criteria_per_call=5)

    def make_batch(idx: int) -> DomainCriterionBatchOutput:
        return DomainCriterionBatchOutput(
            domain="problem_solution",
            batch_index=idx,
            criteria=[
                BatchCriterionResult(
                    criterion_id=cid,
                    verification_status=VerificationStatus.VERIFIED_DOCUMENTED,
                    score=8.0,
                    evidence_ids=["EV-01", "EV-02", "EV-03"] if cid == "PS-01" else ["EV-01"],
                    rationale=f"Documented {cid}.",
                    missing_information="Pilot third-party stamp" if cid == "PS-02" else None,
                    source_provenance="Deck Slide 3" if cid == "PS-01" else None,
                )
                for cid in batches[idx]
            ],
        )

    # Deliberately supply batches out of order; merge restores canonical registry order and preserves all >2 evidence IDs
    merged = merge_domain_criterion_batches(
        "problem_solution",
        [make_batch(2), make_batch(0), make_batch(1)],
        expected_batches=batches,
    )
    assert [m.criterion_id for m in merged] == ps_criteria
    assert merged[0].evidence_ids == ["EV-01", "EV-02", "EV-03"]
    assert merged[0].source_provenance == "Deck Slide 3"
    assert merged[1].missing_information == "Pilot third-party stamp"

    # Reject missing criterion
    b0_missing = DomainCriterionBatchOutput(
        domain="problem_solution",
        batch_index=0,
        criteria=make_batch(0).criteria[:-1],
    )
    with pytest.raises(ValueError, match="missing canonical criteria"):
        merge_domain_criterion_batches("problem_solution", [b0_missing, make_batch(1), make_batch(2)], expected_batches=batches)

    # Reject duplicate criterion
    dup_criteria = make_batch(0).criteria + [make_batch(0).criteria[0]]
    b0_dup = DomainCriterionBatchOutput(domain="problem_solution", batch_index=0, criteria=dup_criteria)
    with pytest.raises(ValueError, match="Duplicate criterion_id"):
        merge_domain_criterion_batches("problem_solution", [b0_dup, make_batch(1), make_batch(2)], expected_batches=batches)

    # Reject unknown / out-of-domain criterion
    b0_unknown = make_batch(0)
    b0_unknown.criteria[0] = BatchCriterionResult(
        criterion_id="II-07",
        verification_status=VerificationStatus.VERIFIED_DOCUMENTED,
        rationale="Wrong domain.",
    )
    with pytest.raises(ValueError, match="Unknown or out-of-domain"):
        merge_domain_criterion_batches("problem_solution", [b0_unknown, make_batch(1), make_batch(2)], expected_batches=batches)

    # Reject cross-batch mismatch (PS-06 returned in batch 0)
    b0_cross = make_batch(0)
    b0_cross.criteria[0] = BatchCriterionResult(
        criterion_id="PS-06",
        verification_status=VerificationStatus.VERIFIED_DOCUMENTED,
        rationale="Belongs to batch 1.",
    )
    with pytest.raises(ValueError, match="Cross-batch criterion mismatch"):
        merge_domain_criterion_batches("problem_solution", [b0_cross, make_batch(1), make_batch(2)], expected_batches=batches)


def test_partial_batch_retry_checkpoint_recovery_without_rerunning_succeeded_batches():
    eval_id = f"eval-batch-recover-{uuid.uuid4().hex[:8]}"
    ckpt_path = get_domain_batch_checkpoint_path(eval_id, "problem_solution")
    if ckpt_path.exists():
        ckpt_path.unlink()

    call_counts = {0: 0, 1: 0, 2: 0}
    fail_batch_1 = True

    def mock_complete_json(req, response_model):
        b_idx = int(req.metadata["batch_index"])
        call_counts[b_idx] += 1
        if b_idx == 1 and fail_batch_1:
            raise AIResponseParseError("Simulated transient truncation on batch 1")
        return AICompletionResult(
            data=DomainCriterionBatchOutput(
                domain="problem_solution",
                batch_index=b_idx,
                criteria=[
                    BatchCriterionResult(
                        criterion_id=cid,
                        verification_status=VerificationStatus.VERIFIED_DOCUMENTED,
                        score=7.8,
                        evidence_ids=["EV-01", "EV-02", "EV-03"],
                        rationale=f"Batch {b_idx} substantiated {cid}.",
                    )
                    for cid in req.metadata["batch_criterion_ids"]
                ],
            ),
            metadata=AICompletionMetadata(
                provider="anthropic",
                model="claude-sonnet-5-5",
                latency_ms=10.0,
                cost_usd=0.004,
            ),
        )

    mock_gw = MagicMock()
    mock_gw.complete_json.side_effect = mock_complete_json
    expert = ProblemSolutionExpert(gateway=mock_gw)

    # 1. Fail permanently on batch 1 (retry once only on batch 1; batch 0 succeeds and is NOT retried)
    rep_failed = expert.evaluate(
        profile=SimpleNamespace(startup_id="st-01", startup_name="PETREVOLT"),
        claims=[],
        evidence=_known_evidence(),
        conflicts=[],
        metadata={"evaluation_id": eval_id, "domain_batch_max_retries": 1, "max_criteria_per_call": 5},
    )

    assert call_counts == {0: 1, 1: 2, 2: 0}
    assert "evaluation incomplete" in rep_failed.summary.lower()
    assert rep_failed.composite_domain_confidence == 0.0
    assert rep_failed.strengths == []
    assert any("BATCH-1" in r.id for r in rep_failed.risks)
    # Batch 0 succeeded criteria were preserved without discarding or fabricating batch 1
    assert rep_failed.criteria_evaluations["PS-01"].evidence_ids == ["EV-01", "EV-02", "EV-03"]
    assert rep_failed.criteria_evaluations["PS-06"].verification_status == VerificationStatus.MISSING_INFORMATION
    assert rep_failed.criteria_evaluations["PS-06"].confidence_score == 0.0
    assert ckpt_path.exists()

    # 2. Resume after fixing batch 1: batch 0 is loaded from checkpoint and NEVER rerun; only batch 1 & 2 execute
    fail_batch_1 = False
    rep_recovered = expert.evaluate(
        profile=SimpleNamespace(startup_id="st-01", startup_name="PETREVOLT"),
        claims=[],
        evidence=_known_evidence(),
        conflicts=[],
        metadata={"evaluation_id": eval_id, "domain_batch_max_retries": 1, "max_criteria_per_call": 5},
    )

    assert call_counts == {0: 1, 1: 3, 2: 1}
    assert rep_recovered.composite_domain_confidence > 0.0
    assert len(rep_recovered.criteria_evaluations) == 13
    assert rep_recovered.criteria_evaluations["PS-01"].evidence_ids == ["EV-01", "EV-02", "EV-03"]
    assert rep_recovered.criteria_evaluations["PS-06"].verification_status == VerificationStatus.VERIFIED_DOCUMENTED
    assert not ckpt_path.exists()


def test_insufficient_budget_skips_retry_and_fails_domain_cleanly():
    mgr = CostLedgerManager.get_instance()
    eval_id = f"eval-low-budget-{uuid.uuid4().hex[:8]}"
    mgr.clear_ledger(eval_id)
    # Give tiny budget ($0.002) so ledger lacks headroom for retrying batch 0
    ledger = mgr.get_or_create_ledger(evaluation_id=eval_id, startup_id="st-budget", max_budget_usd=0.002)
    res_id = ledger.reserve_budget(0.001, "prior_op")
    ledger.reconcile_operation(
        reservation_id=res_id,
        agent_name="prior_op",
        provider="anthropic",
        model="claude-sonnet-5-5",
        input_tokens=100,
        output_tokens=10,
        actual_cost_usd=0.0015,
    )

    attempts = 0
    def mock_fail(req, response_model):
        nonlocal attempts
        attempts += 1
        raise AIResponseParseError("Parse failure on initial batch attempt")

    mock_gw = MagicMock()
    mock_gw.complete_json.side_effect = mock_fail
    expert = MarketOpportunityExpert(gateway=mock_gw)

    report = expert.evaluate(
        profile=SimpleNamespace(startup_id="st-budget", startup_name="BudgetCapCo"),
        claims=[],
        evidence=[],
        conflicts=[],
        metadata={"evaluation_id": eval_id, "domain_batch_max_retries": 2},
    )

    # Budget insufficient ($0.0005 left < batch worst-case) => retry skipped!
    assert attempts == 1
    assert "evaluation incomplete" in report.summary.lower()
    assert report.composite_domain_confidence == 0.0
    assert all(
        c.verification_status == VerificationStatus.MISSING_INFORMATION
        for c in report.criteria_evaluations.values()
    )
    mgr.clear_ledger(eval_id)


def test_batched_domain_reports_pass_report_engine_and_validator():
    mock_gw = MagicMock()
    def complete_json(req, response_model):
        meta = req.metadata or {}
        return AICompletionResult(
            data=DomainCriterionBatchOutput(
                domain=meta["domain"],
                batch_index=int(meta["batch_index"]),
                criteria=[
                    BatchCriterionResult(
                        criterion_id=cid,
                        verification_status=VerificationStatus.VERIFIED_DOCUMENTED,
                        score=8.0,
                        evidence_ids=["EV-01", "EV-02", "EV-03"],
                        rationale=f"Documented {cid} in primary filings.",
                    )
                    for cid in meta["batch_criterion_ids"]
                ],
            ),
            metadata=AICompletionMetadata(
                provider="anthropic",
                model="claude-sonnet-5-5",
                latency_ms=10.0,
                cost_usd=0.005,
            ),
        )
    mock_gw.complete_json.side_effect = complete_json

    experts = {
        "problem_solution": ProblemSolutionExpert(gateway=mock_gw),
        "market_opportunity": MarketOpportunityExpert(gateway=mock_gw),
        "founder_team": FounderTeamExpert(gateway=mock_gw),
        "commercialisation": CommercialisationExpert(gateway=mock_gw),
        "innovation_impact": InnovationImpactExpert(gateway=mock_gw),
        "financials_support": FinancialsSupportExpert(gateway=mock_gw),
    }
    profile = SimpleNamespace(startup_id="st-rep", startup_name="Petrevolt Energy", sector="Battery Tech")
    domain_reports = {
        dkey: exp.evaluate(profile, [], _known_evidence(), [], {"evaluation_id": f"eval-rep-{dkey}"})
        for dkey, exp in experts.items()
    }

    builder = ObservationGraphBuilder()
    graph = builder.build(
        profile=profile,
        claims=[],
        evidence=[],
        assessments=list(domain_reports.values()),
    )
    graph.domain_reports = {dkey: rep.model_dump(mode="json") for dkey, rep in domain_reports.items()}
    graph.domain_assessments = domain_reports
    graph = DueDiligenceReportEngine.generate(graph)
    validation = ReportValidator.validate_structured(graph)
    assert validation["valid"] is True, f"Validation errors: {validation.get('errors')}"
    # All >2 evidence IDs preserved per criterion
    assert domain_reports["problem_solution"].criteria_evaluations["PS-01"].evidence_ids == ["EV-01", "EV-02", "EV-03"]


@pytest.mark.anyio
async def test_simulated_petrevolt_pipeline_completes_under_35_cents_with_batched_domains(tmp_path, monkeypatch):
    from app.core.config import get_settings

    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("TIDES_LIVE_EVAL_REPORT_PATH", str(tmp_path / "live_eval_run_report.json"))
    monkeypatch.setenv("UPLOAD_DIR", str(upload_dir))
    monkeypatch.setenv("AI_ENABLED", "true")
    monkeypatch.setenv("AI_PROVIDER", "litellm")
    monkeypatch.setenv("AI_MAX_EVALUATION_BUDGET_USD", "0.35")
    get_settings.cache_clear()

    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSession()

    try:
        from app.core.enums import DocumentProcessingStatus, DocumentType
        from app.modules.documents.models import Document
        from app.modules.startups.models import StartupApplication

        doc_path = tmp_path / "petrevolt_deck.pdf"
        doc_path.write_bytes(b"%PDF-1.4\n%Mock PETREVOLT pitch deck bytes")

        startup = StartupApplication(
            id=uuid.uuid4(),
            startup_name="PETREVOLT ENERGY SOLUTIONS PVT LTD",
            sector="Battery Tech",
            stage="Prototype",
        )
        db.add(startup)
        db.flush()

        doc = Document(
            id=uuid.uuid4(),
            startup_id=startup.id,
            document_type=DocumentType.PITCH_DECK,
            original_filename="PETREVOLT_Deck.pdf",
            stored_filename="petrevolt_deck.pdf",
            file_path=str(doc_path),
            content_type="application/pdf",
            file_size=doc_path.stat().st_size,
            parsed_text="PETREVOLT converts post-consumer PET waste into hard-carbon sodium battery anodes.",
            processing_status=DocumentProcessingStatus.PARSED,
        )
        db.add(doc)
        db.commit()
        db.refresh(startup)

        catalog = get_pricing_catalog()
        eval_calls = []

        def mock_complete_json(*args, **kwargs):
            req = kwargs.get("request") or args[0]
            rmodel = kwargs.get("response_model") or args[1]
            eval_calls.append(req)
            sname = rmodel.__name__

            if req.agent_name.startswith("extraction_"):
                data = rmodel() if sname != "StartupProfileExtraction" else StartupProfileExtraction(
                    company_name="PETREVOLT ENERGY SOLUTIONS PVT LTD",
                    problem_statement="PET waste converted into porous hard carbon sodium anodes.",
                    founders=[FounderEntry(name="A. Founder", role="CEO")],
                    competitors=[CompetitorEntry(name="CATL")],
                    patents=[PatentEntry(title="PET Solvolysis", status="Filed")],
                    pilot_agreements=[PilotAgreementEntry(partner="Campus Lab")],
                    key_features_benefits=[KeyFeatureBenefit(feature="PET-derived anode")],
                    three_year_revenue=ThreeYearMetric(year_1="0", year_2="50L", year_3="2Cr"),
                )
                model_name = get_settings().ai_fast_model
                in_tok, out_tok = 4000, 350
            elif sname == "DomainCriterionBatchOutput":
                meta = req.metadata or {}
                assert 350 <= req.max_output_tokens <= 900
                data = DomainCriterionBatchOutput(
                    domain=meta["domain"],
                    batch_index=int(meta["batch_index"]),
                    criteria=[
                        BatchCriterionResult(
                            criterion_id=cid,
                            verification_status=VerificationStatus.VERIFIED_DOCUMENTED,
                            score=7.5,
                            evidence_ids=[],
                            rationale="Verified against PETREVOLT deck slides.",
                        )
                        for cid in meta["batch_criterion_ids"]
                    ],
                )
                model_name = get_settings().ai_reasoning_model
                in_tok, out_tok = 850, min(320, 60 * len(meta["batch_criterion_ids"]))
            elif sname == "SupervisoryReviewOutput":
                data = SupervisoryReviewOutput(
                    executive_summary="All 6 canonical domains completed cleanly via criterion batching.",
                    recommendation_rationale="Conditional incubation tied to ARAI/ICAT cell qualification.",
                    overall_recommendation="CONDITIONAL",
                    identified_contradictions=[],
                    missing_domains=[],
                    priority_diligence_questions=["Submit AIS-156 cell qualification roadmap."],
                    incubation_conditions=["Quarterly cycling telemetry verification."],
                    confidence_score=0.86,
                )
                model_name = get_settings().ai_reasoning_model
                in_tok, out_tok = 1350, 480
            else:
                data = rmodel()
                model_name = get_settings().ai_fast_model
                in_tok, out_tok = 500, 100

            cost = catalog.calculate_cost(model=model_name, prompt_tokens=in_tok, completion_tokens=out_tok)
            if req.evaluation_id:
                ledger = CostLedgerManager.get_instance().get_ledger(req.evaluation_id)
                if ledger is not None:
                    res_id = ledger.reserve_budget(max(cost, 0.002), req.agent_name)
                    ledger.reconcile_operation(
                        reservation_id=res_id,
                        agent_name=req.agent_name,
                        provider="anthropic",
                        model=model_name,
                        input_tokens=in_tok,
                        output_tokens=out_tok,
                        actual_cost_usd=cost,
                        finish_reason="stop",
                    )

            return AICompletionResult(
                data=data,
                metadata=AICompletionMetadata(
                    provider="anthropic",
                    model=model_name,
                    latency_ms=10.0,
                    input_tokens=in_tok,
                    output_tokens=out_tok,
                    actual_cost_usd=cost,
                    cost_usd=cost,
                ),
            )

        gw = MagicMock()
        gw.complete_json.side_effect = mock_complete_json

        with patch("app.modules.ai.orchestrator.pipeline.create_ai_gateway", return_value=gw), \
             patch("app.modules.evaluation.expert_agent.create_ai_gateway", return_value=gw), \
             patch("app.modules.evaluation.supervisory.reviewer.create_ai_gateway", return_value=gw):
            res = await coordinate_evaluation_pipeline(
                db=db,
                startup_name=startup.startup_name,
                sector=startup.sector,
                stage=startup.stage,
                files=[],
                existing_startup_id=startup.id,
                max_budget_usd=0.35,
            )

        assert res["evaluation_status"] == "COMPLETED"
        batch_reqs = [r for r in eval_calls if r.agent_name.startswith("domain_")]
        # v1.1 default: 3 criteria per batch -> PS 5, MO 4, FT 5, BC 5, II 4, FI 7 = 30 batches
        assert len(batch_reqs) == 30
        assert all(r.max_output_tokens <= 900 for r in batch_reqs)
        total_spent = float(res["cost_observability"]["total_spent_usd"])
        assert total_spent < 0.35
        # Notice realistic batched total should be well under $0.20 vs the old $0.32 failure!
        assert total_spent < 0.22
    finally:
        db.close()
        get_settings.cache_clear()
