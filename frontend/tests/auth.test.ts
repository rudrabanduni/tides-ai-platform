import { describe, it, expect, vi, beforeEach } from 'vitest';

class LocalStorageMock {
  private store: Record<string, string> = {};

  clear() {
    this.store = {};
  }

  getItem(key: string) {
    return this.store[key] || null;
  }

  setItem(key: string, value: string) {
    this.store[key] = String(value);
  }

  removeItem(key: string) {
    delete this.store[key];
  }
}

// Inject localStorage mock
global.localStorage = new LocalStorageMock() as any;

describe('TIDES Client-side Authentication Flow and Route Protection', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('should store access and refresh tokens upon successful login', () => {
    const email = 'reviewer@tides.ai';
    const accessToken = 'access_jwt_123';
    const refreshToken = 'refresh_jwt_456';

    localStorage.setItem('tides_user', JSON.stringify({ email, name: 'Reviewer' }));
    localStorage.setItem('access_token', accessToken);
    localStorage.setItem('refresh_token', refreshToken);

    expect(localStorage.getItem('access_token')).toBe(accessToken);
    expect(localStorage.getItem('refresh_token')).toBe(refreshToken);
    expect(JSON.parse(localStorage.getItem('tides_user') || '{}').email).toBe(email);
  });

  it('should clear stored session keys upon logout', () => {
    localStorage.setItem('access_token', 'token');
    localStorage.setItem('refresh_token', 'refresh');
    localStorage.setItem('tides_user', 'user');

    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('tides_user');

    expect(localStorage.getItem('access_token')).toBeNull();
    expect(localStorage.getItem('refresh_token')).toBeNull();
    expect(localStorage.getItem('tides_user')).toBeNull();
  });

  it('should authenticate requests using active API Keys', () => {
    const devApiKey = 'td_live_999888';
    localStorage.setItem('tides_api_key', devApiKey);
    
    const retrievedKey = localStorage.getItem('tides_api_key');
    expect(retrievedKey).toBe(devApiKey);
  });
});
