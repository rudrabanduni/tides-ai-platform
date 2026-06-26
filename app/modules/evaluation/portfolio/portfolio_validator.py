from typing import List, Optional
from app.modules.evaluation.graph.graph_models import ObservationGraph
from app.modules.evaluation.portfolio.portfolio_models import Portfolio


class PortfolioValidator:
    """Validator class for verifying TIDES Portfolio and startup ranking reports."""

    @staticmethod
    def validate(portfolio: Portfolio, graphs: Optional[List[ObservationGraph]] = None) -> List[str]:
        """Runs the validation suite on a Portfolio report and checks referential integrity if graphs are provided."""
        errors = []
        entries = portfolio.entries
        stats = portfolio.statistics
        N = len(entries)

        # 1. No duplicate ranks & Ranks consecutive
        ranks = [e.rank for e in entries]
        if len(ranks) != len(set(ranks)):
            errors.append("Duplicate ranks detected in portfolio rankings.")
            
        expected_ranks = list(range(1, N + 1))
        if sorted(ranks) != expected_ranks:
            errors.append(f"Rank sequence is not continuous. Expected {expected_ranks}, got {sorted(ranks)}")

        # 2. Confidence values, evidence strength, and coverage range bounds
        for entry in entries:
            # overall_consensus: [0.0, 1.0]
            if not (0.0 <= entry.overall_consensus <= 1.0):
                errors.append(f"Consensus score for {entry.startup_id} is outside [0.0, 1.0]: {entry.overall_consensus}")
            # graph_confidence / confidence: [0.0, 1.0]
            if not (0.0 <= entry.graph_confidence <= 1.0):
                errors.append(f"Confidence score for {entry.startup_id} is outside [0.0, 1.0]: {entry.graph_confidence}")
            if not (0.0 <= entry.confidence <= 1.0):
                errors.append(f"Secondary confidence score for {entry.startup_id} is outside [0.0, 1.0]: {entry.confidence}")
            # evidence_strength: [0.0, 1.0]
            if not (0.0 <= entry.evidence_strength <= 1.0):
                errors.append(f"Evidence strength for {entry.startup_id} is outside [0.0, 1.0]: {entry.evidence_strength}")
            # document_coverage / coverage: [0.0, 1.0]
            if not (0.0 <= entry.document_coverage <= 1.0):
                errors.append(f"Document coverage for {entry.startup_id} is outside [0.0, 1.0]: {entry.document_coverage}")
            # investment_score: [0.0, 100.0]
            if not (0.0 <= entry.investment_score <= 100.0):
                errors.append(f"Investment score for {entry.startup_id} is outside [0.0, 100.0]: {entry.investment_score}")
            # percentile: [0.0, 100.0]
            if not (0.0 <= entry.percentile <= 100.0):
                errors.append(f"Percentile for {entry.startup_id} is outside [0.0, 100.0]: {entry.percentile}")
            if not entry.graph_hash:
                errors.append(f"Missing graph hash reference for startup {entry.startup_id}")

        # 3. Portfolio statistics validation
        if stats.portfolio_size != N:
            errors.append(f"Portfolio statistics size ({stats.portfolio_size}) does not match rankings count ({N})")
            
        if N > 0:
            scores = [e.investment_score for e in entries]
            avg_score = round(sum(scores) / N, 2)
            if abs(stats.average_score - avg_score) > 0.01:
                errors.append(f"Average score in stats ({stats.average_score}) does not match computed average ({avg_score})")

            highest = max(scores)
            lowest = min(scores)
            if abs(stats.highest_score - highest) > 0.01:
                errors.append(f"Highest score in stats ({stats.highest_score}) does not match computed max ({highest})")
            if abs(stats.lowest_score - lowest) > 0.01:
                errors.append(f"Lowest score in stats ({stats.lowest_score}) does not match computed min ({lowest})")

            # Median
            sorted_scores = sorted(scores)
            if N % 2 == 1:
                computed_median = sorted_scores[N // 2]
            else:
                computed_median = (sorted_scores[N // 2 - 1] + sorted_scores[N // 2]) / 2.0
            computed_median = round(computed_median, 2)
            if abs(stats.median_score - computed_median) > 0.01:
                errors.append(f"Median score in stats ({stats.median_score}) does not match computed median ({computed_median})")

            avg_conf = round(sum(e.confidence for e in entries) / N, 4)
            if abs(stats.average_confidence - avg_conf) > 0.0001:
                errors.append(f"Average confidence in stats ({stats.average_confidence}) does not match computed average ({avg_conf})")

            # Distributions sum check
            rec_sum = sum(stats.recommendation_distribution.values())
            if rec_sum != N:
                errors.append(f"Sum of recommendation counts ({rec_sum}) does not match portfolio size ({N})")
            cat_sum = sum(stats.category_distribution.values())
            if cat_sum != N:
                errors.append(f"Sum of category counts ({cat_sum}) does not match portfolio size ({N})")

        # 4. Indexes consistency
        # Category indexes check
        cat_count_sum = sum(len(ids) for ids in portfolio.category_indexes.values())
        if cat_count_sum != N:
            errors.append(f"Category index count sum ({cat_count_sum}) does not match entries size ({N})")
        # Ranking indexes check
        if len(portfolio.ranking_indexes) != N:
            errors.append(f"Ranking index size ({len(portfolio.ranking_indexes)}) does not match entries size ({N})")
        for r in range(1, N + 1):
            if r not in portfolio.ranking_indexes:
                errors.append(f"Rank {r} is missing from ranking_indexes")

        # 5. Portfolio Hash Validation
        from app.modules.evaluation.portfolio.portfolio_builder import PortfolioBuilder
        recomputed_hash = PortfolioBuilder._compute_portfolio_hash(portfolio)
        if portfolio.portfolio_hash != recomputed_hash:
            errors.append(f"Portfolio hash is invalid. Expected {recomputed_hash}, got {portfolio.portfolio_hash}")

        # 6. Referential Integrity (Graph, Assessment, and Executive references exist)
        if graphs is not None:
            # Map graphs by startup_id/graph_id
            graph_map = {g.startup_id or g.graph_id: g for g in graphs}
            for entry in entries:
                g = graph_map.get(entry.startup_id)
                if not g:
                    errors.append(f"Graph reference does not exist for startup ID: {entry.startup_id}")
                    continue
                # Verify graph hash matches
                if g.graph_hash != entry.graph_hash:
                    errors.append(f"Graph hash mismatch for {entry.startup_id}: expected {g.graph_hash}, got {entry.graph_hash}")
                # Verify Investment Assessment reference exists
                if not g.investment_assessment or g.investment_assessment.assessment_id != entry.investment_assessment_id:
                    errors.append(f"Investment Assessment reference does not exist or mismatch for startup {entry.startup_id}")
                # Verify Executive Assessment reference exists
                if not g.executive_assessment or g.executive_assessment.assessment_id != entry.executive_summary_id:
                    errors.append(f"Executive Assessment reference does not exist or mismatch for startup {entry.startup_id}")

        return errors
