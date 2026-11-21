'use client';

import React, { useMemo, useRef, useState } from 'react';
import Link from 'next/link';
import { CheckCircle2, FileText, Plus, Trash2, UploadCloud, X } from 'lucide-react';
import {
  Application,
  ApplicationPayload,
  DOCUMENT_TYPES,
  DocumentSummary,
  FounderInput,
  apiErrorMessage,
  applicationsApi,
  validateUploadFile,
} from '@/services/applications';
import { Card, ErrorBox, PageHeader, useRequireAuth } from '@/components/workflow/ui';

const STAGES = ['Ideation', 'Pre-Seed', 'Seed', 'MVP', 'Early Revenue', 'Growth', 'Scale'];
const SECTORS = ['CleanTech', 'DeepTech', 'HealthTech', 'MedTech', 'AgriTech', 'FinTech', 'EdTech', 'Enterprise SaaS', 'Manufacturing', 'Mobility', 'Other'];

const inputCls =
  'w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-slate-100 placeholder-slate-500 focus:border-blue-500 focus:outline-none';

function Field({ label, required, hint, error, children }: { label: string; required?: boolean; hint?: string; error?: string; children: React.ReactNode }) {
  return (
    <label className="block">
      <span className="mb-1 block text-xs font-semibold uppercase tracking-wide text-slate-400">
        {label} {required && <span className="text-red-400">*</span>}
      </span>
      {children}
      {hint && !error && <span className="mt-1 block text-xs text-slate-500">{hint}</span>}
      {error && <span className="mt-1 block text-xs text-red-400">{error}</span>}
    </label>
  );
}

const emptyFounder = (): FounderInput => ({ name: '', role_in_startup: '', email: '', education: '', experience_summary: '' });

const SAMPLE: Omit<ApplicationPayload, 'declarations'> = {
  company_name: 'CleanPower Systems Pvt Ltd',
  sector: 'CleanTech',
  industry: 'Stationary energy / backup power',
  stage: 'Seed',
  location: 'Roorkee, Uttarakhand, India',
  website: 'https://cleanpower.example',
  contact_name: 'Dr. Arjun Sharma',
  contact_email: 'founders@cleanpower.example',
  contact_phone: '',
  founders: [
    { name: 'Dr. Arjun Sharma', role_in_startup: 'Co-Founder & CEO', education: 'PhD Electrochemical Engineering', experience_summary: '14 years in electrochemical energy systems' },
    { name: 'Priya Mehta', role_in_startup: 'Co-Founder & CTO', education: 'M.Tech Power Electronics', experience_summary: '9 years designing power conversion systems' },
  ],
  problem_statement: 'Grid outages force telecom towers and edge data centres onto diesel generators.',
  proposed_solution: 'Containerised 10 kW PEM fuel-cell units with remote monitoring and swappable hydrogen cylinders.',
  product_technology: 'Low-platinum PEM stack with in-house power electronics and controller firmware.',
  target_market: 'Telecom tower and edge data-centre operators in North India.',
  business_model: 'Power-as-a-service contracts plus outright hardware sales.',
  traction: 'Three pilot sites; one letter of intent (unsigned).',
  revenue_information: 'Pre-revenue.',
  financial_information: 'INR 25 lakh grant received; INR 6 lakh monthly operating costs.',
  funding_requirement: 'INR 2 crore seed round.',
  incubation_support_requirement: 'Hydrogen-safe test bay, certification mentorship, campus pilot site.',
};

