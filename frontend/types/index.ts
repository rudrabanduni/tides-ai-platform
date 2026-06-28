export interface Startup {
  id: string;
  startup_name: string;
  sector: string;
  stage: string;
  problem_statement?: string;
  solution_summary?: string;
  target_market?: string;
  business_model?: string;
  traction_summary?: string;
  funding_status?: string;
  created_at: string;
  updated_at: string;
  status?: string;
}

export interface DashboardStats {
  total_startups: number;
  recommended: number;
  review: number;
  rejected: number;
  approved_startups: number;
  pending_committee_review: number;
  ai_recommended: number;
  final_rejected: number;
}

export interface ReportSection {
  title: string;
  content: string;
  confidence: number;
}

export interface Report {
  report_id: string;
  generated_at: string;
  graph_version: string;

  // Primary 11-section structure
  executive_summary: ReportSection;
  investment_recommendation: ReportSection;
  founder_assessment: ReportSection;
  product_technology: ReportSection;
  market_opportunity: ReportSection;
  business_model: ReportSection;
  competition: ReportSection;
  financial_overview: ReportSection;
  risks: ReportSection;
  investment_thesis: ReportSection;
  follow_up_questions: ReportSection;

  // Legacy / compatibility fields
  investment_summary?: ReportSection;
  founder_analysis?: ReportSection;
  product_analysis?: ReportSection;
  trl_analysis?: ReportSection;
  market_analysis?: ReportSection;
  competition_analysis?: ReportSection;
  financial_analysis?: ReportSection;
  ip_analysis?: ReportSection;
  risk_analysis?: ReportSection;
  observations?: ReportSection;
  conflicts?: ReportSection;
  resolutions?: ReportSection;
  missing_information?: ReportSection;
}

export interface PortfolioEntry {
  startup_id: string;
  startup_name: string;
  overall_score: number;
  rank: number;
  category: string;
  stage: string;
  recommendation: string;
  evidence_strength: number;
  graph_confidence: number;
  active_risk_count: number;
}

export interface Portfolio {
  entries: PortfolioEntry[];
  statistics: {
    total_startups: number;
    average_score: number;
    highest_score: number;
    lowest_score: number;
  };
}

export interface CommitteeDecision {
  decision_id: string;
  startup_id: string;
  startup_name: string;
  portfolio_rank: number;
  recommendation: string;
  decision_confidence: number;
  decision_reasoning: string;
  investment_priority: string;
  incubation_priority: string;
  grant_priority: string;
  pilot_priority: string;
  review_window: string;
  committee_notes: string;
  blocking_risks: string[];
}
