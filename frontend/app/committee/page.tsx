'use client';

import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { apiService } from '@/services/api';
import { useAuth } from '@/contexts/auth-context';
import { 
  Users, 
  CheckCircle2, 
  HelpCircle, 
  AlertCircle, 
  Scale, 
  FileText,
  BadgeAlert,
  ThumbsUp,
  SlidersHorizontal
} from 'lucide-react';
import { CommitteeDecision } from '@/types';

export default function CommitteePage() {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState<'all' | 'incubate' | 'deferred' | 'pending'>('all');

  const { data: decisions = [], isLoading } = useQuery({
    queryKey: ['committeeDecisions'],
    queryFn: () => apiService.getCommittee(),
    enabled: !!user,
  });

  if (!user) return null;

  // Grouping counts
  const incubateCount = decisions.filter(d => d.recommendation === 'INCUBATE').length;
  const deferredCount = decisions.filter(d => d.recommendation === 'DEFER').length;
  const pendingCount = decisions.filter(d => d.recommendation === 'SEEK_MORE_INFORMATION' || d.recommendation === 'INCUBATE_AFTER_DD').length;

  const filteredDecisions = decisions.filter((d) => {
    if (activeTab === 'incubate') return d.recommendation === 'INCUBATE';
    if (activeTab === 'deferred') return d.recommendation === 'DEFER';
    if (activeTab === 'pending') return d.recommendation === 'SEEK_MORE_INFORMATION' || d.recommendation === 'INCUBATE_AFTER_DD';
    return true;
  });

  return (
    <div className="p-8 space-y-8 max-w-7xl mx-auto">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-extrabold text-slate-100 tracking-tight">Investment Committee</h1>
        <p className="text-slate-400 text-sm mt-1">Review applicant consensus details, conditions, and priority scores</p>
      </div>

      {/* Tabs / Filter Pills */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-900 pb-2">
        <div className="flex space-x-2">
          {(['all', 'incubate', 'deferred', 'pending'] as const).map((tab) => {
            const label = tab.charAt(0).toUpperCase() + tab.slice(1);
            let count = decisions.length;
            if (tab === 'incubate') count = incubateCount;
            if (tab === 'deferred') count = deferredCount;
            if (tab === 'pending') count = pendingCount;

            const isActive = activeTab === tab;
            return (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-4 py-2 rounded-lg text-xs font-semibold transition-all ${
                  isActive
                    ? 'bg-blue-600 text-white'
                    : 'bg-slate-900/40 text-slate-400 hover:text-slate-200 hover:bg-slate-900 border border-slate-900'
                }`}
              >
                {label} ({count})
              </button>
            );
          })}
        </div>

        <div className="text-xs text-slate-500 flex items-center space-x-1.5">
          <Scale className="w-4 h-4 text-slate-400" />
          <span>Consensus threshold: 70%</span>
        </div>
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-8">
        {/* Decisions List (Left) */}
        <div className="xl:col-span-2 space-y-6">
          {isLoading ? (
            <div className="text-center py-12 text-slate-500">
              <span className="h-6 w-6 animate-spin rounded-full border-2 border-slate-500 border-t-transparent inline-block"></span>
            </div>
          ) : filteredDecisions.length > 0 ? (
            filteredDecisions.map((decision) => (
              <div key={decision.decision_id} className="glass rounded-xl border border-slate-800/50 p-6 space-y-4 hover:border-slate-700/50 transition-colors">
                <div className="flex items-start justify-between gap-4">
                  <div className="space-y-1">
                    <h3 className="font-bold text-base text-slate-100">{decision.startup_name}</h3>
                    <p className="text-slate-400 text-xs leading-relaxed">{decision.decision_reasoning}</p>
                  </div>

                  <span className={`px-2.5 py-1 rounded-full text-[10px] font-extrabold uppercase tracking-wider ${
                    decision.recommendation === 'INCUBATE'
                      ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                      : 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                  }`}>
                    {decision.recommendation}
                  </span>
                </div>

                {/* Priority Stats Grid */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 bg-slate-950/40 p-4 rounded-lg text-center text-xs">
                  <div>
                    <span className="text-slate-500 block uppercase tracking-wider text-[10px] font-semibold">Incubation</span>
                    <span className="text-slate-300 font-bold mt-1 block">{decision.incubation_priority}</span>
                  </div>
                  <div>
                    <span className="text-slate-500 block uppercase tracking-wider text-[10px] font-semibold">Investment</span>
                    <span className="text-slate-300 font-bold mt-1 block">{decision.investment_priority}</span>
                  </div>
                  <div>
                    <span className="text-slate-500 block uppercase tracking-wider text-[10px] font-semibold">Grant Option</span>
                    <span className="text-slate-300 font-bold mt-1 block">{decision.grant_priority}</span>
                  </div>
                  <div>
                    <span className="text-slate-500 block uppercase tracking-wider text-[10px] font-semibold">Consensus Score</span>
                    <span className="text-blue-400 font-black mt-1 block">{(decision.decision_confidence * 100).toFixed(0)}%</span>
                  </div>
                </div>

                {/* Notes and Conditions */}
                {decision.committee_notes && (
                  <div className="border-t border-slate-900 pt-3 text-xs text-slate-400 flex items-start space-x-2">
                    <FileText className="w-4 h-4 text-slate-500 mt-0.5 flex-shrink-0" />
                    <span><strong className="text-slate-300">Notes:</strong> {decision.committee_notes}</span>
                  </div>
                )}
              </div>
            ))
          ) : (
            <div className="text-center py-12 text-slate-500 text-sm">
              No applicant decisions registered under this category.
            </div>
          )}
        </div>

        {/* Panel of Active Committee (Right) */}
        <div className="space-y-6">
          <div className="glass rounded-xl p-6 border border-slate-800/50 space-y-4">
            <h4 className="font-bold text-sm text-slate-200 uppercase tracking-wider flex items-center space-x-2">
              <Users className="w-5 h-5 text-blue-400" />
              <span>Incubation Board</span>
            </h4>
            <div className="divide-y divide-slate-900 text-xs">
              <div className="py-3 flex items-center justify-between">
                <div>
                  <h5 className="font-semibold text-slate-300">Dr. Sarah Jenkins</h5>
                  <span className="text-[10px] text-slate-500">General Partner (DeepTech)</span>
                </div>
                <ThumbsUp className="w-4 h-4 text-emerald-400" />
              </div>
              <div className="py-3 flex items-center justify-between">
                <div>
                  <h5 className="font-semibold text-slate-300">Michael Chang</h5>
                  <span className="text-[10px] text-slate-500">Managing Director</span>
                </div>
                <ThumbsUp className="w-4 h-4 text-emerald-400" />
              </div>
              <div className="py-3 flex items-center justify-between">
                <div>
                  <h5 className="font-semibold text-slate-300">Amanda Ross</h5>
                  <span className="text-[10px] text-slate-500">Principal Investment Manager</span>
                </div>
                <ThumbsUp className="w-4 h-4 text-emerald-400" />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
