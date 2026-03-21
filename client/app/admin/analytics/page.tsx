'use client';

import { useState, useEffect, useCallback } from 'react';
import { BarChart3, TrendingUp, Users, Zap, DollarSign, Loader2, AlertCircle, RefreshCw, Wrench } from 'lucide-react';
import AuthGuard from '@/components/auth/auth-guard';
import TopNav from '@/components/layout/top-nav';
import PageHeader from '@/components/layout/page-header';
import { useAuth } from '@/contexts/auth-context';

// ---------------------------------------------------------------------------
// Types (matching /api/admin/dashboard and /api/admin/tools responses)
// ---------------------------------------------------------------------------

interface DashboardSummary {
  total_input_tokens: number;
  total_output_tokens: number;
  total_tokens: number;
  total_cost_usd: number;
  total_requests: number;
  active_sessions: number;
  avg_tokens_per_request: number;
  avg_cost_per_request: number;
}

interface DailyDataPoint {
  date: string;
  input_tokens: number;
  output_tokens: number;
  cost: number;
  requests: number;
}

interface DashboardResponse {
  tenant_id: string;
  period_days: number;
  summary: DashboardSummary;
  daily: DailyDataPoint[];
  generated_at: string;
}

interface ToolEntry {
  name: string;
  count: number;
}

interface ToolsResponse {
  tenant_id: string;
  period_days: number;
  tools: ToolEntry[];
  total_tool_calls: number;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const DATE_RANGES = [
  { label: '7d', days: 7 },
  { label: '30d', days: 30 },
  { label: '90d', days: 90 },
] as const;

function formatCurrency(value: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 4,
  }).format(value);
}

