'use client';

import React, { useState } from 'react';
import { 
  CheckCircle2, 
  ChevronDown, 
  ChevronRight, 
  FileText, 
  AlertTriangle, 
  ShieldAlert, 
  Compass, 
  Cpu, 
  TrendingUp, 
  Users, 
  DollarSign, 
  Shield,
  Search,
  Info
} from 'lucide-react';
import { DomainAssessmentReport, CriterionAssessment } from '@/types';
import { VerificationBadge } from '@/components/VerificationBadge';

interface CanonicalDomainsViewProps {
  domainReports?: Record<string, DomainAssessmentReport> | null;
  legacyGraph?: any;
  className?: string;
  initialDomainKey?: string;
}

export interface DomainConfig {
  key: string;
  title: string;
  number: number;
  icon: React.ComponentType<{ className?: string }>;
  accentColor: string;
  borderClass: string;
  slides: string;
  criteriaPrefix: string;
  description: string;
}

export const CANONICAL_DOMAINS: DomainConfig[] = [
  {
    key: 'problem_solution',
    title: 'Problem & Solution',
    number: 1,
    icon: Compass,
    accentColor: 'text-blue-400',
    borderClass: 'border-blue-500/30',
    slides: 'Slides 3–5',
    criteriaPrefix: 'PS (PS-01 to PS-13)',
    description: 'Core problem severity, target personas, workarounds, solution, UVP, and Technology & TRL (PS-09 to PS-13).',
  },
  {
    key: 'market_opportunity',
    title: 'Market Opportunity & Competition',
    number: 2,
    icon: TrendingUp,
    accentColor: 'text-indigo-400',
    borderClass: 'border-indigo-500/30',
    slides: 'Slides 6–7',
    criteriaPrefix: 'MO (MO-01 to MO-10)',
    description: 'TAM/SAM/SOM, market growth CAGR, key drivers, geographic segment, and competitor benchmarking.',
  },
  {
    key: 'founder_team',
    title: 'Founder & Team Capability',
    number: 3,
    icon: Users,
    accentColor: 'text-purple-400',
    borderClass: 'border-purple-500/30',
    slides: 'Slides 8–10',
    criteriaPrefix: 'FT (FT-01 to FT-13)',
    description: 'Multi-founder backgrounds, education, domain expertise, core team, skill gaps, hiring plan, and advisors.',
  },
  {
    key: 'commercialisation',
    title: 'Business Model & Commercialisation',
    number: 4,
    icon: Cpu,
    accentColor: 'text-emerald-400',
    borderClass: 'border-emerald-500/30',
    slides: 'Slides 11–12',
    criteriaPrefix: 'BC (BC-01 to BC-16)',
    description: 'Business & revenue model, unit economics, GTM channels, CAC, margins, paying users vs trials, and signed pilots.',
  },
  {
    key: 'innovation_impact',
    title: 'Innovation, IP & Impact',
    number: 5,
    icon: Shield,
    accentColor: 'text-rose-400',
    borderClass: 'border-rose-500/30',
    slides: 'Slides 13–14',
    criteriaPrefix: 'II (II-01 to II-14)',
    description: 'Proprietary moats, network effects, patent disclosures, trade secrets, regulatory barriers, and UN SDG alignment.',
  },
  {
    key: 'financials_support',
    title: 'Financials & Incubation Support',
    number: 6,
    icon: DollarSign,
    accentColor: 'text-amber-400',
    borderClass: 'border-amber-500/30',
    slides: 'Slides 15–18',
    criteriaPrefix: 'FI (FI-01 to FI-21)',
    description: '3-year forecasts, monthly burn, runway, break-even timing, operating costs, and TIDES incubation needs.',
  },
];

/**
 * Explicit Domain Adapter:
 * Safely resolves domain report data from either canonical dictionary or legacy graph assessments.
 * Formally handles Technology & TRL tracing: criteria PS-09 through PS-13 reside in problem_solution (Slide 5).
 */
