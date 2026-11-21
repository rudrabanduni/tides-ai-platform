'use client';

import React from 'react';
import { 
  CheckCircle2, 
  HelpCircle, 
  AlertCircle, 
  AlertTriangle, 
  MinusCircle, 
  FileQuestion,
  Info
} from 'lucide-react';
import { VerificationStatus } from '@/types';

interface VerificationBadgeProps {
  status?: VerificationStatus | string | null;
  showIcon?: boolean;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export function getVerificationMeta(status?: VerificationStatus | string | null) {
  switch (status) {
    case 'VERIFIED_DOCUMENTED':
      return {
        label: 'Verified (Documented)',
        shortLabel: 'Verified',
        description: 'Backed by explicit documentation in pitch deck or uploaded records.',
        bgClass: 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30',
        dotClass: 'bg-emerald-400',
        Icon: CheckCircle2,
      };
    case 'SELF_REPORTED_ONLY':
      return {
        label: 'Self-Reported Only',
        shortLabel: 'Self-Reported',
        description: 'Claimed by applicant without independent supporting documentation.',
        bgClass: 'bg-amber-500/15 text-amber-300 border-amber-500/30',
        dotClass: 'bg-amber-400',
        Icon: AlertCircle,
      };
    case 'PLAUSIBLE_ESTIMATE':
      return {
        label: 'Plausible Estimate',
        shortLabel: 'Plausible',
        description: 'Logical deduction or projection aligned with sector benchmarks.',
        bgClass: 'bg-blue-500/15 text-blue-300 border-blue-500/30',
        dotClass: 'bg-blue-400',
        Icon: Info,
      };
    case 'UNSUPPORTED_ASSUMPTION':
      return {
        label: 'Unsupported Assumption',
        shortLabel: 'Unsupported',
        description: 'Critical assumption or growth claim lacking substantiation.',
        bgClass: 'bg-orange-500/15 text-orange-400 border-orange-500/30',
        dotClass: 'bg-orange-400',
        Icon: AlertTriangle,
      };
    case 'CONTRADICTED':
      return {
        label: 'Contradicted',
        shortLabel: 'Contradicted',
        description: 'Directly conflicts with evidence elsewhere in application materials.',
        bgClass: 'bg-rose-500/20 text-rose-400 border-rose-500/40 font-bold',
        dotClass: 'bg-rose-500',
        Icon: AlertTriangle,
      };
    case 'MISSING_INFORMATION':
      return {
        label: 'Missing Information',
        shortLabel: 'Missing',
        description: 'Required criterion omitted or omitted from submitted materials.',
        bgClass: 'bg-slate-700/40 text-slate-400 border-slate-600/40',
        dotClass: 'bg-slate-400',
        Icon: FileQuestion,
      };
    case 'NOT_APPLICABLE':
      return {
        label: 'Not Applicable',
        shortLabel: 'N/A',
        description: 'Criterion not applicable at current venture stage.',
        bgClass: 'bg-slate-800/40 text-slate-500 border-slate-700/40',
        dotClass: 'bg-slate-500',
        Icon: MinusCircle,
      };
    default:
      return {
        label: status ? String(status).replace(/_/g, ' ') : 'Not Assessed',
        shortLabel: 'Not Assessed',
        description: 'Status not specified or not evaluated.',
        bgClass: 'bg-slate-800 text-slate-400 border-slate-700',
        dotClass: 'bg-slate-400',
        Icon: HelpCircle,
      };
  }
}

export function VerificationBadge({
  status,
  showIcon = true,
  size = 'md',
  className = '',
}: VerificationBadgeProps) {
  const meta = getVerificationMeta(status);
  const Icon = meta.Icon;

  const sizeClasses = {
    sm: 'text-[10px] px-2 py-0.5 space-x-1',
    md: 'text-xs px-2.5 py-1 space-x-1.5',
    lg: 'text-sm px-3 py-1.5 space-x-2',
  }[size];

  const iconSizes = {
    sm: 'w-3 h-3',
    md: 'w-3.5 h-3.5',
    lg: 'w-4 h-4',
  }[size];

  return (
    <span
      title={meta.description}
      className={`inline-flex items-center rounded-md border font-medium ${meta.bgClass} ${sizeClasses} ${className}`}
    >
      {showIcon && <Icon className={`${iconSizes} flex-shrink-0`} />}
      <span>{meta.label}</span>
    </span>
  );
}
