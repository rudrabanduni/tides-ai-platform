import time
import uuid
import re
from datetime import datetime
from typing import List, Dict, Any

from app.modules.evaluation.graph.graph_models import ObservationGraph, NodeType
from app.modules.evaluation.graph.graph_builder import ObservationGraphBuilder
from app.modules.evaluation.portfolio.portfolio_models import (
    Portfolio, PortfolioEntry, PortfolioStatistics
)


class PortfolioBuilder:
    """Builder class for assembling, ranking, and hashing startup portfolios."""

    @staticmethod
    def build(graphs: List[ObservationGraph]) -> Portfolio:
        """Assembles, deduplicates, and ranks startups from their ObservationGraphs into a Portfolio."""
        t_start = time.perf_counter()
        
        # 1. Group graphs by startup_id (or graph_id if startup_id not set) to remove duplicates
        startup_groups = {}
        for g in graphs:
            sid = g.startup_id or g.graph_id
            startup_groups.setdefault(sid, []).append(g)
            
        # For each startup, keep the "best" graph based on deterministic ranking criteria
        unique_graphs = []
        for sid, group in startup_groups.items():
            if len(group) == 1:
                unique_graphs.append(group[0])
            else:
                # Sort group descending (best first) using a sorting key helper
                sorted_group = sorted(
                    group,
                    key=lambda g: PortfolioBuilder._make_sorting_key_for_graph(g),
                    reverse=True
                )
                unique_graphs.append(sorted_group[0])
                
        # 2. Build preliminary entry list without ranks and percentiles first
        entries = []
        for g in unique_graphs:
            entry = PortfolioBuilder._build_entry_from_graph(g)
            entries.append(entry)
            
        # 3. Sort entries deterministically
        # Primary: Investment Score (descending)
        # Tie-breakers: overall_consensus (descending), graph_confidence (descending), evidence_strength (descending), startup_name (ascending), startup_id (ascending)
        # Note: Since sorted is stable, we can sort ascending by a tuple key where descending fields are negated
        entries.sort(key=lambda e: (
            -e.investment_score,
            -e.overall_consensus,
            -e.graph_confidence,
            -e.evidence_strength,
            e.startup_name,
            e.startup_id
        ))

        # 4. Assign ranks, percentiles, and generate ranking reasons
        N = len(entries)
        for idx, entry in enumerate(entries):
            rank = idx + 1
            entry.rank = rank
            
            # Percentile: 100.0 for rank 1, 0.0 for rank N, scaled in between
            if N <= 1:
                entry.percentile = 100.0
            else:
                entry.percentile = round(((N - rank) / (N - 1)) * 100.0, 2)
                
            # Generate deterministic ranking reason
            entry.ranking_reason = PortfolioBuilder._generate_ranking_reason(entry, N)
            
        # 5. Populate Portfolio Statistics
        stats = PortfolioBuilder._compute_statistics(entries)
        
        # 6. Build category indexes and ranking indexes
        category_indexes = {}
        ranking_indexes = {}
        for entry in entries:
            category_indexes.setdefault(entry.category, []).append(entry.startup_id)
            ranking_indexes[entry.rank] = entry.startup_id

        # 7. Create Portfolio object
        portfolio_id = f"PORT-{str(uuid.uuid4())[:8]}"
        generated_at = datetime.utcnow().isoformat() + "Z"
        
        graph_hashes_used = [entry.graph_hash for entry in entries]
        
        port = Portfolio(
            portfolio_id=portfolio_id,
            portfolio_version="1.0.0",
            engine_version="1.0.0",
            generated_at=generated_at,
            generation_duration_ms=0.0,  # updated below
            graph_hashes_used=graph_hashes_used,
            portfolio_hash="",  # updated below
            entries=entries,
            category_indexes=category_indexes,
            ranking_indexes=ranking_indexes,
            statistics=stats
        )
        
        # Compute portfolio hash
        port.portfolio_hash = PortfolioBuilder._compute_portfolio_hash(port)
        
        # 8. Propagate entry & statistics back to the corresponding ObservationGraphs
        # and re-compute their hashes
        unique_graph_map = {g.startup_id or g.graph_id: g for g in unique_graphs}
        for entry in entries:
            graph_to_update = unique_graph_map.get(entry.startup_id)
            if graph_to_update:
                graph_to_update.portfolio_entry = entry
                graph_to_update.portfolio_statistics = stats
                # Re-compute hash (which will include portfolio_entry & portfolio_statistics)
                graph_to_update.graph_hash = ObservationGraphBuilder._compute_hash(graph_to_update)
                # Update entry's graph_hash to the final hash so they match!
                entry.graph_hash = graph_to_update.graph_hash
                
        # Measure duration
        t_end = time.perf_counter()
        port.generation_duration_ms = (t_end - t_start) * 1000.0
        
        # Re-compute portfolio hash using the updated entries list (which now has final hashes)
        # Wait, if we compute portfolio hash after step 8, it will include final hashes.
        # But wait! If we do it, does the final hash change?
        # Since the graph hash excludes portfolio_entry.graph_hash from its hash calculation,
        # changing entry.graph_hash does NOT change the graph hash!
        # So we can safely update entry.graph_hash first, and then compute the final portfolio_hash!
        # Let's re-compute portfolio_hash now to ensure the portfolio hash uses the propagated final hashes.
        port.portfolio_hash = PortfolioBuilder._compute_portfolio_hash(port)
        
        return port

    @staticmethod
    def _make_sorting_key_for_graph(graph: ObservationGraph) -> tuple:
        """Helper to compare graphs of same startup for deduplication, choosing the better one."""
        inv = graph.investment_assessment
        score = inv.investment_score if inv else 0.0
        overall_consensus = graph.investment_statistics.get("overall_consensus", 0.0) if graph.investment_statistics else 0.0
        confidence = inv.confidence if inv else 0.0
        evidence_strength = inv.metadata.get("metrics", {}).get("evidence_strength", 0.0) if inv and inv.metadata else 0.0
        return (score, overall_consensus, confidence, evidence_strength)

    @staticmethod
    def _build_entry_from_graph(graph: ObservationGraph) -> PortfolioEntry:
        """Extracts and populates fields for a PortfolioEntry from an ObservationGraph."""
        # Temporarily detach portfolio fields to compute clean graph hash
        orig_entry = graph.portfolio_entry
        orig_stats = graph.portfolio_statistics
        graph.portfolio_entry = None
        graph.portfolio_statistics = None
        
        clean_hash = ObservationGraphBuilder._compute_hash(graph)
        
        # Restore
        graph.portfolio_entry = orig_entry
        graph.portfolio_statistics = orig_stats

        inv = graph.investment_assessment
        exec_asm = graph.executive_assessment
        
        # Safe extractions
        score = inv.investment_score if inv else 50.0
        rec = inv.recommendation.value if inv else "REVIEW"
        confidence = inv.confidence if inv else 0.5
        inv_id = inv.assessment_id if inv else "N/A"
        exec_id = exec_asm.assessment_id if exec_asm else "N/A"
        
        # Statistics/Metrics calculations
        metrics = inv.metadata.get("metrics", {}) if inv and inv.metadata else {}
        overall_consensus = metrics.get("overall_consensus", 0.0)
        evidence_strength = metrics.get("evidence_strength", 0.0)
        doc_coverage = metrics.get("document_coverage", 0.0)
        
        # If metrics were empty, compute manually
        total_obs = len(graph.observations)
        corroborated_count = sum(1 for o in graph.observations.values() if o.consensus_status == "corroborated")
        if total_obs > 0 and overall_consensus == 0.0:
            overall_consensus = corroborated_count / total_obs
            
        if len(graph.evidence) > 0 and evidence_strength == 0.0:
            evidence_strength = sum(ev.confidence for ev in graph.evidence.values()) / len(graph.evidence)
            
        if total_obs > 0 and doc_coverage == 0.0:
            total_docs = len(graph.documents)
            covered_docs = set()
            for edge in graph.edges:
                if edge.target_type == NodeType.DOCUMENT and edge.relationship == "DERIVED_FROM":
                    covered_docs.add(edge.target_id)
            doc_coverage = len(covered_docs) / total_docs if total_docs > 0 else 1.0

        # Disputed observations
        unresolved_claims = set()
        for conflict_id, conflict in graph.conflicts.items():
            if conflict_id not in graph.resolutions_by_conflict:
                for edge in graph.out_edges.get(conflict_id, []):
                    if edge.target_type == NodeType.CLAIM:
                        unresolved_claims.add(edge.target_id)
                        
        disputed_count = 0
        for obs in graph.observations.values():
            if obs.consensus_status == "disputed":
                disputed_count += 1
            else:
                obs_claims = {edge.target_id for edge in graph.out_edges.get(obs.observation_id, []) if edge.target_type == NodeType.CLAIM}
                if obs_claims & unresolved_claims:
                    disputed_count += 1
                    
        # Active risk count
        active_risks_count = graph.investment_statistics.get("active_risks_count") if graph.investment_statistics else len(graph.risks)
        if active_risks_count is None:
            active_risks_count = len(graph.risks)
            
        strengths = inv.strengths if inv else []
        risks = inv.weaknesses if inv else []
        exec_summary = inv.executive_summary if inv else ""
        
        return PortfolioEntry(
            startup_id=graph.startup_id or graph.graph_id,
            startup_name=graph.startup_name or f"Startup-{graph.graph_id[:8]}",
            category=graph.category or "Unknown",
            rank=0,  # to be set by sorting
            ranking_reason="",  # to be set by ranking reason generator
            investment_assessment_id=inv_id,
            executive_summary_id=exec_id,
            overall_consensus=round(overall_consensus, 4),
            graph_confidence=round(confidence, 4),
            evidence_strength=round(evidence_strength, 4),
            document_coverage=round(doc_coverage, 4),
            active_risk_count=active_risks_count,
            corroborated_observation_count=corroborated_count,
            disputed_observation_count=disputed_count,
            created_at=graph.created_at if isinstance(graph.created_at, str) else graph.created_at.isoformat() + "Z",
            investment_score=round(score, 2),
            recommendation=rec,
            confidence=round(confidence, 4),
            percentile=0.0,  # to be set
            strengths=list(strengths),
            risks=list(risks),
            executive_summary=exec_summary,
            graph_hash=clean_hash  # initialize with clean hash for portfolio hashing
        )

    @staticmethod
    def _generate_ranking_reason(entry: PortfolioEntry, portfolio_size: int) -> str:
        """Generates a concise, deterministic ranking explanation."""
        # Focus on key differentiators based on the rank
        if entry.rank == 1:
            return "Top performer with excellent investment score, strong consensus, and minimal risk profile."
        elif entry.rank <= max(2, portfolio_size // 10) and entry.investment_score >= 70.0:
            return "Tier-1 candidate with high confidence, strong evidence strength, and low active risk."
        elif entry.active_risk_count >= 3:
            return f"Rank limited by {entry.active_risk_count} active risks despite moderate consensus."
        elif entry.evidence_strength < 0.6:
            return "Rank impacted by lower evidence strength and limited document coverage."
        else:
            return "Satisfactory investment score backed by stable overall consensus and moderate risk."

    @staticmethod
    def _compute_statistics(entries: List[PortfolioEntry]) -> PortfolioStatistics:
        """Computes summary statistics across all portfolio entries."""
        portfolio_size = len(entries)
        if portfolio_size == 0:
            return PortfolioStatistics(
                portfolio_size=0,
                average_score=0.0,
                median_score=0.0,
                highest_score=0.0,
                lowest_score=0.0,
                recommendation_distribution={},
                category_distribution={},
                average_confidence=0.0
            )
            
        scores = [e.investment_score for e in entries]
        avg_score = round(sum(scores) / portfolio_size, 2)
        highest = max(scores)
        lowest = min(scores)
        
        # Median calculation
        sorted_scores = sorted(scores)
        if portfolio_size % 2 == 1:
            median = sorted_scores[portfolio_size // 2]
        else:
            median = (sorted_scores[portfolio_size // 2 - 1] + sorted_scores[portfolio_size // 2]) / 2.0
        median = round(median, 2)
        
        # Average confidence
        avg_conf = round(sum(e.confidence for e in entries) / portfolio_size, 4)
        
        # Distributions
        rec_dist = {}
        cat_dist = {}
        for e in entries:
            rec_dist[e.recommendation] = rec_dist.get(e.recommendation, 0) + 1
            cat_dist[e.category] = cat_dist.get(e.category, 0) + 1
            
        return PortfolioStatistics(
            portfolio_size=portfolio_size,
            average_score=avg_score,
            median_score=median,
            highest_score=highest,
            lowest_score=lowest,
            recommendation_distribution=rec_dist,
            category_distribution=cat_dist,
            average_confidence=avg_conf
        )

    @staticmethod
    def _compute_portfolio_hash(portfolio: Portfolio) -> str:
        """SHA-256 hash of portfolio metadata, entries, rankings, and underlying graph hashes."""
        import json
        import hashlib
        
        hash_list = [
            portfolio.portfolio_version,
            portfolio.engine_version,
            json.dumps([e.startup_id for e in portfolio.entries]),
            json.dumps({e.startup_id: e.rank for e in portfolio.entries}),
            json.dumps(portfolio.graph_hashes_used),
            json.dumps([e.investment_assessment_id for e in portfolio.entries])
        ]
        
        hasher = hashlib.sha256()
        for item in hash_list:
            hasher.update(item.encode("utf-8"))
        return hasher.hexdigest()
