'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import { ArrowLeft, Download, FileSearch, X } from 'lucide-react';
import {
  CitedItem,
  CriterionResult,
  EvidenceRecord,
  RunResults,
  apiErrorMessage,
  applicationsApi,
} from '@/services/applications';
import {
  Card,
  ErrorBox,
  EvidenceClassBadge,
  MockModeBanner,
  PageHeader,
  Spinner,
  StatusPill,
  formatDate,
  useRequireAuth,
} from '@/components/workflow/ui';

type Tab = 'overview' | 'domains' | 'cover' | 'supervisory' | 'report';

function EvidenceDrawer({ runId, criterion, onClose }: { runId: string; criterion: CriterionResult; onClose: () => void }) {
  const q = useQuery({
    queryKey: ['evidence', runId, criterion.criterion_id],
    queryFn: () => applicationsApi.getEvidence(runId, criterion.evidence_ids),
    enabled: criterion.evidence_ids.length > 0,
  });
  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-black/50" onClick={onClose}>
      <aside className="h-full w-full max-w-lg overflow-y-auto border-l border-slate-800 bg-slate-950 p-6" onClick={(e) => e.stopPropagation()} data-testid="evidence-drawer">
        <div className="mb-4 flex items-start justify-between">
          <div>
            <div className="font-mono text-xs text-slate-500">{criterion.criterion_id}</div>
            <h3 className="text-lg font-bold text-slate-100">{criterion.criterion_name}</h3>
          </div>
          <button onClick={onClose} className="rounded p-1 text-slate-400 hover:bg-slate-800" aria-label="Close evidence"><X className="h-5 w-5" /></button>
        </div>
        <div className="mb-4 flex flex-wrap items-center gap-2 text-xs">
          <EvidenceClassBadge cls={criterion.evidence_class} label={criterion.evidence_class_label} />
          <span className="text-slate-400">Score: {criterion.score ?? '—'}</span>
          <span className="text-slate-500">({criterion.verification_status})</span>
        </div>
        {criterion.rationale && <p className="mb-3 text-sm text-slate-300">{criterion.rationale}</p>}
        {(criterion.applicant_response || criterion.value) && (
          <div className="mb-3 rounded border border-slate-800 p-3 text-xs text-slate-300">
            <div className="mb-1 font-semibold uppercase tracking-wide text-slate-500">Applicant information</div>
            {criterion.applicant_response || criterion.value}
          </div>
        )}
        {criterion.missing_information && <p className="mb-3 text-xs text-amber-300">Missing: {criterion.missing_information}</p>}
        <h4 className="mb-2 mt-4 text-xs font-bold uppercase tracking-wide text-slate-400">Cited evidence</h4>
        {criterion.evidence_ids.length === 0 && <p className="text-sm text-slate-500">No document evidence is cited for this criterion.</p>}
        {q.isLoading && <Spinner label="Loading evidence…" />}
        {q.error && <ErrorBox message={apiErrorMessage(q.error)} />}
        <ul className="space-y-3">
          {(q.data || []).map((e: EvidenceRecord) => (
            <li key={e.evidence_id} className="rounded-lg border border-slate-800 bg-slate-900/60 p-3" data-testid="evidence-record">
              <div className="mb-1 text-xs text-slate-400">{e.document || 'Document'} · {e.page_number ? `page ${e.page_number}` : e.section_name}</div>
              <blockquote className="border-l-2 border-sky-500 pl-3 text-sm text-slate-200">{e.snippet}</blockquote>
              <div className="mt-1 font-mono text-[10px] text-slate-600">{e.evidence_id}</div>
            </li>
          ))}
        </ul>
      </aside>
    </div>
  );
}

