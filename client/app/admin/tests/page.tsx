'use client';

import { useState, useEffect } from 'react';
import AuthGuard from '@/components/auth/auth-guard';
import TopNav from '@/components/layout/top-nav';
import {
  CheckCircle2,
  XCircle,
  ChevronDown,
  ChevronRight,
  Clock,
  DollarSign,
  Cpu,
  Filter,
  RefreshCw,
} from 'lucide-react';

interface TestResult {
  status: 'pass' | 'fail' | 'error';
  logs: string[];
}

interface TraceData {
  timestamp: string;
  results: Record<string, TestResult>;
}

const TEST_NAMES: Record<string, string> = {
  '1': 'Session Creation + Tenant Context Injection',
  '2': 'Session Resume (Stateless Multi-Turn)',
  '3': 'Trace Observation (Frontend Event Types)',
  '4': 'Subagent Orchestration',
  '5': 'Cost + Token Tracking',
  '6': 'Tier-Gated MCP Tool Access',
  '7': 'Skill Loading: OA Intake',
  '8': 'Subagent Tool Tracking',
  '9': 'OA Intake Workflow',
  '10': 'Legal Counsel Skill',
  '11': 'Market Intelligence Skill',
  '12': 'Tech Review Skill',
  '13': 'Public Interest Skill',
  '14': 'Document Generator Skill',
  '15': 'Supervisor Multi-Skill Chain',
  '16': 'S3 Document Operations',
  '17': 'DynamoDB Intake Operations',
  '18': 'CloudWatch Logs Operations',
  '19': 'Document Generation',
  '20': 'CloudWatch E2E Verification',
  '21': 'UC-02 Micro-Purchase (<$15K)',
  '22': 'UC-03 Option Exercise',
  '23': 'UC-04 Contract Modification',
  '24': 'UC-05 CO Package Review',
  '25': 'UC-07 Contract Close-Out',
  '26': 'UC-08 Shutdown Notification',
  '27': 'UC-09 Score Consolidation',
};

