from typing import Dict, Any, List
from pydantic import BaseModel, Field
from app.modules.ai.agents.models import AgentAssessment, Evidence

class AggregatedAssessment(BaseModel):
    overall_score: float = Field(..., description="Overall average evaluation score across experts")
    confidence: float = Field(..., description="Overall average confidence level across experts")
    summary: str = Field(..., description="Aggregated narrative summary of the startup evaluation")
    founder_assessment: AgentAssessment = Field(..., description="Preserved Founder Expert assessment block")
    product_assessment: AgentAssessment = Field(..., description="Preserved Product Expert assessment block")
    market_assessment: AgentAssessment = Field(..., description="Preserved Market Expert assessment block")
    merged_evidence: List[Evidence] = Field(default_factory=list, description="Unique, deduplicated evidence citations list")
    open_questions: List[str] = Field(default_factory=list, description="Unique, deduplicated list of validation questions")

class AssessmentAggregator:
    @staticmethod
    def aggregate(outputs: Dict[str, Any]) -> AggregatedAssessment:
        """Combines expert agent outputs into a single, unified structured assessment."""
        def get_assessment(name: str) -> AgentAssessment:
            val = outputs.get(name)
            if isinstance(val, AgentAssessment):
                return val
            if isinstance(val, dict):
                return AgentAssessment(**val)
                
            # Default fallback for missing expert output
            from app.modules.ai.agents.models import ExecutionMetadata
            from datetime import datetime, timezone
            meta = ExecutionMetadata(
                model="unknown",
                provider="mock",
                latency_ms=0.0,
                retries=0,
                token_count=0,
                prompt_version="1.0.0",
                timestamp=datetime.now(timezone.utc).isoformat(),
                execution_status="missing"
            )
            return AgentAssessment(
                domain=name.replace("Expert", "").lower(),
                overall_score=0.0,
                confidence=0.0,
                summary=f"Missing assessment for {name}.",
                execution_metadata=meta
            )

        founder = get_assessment("FounderExpert")
        product = get_assessment("ProductExpert")
        market = get_assessment("MarketExpert")

        scores = [founder.overall_score, product.overall_score, market.overall_score]
        confidences = [founder.confidence, product.confidence, market.confidence]

        overall_score = sum(scores) / len(scores) if scores else 0.0
        confidence = sum(confidences) / len(confidences) if confidences else 0.0

        summary = (
            f"Unified Assessment:\n"
            f"- Founder: {founder.summary}\n"
            f"- Product: {product.summary}\n"
            f"- Market: {market.summary}"
        )

        # Merge evidence without duplication
        evidence_map = {}
        for asm in [founder, product, market]:
            for ev in asm.supporting_evidence:
                evidence_map[ev.evidence_id] = ev
        merged_evidence = list(evidence_map.values())

        # Merge open questions without duplication
        questions = []
        seen_questions = set()
        for asm in [founder, product, market]:
            for q in asm.open_questions:
                if q not in seen_questions:
                    seen_questions.add(q)
                    questions.append(q)

        return AggregatedAssessment(
            overall_score=overall_score,
            confidence=confidence,
            summary=summary,
            founder_assessment=founder,
            product_assessment=product,
            market_assessment=market,
            merged_evidence=merged_evidence,
            open_questions=questions
        )