function CriteriaTable({ criteria, onInspect }: { criteria: CriterionResult[]; onInspect: (c: CriterionResult) => void }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left text-sm">
        <thead className="border-b border-slate-800 text-xs uppercase tracking-wide text-slate-500">
          <tr><th className="py-2 pr-3">ID</th><th className="pr-3">Criterion</th><th className="pr-3">Score</th><th className="pr-3">Evidence class</th><th className="pr-3">Rationale / missing information</th><th></th></tr>
        </thead>
        <tbody className="divide-y divide-slate-800/70">
          {criteria.map((c) => (
            <tr key={c.criterion_id} data-testid={`criterion-${c.criterion_id}`}>
              <td className="py-2 pr-3 font-mono text-xs text-slate-400">{c.criterion_id}</td>
              <td className="pr-3 text-slate-200">{c.criterion_name}</td>
              <td className="pr-3 text-slate-200">{c.score ?? '—'}</td>
              <td className="pr-3"><EvidenceClassBadge cls={c.evidence_class} label={c.evidence_class_label} /></td>
              <td className="max-w-md pr-3 text-xs text-slate-400">
                {c.rationale || (c.value ? `${c.value} (${c.source})` : '—')}
                {c.missing_information && <div className="text-amber-300/80">Missing: {c.missing_information}</div>}
              </td>
              <td>
                <button onClick={() => onInspect(c)} className="flex items-center gap-1 whitespace-nowrap rounded px-2 py-1 text-xs text-blue-400 hover:bg-blue-500/10" data-testid={`inspect-${c.criterion_id}`}>
                  <FileSearch className="h-3.5 w-3.5" /> {c.evidence_ids.length} evidence
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function CitedList({ title, items, empty }: { title: string; items?: CitedItem[]; empty: string }) {
  return (
    <Card>
      <h3 className="mb-2 text-sm font-bold text-slate-200">{title}</h3>
      {!items || items.length === 0 ? <p className="text-sm text-slate-500">{empty}</p> : (
        <ul className="space-y-1.5 text-sm text-slate-300">
          {items.map((it, i) => (
            <li key={i}>{it.text} <span className="font-mono text-[11px] text-slate-500">[{it.criterion_id} · {it.domain}{it.evidence_ids.length ? ` · ${it.evidence_ids.length} evidence` : ''}]</span></li>
          ))}
        </ul>
      )}
    </Card>
  );
}

function StringList({ title, items, empty }: { title: string; items?: (string | undefined)[]; empty: string }) {
  const list = (items || []).filter(Boolean) as string[];
  return (
    <Card>
      <h3 className="mb-2 text-sm font-bold text-slate-200">{title}</h3>
      {list.length === 0 ? <p className="text-sm text-slate-500">{empty}</p> : (
        <ul className="list-disc space-y-1 pl-5 text-sm text-slate-300">{list.map((x, i) => <li key={i}>{x}</li>)}</ul>
      )}
    </Card>
  );
}

function ReportPanel({ runId, status }: { runId: string; status: string }) {
  const [url, setUrl] = useState<string | null>(null);
  const [filename, setFilename] = useState<string>('report.pdf');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  useEffect(() => () => { if (url) URL.revokeObjectURL(url); }, [url]);
  if (status !== 'COMPLETED') {
    return <ErrorBox message={`No final report: evaluation status is ${status}. Incomplete evaluations never produce a final due-diligence report.`} />;
  }
  const load = async () => {
    setLoading(true); setError(null);
    try {
      const { blob, filename: fn } = await applicationsApi.getReportPdf(runId);
      setFilename(fn);
      setUrl(URL.createObjectURL(blob));
    } catch (err) {
      setError(apiErrorMessage(err, 'Could not load the report PDF.'));
    } finally {
      setLoading(false);
    }
  };
  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-3">
        {!url && (
          <button onClick={load} disabled={loading} data-testid="load-report" className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-500 disabled:opacity-50">
            {loading ? 'Generating PDF…' : 'Open due-diligence report'}
          </button>
        )}
        {url && (
          <button
            type="button"
            data-testid="download-report"
            onClick={() => {
              const a = document.createElement('a');
              a.href = url;
              a.download = filename;
              document.body.appendChild(a);
              a.click();
              a.remove();
            }}
            className="flex items-center gap-2 rounded-lg bg-emerald-600 px-4 py-2 text-sm font-semibold text-white hover:bg-emerald-500"
          >
            <Download className="h-4 w-4" /> Download PDF ({filename})
          </button>
        )}
      </div>
      {error && <ErrorBox message={error} />}
      {url && <iframe title="Due-diligence report" src={url} className="h-[80vh] w-full rounded-lg border border-slate-800 bg-white" data-testid="report-viewer" />}
    </div>
  );
}

export default function EvaluationResultsPage() {
  const user = useRequireAuth();
  const params = useParams<{ runId: string }>();
  const runId = String(params?.runId || '');
  const [tab, setTab] = useState<Tab>('overview');
  const [domainKey, setDomainKey] = useState<string>('problem_solution');
  const [inspect, setInspect] = useState<CriterionResult | null>(null);

  const runQ = useQuery({ queryKey: ['run', runId], queryFn: () => applicationsApi.getRun(runId), enabled: !!user && !!runId });
  const resQ = useQuery({ queryKey: ['results', runId], queryFn: () => applicationsApi.getResults(runId), enabled: !!user && !!runId });

  if (!user) return null;
  if (runQ.isLoading || resQ.isLoading) return <div className="p-8"><Spinner label="Loading evaluation…" /></div>;
  if (runQ.error || !runQ.data) return <div className="p-8"><ErrorBox message={apiErrorMessage(runQ.error, 'Evaluation not found.')} /></div>;

  const run = runQ.data;
  const res: RunResults | undefined = resQ.data;
  if (!res || !res.available) {
    return (
      <div className="p-8">
        <MockModeBanner forceText={run.disclosure} />
        <ErrorBox message={`No persisted results for this evaluation yet (status ${run.status}).`} />
      </div>
    );
  }
  const domain = res.domains.find((d) => d.key === domainKey) || res.domains[0];
  const sup = res.supervisory;
  const cov = res.coverage;

  const tabs: [Tab, string][] = [['overview', 'Overview'], ['domains', 'Six-domain assessment'], ['cover', 'Cover criteria'], ['supervisory', 'Supervisory review'], ['report', 'Due-diligence report']];

  return (
    <div>
      <MockModeBanner forceText={res.disclosure} />
      <div className="mx-auto max-w-7xl p-8">
        <Link href={run.application_id ? `/applications/${run.application_id}` : '/applications'} className="mb-4 inline-flex items-center gap-1 text-xs text-slate-400 hover:text-slate-200">
          <ArrowLeft className="h-3.5 w-3.5" /> Back to application
        </Link>
        <PageHeader
          title={res.startup_name || 'Evaluation'}
          subtitle={<span>Evaluation <span className="font-mono">{run.id}</span> · Startup <span className="font-mono">{run.startup_id}</span> · finished {formatDate(run.finished_at)}</span>}
          actions={<><StatusPill status={run.status} />{res.validation.valid ? <StatusPill status="SUCCESS" /> : <StatusPill status="FAILED" />}</>}
        />

        <div className="mb-6 flex flex-wrap gap-1 border-b border-slate-800">
          {tabs.map(([k, label]) => (
            <button key={k} onClick={() => setTab(k)} data-testid={`tab-${k}`} className={`-mb-px border-b-2 px-4 py-2 text-sm font-semibold ${tab === k ? 'border-blue-500 text-blue-300' : 'border-transparent text-slate-400 hover:text-slate-200'}`}>
              {label}
            </button>
          ))}
        </div>

        {tab === 'overview' && (
          <div className="space-y-6">
            <div className="grid gap-4 md:grid-cols-4">
              <Card><div className="text-xs text-slate-500">Criteria accounted for</div><div className="mt-1 text-2xl font-bold text-slate-100" data-testid="coverage-total">{cov.total_present}/{cov.total_expected}</div><div className="text-xs text-slate-500">{cov.domain_criteria_present}/81 domain · {cov.cover_criteria_present}/6 cover</div></Card>
              <Card><div className="text-xs text-slate-500">Domains completed</div><div className="mt-1 text-2xl font-bold text-slate-100" data-testid="domains-completed">{cov.domains_completed}/6</div></Card>
              <Card><div className="text-xs text-slate-500">Supervisory review</div><div className="mt-2"><StatusPill status={sup.status} /></div></Card>
              <Card><div className="text-xs text-slate-500">Report validation</div><div className="mt-2" data-testid="validation-status"><StatusPill status={res.validation.valid ? 'COMPLETED' : 'FAILED'} /></div>{!res.validation.valid && <div className="mt-1 text-xs text-red-300">{res.validation.errors[0]}</div>}</Card>
            </div>
            {res.weighted_score && (
              <Card>
                <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
                  <h3 className="text-sm font-bold text-slate-200">Weighted score (TAES weightage)</h3>
                  <span className={`rounded px-2 py-0.5 text-[11px] font-bold ${res.weighted_score.standard_status === 'PROVISIONAL' ? 'bg-amber-500/15 text-amber-300' : 'bg-emerald-500/15 text-emerald-300'}`}>
                    {res.weighted_score.standard_version} · {res.weighted_score.standard_status}
                  </span>
                </div>
                <div className="flex flex-wrap items-start gap-6">
                  <div>
                    <div className="text-4xl font-bold text-slate-100" data-testid="weighted-score">
                      {res.weighted_score.overall_score_10 ?? '—'}<span className="text-lg text-slate-500"> / {res.weighted_score.score_scale_max}</span>
                    </div>
                    <div className="mt-1 max-w-xs text-xs text-slate-500">{res.weighted_score.decision_note || res.weighted_score.recommendation_basis}</div>
                  </div>
                  <table className="flex-1 text-left text-xs">
                    <thead className="text-slate-500"><tr><th className="py-1 pr-3">Section</th><th className="pr-3">Weight</th><th className="pr-3">Score</th><th className="pr-3">Contribution</th><th>Criteria scored</th></tr></thead>
                    <tbody className="text-slate-300">
                      {res.weighted_score.sections.map((s) => (
                        <tr key={s.key}>
                          <td className="py-0.5 pr-3">{s.title}</td>
                          <td className="pr-3">{s.weight_pct.toFixed(1)}%</td>
                          <td className="pr-3">{s.score_10 ?? '—'}{s.score_10 !== null ? ' / 10' : ''}</td>
                          <td className="pr-3">{s.weighted_contribution ?? '—'}</td>
                          <td>{s.criteria_scored}{s.criteria_not_scored ? ` (+${s.criteria_not_scored} not scored)` : ''}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <p className="mt-3 text-xs text-slate-500">
                  Approved by {res.weighted_score.approved_by || '—'} · effective {res.weighted_score.effective_date || '—'}. {res.weighted_score.missing_policy_note}
                </p>
              </Card>
            )}
            <Card>
              <h3 className="mb-2 text-sm font-bold text-slate-200">TAES red-flag checks</h3>
              {(res.red_flags || []).length === 0 ? (
                <p className="text-sm text-slate-500" data-testid="red-flags">No red flags triggered (TRL claim vs revenue; combined founder equity).</p>
              ) : (
                <ul className="space-y-1 text-sm text-amber-200" data-testid="red-flags">
                  {(res.red_flags || []).map((f) => <li key={f.id}><b>{f.rule}:</b> {f.finding} {f.action}</li>)}
                </ul>
              )}
            </Card>
            <Card>
              <h3 className="mb-3 text-sm font-bold text-slate-200">Evidence quality</h3>
              <div className="flex flex-wrap gap-3 text-sm">
                {Object.entries(cov.evidence_classes).map(([k, v]) => (
                  <div key={k} className="flex items-center gap-2"><EvidenceClassBadge cls={k as any} label={k.replace(/_/g, ' ').toLowerCase()} /> <span className="text-slate-300">{v}</span></div>
                ))}
              </div>
              <p className="mt-3 text-xs text-slate-500">Applicant statements without a supporting document are never shown as verified. Missing information is a diligence gap, not a weakness score.</p>
            </Card>
            <div className="grid gap-4 md:grid-cols-3">
              {res.domains.map((d) => (
                <button key={d.key} onClick={() => { setDomainKey(d.key); setTab('domains'); }} className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 text-left hover:border-blue-500/50" data-testid={`domain-card-${d.key}`}>
                  <div className="flex items-center justify-between"><span className="text-sm font-semibold text-slate-200">{d.title}</span><StatusPill status={d.status} /></div>
                  <div className="mt-2 text-xs text-slate-400">{d.criteria_assessed}/{d.criteria_total} criteria · avg score {d.average_score ?? '—'}</div>
                </button>
              ))}
            </div>
            {sup.overall_diligence_position && (
              <Card>
                <h3 className="mb-2 text-sm font-bold text-slate-200">Overall diligence position</h3>
                <p className="text-sm text-slate-300">{sup.overall_diligence_position}</p>
                <p className="mt-2 text-sm"><span className="text-slate-500">Committee recommendation:</span> <span className="font-semibold text-slate-100" data-testid="committee-recommendation">{sup.committee_recommendation}</span></p>
              </Card>
            )}
          </div>
        )}

        {tab === 'domains' && domain && (
          <div className="space-y-4">
            <div className="flex flex-wrap gap-2">
              {res.domains.map((d) => (
                <button key={d.key} onClick={() => setDomainKey(d.key)} data-testid={`domain-tab-${d.key}`} className={`rounded-lg border px-3 py-1.5 text-xs font-semibold ${d.key === domain.key ? 'border-blue-500 bg-blue-500/10 text-blue-300' : 'border-slate-800 text-slate-400 hover:text-slate-200'}`}>
                  {d.title} ({d.criteria_assessed}/{d.criteria_total})
                </button>
              ))}
            </div>
            <Card>
              <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
                <h2 className="text-lg font-bold text-slate-100">{domain.title}</h2>
                <div className="flex items-center gap-3 text-xs text-slate-400"><StatusPill status={domain.status} /> confidence {domain.confidence ?? '—'}</div>
              </div>
              {domain.summary && <p className="mb-2 text-sm text-slate-300">{domain.summary}</p>}
              {domain.executive_conclusion && <p className="mb-4 text-sm text-slate-400">{domain.executive_conclusion}</p>}
              <CriteriaTable criteria={domain.criteria} onInspect={setInspect} />
            </Card>
            <div className="grid gap-4 md:grid-cols-2">
              <StringList title="Strengths" items={domain.strengths} empty="None recorded." />
              <StringList title="Weaknesses & gaps" items={domain.weaknesses} empty="None recorded." />
              <StringList title="Risks" items={(domain.risks || []).map((r) => `${r.severity ? `[${r.severity}] ` : ''}${r.description}`)} empty="None recorded." />
              <StringList title="Diligence questions" items={domain.questions} empty="None recorded." />
            </div>
          </div>
        )}

        {tab === 'cover' && (
          <Card>
            <h2 className="mb-1 text-lg font-bold text-slate-100">Cover &amp; intake criteria (CM-01 – CM-06)</h2>
            <p className="mb-4 text-xs text-slate-500">Assessed deterministically from extracted document data and the intake form; no score is assigned.</p>
            <CriteriaTable criteria={res.cover_criteria} onInspect={setInspect} />
          </Card>
        )}

        {tab === 'supervisory' && (
          <div className="space-y-4" data-testid="supervisory-panel">
            <Card>
              <div className="mb-2 flex items-center gap-3"><h2 className="text-lg font-bold text-slate-100">Supervisory synthesis</h2><StatusPill status={sup.status} /></div>
              <p className="text-sm text-slate-300">{sup.overall_diligence_position || 'Supervisory review did not run: it is blocked unless all six domains complete with all criteria accounted for.'}</p>
              {sup.recommendation_rationale && <p className="mt-2 text-sm text-slate-400">{sup.recommendation_rationale}</p>}
              <p className="mt-3 text-sm"><span className="text-slate-500">Committee recommendation:</span> <span className="font-semibold text-slate-100">{sup.committee_recommendation || '—'}</span></p>
              <p className="mt-1 text-xs text-slate-500">Domains cited: {(sup.domains_cited || []).join(', ') || '—'}</p>
            </Card>
            <div className="grid gap-4 md:grid-cols-2">
              <CitedList title="Major strengths" items={sup.major_strengths} empty="No criterion met the documentary-evidence threshold." />
              <CitedList title="Material weaknesses" items={sup.material_weaknesses} empty="None recorded." />
              <StringList title="Contradictions" items={(sup.contradictions || []).map((c) => c.description)} empty="No contradictions identified." />
              <CitedList title="Missing evidence" items={sup.missing_evidence} empty="All criteria contain applicant information." />
              <StringList title="Financial & technical risks" items={(sup.financial_and_technical_risks || []).map((r) => `${r.description} [${r.domain}]`)} empty="None recorded." />
              <StringList title="Market risks" items={(sup.market_risks || []).map((r) => `${r.description} [${r.domain}]`)} empty="None recorded." />
              <CitedList title="Team capability observations" items={sup.team_capability_observations} empty="None recorded." />
              <StringList title="Priority diligence questions" items={sup.priority_diligence_questions} empty="None recorded." />
              <StringList title="Required founder clarifications" items={sup.required_founder_clarifications} empty="None." />
              <CitedList title="Recommended incubation support" items={sup.recommended_incubation_support} empty="No support needs specified." />
              <StringList title="Conditional incubation requirements" items={sup.conditional_requirements} empty="None recorded." />
            </div>
          </div>
        )}

        {tab === 'report' && <ReportPanel runId={run.id} status={run.status} />}
      </div>
      {inspect && <EvidenceDrawer runId={run.id} criterion={inspect} onClose={() => setInspect(null)} />}
    </div>
  );
}
