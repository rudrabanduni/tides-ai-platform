import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from typing import Any

from app.modules.evaluation.context.context_builder import ContextBuilder
from app.modules.evaluation.context.context_filters import FounderContextFilter
from app.modules.evaluation.context.context_registry import context_registry
from app.modules.evaluation.founder_expert import FounderExpert


# Helper function to generate mock claims
def create_mock_claim(field_key: str, value: Any, confidence: float, created_at: datetime = None) -> Any:
    class DummyField:
        def __init__(self, key: str):
            self.field_key = key

    class DummyClaim:
        def __init__(self):
            self.id = uuid4()
            self.field = DummyField(field_key)
            self.value_string = str(value)
            self.value_number = None
            self.value_boolean = None
            self.value_json = None
            self.value_date = None
            self.confidence_score = confidence
            self.validation_status = "VALIDATED"
            self.created_at = created_at or datetime.utcnow()
            self.reasoning = "Mock reasoning for test claim."

    return DummyClaim()


# Helper function to generate mock evidence
def create_mock_evidence(claim_id: Any, doc_type: str = "Pitch Deck") -> Any:
    class DummyDocument:
        def __init__(self):
            self.document_type = doc_type

    class DummyEvidence:
        def __init__(self):
            self.id = uuid4()
            self.claim_id = claim_id
            self.evidence_snippet = "Mock evidence snippet text."
            self.section_name = "Mock Section"
            self.page_number = 1
            self.source_document = DummyDocument()

    return DummyEvidence()


def test_context_builder_registry() -> None:
    # Test registry mapping
    founder_filter = context_registry.get_filter(FounderExpert)
    assert isinstance(founder_filter, FounderContextFilter)
    
    with pytest.raises(ValueError):
        context_registry.get_filter("NonExistentExpert")


def test_context_builder_filtering_and_stats() -> None:
    # 1. Setup mock data: 2 founder claims, 1 product claim (should be filtered out)
    claim1 = create_mock_claim("founder_names", "Alice & Bob", 0.9)
    claim2 = create_mock_claim("commitment_level", "Full-time", 0.85)
    claim3 = create_mock_claim("revenue", 100000.0, 0.95)  # Product/Financial claim
    
    evidence1 = create_mock_evidence(claim1.id, "Pitch Deck")
    evidence2 = create_mock_evidence(claim2.id, "Financial Statement")
    evidence3 = create_mock_evidence(claim3.id, "Pitch Deck")

    # 2. Build context
    profile = Any
    metadata = {"org": "TIDES"}
    context = ContextBuilder.build_context(
        profile=profile,
        all_claims=[claim1, claim2, claim3],
        all_evidence=[evidence1, evidence2, evidence3],
        all_conflicts=[],
        metadata=metadata,
        context_filter=FounderContextFilter()
    )

    # 3. Assertions
    assert len(context.claims) == 2  # Only founder claims
    assert claim3 not in context.claims
    assert len(context.evidence) == 2  # Only evidence linked to final founder claims
    assert evidence3 not in context.evidence
    
    assert context.context_statistics["claims_count"] == 2
    assert context.context_statistics["evidence_count"] == 2
    assert context.source_counts["Pitch Deck"] == 1
    assert context.source_counts["Financial Statement"] == 1
    assert context.confidence_summary["average_confidence"] == 0.875


def test_context_builder_deduplication() -> None:
    # Multiple claims for the same field key "founder_names"
    claim_low = create_mock_claim("founder_names", "Alice", 0.7)
    claim_high = create_mock_claim("founder_names", "Alice & Bob", 0.9)
    
    context = ContextBuilder.build_context(
        profile=None,
        all_claims=[claim_low, claim_high],
        all_evidence=[],
        all_conflicts=[],
        metadata={},
        context_filter=FounderContextFilter()
    )
    
    # Deduplication should keep ONLY the highest confidence claim
    assert len(context.claims) == 1
    assert context.claims[0].confidence_score == 0.9
    assert context.claims[0].value_string == "Alice & Bob"


