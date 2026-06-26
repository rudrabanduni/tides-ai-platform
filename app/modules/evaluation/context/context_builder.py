from datetime import datetime
from typing import Any
from app.modules.evaluation.context.context_schemas import EvaluationContext
from app.modules.evaluation.context.context_filters import BaseContextFilter


class ContextBuilder:
    """Read-only engine that converts full Startup Intelligence Profiles into expert-specific EvaluationContexts."""

    @staticmethod
    def build_context(
        profile: Any,
        all_claims: list[Any],
        all_evidence: list[Any],
        all_conflicts: list[Any],
        metadata: dict[str, Any],
        context_filter: BaseContextFilter,
        max_token_budget: int = 4000,
        min_confidence: float = 0.0,
        sort_by: str = "confidence"  # Options: "confidence", "freshness", "relevance"
    ) -> EvaluationContext:
        """Processes claims, evidence, and conflicts, returning a sandboxed domain context."""
        # 1. Filter claims and conflicts using domain-specific filter
        filtered_claims = context_filter.filter_claims(all_claims)
        filtered_conflicts = context_filter.filter_conflicts(all_conflicts)

        # 2. Filter by minimum confidence score
        filtered_claims = [c for c in filtered_claims if c.confidence_score >= min_confidence]

        # 3. Deduplication
        # Keeps only the highest confidence claim for each field key. If equal, keeps the newer one.
        deduped = {}
        for claim in filtered_claims:
            fk = claim.field.field_key if (hasattr(claim, "field") and claim.field) else "unknown"
            if fk not in deduped:
                deduped[fk] = claim
            else:
                existing = deduped[fk]
                if claim.confidence_score > existing.confidence_score:
                    deduped[fk] = claim
                elif claim.confidence_score == existing.confidence_score:
                    created_new = getattr(claim, "created_at", None)
                    created_old = getattr(existing, "created_at", None)
                    if created_new and created_old and created_new > created_old:
                        deduped[fk] = claim
        filtered_claims = list(deduped.values())

        # 4. Sorting
        required_fields = context_filter.get_required_fields()

        def sort_key(c: Any) -> Any:
            if sort_by == "freshness":
                created = getattr(c, "created_at", None)
                ts = created.timestamp() if isinstance(created, datetime) else 0
                return (ts, c.confidence_score)
            elif sort_by == "relevance":
                fk = c.field.field_key if (hasattr(c, "field") and c.field) else ""
                is_req = 1 if fk in required_fields else 0
                return (is_req, c.confidence_score)
            else:  # Default to confidence
                return (c.confidence_score, getattr(c, "created_at", None))

        filtered_claims.sort(key=sort_key, reverse=True)

        # 5. Token-based Truncation
        # Approximate word count metric used to truncate lists within the token budget
        final_claims = []
        current_tokens = 0
        for claim in filtered_claims:
            val = str(claim.value_string or claim.value_number or claim.value_boolean or claim.value_json or "")
            reasoning = str(getattr(claim, "reasoning", "") or "")
            claim_text = f"{val} {reasoning}"
            claim_tokens = max(10, len(claim_text.split()))  # Simple word-count estimation

            if current_tokens + claim_tokens <= max_token_budget:
                final_claims.append(claim)
                current_tokens += claim_tokens
            else:
                break

        # 6. Evidence Preservation
        # Keep only evidence associated with the selected final claims
        final_claim_ids = {c.id for c in final_claims}
        final_evidence = [ev for ev in all_evidence if ev.claim_id in final_claim_ids]

        # 7. Identify Missing Required Information
        present_fields = {c.field.field_key for c in final_claims if hasattr(c, "field") and c.field}
        missing_info = [f for f in required_fields if f not in present_fields]

        # 8. Source Counts
        source_counts = {}
        for ev in final_evidence:
            doc_type = "unknown"
            if hasattr(ev, "source_document") and ev.source_document:
                if hasattr(ev.source_document, "document_type"):
                    doc_type = ev.source_document.document_type.value if hasattr(ev.source_document.document_type, "value") else str(ev.source_document.document_type)
            elif hasattr(ev, "document_type") and ev.document_type:
                doc_type = str(ev.document_type)
            source_counts[doc_type] = source_counts.get(doc_type, 0) + 1

        # 9. Confidence Summary
        if final_claims:
            scores = [c.confidence_score for c in final_claims]
            conf_summary = {
                "min_confidence": min(scores),
                "max_confidence": max(scores),
                "average_confidence": sum(scores) / len(scores)
            }
        else:
            conf_summary = {
                "min_confidence": 0.0,
                "max_confidence": 0.0,
                "average_confidence": 0.0
            }

        # 10. Context Statistics
        context_stats = {
            "claims_count": len(final_claims),
            "evidence_count": len(final_evidence),
            "conflicts_count": len(filtered_conflicts),
            "estimated_tokens": current_tokens
        }

        return EvaluationContext(
            claims=final_claims,
            evidence=final_evidence,
            metadata=metadata,
            conflicts=filtered_conflicts,
            missing_information=missing_info,
            context_statistics=context_stats,
            source_counts=source_counts,
            confidence_summary=conf_summary
        )
