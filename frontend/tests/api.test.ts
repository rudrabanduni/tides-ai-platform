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
});