export default function NewApplicationPage() {
  const user = useRequireAuth();
  const [step, setStep] = useState<1 | 2 | 3>(1);
  const [form, setForm] = useState<Omit<ApplicationPayload, 'declarations'>>({
    company_name: '', sector: 'CleanTech', industry: '', stage: 'Seed', location: '', website: '',
    contact_name: '', contact_email: '', contact_phone: '', founders: [emptyFounder()],
    problem_statement: '', proposed_solution: '', product_technology: '', target_market: '', business_model: '',
    traction: '', revenue_information: '', financial_information: '', funding_requirement: '', incubation_support_requirement: '',
  });
  const [decl, setDecl] = useState({ information_accurate: false, consent_to_evaluation: false, documents_owned_or_authorised: false, synthetic_demo_data: false });
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [application, setApplication] = useState<Application | null>(null);
  const idemKey = useMemo(() => applicationsApi.newIdempotencyKey(), []);

  // Upload step state
  const fileInput = useRef<HTMLInputElement>(null);
  const [docType, setDocType] = useState('pitch_deck');
  const [uploaded, setUploaded] = useState<DocumentSummary[]>([]);
  const [uploadErrors, setUploadErrors] = useState<string[]>([]);
  const [uploading, setUploading] = useState(false);

  if (!user) return null;

  const set = (k: keyof typeof form, v: any) => setForm((f) => ({ ...f, [k]: v }));
  const setFounder = (i: number, k: keyof FounderInput, v: string) =>
    setForm((f) => ({ ...f, founders: f.founders.map((fd, idx) => (idx === i ? { ...fd, [k]: v } : fd)) }));

  const validate = (): boolean => {
    const e: Record<string, string> = {};
    const need = (k: string, v: string | undefined, min: number, label: string) => {
      if (!v || v.trim().length < min) e[k] = `${label} is required (at least ${min} characters).`;
    };
    need('company_name', form.company_name, 2, 'Company name');
    need('contact_name', form.contact_name, 2, 'Contact name');
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.contact_email || '')) e.contact_email = 'A valid contact email is required.';
    need('problem_statement', form.problem_statement, 20, 'Problem statement');
    need('proposed_solution', form.proposed_solution, 20, 'Proposed solution');
    need('target_market', form.target_market, 10, 'Target market');
    need('business_model', form.business_model, 10, 'Business model');
    form.founders.forEach((f, i) => {
      if (!f.name || f.name.trim().length < 2) e[`founder_${i}`] = 'Founder name is required.';
      if (f.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(f.email)) e[`founder_email_${i}`] = 'Invalid email.';
    });
    if (!decl.information_accurate || !decl.consent_to_evaluation || !decl.documents_owned_or_authorised) {
      e.declarations = 'All three applicant declarations must be accepted.';
    }
    setErrors(e);
    return Object.keys(e).length === 0;
  };

  const clean = (v?: string) => (v && v.trim() ? v.trim() : undefined);

  const submit = async (ev: React.FormEvent) => {
    ev.preventDefault();
    setSubmitError(null);
    if (!validate()) return;
    setSubmitting(true);
    try {
      const payload: ApplicationPayload = {
        ...form,
        industry: clean(form.industry), location: clean(form.location), website: clean(form.website),
        contact_phone: clean(form.contact_phone), product_technology: clean(form.product_technology),
        traction: clean(form.traction), revenue_information: clean(form.revenue_information),
        financial_information: clean(form.financial_information), funding_requirement: clean(form.funding_requirement),
        incubation_support_requirement: clean(form.incubation_support_requirement),
        founders: form.founders.map((f) => ({
          name: f.name.trim(), role_in_startup: clean(f.role_in_startup), email: clean(f.email),
          education: clean(f.education), experience_summary: clean(f.experience_summary),
        })),
        declarations: decl,
      };
      const app = await applicationsApi.create(payload, idemKey);
      setApplication(app);
      setUploaded(app.documents || []);
      setStep(2);
    } catch (err) {
      setSubmitError(apiErrorMessage(err, 'Submission failed.'));
    } finally {
      setSubmitting(false);
    }
  };

  const onFiles = async (files: FileList | null) => {
    if (!files || !application) return;
    setUploadErrors([]);
    setUploading(true);
    const errs: string[] = [];
    for (const file of Array.from(files)) {
      const local = validateUploadFile(file);
      if (local) {
        errs.push(`${file.name}: ${local}`);
        continue;
      }
      try {
        const doc = await applicationsApi.uploadDocument(application.id, file, docType);
        setUploaded((u) => [...u, doc]);
      } catch (err) {
        errs.push(`${file.name}: ${apiErrorMessage(err, 'Upload failed.')}`);
      }
    }
    setUploadErrors(errs);
    setUploading(false);
    if (fileInput.current) fileInput.current.value = '';
  };

  return (
    <div className="mx-auto max-w-5xl p-8">
      <PageHeader
        title="New Startup Application"
        subtitle="LaunchIndex Startup Incubation Application — TIEDS, IIT Roorkee"
        actions={step === 1 ? (
          <button
            type="button"
            data-testid="fill-sample"
            onClick={() => { setForm(SAMPLE); setDecl((d) => ({ ...d, synthetic_demo_data: true })); }}
            className="rounded-lg border border-amber-500/40 px-3 py-2 text-xs font-semibold text-amber-300 hover:bg-amber-500/10"
          >
            Fill synthetic CleanPower sample
          </button>
        ) : undefined}
      />

      <ol className="mb-6 flex gap-2 text-xs font-semibold">
        {['Application form', 'Documents', 'Confirmation'].map((label, i) => (
          <li key={label} className={`flex-1 rounded-lg border px-3 py-2 ${step === i + 1 ? 'border-blue-500 bg-blue-500/10 text-blue-300' : step > i + 1 ? 'border-emerald-500/40 text-emerald-300' : 'border-slate-800 text-slate-500'}`}>
            {i + 1}. {label}
          </li>
        ))}
      </ol>

      {step === 1 && (
        <form onSubmit={submit} noValidate className="space-y-6" data-testid="application-form">
          <Card>
            <h2 className="mb-4 text-sm font-bold text-slate-200">Company</h2>
            <div className="grid gap-4 md:grid-cols-2">
              <Field label="Company name" required error={errors.company_name}>
                <input name="company_name" className={inputCls} value={form.company_name} onChange={(e) => set('company_name', e.target.value)} />
              </Field>
              <Field label="Sector" required>
                <select name="sector" className={inputCls} value={form.sector} onChange={(e) => set('sector', e.target.value)}>
                  {SECTORS.map((s) => <option key={s}>{s}</option>)}
                </select>
              </Field>
              <Field label="Industry"><input name="industry" className={inputCls} value={form.industry} onChange={(e) => set('industry', e.target.value)} /></Field>
              <Field label="Company stage" required>
                <select name="stage" className={inputCls} value={form.stage} onChange={(e) => set('stage', e.target.value)}>
                  {STAGES.map((s) => <option key={s}>{s}</option>)}
                </select>
              </Field>
              <Field label="Location"><input name="location" className={inputCls} value={form.location} onChange={(e) => set('location', e.target.value)} /></Field>
              <Field label="Website"><input name="website" className={inputCls} value={form.website} onChange={(e) => set('website', e.target.value)} /></Field>
            </div>
          </Card>

          <Card>
            <h2 className="mb-4 text-sm font-bold text-slate-200">Contact details</h2>
            <div className="grid gap-4 md:grid-cols-3">
              <Field label="Contact name" required error={errors.contact_name}><input name="contact_name" className={inputCls} value={form.contact_name} onChange={(e) => set('contact_name', e.target.value)} /></Field>
              <Field label="Contact email" required error={errors.contact_email}><input name="contact_email" type="email" className={inputCls} value={form.contact_email} onChange={(e) => set('contact_email', e.target.value)} /></Field>
              <Field label="Contact phone"><input name="contact_phone" className={inputCls} value={form.contact_phone} onChange={(e) => set('contact_phone', e.target.value)} /></Field>
            </div>
          </Card>

          <Card>
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-sm font-bold text-slate-200">Founders &amp; co-founders</h2>
              <button type="button" onClick={() => set('founders', [...form.founders, emptyFounder()])} disabled={form.founders.length >= 10} className="flex items-center gap-1 text-xs font-semibold text-blue-400 hover:text-blue-300">
                <Plus className="h-4 w-4" /> Add founder
              </button>
            </div>
            <div className="space-y-4">
              {form.founders.map((f, i) => (
                <div key={i} className="grid gap-3 rounded-lg border border-slate-800 p-3 md:grid-cols-2">
                  <Field label={`Founder ${i + 1} name`} required error={errors[`founder_${i}`]}><input name={`founder_${i}_name`} className={inputCls} value={f.name} onChange={(e) => setFounder(i, 'name', e.target.value)} /></Field>
                  <Field label="Role"><input name={`founder_${i}_role`} className={inputCls} value={f.role_in_startup || ''} onChange={(e) => setFounder(i, 'role_in_startup', e.target.value)} /></Field>
                  <Field label="Email" error={errors[`founder_email_${i}`]}><input className={inputCls} value={f.email || ''} onChange={(e) => setFounder(i, 'email', e.target.value)} /></Field>
                  <Field label="Education"><input className={inputCls} value={f.education || ''} onChange={(e) => setFounder(i, 'education', e.target.value)} /></Field>
                  <div className="md:col-span-2">
                    <Field label="Relevant experience"><input className={inputCls} value={f.experience_summary || ''} onChange={(e) => setFounder(i, 'experience_summary', e.target.value)} /></Field>
                  </div>
                  {form.founders.length > 1 && (
                    <button type="button" onClick={() => set('founders', form.founders.filter((_, idx) => idx !== i))} className="flex items-center gap-1 text-xs text-red-400 hover:text-red-300 md:col-span-2">
                      <Trash2 className="h-3.5 w-3.5" /> Remove founder
                    </button>
                  )}
                </div>
              ))}
            </div>
          </Card>

          <Card>
            <h2 className="mb-4 text-sm font-bold text-slate-200">Venture</h2>
            <div className="grid gap-4">
              {([
                ['problem_statement', 'Problem statement', true],
                ['proposed_solution', 'Proposed solution', true],
                ['product_technology', 'Product and technology', false],
                ['target_market', 'Target market', true],
                ['business_model', 'Business model', true],
                ['traction', 'Traction', false],
              ] as [keyof typeof form, string, boolean][]).map(([k, label, req]) => (
                <Field key={k} label={label} required={req} error={errors[k as string]}>
                  <textarea name={k as string} rows={3} className={inputCls} value={(form[k] as string) || ''} onChange={(e) => set(k, e.target.value)} />
                </Field>
              ))}
            </div>
          </Card>

          <Card>
            <h2 className="mb-4 text-sm font-bold text-slate-200">Financials &amp; incubation support</h2>
            <div className="grid gap-4 md:grid-cols-2">
              {([
                ['revenue_information', 'Revenue information'],
                ['financial_information', 'Financial information'],
                ['funding_requirement', 'Funding requirement'],
                ['incubation_support_requirement', 'Incubation support requirement'],
              ] as [keyof typeof form, string][]).map(([k, label]) => (
                <Field key={k} label={label}>
                  <textarea name={k as string} rows={2} className={inputCls} value={(form[k] as string) || ''} onChange={(e) => set(k, e.target.value)} />
                </Field>
              ))}
            </div>
          </Card>

          <Card>
            <h2 className="mb-3 text-sm font-bold text-slate-200">Declarations</h2>
            <div className="space-y-2 text-sm text-slate-300">
              {([
                ['information_accurate', 'The information in this application is accurate to the best of my knowledge.'],
                ['consent_to_evaluation', 'I consent to AI-assisted due-diligence evaluation of this application by TIEDS.'],
                ['documents_owned_or_authorised', 'I own, or am authorised to share, all uploaded documents.'],
                ['synthetic_demo_data', 'This is synthetic demonstration data (not a real applicant).'],
              ] as [keyof typeof decl, string][]).map(([k, label]) => (
                <label key={k} className="flex items-start gap-2">
                  <input type="checkbox" name={k} checked={decl[k]} onChange={(e) => setDecl((d) => ({ ...d, [k]: e.target.checked }))} className="mt-1" />
                  <span>{label}</span>
                </label>
              ))}
            </div>
            {errors.declarations && <p className="mt-2 text-xs text-red-400">{errors.declarations}</p>}
          </Card>

          {Object.keys(errors).length > 0 && <ErrorBox message="Please correct the highlighted fields." />}
          {submitError && <ErrorBox message={submitError} />}
          <div className="flex justify-end">
            <button type="submit" disabled={submitting} data-testid="submit-application" className="rounded-lg bg-blue-600 px-6 py-2.5 text-sm font-semibold text-white hover:bg-blue-500 disabled:opacity-50">
              {submitting ? 'Submitting…' : 'Submit application'}
            </button>
          </div>
        </form>
      )}

      {step === 2 && application && (
        <div className="space-y-6">
          <Card>
            <p className="text-sm text-slate-300">
              Application <span className="font-mono font-semibold text-emerald-300" data-testid="application-ref">{application.application_ref}</span> was saved for{' '}
              <span className="font-semibold">{application.company_name}</span>. Upload the supporting documents next.
            </p>
          </Card>
          <Card>
            <div className="mb-4 flex flex-wrap items-end gap-3">
              <Field label="Document type">
                <select className={inputCls} value={docType} onChange={(e) => setDocType(e.target.value)} data-testid="document-type">
                  {DOCUMENT_TYPES.map((t) => <option key={t.value} value={t.value}>{t.label}</option>)}
                </select>
              </Field>
              <button type="button" onClick={() => fileInput.current?.click()} disabled={uploading} className="flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-500 disabled:opacity-50">
                <UploadCloud className="h-4 w-4" /> {uploading ? 'Uploading…' : 'Choose files'}
              </button>
              <input ref={fileInput} type="file" multiple data-testid="file-input" className="hidden" onChange={(e) => onFiles(e.target.files)} accept=".pdf,.pptx,.ppt,.docx,.doc,.xlsx,.xls,.csv,.txt,.md" />
            </div>
            <p className="mb-4 text-xs text-slate-500">PDF, PPTX, PPT, DOCX, DOC, XLSX, XLS, CSV, TXT or MD · max 25 MB · files are checked for type, corruption and executable content.</p>
            {uploadErrors.map((e) => (
              <div key={e} className="mb-2 flex items-start gap-2 rounded border border-red-500/30 bg-red-500/10 px-3 py-2 text-xs text-red-300" data-testid="upload-error">
                <X className="mt-0.5 h-3.5 w-3.5" /> {e}
              </div>
            ))}
            <ul className="divide-y divide-slate-800" data-testid="uploaded-documents">
              {uploaded.map((d) => (
                <li key={d.id} className="flex items-center justify-between py-2 text-sm">
                  <span className="flex items-center gap-2 text-slate-200"><FileText className="h-4 w-4 text-blue-400" /> {d.original_filename}</span>
                  <span className="text-xs text-slate-500">{DOCUMENT_TYPES.find((t) => t.value === d.document_type)?.label || d.document_type} · {(d.file_size / 1024).toFixed(0)} KB</span>
                </li>
              ))}
              {uploaded.length === 0 && <li className="py-3 text-sm text-slate-500">No documents uploaded yet.</li>}
            </ul>
          </Card>
          <div className="flex justify-end">
            <button type="button" disabled={uploaded.length === 0} onClick={() => setStep(3)} data-testid="finish-uploads" className="rounded-lg bg-emerald-600 px-6 py-2.5 text-sm font-semibold text-white hover:bg-emerald-500 disabled:opacity-40">
              Continue
            </button>
          </div>
        </div>
      )}

      {step === 3 && application && (
        <Card className="text-center">
          <CheckCircle2 className="mx-auto mb-3 h-12 w-12 text-emerald-400" />
          <h2 className="text-lg font-bold text-slate-100">Application submitted</h2>
          <p className="mt-2 text-sm text-slate-400">
            Reference <span className="font-mono text-slate-200">{application.application_ref}</span> · {uploaded.length} document(s) registered.
          </p>
          <Link href={`/applications/${application.id}`} data-testid="open-application" className="mt-6 inline-block rounded-lg bg-blue-600 px-6 py-2.5 text-sm font-semibold text-white hover:bg-blue-500">
            Open application &amp; start evaluation
          </Link>
        </Card>
      )}
    </div>
  );
}
