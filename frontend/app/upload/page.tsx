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
  Sparkles
} from 'lucide-react';

interface StepperState {
  step: number;
  status: 'idle' | 'running' | 'completed' | 'failed';
  error?: string;
}

export default function UploadPage() {
  const { user } = useAuth();
  const router = useRouter();
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Form inputs
  const [startupName, setStartupName] = useState('');
  const [sector, setSector] = useState('SaaS');
  const [stage, setStage] = useState('Pre-Seed');
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);

  // Stepper state
  const [stepper, setStepper] = useState<StepperState>({
    step: 0,
    status: 'idle',
  });

  const [resultData, setResultData] = useState<any>(null);

  const stepsList = [
    { label: 'File Upload & Ingestion', desc: 'Securely saving pitch deck on server' },
    { label: 'Document Parsing & Extraction', desc: 'Parsing PDF/DOCX content to layout text' },
    { label: 'Startup Profile Extraction', desc: 'Running AI schema extractor on parsed text' },
    { label: 'Fact Base Generation', desc: 'Cataloging factual claims and verification evidence' },
    { label: 'Multi-Agent Assessments', desc: 'Coordinating Founder, Product, & Market Experts' },
    { label: 'Graph Build & Reports', desc: 'Resolving conflicts and compiling PDF bytes' }
  ];

  if (!user) return null;

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    if (e.dataTransfer.files) {
      const files = Array.from(e.dataTransfer.files);
      setSelectedFiles((prev) => [...prev, ...files]);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const files = Array.from(e.target.files);
      setSelectedFiles((prev) => [...prev, ...files]);
    }
  };

  const removeFile = (index: number) => {
    setSelectedFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const triggerUpload = async () => {
    if (!startupName.trim()) {
      alert('Please enter a startup name.');
      return;
    }
    if (selectedFiles.length === 0) {
      alert('Please upload at least one startup document.');
      return;
    }

    setResultData(null);
    setStepper({ step: 1, status: 'running' });

    const formData = new FormData();
    formData.append('startup_name', startupName);
    formData.append('sector', sector);
    formData.append('stage', stage);
    selectedFiles.forEach((file) => {
      formData.append('files', file);
    });

    try {
      // Step 1: Uploading
      await delay(1200);
      setStepper({ step: 2, status: 'running' });

      // Step 2: Parsing
      await delay(1500);
      setStepper({ step: 3, status: 'running' });

      // Step 3: Profile Extraction
      await delay(1800);
      setStepper({ step: 4, status: 'running' });

      // Step 4: Claim seeding
      await delay(1500);
      setStepper({ step: 5, status: 'running' });

      // Step 5: Multi-agent assessments
      // Trigger the actual backend E2E coordination request
      const data = await apiService.evaluateStartup(formData);
      
      setStepper({ step: 6, status: 'running' });
      await delay(1200);

      setResultData(data);
      setStepper({ step: 6, status: 'completed' });
    } catch (err: any) {
      setStepper({
        step: stepper.step,
        status: 'failed',
        error: err.response?.data?.message || err.message || 'Evaluation pipeline failed.'
      });
    }
  };

  const delay = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

  return (
    <div className="p-8 space-y-8 max-w-4xl mx-auto">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-extrabold text-slate-100 tracking-tight">Evaluate Startup</h1>
        <p className="text-slate-400 text-sm mt-1">Upload a pitch deck to execute the end-to-end evaluation pipeline</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Form Inputs (Left) */}
        <div className="lg:col-span-2 space-y-6">
          {stepper.status === 'idle' || stepper.status === 'failed' ? (
            <div className="glass rounded-xl p-6 border border-slate-800/50 space-y-5">
              <h3 className="font-bold text-lg text-slate-200 border-b border-slate-900 pb-3 flex items-center space-x-2">
                <Sparkles className="w-5 h-5 text-blue-400" />
                <span>Applicant Information</span>
              </h3>

              <div className="space-y-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Startup Name</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. Acme AI Technologies"
                    value={startupName}
                    onChange={(e) => setStartupName(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-800 rounded-lg px-4 py-2.5 text-slate-200 text-sm focus:outline-none focus:border-blue-500"
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Sector</label>
                    <select
                      value={sector ?? ""}
                      onChange={(e) => setSector(e.target.value)}
                      className="w-full bg-slate-900 border border-slate-800 rounded-lg px-4 py-2.5 text-slate-200 text-sm focus:outline-none focus:border-blue-500"
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
                    <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Stage</label>
                    <select
                      value={stage ?? ""}
                      onChange={(e) => setStage(e.target.value)}
                      className="w-full bg-slate-900 border border-slate-800 rounded-lg px-4 py-2.5 text-slate-200 text-sm focus:outline-none focus:border-blue-500"
                    >
                      <option value="Idea">Idea</option>
                      <option value="Prototype">Prototype</option>
                      <option value="MVP">MVP</option>
                      <option value="Validation">Validation</option>
                      <option value="Early Revenue">Early Revenue</option>
                      <option value="Growth">Growth</option>
                      <option value="Scale-up">Scale-up</option>
                    </select>
                  </div>
                </div>

                {/* Dropzone */}
                <div>
                  <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Pitch Deck Documents</label>
                  <div
                    onDragOver={handleDragOver}
                    onDrop={handleDrop}
                    onClick={() => fileInputRef.current?.click()}
                    className="border-2 border-dashed border-slate-800 hover:border-blue-500/50 rounded-xl p-8 text-center bg-slate-900/30 hover:bg-slate-900/50 transition-all cursor-pointer flex flex-col items-center justify-center space-y-3"
                  >
                    <UploadCloud className="w-10 h-10 text-slate-500" />
                    <span className="text-sm font-semibold text-slate-300">Drag and drop pitch deck here</span>
                    <span className="text-xs text-slate-500">Supports PDF, DOCX, PPTX (max 20MB)</span>
                    <input
                      type="file"
                      ref={fileInputRef}
                      onChange={handleFileChange}
                      multiple
                      className="hidden"
                    />
                  </div>
                </div>

                {/* Selected Files */}
                {selectedFiles.length > 0 && (
                  <div className="space-y-2 mt-4">
                    <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Uploaded files</span>
                    {selectedFiles.map((file, idx) => (
                      <div key={idx} className="flex items-center justify-between p-3 rounded-lg bg-slate-900 border border-slate-800/80">
                        <div className="flex items-center space-x-3 text-slate-300 text-sm">
                          <FileText className="w-4 h-4 text-blue-400" />
                          <span className="truncate max-w-[200px]">{file.name}</span>
                          <span className="text-xs text-slate-500">({(file.size / 1024 / 1024).toFixed(2)} MB)</span>
                        </div>
                        <button
                          type="button"
                          onClick={() => removeFile(idx)}
                          className="text-slate-500 hover:text-red-400 text-xs"
                        >
                          Remove
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {stepper.status === 'failed' && (
                <div className="bg-red-500/10 border border-red-500/20 text-red-400 text-sm px-4 py-3 rounded-lg flex items-center space-x-2">
                  <AlertCircle className="w-5 h-5 flex-shrink-0" />
                  <span>{stepper.error}</span>
                </div>
              )}

              <button
                type="button"
                onClick={triggerUpload}
                className="w-full bg-blue-600 hover:bg-blue-500 text-white rounded-lg py-3 font-semibold transition-colors shadow-lg shadow-blue-500/20 text-sm"
              >
                Start AI Analysis Pipeline
              </button>
            </div>
          ) : (
            /* Running Stepper Progress */
            <div className="glass rounded-xl p-8 border border-slate-800/50 space-y-8 flex flex-col justify-center">
              <div className="text-center space-y-2">
                <h3 className="font-extrabold text-xl text-slate-200">Processing Evaluation</h3>
                <p className="text-slate-400 text-xs">The TIDES multi-agent orchestrator is evaluating startup profiles</p>
              </div>

              {/* Progress Bar */}
              <div className="w-full bg-slate-900 h-2 rounded-full overflow-hidden">
                <div 
                  className="bg-blue-500 h-full transition-all duration-300 rounded-full" 
                  style={{ width: `${(stepper.step / stepsList.length) * 100}%` }}
                ></div>
              </div>

              <div className="space-y-6">
                {stepsList.map((step, idx) => {
                  const stepNum = idx + 1;
                  const isCompleted = stepper.step > stepNum || (stepper.step === stepNum && stepper.status === 'completed');
                  const isCurrent = stepper.step === stepNum && stepper.status === 'running';
                  const isPending = stepper.step < stepNum;

                  return (
                    <div key={idx} className="flex items-start space-x-4">
                      {isCompleted ? (
                        <div className="p-1 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                          <CheckCircle2 className="w-5 h-5" />
                        </div>
                      ) : isCurrent ? (
                        <div className="p-1 rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/20">
                          <Loader2 className="w-5 h-5 animate-spin" />
                        </div>
                      ) : (
                        <div className="w-7 h-7 rounded-full bg-slate-900 border border-slate-800 flex items-center justify-center text-xs font-semibold text-slate-500">
                          {stepNum}
                        </div>
                      )}
                      <div>
                        <h4 className={`text-sm font-semibold ${isPending ? 'text-slate-600' : 'text-slate-200'}`}>
                          {step.label}
                        </h4>
                        <p className="text-xs text-slate-500 mt-0.5">{step.desc}</p>
                      </div>
                    </div>
                  );
                })}
              </div>

              {stepper.status === 'completed' && resultData && (
                <div className="bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-sm p-6 rounded-xl space-y-4">
                  <div className="flex items-center space-x-2">
                    <CheckCircle2 className="w-5 h-5" />
                    <span className="font-semibold">Pipeline Complete!</span>
                  </div>
                  <p className="text-slate-400 text-xs">
                    Startup evaluated successfully. Due diligence report ID: <span className="text-slate-200 font-semibold">{resultData.assessment_identifier}</span>.
                  </p>
                  <div className="flex space-x-3 pt-2">
                    <button
                      onClick={() => router.push(`/reports/${resultData.assessment_identifier}`)}
                      className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-semibold transition-colors flex items-center space-x-2"
                    >
                      <span>Open Report</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </button>
                    <button
                      onClick={() => {
                        // Download PDF from base64 string
                        const link = document.createElement('a');
                        link.href = `data:application/pdf;base64,${resultData.pdf_base64}`;
                        link.download = `Due_Diligence_Report_${resultData.assessment_identifier}.pdf`;
                        link.click();
                      }}
                      className="px-4 py-2 border border-emerald-500/30 text-emerald-400 hover:bg-emerald-500/10 rounded-lg text-xs font-semibold transition-colors"
                    >
                      Download PDF
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Informative Side Panel (Right) */}
        <div className="space-y-6">
          <div className="glass rounded-xl p-6 border border-slate-800/50 space-y-4">
            <h4 className="font-bold text-sm text-slate-200 uppercase tracking-wider">Evaluation Specs</h4>
            <ul className="text-xs text-slate-400 space-y-3">
              <li className="flex items-start space-x-2">
                <span className="w-1.5 h-1.5 bg-blue-500 rounded-full mt-1.5 flex-shrink-0"></span>
                <span>The upload parses content layout structure cleanly from documents.</span>
              </li>
              <li className="flex items-start space-x-2">
                <span className="w-1.5 h-1.5 bg-blue-500 rounded-full mt-1.5 flex-shrink-0"></span>
                <span>The analysis engine generates and links factual evidence verification records.</span>
              </li>
              <li className="flex items-start space-x-2">
                <span className="w-1.5 h-1.5 bg-blue-500 rounded-full mt-1.5 flex-shrink-0"></span>
                <span>Experts evaluate founder experience, product-market fit, and technical risk.</span>
              </li>
              <li className="flex items-start space-x-2">
                <span className="w-1.5 h-1.5 bg-blue-500 rounded-full mt-1.5 flex-shrink-0"></span>
                <span>Evaluation metrics flow directly into the final portfolio analytics and decision system.</span>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}
