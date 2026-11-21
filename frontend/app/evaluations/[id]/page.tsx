'use client';

import React, { use, useEffect, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useRouter } from 'next/navigation';
import { apiService } from '@/services/api';
import { useAuth } from '@/contexts/auth-context';
import { 
  Sparkles, 
  HelpCircle, 
  AlertTriangle, 
  CheckCircle, 
  FileText, 
  Workflow, 
  ArrowLeft, 
  Gauge, 
  Loader2,
  Layers,
  RefreshCw
} from 'lucide-react';
import { SupervisoryReviewView } from '@/components/SupervisoryReviewView';
import { CanonicalDomainsView } from '@/components/CanonicalDomainsView';
import { FinalReviewAssessment, DomainAssessmentReport } from '@/types';

export default function EvaluationDetailsPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const { user } = useAuth();
  const router = useRouter();
  const [activeTab, setActiveTab] = useState<'domains' | 'supervisory' | 'graph_feed'>('domains');

  // Redirect if not authenticated
  useEffect(() => {
    if (!user) {
      router.push('/login');
    }
  }, [user, router]);

  const { data: graph, isLoading, error, refetch } = useQuery({
    queryKey: ['evaluationResult', id],
    queryFn: () => apiService.getEvaluationResult(id),
    enabled: !!user && !!id,
    retry: 2,
  });

  if (!user) {
    return (
      <div className="flex h-screen items-center justify-center bg-slate-950 text-slate-100">
        <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center bg-slate-950 text-slate-100">
        <div className="flex flex-col items-center space-y-4">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-500 border-t-transparent"></div>
          <span className="text-sm text-slate-400">Loading evaluation results...</span>
        </div>
      </div>
    );
  }

  if (error || !graph) {
    return (
      <div className="flex h-screen items-center justify-center bg-slate-950">
        <div className="p-8 text-center text-slate-500 max-w-lg mx-auto space-y-4">
          <AlertTriangle className="w-12 h-12 text-amber-500 mx-auto" />
          <h3 className="text-lg font-bold text-slate-200">Evaluation Not Found</h3>
          <p className="text-sm text-slate-400">
            The startup evaluation graph ({id}) could not be resolved. Please execute the evaluation pipeline first.
          </p>
          <div className="flex justify-center space-x-3 pt-2">
            <button
              onClick={() => refetch()}
              className="bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg px-4 py-2 text-xs font-semibold transition-colors flex items-center space-x-1.5"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              <span>Retry</span>
            </button>
            <button
              onClick={() => router.push('/upload')}
              className="bg-blue-600 hover:bg-blue-500 text-white rounded-lg px-4 py-2 text-sm font-semibold transition-colors"
            >
              Go to Uploader
            </button>
          </div>
        </div>
      </div>
    );
  }

  const exec = graph.executive_assessment || {
    summary: 'No executive summary has been generated yet.',
    confidence: null as number | null,
    overall_score: null as number | null,
    recommendation: null as string | null,
  };

  const inv = graph.investment_assessment || null;

  const supervisoryReview: FinalReviewAssessment | null =
    (graph.supervisory_review as FinalReviewAssessment) ||
    (graph.final_review as FinalReviewAssessment) ||
    (graph.report?.final_review as FinalReviewAssessment) ||
    null;

  const domainReports: Record<string, DomainAssessmentReport> =
    (graph.domain_reports as Record<string, DomainAssessmentReport>) ||
    (graph.domain_assessments as Record<string, DomainAssessmentReport>) ||
    (graph.report?.domain_reports as Record<string, DomainAssessmentReport>) ||
    {};

  // Observations, risks, questions from graph nodes
  const observations = Object.values(graph.observations || {});
  const risks = Object.values(graph.risks || {});
  const questions = Object.values(graph.questions || {});

  const reportId = graph.report?.report_id || graph.startup_id || id;

  return (
    <div className="p-6 md:p-8 space-y-8 max-w-7xl mx-auto">
      {/* Back & Actions */}
      <div className="flex items-center justify-between border-b border-slate-900 pb-4">
        <button
          onClick={() => router.push('/startups')}
          className="flex items-center space-x-2 text-xs text-slate-400 hover:text-slate-200 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to startups</span>
        </button>

        <div className="flex space-x-3">
          <button
            onClick={() => router.push(`/evaluations/${id}/graph`)}
            className="flex items-center space-x-2 bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-300 rounded-lg px-4 py-2 text-xs font-semibold transition-all"
          >
            <Workflow className="w-4 h-4 text-blue-400" />
            <span>Interactive Graph</span>
          </button>
          <button
            onClick={() => router.push(`/reports/${reportId}`)}
            className="flex items-center space-x-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg px-4 py-2 text-xs font-semibold transition-all shadow-lg shadow-blue-500/10"
          >
            <FileText className="w-4 h-4" />
            <span>Open Due Diligence Report</span>
          </button>
        </div>
      </div>

      {/* Startup Executive Block */}
      <div className="glass rounded-xl p-8 border border-slate-800 grid grid-cols-1 md:grid-cols-4 gap-8 items-center">
        <div className="md:col-span-3 space-y-3">
          <div className="flex items-center space-x-3">
            <span className="text-xs font-extrabold text-blue-400 uppercase tracking-widest bg-blue-500/10 border border-blue-500/20 px-3 py-1 rounded-full">
              {supervisoryReview?.overall_recommendation || exec.recommendation || inv?.recommendation || 'PENDING'}
            </span>
            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-500/20 text-amber-300 border border-amber-500/40 uppercase tracking-wider">
              MOCK DEMONSTRATION
            </span>
            <h1 className="text-3xl font-black text-slate-100">{graph.startup_name || 'Venture Evaluation'}</h1>
          </div>
          <p className="text-slate-300 text-xs md:text-sm leading-relaxed">
            {typeof (supervisoryReview?.executive_summary || exec.summary) === 'string'
              ? (supervisoryReview?.executive_summary || exec.summary)
              : (supervisoryReview?.executive_summary || exec.summary)?.overview || 'Evaluation and synthesis complete.'}
          </p>
        </div>

        {/* Scoring Radial Meter */}
        {(() => {
          const displayScore = supervisoryReview?.investment_score ?? inv?.investment_score ?? exec.overall_score;
          const displayConf = supervisoryReview?.confidence_score ?? inv?.confidence ?? exec.confidence;
          return (
            <div className="flex flex-col items-center justify-center p-4 rounded-xl bg-slate-950 border border-slate-900 text-center">
              <Gauge className="w-8 h-8 text-blue-400 mb-2" />
              <span className="text-3xl font-black text-slate-100">
                {typeof displayScore === 'number' ? displayScore.toFixed(0) : 'N/A'}
              </span>
              <span className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider mt-1">Investment Score</span>
              <span className="text-xs text-slate-400 mt-1">
                Confidence: {typeof displayConf === 'number' ? `${(displayConf * 100).toFixed(0)}%` : 'N/A'}
              </span>
            </div>
          );
        })()}
      </div>

      {/* Tab Switcher */}
      <div className="flex items-center space-x-2 border-b border-slate-800 pb-2">
        <button
          type="button"
          onClick={() => setActiveTab('domains')}
          className={`flex items-center space-x-2 px-4 py-2 rounded-lg text-xs font-bold transition-all ${
            activeTab === 'domains'
              ? 'bg-blue-600 text-white shadow-md shadow-blue-500/20'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
          }`}
        >
          <Layers className="w-4 h-4" />
          <span>Six Canonical Domains</span>
        </button>

        <button
          type="button"
          onClick={() => setActiveTab('supervisory')}
          className={`flex items-center space-x-2 px-4 py-2 rounded-lg text-xs font-bold transition-all ${
            activeTab === 'supervisory'
              ? 'bg-blue-600 text-white shadow-md shadow-blue-500/20'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
          }`}
        >
          <Sparkles className="w-4 h-4" />
          <span>Supervisory Review Synthesis</span>
        </button>

        <button
          type="button"
          onClick={() => setActiveTab('graph_feed')}
          className={`flex items-center space-x-2 px-4 py-2 rounded-lg text-xs font-bold transition-all ${
            activeTab === 'graph_feed'
              ? 'bg-blue-600 text-white shadow-md shadow-blue-500/20'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
          }`}
        >
          <CheckCircle className="w-4 h-4" />
          <span>Observation & Risk Feeds</span>
        </button>
      </div>

      {/* Tab 1: Canonical Domains View */}
      {activeTab === 'domains' && (
        <CanonicalDomainsView domainReports={domainReports} legacyGraph={graph} />
      )}

      {/* Tab 2: Supervisory Review Synthesis */}
      {activeTab === 'supervisory' && (
        <SupervisoryReviewView review={supervisoryReview} />
      )}

      {/* Tab 3: Observation & Risk Feeds */}
      {activeTab === 'graph_feed' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Observations Feed */}
          <div className="glass rounded-xl border border-slate-800 overflow-hidden flex flex-col">
            <div className="p-5 border-b border-slate-900 bg-slate-950/40 flex items-center justify-between">
              <span className="text-xs font-semibold text-slate-200 uppercase tracking-wider">
                Observations ({observations.length})
              </span>
              <CheckCircle className="w-4 h-4 text-emerald-400" />
            </div>
            <div className="p-4 space-y-4 divide-y divide-slate-900 overflow-y-auto max-h-[400px]">
              {observations.length > 0 ? (
                observations.map((obs: any, idx) => (
                  <div key={idx} className={`pt-4 ${idx === 0 ? 'pt-0' : ''} space-y-1`}>
                    <p className="text-slate-300 text-xs leading-relaxed font-medium">
                      {obs.description || obs.content}
                    </p>
                    <div className="flex items-center justify-between text-[10px] text-slate-500 pt-1">
                      <span>Score: {typeof obs.score === 'number' ? obs.score.toFixed(2) : 'N/A'}</span>
                      <span>Source: {obs.source || 'Submitted Document'}</span>
                    </div>
                  </div>
                ))
              ) : (
                <div className="text-center text-slate-600 text-xs py-8">No observations registered.</div>
              )}
            </div>
          </div>

          {/* Risks Feed */}
          <div className="glass rounded-xl border border-slate-800 overflow-hidden flex flex-col">
            <div className="p-5 border-b border-slate-900 bg-slate-950/40 flex items-center justify-between">
              <span className="text-xs font-semibold text-slate-200 uppercase tracking-wider">
                Active Risks ({risks.length})
              </span>
              <AlertTriangle className="w-4 h-4 text-amber-500" />
            </div>
            <div className="p-4 space-y-4 divide-y divide-slate-900 overflow-y-auto max-h-[400px]">
              {risks.length > 0 ? (
                risks.map((risk: any, idx) => (
                  <div key={idx} className={`pt-4 ${idx === 0 ? 'pt-0' : ''} space-y-1`}>
                    <p className="text-slate-300 text-xs leading-relaxed font-medium">
                      {risk.description || risk.content}
                    </p>
                    <div className="flex items-center justify-between text-[10px] text-slate-500 pt-1">
                      <span className="text-rose-400">Severity: {risk.severity || 'HIGH'}</span>
                      <span>Category: {risk.category || 'Executive'}</span>
                    </div>
                  </div>
                ))
              ) : (
                <div className="text-center text-slate-600 text-xs py-8">No risks registered.</div>
              )}
            </div>
          </div>

          {/* Questions Feed */}
          <div className="glass rounded-xl border border-slate-800 overflow-hidden flex flex-col">
            <div className="p-5 border-b border-slate-900 bg-slate-950/40 flex items-center justify-between">
              <span className="text-xs font-semibold text-slate-200 uppercase tracking-wider">
                Follow-up Questions ({questions.length})
              </span>
              <HelpCircle className="w-4 h-4 text-blue-400" />
            </div>
            <div className="p-4 space-y-4 divide-y divide-slate-900 overflow-y-auto max-h-[400px]">
              {questions.length > 0 ? (
                questions.map((q: any, idx) => (
                  <div key={idx} className={`pt-4 ${idx === 0 ? 'pt-0' : ''} space-y-1`}>
                    <p className="text-slate-300 text-xs leading-relaxed font-medium">
                      {q.question_text || q.content}
                    </p>
                    <div className="flex items-center justify-between text-[10px] text-slate-500 pt-1">
                      <span>Priority: {q.priority || 'MEDIUM'}</span>
                      <span>Domain: {q.domain || 'Technology'}</span>
                    </div>
                  </div>
                ))
              ) : (
                <div className="text-center text-slate-600 text-xs py-8">No validation questions.</div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
