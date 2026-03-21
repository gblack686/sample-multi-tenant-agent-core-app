'use client';

import { useState, useEffect, useCallback } from 'react';
import { Bot, Loader2, AlertCircle, RefreshCw, CheckCircle, XCircle, Code, ChevronDown, ChevronUp } from 'lucide-react';
import AuthGuard from '@/components/auth/auth-guard';
import TopNav from '@/components/layout/top-nav';
import PageHeader from '@/components/layout/page-header';
import { useAuth } from '@/contexts/auth-context';
import { pluginApi } from '@/lib/admin-api';
import type { PluginEntity } from '@/types/admin';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function formatDate(d: string): string {
  return new Date(d).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}

function AgentCard({ agent }: { agent: PluginEntity }) {
  const [expanded, setExpanded] = useState(false);
  const meta = agent.metadata as Record<string, unknown>;
  const description = (meta?.description as string) || '';
  const model = (meta?.model as string) || '';
  const tools = (meta?.tools as string[]) || [];

  return (
    <div className="bg-white rounded-2xl border border-gray-200 p-5 hover:border-gray-300 transition-colors">
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-[#003149]/10">
            <Bot className="w-5 h-5 text-[#003149]" />
          </div>
          <div>
            <h3 className="font-semibold text-gray-900">{agent.name}</h3>
            {model && (
              <span className="text-xs bg-blue-50 text-blue-700 px-2 py-0.5 rounded-full font-medium">{model}</span>
            )}
          </div>
        </div>
        <div className="flex items-center gap-2">
          {agent.is_active ? (
            <span className="flex items-center gap-1 text-xs bg-green-50 text-green-700 px-2 py-1 rounded-full font-medium">
              <CheckCircle className="w-3 h-3" /> Active
            </span>
          ) : (
            <span className="flex items-center gap-1 text-xs bg-gray-100 text-gray-500 px-2 py-1 rounded-full font-medium">
              <XCircle className="w-3 h-3" /> Inactive
            </span>
          )}
        </div>
      </div>

      {description && (
        <p className="text-sm text-gray-600 mb-3">{description}</p>
      )}

      {tools.length > 0 && (
        <div className="flex flex-wrap gap-1 mb-3">
          {tools.map((t: string) => (
            <span key={t} className="text-[10px] bg-purple-50 text-purple-700 px-2 py-0.5 rounded-full font-medium">{t}</span>
          ))}
        </div>
      )}

      <div className="flex items-center justify-between pt-3 border-t border-gray-50">
        <span className="text-xs text-gray-400">v{agent.version} · Updated {formatDate(agent.updated_at)}</span>
        <button
          onClick={() => setExpanded(!expanded)}
          className="flex items-center gap-1 text-xs text-gray-500 hover:text-gray-700 transition-colors"
        >
          <Code className="w-3 h-3" />
          {expanded ? 'Hide' : 'View'} prompt
          {expanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
        </button>
      </div>

      {expanded && (
        <pre className="mt-3 p-3 bg-gray-900 text-green-400 text-xs rounded-xl overflow-x-auto whitespace-pre-wrap font-mono max-h-64 overflow-y-auto">
          {agent.content || '(no content)'}
        </pre>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export default function AgentsPage() {
  const { getToken } = useAuth();
  const [agents, setAgents] = useState<PluginEntity[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAgents = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await pluginApi.list(getToken, 'agents');
      setAgents(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load agents');
      setAgents([]);
    } finally {
      setIsLoading(false);
    }
  }, [getToken]);

  useEffect(() => {
    fetchAgents();
  }, [fetchAgents]);

  const activeCount = agents.filter(a => a.is_active).length;

  return (
    <AuthGuard>
    <div className="flex flex-col h-screen bg-gray-50">
      <TopNav />
      <main className="flex-1 overflow-y-auto">
        <div className="p-8">
          <PageHeader
            title="Agents"
            description="EAGLE plugin agents and their configurations"
            breadcrumbs={[
              { label: 'Admin', href: '/admin' },
              { label: 'Agents' },
            ]}
            actions={
              <button
                onClick={fetchAgents}
                disabled={isLoading}
                className="flex items-center gap-2 px-4 py-2.5 bg-white border border-gray-200 text-gray-700 rounded-xl font-medium hover:bg-gray-50 transition-colors disabled:opacity-50"
              >
                <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
                Refresh
              </button>
            }
          />

          {/* Stats */}
          {!isLoading && agents.length > 0 && (
            <div className="flex items-center gap-4 mb-6">
              <div className="bg-white rounded-xl border border-gray-200 px-4 py-2.5 flex items-center gap-2">
                <Bot className="w-4 h-4 text-[#003149]" />
                <span className="text-sm font-medium text-gray-700">{agents.length} total agents</span>
              </div>
              <div className="bg-white rounded-xl border border-gray-200 px-4 py-2.5 flex items-center gap-2">
                <CheckCircle className="w-4 h-4 text-green-500" />
                <span className="text-sm font-medium text-gray-700">{activeCount} active</span>
              </div>
            </div>
          )}

          {/* Error */}
          {error && (
            <div className="mb-6 flex items-center gap-3 p-4 bg-red-50 border border-red-200 rounded-xl text-red-700">
              <AlertCircle className="w-5 h-5 flex-shrink-0" />
              <p className="flex-1">{error}</p>
              <button onClick={fetchAgents} className="px-3 py-1.5 bg-red-100 text-red-700 rounded-lg text-sm font-medium hover:bg-red-200 transition-colors">Retry</button>
            </div>
          )}

          {/* Loading */}
          {isLoading ? (
            <div className="flex flex-col items-center justify-center py-20">
              <Loader2 className="w-8 h-8 text-[#003149] animate-spin mb-4" />
              <p className="text-gray-500 text-sm">Loading agents...</p>
            </div>
          ) : agents.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
              {agents.map((agent) => (
                <AgentCard key={agent.name} agent={agent} />
              ))}
            </div>
          ) : !error ? (
            <div className="flex flex-col items-center justify-center py-20">
              <Bot className="w-10 h-10 text-gray-300 mb-3" />
              <p className="text-sm font-medium text-gray-500">No agents found</p>
              <p className="text-xs text-gray-400 mt-1">Plugin agents will appear here once seeded</p>
            </div>
          ) : null}
        </div>
      </main>
    </div>
    </AuthGuard>
  );
}