export function resolveDomainData(
  domainKey: string,
  domainReports?: Record<string, DomainAssessmentReport> | null,
  legacyGraph?: any
): { report: DomainAssessmentReport | null; sourceKey: string; provenanceNote?: string } {
  const normKey = domainKey.toLowerCase().trim();

  // Direct canonical resolution
  if (domainReports && domainReports[normKey]) {
    return { report: domainReports[normKey], sourceKey: normKey };
  }

  // Alias resolution for Technology & TRL queries
  if (normKey === 'trl' || normKey === 'technology') {
    const psReport = domainReports?.['problem_solution'] || legacyGraph?.domain_assessments?.['problem_solution'];
    if (psReport) {
      return {
        report: psReport,
        sourceKey: 'problem_solution',
        provenanceNote: 'Technology & TRL findings originate from LaunchIndex Domain 1 (Problem & Solution), Slide 5 (Criteria PS-09 to PS-13).',
      };
    }
  }

  // Legacy graph backward compatibility fallbacks
  const legacyMap: Record<string, string[]> = {
    problem_solution: ['problem_solution', 'product', 'trl'],
    market_opportunity: ['market_opportunity', 'market', 'competition'],
    founder_team: ['founder_team', 'founder'],
    commercialisation: ['commercialisation', 'commercialization'],
    innovation_impact: ['innovation_impact', 'ip'],
    financials_support: ['financials_support', 'financial', 'financials'],
  };

  const lookupKeys = legacyMap[normKey] || [normKey];
  for (const k of lookupKeys) {
    if (domainReports && domainReports[k]) {
      return { report: domainReports[k], sourceKey: k };
    }
    if (legacyGraph?.domain_assessments && legacyGraph.domain_assessments[k]) {
      return { report: legacyGraph.domain_assessments[k], sourceKey: k };
    }
  }

  return { report: null, sourceKey: normKey };
}

