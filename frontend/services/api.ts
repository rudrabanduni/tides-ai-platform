import { apiClient } from '@/lib/api-client';
import { Startup, DashboardStats, Report, Portfolio, CommitteeDecision } from '@/types';

export const apiService = {
  async login(payload: any) {
    try {
      const res = await apiClient.post('/api/v1/auth/login', payload);
      return res.data;
    } catch (err: any) {
      // Auto bootstrap admin credentials on first attempt
      try {
        await apiClient.post('/api/v1/auth/bootstrap-admin', {
          name: 'Lead Incubation Manager',
          email: payload.email,
          password: payload.password,
        });
        const resRetry = await apiClient.post('/api/v1/auth/login', payload);
        return resRetry.data;
      } catch (bootstrapErr) {
        throw err;
      }
    }
  },

  // Dashboard
  async getDashboardSummary(): Promise<DashboardStats> {
    const res = await apiClient.get('/api/v1/dashboard/summary');
    return res.data;
  },

  // Startups
  async getStartups(): Promise<Startup[]> {
    const res = await apiClient.get('/api/v1/startups');
    return res.data;
  },

  async createStartup(payload: Partial<Startup>): Promise<Startup> {
    const res = await apiClient.post('/api/v1/startups', payload);
    return res.data;
  },

  async updateStartup(id: string, payload: Partial<Startup>): Promise<Startup> {
    const res = await apiClient.patch(`/api/v1/startups/${id}`, payload);
    return res.data;
  },

  async deleteStartup(id: string): Promise<void> {
    await apiClient.delete(`/api/v1/startups/${id}`);
  },

  // Ingestion & E2E Evaluation
  async evaluateStartup(formData: FormData): Promise<any> {
    const res = await apiClient.post('/api/v1/evaluate-startup', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    // This returns: { status_code, message, data: { evaluation_status, assessment_identifier, generated_report, pdf_url, pdf_base64 } }
    return res.data.data;
  },

  // Evaluation Results
  async getEvaluationResult(id: string): Promise<any> {
    const res = await apiClient.get(`/api/v1/evaluation/${id}`);
    return res.data.data;
  },

  // Reports
  async getReport(id: string): Promise<Report> {
    const res = await apiClient.get(`/api/v1/reports/${id}`);
    return res.data.data;
  },

  async getReportPdf(id: string): Promise<Blob> {
    const res = await apiClient.get(`/api/v1/reports/${id}/download`, {
      responseType: 'blob',
    });
    return res.data;
  },

  // Portfolio
  async getPortfolio(): Promise<Portfolio> {
    const res = await apiClient.get('/api/v1/portfolio');
    return res.data;
  },

  async getPortfolioStats(): Promise<any> {
    const res = await apiClient.get('/api/v1/portfolio/statistics');
    return res.data;
  },

  // Committee
  async getCommittee(): Promise<CommitteeDecision[]> {
    const res = await apiClient.get('/api/v1/committee');
    return res.data;
  },

  // API Keys
  async getApiKeys(): Promise<any[]> {
    const res = await apiClient.get('/api/v1/apikeys');
    return res.data;
  },

  async createApiKey(payload: { name: string; expiry_days?: number }): Promise<any> {
    const res = await apiClient.post('/api/v1/apikeys', payload);
    return res.data;
  },

  async deleteApiKey(keyId: string): Promise<any> {
    const res = await apiClient.delete(`/api/v1/apikeys/${keyId}`);
    return res.data;
  },
};
