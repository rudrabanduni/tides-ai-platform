'use client';

import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { apiService } from '@/services/api';
import { useAuth } from '@/contexts/auth-context';
import { 
  TrendingUp, 
  Award, 
  ShieldAlert, 
  Compass,
  ArrowRight,
  SlidersHorizontal,
  ChevronDown
} from 'lucide-react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip
} from 'recharts';

export default function PortfolioPage() {
  const { user } = useAuth();
  const [sectorFilter, setSectorFilter] = useState('');

  const { data: portfolio, isLoading } = useQuery({
    queryKey: ['portfolioData'],
    queryFn: () => apiService.getPortfolio(),
    enabled: !!user,
  });

  if (!user) return null;

  const entries = portfolio?.entries || [];
  const stats = portfolio?.statistics || {
    total_startups: entries.length || 6,
    average_score: 74.5,
    highest_score: 85.0,
    lowest_score: 62.0,
  };

  const filteredEntries = sectorFilter 
    ? entries.filter(e => e.category.toLowerCase() === sectorFilter.toLowerCase())
    : entries;

  // Sorting: highest score first (rank order)
  const sortedEntries = [...filteredEntries].sort((a, b) => a.rank - b.rank);

  // Chart data mapping
  const chartData = sortedEntries.map(e => ({
    name: e.startup_name,
    score: (e.overall_score * (e.overall_score <= 1 ? 100 : 1)),
  }));

  const sectorsList = Array.from(new Set(entries.map(e => e.category))).filter(Boolean);

  return (
    <div className="p-8 space-y-8 max-w-7xl mx-auto">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-extrabold text-slate-100 tracking-tight">Portfolio Intelligence</h1>
        <p className="text-slate-400 text-sm mt-1">Venture leaderboards, ranking comparisons, and risk profiles</p>
      </div>

      {/* Summary grid */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="glass rounded-xl p-5 border border-slate-800/40 space-y-1">
          <span className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider">Total Companies</span>
          <h3 className="text-2xl font-black text-slate-100">{stats.total_startups}</h3>
        </div>
        <div className="glass rounded-xl p-5 border border-slate-800/40 space-y-1">
          <span className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider">Average Score</span>
          <h3 className="text-2xl font-black text-blue-400">{stats.average_score.toFixed(1)}</h3>
        </div>
        <div className="glass rounded-xl p-5 border border-slate-800/40 space-y-1">
          <span className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider">Highest Scored</span>
          <h3 className="text-2xl font-black text-emerald-400">{stats.highest_score.toFixed(1)}</h3>
        </div>
        <div className="glass rounded-xl p-5 border border-slate-800/40 space-y-1">
          <span className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider">Lowest Scored</span>
          <h3 className="text-2xl font-black text-rose-500">{stats.lowest_score.toFixed(1)}</h3>
        </div>
      </div>

      {/* Grid: Charts + Rankings */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-8">
        {/* Rankings leaderboard (Left) */}
        <div className="xl:col-span-2 space-y-6">
          <div className="glass rounded-xl border border-slate-800/50 overflow-hidden">
            <div className="p-6 border-b border-slate-900 flex items-center justify-between">
              <div>
                <h3 className="text-sm font-semibold text-slate-200 uppercase tracking-wider">Incubator Leaderboard</h3>
                <span className="text-[10px] text-slate-500">Ranked by investment consensus criteria</span>
              </div>

              {/* Filter */}
              <div className="relative">
                <select
                  value={sectorFilter ?? ""}
                  onChange={(e) => setSectorFilter(e.target.value)}
                  className="bg-slate-900 border border-slate-800 rounded-lg px-3 py-1.5 text-slate-300 text-xs focus:outline-none cursor-pointer appearance-none pr-8"
                >
                  <option value="">All Sectors</option>
                  {sectorsList.map(s => (
                    <option key={s} value={s}>{s}</option>
                  ))}
                </select>
                <ChevronDown className="w-3.5 h-3.5 text-slate-500 absolute right-2.5 top-1/2 -translate-y-1/2 pointer-events-none" />
              </div>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="border-b border-slate-900 text-[10px] font-semibold text-slate-500 uppercase tracking-wider bg-slate-950/40">
                    <th className="py-3 px-6">Rank</th>
                    <th className="py-3 px-6">Startup</th>
                    <th className="py-3 px-6">Category</th>
                    <th className="py-3 px-6">Score</th>
                    <th className="py-3 px-6">Confidence</th>
                    <th className="py-3 px-6 text-right">Risks</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-900 text-xs text-slate-300">
                  {isLoading ? (
                    <tr>
                      <td colSpan={6} className="py-12 text-center text-slate-500">
                        <span className="h-5 w-5 animate-spin rounded-full border-2 border-slate-500 border-t-transparent inline-block"></span>
                      </td>
                    </tr>
                  ) : sortedEntries.length > 0 ? (
                    sortedEntries.map((entry) => (
                      <tr key={entry.startup_id} className="hover:bg-slate-900/10 transition-colors">
                        <td className="py-4 px-6 font-black text-slate-400">
                          {entry.rank === 1 ? (
                            <Award className="w-4 h-4 text-amber-500 inline-block mr-1" />
                          ) : null}
                          <span>#{entry.rank}</span>
                        </td>
                        <td className="py-4 px-6 font-semibold text-slate-100">{entry.startup_name}</td>
                        <td className="py-4 px-6">{entry.category}</td>
                        <td className="py-4 px-6 font-bold text-blue-400">
                          {(entry.overall_score * (entry.overall_score <= 1 ? 100 : 1)).toFixed(0)}
                        </td>
                        <td className="py-4 px-6">{(entry.graph_confidence || 0.8).toFixed(2)}</td>
                        <td className="py-4 px-6 text-right font-medium text-rose-500">
                          {entry.active_risk_count || 0}
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan={6} className="py-12 text-center text-slate-500">
                        No portfolio entries present.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Charts column (Right) */}
        <div className="space-y-6">
          <div className="glass rounded-xl p-6 border border-slate-800/50 flex flex-col space-y-4">
            <div>
              <h4 className="font-bold text-sm text-slate-200 uppercase tracking-wider flex items-center space-x-2">
                <TrendingUp className="w-5 h-5 text-blue-400" />
                <span>Score Comparison</span>
              </h4>
              <span className="text-[10px] text-slate-500 mt-1 block">Quick overview of scored applicant companies</span>
            </div>
            {chartData.length > 0 ? (
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={chartData}>
                    <XAxis dataKey="name" stroke="#475569" fontSize={10} tickLine={false} />
                    <YAxis stroke="#475569" fontSize={10} tickLine={false} />
                    <Tooltip 
                      contentStyle={{ backgroundColor: '#0f172a', borderColor: '#1e293b' }}
                      labelStyle={{ color: '#f8fafc' }}
                    />
                    <Bar dataKey="score" fill="#6366f1" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <div className="text-center py-12 text-slate-600 text-xs">No graph comparison details.</div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
