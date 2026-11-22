import { apiClient } from '@/lib/api-client';

export type EvidenceClass =
  | 'APPLICANT_REPORTED'
  | 'DOCUMENTARY_EVIDENCE'
  | 'INDEPENDENTLY_VERIFIED'
  | 'NOT_VERIFIED'
  | 'MISSING'
  | 'NOT_APPLICABLE';

export interface FounderInput {
  name: string;
  role_in_startup?: string;
  email?: string;
  phone?: string;
  education?: string;
  experience_summary?: string;
  linkedin_url?: string;
}

export interface ApplicationPayload {
  company_name: string;
  sector: string;
  industry?: string;
  stage: string;
  location?: string;
  website?: string;
  contact_name: string;
  contact_email: string;
  contact_phone?: string;
  founders: FounderInput[];
  problem_statement: string;
  proposed_solution: string;
  product_technology?: string;
  target_market: string;
  business_model: string;
  traction?: string;
  revenue_information?: string;
  financial_information?: string;
  funding_requirement?: string;
  incubation_support_requirement?: string;
  declarations: {
    information_accurate: boolean;
    consent_to_evaluation: boolean;
    documents_owned_or_authorised: boolean;
    synthetic_demo_data: boolean;
  };
}

export interface DocumentSummary {
  id: string;
  document_type: string;
  original_filename: string;
  content_type: string | null;
  file_size: number;
  processing_status: string;
  created_at: string;
}

export interface RunStage {
  key: string;
  label: string;
  group: string;
  status: 'PENDING' | 'RUNNING' | 'SUCCESS' | 'FAILED' | 'BLOCKED' | 'SKIPPED' | 'EXHAUSTED' | string;
  started_at?: string;
  finished_at?: string;
  detail?: Record<string, any>;
}

export interface EvaluationRun {
  id: string;
  startup_id: string;
  application_id: string | null;
  status: 'QUEUED' | 'RUNNING' | 'COMPLETED' | 'BLOCKED' | 'FAILED';
  mode: 'MOCK_DEMONSTRATION' | 'LIVE_PROVIDER';
  current_stage: string | null;
  progress_pct: number;
  stages: RunStage[];
  pipeline_status: string | null;
  error_message: string | null;
  report_id: string | null;
  summary: Record<string, any>;
  cost_usd: number;
  created_at: string;
  started_at: string | null;
  finished_at: string | null;
  disclosure: string | null;
}

export interface Application {
  id: string;
  application_ref: string;
  startup_id: string;
  company_name: string;
  sector: string | null;
  industry: string | null;
  stage: string | null;
  location: string | null;
  website: string | null;
  status: string;
  contact_name: string | null;
  contact_email: string | null;
  contact_phone: string | null;
  problem_statement: string | null;
  proposed_solution: string | null;
  product_technology: string | null;
  target_market: string | null;
  business_model: string | null;
  traction: string | null;
  revenue_information: string | null;
  financial_information: string | null;
  funding_requirement: string | null;
  incubation_support_requirement: string | null;
  declarations: Record<string, boolean>;
  is_synthetic: boolean;
  submitted_at: string | null;
  created_at: string;
  founders: (FounderInput & { id: string })[];
  documents: DocumentSummary[];
  latest_run: EvaluationRun | null;
}

export interface ApplicationListItem {
  id: string;
  application_ref: string;
  startup_id: string;
  company_name: string;
  sector: string | null;
  stage: string | null;
  status: string;
  is_synthetic: boolean;
  document_count: number;
  created_at: string;
  latest_run_status: string | null;
  latest_run_id: string | null;
}

export interface CriterionResult {
  criterion_id: string;
  criterion_name: string;
  score: number | null;
  verification_status: string;
  evidence_class: EvidenceClass;
  evidence_class_label: string;
  evidence_ids: string[];
  rationale?: string | null;
  missing_information?: string | null;
  applicant_response?: string | null;
  source_locations?: string[];
  value?: string | null;
  source?: string | null;
}