export function CanonicalDomainsView({
  domainReports = {},
  legacyGraph = null,
  className = '',
  initialDomainKey = 'problem_solution',
}: CanonicalDomainsViewProps) {
  const [selectedDomainKey, setSelectedDomainKey] = useState<string>(initialDomainKey);
  const [activeFilterTab, setActiveFilterTab] = useState<'all' | 'trl_only'>('all');
  const [expandedCriteria, setExpandedCriteria] = useState<Record<string, boolean>>({});
  const [searchFilter, setSearchFilter] = useState('');

  const toggleCriterion = (id: string) => {
    setExpandedCriteria(prev => ({ ...prev, [id]: !prev[id] }));
  };

  const activeConfig = CANONICAL_DOMAINS.find(d => d.key === selectedDomainKey) || CANONICAL_DOMAINS[0];
  const { report: activeReport, provenanceNote } = resolveDomainData(activeConfig.key, domainReports, legacyGraph);

  // Criteria evaluations list
  const criteriaList: CriterionAssessment[] = activeReport?.criteria_evaluations
    ? Object.values(activeReport.criteria_evaluations)
    : [];

  // Technology & TRL criteria in Domain 1 are PS-09 through PS-13
  const isTrlCriterion = (c: CriterionAssessment) => {
    const id = (c.criterion_id || '').toUpperCase();
    return id === 'PS-09' || id === 'PS-10' || id === 'PS-11' || id === 'PS-12' || id === 'PS-13' || id.startsWith('TRL');
  };

  const filteredCriteria = criteriaList.filter(c => {
    if (activeFilterTab === 'trl_only' && activeConfig.key === 'problem_solution') {
      if (!isTrlCriterion(c)) return false;
    }
    if (!searchFilter.trim()) return true;
    const q = searchFilter.toLowerCase();
    return (
      c.criterion_id?.toLowerCase().includes(q) ||
      c.criterion_name?.toLowerCase().includes(q) ||
      c.assessment_narrative?.toLowerCase().includes(q) ||
      c.extracted_startup_response?.toLowerCase().includes(q)
    );
  });

  return (
    <div className={`space-y-6 ${className}`}>
      {/* 6 Canonical Domain Selector Pills */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <div>
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300">
              Authoritative Evaluation Domains (6 Canonical Domains)
            </h3>
            <p className="text-[11px] text-slate-500">
              LaunchIndex Incubation Application pitch deck specification (18 slides across 6 specialist domains).
            </p>
          </div>
          <span className="text-[10px] text-slate-500 font-mono bg-slate-900 px-2 py-0.5 rounded border border-slate-800">
            LaunchIndex Registry
          </span>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
          {CANONICAL_DOMAINS.map((dom) => {
            const isSelected = selectedDomainKey === dom.key;
            const { report: rep } = resolveDomainData(dom.key, domainReports, legacyGraph);
            const Icon = dom.icon;
            const criteriaCount = rep?.criteria_evaluations ? Object.keys(rep.criteria_evaluations).length : 0;
            const confidence = rep?.composite_domain_confidence ?? 0.85;

            return (
              <button
                key={dom.key}
                type="button"
                onClick={() => {
                  setSelectedDomainKey(dom.key);
                  setActiveFilterTab('all');
                }}
                className={`flex flex-col p-3.5 rounded-xl text-left transition-all border ${
                  isSelected
                    ? `bg-slate-900 ${dom.borderClass} shadow-lg shadow-blue-500/5 ring-1 ring-blue-500/20`
                    : 'bg-slate-950/60 border-slate-800/80 hover:bg-slate-900/60 hover:border-slate-700'
                }`}
              >
                <div className="flex items-center justify-between w-full mb-2">
                  <span className="text-[10px] font-bold text-slate-500">Domain {dom.number}</span>
                  <Icon className={`w-4 h-4 ${isSelected ? dom.accentColor : 'text-slate-500'}`} />
                </div>
                <span className={`text-xs font-bold truncate ${isSelected ? 'text-slate-100' : 'text-slate-300'}`}>
                  {dom.title}
                </span>
                <span className="text-[10px] text-slate-500 truncate mt-0.5">{dom.slides}</span>
                <div className="flex items-center justify-between text-[10px] text-slate-500 mt-2 pt-2 border-t border-slate-900">
                  <span>{criteriaCount > 0 ? `${criteriaCount} criteria` : 'Active'}</span>
                  <span className="font-mono text-blue-400">{(confidence * 100).toFixed(0)}%</span>
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Active Domain Panel */}
      <div className="glass rounded-xl p-6 md:p-8 border border-slate-800 space-y-6">
        {/* Active Domain Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-5">
          <div className="space-y-1">
            <div className="flex items-center space-x-2">
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-900 border border-slate-800 text-slate-400 uppercase">
                Domain {activeConfig.number} &bull; {activeConfig.key}
              </span>
              <span className="px-2 py-0.5 rounded-full text-[9px] font-bold bg-amber-500/20 text-amber-300 border border-amber-500/40 uppercase tracking-wider">
                MOCK DEMONSTRATION
              </span>
              <span className="text-[10px] text-slate-500">
                {activeConfig.slides} &bull; {activeConfig.criteriaPrefix}
              </span>
              {activeReport?.model_used && (
                <span className="text-[10px] font-mono text-slate-500">
                  Model: {activeReport.model_used}
                </span>
              )}
            </div>
            <h2 className="text-xl font-bold text-slate-100 flex items-center space-x-2">
              <span>{activeConfig.title}</span>
            </h2>
            <p className="text-xs text-slate-400">{activeConfig.description}</p>
          </div>

          <div className="flex items-center space-x-3 text-xs">
            <div className="bg-slate-950 px-3 py-1.5 rounded-lg border border-slate-800 text-slate-300">
              <span className="text-slate-500 text-[10px] uppercase block">Composite Confidence</span>
              <span className="font-bold text-blue-400">
                {((activeReport?.composite_domain_confidence ?? 0.85) * 100).toFixed(0)}%
              </span>
            </div>
            {activeReport?.cost_usd !== undefined && (
              <div className="bg-slate-950 px-3 py-1.5 rounded-lg border border-slate-800 text-slate-300">
                <span className="text-slate-500 text-[10px] uppercase block">Allocated Cost</span>
                <span className="font-mono font-bold text-emerald-400">
                  ${activeReport.cost_usd.toFixed(4)}
                </span>
              </div>
            )}
          </div>
        </div>

        {/* Technology & TRL Provenance Note if applicable */}
        {provenanceNote && (
          <div className="bg-blue-950/20 border border-blue-900/40 p-3 rounded-lg flex items-start space-x-2 text-xs text-blue-300">
            <Info className="w-4 h-4 text-blue-400 flex-shrink-0 mt-0.5" />
            <span>{provenanceNote}</span>
          </div>
        )}

        {/* Domain Executive Narrative */}
        <div className="space-y-2">
          <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider">Domain Synthesis Narrative</h4>
          <p className="text-xs text-slate-300 leading-relaxed whitespace-pre-line bg-slate-950/50 p-4 rounded-lg border border-slate-800/60">
            {activeReport?.executive_summary || activeReport?.summary || 'Detailed domain analysis registered across canonical criteria.'}
          </p>
        </div>

        {/* Strengths / Weaknesses / Unsupported Claims Quick Cards */}
        {activeReport && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Strengths */}
            <div className="bg-slate-950/60 p-4 rounded-xl border border-slate-800/80 space-y-2">
              <span className="text-[10px] font-bold text-emerald-400 uppercase tracking-wider flex items-center space-x-1">
                <CheckCircle2 className="w-3.5 h-3.5" />
                <span>Verified Strengths ({activeReport.strengths?.length || 0})</span>
              </span>
              {activeReport.strengths && activeReport.strengths.length > 0 ? (
                <ul className="text-xs text-slate-300 space-y-1.5 list-disc list-inside">
                  {activeReport.strengths.slice(0, 4).map((s, idx) => (
                    <li key={idx} className="leading-snug text-slate-300">{s}</li>
                  ))}
                </ul>
              ) : (
                <p className="text-xs text-slate-500 italic">No specific strengths listed.</p>
              )}
            </div>

            {/* Weaknesses */}
            <div className="bg-slate-950/60 p-4 rounded-xl border border-slate-800/80 space-y-2">
              <span className="text-[10px] font-bold text-amber-400 uppercase tracking-wider flex items-center space-x-1">
                <AlertTriangle className="w-3.5 h-3.5" />
                <span>Identified Deficiencies ({activeReport.weaknesses?.length || 0})</span>
              </span>
              {activeReport.weaknesses && activeReport.weaknesses.length > 0 ? (
                <ul className="text-xs text-slate-300 space-y-1.5 list-disc list-inside">
                  {activeReport.weaknesses.slice(0, 4).map((w, idx) => (
                    <li key={idx} className="leading-snug text-slate-300">{w}</li>
                  ))}
                </ul>
              ) : (
                <p className="text-xs text-slate-500 italic">No critical deficiencies noted.</p>
              )}
            </div>

            {/* Unsupported Claims */}
            <div className="bg-slate-950/60 p-4 rounded-xl border border-slate-800/80 space-y-2">
              <span className="text-[10px] font-bold text-rose-400 uppercase tracking-wider flex items-center space-x-1">
                <ShieldAlert className="w-3.5 h-3.5" />
                <span>Unsupported Claims ({activeReport.unsupported_claims?.length || 0})</span>
              </span>
              {activeReport.unsupported_claims && activeReport.unsupported_claims.length > 0 ? (
                <ul className="text-xs text-slate-300 space-y-1.5 list-disc list-inside">
                  {activeReport.unsupported_claims.slice(0, 4).map((u, idx) => (
                    <li key={idx} className="leading-snug text-slate-300">{u}</li>
                  ))}
                </ul>
              ) : (
                <p className="text-xs text-slate-500 italic">No unsubstantiated leaps identified.</p>
              )}
            </div>
          </div>
        )}

        {/* Criteria Evaluation List Header & Filters */}
        <div className="space-y-4 pt-2">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-3">
            <div className="space-y-1">
              <h4 className="text-xs font-bold text-slate-200 uppercase tracking-wider">
                Criteria Evaluations ({filteredCriteria.length} of {criteriaList.length})
              </h4>
              <p className="text-[11px] text-slate-400">
                Detailed evidence provenance and verification grading for individual criteria.
              </p>
            </div>

            {/* Specialized Technology & TRL Filter for Problem & Solution */}
            {activeConfig.key === 'problem_solution' && (
              <div className="flex items-center space-x-2">
                <button
                  type="button"
                  onClick={() => setActiveFilterTab('all')}
                  className={`px-2.5 py-1 rounded text-[11px] font-semibold transition-all ${
                    activeFilterTab === 'all'
                      ? 'bg-blue-600 text-white'
                      : 'bg-slate-900 text-slate-400 hover:text-slate-200 border border-slate-800'
                  }`}
                >
                  All (PS-01 to PS-13)
                </button>
                <button
                  type="button"
                  onClick={() => setActiveFilterTab('trl_only')}
                  className={`px-2.5 py-1 rounded text-[11px] font-semibold transition-all flex items-center space-x-1 ${
                    activeFilterTab === 'trl_only'
                      ? 'bg-emerald-600 text-white'
                      : 'bg-slate-900 text-slate-400 hover:text-slate-200 border border-slate-800'
                  }`}
                  title="Filter to Technology Readiness Level & Prototype Validation (PS-09 to PS-13)"
                >
                  <Cpu className="w-3 h-3" />
                  <span>Technology & TRL (PS-09–13)</span>
                </button>
              </div>
            )}

            {criteriaList.length > 0 && (
              <div className="relative w-full sm:w-64">
                <Search className="w-3.5 h-3.5 text-slate-500 absolute left-3 top-2.5" />
                <input
                  type="text"
                  placeholder="Filter criteria or ID..."
                  value={searchFilter}
                  onChange={(e) => setSearchFilter(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg pl-8 pr-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-blue-500"
                />
              </div>
            )}
          </div>

          {/* Criteria Cards Accordion */}
          {filteredCriteria.length > 0 ? (
            <div className="space-y-3">
              {filteredCriteria.map((c: CriterionAssessment) => {
                const isExpanded = !!expandedCriteria[c.criterion_id];
                const isTrl = isTrlCriterion(c);

                return (
                  <div
                    key={c.criterion_id}
                    className={`rounded-xl border transition-all ${
                      isTrl 
                        ? 'border-emerald-500/20 bg-slate-950/70' 
                        : 'border-slate-800 bg-slate-950/60'
                    } overflow-hidden`}
                  >
                    {/* Header Row */}
                    <div
                      onClick={() => toggleCriterion(c.criterion_id)}
                      className="p-4 flex items-center justify-between cursor-pointer hover:bg-slate-900/40 select-none gap-4"
                    >
                      <div className="flex items-center space-x-3 min-w-0">
                        <span className={`font-mono text-xs font-bold px-2 py-0.5 rounded border flex-shrink-0 ${
                          isTrl 
                            ? 'text-emerald-400 bg-emerald-500/10 border-emerald-500/30' 
                            : 'text-blue-400 bg-blue-500/10 border-blue-500/20'
                        }`}>
                          {c.criterion_id}
                        </span>
                        <div className="min-w-0">
                          <div className="flex items-center space-x-2">
                            <h5 className="text-xs font-bold text-slate-200 truncate">
                              {c.criterion_name}
                            </h5>
                            {isTrl && (
                              <span className="text-[9px] uppercase font-bold text-emerald-400 bg-emerald-950/80 px-1.5 py-0.2 rounded border border-emerald-800/40">
                                Tech / TRL
                              </span>
                            )}
                          </div>
                          {c.source_locations && c.source_locations.length > 0 && (
                            <span className="text-[10px] text-slate-500 flex items-center space-x-1 mt-0.5">
                              <FileText className="w-3 h-3 text-slate-500" />
                              <span>Cited in: {c.source_locations.join(', ')}</span>
                            </span>
                          )}
                        </div>
                      </div>

                      <div className="flex items-center space-x-3 flex-shrink-0">
                        <VerificationBadge status={c.verification_status} size="sm" />
                        {isExpanded ? (
                          <ChevronDown className="w-4 h-4 text-slate-400" />
                        ) : (
                          <ChevronRight className="w-4 h-4 text-slate-500" />
                        )}
                      </div>
                    </div>

                    {/* Expanded Body with Evidence Provenance */}
                    {isExpanded && (
                      <div className="p-4 pt-2 border-t border-slate-900 bg-slate-900/20 space-y-4 text-xs">
                        {/* Extracted Startup Response */}
                        {c.extracted_startup_response && (
                          <div className="space-y-1">
                            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                              Extracted Application Statement:
                            </span>
                            <div className="bg-slate-950 p-3 rounded-lg border border-slate-800 text-slate-300 font-mono text-[11px] leading-relaxed">
                              &ldquo;{c.extracted_startup_response}&rdquo;
                            </div>
                          </div>
                        )}

                        {/* Specialist Assessment Narrative */}
                        <div className="space-y-1">
                          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                            Specialist Domain Assessment:
                          </span>
                          <p className="text-slate-300 leading-relaxed bg-slate-950/40 p-3 rounded-lg border border-slate-800/50">
                            {c.assessment_narrative}
                          </p>
                        </div>

                        {/* Provenance Citations & Evidence IDs */}
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-[11px] text-slate-400 pt-1">
                          {c.source_locations && c.source_locations.length > 0 && (
                            <div className="bg-slate-950 p-2.5 rounded-lg border border-slate-800/80">
                              <span className="text-[10px] font-semibold text-slate-500 uppercase block mb-1">
                                Document Locations
                              </span>
                              <span className="text-slate-300">{c.source_locations.join('; ')}</span>
                            </div>
                          )}
                          {c.evidence_ids && c.evidence_ids.length > 0 && (
                            <div className="bg-slate-950 p-2.5 rounded-lg border border-slate-800/80">
                              <span className="text-[10px] font-semibold text-slate-500 uppercase block mb-1">
                                Evidence IDs
                              </span>
                              <span className="text-slate-300 font-mono text-[10px]">{c.evidence_ids.join(', ')}</span>
                            </div>
                          )}
                        </div>

                        {/* Contradictions or Risks if present */}
                        {c.contradictions && c.contradictions.length > 0 && (
                          <div className="bg-rose-950/20 border border-rose-900/30 p-3 rounded-lg text-rose-300">
                            <span className="text-[10px] font-bold uppercase block mb-1">Contradiction Detected:</span>
                            <ul className="list-disc list-inside space-y-0.5 text-[11px]">
                              {c.contradictions.map((ct, idx) => (
                                <li key={idx}>{ct}</li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="text-center py-8 text-slate-500 text-xs bg-slate-950/30 rounded-xl border border-slate-900">
              {searchFilter
                ? 'No criteria match your search query.'
                : 'Canonical criteria evaluations are structured across application dimensions.'}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