function formatNumber(value: number): string {
  return new Intl.NumberFormat('en-US').format(value);
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export default function AnalyticsPage() {
  const { getToken } = useAuth();
  const [selectedDays, setSelectedDays] = useState<number>(30);
  const [dashboard, setDashboard] = useState<DashboardResponse | null>(null);
  const [tools, setTools] = useState<ToolsResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async (days: number) => {
    setIsLoading(true);
    setError(null);
    try {
      const token = await getToken();
      const headers = { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' };
      const [dashRes, toolsRes] = await Promise.all([
        fetch(`/api/admin/dashboard?days=${days}`, { headers }),
        fetch(`/api/admin/tools?days=${days}`, { headers }),
      ]);
      if (!dashRes.ok) throw new Error(`Dashboard fetch failed (${dashRes.status})`);
      const dashData: DashboardResponse = await dashRes.json();
      setDashboard(dashData);
      if (toolsRes.ok) {
        const toolsData: ToolsResponse = await toolsRes.json();
        setTools(toolsData);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An unexpected error occurred');
      setDashboard(null);
    } finally {
      setIsLoading(false);
    }
  }, [getToken]);

  useEffect(() => {
    fetchData(selectedDays);
  }, [selectedDays, fetchData]);

  const summary = dashboard?.summary;
  const daily = dashboard?.daily || [];
  const maxRequests = Math.max(...daily.map(d => d.requests), 1);

  return (
    <AuthGuard>
    <div className="flex flex-col h-screen bg-gray-50">
      <TopNav />
      <main className="flex-1 overflow-y-auto">
        <div className="p-8">
          <PageHeader
            title="Analytics"
            description="API usage, costs, and tool activity"
            breadcrumbs={[
              { label: 'Admin', href: '/admin' },
              { label: 'Analytics' },
            ]}
            actions={
              <button
                onClick={() => fetchData(selectedDays)}
                disabled={isLoading}
                className="flex items-center gap-2 px-4 py-2.5 bg-white border border-gray-200 text-gray-700 rounded-xl font-medium hover:bg-gray-50 transition-colors disabled:opacity-50"
              >
                <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
                Refresh
              </button>
            }
          />

          {/* Date Range Selector */}
          <div className="mb-6">
            <div className="inline-flex items-center bg-white border border-gray-200 rounded-xl p-1">
              {DATE_RANGES.map((range) => (
                <button
                  key={range.days}
                  onClick={() => setSelectedDays(range.days)}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                    selectedDays === range.days
                      ? 'bg-[#003149] text-white shadow-md'
                      : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
                  }`}
                >
                  {range.label}
                </button>
              ))}
            </div>
          </div>

          {/* Error */}
          {error && (
            <div className="mb-6 flex items-center gap-3 p-4 bg-red-50 border border-red-200 rounded-xl text-red-700">
              <AlertCircle className="w-5 h-5 flex-shrink-0" />
              <p className="flex-1">{error}</p>
              <button onClick={() => fetchData(selectedDays)} className="px-3 py-1.5 bg-red-100 text-red-700 rounded-lg text-sm font-medium hover:bg-red-200 transition-colors">Retry</button>
            </div>
          )}

          {/* Loading */}
          {isLoading && !dashboard ? (
            <div className="flex flex-col items-center justify-center py-20">
              <Loader2 className="w-8 h-8 text-[#003149] animate-spin mb-4" />
              <p className="text-gray-500 text-sm">Loading analytics...</p>
            </div>
          ) : (
            <>
              {/* Summary Cards */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
                {[
                  { label: 'Total Requests', value: summary ? formatNumber(summary.total_requests) : '--', icon: <TrendingUp className="w-5 h-5" />, color: 'bg-blue-500', desc: `Last ${selectedDays} days` },
                  { label: 'Total Tokens', value: summary ? formatNumber(summary.total_tokens) : '--', icon: <Zap className="w-5 h-5" />, color: 'bg-purple-500', desc: 'Input + Output' },
                  { label: 'Total Cost', value: summary ? formatCurrency(summary.total_cost_usd) : '--', icon: <DollarSign className="w-5 h-5" />, color: 'bg-green-500', desc: 'USD' },
                  { label: 'Active Sessions', value: summary ? String(summary.active_sessions) : '--', icon: <Users className="w-5 h-5" />, color: 'bg-amber-500', desc: 'Open sessions' },
                ].map((card, i) => (
                  <div key={i} className="bg-white rounded-2xl border border-gray-200 p-5">
                    <div className="flex items-start justify-between mb-4">
                      <div className={`p-3 rounded-xl ${card.color} text-white`}>{card.icon}</div>
                      <span className="text-xs text-gray-400 font-medium">{card.desc}</span>
                    </div>
                    <p className="text-2xl font-bold text-gray-900">
                      {isLoading ? <span className="inline-block w-24 h-7 bg-gray-100 rounded animate-pulse" /> : card.value}
                    </p>
                    <p className="text-sm text-gray-500">{card.label}</p>
                  </div>
                ))}
              </div>

              {/* Daily Activity Chart */}
              {daily.length > 0 && (
                <div className="bg-white rounded-2xl border border-gray-200 p-6 mb-6">
                  <div className="flex items-center gap-2 mb-6">
                    <BarChart3 className="w-5 h-5 text-gray-600" />
                    <h3 className="font-bold text-gray-900">Daily Requests</h3>
                  </div>
                  <div className="flex items-end gap-1 h-32">
                    {daily.map((d, i) => (
                      <div key={i} className="flex-1 flex flex-col items-center gap-1 group">
                        <div
                          className="w-full bg-[#003149]/20 hover:bg-[#003149]/40 rounded-t transition-colors cursor-default"
                          style={{ height: `${Math.max((d.requests / maxRequests) * 100, 4)}%` }}
                          title={`${d.date}: ${d.requests} requests`}
                        />
                        {i % Math.ceil(daily.length / 6) === 0 && (
                          <span className="text-[9px] text-gray-400 rotate-[-45deg] origin-top-left ml-1">
                            {d.date.slice(5)}
                          </span>
                        )}
                      </div>
                    ))}
                  </div>
                  <div className="mt-6 flex items-center gap-6 text-sm text-gray-600 border-t border-gray-50 pt-4">
                    <span>Avg {summary ? formatNumber(summary.avg_tokens_per_request) : '--'} tokens/req</span>
                    <span>Avg {summary ? formatCurrency(summary.avg_cost_per_request) : '--'}/req</span>
                  </div>
                </div>
              )}

              {/* Tool Usage */}
              {tools && tools.tools.length > 0 && (
                <div className="bg-white rounded-2xl border border-gray-200 p-6">
                  <div className="flex items-center gap-2 mb-6">
                    <Wrench className="w-5 h-5 text-gray-600" />
                    <h3 className="font-bold text-gray-900">Tool Usage</h3>
                    <span className="text-xs text-gray-400 ml-auto">{formatNumber(tools.total_tool_calls)} total calls</span>
                  </div>
                  <div className="space-y-3">
                    {tools.tools.slice(0, 10).map((t) => (
                      <div key={t.name} className="flex items-center gap-3">
                        <span className="text-sm text-gray-600 w-40 truncate font-mono">{t.name}</span>
                        <div className="flex-1 h-5 bg-gray-100 rounded-full overflow-hidden">
                          <div
                            className="h-full bg-gradient-to-r from-[#003149] to-[#7740A4] rounded-full"
                            style={{ width: `${(t.count / tools.tools[0].count) * 100}%` }}
                          />
                        </div>
                        <span className="text-xs font-bold text-gray-700 w-10 text-right tabular-nums">{formatNumber(t.count)}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {!dashboard && !error && (
                <div className="flex flex-col items-center justify-center py-20">
                  <BarChart3 className="w-10 h-10 text-gray-300 mb-3" />
                  <p className="text-sm font-medium text-gray-500">No analytics data</p>
                  <p className="text-xs text-gray-400 mt-1">Usage data will appear here once API calls are made</p>
                </div>
              )}
            </>
          )}
        </div>
      </main>
    </div>
    </AuthGuard>
  );
}
