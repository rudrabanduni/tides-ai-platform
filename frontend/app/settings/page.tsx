'use client';

import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiService } from '@/services/api';
import { useAuth } from '@/contexts/auth-context';
import { 
  Key, 
  Trash2, 
  Plus, 
  Copy, 
  Check, 
  User, 
  Building,
} from 'lucide-react';

export default function SettingsPage() {
  const { user } = useAuth();
  const queryClient = useQueryClient();

  const [keyName, setKeyName] = useState('');
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [newGeneratedKey, setNewGeneratedKey] = useState<string | null>(null);
  const [apiError, setApiError] = useState<string | null>(null);

  const extractError = (err: any, fallback: string) => {
    if (err?.response?.status === 403) {
      return 'Admin role required to view or manage developer API keys.';
    }
    return err?.response?.data?.detail || err?.response?.data?.message || err?.message || fallback;
  };

  const {
    data: keys = [],
    isLoading: keysLoading,
    isError: keysIsError,
    error: keysError,
  } = useQuery({
    queryKey: ['apiKeys'],
    queryFn: () => apiService.getApiKeys(),
    enabled: !!user,
    retry: false,
  });

  const createMutation = useMutation({
    mutationFn: (payload: { name: string }) => apiService.createApiKey(payload),
    onSuccess: (data) => {
      setApiError(null);
      queryClient.invalidateQueries({ queryKey: ['apiKeys'] });
      setKeyName('');
      if (data && data.key) {
        setNewGeneratedKey(data.key);
      }
    },
    onError: (err: any) => {
      setApiError(extractError(err, 'Failed to generate API key.'));
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => apiService.deleteApiKey(id),
    onSuccess: () => {
      setApiError(null);
      queryClient.invalidateQueries({ queryKey: ['apiKeys'] });
    },
    onError: (err: any) => {
      setApiError(extractError(err, 'Failed to revoke API key.'));
    },
  });

  const handleCreate = (e: React.FormEvent) => {
    e.preventDefault();
    if (!keyName.trim()) return;
    createMutation.mutate({ name: keyName });
  };

  const handleCopy = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  if (!user) return null;

  return (
    <div className="p-8 space-y-8 max-w-4xl mx-auto">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-extrabold text-slate-100 tracking-tight">System Settings</h1>
        <p className="text-slate-400 text-sm mt-1">Configure workspace preferences, developer API tokens, and user credentials</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        {/* Profile Card */}
        <div className="md:col-span-1 space-y-6">
          <div className="glass rounded-xl p-6 border border-slate-800/50 space-y-5">
            <h3 className="font-bold text-sm text-slate-200 uppercase tracking-wider flex items-center space-x-2">
              <User className="w-5 h-5 text-blue-400" />
              <span>User Profile</span>
            </h3>

            <div className="space-y-4 text-xs">
              <div className="flex items-center space-x-3 bg-slate-900/50 p-3 rounded-lg border border-slate-800/25">
                <Building className="w-5 h-5 text-slate-500" />
                <div>
                  <span className="text-slate-500 block uppercase tracking-wider text-[9px]">Organization</span>
                  <span className="text-slate-300 font-bold">TIDES Ventures Inc.</span>
                </div>
              </div>

              <div>
                <span className="text-slate-500 block uppercase tracking-wider text-[9px] mb-1">Full Name</span>
                <span className="text-slate-200 font-semibold">{user.name}</span>
              </div>

              <div>
                <span className="text-slate-500 block uppercase tracking-wider text-[9px] mb-1">Role Classification</span>
                <span className="text-slate-200 font-semibold">{user.role}</span>
              </div>

              <div>
                <span className="text-slate-500 block uppercase tracking-wider text-[9px] mb-1">Email Account</span>
                <span className="text-slate-200 font-semibold">{user.email}</span>
              </div>
            </div>
          </div>
        </div>

        {/* API Keys Card */}
        <div className="md:col-span-2 space-y-6">
          <div className="glass rounded-xl p-6 border border-slate-800/50 space-y-6">
            <div className="space-y-1">
              <h3 className="font-bold text-sm text-slate-200 uppercase tracking-wider flex items-center space-x-2">
                <Key className="w-5 h-5 text-indigo-400" />
                <span>Developer API Keys</span>
              </h3>
              <p className="text-slate-400 text-xs leading-relaxed">
                Use API tokens to securely query the TIDES Intelligence Engine from external intake webhooks or scripts.
              </p>
            </div>

            {/* Keys Generator Form */}
            <form onSubmit={handleCreate} className="flex gap-3">
              <input
                type="text"
                placeholder="Token label name (e.g. CI script)..."
                value={keyName}
                onChange={(e) => setKeyName(e.target.value)}
                className="flex-1 bg-slate-900 border border-slate-800 rounded-lg px-4 py-2 text-slate-200 text-xs focus:outline-none focus:border-blue-500"
                required
              />
              <button
                type="submit"
                disabled={createMutation.isPending}
                className="bg-blue-600 hover:bg-blue-500 text-white rounded-lg px-4 py-2 font-semibold text-xs transition-colors flex items-center space-x-1.5"
              >
                <Plus className="w-4 h-4" />
                <span>Generate Key</span>
              </button>
            </form>

            {/* Display newly generated key */}
            {newGeneratedKey && (
              <div className="bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs p-4 rounded-lg space-y-2">
                <div className="font-semibold">Token generated successfully:</div>
                <div className="flex items-center justify-between bg-slate-950 p-2 rounded border border-slate-900">
                  <span className="font-mono text-slate-300 break-all select-all">{newGeneratedKey}</span>
                  <button
                    onClick={() => handleCopy(newGeneratedKey, 'new')}
                    className="p-1 hover:bg-slate-800 rounded text-slate-400 hover:text-slate-200 ml-2"
                  >
                    {copiedId === 'new' ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                  </button>
                </div>
                <span className="text-[10px] text-slate-500 block">
                  Copy this token now. For security, it will not be displayed again.
                </span>
              </div>
            )}

            {(apiError || keysIsError) && (
              <div className="bg-red-500/10 border border-red-500/20 text-red-400 text-xs p-3 rounded-lg">
                {apiError || extractError(keysError, 'Unable to load API keys.')}
              </div>
            )}

            {/* Keys List */}
            <div className="divide-y divide-slate-900">
              {keysLoading ? (
                <div className="text-center py-6 text-slate-500 text-xs">Loading API keys...</div>
              ) : keys.length > 0 ? (
                keys.map((key: any) => (
                  <div key={key.id} className="py-4 flex items-center justify-between gap-4 text-xs">
                    <div className="space-y-1">
                      <h4 className="font-semibold text-slate-200">{key.name}</h4>
                      <div className="flex items-center space-x-2 text-slate-500 text-[10px]">
                        <span className="font-mono">{key.key_prefix || key.prefix || 'td_live_***'}</span>
                        <span>•</span>
                        <span>Created {new Date(key.created_at).toLocaleDateString()}</span>
                      </div>
                    </div>

                    <button
                      onClick={() => deleteMutation.mutate(key.id)}
                      className="p-2 hover:bg-red-500/10 text-slate-500 hover:text-red-400 rounded-lg transition-colors"
                      title="Revoke Token"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                ))
              ) : (
                <div className="text-center py-6 text-slate-600 text-xs">
                  No active developer API tokens found.
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
