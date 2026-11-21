'use client';

import React, { use, useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useRouter } from 'next/navigation';
import { apiService } from '@/services/api';
import { useAuth } from '@/contexts/auth-context';
import { 
  ArrowLeft, 
  DownloadCloud, 
  FileText, 
  ChevronRight,
  AlertTriangle,
  FileCode,
  CheckCircle2,
  Loader2,
  Layers,
  FileDown,
  RefreshCw,
  Sparkles
} from 'lucide-react';
import { FinalReviewAssessment, DomainAssessmentReport } from '@/types';
import { SupervisoryReviewView } from '@/components/SupervisoryReviewView';
import { CanonicalDomainsView } from '@/components/CanonicalDomainsView';

export default function ReportPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const { user } = useAuth();
  const router = useRouter();

  // View mode tab: 'supervisory' | 'domains' | 'markdown' | 'sectional'
  const [activeTab, setActiveTab] = useState<'supervisory' | 'markdown' | 'sectional'>('supervisory');
  const [activeSection, setActiveSection] = useState('executive');
  const [markdownContent, setMarkdownContent] = useState<string | null>(null);
  const [isLoadingMarkdown, setIsLoadingMarkdown] = useState(false);

  // Redirect if not authenticated
  useEffect(() => {
    if (!user) {
      router.push('/login');
    }
  }, [user, router]);

  const { data: report, isLoading, error, refetch } = useQuery({
    queryKey: ['reportDetails', id],
    queryFn: () => apiService.getReport(id),
    enabled: !!user && !!id,
    retry: 2,
  });

  // Fetch markdown on demand when markdown tab is selected
  useEffect(() => {
    if (activeTab === 'markdown' && !markdownContent && id) {
      setIsLoadingMarkdown(true);
      apiService.getReportMarkdown(id)
        .then((md) => setMarkdownContent(md))
        .catch(() => setMarkdownContent('# Due Diligence Report\n\nFailed to load live markdown.'))
        .finally(() => setIsLoadingMarkdown(false));
    }
  }, [activeTab, markdownContent, id]);

  if (!user) {
    return (
      <div className="flex h-screen items-center justify-center bg-slate-950 text-slate-100">
        <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center bg-slate-950 text-slate-100">
        <div className="flex flex-col items-center space-y-4">
          <span className="h-8 w-8 animate-spin rounded-full border-4 border-blue-500 border-t-transparent"></span>
          <span className="text-xs text-slate-400">Loading due diligence report...</span>
        </div>
      </div>
    );
  }

  if (error || !report) {
    return (
      <div className="flex h-screen items-center justify-center bg-slate-950">
        <div className="p-8 text-center text-slate-500 max-w-lg mx-auto space-y-4">
          <AlertTriangle className="w-12 h-12 text-amber-500 mx-auto" />
          <h3 className="text-lg font-bold text-slate-200">Report Not Found</h3>
          <p className="text-sm text-slate-400">
            The requested investment committee due diligence report ({id}) could not be resolved or is currently being generated.
          </p>
          <div className="flex justify-center space-x-3 pt-2">
            <button
              onClick={() => refetch()}
              className="bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg px-4 py-2 text-xs font-semibold transition-colors flex items-center space-x-1.5"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              <span>Retry</span>
            </button>
            <button
              onClick={() => router.push('/upload')}
              className="bg-blue-600 hover:bg-blue-500 text-white rounded-lg px-4 py-2 text-xs font-semibold transition-colors"
            >
              Go to Uploader
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Extract Supervisory Review and Domain Reports with robust fallbacks
  const supervisoryReview: FinalReviewAssessment | null =
    (report.final_review as FinalReviewAssessment) ||
    (report.metadata?.final_review as FinalReviewAssessment) ||
    null;

  const domainReports: Record<string, DomainAssessmentReport> =
    (report.domain_reports as Record<string, DomainAssessmentReport>) ||
    (report.metadata?.domain_reports as Record<string, DomainAssessmentReport>) ||
    {};

  // Helper parsers for sectional view
  const parseInlineStyles = (text: string) => {
    const parts = text.split(/\*\*(.*?)\*\*/g);
    return parts.map((part, index) => {
      if (index % 2 === 1) {
        return <strong key={index} className="font-bold text-slate-100">{part}</strong>;
      }
      return part;
    });
  };

  const renderMarkdownContent = (text: string) => {
    const lines = text.split('\n');
    const renderedElements: React.ReactNode[] = [];
    
    let inTable = false;
    let tableHeaders: string[] = [];
    let tableRows: string[][] = [];

    for (let idx = 0; idx < lines.length; idx++) {
      const line = lines[idx].trim();
      if (!line) continue;

      if (line.includes('|')) {
        const cells = line.split('|').map(c => c.trim()).filter(c => c);
        if (cells.length > 0) {
          if (cells.every(c => c.startsWith('---') || c.startsWith(':---'))) {
            continue;
          }
          if (!inTable) {
            inTable = true;
            tableHeaders = cells;
            tableRows = [];
          } else {
            tableRows.push(cells);
          }
        }
        continue;
      } else {
        if (inTable) {
          renderedElements.push(
            <div key={`tbl-${idx}`} className="my-4 border border-slate-800 rounded-lg overflow-hidden max-w-lg">
              <table className="min-w-full divide-y divide-slate-800 text-[11px]">
                <thead className="bg-slate-900">
                  <tr>
                    {tableHeaders.map((th, i) => (
                      <th key={i} className="px-3 py-2 text-left font-bold text-slate-400">{th}</th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-900 bg-slate-950/20">
                  {tableRows.map((row, ri) => (
                    <tr key={ri} className="hover:bg-slate-900/10">
                      {row.map((cell, ci) => (
                        <td key={ci} className="px-3 py-2 text-slate-300">{cell}</td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          );
          inTable = false;
        }
      }

      if (line.startsWith('### ')) {
        renderedElements.push(
          <h4 key={idx} className="text-xs font-bold text-slate-400 uppercase tracking-widest mt-6 mb-2">
            {line.replace('### ', '')}
          </h4>
        );
      } else if (line.startsWith('* ') || line.startsWith('- ')) {
        const bulletText = line.substring(2);
        renderedElements.push(
          <div key={idx} className="flex items-start space-x-2 text-slate-300 my-1.5 ml-4">
            <span className="text-blue-500 mt-1">&bull;</span>
            <span>{parseInlineStyles(bulletText)}</span>
          </div>
        );
      } else {
        renderedElements.push(
          <p key={idx} className="my-2.5 leading-relaxed text-slate-300">
            {parseInlineStyles(line)}
          </p>
        );
      }
    }

    if (inTable) {
      renderedElements.push(
        <div key="tbl-final" className="my-4 border border-slate-800 rounded-lg overflow-hidden max-w-lg">
          <table className="min-w-full divide-y divide-slate-800 text-[11px]">
            <thead className="bg-slate-900">
              <tr>
                {tableHeaders.map((th, i) => (
                  <th key={i} className="px-3 py-2 text-left font-bold text-slate-400">{th}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-900 bg-slate-950/20">
              {tableRows.map((row, ri) => (
                <tr key={ri} className="hover:bg-slate-900/10">
                  {row.map((cell, ci) => (
                    <td key={ci} className="px-3 py-2 text-slate-300">{cell}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      );
    }

    return renderedElements;
  };

  const renderSectionContent = (content: string) => {
    if (!content) return <span className="text-slate-500 italic">No details available.</span>;
    return (
      <div className="text-slate-300 text-sm leading-relaxed space-y-4">
        {renderMarkdownContent(content)}
      </div>
    );
  };

  // Section items for legacy view
  const menuItems = [
    { id: 'executive', name: '1. Executive Summary', data: report.executive_summary },
    { id: 'investment_rec', name: '2. Investment Recommendation', data: report.investment_recommendation },
    { id: 'founder_ass', name: '3. Founder Assessment', data: report.founder_assessment },
    { id: 'product_tech', name: '4. Product & Technology', data: report.product_technology },
    { id: 'market_opp', name: '5. Market Opportunity', data: report.market_opportunity },
    { id: 'biz_model', name: '6. Business Model', data: report.business_model },
    { id: 'competition', name: '7. Competition', data: report.competition },
    { id: 'financial_ov', name: '8. Financial Overview', data: report.financial_overview },
    { id: 'risks_sec', name: '9. Risks', data: report.risks },
    { id: 'inv_thesis', name: '10. Investment Thesis', data: report.investment_thesis },
    { id: 'follow_up_qsts', name: '11. Follow-up Questions', data: report.follow_up_questions }
  ];

  const currentSection = menuItems.find(item => item.id === activeSection) || menuItems[0];

  const downloadPdf = async () => {
    try {
      const blob = await apiService.getReportPdf(id);
      if (blob.type === 'application/json') {
        const errText = await blob.text();
        const errJson = JSON.parse(errText);
        alert(errJson.message || errJson.detail || 'Failed to download PDF report from server.');
        return;
      }
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `Due_Diligence_Report_${id}.pdf`;
      link.click();
      window.URL.revokeObjectURL(url);
    } catch (err: any) {
      alert(err.response?.data?.message || err.message || 'Failed to download PDF report. Ensure backend report engine is available.');
    }
  };

  const downloadMarkdown = async () => {
    try {
      let md = markdownContent;
      if (!md) {
        md = await apiService.getReportMarkdown(id);
      }
      if (!md || typeof md !== 'string') {
        alert('Markdown content unavailable from server.');
        return;
      }
      const blob = new Blob([md], { type: 'text/markdown;charset=utf-8' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `Due_Diligence_Report_${id}.md`;
      link.click();
      window.URL.revokeObjectURL(url);
    } catch (err: any) {
      alert(err.response?.data?.message || err.message || 'Failed to download Markdown report.');
    }
  };

  const downloadJson = () => {
    const jsonStr = JSON.stringify(report, null, 2);
    const blob = new Blob([jsonStr], { type: 'application/json' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `TIDES_Traceability_Report_${id}.json`;
    link.click();
    window.URL.revokeObjectURL(url);
  };

  return (
    <div className="p-6 md:p-8 space-y-8 max-w-7xl mx-auto">
      {/* Top Header Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-900 pb-4">
        <div className="flex items-center space-x-3">
          <button
            onClick={() => router.back()}
            className="flex items-center space-x-1.5 text-xs text-slate-400 hover:text-slate-200 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Back</span>
          </button>
          <span className="text-slate-700">|</span>
          <span className="text-xs text-slate-400">Due Diligence Report:</span>
          <span className="font-mono text-xs font-bold text-slate-200">{report.report_id}</span>
          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-500/20 text-amber-300 border border-amber-500/40 uppercase tracking-wider ml-1">
            MOCK DEMONSTRATION
          </span>
        </div>

        {/* Export Buttons */}
        <div className="flex items-center space-x-2.5">
          <button
            onClick={downloadJson}
            className="flex items-center space-x-1.5 bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-300 rounded-lg px-3 py-1.5 text-xs font-medium transition-all"
            title="Download full JSON traceability graph"
          >
            <FileCode className="w-3.5 h-3.5 text-indigo-400" />
            <span>JSON</span>
          </button>
          <button
            onClick={downloadMarkdown}
            className="flex items-center space-x-1.5 bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-300 rounded-lg px-3 py-1.5 text-xs font-medium transition-all"
            title="Download Markdown report"
          >
            <FileDown className="w-3.5 h-3.5 text-blue-400" />
            <span>Markdown</span>
          </button>
          <button
            onClick={downloadPdf}
            className="flex items-center space-x-1.5 bg-blue-600 hover:bg-blue-500 text-white rounded-lg px-3.5 py-1.5 text-xs font-semibold transition-all shadow-md shadow-blue-500/20"
            title="Download PDF report"
          >
            <DownloadCloud className="w-3.5 h-3.5" />
            <span>Download PDF</span>
          </button>
        </div>
      </div>

      {/* Main Tab Controls */}
      <div className="flex items-center space-x-2 border-b border-slate-800 pb-2">
        <button
          type="button"
          onClick={() => setActiveTab('supervisory')}
          className={`flex items-center space-x-2 px-4 py-2 rounded-lg text-xs font-bold transition-all ${
            activeTab === 'supervisory'
              ? 'bg-blue-600 text-white shadow-md shadow-blue-500/20'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
          }`}
        >
          <Sparkles className="w-4 h-4" />
          <span>Supervisory & Canonical Domains</span>
        </button>

        <button
          type="button"
          onClick={() => setActiveTab('markdown')}
          className={`flex items-center space-x-2 px-4 py-2 rounded-lg text-xs font-bold transition-all ${
            activeTab === 'markdown'
              ? 'bg-blue-600 text-white shadow-md shadow-blue-500/20'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
          }`}
        >
          <FileText className="w-4 h-4" />
          <span>Markdown Document View</span>
        </button>

        <button
          type="button"
          onClick={() => setActiveTab('sectional')}
          className={`flex items-center space-x-2 px-4 py-2 rounded-lg text-xs font-bold transition-all ${
            activeTab === 'sectional'
              ? 'bg-blue-600 text-white shadow-md shadow-blue-500/20'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
          }`}
        >
          <Layers className="w-4 h-4" />
          <span>11-Section Investment Memo</span>
        </button>
      </div>

      {/* Tab 1: Supervisory & Canonical Domains View */}
      {activeTab === 'supervisory' && (
        <div className="space-y-8">
          {/* Supervisory Review Component */}
          <SupervisoryReviewView review={supervisoryReview} />

          {/* 6 Canonical Domains Component */}
          <CanonicalDomainsView domainReports={domainReports} legacyGraph={report} />
        </div>
      )}

      {/* Tab 2: Markdown Document View */}
      {activeTab === 'markdown' && (
        <div className="glass rounded-xl p-8 border border-slate-800 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <h3 className="text-sm font-bold text-slate-200 uppercase tracking-wider">
              Markdown Document View
            </h3>
            <span className="text-xs text-slate-500 font-mono">Format: GitHub Flavored Markdown</span>
          </div>

          {isLoadingMarkdown ? (
            <div className="flex items-center justify-center py-16 space-x-2 text-slate-400 text-xs">
              <Loader2 className="w-4 h-4 animate-spin text-blue-500" />
              <span>Fetching markdown report content...</span>
            </div>
          ) : (
            <div className="bg-slate-950 p-6 rounded-xl border border-slate-800 overflow-x-auto">
              <pre className="font-mono text-xs text-slate-300 whitespace-pre-wrap leading-relaxed">
                {markdownContent || 'Markdown not available.'}
              </pre>
            </div>
          )}
        </div>
      )}

      {/* Tab 3: Legacy 11-Section Memo View */}
      {activeTab === 'sectional' && (
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
          <div className="space-y-2">
            <div className="p-3 bg-slate-950 border border-slate-900 rounded-lg mb-4 text-center">
              <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest block">Report ID</span>
              <span className="font-mono text-xs font-bold text-slate-300 mt-1 block">{report.report_id}</span>
            </div>

            <nav className="space-y-1">
              {menuItems.map((item) => {
                const isActive = activeSection === item.id;
                return (
                  <button
                    key={item.id}
                    onClick={() => setActiveSection(item.id)}
                    className={`w-full flex items-center justify-between text-left px-4 py-3 rounded-lg text-xs font-semibold transition-all ${
                      isActive
                        ? 'bg-blue-600/10 text-blue-400 border border-blue-500/20'
                        : 'text-slate-400 hover:bg-slate-900/50 hover:text-slate-200 border border-transparent'
                    }`}
                  >
                    <span>{item.name}</span>
                    <ChevronRight className={`w-3.5 h-3.5 opacity-60 ${isActive ? 'block' : 'hidden'}`} />
                  </button>
                );
              })}
            </nav>
          </div>

          <div className="lg:col-span-3 space-y-6">
            <div className="glass rounded-xl p-8 border border-slate-800/50 space-y-6 min-h-[500px] flex flex-col justify-between">
              <div className="space-y-4">
                <div className="flex justify-between items-center border-b border-slate-900 pb-4">
                  <h2 className="text-lg font-bold text-slate-100">{currentSection.name.split('. ')[1]}</h2>
                  <div className="flex items-center space-x-2 text-xs">
                    <span className="text-slate-500">Confidence:</span>
                    <span className="text-blue-400 font-bold">{typeof currentSection.data?.confidence === 'number' ? currentSection.data.confidence.toFixed(2) : 'N/A'}</span>
                  </div>
                </div>

                <div className="w-full">
                  {renderSectionContent(currentSection.data?.content || '')}
                </div>
              </div>

              {/* Verification Footer */}
              <div className="pt-6 border-t border-slate-900/60 flex items-center justify-between text-[10px] text-slate-500 font-semibold">
                <div className="flex items-center space-x-1.5">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
                  <span>Verified Fact-to-Evidence Traceability Audit Check Passed</span>
                </div>
                <span>Graph Version: {report.graph_version}</span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