export interface DomainResult {
  key: string;
  title: string;
  status: string;
  criteria_total: number;
  criteria_assessed: number;
  average_score?: number | null;
  confidence?: number | null;
  summary?: string;
  executive_conclusion?: string;
  strengths?: string[];
  weaknesses?: string[];
  contradictions?: string[];
  missing_information?: string[];
  risks?: { id: string; category?: string; severity?: string; description?: string; mitigation?: string }[];
  questions?: string[];
  criteria: CriterionResult[];
}

export interface CitedItem {
  text: string;
  domain: string;
  criterion_id: string;
  evidence_ids: string[];
}

export interface RunResults {
  available: boolean;
  evaluation_id: string;
  startup_id?: string;
  startup_name?: string;
  status: string;
  mode?: string;
  report_id?: string | null;
  disclosure: string | null;
  domains: DomainResult[];
  cover_criteria: CriterionResult[];
  coverage: {
    domain_criteria_expected: number;
    domain_criteria_present: number;
    cover_criteria_expected: number;
    cover_criteria_present: number;
    total_expected: number;
    total_present: number;
    missing: string[];
    duplicates: string[];
    unknown: string[];
    domains_completed: number;
    evidence_classes: Record<string, number>;
    complete: boolean;
  };
  supervisory: {
    status: string;
    overall_diligence_position?: string;
    committee_recommendation?: string;
    recommendation_rationale?: string;
    confidence?: number;
    major_strengths?: CitedItem[];
    material_weaknesses?: CitedItem[];
    contradictions?: { description?: string; domain?: string }[];
    missing_evidence?: CitedItem[];
    financial_and_technical_risks?: { description?: string; severity?: string; domain?: string }[];
    market_risks?: { description?: string; severity?: string; domain?: string }[];
    team_capability_observations?: CitedItem[];
    priority_diligence_questions?: string[];
    required_founder_clarifications?: string[];
    recommended_incubation_support?: CitedItem[];
    conditional_requirements?: string[];
    domains_cited?: string[];
  };
  validation: { valid: boolean; errors: string[]; warnings?: string[] };
  weighted_score?: WeightedScore;
  red_flags?: { id: string; rule: string; finding: string; action: string; criteria: string[] }[];
}

export interface WeightedScore {
  standard_version: string;
  standard_status: 'PROVISIONAL' | 'APPROVED' | string;
  standard_source?: string;
  missing_policy: string;
  overall_score_pct: number | null;
  overall_score_10: number | null;
  score_scale_max: number;
  approved_by?: string | null;
  effective_date?: string | null;
  decision_note?: string | null;
  missing_policy_note?: string | null;
  weight_coverage_pct: number;
  recommendation: string | null;
  recommendation_basis: string;
  sections: {
    key: string;
    title: string;
    weight_pct: number;
    score_pct: number | null;
    score_10: number | null;
    criteria_scored: number;
    criteria_not_scored: number;
    weighted_contribution: number | null;
  }[];
}

export interface EvidenceRecord {
  evidence_id: string;
  document: string | null;
  page_number: number | null;
  section_name: string | null;
  snippet: string | null;
  confidence: number | null;
  claim_field: string | null;
  claim_value: string | null;
}

export interface DashboardStats {
  total_applications: number;
  synthetic_applications: number;
  pending_applications: number;
  under_evaluation: number;
  completed_evaluations: number;
  blocked_or_failed_evaluations: number;
  pending_supervisory_reviews: number;
  sectors: Record<string, number>;
  stages: Record<string, number>;
  recent_activity: {
    type: string;
    startup_name: string | null;
    status: string;
    at: string;
    evaluation_id?: string;
    application_id?: string;
    application_ref?: string;
    mode?: string;
  }[];
}

export interface RuntimeMode {
  mode: 'MOCK_DEMONSTRATION' | 'LIVE_PROVIDER';
  disclosure: string | null;
  live_evaluations_enabled_in_ui: boolean;
  evaluation_budget_usd: number;
}

export const ALLOWED_UPLOAD_EXTENSIONS = ['pdf', 'pptx', 'ppt', 'docx', 'doc', 'xlsx', 'xls', 'csv', 'txt', 'md'];
export const MAX_UPLOAD_BYTES = 25 * 1024 * 1024;

