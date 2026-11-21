'use client';

import React from 'react';
import { 
  ShieldCheck, 
  AlertTriangle, 
  CheckCircle2, 
  HelpCircle, 
  Layers, 
  RefreshCw,
  GitCompare,
  FileSpreadsheet,
  Info
} from 'lucide-react';
import { FinalReviewAssessment, CrossDomainContradiction, TargetedRecheckResult } from '@/types';

interface SupervisoryReviewViewProps {
  review?: FinalReviewAssessment | null;
  className?: string;
}

export function mapRecommendation(rec?: string): {
  display: 'Support' | 'Nurture' | 'Decline';
  badgeClass: string;
  dotClass: string;
  description: string;
} {
  const norm = (rec || '').toUpperCase().trim();
  if (norm === 'INCUBATE' || norm === 'SUPPORT' || norm === 'APPROVE') {
    return {
      display: 'Support',
      badgeClass: 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30',
      dotClass: 'bg-emerald-400',
      description: 'Strong incubation candidate meeting strategic and evidentiary thresholds.',
    };
  }
  if (norm === 'REJECT' || norm === 'DECLINE') {
    return {
      display: 'Decline',
      badgeClass: 'bg-rose-500/15 text-rose-400 border-rose-500/30',
      dotClass: 'bg-rose-400',
      description: 'Does not currently satisfy incubation criteria or exhibits unresolvable risks.',
    };
  }
  // Default to Nurture for CONDITIONAL, DEFER, or other states
  return {
    display: 'Nurture',
    badgeClass: 'bg-amber-500/15 text-amber-300 border-amber-500/30',
    dotClass: 'bg-amber-400',
    description: 'Promising venture requiring targeted milestone completion prior to onboarding.',
  };
}

