'use client';

import React, { useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/auth-context';
import { apiService } from '@/services/api';
import { 
  Rocket, 
  FileText, 
  CheckCircle, 
  Clock, 
  TrendingUp, 
  AlertTriangle,
  ArrowRight
} from 'lucide-react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line
} from 'recharts';

export default function DashboardPage() {
  const { user } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!user) {
      router.push('/login');
    }
  }, [user, router]);

  // Query stats
  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ['dashboardSummary'],
    queryFn: () => apiService.getDashboardSummary(),
    enabled: !!user,
  });

  // Query startups
  const { data: startups, isLoading: startupsLoading } = useQuery({
    queryKey: ['startups'],
    queryFn: () => apiService.getStartups(),
    enabled: !!user,
  });

  if (!user) return null;

  // Fallback defaults if database has no records yet
  const summaryCards = [
    {
      title: 'Total Startups',
      value: stats?.total_startups ?? startups?.length ?? 0,
      description: 'Ingested into engine',
      icon: Rocket,
      color: 'text-blue-500',
      bg: 'bg-blue-500/10 border-blue-500/20'
    },
    {
      title: 'AI Recommended',
      value: stats?.ai_recommended ?? 0,
      description: 'Scored above threshold',
      icon: CheckCircle,
      color: 'text-emerald-500',
      bg: 'bg-emerald-500/10 border-emerald-500/20'
    },
    {
      title: 'Pending Review',
      value: stats?.pending_committee_review ?? 0,
      description: 'Awaiting decision',
      icon: Clock,
      color: 'text-amber-500',
      bg: 'bg-amber-500/10 border-amber-500/20'
    },
    {
      title: 'Completed Reports',
      value: stats?.approved_startups ?? 0,
      description: 'With fully built graphs',
      icon: FileText,
      color: 'text-indigo-500',
      bg: 'bg-indigo-500/10 border-indigo-500/20'
    }
  ];

  // Pipeline Data (by stage)
  const pipelineData = [
    { name: 'Pre-Seed', value: startups?.filter(s => s.stage?.toLowerCase() === 'pre-seed').length || 0 },
    { name: 'Seed', value: startups?.filter(s => s.stage?.toLowerCase() === 'seed').length || 0 },
    { name: 'Series A', value: startups?.filter(s => s.stage?.toLowerCase() === 'series a').length || 0 }
  ];

  // Sector Data (by sector)
  const COLORS = ['#3b82f6', '#10b981', '#6366f1', '#f59e0b', '#ec4899'];
  const sectorMap: Record<string, number> = {};
  startups?.forEach(s => {
    const sName = s.sector || 'SaaS';
    sectorMap[sName] = (sectorMap[sName] || 0) + 1;
  });
  const sectorData = Object.keys(sectorMap).length > 0 
    ? Object.keys(sectorMap).map(k => ({ name: k, value: sectorMap[k] }))
    : [];

  // Group live startups dynamically by creation date for trend tracking
  const trendMap: Record<string, { month: string; reports: number; reviews: number }> = {};
  const startupsList = startups || [];
  startupsList.forEach((s) => {
    if (!s.created_at) return;
    const date = new Date(s.created_at);
    const monthName = date.toLocaleString('default', { month: 'short' });
    if (!trendMap[monthName]) {
      trendMap[monthName] = { month: monthName, reports: 0, reviews: 0 };
    }
    if (s.stage?.toLowerCase() === 'seed' || s.stage?.toLowerCase() === 'growth') {
      trendMap[monthName].reports += 1;
    } else {
      trendMap[monthName].reviews += 1;
    }
  });

  const trendData = Object.values(trendMap).length > 0
    ? Object.values(trendMap)
    : [];

  return (
    <div className="p-8 space-y-8 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-extrabold text-slate-100 tracking-tight">Incubator Dashboard</h1>
          <p className="text-slate-400 text-sm mt-1">Real-time status of multi-agent evaluations & pipeline rankings</p>
        </div>
        <button
          onClick={() => router.push('/upload')}
          className="bg-blue-600 hover:bg-blue-500 text-white rounded-lg px-4 py-2.5 font-semibold text-sm transition-all duration-150 flex items-center justify-center space-x-2 shadow-lg shadow-blue-500/10"
        >
          <span>Evaluate Startup</span>
          <ArrowRight className="w-4 h-4" />
        </button>
      </div>

      {/* Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {summaryCards.map((card) => {
          const Icon = card.icon;
          return (
            <div key={card.title} className={`glass rounded-xl p-6 border ${card.bg} relative overflow-hidden flex items-center justify-between`}>
              <div className="space-y-1">
                <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">{card.title}</span>
                <h3 className="text-3xl font-black text-slate-100">{card.value}</h3>
                <p className="text-xs text-slate-500">{card.description}</p>
              </div>
              <div className={`p-3 rounded-xl bg-slate-900 border border-slate-800/50 ${card.color}`}>
                <Icon className="w-6 h-6" />
              </div>
            </div>
          );
        })}
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Pipeline Distribution Chart */}
        <div className="glass rounded-xl p-6 border border-slate-800/50 flex flex-col space-y-4">
          <div>
            <h3 className="text-sm font-semibold text-slate-200 uppercase tracking-wider">Startup Stage Pipeline</h3>
            <span className="text-xs text-slate-500">Distribution of company stages</span>
          </div>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={pipelineData}>
                <XAxis dataKey="name" stroke="#64748b" fontSize={12} tickLine={false} />
                <YAxis stroke="#64748b" fontSize={12} tickLine={false} />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#1e293b' }}
                  labelStyle={{ color: '#f8fafc' }}
                />
                <Bar dataKey="value" fill="#3b82f6" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Sector Pie Chart */}
        <div className="glass rounded-xl p-6 border border-slate-800/50 flex flex-col space-y-4">
          <div>
            <h3 className="text-sm font-semibold text-slate-200 uppercase tracking-wider">Sector Distribution</h3>
            <span className="text-xs text-slate-500">Breakdown of portfolio industries</span>
          </div>
          <div className="h-64 flex items-center justify-center">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={sectorData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={80}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {sectorData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip 
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#1e293b' }}
                  itemStyle={{ color: '#f8fafc' }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="flex flex-wrap gap-x-4 gap-y-2 justify-center text-xs">
            {sectorData.map((d, index) => (
              <div key={d.name} className="flex items-center space-x-2">
                <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: COLORS[index % COLORS.length] }}></span>
                <span className="text-slate-400">{d.name}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Line Chart */}
        <div className="glass rounded-xl p-6 border border-slate-800/50 flex flex-col space-y-4">
          <div>
            <h3 className="text-sm font-semibold text-slate-200 uppercase tracking-wider">Evaluation Timelines</h3>
            <span className="text-xs text-slate-500">Reports and reviews completion history</span>
          </div>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={trendData}>
                <XAxis dataKey="month" stroke="#64748b" fontSize={12} tickLine={false} />
                <YAxis stroke="#64748b" fontSize={12} tickLine={false} />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#1e293b' }}
                  labelStyle={{ color: '#f8fafc' }}
                />
                <Line type="monotone" dataKey="reports" stroke="#6366f1" strokeWidth={2} dot={false} />
                <Line type="monotone" dataKey="reviews" stroke="#f59e0b" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Recent Activities Section */}
      <div className="glass rounded-xl border border-slate-800/50 overflow-hidden">
        <div className="p-6 border-b border-slate-900 flex items-center justify-between">
          <div>
            <h3 className="text-sm font-semibold text-slate-200 uppercase tracking-wider">Recent Evaluation Activity</h3>
            <span className="text-xs text-slate-500">Live feed of active analysis updates</span>
          </div>
          <button 
            onClick={() => router.push('/startups')}
            className="text-xs text-blue-400 hover:text-blue-300 font-medium"
          >
            View all startups
          </button>
        </div>

        <div className="divide-y divide-slate-900">
          {startupsLoading ? (
            <div className="p-6 text-center text-slate-500 text-sm">Loading activity list...</div>
          ) : startups && startups.length > 0 ? (
            startups.slice(0, 4).map((startup) => (
              <div key={startup.id} className="p-6 flex flex-col md:flex-row md:items-center justify-between gap-4 hover:bg-slate-900/10 transition-colors">
                <div className="flex items-start space-x-3">
                  <div className="bg-blue-500/10 text-blue-400 p-2.5 rounded-lg border border-blue-500/10">
                    <Rocket className="w-5 h-5" />
                  </div>
                  <div>
                    <h4 className="font-semibold text-slate-200 text-sm">{startup.startup_name}</h4>
                    <div className="flex flex-wrap items-center gap-x-2 text-xs text-slate-500 mt-1">
                      <span>{startup.sector}</span>
                      <span>•</span>
                      <span>{startup.stage}</span>
                      <span>•</span>
                      <span>Created {new Date(startup.created_at).toLocaleDateString()}</span>
                    </div>
                  </div>
                </div>
                <div className="flex items-center space-x-3">
                  <span className={`px-2.5 py-1 rounded-full text-xs font-semibold ${
                    startup.status === 'APPROVED' 
                      ? 'bg-emerald-500/10 text-emerald-400' 
                      : 'bg-amber-500/10 text-amber-400'
                  }`}>
                    {startup.status || 'INGESTED'}
                  </span>
                  <button
                    onClick={() => router.push(`/evaluations/${startup.id}`)}
                    className="p-1.5 hover:bg-slate-800 text-slate-400 hover:text-slate-200 rounded-lg transition-colors"
                  >
                    <ArrowRight className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))
          ) : (
            <div className="p-12 text-center text-slate-500 text-sm">
              No recent startup evaluations. Run your first analysis by clicking "Evaluate Startup".
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
