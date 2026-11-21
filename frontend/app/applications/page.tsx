'use client';

import React, { useMemo, useState } from 'react';
import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';
import { Plus } from 'lucide-react';
import { apiErrorMessage, applicationsApi } from '@/services/applications';
import { Card, ErrorBox, MockModeBanner, PageHeader, Spinner, StatusPill, formatDate, useRequireAuth } from '@/components/workflow/ui';

export default function ApplicationsPage() {
  const user = useRequireAuth();
  const [query, setQuery] = useState('');
  const q = useQuery({ queryKey: ['applications'], queryFn: () => applicationsApi.list(), enabled: !!user });
  const rows = useMemo(
    () => (q.data || []).filter((a) => `${a.company_name} ${a.application_ref} ${a.sector} ${a.stage}`.toLowerCase().includes(query.toLowerCase())),
    [q.data, query],
  );
  if (!user) return null;
  return (
    <div>
      <MockModeBanner />
      <div className="mx-auto max-w-7xl p-8">
        <PageHeader
          title="Startup Portfolio"
          subtitle="Every submitted incubation application and its latest evaluation"
          actions={<Link href="/applications/new" data-testid="new-application" className="flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-500"><Plus className="h-4 w-4" /> New application</Link>}
        />
        <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search company, reference, sector…" className="mb-4 w-full max-w-sm rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-slate-100" />
        {q.isLoading && <Spinner />}
        {q.error && <ErrorBox message={apiErrorMessage(q.error)} />}
        {q.data && (
          <Card className="p-0">
            <table className="w-full text-left text-sm">
              <thead className="border-b border-slate-800 text-xs uppercase tracking-wide text-slate-500">
                <tr><th className="px-4 py-3">Company</th><th>Reference</th><th>Sector / stage</th><th>Documents</th><th>Submitted</th><th>Evaluation</th></tr>
              </thead>
              <tbody className="divide-y divide-slate-800/70">
                {rows.map((a) => (
                  <tr key={a.id} className="hover:bg-slate-900/80">
                    <td className="px-4 py-3">
                      <Link href={`/applications/${a.id}`} className="font-semibold text-blue-300 hover:underline">{a.company_name}</Link>
                      {a.is_synthetic && <span className="ml-2 rounded bg-amber-500/15 px-1.5 py-0.5 text-[10px] font-bold text-amber-300">SYNTHETIC</span>}
                    </td>
                    <td className="font-mono text-xs text-slate-400">{a.application_ref}</td>
                    <td className="text-slate-300">{a.sector} · {a.stage}</td>
                    <td className="text-slate-300">{a.document_count}</td>
                    <td className="text-xs text-slate-400">{formatDate(a.created_at)}</td>
                    <td>{a.latest_run_id ? <Link href={`/evaluations/run/${a.latest_run_id}`}><StatusPill status={a.latest_run_status} /></Link> : <StatusPill status="NOT STARTED" />}</td>
                  </tr>
                ))}
                {rows.length === 0 && <tr><td colSpan={6} className="px-4 py-8 text-center text-slate-500">No applications yet. Submit the first one with “New application”.</td></tr>}
              </tbody>
            </table>
          </Card>
        )}
      </div>
    </div>
  );
}
