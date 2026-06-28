'use client';

import React, { useState } from 'react';
import { useAuth } from '@/contexts/auth-context';
import { apiService } from '@/services/api';
import { ShieldCheck } from 'lucide-react';

export default function LoginPage() {
  const { login } = useAuth();
  const [email, setEmail] = useState('analyst@tides.ai');
  const [password, setPassword] = useState('password');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const data = await apiService.login({ email, password });
      const userPayload = {
        id: data.user.id || 'usr-1',
        email: data.user.email,
        name: data.user.name || 'Lead Incubation Manager',
        role: data.user.role?.name || 'Evaluator',
      };
      login(userPayload, data.access_token, data.refresh_token);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Authentication failed. Please check credentials.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-950 px-4 relative overflow-hidden">
      {/* Background gradients */}
      <div className="absolute top-1/4 left-1/4 -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl pointer-events-none"></div>
      <div className="absolute bottom-1/4 right-1/4 translate-x-1/2 translate-y-1/2 w-96 h-96 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none"></div>

      <div className="w-full max-w-md glass rounded-2xl p-8 relative z-10">
        <div className="flex flex-col items-center mb-8">
          <div className="bg-blue-600/10 p-3 rounded-2xl text-blue-400 mb-4 border border-blue-500/20">
            <ShieldCheck className="w-8 h-8" />
          </div>
          <h2 className="text-2xl font-bold text-slate-100">Welcome to TIDES</h2>
          <p className="text-slate-400 text-xs mt-2">Venture Intelligence & Decision Engine</p>
        </div>

        {error && (
          <div className="bg-red-500/10 border border-red-500/20 text-red-400 text-sm px-4 py-2.5 rounded-lg mb-6">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Email Address</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full bg-slate-900 border border-slate-800 rounded-lg px-4 py-3 text-slate-100 placeholder-slate-500 focus:outline-none focus:border-blue-500 transition-colors text-sm"
              required
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full bg-slate-900 border border-slate-800 rounded-lg px-4 py-3 text-slate-100 placeholder-slate-500 focus:outline-none focus:border-blue-500 transition-colors text-sm"
              required
            />
          </div>

          <div className="flex items-center justify-between text-xs text-slate-400">
            <label className="flex items-center space-x-2 cursor-pointer">
              <input type="checkbox" defaultChecked className="rounded border-slate-800 bg-slate-900 text-blue-500 focus:ring-0" />
              <span>Remember me</span>
            </label>
            <span className="hover:text-blue-400 cursor-pointer">Forgot password?</span>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-600 hover:bg-blue-500 text-white rounded-lg py-3 font-semibold transition-colors shadow-lg shadow-blue-500/20 text-sm flex items-center justify-center"
          >
            {loading ? (
              <span className="h-5 w-5 animate-spin rounded-full border-2 border-white border-t-transparent"></span>
            ) : (
              'Sign In'
            )}
          </button>
        </form>

        <div className="mt-8 text-center text-xs text-slate-500">
          Demo login: <span className="text-slate-400">analyst@tides.ai</span> / <span className="text-slate-400">password</span>
        </div>
      </div>
    </div>
  );
}