export function SupervisoryReviewView({ review, className = '' }: SupervisoryReviewViewProps) {
  if (!review) {
    return (
      <div className={`glass rounded-xl p-6 border border-slate-800 text-center space-y-3 ${className}`}>
        <Info className="w-8 h-8 text-slate-500 mx-auto" />
        <h3 className="text-sm font-semibold text-slate-300">Supervisory Review Pending</h3>
        <p className="text-xs text-slate-500 max-w-md mx-auto">
          The supervisory synthesis reviewer will produce an institutional recommendation once specialist domain assessments are complete.
        </p>
      </div>
    );
  }

  const recMeta = mapRecommendation(review.overall_recommendation);
  const investmentScore = review.investment_score ?? null;
  const confidenceScore = review.confidence_score ?? 0.85;

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Mandatory Regulatory / Human Decision Disclosure */}
      <div className="bg-slate-900/80 border border-slate-700/60 rounded-xl p-4 flex items-start space-x-3 text-slate-300 shadow-sm">
        <AlertTriangle className="w-5 h-5 text-amber-400 flex-shrink-0 mt-0.5" />
        <div className="text-xs leading-relaxed">
          <span className="font-semibold text-slate-200">Institutional Governance Notice: </span>
          This AI-generated due diligence assessment supports human decision-making and does not constitute an approval, guarantee, or funding sanction. Final investment and incubation onboarding decisions reside exclusively with the designated Investment and Incubation Committees.
        </div>
      </div>

      {/* Hero Decision Block */}
      <div className="glass rounded-xl p-6 md:p-8 border border-slate-800 bg-gradient-to-br from-slate-900/80 via-slate-900/40 to-slate-950/80 space-y-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-6">
          <div className="space-y-2">
            <div className="flex items-center space-x-3">
              <span className={`px-3 py-1 rounded-full text-xs font-bold border tracking-wide uppercase ${recMeta.badgeClass}`}>
                Recommendation: {recMeta.display}
              </span>
              <span className="text-xs font-mono text-slate-400">
                ({review.overall_recommendation || 'CONDITIONAL'})
              </span>
              <span className="px-2.5 py-0.5 rounded-full text-[10px] font-extrabold bg-amber-500/20 text-amber-300 border border-amber-500/40 uppercase tracking-widest">
                MOCK DEMONSTRATION
              </span>
              {review.report_id && (
                <span className="text-[11px] font-mono text-slate-500 bg-slate-950/60 px-2 py-0.5 rounded border border-slate-800">
                  {review.report_id}
                </span>
              )}
            </div>
            <h2 className="text-2xl font-bold text-slate-100 tracking-tight">
              {review.startup_name || 'Venture Due Diligence Synthesis'}
            </h2>
            <p className="text-xs text-slate-400">{recMeta.description}</p>
          </div>

          {/* Scores Meter */}
          <div className="flex items-center space-x-4 bg-slate-950/80 p-4 rounded-xl border border-slate-800/80">
            <div className="text-center px-3 border-r border-slate-800">
              <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">Investment Score</span>
              <span className="text-2xl font-black text-slate-100">
                {investmentScore !== null ? `${investmentScore.toFixed(0)}` : 'N/A'}
                <span className="text-xs text-slate-500 font-normal"> / 100</span>
              </span>
            </div>
            <div className="text-center px-3">
              <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">Confidence</span>
              <span className="text-2xl font-black text-blue-400">
                {(confidenceScore * 100).toFixed(0)}%
              </span>
            </div>
          </div>
        </div>

        {/* Executive Synthesis & Rationale */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="space-y-2">
            <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center space-x-1.5">
              <ShieldCheck className="w-4 h-4 text-blue-400" />
              <span>Supervisory Executive Summary</span>
            </h4>
            <p className="text-xs text-slate-300 leading-relaxed whitespace-pre-line bg-slate-950/40 p-4 rounded-lg border border-slate-800/50">
              {review.executive_summary || 'No executive summary provided.'}
            </p>
          </div>

          <div className="space-y-2">
            <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center space-x-1.5">
              <Layers className="w-4 h-4 text-indigo-400" />
              <span>Institutional Rationale</span>
            </h4>
            <p className="text-xs text-slate-300 leading-relaxed whitespace-pre-line bg-slate-950/40 p-4 rounded-lg border border-slate-800/50">
              {review.recommendation_rationale || 'No detailed rationale recorded.'}
            </p>
          </div>
        </div>

        {/* Cross-Domain Findings */}
        {review.cross_domain_findings && review.cross_domain_findings.length > 0 && (
          <div className="space-y-3 pt-2 border-t border-slate-800/60">
            <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider">
              Cross-Domain Synthesis Observations ({review.cross_domain_findings.length})
            </h4>
            <ul className="grid grid-cols-1 md:grid-cols-2 gap-2 text-xs text-slate-300">
              {review.cross_domain_findings.map((f, i) => (
                <li key={i} className="flex items-start space-x-2 bg-slate-950/30 p-2.5 rounded-lg border border-slate-800/40">
                  <span className="text-blue-400 font-bold mt-0.5">&bull;</span>
                  <span className="leading-relaxed">{f}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {/* Incubation Conditions & Resource Tranches */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Conditions */}
        <div className="glass rounded-xl p-6 border border-slate-800 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center space-x-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              <span>Incubation Conditions ({review.incubation_conditions?.length || 0})</span>
            </h4>
            <span className="text-[10px] text-slate-500">Prerequisites</span>
          </div>

          {review.incubation_conditions && review.incubation_conditions.length > 0 ? (
            <div className="space-y-2">
              {review.incubation_conditions.map((cond, i) => (
                <div key={i} className="flex items-start space-x-2.5 p-3 rounded-lg bg-slate-950/60 border border-slate-800/60 text-xs text-slate-300">
                  <span className="w-5 h-5 rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/20 flex items-center justify-center text-[10px] font-bold flex-shrink-0 mt-0.5">
                    {i + 1}
                  </span>
                  <span className="leading-relaxed">{cond}</span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-xs text-slate-500 italic p-4 text-center">No conditional prerequisites attached.</p>
          )}
        </div>

        {/* Tranches */}
        <div className="glass rounded-xl p-6 border border-slate-800 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center space-x-2">
              <FileSpreadsheet className="w-4 h-4 text-indigo-400" />
              <span>Recommended Tranches & Milestones</span>
            </h4>
            <span className="text-[10px] text-slate-500">Capital & Support Schedule</span>
          </div>

          {review.recommended_tranches && review.recommended_tranches.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-slate-800 text-[10px] text-slate-500 uppercase tracking-wider">
                    <th className="pb-2">Tranche / Phase</th>
                    <th className="pb-2">Milestone Prerequisite</th>
                    <th className="pb-2 text-right">Allocation</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 text-slate-300">
                  {review.recommended_tranches.map((tr, i) => (
                    <tr key={i} className="hover:bg-slate-900/30">
                      <td className="py-2.5 font-semibold text-slate-200">
                        {tr.tranche_name || `Tranche ${i + 1}`}
                      </td>
                      <td className="py-2.5 text-slate-400 max-w-xs break-words">
                        {tr.milestone || tr.description || 'Milestone verification'}
                      </td>
                      <td className="py-2.5 text-right font-mono text-emerald-400">
                        {tr.amount ? `${tr.currency || 'INR'} ${Number(tr.amount).toLocaleString()}` : 'Support / Grant'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="text-xs text-slate-500 italic p-4 text-center">Tranche allocations will be structured post-committee approval.</p>
          )}
        </div>
      </div>

      {/* Cross-Domain Contradictions Table */}
      {review.identified_contradictions && review.identified_contradictions.length > 0 && (
        <div className="glass rounded-xl p-6 border border-rose-900/30 bg-rose-950/5 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <h4 className="text-xs font-bold text-rose-300 uppercase tracking-wider flex items-center space-x-2">
              <GitCompare className="w-4 h-4 text-rose-400" />
              <span>Cross-Domain Discrepancies & Contradictions ({review.identified_contradictions.length})</span>
            </h4>
            <span className="text-[10px] text-slate-500">Audited Cross-Checks</span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-slate-800 text-[10px] text-slate-400 uppercase tracking-wider">
                  <th className="pb-2">Conflict Nature</th>
                  <th className="pb-2">First Claim (Domain A)</th>
                  <th className="pb-2">Conflicting Claim (Domain B)</th>
                  <th className="pb-2">Resolution Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/80 text-slate-300">
                {review.identified_contradictions.map((c: CrossDomainContradiction, i: number) => {
                  const isResolved = c.resolution_status === 'RESOLVED';
                  const isDisagreement = c.resolution_status === 'PRESERVED_DISAGREEMENT';

                  return (
                    <tr key={i} className="hover:bg-slate-900/40">
                      <td className="py-3 font-semibold text-rose-400 text-[11px] align-top">
                        {c.nature_of_conflict || 'CONFLICT'}
                      </td>
                      <td className="py-3 text-slate-300 text-xs align-top pr-2">
                        <span className="text-[10px] font-mono text-slate-500 block mb-1">
                          {c.domain_a} &bull; {c.criterion_a}
                        </span>
                        <span>{c.claim_a_summary}</span>
                      </td>
                      <td className="py-3 text-slate-300 text-xs align-top pr-2">
                        <span className="text-[10px] font-mono text-slate-500 block mb-1">
                          {c.domain_b} &bull; {c.criterion_b}
                        </span>
                        <span>{c.claim_b_summary}</span>
                      </td>
                      <td className="py-3 align-top whitespace-nowrap">
                        <span className={`inline-block px-2 py-0.5 rounded text-[10px] font-bold border ${
                          isResolved ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30' :
                          isDisagreement ? 'bg-purple-500/10 text-purple-400 border-purple-500/30' :
                          'bg-amber-500/10 text-amber-400 border-amber-500/30'
                        }`}>
                          {c.resolution_status}
                        </span>
                        {c.resolution_rationale && (
                          <p className="text-[10px] text-slate-400 mt-1 max-w-xs break-words">
                            {c.resolution_rationale}
                          </p>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Targeted Rechecks & Preserved Disagreements */}
      {((review.rechecks_triggered && review.rechecks_triggered.length > 0) ||
        (review.unresolved_disagreements && review.unresolved_disagreements.length > 0)) && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Rechecks */}
          {review.rechecks_triggered && review.rechecks_triggered.length > 0 && (
            <div className="glass rounded-xl p-6 border border-slate-800 space-y-3">
              <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center space-x-2">
                <RefreshCw className="w-4 h-4 text-blue-400" />
                <span>Targeted Specialist Re-Checks ({review.rechecks_triggered.length})</span>
              </h4>
              <div className="space-y-2">
                {review.rechecks_triggered.map((rc: TargetedRecheckResult, i: number) => (
                  <div key={i} className="p-3 rounded-lg bg-slate-950/60 border border-slate-800 text-xs space-y-1.5">
                    <div className="flex items-center justify-between text-[10px] text-slate-400">
                      <span className="font-mono text-blue-400">{rc.domain_key} &bull; {rc.criterion_id}</span>
                      <span className="font-mono">{rc.recheck_id}</span>
                    </div>
                    <div className="flex items-center space-x-2 text-[11px]">
                      <span className="text-slate-500 line-through">{rc.original_verification_status}</span>
                      <span className="text-slate-400">&rarr;</span>
                      <span className="text-emerald-400 font-semibold">{rc.updated_verification_status}</span>
                    </div>
                    <p className="text-slate-300 text-xs">{rc.recheck_reasoning}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Preserved Disagreements */}
          {review.unresolved_disagreements && review.unresolved_disagreements.length > 0 && (
            <div className="glass rounded-xl p-6 border border-slate-800 space-y-3">
              <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center space-x-2">
                <HelpCircle className="w-4 h-4 text-purple-400" />
                <span>Preserved Disagreements for Committee ({review.unresolved_disagreements.length})</span>
              </h4>
              <ul className="space-y-2 text-xs text-slate-300">
                {review.unresolved_disagreements.map((d: string, i: number) => (
                  <li key={i} className="p-3 rounded-lg bg-purple-950/10 border border-purple-800/30">
                    <span className="text-purple-400 font-bold mr-1.5">&bull;</span>
                    {d}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
