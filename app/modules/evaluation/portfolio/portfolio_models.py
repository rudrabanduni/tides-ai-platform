from typing import List, Dict, Any
from pydantic import BaseModel, Field


class PortfolioEntry(BaseModel):
    startup_id: str
    startup_name: str
    category: str
    rank: int
    ranking_reason: str
    investment_assessment_id: str
    executive_summary_id: str
    overall_consensus: float
    graph_confidence: float
    evidence_strength: float
    document_coverage: float
    active_risk_count: int
    corroborated_observation_count: int
    disputed_observation_count: int
    created_at: str
    
    # Combined/Extended fields for full compatibility across different specs
    investment_score: float
    recommendation: str
    confidence: float
    percentile: float
    strengths: List[str] = Field(default_factory=list)
    risks: List[str] = Field(default_factory=list)
    executive_summary: str
    graph_hash: str


class PortfolioStatistics(BaseModel):
    portfolio_size: int
    average_score: float
    median_score: float
    highest_score: float
    lowest_score: float
    recommendation_distribution: Dict[str, int] = Field(default_factory=dict)
    category_distribution: Dict[str, int] = Field(default_factory=dict)
    average_confidence: float


class Portfolio(BaseModel):
    portfolio_id: str
    portfolio_version: str = "1.0.0"
    engine_version: str = "1.0.0"
    generated_at: str
    generation_duration_ms: float
    graph_hashes_used: List[str] = Field(default_factory=list)
    portfolio_hash: str
    entries: List[PortfolioEntry] = Field(default_factory=list)
    category_indexes: Dict[str, List[str]] = Field(default_factory=dict)
    ranking_indexes: Dict[int, str] = Field(default_factory=dict)
    statistics: PortfolioStatistics

# Create alias
PortfolioReport = Portfolio
