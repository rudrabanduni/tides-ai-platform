'use client';

import React from 'react';
import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';
import { Activity, CheckCircle2, Clock, FileStack, Loader2, ShieldAlert } from 'lucide-react';
import { Bar, BarChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { apiErrorMessage, applicationsApi } from '@/services/applications';
import { Card, ErrorBox, MockModeBanner, PageHeader, Spinner, StatusPill, formatDate, useRequireAuth } from '@/components/workflow/ui';

function toSeries(obj: Record<string, number> | undefined) {
  return Object.entries(obj || {}).map(([name, value]) => ({ name, value })).sort((a, b) => b.value - a.value);
}

export default function DashboardPage() {
  const user = useRequireAuth();
  const q = useQuery({
    queryKey: ['applicationsDashboard'],
    queryFn: () => applicationsApi.dashboard(),
    enabled: !!user,
    refetchInterval: 10_000,
  });
  if (!user) return null;
  const s = q.data;
  const cards = s
    ? [
        { label: 'Total applications', value: s.total_applications, icon: FileStack, testid: 'stat-total' },
        { label: 'Pending evaluation', value: s.pending_applications, icon: Clock, testid: 'stat-pending' },
        { label: 'Under evaluation', value: s.under_evaluation, icon: Loader2, testid: 'stat-running' },
        { label: 'Completed evaluations', value: s.completed_evaluations, icon: CheckCircle2, testid: 'stat-completed' },
        { label: 'Pending supervisory review', value: s.pending_supervisory_reviews, icon: ShieldAlert, testid: 'stat-supervisory' },
        { label: 'Blocked / failed', value: s.blocked_or_failed_evaluations, icon: Activity, testid: 'stat-blocked' },
      ]
    : [];
  return (
    <div>
      <MockModeBanner />
      <div className="mx-auto max-w-7xl p-8">
        <PageHeader
          title="Incubation Diligence Dashboard"
          subtitle="Technology Incubation and Entrepreneurship Development Society (TIEDS), IIT Roorkee"
          actions={<Link href="/applications/new" className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-500">New application</Link>}
        />
        {q.isLoading && <Spinner label="Loading dashboard…" />}
        {q.error && <ErrorBox message={apiErrorMessage(q.error, 'Dashboard unavailable.')} />}
        {s && (
          <>
            {s.synthetic_applications > 0 && (
              <p className="mb-4 text-xs text-amber-300" data-testid="synthetic-note">
                {s.synthetic_applications} of {s.total_applications} application(s) are synthetic demonstration records. Statistics below are computed from the database and include them.
              </p>
            )}
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {cards.map((c) => (
                <Card key={c.label}>
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold uppercase tracking-wide text-slate-500">{c.label}</span>
                    <c.icon className="h-4 w-4 text-slate-500" />
                  </div>
                  <div className="mt-2 text-3xl font-bold text-slate-100" data-testid={c.testid}>{c.value}</div>
                </Card>
              ))}
            </div>
            <div className="mt-6 grid gap-6 lg:grid-cols-3">
              <Card>
                <h2 className="mb-3 text-sm font-bold text-slate-200">Applications by sector</h2>
                {toSeries(s.sectors).length === 0 ? <p className="text-sm text-slate-500">No data yet.</p> : (
                  <ResponsiveContainer width="100%" height={200}>
                    <BarChart data={toSeries(s.sectors)} layout="vertical" margin={{ left: 20 }}>
                      <XAxis type="number" allowDecimals={false} stroke="#64748b" fontSize={11} />
                      <YAxis type="category" dataKey="name" stroke="#64748b" fontSize={11} width={90} />
                      <Tooltip contentStyle={{ background: '#0f172a', border: '1px solid #1e293b' }} />
                      <Bar dataKey="value" fill="#3b82f6" radius={[0, 4, 4, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                )}
              </Card>
              <Card>
                <h2 className="mb-3 text-sm font-bold text-slate-200">Applications by stage</h2>
                {toSeries(s.stages).length === 0 ? <p className="text-sm text-slate-500">No data yet.</p> : (
                  <ResponsiveContainer width="100%" height={200}>
                    <BarChart data={toSeries(s.stages)} layout="vertical" margin={{ left: 20 }}>
                      <XAxis type="number" allowDecimals={false} stroke="#64748b" fontSize={11} />
                      <YAxis type="category" dataKey="name" stroke="#64748b" fontSize={11} width={90} />
                      <Tooltip contentStyle={{ background: '#0f172a', border: '1px solid #1e293b' }} />
                      <Bar dataKey="value" fill="#6366f1" radius={[0, 4, 4, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                )}
              </Card>
              <Card>
                <h2 className="mb-3 text-sm font-bold text-slate-200">Recent activity</h2>
                <ul className="space-y-2" data-testid="recent-activity">
                  {s.recent_activity.map((a, i) => (
                    <li key={i} className="flex items-start justify-between gap-2 text-sm">
                      <div>
                        {a.type === 'evaluation' && a.evaluation_id ? (
                          <Link href={`/evaluations/run/${a.evaluation_id}`} className="text-slate-200 hover:text-blue-300">Evaluation · {a.startup_name}</Link>
                        ) : (
                          <Link href={`/applications/${a.application_id}`} className="text-slate-200 hover:text-blue-300">Application {a.application_ref} · {a.startup_name}</Link>
                        )}
                        <div className="text-xs text-slate-500">{formatDate(a.at)}</div>
                      </div>
                      <StatusPill status={a.status} />
                    </li>
                  ))}
                  {s.recent_activity.length === 0 && <li className="text-sm text-slate-500">No activity yet.</li>}
                </ul>
              </Card>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
