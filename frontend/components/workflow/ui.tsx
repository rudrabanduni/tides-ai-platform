'use client';

import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/auth-context';
import { AlertTriangle, CheckCircle2, CircleDashed, Loader2, XCircle, Ban } from 'lucide-react';
import { applicationsApi, EvidenceClass } from '@/services/applications';

export const MOCK_DISCLOSURE = 'MOCK DEMONSTRATION — OFFLINE SYNTHETIC RESULTS — NOT A REAL AI EVALUATION';

/** Global disclosure banner, shown whenever the server runs the offline mock provider. */
export function MockModeBanner({ forceText }: { forceText?: string | null }) {
  const { data } = useQuery({
    queryKey: ['runtimeMode'],
    queryFn: () => applicationsApi.runtimeMode(),
    staleTime: 60_000,
    enabled: forceText === undefined,
  });
  const text = forceText !== undefined ? forceText : data?.disclosure;
  if (!text) return null;
  return (
    <div
      role="alert"
      data-testid="mock-disclosure"
      className="w-full border-b border-amber-500/40 bg-amber-500/15 px-6 py-2 text-center text-xs font-bold tracking-wide text-amber-300"
    >
      <AlertTriangle className="mr-2 inline h-4 w-4 -mt-0.5" />
      {text}
    </div>
  );
}

export function Card({ children, className = '' }: { children: React.ReactNode; className?: string }) {
  return <div className={`rounded-xl border border-slate-800 bg-slate-900/60 p-5 ${className}`}>{children}</div>;
}

export function PageHeader({ title, subtitle, actions }: { title: string; subtitle?: React.ReactNode; actions?: React.ReactNode }) {
  return (
    <div className="mb-6 flex flex-wrap items-start justify-between gap-4">
      <div>
        <h1 className="text-2xl font-bold text-slate-100">{title}</h1>
        {subtitle && <div className="mt-1 text-sm text-slate-400">{subtitle}</div>}
      </div>
      {actions && <div className="flex flex-wrap items-center gap-2">{actions}</div>}
    </div>
  );
}

const STATUS_STYLES: Record<string, string> = {
  COMPLETED: 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30',
  SUCCESS: 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30',
  RUNNING: 'bg-blue-500/10 text-blue-300 border-blue-500/30',
  QUEUED: 'bg-slate-500/10 text-slate-300 border-slate-500/30',
  PENDING: 'bg-slate-800 text-slate-400 border-slate-700',
  BLOCKED: 'bg-amber-500/10 text-amber-300 border-amber-500/30',
  FAILED: 'bg-red-500/10 text-red-300 border-red-500/30',
  EXHAUSTED: 'bg-red-500/10 text-red-300 border-red-500/30',
  MISSING: 'bg-red-500/10 text-red-300 border-red-500/30',
};

export function StatusPill({ status }: { status: string | null | undefined }) {
  const s = (status || 'NOT STARTED').toUpperCase();
  return (
    <span className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold ${STATUS_STYLES[s] || 'bg-slate-800 text-slate-300 border-slate-700'}`}>
      {s.replace(/_/g, ' ')}
    </span>
  );
}

export function StageIcon({ status }: { status: string }) {
  switch (status) {
    case 'SUCCESS':
    case 'SKIPPED':
      return <CheckCircle2 className="h-4 w-4 text-emerald-400" />;
    case 'RUNNING':
      return <Loader2 className="h-4 w-4 animate-spin text-blue-400" />;
    case 'FAILED':
    case 'EXHAUSTED':
      return <XCircle className="h-4 w-4 text-red-400" />;
    case 'BLOCKED':
      return <Ban className="h-4 w-4 text-amber-400" />;
    default:
      return <CircleDashed className="h-4 w-4 text-slate-600" />;
  }
}

const EVIDENCE_STYLES: Record<EvidenceClass, string> = {
  INDEPENDENTLY_VERIFIED: 'bg-emerald-500/15 text-emerald-200 border-emerald-400/40',
  DOCUMENTARY_EVIDENCE: 'bg-sky-500/10 text-sky-300 border-sky-500/30',
  APPLICANT_REPORTED: 'bg-violet-500/10 text-violet-300 border-violet-500/30',
  NOT_VERIFIED: 'bg-amber-500/10 text-amber-300 border-amber-500/30',
  MISSING: 'bg-red-500/10 text-red-300 border-red-500/30',
  NOT_APPLICABLE: 'bg-slate-800 text-slate-400 border-slate-700',
};

export function EvidenceClassBadge({ cls, label }: { cls: EvidenceClass; label: string }) {
  return (
    <span className={`inline-flex whitespace-nowrap rounded border px-2 py-0.5 text-[11px] font-semibold ${EVIDENCE_STYLES[cls] || EVIDENCE_STYLES.NOT_APPLICABLE}`}>
      {label}
    </span>
  );
}

export function ErrorBox({ message }: { message: string }) {
  return (
    <div role="alert" className="rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-300">
      {message}
    </div>
  );
}

export function Spinner({ label }: { label?: string }) {
  return (
    <div className="flex items-center gap-3 py-10 text-sm text-slate-400">
      <Loader2 className="h-5 w-5 animate-spin text-blue-400" />
      {label || 'Loading…'}
    </div>
  );
}

export function formatDate(value?: string | null): string {
  if (!value) return '—';
  try {
    return new Date(value).toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' });
  } catch {
    return value;
  }
}

export function useRequireAuth() {
  const { user, isLoading } = useAuth();
  const router = useRouter();
  React.useEffect(() => {
    if (!isLoading && !user) router.push('/login');
  }, [user, isLoading, router]);
  return user;
}