def test_context_builder_confidence_filtering() -> None:
    claim1 = create_mock_claim("founder_names", "Alice", 0.5)
    claim2 = create_mock_claim("commitment_level", "Full-time", 0.8)
    
    context = ContextBuilder.build_context(
        profile=None,
        all_claims=[claim1, claim2],
        all_evidence=[],
        all_conflicts=[],
        metadata={},
        context_filter=FounderContextFilter(),
        min_confidence=0.7
    )
    
    assert len(context.claims) == 1
    assert context.claims[0].confidence_score == 0.8


def test_context_builder_freshness_sorting() -> None:
    now = datetime.utcnow()
    # claim_old has higher confidence but older timestamp
    claim_old = create_mock_claim("founder_names", "Alice", 0.9, created_at=now - timedelta(days=10))
    # claim_new has lower confidence but newer timestamp
    claim_new = create_mock_claim("commitment_level", "Full-time", 0.8, created_at=now)
    
    context = ContextBuilder.build_context(
        profile=None,
        all_claims=[claim_old, claim_new],
        all_evidence=[],
        all_conflicts=[],
        metadata={},
        context_filter=FounderContextFilter(),
        sort_by="freshness"
    )
    
    # Sorting by freshness should put the newer claim first
    assert len(context.claims) == 2
    assert context.claims[0].value_string == "Full-time"
    assert context.claims[1].value_string == "Alice"


def test_context_builder_truncation() -> None:
    # 3 founder claims, each estimated to consume ~10-15 tokens
    claim1 = create_mock_claim("founder_names", "Alice & Bob", 0.9)
    claim2 = create_mock_claim("commitment_level", "Full-time", 0.8)
    claim3 = create_mock_claim("leadership_experience", "Ten years of executive experience", 0.7)
    
    # Set a tiny budget of 15 tokens
    context = ContextBuilder.build_context(
        profile=None,
        all_claims=[claim1, claim2, claim3],
        all_evidence=[],
        all_conflicts=[],
        metadata={},
        context_filter=FounderContextFilter(),
        max_token_budget=15
    )
    
    # Due to truncation, only the highest confidence claim (which is claim1) should fit
    assert len(context.claims) == 1
    assert context.claims[0].value_string == "Alice & Bob"


def test_context_builder_missing_information() -> None:
    # Required fields for Founder: founder_names, leadership_experience, domain_expertise, commitment_level
    # We only pass founder_names claim
    claim = create_mock_claim("founder_names", "Alice", 0.9)
    
    context = ContextBuilder.build_context(
        profile=None,
        all_claims=[claim],
        all_evidence=[],
        all_conflicts=[],
        metadata={},
        context_filter=FounderContextFilter()
    )
    
    # Gaps should list the remaining 3 required fields
    assert len(context.missing_information) == 3
    assert "leadership_experience" in context.missing_information
    assert "domain_expertise" in context.missing_information
    assert "commitment_level" in context.missing_information


def test_context_builder_large_profile() -> None:
    # Generate 500+ claims to test scalability
    claims = []
    # 250 duplicate claims for founder_names, 250 for commitment_level
    for i in range(250):
        # Varying confidence scores
        claims.append(create_mock_claim("founder_names", f"Founder {i}", 0.1 + (i * 0.003)))
        claims.append(create_mock_claim("commitment_level", f"Level {i}", 0.1 + (i * 0.003)))
        
    context = ContextBuilder.build_context(
        profile=None,
        all_claims=claims,
        all_evidence=[],
        all_conflicts=[],
        metadata={},
        context_filter=FounderContextFilter()
    )
    
    # Deduplication should reduce the 500 claims down to exactly 2 (one per field key)
    assert len(context.claims) == 2
    # They should hold the highest confidence values (index 249)
    assert context.confidence_summary["max_confidence"] == pytest.approx(0.1 + (249 * 0.003))
