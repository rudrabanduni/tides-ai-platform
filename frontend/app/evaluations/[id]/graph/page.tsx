'use client';

import React, { useState, useEffect, use } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useRouter } from 'next/navigation';
import { apiService } from '@/services/api';
import { useAuth } from '@/contexts/auth-context';
import { ReactFlow, Background, Controls, MiniMap } from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { 
  ArrowLeft, 
  Workflow, 
  X,
  FileText,
  ShieldCheck,
  AlertTriangle,
  HelpCircle,
  Loader2
} from 'lucide-react';

interface NodeData {
  id: string;
  type: string;
  label: string;
  details: any;
}

export default function GraphPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const { user } = useAuth();
  const router = useRouter();

  const [nodes, setNodes] = useState<any[]>([]);
  const [edges, setEdges] = useState<any[]>([]);
  const [selectedNode, setSelectedNode] = useState<NodeData | null>(null);

  // Redirect if not authenticated
  useEffect(() => {
    if (!user) {
      router.push('/login');
    }
  }, [user, router]);

  const { data: graph, isLoading } = useQuery({
    queryKey: ['evaluationResult', id],
    queryFn: () => apiService.getEvaluationResult(id),
    enabled: !!user && !!id,
  });

  useEffect(() => {
    if (!graph) return;

    const flowNodes: any[] = [];
    const flowEdges: any[] = [];

    // Helper to add nodes with positioning
    let nodeIndex = 0;
    const addNode = (nodeId: string, type: string, label: string, details: any, x: number, y: number) => {
      let colorClass = 'bg-slate-900 border-slate-700 text-slate-100';
      if (type === 'CLAIM') colorClass = 'bg-blue-600/10 border-blue-500/50 text-blue-300';
      if (type === 'OBSERVATION') colorClass = 'bg-emerald-600/10 border-emerald-500/50 text-emerald-300';
      if (type === 'RISK') colorClass = 'bg-red-600/10 border-red-500/50 text-red-300';
      if (type === 'QUESTION') colorClass = 'bg-amber-600/10 border-amber-500/50 text-amber-300';
      if (type === 'CONFLICT') colorClass = 'bg-purple-600/10 border-purple-500/50 text-purple-300';

      flowNodes.push({
        id: nodeId,
        type: 'default',
        position: { x, y },
        data: { 
          label: (
            <div className="flex flex-col items-start p-1 text-left text-xs max-w-[150px]">
              <span className="font-bold text-[9px] uppercase tracking-wider opacity-60">{type}</span>
              <span className="truncate w-full mt-0.5">{label}</span>
            </div>
          ),
          details,
          nodeType: type
        },
        style: {
          background: 'rgba(15, 23, 42, 0.9)',
          color: '#f8fafc',
          border: '1px solid rgba(255, 255, 255, 0.08)',
          borderRadius: '8px',
          boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)',
        }
      });
      nodeIndex++;
    };

    // 1. Documents Level (Top)
    const docId = 'doc-1';
    addNode(docId, 'DOCUMENT', 'Startup Pitch Deck', {}, 250, 50);

    // 2. Claims Level (Middle-Top)
    const claims = Object.values(graph.claims || {});
    claims.forEach((claim: any, idx) => {
      const xPos = 50 + idx * 250;
      addNode(claim.claim_id, 'CLAIM', claim.statement || claim.content, claim, xPos, 180);
      flowEdges.push({
        id: `e-doc-${claim.claim_id}`,
        source: docId,
        target: claim.claim_id,
        animated: true,
        style: { stroke: '#475569' }
      });
    });

    // 3. Observations Level (Middle)
    const observations = Object.values(graph.observations || {});
    observations.forEach((obs: any, idx) => {
      const xPos = 100 + idx * 220;
      addNode(obs.node_id || obs.observation_id, 'OBSERVATION', obs.content || obs.summary, obs, xPos, 320);
      
      // Link observation to corresponding claim
      if (obs.claim_id) {
        flowEdges.push({
          id: `e-claim-${obs.node_id}`,
          source: obs.claim_id,
          target: obs.node_id || obs.observation_id,
          label: 'SUPPORTED_BY',
          style: { stroke: '#10b981' }
        });
      }
    });

    // 4. Risks & Questions (Bottom)
    const risks = Object.values(graph.risks || {});
    risks.forEach((risk: any, idx) => {
      const xPos = 50 + idx * 200;
      addNode(risk.node_id || risk.risk_id, 'RISK', risk.content || risk.description, risk, xPos, 480);
      
      // Link to source observation
      if (risk.observation_id) {
        flowEdges.push({
          id: `e-risk-${risk.node_id}`,
          source: risk.observation_id,
          target: risk.node_id || risk.risk_id,
          label: 'EXPOSES',
          style: { stroke: '#ef4444' }
        });
      }
    });

    const questions = Object.values(graph.questions || {});
    questions.forEach((q: any, idx) => {
      const xPos = 400 + idx * 200;
      addNode(q.node_id || q.question_id, 'QUESTION', q.content || q.question_text, q, xPos, 480);
      
      // Link to source observation
      if (q.observation_id) {
        flowEdges.push({
          id: `e-q-${q.node_id}`,
          source: q.observation_id,
          target: q.node_id || q.question_id,
          label: 'QUESTIONS',
          style: { stroke: '#f59e0b' }
        });
      }
    });

    setNodes(flowNodes);
    setEdges(flowEdges);
  }, [graph]);

  if (!user) {
    return (
      <div className="flex h-screen items-center justify-center bg-slate-950 text-slate-100">
        <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
      </div>
    );
  }

  const onNodeClick = (event: any, node: any) => {
    setSelectedNode({
      id: node.id,
      type: node.data.nodeType,
      label: node.data.label.props.children[1].props.children,
      details: node.data.details
    });
  };

  return (
    <div className="flex h-screen bg-slate-950 text-slate-100 overflow-hidden relative">
      {/* Header overlay */}
      <div className="absolute top-4 left-4 z-10 flex items-center space-x-4 bg-slate-950/80 backdrop-blur border border-slate-800 p-3 rounded-xl">
        <button
          onClick={() => router.push(`/evaluations/${id}`)}
          className="p-1.5 hover:bg-slate-800 rounded-lg text-slate-400 hover:text-slate-200 transition-colors"
        >
          <ArrowLeft className="w-5 h-5" />
        </button>
        <div>
          <h2 className="text-sm font-bold text-slate-200 flex items-center space-x-2">
            <Workflow className="w-4 h-4 text-blue-400" />
            <span>Interactive Observation Graph</span>
          </h2>
          <p className="text-[10px] text-slate-500 mt-0.5">Click nodes to inspect claims, conflicts, and evidence lineage</p>
        </div>
      </div>

      {/* Main Flow Canvas */}
      <div className="flex-1 h-full">
        {isLoading ? (
          <div className="flex h-full w-full items-center justify-center">
            <div className="flex flex-col items-center space-y-3">
              <span className="h-8 w-8 animate-spin rounded-full border-4 border-blue-500 border-t-transparent"></span>
              <span className="text-xs text-slate-400">Rendering node linkages...</span>
            </div>
          </div>
        ) : (
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodeClick={onNodeClick}
            fitView
            className="bg-slate-950"
          >
            <Background color="#1e293b" gap={16} />
            <Controls className="bg-slate-900 border border-slate-800 text-slate-200" />
            <MiniMap 
              nodeColor={() => '#1e293b'} 
              maskColor="rgba(15, 23, 42, 0.6)"
              className="bg-slate-900 border border-slate-800"
            />
          </ReactFlow>
        )}
      </div>

      {/* Details Side Panel */}
      {selectedNode && (
        <div className="w-96 border-l border-slate-800 bg-slate-950 h-full flex flex-col justify-between shadow-2xl relative z-20">
          <div>
            <div className="p-6 border-b border-slate-900 flex items-center justify-between">
              <div>
                <span className="text-[10px] font-bold text-blue-400 bg-blue-500/10 px-2 py-0.5 rounded border border-blue-500/20 uppercase tracking-wider">
                  {selectedNode.type}
                </span>
                <h3 className="font-bold text-sm text-slate-200 mt-2 truncate w-72">Node Inspector</h3>
              </div>
              <button 
                onClick={() => setSelectedNode(null)}
                className="p-1 text-slate-500 hover:text-slate-200 rounded-lg hover:bg-slate-900"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="p-6 space-y-6 overflow-y-auto max-h-[calc(100vh-150px)]">
              {/* Content Summary */}
              <div className="space-y-2">
                <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Summary</span>
                <p className="text-slate-300 text-xs leading-relaxed bg-slate-900/50 border border-slate-800/30 p-3 rounded-lg">
                  {selectedNode.label || 'No description provided.'}
                </p>
              </div>

              {/* Node Metadata Details */}
              <div className="space-y-3">
                <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Lineage & Metrics</span>
                <div className="divide-y divide-slate-900 text-xs">
                  {selectedNode.type === 'CLAIM' && (
                    <>
                      <div className="py-2.5 flex justify-between">
                        <span className="text-slate-500">Knowledge Key:</span>
                        <span className="text-slate-300 font-mono">{selectedNode.details.knowledge_key || 'N/A'}</span>
                      </div>
                      <div className="py-2.5 flex justify-between">
                        <span className="text-slate-500">Field Type:</span>
                        <span className="text-slate-300">{selectedNode.details.field_type || 'String'}</span>
                      </div>
                    </>
                  )}

                  {selectedNode.type === 'OBSERVATION' && (
                    <>
                      <div className="py-2.5 flex justify-between">
                        <span className="text-slate-500">Confidence:</span>
                        <span className="text-emerald-400 font-semibold">{selectedNode.details.confidence || '0.90'}</span>
                      </div>
                      <div className="py-2.5 flex justify-between">
                        <span className="text-slate-500">Status:</span>
                        <span className="text-slate-300 font-medium">{selectedNode.details.status || 'VERIFIED'}</span>
                      </div>
                    </>
                  )}

                  {selectedNode.type === 'RISK' && (
                    <>
                      <div className="py-2.5 flex justify-between">
                        <span className="text-slate-500">Risk Severity:</span>
                        <span className="text-red-400 font-semibold">{selectedNode.details.severity || 'HIGH'}</span>
                      </div>
                      <div className="py-2.5 flex justify-between">
                        <span className="text-slate-500">Mitigation Status:</span>
                        <span className="text-slate-300">{selectedNode.details.mitigation || 'Unresolved'}</span>
                      </div>
                    </>
                  )}

                  {selectedNode.type === 'QUESTION' && (
                    <>
                      <div className="py-2.5 flex justify-between">
                        <span className="text-slate-500">Priority:</span>
                        <span className="text-amber-500 font-semibold">{selectedNode.details.priority || 'MEDIUM'}</span>
                      </div>
                      <div className="py-2.5 flex justify-between">
                        <span className="text-slate-500">Incubator Action:</span>
                        <span className="text-slate-300">Awaiting founder validation</span>
                      </div>
                    </>
                  )}
                </div>
              </div>
            </div>
          </div>

          <div className="p-4 border-t border-slate-900 bg-slate-950/50 text-[10px] text-center text-slate-500">
            Node ID: {selectedNode.id}
          </div>
        </div>
      )}
    </div>
  );
}
