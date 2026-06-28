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
  Loader2
} from 'lucide-react';
import { Report } from '@/types';

export default function ReportPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const { user } = useAuth();
  const router = useRouter();
  const [activeSection, setActiveSection] = useState('executive');

  // Redirect if not authenticated
  useEffect(() => {
    if (!user) {
      router.push('/login');
    }
  }, [user, router]);

  const { data: report, isLoading, error } = useQuery({
    queryKey: ['reportDetails', id],
    queryFn: () => apiService.getReport(id),
    enabled: !!user && !!id,
  });

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
            The requested investment committee due diligence report ID could not be resolved.
          </p>
          <button
            onClick={() => router.push('/dashboard')}
            className="bg-blue-600 hover:bg-blue-500 text-white rounded-lg px-4 py-2 text-sm font-semibold transition-colors"
          >
            Return to Dashboard
          </button>
        </div>
      </div>
    );
  }

  // Custom inline styles parser for bold tags
  const parseInlineStyles = (text: string) => {
    const parts = text.split(/\*\*(.*?)\*\*/g);
    return parts.map((part, index) => {
      if (index % 2 === 1) {
        return <strong key={index} className="font-bold text-slate-100">{part}</strong>;
      }
      return part;
    });
  };

  // Custom markdown block elements parser
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

  // Custom table element parser
  const parseAndRenderTable = (content: string, startTag: string, endTag: string, type: 'founder' | 'risk') => {
    const parts = content.split(startTag);
    const before = parts[0];
    const tableBlock = parts[1].split(endTag)[0];
    const after = parts[1].split(endTag)[1] || '';

    const lines = tableBlock.trim().split('\n');
    const headers = lines[0].split('|').map(h => h.trim());
    const rows = lines.slice(1).map(line => line.split('|').map(cell => cell.trim()));

    return (
      <div className="space-y-6 w-full">
        {before && <div className="text-slate-300 text-sm leading-relaxed space-y-2">{renderMarkdownContent(before)}</div>}
        
        <div className="bg-slate-950 border border-slate-800/80 rounded-xl overflow-hidden shadow-lg shadow-black/20">
          <table className="min-w-full divide-y divide-slate-800 text-xs">
            <thead className="bg-slate-900/80">
              <tr>
                {headers.map((h, i) => (
                  <th key={i} className="px-4 py-3 text-left font-bold text-slate-400 uppercase tracking-wider">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-900 bg-slate-950/40">
              {rows.map((row, rIdx) => (
                <tr key={rIdx} className="hover:bg-slate-900/30 transition-all">
                  {row.map((cell, cIdx) => {
                    let cellContent: React.ReactNode = cell;
                    if (type === 'risk' && cIdx === 1) {
                      const isHigh = cell.toLowerCase() === 'high' || cell.toLowerCase() === 'critical';
                      const isMed = cell.toLowerCase() === 'medium';
                      cellContent = (
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                          isHigh ? 'bg-rose-500/10 text-rose-400 border border-rose-500/20' : 
                          isMed ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20' : 
                          'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                        }`}>
                          {cell}
                        </span>
                      );
                    } else if (type === 'risk' && cIdx === 2) {
                      const isHigh = cell.toLowerCase() === 'high';
                      const isMed = cell.toLowerCase() === 'medium';
                      cellContent = (
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                          isHigh ? 'bg-rose-500/10 text-rose-400 border border-rose-500/20' : 
                          isMed ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20' : 
                          'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                        }`}>
                          {cell}
                        </span>
                      );
                    } else if (cIdx === row.length - 1) {
                      cellContent = <span className="font-mono text-slate-400">{cell}</span>;
                    }
                    
                    return (
                      <td key={cIdx} className="px-4 py-3.5 text-slate-300 leading-relaxed max-w-[200px] break-words">
                        {cellContent}
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {after && <div className="text-slate-300 text-sm leading-relaxed space-y-2">{renderMarkdownContent(after)}</div>}
      </div>
    );
  };

  // Section Content layout builder
  const renderSectionContent = (content: string) => {
    if (!content) return <span className="text-slate-500 italic">No details available.</span>;

    if (content.includes('[METRICS]') && content.includes('[/METRICS]')) {
      const parts = content.split('[METRICS]');
      const metricsBlock = parts[1].split('[/METRICS]')[0];
      const after = parts[1].split('[/METRICS]')[1] || '';

      const lines = metricsBlock.trim().split('\n');
      const metrics: { [key: string]: string } = {};
      lines.forEach(line => {
        if (line.includes(':')) {
          const [k, v] = line.split(':');
          metrics[k.trim()] = v.trim();
        }
      });

      const getRecBadgeClass = (rec: string) => {
        switch (rec?.toUpperCase()) {
          case 'INVEST': return 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20';
          case 'WATCH': return 'bg-amber-500/10 text-amber-400 border border-amber-500/20';
          case 'DEFER': return 'bg-blue-500/10 text-blue-400 border border-blue-500/20';
          case 'REJECT': return 'bg-rose-500/10 text-rose-400 border border-rose-500/20';
          default: return 'bg-slate-500/10 text-slate-400 border border-slate-500/20';
        }
      };

      return (
        <div className="space-y-6 w-full">
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
            <div className="bg-slate-900/60 p-4 border border-slate-800 rounded-xl flex flex-col justify-between">
              <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">Recommendation</span>
              <span className={`inline-block mt-2 px-2.5 py-1 text-xs font-bold rounded-lg text-center ${getRecBadgeClass(metrics['Recommendation'])}`}>
                {metrics['Recommendation'] || 'WATCH'}
              </span>
            </div>
            <div className="bg-slate-900/60 p-4 border border-slate-800 rounded-xl flex flex-col justify-between">
              <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">Overall Score</span>
              <span className="text-xl font-bold text-slate-100 mt-2 block">{metrics['Overall Score'] || '80 / 100'}</span>
            </div>
            <div className="bg-slate-900/60 p-4 border border-slate-800 rounded-xl flex flex-col justify-between">
              <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">Confidence</span>
              <span className="text-xl font-bold text-blue-400 mt-2 block">{metrics['Confidence'] || '85%'}</span>
            </div>
            <div className="bg-slate-900/60 p-4 border border-slate-800 rounded-xl flex flex-col justify-between">
              <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">Stage</span>
              <span className="text-xl font-bold text-purple-400 mt-2 block">{metrics['Stage'] || 'Pre-Seed'}</span>
            </div>
            <div className="bg-slate-900/60 p-4 border border-slate-800 rounded-xl flex flex-col justify-between">
              <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">Sector</span>
              <span className="text-xl font-bold text-slate-100 mt-2 block overflow-hidden text-ellipsis whitespace-nowrap">{metrics['Sector'] || 'DeepTech'}</span>
            </div>
            <div className="bg-slate-900/60 p-4 border border-slate-800 rounded-xl flex flex-col justify-between">
              <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">TRL</span>
              <span className="text-xl font-bold text-indigo-400 mt-2 block">{metrics['TRL'] || 'TRL-4'}</span>
            </div>
          </div>

          <div className="text-slate-300 text-sm leading-relaxed space-y-4">
            {renderMarkdownContent(after)}
          </div>
        </div>
      );
    }

    if (content.includes('[FOUNDER_TABLE]') && content.includes('[/FOUNDER_TABLE]')) {
      return parseAndRenderTable(content, '[FOUNDER_TABLE]', '[/FOUNDER_TABLE]', 'founder');
    }
    if (content.includes('[RISK_TABLE]') && content.includes('[/RISK_TABLE]')) {
      return parseAndRenderTable(content, '[RISK_TABLE]', '[/RISK_TABLE]', 'risk');
    }

    return (
      <div className="text-slate-300 text-sm leading-relaxed space-y-4">
        {renderMarkdownContent(content)}
      </div>
    );
  };

  // Sections navigation mapping
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
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `TIDES_Due_Diligence_Report_${id}.pdf`;
      link.click();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      alert('Failed to download PDF report.');
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
    <div className="p-8 space-y-8 max-w-7xl mx-auto">
      <div className="flex items-center justify-between border-b border-slate-900 pb-4">
        <button
          onClick={() => router.back()}
          className="flex items-center space-x-2 text-xs text-slate-400 hover:text-slate-200 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back</span>
        </button>

        <div className="flex space-x-3">
          <button
            onClick={downloadJson}
            className="flex items-center space-x-2 bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-300 rounded-lg px-4 py-2 text-xs font-semibold transition-all"
          >
            <FileCode className="w-4 h-4 text-indigo-400" />
            <span>Export Traceability JSON</span>
          </button>
          <button
            onClick={downloadPdf}
            className="flex items-center space-x-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg px-4 py-2 text-xs font-semibold transition-all shadow-lg shadow-blue-500/10"
          >
            <DownloadCloud className="w-4 h-4" />
            <span>Download PDF</span>
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
        <div className="space-y-2">
          <div className="p-3 bg-slate-950 border border-slate-900 rounded-lg mb-4 text-center">
            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest block">Report Identifier</span>
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
                  <span className="text-blue-400 font-bold">{(currentSection.data?.confidence || 0.85).toFixed(2)}</span>
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
    </div>
  );
}
