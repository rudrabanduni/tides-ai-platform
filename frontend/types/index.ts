export type VerificationStatus =
  | 'VERIFIED_DOCUMENTED'
  | 'SELF_REPORTED_ONLY'
  | 'PLAUSIBLE_ESTIMATE'
  | 'CONTRADICTED'
  | 'UNSUPPORTED_ASSUMPTION'
  | 'MISSING_INFORMATION'
  | 'NOT_APPLICABLE';

export interface CriterionAssessment {
  criterion_id: string;
  criterion_name: string;
  extracted_startup_response?: string;
  assessment_narrative: string;
  evidence_ids?: string[];
  source_locations?: string[];
  verification_status: VerificationStatus | string;
  strengths?: string[];
  weaknesses?: string[];
  risks?: string[];
  contradictions?: string[];
  confidence_score?: number;
  confidence_limitations?: string;
  score?: number;
}

export interface DomainAssessmentReport {
  domain: string;
  domain_key: string;
  domain_title: string;
  evaluation_id?: string;
  startup_id?: string;
  criteria_evaluated?: string[];
  criteria_evaluations: Record<string, CriterionAssessment>;
  summary: string;
  executive_summary?: string;
  executive_conclusion?: string;
  reasoning?: string;
  investment_implication?: string;
  strengths?: string[];
  weaknesses?: string[];
  unsupported_claims?: string[];
  contradictions?: string[];
  missing_evidence?: any[];
  missing_information?: string[];
  follow_up_questions?: string[];
  composite_domain_confidence: number;
  confidence_limitations?: string;
  cost_usd?: number;
  model_used?: string;
  generated_at?: string;
}

export interface CrossDomainContradiction {
  contradiction_id: string;
  domain_a: string;
  criterion_a: string;
  claim_a_summary: string;
  domain_b: string;
  criterion_b: string;
  claim_b_summary: string;
  nature_of_conflict: string;
  resolution_status: 'RESOLVED' | 'PRESERVED_DISAGREEMENT' | 'UNRESOLVED' | string;
  resolution_rationale?: string;
}

export interface TargetedRecheckResult {
  recheck_id: string;
  domain_key: string;
  criterion_id: string;
  original_verification_status: string;
  updated_verification_status: string;
  original_finding_summary: string;
  updated_finding_summary: string;
  recheck_reasoning: string;
  evidence_confirmed: boolean;
  unresolved_disagreement: boolean;
  cost_usd?: number;
  rechecked_at?: string;
}

export interface RecommendedTranche {
  tranche_name?: string;
  milestone?: string;
  amount?: number;
  currency?: string;
  conditions?: string[];
  [key: string]: any;
}

export interface FinalReviewAssessment {
  report_id: string;
  evaluation_id: string;
  startup_id: string;
  startup_name: string;
  sector: string;
  stage: string;
  executive_summary: string;
  recommendation_rationale: string;
  overall_recommendation: 'INCUBATE' | 'DEFER' | 'REJECT' | 'CONDITIONAL' | string;
  incubation_conditions?: string[];
  recommended_tranches?: RecommendedTranche[];
  domain_reports?: Record<string, DomainAssessmentReport>;
  cross_domain_findings?: string[];
  identified_contradictions?: CrossDomainContradiction[];
  material_unsupported_claims?: string[];
  composite_risk_matrix?: any[];
  unresolved_questions?: string[];
  rechecks_triggered?: TargetedRecheckResult[];
  unresolved_disagreements?: string[];
  investment_score?: number;
  confidence_score?: number;
  cost_summary?: Record<string, any>;
  reviewer_agent_version?: string;
  generated_at?: string;
}

export interface Appendix {
  appendix_id: string;
  title: string;
  content: string;
}

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
  current_status?: string;
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
  section_id?: string;
  supporting_nodes?: string[];
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

  // Canonical Phase 2/3 additions
  final_review?: FinalReviewAssessment;
  domain_reports?: Record<string, DomainAssessmentReport>;
  metadata?: Record<string, any>;
  appendices?: Appendix[];

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

export interface EvaluationGraph {
  startup_id?: string;
  startup_name?: string;
  executive_assessment?: {
    summary: string;
    confidence: number;
    overall_score: number;
    recommendation: string;
  };
  investment_assessment?: {
    recommendation: string;
    investment_score: number;
    confidence: number;
  };
  supervisory_review?: FinalReviewAssessment;
  final_review?: FinalReviewAssessment;
  domain_reports?: Record<string, DomainAssessmentReport>;
  domain_assessments?: Record<string, any>;
  report?: Report;
  observations?: Record<string, any>;
  risks?: Record<string, any>;
  questions?: Record<string, any>;
  cost_observability?: Record<string, any>;
  founder_assessment?: any;
  product_assessment?: any;
  market_assessment?: any;
  trl_assessment?: any;
  ip_assessment?: any;
  financial_assessment?: any;
}

export interface PortfolioEntry {
  startup_id: string;
  startup_name: string;
  overall_score?: number;
  investment_score?: number;
  rank?: number;
  category?: string;
  sector?: string;
  stage: string;
  recommendation: string;
  evidence_strength?: number;
  graph_confidence?: number | null;
  active_risk_count?: number;
}

export interface Portfolio {
  entries: PortfolioEntry[];
  statistics?: {
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
