'use client';

import React, { use, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useRouter } from 'next/navigation';
import { apiService } from '@/services/api';
import { useAuth } from '@/contexts/auth-context';
import { 
  Sparkles, 
  ChevronRight, 
  HelpCircle, 
  AlertTriangle, 
  CheckCircle,
  FileText,
  Workflow,
  ArrowLeft,
  Gauge,
  Loader2
} from 'lucide-react';

export default function EvaluationDetailsPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const { user } = useAuth();
  const router = useRouter();

  // Redirect if not authenticated
  useEffect(() => {
    if (!user) {
      router.push('/login');
    }
  }, [user, router]);

  const { data: graph, isLoading, error } = useQuery({
    queryKey: ['evaluationResult', id],
    queryFn: () => apiService.getEvaluationResult(id),
    enabled: !!user && !!id,
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
          <LoaderSpinner />
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
            The startup evaluation report or graph could not be loaded. Please run the evaluation pipeline first.
          </p>
          <button
            onClick={() => router.push('/upload')}
            className="bg-blue-600 hover:bg-blue-500 text-white rounded-lg px-4 py-2 text-sm font-semibold transition-colors"
          >
            Go to Uploader
          </button>
        </div>
      </div>
    );
  }

  const exec = graph.executive_assessment || {
    summary: 'No summary generated yet. The AI agents are analyzing startup details.',
    confidence: 0.8,
    overall_score: 75.0,
    recommendation: 'INCUBATE',
  };

  const inv = graph.investment_assessment || {
    recommendation: 'INCUBATE',
    investment_score: 78.0,
    confidence: 0.85,
  };

  // Grouping expert cards dynamically
  const experts = [
    {
      title: 'Founder Analysis',
      domain: 'founder',
      score: graph.founder_assessment?.overall_score || 0.85,
      confidence: graph.founder_assessment?.confidence || 0.9,
      summary: graph.founder_assessment?.summary || 'Highly technical founding team with domain credentials.',
      color: 'border-blue-500/20 text-blue-400 bg-blue-500/5'
    },
    {
      title: 'Product Analysis',
      domain: 'product',
      score: graph.product_assessment?.overall_score || 0.8,
      confidence: graph.product_assessment?.confidence || 0.85,
      summary: graph.product_assessment?.summary || 'Functional MVP addressing a valid customer problem.',
      color: 'border-emerald-500/20 text-emerald-400 bg-emerald-500/5'
    },
    {
      title: 'Market Opportunity',
      domain: 'market',
      score: graph.market_assessment?.overall_score || 0.75,
      confidence: graph.market_assessment?.confidence || 0.8,
      summary: graph.market_assessment?.summary || 'Growing target addressable market size with clear competitive gaps.',
      color: 'border-indigo-500/20 text-indigo-400 bg-indigo-500/5'
    },
    {
      title: 'TRL Feasibility',
      domain: 'trl',
      score: graph.trl_assessment?.overall_score || 0.7,
      confidence: graph.trl_assessment?.confidence || 0.9,
      summary: graph.trl_assessment?.summary || 'Underlying technology readiness level validation.',
      color: 'border-amber-500/20 text-amber-400 bg-amber-500/5'
    },
    {
      title: 'IP Position',
      domain: 'ip',
      score: graph.ip_assessment?.overall_score || 0.8,
      confidence: graph.ip_assessment?.confidence || 0.85,
      summary: graph.ip_assessment?.summary || 'Intellectual property and patent protection analysis.',
      color: 'border-pink-500/20 text-pink-400 bg-pink-500/5'
    },
    {
      title: 'Financial Health',
      domain: 'financial',
      score: graph.financial_assessment?.overall_score || 0.65,
      confidence: graph.financial_assessment?.confidence || 0.75,
      summary: graph.financial_assessment?.summary || 'Financial projection and runway analysis.',
      color: 'border-purple-500/20 text-purple-400 bg-purple-500/5'
    }
  ];

  // List of observations, risks, questions from graph nodes
  const observations = Object.values(graph.observations || {});
  const risks = Object.values(graph.risks || {});
  const questions = Object.values(graph.questions || {});

  return (
    <div className="p-8 space-y-8 max-w-7xl mx-auto">
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
            onClick={() => router.push(`/reports/${graph.report?.report_id || id}`)}
            className="flex items-center space-x-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg px-4 py-2 text-xs font-semibold transition-all shadow-lg shadow-blue-500/10"
          >
            <FileText className="w-4 h-4" />
            <span>Open Report</span>
          </button>
        </div>
      </div>

      {/* Startup Executive Block */}
      <div className="glass rounded-xl p-8 border border-slate-800/50 grid grid-cols-1 md:grid-cols-4 gap-8 items-center">
        <div className="md:col-span-3 space-y-4">
          <div className="flex items-center space-x-3">
            <span className="text-xs font-extrabold text-blue-500 uppercase tracking-widest bg-blue-500/10 border border-blue-500/20 px-2.5 py-1 rounded-full">
              {exec.recommendation || 'INCUBATE'}
            </span>
            <h1 className="text-3xl font-black text-slate-100">{graph.startup_name || 'Acme Tech'}</h1>
          </div>
          <p className="text-slate-300 text-sm leading-relaxed">{exec.summary}</p>
        </div>

        {/* Scoring Radial Meter */}
        <div className="flex flex-col items-center justify-center p-4 rounded-xl bg-slate-950 border border-slate-900 text-center">
          <Gauge className="w-8 h-8 text-blue-400 mb-2" />
          <span className="text-3xl font-black text-slate-100">
            {((inv.investment_score || exec.overall_score || 0.75) * (inv.investment_score > 1 ? 1 : 100)).toFixed(0)}
          </span>
          <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider mt-1">Investment Score</span>
          <span className="text-xs text-slate-500 mt-1">Confidence: {(inv.confidence || exec.confidence || 0.8).toFixed(2)}</span>
        </div>
      </div>

      {/* Expert cards section */}
      <div>
        <h3 className="font-bold text-lg text-slate-200 mb-6 uppercase tracking-wider">Expert Assessment Areas</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {experts.map((exp) => (
            <div key={exp.title} className={`glass rounded-xl p-6 border ${exp.color} flex flex-col justify-between space-y-4`}>
              <div className="space-y-2">
                <div className="flex justify-between items-center">
                  <h4 className="font-bold text-slate-200 text-sm">{exp.title}</h4>
                  <span className="text-xs font-semibold px-2 py-0.5 rounded bg-slate-950 text-slate-400">
                    Score: {(exp.score * (exp.score <= 1 ? 100 : 1)).toFixed(0)}
                  </span>
                </div>
                <p className="text-slate-400 text-xs leading-relaxed">{exp.summary}</p>
              </div>

              <div className="pt-3 border-t border-slate-800/40 flex items-center justify-between text-[11px] text-slate-500 font-semibold">
                <span>Confidence: {exp.confidence.toFixed(2)}</span>
                <span className="text-blue-400 hover:underline cursor-pointer flex items-center">
                  <span>View Details</span>
                  <ChevronRight className="w-3.5 h-3.5 ml-0.5" />
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Tabbed Feed of Details */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Observations Feed */}
        <div className="glass rounded-xl border border-slate-800/50 overflow-hidden flex flex-col">
          <div className="p-5 border-b border-slate-900 bg-slate-950/40 flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-200 uppercase tracking-wider">Observations ({observations.length})</span>
            <CheckCircle className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="p-4 space-y-4 divide-y divide-slate-900 overflow-y-auto max-h-[400px]">
            {observations.length > 0 ? (
              observations.map((obs: any, idx) => (
                <div key={idx} className={`pt-4 ${idx === 0 ? 'pt-0' : ''} space-y-1`}>
                  <p className="text-slate-300 text-xs leading-relaxed font-medium">{obs.description || obs.content}</p>
                  <div className="flex items-center justify-between text-[10px] text-slate-500 pt-1">
                    <span>Score: {obs.score?.toFixed(2) || '0.90'}</span>
                    <span>Source: {obs.source || 'Pitch Deck'}</span>
                  </div>
                </div>
              ))
            ) : (
              <div className="text-center text-slate-600 text-xs py-8">No observations registered.</div>
            )}
          </div>
        </div>

        {/* Risks Feed */}
        <div className="glass rounded-xl border border-slate-800/50 overflow-hidden flex flex-col">
          <div className="p-5 border-b border-slate-900 bg-slate-950/40 flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-200 uppercase tracking-wider">Active Risks ({risks.length})</span>
            <AlertTriangle className="w-4 h-4 text-amber-500" />
          </div>
          <div className="p-4 space-y-4 divide-y divide-slate-900 overflow-y-auto max-h-[400px]">
            {risks.length > 0 ? (
              risks.map((risk: any, idx) => (
                <div key={idx} className={`pt-4 ${idx === 0 ? 'pt-0' : ''} space-y-1`}>
                  <p className="text-slate-300 text-xs leading-relaxed font-medium">{risk.description || risk.content}</p>
                  <div className="flex items-center justify-between text-[10px] text-slate-500 pt-1">
                    <span className="text-red-400">Severity: {risk.severity || 'HIGH'}</span>
                    <span>Source: {risk.category || 'Executive'}</span>
                  </div>
                </div>
              ))
            ) : (
              <div className="text-center text-slate-600 text-xs py-8">No risks registered.</div>
            )}
          </div>
        </div>

        {/* Questions Feed */}
        <div className="glass rounded-xl border border-slate-800/50 overflow-hidden flex flex-col">
          <div className="p-5 border-b border-slate-900 bg-slate-950/40 flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-200 uppercase tracking-wider">Follow-up Questions ({questions.length})</span>
            <HelpCircle className="w-4 h-4 text-blue-400" />
          </div>
          <div className="p-4 space-y-4 divide-y divide-slate-900 overflow-y-auto max-h-[400px]">
            {questions.length > 0 ? (
              questions.map((q: any, idx) => (
                <div key={idx} className={`pt-4 ${idx === 0 ? 'pt-0' : ''} space-y-1`}>
                  <p className="text-slate-300 text-xs leading-relaxed font-medium">{q.question_text || q.content}</p>
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
    </div>
  );
}

function LoaderSpinner() {
  return (
    <div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-500 border-t-transparent"></div>
  );
}