export default function TestResults() {
  const [data, setData] = useState<TraceData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedTests, setExpandedTests] = useState<Set<string>>(new Set());
  const [filter, setFilter] = useState<'all' | 'pass' | 'fail'>('all');

  useEffect(() => {
    loadTraceData();
  }, []);

  const loadTraceData = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch('/api/trace-logs');
      if (!res.ok) throw new Error('Failed to load trace logs');
      const json = await res.json();
      setData(json);
    } catch {
      // Fallback: try loading from a static path or show placeholder
      setError('Could not load trace_logs.json. Run SDK tests to generate results.');
      setData(null);
    }
    setLoading(false);
  };

  const toggleExpand = (id: string) => {
    setExpandedTests(prev => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const expandAll = () => {
    if (!data) return;
    setExpandedTests(new Set(Object.keys(data.results)));
  };

  const collapseAll = () => {
    setExpandedTests(new Set());
  };

  const results = data ? Object.entries(data.results) : [];
  const filteredResults = results.filter(([, r]) => {
    if (filter === 'all') return true;
    if (filter === 'pass') return r.status === 'pass';
    return r.status !== 'pass';
  });

  const passCount = results.filter(([, r]) => r.status === 'pass').length;
  const failCount = results.filter(([, r]) => r.status !== 'pass').length;
  const totalTests = results.length;

  // Extract cost from logs
  const extractCost = (logs: string[]) => {
    for (const line of logs) {
      const match = line.match(/Cost:\s*\$(\d+\.\d+)/);
      if (match) return parseFloat(match[1]);
    }
    return null;
  };

  const extractTokens = (logs: string[]) => {
    for (const line of logs) {
      const match = line.match(/Tokens?:\s*(\d+)\s*in\s*\/\s*(\d+)\s*out/);
      if (match) return { input: parseInt(match[1]), output: parseInt(match[2]) };
    }
    return null;
  };

  const totalCost = results.reduce((sum, [, r]) => sum + (extractCost(r.logs) || 0), 0);

  return (
    <AuthGuard>
      <div className="flex flex-col h-screen overflow-hidden bg-gray-50">
        <TopNav />
          <main className="flex-1 overflow-y-auto">
            <div className="p-8 max-w-6xl">
              {/* Page header */}
              <div className="mb-8">
                <h1 className="text-2xl font-bold text-gray-900">SDK Test Results</h1>
                <p className="mt-1 text-gray-500">Claude Agent SDK validation tests (15 tests across sessions, skills, orchestration)</p>
              </div>

              {loading ? (
                <div className="flex items-center justify-center py-20">
                  <RefreshCw className="w-6 h-6 animate-spin text-gray-400" />
                  <span className="ml-2 text-gray-500">Loading test results...</span>
                </div>
              ) : error ? (
                <div className="bg-amber-50 border border-amber-200 rounded-xl p-6 text-center">
                  <p className="text-amber-700 font-medium">{error}</p>
                  <p className="text-amber-600 text-sm mt-2">Run <code className="bg-amber-100 px-1.5 py-0.5 rounded">python test_eagle_sdk_eval.py</code> to generate results</p>
                </div>
              ) : data && (
                <>
                  {/* Stats cards */}
                  <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
                    <div className="bg-white rounded-2xl border border-gray-200 p-5">
                      <div className="flex items-start justify-between mb-3">
                        <div className="p-3 rounded-xl bg-blue-500 text-white">
                          <Cpu className="w-5 h-5" />
                        </div>
                      </div>
                      <p className="text-2xl font-bold text-gray-900">{totalTests}</p>
                      <p className="text-sm text-gray-500">Total Tests</p>
                    </div>
                    <div className="bg-white rounded-2xl border border-gray-200 p-5">
                      <div className="flex items-start justify-between mb-3">
                        <div className="p-3 rounded-xl bg-green-500 text-white">
                          <CheckCircle2 className="w-5 h-5" />
                        </div>
                      </div>
                      <p className="text-2xl font-bold text-green-600">{passCount}</p>
                      <p className="text-sm text-gray-500">Passed</p>
                    </div>
                    <div className="bg-white rounded-2xl border border-gray-200 p-5">
                      <div className="flex items-start justify-between mb-3">
                        <div className="p-3 rounded-xl bg-red-500 text-white">
                          <XCircle className="w-5 h-5" />
                        </div>
                      </div>
                      <p className="text-2xl font-bold text-red-600">{failCount}</p>
                      <p className="text-sm text-gray-500">Failed</p>
                    </div>
                    <div className="bg-white rounded-2xl border border-gray-200 p-5">
                      <div className="flex items-start justify-between mb-3">
                        <div className="p-3 rounded-xl bg-amber-500 text-white">
                          <DollarSign className="w-5 h-5" />
                        </div>
                      </div>
                      <p className="text-2xl font-bold text-gray-900">${totalCost.toFixed(4)}</p>
                      <p className="text-sm text-gray-500">Total Cost</p>
                    </div>
                  </div>

                  {/* Metadata row */}
                  <div className="flex items-center gap-4 mb-4 text-xs text-gray-500">
                    <span className="flex items-center gap-1">
                      <Clock className="w-3.5 h-3.5" />
                      Run: {new Date(data.timestamp).toLocaleString()}
                    </span>
                    <span className="flex items-center gap-1">
                      Pass rate: {totalTests > 0 ? Math.round((passCount / totalTests) * 100) : 0}%
                    </span>
                  </div>

                  {/* Filter bar */}
                  <div className="flex items-center gap-2 mb-4">
                    <Filter className="w-4 h-4 text-gray-400" />
                    {(['all', 'pass', 'fail'] as const).map(f => (
                      <button
                        key={f}
                        onClick={() => setFilter(f)}
                        className={`px-3 py-1 text-xs rounded-full transition-colors ${
                          filter === f
                            ? 'bg-blue-600 text-white'
                            : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                        }`}
                      >
                        {f === 'all' ? `All (${totalTests})` : f === 'pass' ? `Pass (${passCount})` : `Fail (${failCount})`}
                      </button>
                    ))}
                    <div className="ml-auto flex gap-2">
                      <button onClick={expandAll} className="text-xs text-blue-600 hover:text-blue-700">Expand All</button>
                      <button onClick={collapseAll} className="text-xs text-blue-600 hover:text-blue-700">Collapse All</button>
                    </div>
                  </div>

                  {/* Test list */}
                  <div className="space-y-2">
                    {filteredResults.map(([id, result]) => {
                      const isExpanded = expandedTests.has(id);
                      const cost = extractCost(result.logs);
                      const tokens = extractTokens(result.logs);
                      const name = TEST_NAMES[id] || `Test ${id}`;

                      return (
                        <div key={id} className="bg-white rounded-xl border border-gray-200 overflow-hidden">
                          <button
                            onClick={() => toggleExpand(id)}
                            className="w-full flex items-center gap-3 px-4 py-3 text-left hover:bg-gray-50 transition-colors"
                          >
                            {isExpanded ? <ChevronDown className="w-4 h-4 text-gray-400 shrink-0" /> : <ChevronRight className="w-4 h-4 text-gray-400 shrink-0" />}
                            {result.status === 'pass' ? (
                              <CheckCircle2 className="w-5 h-5 text-green-500 shrink-0" />
                            ) : (
                              <XCircle className="w-5 h-5 text-red-500 shrink-0" />
                            )}
                            <div className="flex-1 min-w-0">
                              <span className="text-sm font-medium text-gray-900">Test {id}: {name}</span>
                            </div>
                            <div className="flex items-center gap-4 text-xs text-gray-500">
                              {tokens && (
                                <span>{tokens.input.toLocaleString()} in / {tokens.output} out</span>
                              )}
                              {cost !== null && (
                                <span className="font-mono">${cost.toFixed(4)}</span>
                              )}
                              <span className={`px-2 py-0.5 rounded-full font-medium ${
                                result.status === 'pass' ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'
                              }`}>
                                {result.status.toUpperCase()}
                              </span>
                            </div>
                          </button>
                          {isExpanded && (
                            <div className="border-t border-gray-100 bg-gray-50 px-4 py-3">
                              <pre className="text-[11px] text-gray-600 font-mono whitespace-pre-wrap leading-relaxed max-h-80 overflow-y-auto">
                                {result.logs.join('\n')}
                              </pre>
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                </>
              )}
            </div>
          </main>
      </div>
    </AuthGuard>
  );
}
