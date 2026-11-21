'use client';

import React, { useState, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { apiService } from '@/services/api';
import { useAuth } from '@/contexts/auth-context';
import { 
  UploadCloud, 
  FileText, 
  CheckCircle2, 
  AlertCircle, 
  Loader2, 
  ArrowRight,
  Sparkles,
  FileSpreadsheet,
  File,
  X,
  ExternalLink,
  Download
} from 'lucide-react';

const ALLOWED_EXTENSIONS = [
  // Pitch Decks & Documents
  'pdf', 'pptx', 'ppt', 'docx', 'doc',
  // Financial Spreadsheets & Tables
  'xlsx', 'xls', 'csv'
];

const MAX_FILE_SIZE_BYTES = 25 * 1024 * 1024; // 25 MB

interface UploadError {
  fileName?: string;
  message: string;
}

export default function UploadPage() {
  const { user } = useAuth();
  const router = useRouter();
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Form inputs
  const [startupName, setStartupName] = useState('');
  const [sector, setSector] = useState('DeepTech');
  const [stage, setStage] = useState('MVP');
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);

  // Submission & Real Pipeline State
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [pipelineStage, setPipelineStage] = useState<'idle' | 'uploading' | 'evaluating' | 'completed' | 'failed'>('idle');
  const [validationErrors, setValidationErrors] = useState<UploadError[]>([]);
  const [pipelineError, setPipelineError] = useState<string | null>(null);
  const [resultData, setResultData] = useState<any>(null);

  if (!user) return null;

  const validateFiles = (files: File[]): { valid: File[]; errors: UploadError[] } => {
    const valid: File[] = [];
    const errors: UploadError[] = [];

    files.forEach((file) => {
      const ext = file.name.split('.').pop()?.toLowerCase() || '';
      if (!ALLOWED_EXTENSIONS.includes(ext)) {
        errors.push({
          fileName: file.name,
          message: `Unsupported file type (.${ext}). Supported: PDF, PPTX, PPT, DOCX, XLSX, XLS, CSV.`,
        });
        return;
      }
      if (file.size === 0) {
        errors.push({
          fileName: file.name,
          message: 'File is empty (0 bytes) and cannot be evaluated.',
        });
        return;
      }
      if (file.size > MAX_FILE_SIZE_BYTES) {
        errors.push({
          fileName: file.name,
          message: `File exceeds 25 MB size limit (${(file.size / (1024 * 1024)).toFixed(1)} MB).`,
        });
        return;
      }
      valid.push(file);
    });

    return { valid, errors };
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    if (e.dataTransfer.files) {
      const droppedFiles = Array.from(e.dataTransfer.files);
      const { valid, errors } = validateFiles(droppedFiles);
      setSelectedFiles((prev) => [...prev, ...valid]);
      setValidationErrors((prev) => [...prev, ...errors]);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const chosen = Array.from(e.target.files);
      const { valid, errors } = validateFiles(chosen);
      setSelectedFiles((prev) => [...prev, ...valid]);
      setValidationErrors((prev) => [...prev, ...errors]);
    }
  };

  const removeFile = (index: number) => {
    setSelectedFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const getFileIcon = (fileName: string) => {
    const ext = fileName.split('.').pop()?.toLowerCase();
    if (ext === 'xlsx' || ext === 'xls' || ext === 'csv') {
      return <FileSpreadsheet className="w-4 h-4 text-emerald-400" />;
    }
    if (ext === 'pptx' || ext === 'ppt') {
      return <FileText className="w-4 h-4 text-orange-400" />;
    }
    return <File className="w-4 h-4 text-blue-400" />;
  };

  const triggerUpload = async () => {
    const trimmedName = startupName.trim();
    if (!trimmedName) {
      setPipelineError('Please provide a valid startup name.');
      return;
    }
    if (selectedFiles.length === 0) {
      setPipelineError('Please upload at least one pitch deck or financial spreadsheet.');
      return;
    }

    setPipelineError(null);
    setValidationErrors([]);
    setResultData(null);
    setIsSubmitting(true);
    setPipelineStage('uploading');

    const formData = new FormData();
    formData.append('startup_name', trimmedName);
    formData.append('sector', sector);
    formData.append('stage', stage);
    selectedFiles.forEach((file) => {
      formData.append('files', file);
    });

    try {
      // In-flight status update
      setPipelineStage('evaluating');

      // Trigger the real backend E2E evaluation request
      const data = await apiService.evaluateStartup(formData);

      setResultData(data);
      if (data?.evaluation_status && !['COMPLETED', 'COMPLETED_SIMULATED'].includes(data.evaluation_status)) {
        setPipelineStage('failed');
        setPipelineError(
          data?.error_message || data?.message || `Evaluation ended with status: ${data.evaluation_status}`
        );
      } else {
        setPipelineStage('completed');
      }
    } catch (err: any) {
      setPipelineStage('failed');
      const backendMsg = err.response?.data?.message || err.response?.data?.detail || err.message;
      setPipelineError(backendMsg || 'Evaluation pipeline execution failed. Please verify files and try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="p-8 space-y-8 max-w-5xl mx-auto">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-extrabold text-slate-100 tracking-tight">Evaluate Startup</h1>
        <p className="text-slate-400 text-sm mt-1">
          Intake application materials, run the 6 canonical specialist domains, and generate a unified supervisory due diligence report.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Form Inputs (Left) */}
        <div className="lg:col-span-2 space-y-6">
          {pipelineStage !== 'completed' ? (
            <div className="glass rounded-xl p-6 border border-slate-800 space-y-5">
              <h3 className="font-bold text-lg text-slate-200 border-b border-slate-900 pb-3 flex items-center space-x-2">
                <Sparkles className="w-5 h-5 text-blue-400" />
                <span>Application Intake Information</span>
              </h3>

              <div className="space-y-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
                    Startup Name *
                  </label>
                  <input
                    type="text"
                    required
                    disabled={isSubmitting}
                    placeholder="e.g. HyperDrive Robotics"
                    value={startupName}
                    onChange={(e) => setStartupName(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-800 rounded-lg px-4 py-2.5 text-slate-200 text-sm focus:outline-none focus:border-blue-500 disabled:opacity-50"
                  />
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
                      Target Sector
                    </label>
                    <select
                      value={sector}
                      disabled={isSubmitting}
                      onChange={(e) => setSector(e.target.value)}
                      className="w-full bg-slate-900 border border-slate-800 rounded-lg px-4 py-2.5 text-slate-200 text-sm focus:outline-none focus:border-blue-500 disabled:opacity-50"
                    >
                      <option value="DeepTech">DeepTech</option>
                      <option value="AI / ML">AI / ML</option>
                      <option value="Robotics">Robotics</option>
                      <option value="Drones">Drones</option>
                      <option value="SpaceTech">SpaceTech</option>
                      <option value="DefenceTech">DefenceTech</option>
                      <option value="CleanTech">CleanTech</option>
                      <option value="ClimateTech">ClimateTech</option>
                      <option value="AgriTech">AgriTech</option>
                      <option value="BioTech">BioTech</option>
                      <option value="MedTech">MedTech</option>
                      <option value="EV & Battery">EV & Battery</option>
                      <option value="Semiconductor">Semiconductor</option>
                      <option value="Manufacturing">Manufacturing</option>
                      <option value="IoT">IoT</option>
                      <option value="Cybersecurity">Cybersecurity</option>
                      <option value="FinTech">FinTech</option>
                      <option value="HealthTech">HealthTech</option>
                      <option value="EdTech">EdTech</option>
                      <option value="SaaS">SaaS</option>
                      <option value="Other">Other</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
                      Maturity Stage
                    </label>
                    <select
                      value={stage}
                      disabled={isSubmitting}
                      onChange={(e) => setStage(e.target.value)}
                      className="w-full bg-slate-900 border border-slate-800 rounded-lg px-4 py-2.5 text-slate-200 text-sm focus:outline-none focus:border-blue-500 disabled:opacity-50"
                    >
                      <option value="Idea">Idea</option>
                      <option value="Prototype">Prototype (TRL 3-4)</option>
                      <option value="MVP">MVP (TRL 5-6)</option>
                      <option value="Validation">Validation</option>
                      <option value="Early Revenue">Early Revenue</option>
                      <option value="Growth">Growth</option>
                      <option value="Scale-up">Scale-up</option>
                    </select>
                  </div>
                </div>

                {/* Dropzone */}
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider">
                      Startup Documents & Spreadsheets *
                    </label>
                    <span className="text-[11px] text-slate-500">Max 25 MB per file</span>
                  </div>

                  <div
                    onDragOver={handleDragOver}
                    onDrop={handleDrop}
                    onClick={() => !isSubmitting && fileInputRef.current?.click()}
                    className={`border-2 border-dashed rounded-xl p-8 text-center transition-all cursor-pointer flex flex-col items-center justify-center space-y-3 ${
                      isSubmitting
                        ? 'border-slate-800 bg-slate-950/40 opacity-50 cursor-not-allowed'
                        : 'border-slate-800 hover:border-blue-500/50 bg-slate-900/30 hover:bg-slate-900/60'
                    }`}
                  >
                    <UploadCloud className="w-10 h-10 text-slate-500" />
                    <div>
                      <span className="text-sm font-semibold text-slate-200 block">
                        Drag and drop files here, or browse
                      </span>
                      <span className="text-xs text-slate-400 mt-1 block">
                        Pitch Decks: PDF, PPTX, PPT, DOCX &bull; Financials: XLSX, XLS, CSV
                      </span>
                    </div>
                    <input
                      type="file"
                      ref={fileInputRef}
                      disabled={isSubmitting}
                      onChange={handleFileChange}
                      multiple
                      accept=".pdf,.pptx,.ppt,.docx,.doc,.xlsx,.xls,.csv"
                      className="hidden"
                    />
                  </div>
                </div>

                {/* Validation Errors */}
                {validationErrors.length > 0 && (
                  <div className="space-y-1.5 p-3 rounded-lg bg-rose-950/30 border border-rose-900/40 text-xs text-rose-300">
                    <span className="font-semibold block">File validation notices:</span>
                    {validationErrors.map((err, i) => (
                      <p key={i}>&bull; {err.fileName ? `${err.fileName}: ` : ''}{err.message}</p>
                    ))}
                  </div>
                )}

                {/* Selected Files List */}
                {selectedFiles.length > 0 && (
                  <div className="space-y-2 mt-4">
                    <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                      Selected Files ({selectedFiles.length})
                    </span>
                    <div className="space-y-2 max-h-48 overflow-y-auto">
                      {selectedFiles.map((file, idx) => (
                        <div
                          key={idx}
                          className="flex items-center justify-between p-3 rounded-lg bg-slate-900 border border-slate-800/80 text-xs"
                        >
                          <div className="flex items-center space-x-3 text-slate-300 min-w-0">
                            {getFileIcon(file.name)}
                            <span className="truncate max-w-[280px] font-medium">{file.name}</span>
                            <span className="text-[11px] text-slate-500 font-mono">
                              ({(file.size / (1024 * 1024)).toFixed(2)} MB)
                            </span>
                          </div>
                          {!isSubmitting && (
                            <button
                              type="button"
                              onClick={() => removeFile(idx)}
                              className="text-slate-500 hover:text-rose-400 p-1"
                              title="Remove file"
                            >
                              <X className="w-4 h-4" />
                            </button>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* In-Flight Real Pipeline Feedback */}
              {isSubmitting && (
                <div className="p-4 rounded-xl bg-blue-950/20 border border-blue-900/40 text-blue-300 space-y-2">
                  <div className="flex items-center space-x-2 text-xs font-semibold">
                    <Loader2 className="w-4 h-4 animate-spin text-blue-400" />
                    <span>
                      {pipelineStage === 'uploading'
                        ? 'Uploading application documents to server...'
                        : 'Orchestrating 6 canonical specialist domains and supervisory synthesis...'}
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-400 leading-relaxed">
                    Executing fact-base claim extraction, specialist analysis across all LaunchIndex criteria, and supervisory conflict auditing. Please do not close this window.
                  </p>
                </div>
              )}

              {/* Pipeline Error Banner */}
              {pipelineError && (
                <div className="bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs p-4 rounded-lg flex items-start space-x-2.5">
                  <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
                  <span>{pipelineError}</span>
                </div>
              )}

              <button
                type="button"
                disabled={isSubmitting || selectedFiles.length === 0 || !startupName.trim()}
                onClick={triggerUpload}
                className="w-full bg-blue-600 hover:bg-blue-500 disabled:bg-slate-800 disabled:text-slate-500 disabled:cursor-not-allowed text-white rounded-lg py-3 font-semibold transition-colors shadow-lg shadow-blue-500/10 text-sm flex items-center justify-center space-x-2"
              >
                {isSubmitting ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span>Running Evaluation Pipeline...</span>
                  </>
                ) : (
                  <span>Start AI Evaluation Pipeline</span>
                )}
              </button>
            </div>
          ) : (
            /* Completed Pipeline State Card */
            <div className="glass rounded-xl p-8 border border-emerald-500/30 bg-emerald-950/10 space-y-6">
              <div className="flex items-start space-x-3">
                <div className="p-2 rounded-full bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 mt-0.5">
                  <CheckCircle2 className="w-6 h-6" />
                </div>
                <div className="space-y-1">
                  <h3 className="text-xl font-bold text-slate-100">Due Diligence Pipeline Complete!</h3>
                  <p className="text-xs text-slate-400">
                    All six specialist domain assessments and supervisory synthesis have been successfully generated.
                  </p>
                </div>
              </div>

              {/* Assessment IDs & Telemetry */}
              <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-2 text-xs">
                <div className="flex items-center justify-between text-slate-300">
                  <span className="text-slate-500">Evaluation Report Identifier:</span>
                  <span className="font-mono font-bold text-emerald-400">
                    {resultData?.assessment_identifier || 'DD-TIDES-AI'}
                  </span>
                </div>
                <div className="flex items-center justify-between text-slate-300">
                  <span className="text-slate-500">Startup Evaluated:</span>
                  <span className="font-semibold text-slate-200">{startupName}</span>
                </div>
                <div className="flex items-center justify-between text-slate-300">
                  <span className="text-slate-500">Status:</span>
                  <div className="flex items-center space-x-2">
                    <span className="font-semibold text-emerald-400">COMPLETED</span>
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-500/20 text-amber-300 border border-amber-500/40 uppercase">
                      MOCK DEMONSTRATION
                    </span>
                  </div>
                </div>
              </div>

              {/* Direct Navigation Actions */}
              <div className="flex flex-col sm:flex-row gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => router.push(`/reports/${resultData?.assessment_identifier}`)}
                  className="flex-1 px-4 py-2.5 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-semibold transition-colors flex items-center justify-center space-x-2"
                >
                  <span>Open Due Diligence Report</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </button>

                <button
                  type="button"
                  onClick={() => router.push(`/evaluations/${resultData?.startup_id || resultData?.assessment_identifier}`)}
                  className="px-4 py-2.5 bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-300 rounded-lg text-xs font-semibold transition-colors flex items-center justify-center space-x-2"
                >
                  <ExternalLink className="w-3.5 h-3.5" />
                  <span>View Knowledge Graph</span>
                </button>

                <button
                  type="button"
                  onClick={async () => {
                    try {
                      if (resultData?.assessment_identifier) {
                        const blob = await apiService.getReportPdf(resultData.assessment_identifier);
                        if (blob.type === 'application/json') {
                          const errText = await blob.text();
                          const errJson = JSON.parse(errText);
                          alert(errJson.message || 'PDF report is not available.');
                          return;
                        }
                        const url = window.URL.createObjectURL(blob);
                        const link = document.createElement('a');
                        link.href = url;
                        link.download = `Due_Diligence_Report_${resultData.assessment_identifier}.pdf`;
                        link.click();
                        window.URL.revokeObjectURL(url);
                      } else if (resultData?.pdf_base64) {
                        const link = document.createElement('a');
                        link.href = `data:application/pdf;base64,${resultData.pdf_base64}`;
                        link.download = `Due_Diligence_Report_${resultData.assessment_identifier || 'evaluation'}.pdf`;
                        link.click();
                      }
                    } catch (err: any) {
                      alert(err.response?.data?.message || err.message || 'Failed to download PDF report.');
                    }
                  }}
                  className="px-4 py-2.5 border border-emerald-500/30 text-emerald-400 hover:bg-emerald-500/10 rounded-lg text-xs font-semibold transition-colors flex items-center justify-center space-x-2"
                >
                  <Download className="w-3.5 h-3.5" />
                  <span>Download PDF</span>
                </button>
              </div>

              <div className="border-t border-slate-900 pt-4 text-center">
                <button
                  type="button"
                  onClick={() => {
                    setPipelineStage('idle');
                    setResultData(null);
                    setSelectedFiles([]);
                    setStartupName('');
                  }}
                  className="text-xs text-slate-500 hover:text-slate-300 underline"
                >
                  Evaluate Another Startup
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Right Info Panel */}
        <div className="space-y-6">
          <div className="glass rounded-xl p-6 border border-slate-800 space-y-4">
            <h4 className="font-bold text-xs text-slate-300 uppercase tracking-wider">
              Canonical Evaluation Framework
            </h4>
            <p className="text-xs text-slate-400 leading-relaxed">
              Every document format is extracted into the canonical LaunchIndex criteria registry before evaluation:
            </p>
            <ul className="text-xs text-slate-400 space-y-2.5">
              <li className="flex items-start space-x-2">
                <span className="w-1.5 h-1.5 bg-blue-400 rounded-full mt-1.5 flex-shrink-0" />
                <span><strong className="text-slate-300">1. Problem & Solution:</strong> Validates user pain, proposition, and Technology & TRL feasibility (PS-09 to PS-13).</span>
              </li>
              <li className="flex items-start space-x-2">
                <span className="w-1.5 h-1.5 bg-indigo-400 rounded-full mt-1.5 flex-shrink-0" />
                <span><strong className="text-slate-300">2. Market Opportunity & Competition:</strong> Analyzes TAM/SAM/SOM, CAGR, and defensibility against incumbents.</span>
              </li>
              <li className="flex items-start space-x-2">
                <span className="w-1.5 h-1.5 bg-purple-400 rounded-full mt-1.5 flex-shrink-0" />
                <span><strong className="text-slate-300">3. Founder & Team Capability:</strong> Evaluates founder pedigrees, domain commitment, and hiring roadmap.</span>
              </li>
              <li className="flex items-start space-x-2">
                <span className="w-1.5 h-1.5 bg-emerald-400 rounded-full mt-1.5 flex-shrink-0" />
                <span><strong className="text-slate-300">4. Business Model & Commercialisation:</strong> Scrutinizes pricing unit economics, sales channels, and customer traction.</span>
              </li>
              <li className="flex items-start space-x-2">
                <span className="w-1.5 h-1.5 bg-rose-400 rounded-full mt-1.5 flex-shrink-0" />
                <span><strong className="text-slate-300">5. Innovation, IP & Impact:</strong> Investigates proprietary moats, patents, regulatory barriers, and SDG impact.</span>
              </li>
              <li className="flex items-start space-x-2">
                <span className="w-1.5 h-1.5 bg-amber-400 rounded-full mt-1.5 flex-shrink-0" />
                <span><strong className="text-slate-300">6. Financials & Incubation Support:</strong> Evaluates multi-year pro forma, runway, burn rate, and TIDES support needs.</span>
              </li>
            </ul>
          </div>

          <div className="glass rounded-xl p-6 border border-slate-800 space-y-3 bg-slate-950/40">
            <h4 className="font-bold text-xs text-slate-400 uppercase tracking-wider">
              Evidence Attribution
            </h4>
            <p className="text-xs text-slate-500 leading-relaxed">
              Every specialist finding maintains strict link traceability back to slide numbers and document quotes. Unsubstantiated claims are flagged for committee review.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
