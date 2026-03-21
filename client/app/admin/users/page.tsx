'use client';

import { useState, useEffect, useCallback } from 'react';
import { Plus, Search, Users, Loader2, AlertCircle, RefreshCw, TrendingUp, DollarSign, Zap } from 'lucide-react';
import AuthGuard from '@/components/auth/auth-guard';
import TopNav from '@/components/layout/top-nav';
import PageHeader from '@/components/layout/page-header';
import { useAuth } from '@/contexts/auth-context';

// ---------------------------------------------------------------------------
// Types (matching /api/admin/users response)
// ---------------------------------------------------------------------------

interface UserUsage {
  user_id: string;
  total_tokens: number;
  total_cost: number;
  request_count: number;
}

interface UsersResponse {
  users: UserUsage[];
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

function userInitials(userId: string): string {
  return userId.slice(0, 2).toUpperCase();
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export default function UsersPage() {
  const { getToken } = useAuth();
  const [users, setUsers] = useState<UserUsage[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedDays, setSelectedDays] = useState<number>(30);
  const [searchQuery, setSearchQuery] = useState('');

  const fetchUsers = useCallback(async (days: number) => {
    setIsLoading(true);
    setError(null);
    try {
      const token = await getToken();
      const res = await fetch(`/api/admin/users?days=${days}&limit=50`, {
        headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
      });
      if (!res.ok) throw new Error(`Failed to fetch users (${res.status})`);
      const data: UsersResponse = await res.json();
      setUsers(data.users || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An unexpected error occurred');
      setUsers([]);
    } finally {
      setIsLoading(false);
    }
  }, [getToken]);

  useEffect(() => {
    fetchUsers(selectedDays);
  }, [selectedDays, fetchUsers]);

  const filtered = users.filter(u =>
    u.user_id.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const totalCost = users.reduce((s, u) => s + u.total_cost, 0);
  const totalRequests = users.reduce((s, u) => s + u.request_count, 0);
  const totalTokens = users.reduce((s, u) => s + u.total_tokens, 0);

  return (
    <AuthGuard>
    <div className="flex flex-col h-screen bg-gray-50">
      <TopNav />
      <main className="flex-1 overflow-y-auto">
        <div className="p-8">
          <PageHeader
            title="User Management"
            description="Top users by API usage"
            breadcrumbs={[
              { label: 'Admin', href: '/admin' },
              { label: 'Users' },
            ]}
            actions={
              <button
                onClick={() => fetchUsers(selectedDays)}
                disabled={isLoading}
                className="flex items-center gap-2 px-4 py-2.5 bg-white border border-gray-200 text-gray-700 rounded-xl font-medium hover:bg-gray-50 transition-colors disabled:opacity-50"
              >
                <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
                Refresh
              </button>
            }
          />

          {/* Date Range Selector */}
          <div className="mb-6 flex items-center gap-4">
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

          {/* Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            {[
              { label: 'Active Users', value: String(users.length), icon: <Users className="w-5 h-5" />, color: 'bg-blue-500' },
              { label: 'Total Requests', value: formatNumber(totalRequests), icon: <TrendingUp className="w-5 h-5" />, color: 'bg-purple-500' },
              { label: 'Total Cost', value: formatCurrency(totalCost), icon: <DollarSign className="w-5 h-5" />, color: 'bg-green-500' },
            ].map((card, i) => (
              <div key={i} className="bg-white rounded-2xl border border-gray-200 p-5">
                <div className="flex items-start justify-between mb-4">
                  <div className={`p-3 rounded-xl ${card.color} text-white`}>{card.icon}</div>
                  <span className="text-xs text-gray-400 font-medium">Last {selectedDays} days</span>
                </div>
                <p className="text-2xl font-bold text-gray-900">
                  {isLoading ? <span className="inline-block w-24 h-7 bg-gray-100 rounded animate-pulse" /> : card.value}
                </p>
                <p className="text-sm text-gray-500">{card.label}</p>
              </div>
            ))}
          </div>

          {/* Error State */}
          {error && (
            <div className="mb-6 flex items-center gap-3 p-4 bg-red-50 border border-red-200 rounded-xl text-red-700">
              <AlertCircle className="w-5 h-5 flex-shrink-0" />
              <p className="flex-1">{error}</p>
              <button onClick={() => fetchUsers(selectedDays)} className="px-3 py-1.5 bg-red-100 text-red-700 rounded-lg text-sm font-medium hover:bg-red-200 transition-colors">Retry</button>
            </div>
          )}

          {/* Search */}
          <div className="mb-4">
            <div className="relative max-w-md">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                placeholder="Search users..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2.5 bg-white border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
              />
            </div>
          </div>

          {/* Users Table */}
          {isLoading && !users.length ? (
            <div className="flex flex-col items-center justify-center py-20">
              <Loader2 className="w-8 h-8 text-[#003149] animate-spin mb-4" />
              <p className="text-gray-500 text-sm">Loading users...</p>
            </div>
          ) : (
            <div className="bg-white rounded-2xl border border-gray-200">
              {filtered.length > 0 ? (
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b border-gray-100">
                        <th className="text-left text-xs font-semibold text-gray-500 uppercase tracking-wider px-6 py-3">User</th>
                        <th className="text-right text-xs font-semibold text-gray-500 uppercase tracking-wider px-6 py-3">Requests</th>
                        <th className="text-right text-xs font-semibold text-gray-500 uppercase tracking-wider px-6 py-3">Total Tokens</th>
                        <th className="text-right text-xs font-semibold text-gray-500 uppercase tracking-wider px-6 py-3">Total Cost</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-50">
                      {filtered.map((user) => (
                        <tr key={user.user_id} className="hover:bg-gray-50 transition-colors">
                          <td className="px-6 py-4">
                            <div className="flex items-center gap-3">
                              <div className="w-9 h-9 bg-gradient-to-br from-[#003149] to-[#7740A4] rounded-full flex items-center justify-center text-white font-semibold text-xs">
                                {userInitials(user.user_id)}
                              </div>
                              <span className="text-sm text-gray-700 font-medium truncate max-w-[200px]">{user.user_id}</span>
                            </div>
                          </td>
                          <td className="px-6 py-4 text-sm text-gray-600 text-right tabular-nums">{formatNumber(user.request_count)}</td>
                          <td className="px-6 py-4 text-sm text-gray-600 text-right tabular-nums">
                            <div className="flex items-center justify-end gap-1">
                              <Zap className="w-3 h-3 text-purple-400" />
                              {formatNumber(user.total_tokens)}
                            </div>
                          </td>
                          <td className="px-6 py-4 text-sm font-semibold text-gray-900 text-right tabular-nums">{formatCurrency(user.total_cost)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="p-12 text-center">
                  <Users className="w-10 h-10 text-gray-300 mx-auto mb-3" />
                  <p className="text-sm font-medium text-gray-500">No users found</p>
                  <p className="text-xs text-gray-400 mt-1">No API usage recorded in the last {selectedDays} days</p>
                </div>
              )}
            </div>
          )}
        </div>
      </main>
    </div>
    </AuthGuard>
  );
}
