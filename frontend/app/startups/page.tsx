'use client';

import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useRouter } from 'next/navigation';
import { apiService } from '@/services/api';
import { useAuth } from '@/contexts/auth-context';
import { 
  Plus, 
  Search, 
  Trash2, 
  Edit3, 
  Play, 
  FileText,
  X,
  SlidersHorizontal,
  ChevronLeft,
  ChevronRight
} from 'lucide-react';
import { Startup } from '@/types';

export default function StartupsPage() {
  const { user } = useAuth();
  const router = useRouter();
  const queryClient = useQueryClient();

  // Dialog State
  const [isAddOpen, setIsAddOpen] = useState(false);
  const [isEditOpen, setIsEditOpen] = useState(false);
  const [isDeleteOpen, setIsDeleteOpen] = useState(false);
  
  const [selectedStartup, setSelectedStartup] = useState<Startup | null>(null);

  // Form Field State
  const [formName, setFormName] = useState('');
  const [formSector, setFormSector] = useState('SaaS');
  const [formStage, setFormStage] = useState('Pre-Seed');
  const [formProblem, setFormProblem] = useState('');
  const [formSolution, setFormSolution] = useState('');

  // Search & Filter State
  const [search, setSearch] = useState('');
  const [stageFilter, setStageFilter] = useState('');
  const [sortField, setSortField] = useState('startup_name');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc');
  
  // Pagination
  const [page, setPage] = useState(1);
  const itemsPerPage = 8;

  // React Query Fetch List
  const { data: startups = [], isLoading } = useQuery({
    queryKey: ['startups'],
    queryFn: () => apiService.getStartups(),
    enabled: !!user,
  });

  // Mutations
  const createMutation = useMutation({
    mutationFn: (payload: Partial<Startup>) => apiService.createStartup(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['startups'] });
      setIsAddOpen(false);
      resetForm();
    }
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: Partial<Startup> }) => 
      apiService.updateStartup(id, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['startups'] });
      setIsEditOpen(false);
      resetForm();
    }
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => apiService.deleteStartup(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['startups'] });
      setIsDeleteOpen(false);
      setSelectedStartup(null);
    }
  });

  const resetForm = () => {
    setFormName('');
    setFormSector('SaaS');
    setFormStage('Pre-Seed');
    setFormProblem('');
    setFormSolution('');
    setSelectedStartup(null);
  };

  const handleOpenAdd = () => {
    resetForm();
    setIsAddOpen(true);
  };

  const handleOpenEdit = (startup: Startup) => {
    setSelectedStartup(startup);
    setFormName(startup.startup_name);
    setFormSector(startup.sector || 'SaaS');
    setFormStage(startup.stage || 'Pre-Seed');
    setFormProblem(startup.problem_statement || '');
    setFormSolution(startup.solution_summary || '');
    setIsEditOpen(true);
  };

  const handleOpenDelete = (startup: Startup) => {
    setSelectedStartup(startup);
    setIsDeleteOpen(true);
  };

  const handleAddSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    createMutation.mutate({
      startup_name: formName,
      sector: formSector,
      stage: formStage,
      problem_statement: formProblem,
      solution_summary: formSolution
    });
  };

  const handleEditSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (selectedStartup) {
      updateMutation.mutate({
        id: selectedStartup.id,
        payload: {
          startup_name: formName,
          sector: formSector,
          stage: formStage,
          problem_statement: formProblem,
          solution_summary: formSolution
        }
      });
    }
  };

  const handleDeleteConfirm = () => {
    if (selectedStartup) {
      deleteMutation.mutate(selectedStartup.id);
    }
  };

  if (!user) return null;

  // Search and Filter Logic
  const filtered = startups.filter((s) => {
    const matchesSearch = 
      s.startup_name.toLowerCase().includes(search.toLowerCase()) ||
      s.sector.toLowerCase().includes(search.toLowerCase());
    const matchesStage = stageFilter ? s.stage === stageFilter : true;
    return matchesSearch && matchesStage;
  });

  // Sort Logic
  const sorted = [...filtered].sort((a, b) => {
    const valA = (a[sortField as keyof Startup] || '').toString().toLowerCase();
    const valB = (b[sortField as keyof Startup] || '').toString().toLowerCase();
    
    if (valA < valB) return sortOrder === 'asc' ? -1 : 1;
    if (valA > valB) return sortOrder === 'asc' ? 1 : -1;
    return 0;
  });

  // Pagination Logic
  const totalPages = Math.ceil(sorted.length / itemsPerPage);
  const paginated = sorted.slice((page - 1) * itemsPerPage, page * itemsPerPage);

  const toggleSort = (field: string) => {
    if (sortField === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortOrder('asc');
    }
  };

  return (
    <div className="p-8 space-y-8 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-extrabold text-slate-100 tracking-tight">Startup Repository</h1>
          <p className="text-slate-400 text-sm mt-1">Manage and evaluate incubation applicant companies</p>
        </div>
        <button
          onClick={handleOpenAdd}
          className="bg-blue-600 hover:bg-blue-500 text-white rounded-lg px-4 py-2.5 font-semibold text-sm transition-all duration-150 flex items-center justify-center space-x-2 shadow-lg shadow-blue-500/10"
        >
          <Plus className="w-4 h-4" />
          <span>Add Startup</span>
        </button>
      </div>

      {/* Filters Hub */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 items-center">
        {/* Search */}
        <div className="md:col-span-2 relative">
          <Search className="w-4 h-4 text-slate-500 absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search startups by name or industry..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full bg-slate-900 border border-slate-800 rounded-lg pl-10 pr-4 py-2.5 text-slate-200 placeholder-slate-500 focus:outline-none focus:border-blue-500 text-sm"
          />
        </div>

        {/* Stage Filter */}
        <div className="relative">
          <select
            value={stageFilter ?? ""}
            onChange={(e) => setStageFilter(e.target.value)}
            className="w-full bg-slate-900 border border-slate-800 rounded-lg px-4 py-2.5 text-slate-200 focus:outline-none focus:border-blue-500 text-sm appearance-none cursor-pointer"
          >
            <option value="">All Stages</option>
            <option value="Pre-Seed">Pre-Seed</option>
            <option value="Seed">Seed</option>
            <option value="Series A">Series A</option>
          </select>
        </div>

        {/* Info label */}
        <div className="text-right text-xs text-slate-500">
          Showing {filtered.length} of {startups.length} startups
        </div>
      </div>

      {/* Table grid */}
      <div className="glass rounded-xl border border-slate-800/50 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-slate-800 text-xs font-semibold text-slate-400 uppercase tracking-wider bg-slate-950/50">
                <th className="py-4 px-6 cursor-pointer" onClick={() => toggleSort('startup_name')}>
                  Startup Name {sortField === 'startup_name' && (sortOrder === 'asc' ? '▲' : '▼')}
                </th>
                <th className="py-4 px-6 cursor-pointer" onClick={() => toggleSort('sector')}>
                  Sector {sortField === 'sector' && (sortOrder === 'asc' ? '▲' : '▼')}
                </th>
                <th className="py-4 px-6 cursor-pointer" onClick={() => toggleSort('stage')}>
                  Stage {sortField === 'stage' && (sortOrder === 'asc' ? '▲' : '▼')}
                </th>
                <th className="py-4 px-6">Status</th>
                <th className="py-4 px-6 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-900 text-sm text-slate-300">
              {isLoading ? (
                <tr>
                  <td colSpan={5} className="py-12 text-center text-slate-500">
                    <span className="h-6 w-6 animate-spin rounded-full border-2 border-slate-500 border-t-transparent inline-block"></span>
                  </td>
                </tr>
              ) : paginated.length > 0 ? (
                paginated.map((startup) => (
                  <tr key={startup.id} className="hover:bg-slate-900/10 transition-colors">
                    <td className="py-4 px-6 font-semibold text-slate-100">{startup.startup_name}</td>
                    <td className="py-4 px-6">{startup.sector}</td>
                    <td className="py-4 px-6">
                      <span className="px-2.5 py-0.5 rounded-full text-xs font-medium bg-slate-800 border border-slate-700 text-slate-300">
                        {startup.stage}
                      </span>
                    </td>
                    <td className="py-4 px-6">
                      <span className={`px-2.5 py-0.5 rounded-full text-xs font-medium ${
                        startup.status === 'APPROVED' 
                          ? 'bg-emerald-500/10 text-emerald-400' 
                          : 'bg-amber-500/10 text-amber-400'
                      }`}>
                        {startup.status || 'INGESTED'}
                      </span>
                    </td>
                    <td className="py-4 px-6 text-right space-x-2">
                      <button
                        onClick={() => router.push(`/evaluations/${startup.id}`)}
                        className="p-2 hover:bg-blue-600/10 text-slate-400 hover:text-blue-400 rounded-lg transition-all"
                        title="Run Evaluation / View Graph"
                      >
                        <Play className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => handleOpenEdit(startup)}
                        className="p-2 hover:bg-slate-800 text-slate-400 hover:text-slate-200 rounded-lg transition-all"
                        title="Edit Details"
                      >
                        <Edit3 className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => handleOpenDelete(startup)}
                        className="p-2 hover:bg-red-500/10 text-slate-400 hover:text-red-400 rounded-lg transition-all"
                        title="Delete Record"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={5} className="py-12 text-center text-slate-500">
                    No startups match the search criteria.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination footer */}
        {totalPages > 1 && (
          <div className="p-4 border-t border-slate-800 bg-slate-950/30 flex items-center justify-between">
            <span className="text-xs text-slate-500">Page {page} of {totalPages}</span>
            <div className="flex space-x-2">
              <button
                onClick={() => setPage(page - 1)}
                disabled={page === 1}
                className="p-1.5 bg-slate-900 border border-slate-800 rounded-lg text-slate-400 hover:text-slate-200 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              <button
                onClick={() => setPage(page + 1)}
                disabled={page === totalPages}
                className="p-1.5 bg-slate-900 border border-slate-800 rounded-lg text-slate-400 hover:text-slate-200 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Add Startup Modal */}
      {isAddOpen && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="w-full max-w-lg glass rounded-xl overflow-hidden border border-slate-800/80">
            <div className="p-6 border-b border-slate-800 flex items-center justify-between">
              <h3 className="font-bold text-lg text-slate-100">Add Applicant Startup</h3>
              <button onClick={() => setIsAddOpen(false)} className="p-1 text-slate-400 hover:text-slate-200">
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleAddSubmit} className="p-6 space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Startup Name</label>
                <input
                  type="text"
                  required
                  value={formName}
                  onChange={(e) => setFormName(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-800 rounded-lg px-4 py-2.5 text-slate-200 text-sm focus:outline-none focus:border-blue-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Sector</label>
                  <select
                    value={formSector ?? ""}
                    onChange={(e) => setFormSector(e.target.value)}
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
                    value={formStage ?? ""}
                    onChange={(e) => setFormStage(e.target.value)}
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

              <div>
                <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Problem Statement</label>
                <textarea
                  value={formProblem}
                  onChange={(e) => setFormProblem(e.target.value)}
                  rows={2}
                  className="w-full bg-slate-900 border border-slate-800 rounded-lg px-4 py-2.5 text-slate-200 text-sm focus:outline-none focus:border-blue-500 resize-none"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Solution Summary</label>
                <textarea
                  value={formSolution}
                  onChange={(e) => setFormSolution(e.target.value)}
                  rows={2}
                  className="w-full bg-slate-900 border border-slate-800 rounded-lg px-4 py-2.5 text-slate-200 text-sm focus:outline-none focus:border-blue-500 resize-none"
                />
              </div>

              <div className="flex justify-end space-x-3 pt-4 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setIsAddOpen(false)}
                  className="px-4 py-2 border border-slate-800 text-slate-400 hover:text-slate-200 rounded-lg text-sm"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={createMutation.isPending}
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-sm font-semibold transition-colors"
                >
                  {createMutation.isPending ? 'Adding...' : 'Add Startup'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Edit Startup Modal */}
      {isEditOpen && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="w-full max-w-lg glass rounded-xl overflow-hidden border border-slate-800/80">
            <div className="p-6 border-b border-slate-800 flex items-center justify-between">
              <h3 className="font-bold text-lg text-slate-100">Edit Startup Details</h3>
              <button onClick={() => setIsEditOpen(false)} className="p-1 text-slate-400 hover:text-slate-200">
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleEditSubmit} className="p-6 space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Startup Name</label>
                <input
                  type="text"
                  required
                  value={formName}
                  onChange={(e) => setFormName(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-800 rounded-lg px-4 py-2.5 text-slate-200 text-sm focus:outline-none focus:border-blue-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Sector</label>
                  <select
                    value={formSector ?? ""}
                    onChange={(e) => setFormSector(e.target.value)}
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
                    value={formStage ?? ""}
                    onChange={(e) => setFormStage(e.target.value)}
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

              <div>
                <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Problem Statement</label>
                <textarea
                  value={formProblem}
                  onChange={(e) => setFormProblem(e.target.value)}
                  rows={2}
                  className="w-full bg-slate-900 border border-slate-800 rounded-lg px-4 py-2.5 text-slate-200 text-sm focus:outline-none focus:border-blue-500 resize-none"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Solution Summary</label>
                <textarea
                  value={formSolution}
                  onChange={(e) => setFormSolution(e.target.value)}
                  rows={2}
                  className="w-full bg-slate-900 border border-slate-800 rounded-lg px-4 py-2.5 text-slate-200 text-sm focus:outline-none focus:border-blue-500 resize-none"
                />
              </div>

              <div className="flex justify-end space-x-3 pt-4 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setIsEditOpen(false)}
                  className="px-4 py-2 border border-slate-800 text-slate-400 hover:text-slate-200 rounded-lg text-sm"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={updateMutation.isPending}
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-sm font-semibold transition-colors"
                >
                  {updateMutation.isPending ? 'Saving...' : 'Save Changes'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {isDeleteOpen && selectedStartup && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="w-full max-w-md glass rounded-xl overflow-hidden border border-slate-800/80 p-6 space-y-6">
            <div>
              <h3 className="font-bold text-lg text-slate-100">Delete Startup</h3>
              <p className="text-slate-400 text-sm mt-2">
                Are you sure you want to delete <span className="font-semibold text-slate-200">{selectedStartup.startup_name}</span>? This action is permanent and will delete all associated evaluations, claims, and graphs.
              </p>
            </div>

            <div className="flex justify-end space-x-3">
              <button
                type="button"
                onClick={() => setIsDeleteOpen(false)}
                className="px-4 py-2 border border-slate-800 text-slate-400 hover:text-slate-200 rounded-lg text-sm"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleDeleteConfirm}
                disabled={deleteMutation.isPending}
                className="px-4 py-2 bg-red-600 hover:bg-red-500 text-white rounded-lg text-sm font-semibold transition-colors"
              >
                {deleteMutation.isPending ? 'Deleting...' : 'Confirm Delete'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
