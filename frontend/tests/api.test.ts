import { describe, it, expect, vi } from 'vitest';
import { apiService } from '../services/api';
import { apiClient } from '../lib/api-client';

// Mock the apiClient module
vi.mock('../lib/api-client', () => {
  return {
    apiClient: {
      post: vi.fn(),
      get: vi.fn(),
      patch: vi.fn(),
      delete: vi.fn(),
    },
  };
});

describe('TIDES Frontend API Service Layer', () => {
  it('should authenticate user and handle JWT credentials exchange', async () => {
    const mockAuthResponse = {
      data: {
        access_token: 'valid_access_token',
        refresh_token: 'valid_refresh_token',
        user: { id: 'usr-1', email: 'analyst@tides.ai', name: 'Lead Analyst', role: 'Evaluator' }
      }
    };
    
    vi.mocked(apiClient.post).mockResolvedValueOnce(mockAuthResponse);
    
    const result = await apiService.login({ email: 'analyst@tides.ai', password: 'password' });
    
    expect(apiClient.post).toHaveBeenCalledWith('/api/v1/auth/login', {
      email: 'analyst@tides.ai',
      password: 'password'
    });
    expect(result.access_token).toBe('valid_access_token');
    expect(result.user.email).toBe('analyst@tides.ai');
  });

  it('should fetch dashboard aggregate summaries from backend repositories', async () => {
    const mockSummary = {
      data: {
        total_startups: 10,
        recommended: 4,
        review: 3,
        rejected: 3,
        approved_startups: 5,
        pending_committee_review: 2,
        ai_recommended: 4,
        final_rejected: 2
      }
    };
    
    vi.mocked(apiClient.get).mockResolvedValueOnce(mockSummary);
    
    const stats = await apiService.getDashboardSummary();
    
    expect(apiClient.get).toHaveBeenCalledWith('/api/v1/dashboard/summary');
    expect(stats.total_startups).toBe(10);
    expect(stats.ai_recommended).toBe(4);
  });

  it('should list all ingested startups from CRUD services', async () => {
    const mockList = {
      data: [
        { id: '1', startup_name: 'Alpha Tech', sector: 'SaaS', stage: 'Seed', created_at: '2026-06-25', updated_at: '2026-06-25' }
      ]
    };
    
    vi.mocked(apiClient.get).mockResolvedValueOnce(mockList);
    
    const startups = await apiService.getStartups();
    
    expect(apiClient.get).toHaveBeenCalledWith('/api/v1/startups');
    expect(startups.length).toBe(1);
    expect(startups[0].startup_name).toBe('Alpha Tech');
  });

  it('should trigger evaluateStartup with multipart form data', async () => {
    const mockEvalResponse = {
      data: {
        data: {
          evaluation_status: 'COMPLETED',
          assessment_identifier: 'DD-TEST-2026-01',
          generated_report: { report_id: 'DD-TEST-2026-01' },
          pdf_url: '/api/v1/reports/DD-TEST-2026-01/download',
          pdf_base64: 'JVBERi0xLjQK...',
        }
      }
    };

    vi.mocked(apiClient.post).mockResolvedValueOnce(mockEvalResponse);

    const formData = new FormData();
    formData.append('startup_name', 'Quantum Motors');
    formData.append('sector', 'EV & Battery');
    formData.append('stage', 'Prototype');

    const result = await apiService.evaluateStartup(formData);

    expect(apiClient.post).toHaveBeenCalledWith(
      '/api/v1/evaluate-startup',
      formData,
      expect.objectContaining({
        headers: { 'Content-Type': 'multipart/form-data' },
      })
    );
    expect(result.evaluation_status).toBe('COMPLETED');
    expect(result.assessment_identifier).toBe('DD-TEST-2026-01');
  });

  it('should fetch due diligence report by ID', async () => {
    const mockReportResponse = {
      data: {
        data: {
          report_id: 'DD-TEST-2026-01',
          generated_at: '2026-10-20T20:00:00Z',
          graph_version: '1.0.0',
          final_review: {
            overall_recommendation: 'INCUBATE',
            investment_score: 84.5,
          },
        }
      }
    };

    vi.mocked(apiClient.get).mockResolvedValueOnce(mockReportResponse);

    const report = await apiService.getReport('DD-TEST-2026-01');

    expect(apiClient.get).toHaveBeenCalledWith('/api/v1/reports/DD-TEST-2026-01');
    expect(report.report_id).toBe('DD-TEST-2026-01');
    expect(report.final_review?.overall_recommendation).toBe('INCUBATE');
  });

  it('should fetch markdown report text by ID', async () => {
    const mockMdResponse = {
      data: {
        data: '# Due Diligence Report: DD-TEST-2026-01\n\n**Recommendation:** INCUBATE'
      }
    };

    vi.mocked(apiClient.get).mockResolvedValueOnce(mockMdResponse);

    const md = await apiService.getReportMarkdown('DD-TEST-2026-01');

    expect(apiClient.get).toHaveBeenCalledWith('/api/v1/reports/DD-TEST-2026-01/markdown');
    expect(md).toContain('# Due Diligence Report: DD-TEST-2026-01');
  });

  it('should download report PDF as blob', async () => {
    const mockBlob = new Blob(['%PDF-1.4 mock content'], { type: 'application/pdf' });
    vi.mocked(apiClient.get).mockResolvedValueOnce({ data: mockBlob });

    const blob = await apiService.getReportPdf('DD-TEST-2026-01');

    expect(apiClient.get).toHaveBeenCalledWith('/api/v1/reports/DD-TEST-2026-01/download', {
      responseType: 'blob',
    });
    expect(blob).toBe(mockBlob);
  });

  it('should not auto-bootstrap admin when login fails with 401', async () => {
    vi.mocked(apiClient.post).mockReset();
    vi.mocked(apiClient.post).mockRejectedValueOnce({
      response: { status: 401, data: { detail: 'Invalid credentials' } },
    });

    await expect(
      apiService.login({ email: 'bad@tides.ai', password: 'wrong' })
    ).rejects.toBeDefined();

    expect(apiClient.post).toHaveBeenCalledTimes(1);
    expect(apiClient.post).toHaveBeenCalledWith('/api/v1/auth/login', {
      email: 'bad@tides.ai',
      password: 'wrong',
    });
  });

  it('should unwrap envelope payloads for startups, portfolio, and committee endpoints', async () => {
    vi.mocked(apiClient.get).mockResolvedValueOnce({
      data: { data: { items: [{ id: 's-1', startup_name: 'Env Co', sector: 'MedTech', stage: 'Seed' }] } },
    });
    const startups = await apiService.getStartups();
    expect(startups).toHaveLength(1);
    expect(startups[0].startup_name).toBe('Env Co');

    vi.mocked(apiClient.get).mockResolvedValueOnce({
      data: {
        success: true,
        data: { items: [{ startup_id: 's-1', startup_name: 'Env Co', investment_score: 81.2, recommendation: 'INCUBATE' }] },
      },
    });
    const portfolio = await apiService.getPortfolio();
    expect(portfolio.entries).toHaveLength(1);
    expect(portfolio.entries[0].investment_score).toBe(81.2);

    vi.mocked(apiClient.get).mockResolvedValueOnce({
      data: {
        success: true,
        data: { items: [{ decision_id: 'd-1', startup_id: 's-1', startup_name: 'Env Co', recommendation: 'INCUBATE' }] },
      },
    });
    const decisions = await apiService.getCommittee();
    expect(decisions).toHaveLength(1);
    expect(decisions[0].recommendation).toBe('INCUBATE');
  });
});
