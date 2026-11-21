'use client';

import React, { useRef, useState } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { ArrowRight, FileText, Play, RotateCcw, UploadCloud } from 'lucide-react';
import {
  DOCUMENT_TYPES,
  EvaluationRun,
  RunStage,
  apiErrorMessage,
  applicationsApi,
  validateUploadFile,
} from '@/services/applications';
import { Card, ErrorBox, MockModeBanner, PageHeader, Spinner, StageIcon, StatusPill, formatDate, useRequireAuth } from '@/components/workflow/ui';

const GROUP_LABELS: Record<string, string> = {
  intake: 'Intake',
  extraction: 'Document extraction, claims & evidence',
  domains: 'Six domain specialists',
  supervisory: 'Supervisory review',
  report: 'Report, validation & PDF',
};

function RunProgress({ run }: { run: EvaluationRun }) {
  const groups = Object.keys(GROUP_LABELS);
  const byGroup = (g: string) => run.stages.filter((s) => s.group === g);
  const extraction = run.stages.filter((s) => s.key.startsWith('extraction:'));
  const domains = run.stages.filter((s) => s.key.startsWith('domain:'));
  return (
    <div className="space-y-4" data-testid="run-progress">
      <div>
        <div className="mb-1 flex justify-between text-xs text-slate-400">
          <span>{run.current_stage || run.status}</span>
          <span data-testid="progress-pct">{run.progress_pct}%</span>
        </div>
        <div className="h-2 overflow-hidden rounded bg-slate-800">
          <div className={`h-full transition-all ${run.status === 'FAILED' ? 'bg-red-500' : run.status === 'BLOCKED' ? 'bg-amber-500' : 'bg-blue-500'}`} style={{ width: `${run.progress_pct}%` }} />
        </div>
        <div className="mt-2 flex flex-wrap gap-4 text-xs text-slate-400">
          <span>Extraction: {extraction.filter((s) => s.status === 'SUCCESS').length}/{extraction.length} stages</span>
          <span>Domains: {domains.filter((s) => s.status === 'SUCCESS').length}/{domains.length}</span>
          {run.summary?.coverage && <span>Criteria: {run.summary.coverage.total_present}/{run.summary.coverage.total_expected}</span>}
          <span>Provider spend: ${run.cost_usd.toFixed(4)}</span>
        </div>
      </div>
      <div className="grid gap-3 md:grid-cols-2">
        {groups.map((g) => (
          <div key={g} className="rounded-lg border border-slate-800 p-3">
            <div className="mb-2 text-xs font-bold uppercase tracking-wide text-slate-400">{GROUP_LABELS[g]}</div>
            <ul className="space-y-1.5">
              {byGroup(g).map((s: RunStage) => (
                <li key={s.key} className="flex items-start gap-2 text-xs" data-testid={`stage-${s.key}`} data-status={s.status}>
                  <StageIcon status={s.status} />
                  <span className={s.status === 'PENDING' ? 'text-slate-500' : 'text-slate-200'}>{s.label}</span>
                  {s.detail?.criteria_assessed !== undefined && (
                    <span className="ml-auto text-slate-500">{s.detail.criteria_assessed}/{s.detail.criteria_total}</span>
                  )}
                  {s.detail?.error && <span className="ml-auto max-w-[50%] truncate text-red-400" title={s.detail.error}>{s.detail.error}</span>}
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
      {run.error_message && <ErrorBox message={run.error_message} />}
    </div>
  );
}

export default function ApplicationDetailPage() {
  const user = useRequireAuth();
  const params = useParams<{ id: string }>();
  const id = String(params?.id || '');
  const qc = useQueryClient();
  const fileInput = useRef<HTMLInputElement>(null);
  const [docType, setDocType] = useState('pitch_deck');
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  const appQuery = useQuery({
    queryKey: ['application', id],
    queryFn: () => applicationsApi.get(id),
    enabled: !!user && !!id,
  });
  const runId = appQuery.data?.latest_run?.id;
  const runQuery = useQuery({
    queryKey: ['run', runId],
    queryFn: () => applicationsApi.getRun(runId as string),
    enabled: !!runId,
    // Poll the database-backed run row only while the evaluation is active.
    refetchInterval: (q) => (q.state.data && ['QUEUED', 'RUNNING'].includes(q.state.data.status) ? 1500 : false),
  });

  const start = useMutation({
    mutationFn: (rerun: boolean) => applicationsApi.startEvaluation(id, rerun),
    onSuccess: (run) => {
      setActionError(null);
      qc.setQueryData(['run', run.id], run);
      qc.invalidateQueries({ queryKey: ['application', id] });
    },
    onError: (err) => setActionError(apiErrorMessage(err, 'Could not start the evaluation.')),
  });

  const upload = async (files: FileList | null) => {
    if (!files?.length) return;
    setUploadError(null);
    for (const f of Array.from(files)) {
      const local = validateUploadFile(f);
      if (local) { setUploadError(`${f.name}: ${local}`); continue; }
      try {
        await applicationsApi.uploadDocument(id, f, docType);
      } catch (err) {
        setUploadError(`${f.name}: ${apiErrorMessage(err, 'Upload failed.')}`);
      }
    }
    if (fileInput.current) fileInput.current.value = '';
    qc.invalidateQueries({ queryKey: ['application', id] });
  };

  if (!user) return null;
  if (appQuery.isLoading) return <div className="p-8"><Spinner label="Loading application…" /></div>;
  if (appQuery.error || !appQuery.data) return <div className="p-8"><ErrorBox message={apiErrorMessage(appQuery.error, 'Application not found.')} /></div>;

  const app = appQuery.data;
  const run = runQuery.data || app.latest_run;
  const active = run && ['QUEUED', 'RUNNING'].includes(run.status);

  return (
    <div>
      <MockModeBanner />
      <div className="mx-auto max-w-6xl p-8">
        <PageHeader
          title={app.company_name}
          subtitle={<span>Application <span className="font-mono text-slate-300">{app.application_ref}</span> · {app.sector} · {app.stage} · submitted {formatDate(app.submitted_at)}{app.is_synthetic && <span className="ml-2 rounded bg-amber-500/15 px-1.5 py-0.5 text-[11px] font-bold text-amber-300">SYNTHETIC</span>}</span>}
          actions={<StatusPill status={app.status} />}
        />

        <div className="grid gap-6 lg:grid-cols-3">
          <div className="space-y-6 lg:col-span-2">
            <Card>
              <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
                <h2 className="text-sm font-bold text-slate-200">Evaluation</h2>
                <div className="flex gap-2">
                  {!run && (
                    <button data-testid="start-evaluation" disabled={start.isPending || app.documents.length === 0} onClick={() => start.mutate(false)} className="flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-500 disabled:opacity-40">
                      <Play className="h-4 w-4" /> {start.isPending ? 'Starting…' : 'Start evaluation'}
                    </button>
                  )}
                  {run && !active && run.status !== 'COMPLETED' && (
                    <button onClick={() => start.mutate(true)} className="flex items-center gap-2 rounded-lg border border-slate-700 px-3 py-2 text-xs font-semibold text-slate-200 hover:bg-slate-800">
                      <RotateCcw className="h-4 w-4" /> Start a new run
                    </button>
                  )}
                  {run?.status === 'COMPLETED' && (
                    <Link href={`/evaluations/run/${run.id}`} data-testid="open-results" className="flex items-center gap-2 rounded-lg bg-emerald-600 px-4 py-2 text-sm font-semibold text-white hover:bg-emerald-500">
                      View assessment &amp; report <ArrowRight className="h-4 w-4" />
                    </Link>
                  )}
                  {run && (run.status === 'BLOCKED' || run.status === 'FAILED') && (
                    <Link href={`/evaluations/run/${run.id}`} className="rounded-lg border border-slate-700 px-3 py-2 text-xs font-semibold text-slate-300 hover:bg-slate-800">Inspect partial results</Link>
                  )}
                </div>
              </div>
              {app.documents.length === 0 && !run && <p className="text-sm text-amber-300">Upload at least one document before starting the evaluation.</p>}
              {actionError && <ErrorBox message={actionError} />}
              {run ? (
                <div>
                  <div className="mb-3 flex flex-wrap items-center gap-3 text-xs text-slate-400">
                    <StatusPill status={run.status} />
                    <span>Evaluation ID <span className="font-mono text-slate-300" data-testid="evaluation-id">{run.id}</span></span>
                    <span>Mode: {run.mode === 'MOCK_DEMONSTRATION' ? 'Offline mock demonstration' : 'Live provider'}</span>
                  </div>
                  <RunProgress run={run} />
                </div>
              ) : (
                <p className="text-sm text-slate-500">No evaluation has been started for this application.</p>
              )}
            </Card>

            <Card>
              <h2 className="mb-3 text-sm font-bold text-slate-200">Application details</h2>
              <dl className="grid gap-x-6 gap-y-3 text-sm md:grid-cols-2">
                {([
                  ['Problem statement', app.problem_statement], ['Proposed solution', app.proposed_solution],
                  ['Product & technology', app.product_technology], ['Target market', app.target_market],
                  ['Business model', app.business_model], ['Traction', app.traction],
                  ['Revenue', app.revenue_information], ['Financial information', app.financial_information],
                  ['Funding requirement', app.funding_requirement], ['Incubation support', app.incubation_support_requirement],
                  ['Industry', app.industry], ['Location', app.location],
                ] as [string, string | null][]).map(([k, v]) => (
                  <div key={k}>
                    <dt className="text-xs font-semibold uppercase tracking-wide text-slate-500">{k}</dt>
                    <dd className="mt-0.5 text-slate-200">{v || <span className="text-slate-600">Not provided</span>}</dd>
                  </div>
                ))}
              </dl>
            </Card>
          </div>

          <div className="space-y-6">
            <Card>
              <h2 className="mb-3 text-sm font-bold text-slate-200">Founders</h2>
              <ul className="space-y-2 text-sm">
                {app.founders.map((f) => (
                  <li key={f.id}><div className="font-semibold text-slate-200">{f.name}</div><div className="text-xs text-slate-500">{f.role_in_startup || 'Founder'}{f.education ? ` · ${f.education}` : ''}</div></li>
                ))}
              </ul>
              <div className="mt-4 border-t border-slate-800 pt-3 text-xs text-slate-400">
                Contact: {app.contact_name} · {app.contact_email}
              </div>
            </Card>
            <Card>
              <h2 className="mb-3 text-sm font-bold text-slate-200">Documents</h2>
              <ul className="mb-3 space-y-2" data-testid="application-documents">
                {app.documents.map((d) => (
                  <li key={d.id} className="flex items-start gap-2 text-sm">
                    <FileText className="mt-0.5 h-4 w-4 text-blue-400" />
                    <div>
                      <div className="text-slate-200">{d.original_filename}</div>
                      <div className="text-xs text-slate-500">{DOCUMENT_TYPES.find((t) => t.value === d.document_type)?.label || d.document_type} · {(d.file_size / 1024).toFixed(0)} KB · {d.processing_status}</div>
                    </div>
                  </li>
                ))}
                {app.documents.length === 0 && <li className="text-sm text-slate-500">None</li>}
              </ul>
              {!active && (
                <div className="flex gap-2">
                  <select className="flex-1 rounded border border-slate-700 bg-slate-950 px-2 py-1 text-xs text-slate-200" value={docType} onChange={(e) => setDocType(e.target.value)}>
                    {DOCUMENT_TYPES.map((t) => <option key={t.value} value={t.value}>{t.label}</option>)}
                  </select>
                  <button onClick={() => fileInput.current?.click()} className="flex items-center gap-1 rounded bg-slate-800 px-2 py-1 text-xs text-slate-200 hover:bg-slate-700">
                    <UploadCloud className="h-3.5 w-3.5" /> Add
                  </button>
                  <input ref={fileInput} type="file" multiple className="hidden" onChange={(e) => upload(e.target.files)} />
                </div>
              )}
              {uploadError && <div className="mt-2"><ErrorBox message={uploadError} /></div>}
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}