export const DOCUMENT_TYPES: { value: string; label: string }[] = [
  { value: 'pitch_deck', label: 'Pitch deck' },
  { value: 'founder_resume', label: 'Founder CV' },
  { value: 'business_plan', label: 'Financial / business plan' },
  { value: 'company_document', label: 'Product or technical document' },
  { value: 'other', label: 'Supporting evidence' },
];

export function validateUploadFile(file: File): string | null {
  const ext = file.name.split('.').pop()?.toLowerCase() || '';
  if (!ALLOWED_UPLOAD_EXTENSIONS.includes(ext)) {
    return `Unsupported file type (.${ext || 'none'}). Allowed: PDF, PPTX, PPT, DOCX, DOC, XLSX, XLS, CSV, TXT, MD.`;
  }
  if (file.size === 0) return 'File is empty (0 bytes).';
  if (file.size > MAX_UPLOAD_BYTES) return `File exceeds the 25 MB limit (${(file.size / 1048576).toFixed(1)} MB).`;
  return null;
}

export function apiErrorMessage(err: any, fallback = 'Request failed.'): string {
  const data = err?.response?.data;
  if (typeof data?.detail === 'string') return data.detail;
  if (typeof data?.message === 'string') return data.message;
  if (Array.isArray(data?.detail)) return data.detail.map((d: any) => d.msg).join('; ');
  return err?.message || fallback;
}

function newIdempotencyKey(): string {
  if (typeof crypto !== 'undefined' && 'randomUUID' in crypto) return crypto.randomUUID();
  return `idem-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

export const applicationsApi = {
  newIdempotencyKey,

  async runtimeMode(): Promise<RuntimeMode> {
    return (await apiClient.get('/api/v1/runtime-mode')).data;
  },
  async dashboard(): Promise<DashboardStats> {
    return (await apiClient.get('/api/v1/applications-dashboard')).data;
  },
  async list(): Promise<ApplicationListItem[]> {
    const data = (await apiClient.get('/api/v1/applications')).data;
    return Array.isArray(data) ? data : [];
  },
  async get(id: string): Promise<Application> {
    return (await apiClient.get(`/api/v1/applications/${id}`)).data;
  },
  async create(payload: ApplicationPayload, idempotencyKey: string): Promise<Application> {
    return (await apiClient.post('/api/v1/applications', payload, { headers: { 'Idempotency-Key': idempotencyKey } })).data;
  },
  async uploadDocument(id: string, file: File, documentType: string): Promise<DocumentSummary> {
    const form = new FormData();
    form.append('document_type', documentType);
    form.append('file', file);
    return (await apiClient.post(`/api/v1/applications/${id}/documents`, form, { headers: { 'Content-Type': 'multipart/form-data' } })).data;
  },
  async startEvaluation(id: string, rerun = false): Promise<EvaluationRun> {
    return (await apiClient.post(`/api/v1/applications/${id}/evaluations`, null, { params: rerun ? { rerun: true } : {} })).data;
  },
  async getRun(runId: string): Promise<EvaluationRun> {
    return (await apiClient.get(`/api/v1/evaluation-runs/${runId}`)).data;
  },
  async getResults(runId: string): Promise<RunResults> {
    return (await apiClient.get(`/api/v1/evaluation-runs/${runId}/results`)).data;
  },
  async getEvidence(runId: string, ids: string[]): Promise<EvidenceRecord[]> {
    return (await apiClient.get(`/api/v1/evaluation-runs/${runId}/evidence`, { params: { ids: ids.join(',') } })).data;
  },
  async getReportPdf(runId: string): Promise<{ blob: Blob; filename: string }> {
    const res = await apiClient.get(`/api/v1/evaluation-runs/${runId}/report.pdf`, { responseType: 'blob' });
    const disposition = String(res.headers?.['content-disposition'] || '');
    const match = disposition.match(/filename="([^"]+)"/);
    return { blob: res.data, filename: match ? match[1] : `TIDES_Report_${runId.slice(0, 8)}.pdf` };
  },
};
