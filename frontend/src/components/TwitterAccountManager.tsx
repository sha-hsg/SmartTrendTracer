import { useState, useEffect, useCallback } from 'react';
import { Plus, RefreshCw, Search, Users, ToggleLeft, ToggleRight, Trash2, Edit2, ChevronDown, ChevronUp, ExternalLink, Activity, Clock, TrendingUp, BarChart3, Calendar, AlertTriangle, CheckCircle, XCircle, Zap, Download, Loader2, MinusCircle, AlertCircle, CircleDashed } from 'lucide-react';
import axios from 'axios';

interface TwitterAccount {
  id: string;
  twitter_id: string;
  username: string;
  display_name: string;
  category: string;
  description: string | null;
  tier: number;
  enabled: boolean;
  created_at: string | null;
  updated_at: string | null;
  profile_image_url: string | null;
  followers_count: number | null;
  verified: boolean | null;
  last_collected_at: string | null;
  tweets_collected: number;
}

interface AccountStats {
  accounts: Array<{
    id: string;
    username: string;
    display_name: string;
    tier: number;
    enabled: boolean;
    category: string;
    tweets_collected: number;
    // Tweet timing (when tweets were POSTED on Twitter)
    latest_tweet: string | null;
    oldest_tweet: string | null;
    days_without_new_tweets: number | null;
    // Collection timing (when WE CHECKED this account)
    last_checked_at: string | null;
    minutes_since_check: number | null;
    minutes_until_next: number | null;
    is_overdue: boolean;
    // Check result
    tweets_in_last_check: number;
    check_status: 'success' | 'no_new_tweets' | 'error' | 'never_checked';
    last_error: string | null;
    error_count: number;
    // Legacy fields
    last_collection_run: string | null;
    tweets_in_last_collection: number;
  }>;
  total_accounts: number;
  enabled_accounts: number;
  total_tweets: number;
  // New summary fields
  accounts_with_new_tweets: number;
  accounts_without_new_tweets: number;
  accounts_with_errors: number;
  accounts_never_checked: number;
  accounts_overdue: number;
}

interface DashboardData {
  overview: {
    total_accounts: number;
    enabled_accounts: number;
    disabled_accounts: number;
    total_tweets: number;
    tweets_24h: number;
    tweets_7d: number;
    tweets_30d: number;
    avg_tweets_per_day: number;
  };
  last_collection: {
    timestamp: string | null;
    account: string | null;
    total_tweets_collected: number;
  };
  tier_stats: Record<number, { accounts: number; tweets: number }>;
  category_stats: Record<string, { accounts: number; tweets: number }>;
  top_accounts: Array<{ username: string; tweets: number }>;
  recent_activity: Array<{
    username: string;
    last_run: string;
    tweets_collected: number;
    last_tweet_id: string | null;
  }>;
}

interface CollectionHistory {
  period_days: number;
  start_date: string;
  end_date: string;
  total_tweets: number;
  daily_history: Array<{ date: string; tweets: number }>;
  by_account: Array<{ username: string; tweets: number }>;
}

interface CollectorStatus {
  collector_running: boolean;
  collector_pid: string | null;
  last_collection: {
    timestamp: string | null;
    account: string | null;
    time_ago: { minutes: number; hours: number } | null;
  };
  cycle_summary: {
    accounts_checked: number;
    accounts_with_new_tweets: number;
    accounts_without_new_tweets: number;
    accounts_never_checked: number;
    accounts_with_errors: number;
    total_tweets_collected: number;
  };
  overdue_accounts: {
    tier_1: Array<{ username: string; minutes_overdue: number | null }>;
    tier_2: Array<{ username: string; minutes_overdue: number | null }>;
    tier_3: Array<{ username: string; minutes_overdue: number | null }>;
    total: number;
  };
  schedule: {
    tier_1_interval: string;
    tier_2_interval: string;
    tier_3_interval: string;
  };
}

interface UsageStats {
  monthly: {
    collected: number;
    limit: number;
    remaining: number;
    usage_percentage: number;
    days_elapsed: number;
    days_remaining: number;
  };
  daily: {
    collected: number;
    suggested_budget: number;
    avg_last_7_days: number;
  };
  status: 'ok' | 'warning' | 'critical';
}

interface LiveProgress {
  status: 'collecting' | 'sleeping' | 'rate_limited' | 'error' | 'stopped' | 'unknown';
  current_account: string | null;
  accounts_processed: number;
  total_accounts: number;
  progress_percent: number;
  tweets_this_cycle: number;
  current_batch: number;
  total_batches: number;
  cycle_start_time: string | null;
  next_cycle_at: string | null;
  seconds_until_next_cycle: number | null;
  error_message: string | null;
  updated_at: string | null;
  seconds_since_update: number | null;
  is_stale: boolean;
  pid: number | null;
}

interface AddAccountData {
  username: string;
  display_name: string;
  category: string;
  description: string;
  tier: number;
  enabled: boolean;
}

interface TwitterUserLookup {
  exists: boolean;
  user?: {
    id: string;
    username: string;
    name: string;
    description: string | null;
    profile_image_url: string | null;
    followers_count: number;
    verified: boolean;
  };
  error?: string;
}

const API_BASE = 'http://localhost:8000/api/twitter-accounts';

const TIER_LABELS: Record<number, string> = {
  1: 'High Priority',
  2: 'Medium Priority',
  3: 'Low Priority'
};

const TIER_COLORS: Record<number, string> = {
  1: 'bg-red-100 text-red-800',
  2: 'bg-yellow-100 text-yellow-800',
  3: 'bg-green-100 text-green-800'
};

const CATEGORIES = [
  'AI Company',
  'AI Research',
  'AI Education',
  'AI Tools',
  'AI Leadership',
  'AI Community',
  'AI Applications',
  'Conference',
  'PhD Student',
  'Asst Prof',
  'Other'
];

export default function TwitterAccountManager() {
  const [accounts, setAccounts] = useState<TwitterAccount[]>([]);
  const [stats, setStats] = useState<AccountStats | null>(null);
  const [dashboard, setDashboard] = useState<DashboardData | null>(null);
  const [history, setHistory] = useState<CollectionHistory | null>(null);
  const [collectorStatus, setCollectorStatus] = useState<CollectorStatus | null>(null);
  const [usageStats, setUsageStats] = useState<UsageStats | null>(null);
  const [liveProgress, setLiveProgress] = useState<LiveProgress | null>(null);
  const [loading, setLoading] = useState(true);
  const [collectingAccount, setCollectingAccount] = useState<string | null>(null);
  const [collectionResult, setCollectionResult] = useState<{
    success: boolean;
    account: string;
    message: string;
    tweets_collected?: number;
    new_tweets?: number;
  } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterTier, setFilterTier] = useState<number | null>(null);
  const [filterCategory, setFilterCategory] = useState<string | null>(null);
  const [showAddModal, setShowAddModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [editingAccount, setEditingAccount] = useState<TwitterAccount | null>(null);
  const [sortField, setSortField] = useState<'username' | 'tier' | 'tweets_collected' | 'category' | 'status' | 'last_checked' | 'last_tweet'>('tier');
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('asc');
  const [activeTab, setActiveTab] = useState<'accounts' | 'dashboard'>('dashboard');

  // Add account form state
  const [newAccountData, setNewAccountData] = useState<AddAccountData>({
    username: '',
    display_name: '',
    category: 'Other',
    description: '',
    tier: 2,
    enabled: true
  });
  const [lookupResult, setLookupResult] = useState<TwitterUserLookup | null>(null);
  const [lookingUp, setLookingUp] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const fetchAccounts = useCallback(async () => {
    try {
      setLoading(true);
      const [accountsRes, statsRes, dashboardRes, historyRes, statusRes, usageRes] = await Promise.all([
        axios.get<TwitterAccount[]>(API_BASE),
        axios.get<AccountStats>(`${API_BASE}/stats`),
        axios.get<DashboardData>(`${API_BASE}/dashboard`),
        axios.get<CollectionHistory>(`${API_BASE}/collection-history?days=30`),
        axios.get<CollectorStatus>(`${API_BASE}/collector-status`),
        axios.get<UsageStats>(`${API_BASE}/usage`)
      ]);
      setAccounts(accountsRes.data);
      setStats(statsRes.data);
      setDashboard(dashboardRes.data);
      setHistory(historyRes.data);
      setCollectorStatus(statusRes.data);
      setUsageStats(usageRes.data);
      setError(null);
    } catch (err) {
      setError('Failed to load accounts');
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, []);

  // Fetch collector status more frequently (every 10 seconds)
  const fetchCollectorStatus = useCallback(async () => {
    try {
      const res = await axios.get<CollectorStatus>(`${API_BASE}/collector-status`);
      setCollectorStatus(res.data);
    } catch (err) {
      console.error('Failed to fetch collector status:', err);
    }
  }, []);

  // Fetch live collection progress (every 2 seconds when actively collecting)
  const fetchLiveProgress = useCallback(async () => {
    try {
      const res = await axios.get<LiveProgress>(`${API_BASE}/live-progress`);
      setLiveProgress(res.data);
    } catch (err) {
      console.error('Failed to fetch live progress:', err);
    }
  }, []);

  useEffect(() => {
    fetchAccounts();
  }, [fetchAccounts]);

  // Auto-refresh collector status every 10 seconds when on dashboard tab
  useEffect(() => {
    if (activeTab !== 'dashboard') return;

    const interval = setInterval(fetchCollectorStatus, 10000);
    return () => clearInterval(interval);
  }, [activeTab, fetchCollectorStatus]);

  // Fast polling for live progress when collector is running and actively collecting
  useEffect(() => {
    if (activeTab !== 'dashboard') return;
    if (!collectorStatus?.collector_running) return;

    // Initial fetch
    fetchLiveProgress();

    // Poll every 2 seconds during active collection
    const interval = setInterval(fetchLiveProgress, 2000);
    return () => clearInterval(interval);
  }, [activeTab, collectorStatus?.collector_running, fetchLiveProgress]);

  const lookupTwitterUser = async () => {
    if (!newAccountData.username.trim()) return;

    setLookingUp(true);
    try {
      const res = await axios.get<TwitterUserLookup>(`${API_BASE}/lookup`, {
        params: { username: newAccountData.username.replace('@', '') }
      });
      setLookupResult(res.data);

      if (res.data.exists && res.data.user) {
        setNewAccountData(prev => ({
          ...prev,
          display_name: res.data.user!.name || prev.display_name
        }));
      }
    } catch (err: unknown) {
      if (axios.isAxiosError(err)) {
        setLookupResult({ exists: false, error: err.response?.data?.detail || 'Lookup failed' });
      }
    } finally {
      setLookingUp(false);
    }
  };

  const addAccount = async () => {
    setSubmitting(true);
    try {
      await axios.post(API_BASE, {
        username: newAccountData.username.replace('@', ''),
        display_name: newAccountData.display_name || null,
        category: newAccountData.category,
        description: newAccountData.description || null,
        tier: newAccountData.tier,
        enabled: newAccountData.enabled
      });
      setShowAddModal(false);
      setNewAccountData({
        username: '',
        display_name: '',
        category: 'Other',
        description: '',
        tier: 2,
        enabled: true
      });
      setLookupResult(null);
      fetchAccounts();
    } catch (err: unknown) {
      if (axios.isAxiosError(err)) {
        setError(err.response?.data?.detail || 'Failed to add account');
      }
    } finally {
      setSubmitting(false);
    }
  };

  const updateAccount = async () => {
    if (!editingAccount) return;

    setSubmitting(true);
    try {
      await axios.put(`${API_BASE}/${editingAccount.id}`, {
        display_name: editingAccount.display_name,
        category: editingAccount.category,
        description: editingAccount.description,
        tier: editingAccount.tier,
        enabled: editingAccount.enabled
      });
      setShowEditModal(false);
      setEditingAccount(null);
      fetchAccounts();
    } catch (err: unknown) {
      if (axios.isAxiosError(err)) {
        setError(err.response?.data?.detail || 'Failed to update account');
      }
    } finally {
      setSubmitting(false);
    }
  };

  const toggleAccount = async (account: TwitterAccount) => {
    try {
      await axios.post(`${API_BASE}/${account.id}/toggle`);
      fetchAccounts();
    } catch (err) {
      console.error('Failed to toggle account:', err);
    }
  };

  const deleteAccount = async (account: TwitterAccount) => {
    if (!confirm(`Delete @${account.username}? This will remove the account from monitoring.`)) {
      return;
    }

    try {
      await axios.delete(`${API_BASE}/${account.id}`);
      fetchAccounts();
    } catch (err) {
      console.error('Failed to delete account:', err);
    }
  };

  const refreshAccountInfo = async (account: TwitterAccount) => {
    try {
      await axios.post(`${API_BASE}/${account.id}/refresh`);
      fetchAccounts();
    } catch (err: unknown) {
      if (axios.isAxiosError(err)) {
        setError(err.response?.data?.detail || 'Failed to refresh account');
      }
    }
  };

  const collectTweets = async (account: TwitterAccount, maxTweets: number = 100) => {
    setCollectingAccount(account.id);
    setCollectionResult(null);
    try {
      const res = await axios.post(`${API_BASE}/${account.id}/collect?max_tweets=${maxTweets}`);
      setCollectionResult({
        success: true,
        account: account.username,
        message: res.data.message,
        tweets_collected: res.data.tweets_collected,
        new_tweets: res.data.new_tweets
      });
      // Refresh data after collection
      fetchAccounts();
    } catch (err: unknown) {
      if (axios.isAxiosError(err)) {
        setCollectionResult({
          success: false,
          account: account.username,
          message: err.response?.data?.detail || 'Collection failed'
        });
      }
    } finally {
      setCollectingAccount(null);
    }
  };

  // Helper to get stats for an account
  const getAccountStats = (accountId: string) => stats?.accounts.find(s => s.id === accountId);

  // Filter and sort accounts
  const filteredAccounts = accounts
    .filter(acc => {
      if (searchTerm && !acc.username.toLowerCase().includes(searchTerm.toLowerCase()) &&
          !acc.display_name.toLowerCase().includes(searchTerm.toLowerCase())) {
        return false;
      }
      if (filterTier !== null && acc.tier !== filterTier) return false;
      if (filterCategory && acc.category !== filterCategory) return false;
      return true;
    })
    .sort((a, b) => {
      let comparison = 0;
      const statsA = getAccountStats(a.id);
      const statsB = getAccountStats(b.id);

      if (sortField === 'username') {
        comparison = a.username.localeCompare(b.username);
      } else if (sortField === 'tier') {
        comparison = a.tier - b.tier;
      } else if (sortField === 'tweets_collected') {
        comparison = a.tweets_collected - b.tweets_collected;
      } else if (sortField === 'category') {
        comparison = a.category.localeCompare(b.category);
      } else if (sortField === 'status') {
        // Sort by check_status: success > no_new_tweets > error > never_checked
        const statusOrder = { 'success': 0, 'no_new_tweets': 1, 'error': 2, 'never_checked': 3 };
        const statusA = statsA?.check_status || 'never_checked';
        const statusB = statsB?.check_status || 'never_checked';
        comparison = statusOrder[statusA] - statusOrder[statusB];
      } else if (sortField === 'last_checked') {
        // Sort by minutes_since_check (lower = more recent = comes first in asc)
        const minsA = statsA?.minutes_since_check ?? 999999;
        const minsB = statsB?.minutes_since_check ?? 999999;
        comparison = minsA - minsB;
      } else if (sortField === 'last_tweet') {
        // Sort by latest_tweet date
        const dateA = statsA?.latest_tweet ? new Date(statsA.latest_tweet).getTime() : 0;
        const dateB = statsB?.latest_tweet ? new Date(statsB.latest_tweet).getTime() : 0;
        comparison = dateB - dateA; // More recent first in asc
      }
      return sortDirection === 'asc' ? comparison : -comparison;
    });

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return 'Never';
    const date = new Date(dateStr);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));

    if (diffHours < 1) return 'Just now';
    if (diffHours < 24) return `${diffHours}h ago`;
    const diffDays = Math.floor(diffHours / 24);
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString();
  };

  const SortHeader = ({ field, label }: { field: typeof sortField; label: string }) => (
    <th
      className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
      onClick={() => {
        if (sortField === field) {
          setSortDirection(d => d === 'asc' ? 'desc' : 'asc');
        } else {
          setSortField(field);
          setSortDirection('asc');
        }
      }}
    >
      <div className="flex items-center gap-1">
        {label}
        {sortField === field && (
          sortDirection === 'asc' ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />
        )}
      </div>
    </th>
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="w-8 h-8 animate-spin text-blue-500" />
      </div>
    );
  }

  // Simple bar chart component
  const SimpleBarChart = ({ data, maxValue }: { data: Array<{ date: string; tweets: number }>; maxValue: number }) => {
    const last14Days = data.slice(-14);
    return (
      <div className="flex items-end gap-1 h-24">
        {last14Days.map((d, i) => {
          const height = maxValue > 0 ? (d.tweets / maxValue) * 100 : 0;
          return (
            <div
              key={i}
              className="flex-1 bg-blue-500 rounded-t hover:bg-blue-600 transition-colors cursor-pointer group relative"
              style={{ height: `${Math.max(height, 2)}%` }}
              title={`${d.date}: ${d.tweets} tweets`}
            >
              <div className="hidden group-hover:block absolute bottom-full mb-1 left-1/2 -translate-x-1/2 bg-gray-800 text-white text-xs px-2 py-1 rounded whitespace-nowrap z-10">
                {d.date.slice(5)}: {d.tweets}
              </div>
            </div>
          );
        })}
      </div>
    );
  };

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <Users className="w-8 h-8 text-blue-500" />
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Twitter Account Manager</h1>
            <p className="text-sm text-gray-500">
              Manage monitored Twitter accounts ({dashboard?.overview.enabled_accounts}/{dashboard?.overview.total_accounts} enabled)
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={fetchAccounts}
            className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg"
            title="Refresh"
          >
            <RefreshCw className="w-5 h-5" />
          </button>
          <button
            onClick={() => setShowAddModal(true)}
            className="flex items-center gap-2 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600"
          >
            <Plus className="w-5 h-5" />
            Add Account
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 mb-6 border-b">
        <button
          onClick={() => setActiveTab('dashboard')}
          className={`px-4 py-2 font-medium border-b-2 transition-colors ${
            activeTab === 'dashboard'
              ? 'border-blue-500 text-blue-600'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          <div className="flex items-center gap-2">
            <BarChart3 className="w-4 h-4" />
            Dashboard
          </div>
        </button>
        <button
          onClick={() => setActiveTab('accounts')}
          className={`px-4 py-2 font-medium border-b-2 transition-colors ${
            activeTab === 'accounts'
              ? 'border-blue-500 text-blue-600'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          <div className="flex items-center gap-2">
            <Users className="w-4 h-4" />
            Accounts ({stats?.total_accounts})
          </div>
        </button>
      </div>

      {/* Error Alert */}
      {error && (
        <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
          {error}
          <button onClick={() => setError(null)} className="ml-2 underline">Dismiss</button>
        </div>
      )}

      {/* Collection Result Notification */}
      {collectionResult && (
        <div className={`mb-4 p-4 rounded-lg border flex items-start justify-between ${
          collectionResult.success
            ? 'bg-green-50 border-green-200'
            : 'bg-red-50 border-red-200'
        }`}>
          <div className="flex items-start gap-3">
            {collectionResult.success ? (
              <CheckCircle className="w-5 h-5 text-green-600 mt-0.5" />
            ) : (
              <XCircle className="w-5 h-5 text-red-600 mt-0.5" />
            )}
            <div>
              <div className={`font-medium ${collectionResult.success ? 'text-green-800' : 'text-red-800'}`}>
                {collectionResult.success ? 'Collection Complete' : 'Collection Failed'}
              </div>
              <div className={`text-sm ${collectionResult.success ? 'text-green-700' : 'text-red-700'}`}>
                @{collectionResult.account}: {collectionResult.message}
              </div>
              {collectionResult.success && collectionResult.new_tweets !== undefined && (
                <div className="text-sm text-green-600 mt-1">
                  <span className="font-medium">{collectionResult.new_tweets}</span> new tweets added
                  {collectionResult.tweets_collected !== undefined && (
                    <span className="text-gray-500 ml-2">
                      ({collectionResult.tweets_collected} fetched, {collectionResult.tweets_collected - collectionResult.new_tweets} duplicates)
                    </span>
                  )}
                </div>
              )}
            </div>
          </div>
          <button
            onClick={() => setCollectionResult(null)}
            className="text-gray-400 hover:text-gray-600"
          >
            <XCircle className="w-5 h-5" />
          </button>
        </div>
      )}

      {/* Dashboard Tab */}
      {activeTab === 'dashboard' && dashboard && (
        <div className="space-y-6">
          {/* Live Collector Status */}
          {collectorStatus && (
            <div className={`p-4 rounded-lg border-2 ${
              collectorStatus.collector_running
                ? 'bg-green-50 border-green-200'
                : 'bg-red-50 border-red-200'
            }`}>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  {collectorStatus.collector_running ? (
                    <div className="flex items-center gap-2">
                      <div className="relative">
                        <Zap className="w-6 h-6 text-green-600" />
                        <span className="absolute -top-1 -right-1 w-3 h-3 bg-green-500 rounded-full animate-pulse" />
                      </div>
                      <div>
                        <div className="font-semibold text-green-800">Collector Running</div>
                        <div className="text-sm text-green-600">PID: {collectorStatus.collector_pid}</div>
                      </div>
                    </div>
                  ) : (
                    <div className="flex items-center gap-2">
                      <XCircle className="w-6 h-6 text-red-600" />
                      <div>
                        <div className="font-semibold text-red-800">Collector Stopped</div>
                        <div className="text-sm text-red-600">Start with: python tweet_collector_service.py</div>
                      </div>
                    </div>
                  )}
                </div>
                <div className="flex items-center gap-6 text-sm">
                  <div className="text-right">
                    <div className="text-gray-500">Last Collection</div>
                    <div className="font-medium">
                      {collectorStatus.last_collection.time_ago
                        ? `${collectorStatus.last_collection.time_ago.minutes} min ago`
                        : 'Never'
                      }
                      {collectorStatus.last_collection.account && (
                        <span className="text-gray-500 ml-1">(@{collectorStatus.last_collection.account})</span>
                      )}
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-gray-500">Need Checking</div>
                    <div className={`font-bold ${
                      collectorStatus.overdue_accounts.total > 0 ? 'text-orange-600' : 'text-green-600'
                    }`}>
                      {collectorStatus.overdue_accounts.total > 0
                        ? `${collectorStatus.overdue_accounts.total} accounts`
                        : 'All up to date'}
                    </div>
                  </div>
                  <button
                    onClick={fetchCollectorStatus}
                    className="p-2 text-gray-500 hover:text-gray-700 hover:bg-white/50 rounded-lg"
                    title="Refresh status"
                  >
                    <RefreshCw className="w-4 h-4" />
                  </button>
                </div>
              </div>

              {/* Live Collection Progress */}
              {liveProgress && liveProgress.status === 'collecting' && !liveProgress.is_stale && (
                <div className="mt-3 pt-3 border-t border-current/10">
                  <div className="space-y-2">
                    <div className="flex items-center justify-between text-sm">
                      <div className="flex items-center gap-2">
                        <Loader2 className="w-4 h-4 text-blue-500 animate-spin" />
                        <span className="text-blue-700 font-medium">Live Collection</span>
                        {liveProgress.current_account && (
                          <span className="px-2 py-0.5 bg-blue-100 text-blue-700 rounded text-xs">
                            @{liveProgress.current_account}
                          </span>
                        )}
                      </div>
                      <div className="text-gray-600">
                        Batch {liveProgress.current_batch}/{liveProgress.total_batches}
                      </div>
                    </div>

                    {/* Progress bar */}
                    <div className="relative h-2 bg-gray-200 rounded-full overflow-hidden">
                      <div
                        className="absolute h-full bg-blue-500 transition-all duration-300"
                        style={{ width: `${liveProgress.progress_percent}%` }}
                      />
                    </div>

                    <div className="flex justify-between text-xs text-gray-500">
                      <span>
                        {liveProgress.accounts_processed} / {liveProgress.total_accounts} accounts
                        ({liveProgress.progress_percent}%)
                      </span>
                      <span className="text-green-600 font-medium">
                        +{liveProgress.tweets_this_cycle} tweets
                      </span>
                    </div>
                  </div>
                </div>
              )}

              {/* Sleeping Status with Countdown */}
              {liveProgress && liveProgress.status === 'sleeping' && !liveProgress.is_stale && liveProgress.seconds_until_next_cycle !== null && (
                <div className="mt-3 pt-3 border-t border-current/10">
                  <div className="flex items-center justify-between text-sm">
                    <div className="flex items-center gap-2">
                      <Clock className="w-4 h-4 text-gray-400" />
                      <span className="text-gray-600">Next cycle in:</span>
                      <span className="font-medium text-gray-700">
                        {liveProgress.seconds_until_next_cycle > 60
                          ? `${Math.floor(liveProgress.seconds_until_next_cycle / 60)}m ${liveProgress.seconds_until_next_cycle % 60}s`
                          : `${liveProgress.seconds_until_next_cycle}s`
                        }
                      </span>
                    </div>
                  </div>
                </div>
              )}

              {/* Cycle Summary (shown when not actively collecting) */}
              {collectorStatus.cycle_summary && (!liveProgress || liveProgress.status !== 'collecting' || liveProgress.is_stale) && (
                <div className="mt-3 pt-3 border-t border-current/10">
                  <div className="flex items-center justify-between text-sm">
                    <div className="flex items-center gap-4">
                      <span className="text-gray-600">Last Cycle:</span>
                      <span className="flex items-center gap-1">
                        <CheckCircle className="w-4 h-4 text-green-500" />
                        <span className="text-green-700 font-medium">
                          {collectorStatus.cycle_summary.accounts_with_new_tweets}
                        </span>
                        <span className="text-gray-500">had new tweets</span>
                      </span>
                      <span className="flex items-center gap-1">
                        <MinusCircle className="w-4 h-4 text-blue-400" />
                        <span className="text-blue-600 font-medium">
                          {collectorStatus.cycle_summary.accounts_without_new_tweets}
                        </span>
                        <span className="text-gray-500">no new tweets</span>
                      </span>
                      {collectorStatus.cycle_summary.accounts_with_errors > 0 && (
                        <span className="flex items-center gap-1">
                          <AlertCircle className="w-4 h-4 text-red-500" />
                          <span className="text-red-600 font-medium">
                            {collectorStatus.cycle_summary.accounts_with_errors}
                          </span>
                          <span className="text-gray-500">errors</span>
                        </span>
                      )}
                    </div>
                    <div className="text-right">
                      <span className="text-gray-500">Collected: </span>
                      <span className="font-bold text-green-600">
                        {collectorStatus.cycle_summary.total_tweets_collected}
                      </span>
                      <span className="text-gray-500"> tweets</span>
                    </div>
                  </div>
                </div>
              )}

              {/* Accounts Due for Check */}
              {collectorStatus.overdue_accounts.total > 0 && (
                <div className="mt-3 pt-3 border-t border-current/10">
                  <div className="flex items-center gap-2 text-sm flex-wrap">
                    <AlertTriangle className="w-4 h-4 text-orange-500" />
                    <span className="text-gray-700">
                      Not checked yet:
                      <span className="font-medium text-red-600 ml-1">
                        T1: {collectorStatus.overdue_accounts.tier_1.length}
                      </span>
                      <span className="font-medium text-yellow-600 ml-2">
                        T2: {collectorStatus.overdue_accounts.tier_2.length}
                      </span>
                      <span className="font-medium text-green-600 ml-2">
                        T3: {collectorStatus.overdue_accounts.tier_3.length}
                      </span>
                    </span>
                    {collectorStatus.overdue_accounts.tier_1.slice(0, 3).map(acc => (
                      <span key={acc.username} className="px-2 py-0.5 bg-white/50 rounded text-xs">
                        @{acc.username}
                        {acc.minutes_overdue !== null && (
                          <span className="text-gray-500 ml-1" title="Time since last check">
                            ({acc.minutes_overdue > 60 ? `${Math.round(acc.minutes_overdue / 60)}h ago` : `${acc.minutes_overdue}m ago`})
                          </span>
                        )}
                      </span>
                    ))}
                    {collectorStatus.overdue_accounts.tier_1.length > 3 && (
                      <span className="text-xs text-gray-500">
                        +{collectorStatus.overdue_accounts.tier_1.length - 3} more
                      </span>
                    )}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Monthly Usage Budget */}
          {usageStats && (
            <div className={`p-4 rounded-lg border-2 ${
              usageStats.status === 'ok' ? 'bg-blue-50 border-blue-200' :
              usageStats.status === 'warning' ? 'bg-yellow-50 border-yellow-300' :
              'bg-red-50 border-red-300'
            }`}>
              <div className="flex items-center justify-between mb-3">
                <h3 className="font-semibold text-gray-900 flex items-center gap-2">
                  <BarChart3 className="w-5 h-5" />
                  Monthly Tweet Budget (Basic Account)
                </h3>
                <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                  usageStats.status === 'ok' ? 'bg-green-100 text-green-800' :
                  usageStats.status === 'warning' ? 'bg-yellow-100 text-yellow-800' :
                  'bg-red-100 text-red-800'
                }`}>
                  {usageStats.status === 'ok' ? 'On Track' :
                   usageStats.status === 'warning' ? 'Caution' : 'Over Budget'}
                </span>
              </div>

              {/* Progress bar */}
              <div className="relative h-4 bg-gray-200 rounded-full overflow-hidden mb-2">
                <div
                  className={`absolute h-full transition-all ${
                    usageStats.status === 'ok' ? 'bg-blue-500' :
                    usageStats.status === 'warning' ? 'bg-yellow-500' :
                    'bg-red-500'
                  }`}
                  style={{ width: `${Math.min(usageStats.monthly.usage_percentage, 100)}%` }}
                />
                {/* Budget line indicator */}
                <div
                  className="absolute h-full w-0.5 bg-gray-700"
                  style={{ left: `${(usageStats.monthly.days_elapsed / 30) * 100}%` }}
                  title={`Expected usage at day ${usageStats.monthly.days_elapsed}`}
                />
              </div>

              <div className="flex justify-between text-sm">
                <span className="text-gray-600">
                  <span className="font-bold text-gray-900">{usageStats.monthly.collected.toLocaleString()}</span> collected
                </span>
                <span className="text-gray-600">
                  <span className="font-bold text-green-600">{usageStats.monthly.remaining.toLocaleString()}</span> remaining
                </span>
                <span className="text-gray-500">
                  of {usageStats.monthly.limit.toLocaleString()} total
                </span>
              </div>

              <div className="grid grid-cols-3 gap-4 mt-4 pt-3 border-t border-current/10">
                <div className="text-center">
                  <div className="text-lg font-bold text-gray-900">{usageStats.daily.collected}</div>
                  <div className="text-xs text-gray-500">Today</div>
                </div>
                <div className="text-center">
                  <div className="text-lg font-bold text-blue-600">{usageStats.daily.suggested_budget}</div>
                  <div className="text-xs text-gray-500">Daily Budget</div>
                </div>
                <div className="text-center">
                  <div className="text-lg font-bold text-gray-700">{usageStats.daily.avg_last_7_days}</div>
                  <div className="text-xs text-gray-500">7-Day Avg</div>
                </div>
              </div>

              <div className="mt-3 text-xs text-gray-500 text-center">
                Day {usageStats.monthly.days_elapsed} of month · {usageStats.monthly.days_remaining} days remaining
              </div>
            </div>
          )}

          {/* Overview Stats */}
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
            <div className="bg-white p-4 rounded-lg border shadow-sm">
              <div className="flex items-center gap-2 text-gray-500 mb-1">
                <Users className="w-4 h-4" />
                <span className="text-xs">Total Accounts</span>
              </div>
              <div className="text-2xl font-bold text-gray-900">{dashboard.overview.total_accounts}</div>
            </div>
            <div className="bg-white p-4 rounded-lg border shadow-sm">
              <div className="flex items-center gap-2 text-gray-500 mb-1">
                <Activity className="w-4 h-4" />
                <span className="text-xs">Enabled</span>
              </div>
              <div className="text-2xl font-bold text-green-600">{dashboard.overview.enabled_accounts}</div>
            </div>
            <div className="bg-white p-4 rounded-lg border shadow-sm">
              <div className="flex items-center gap-2 text-gray-500 mb-1">
                <TrendingUp className="w-4 h-4" />
                <span className="text-xs">Total Tweets</span>
              </div>
              <div className="text-2xl font-bold text-blue-600">{dashboard.overview.total_tweets.toLocaleString()}</div>
            </div>
            <div className="bg-white p-4 rounded-lg border shadow-sm">
              <div className="flex items-center gap-2 text-gray-500 mb-1">
                <Clock className="w-4 h-4" />
                <span className="text-xs">Last 24h</span>
              </div>
              <div className="text-2xl font-bold text-purple-600">{dashboard.overview.tweets_24h.toLocaleString()}</div>
            </div>
            <div className="bg-white p-4 rounded-lg border shadow-sm">
              <div className="flex items-center gap-2 text-gray-500 mb-1">
                <Calendar className="w-4 h-4" />
                <span className="text-xs">Last 7 Days</span>
              </div>
              <div className="text-2xl font-bold text-indigo-600">{dashboard.overview.tweets_7d.toLocaleString()}</div>
            </div>
            <div className="bg-white p-4 rounded-lg border shadow-sm">
              <div className="flex items-center gap-2 text-gray-500 mb-1">
                <BarChart3 className="w-4 h-4" />
                <span className="text-xs">Avg/Day</span>
              </div>
              <div className="text-2xl font-bold text-orange-600">{dashboard.overview.avg_tweets_per_day}</div>
            </div>
          </div>

          {/* Collection Activity and Chart */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Tweet Activity Chart */}
            <div className="bg-white p-4 rounded-lg border shadow-sm">
              <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <TrendingUp className="w-5 h-5 text-blue-500" />
                Tweet Activity (Last 14 Days)
              </h3>
              {history && history.daily_history.length > 0 ? (
                <div>
                  <SimpleBarChart
                    data={history.daily_history}
                    maxValue={Math.max(...history.daily_history.map(d => d.tweets))}
                  />
                  <div className="flex justify-between text-xs text-gray-500 mt-2">
                    <span>{history.daily_history.slice(-14)[0]?.date.slice(5)}</span>
                    <span>{history.daily_history.slice(-1)[0]?.date.slice(5)}</span>
                  </div>
                </div>
              ) : (
                <div className="text-gray-500 text-center py-8">No recent activity data</div>
              )}
            </div>

            {/* Last Collection Info */}
            <div className="bg-white p-4 rounded-lg border shadow-sm">
              <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <Clock className="w-5 h-5 text-green-500" />
                Last Collection
              </h3>
              {dashboard.last_collection.timestamp ? (
                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="text-gray-500">Time</span>
                    <span className="font-medium">{formatDate(dashboard.last_collection.timestamp)}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-gray-500">Account</span>
                    <span className="font-medium">@{dashboard.last_collection.account}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-gray-500">Tweets Collected</span>
                    <span className="font-medium text-green-600">{dashboard.last_collection.total_tweets_collected}</span>
                  </div>
                </div>
              ) : (
                <div className="text-gray-500 text-center py-8">No collection runs yet</div>
              )}
            </div>
          </div>

          {/* Tier Stats and Top Accounts */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Tier Distribution */}
            <div className="bg-white p-4 rounded-lg border shadow-sm">
              <h3 className="font-semibold text-gray-900 mb-4">Collection Priority Tiers</h3>
              <div className="space-y-3">
                {[1, 2, 3].map(tier => {
                  const tierData = dashboard.tier_stats[tier] || { accounts: 0, tweets: 0 };
                  const totalTweets = dashboard.overview.total_tweets || 1;
                  const percentage = Math.round((tierData.tweets / totalTweets) * 100);
                  return (
                    <div key={tier} className="space-y-1">
                      <div className="flex justify-between text-sm">
                        <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${TIER_COLORS[tier]}`}>
                          {TIER_LABELS[tier]}
                        </span>
                        <span className="text-gray-600">
                          {tierData.accounts} accounts · {tierData.tweets.toLocaleString()} tweets
                        </span>
                      </div>
                      <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                        <div
                          className={`h-full ${tier === 1 ? 'bg-red-400' : tier === 2 ? 'bg-yellow-400' : 'bg-green-400'}`}
                          style={{ width: `${percentage}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Top Accounts */}
            <div className="bg-white p-4 rounded-lg border shadow-sm">
              <h3 className="font-semibold text-gray-900 mb-4">Top Accounts by Tweets</h3>
              <div className="space-y-2">
                {dashboard.top_accounts.slice(0, 8).map((acc, i) => (
                  <div key={acc.username} className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="text-xs text-gray-400 w-4">{i + 1}.</span>
                      <a
                        href={`https://x.com/${acc.username}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-blue-600 hover:underline"
                      >
                        @{acc.username}
                      </a>
                    </div>
                    <span className="text-sm text-gray-600">{acc.tweets.toLocaleString()}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Recent Activity */}
          <div className="bg-white p-4 rounded-lg border shadow-sm">
            <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <Activity className="w-5 h-5 text-purple-500" />
              Recent Collection Activity
            </h3>
            <div className="overflow-x-auto">
              <table className="min-w-full text-sm">
                <thead>
                  <tr className="text-left text-gray-500">
                    <th className="pb-2">Account</th>
                    <th className="pb-2">Last Run</th>
                    <th className="pb-2">Tweets</th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {dashboard.recent_activity.slice(0, 10).map((activity, i) => (
                    <tr key={i}>
                      <td className="py-2">@{activity.username}</td>
                      <td className="py-2 text-gray-500">{formatDate(activity.last_run)}</td>
                      <td className="py-2">
                        <span className={`px-2 py-0.5 rounded-full text-xs ${
                          activity.tweets_collected > 0 ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'
                        }`}>
                          {activity.tweets_collected}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Accounts Tab */}
      {activeTab === 'accounts' && (
        <>
          {/* Stats Cards */}
          {stats && (
            <div className="grid grid-cols-4 gap-4 mb-6">
              <div className="bg-white p-4 rounded-lg border shadow-sm">
                <div className="text-2xl font-bold text-gray-900">{stats.total_accounts}</div>
                <div className="text-sm text-gray-500">Total Accounts</div>
              </div>
              <div className="bg-white p-4 rounded-lg border shadow-sm">
                <div className="text-2xl font-bold text-green-600">{stats.enabled_accounts}</div>
                <div className="text-sm text-gray-500">Enabled</div>
              </div>
              <div className="bg-white p-4 rounded-lg border shadow-sm">
                <div className="text-2xl font-bold text-blue-600">{stats.total_tweets.toLocaleString()}</div>
                <div className="text-sm text-gray-500">Total Tweets</div>
              </div>
              <div className="bg-white p-4 rounded-lg border shadow-sm">
                <div className="text-2xl font-bold text-purple-600">
                  {accounts.filter(a => a.tier === 1).length}
                </div>
                <div className="text-sm text-gray-500">High Priority</div>
              </div>
            </div>
          )}

      {/* Filters */}
      <div className="flex items-center gap-4 mb-4">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
          <input
            type="text"
            placeholder="Search accounts..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <select
          value={filterTier ?? ''}
          onChange={(e) => setFilterTier(e.target.value ? Number(e.target.value) : null)}
          className="px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="">All Tiers</option>
          <option value="1">Tier 1 - High Priority</option>
          <option value="2">Tier 2 - Medium Priority</option>
          <option value="3">Tier 3 - Low Priority</option>
        </select>
        <select
          value={filterCategory ?? ''}
          onChange={(e) => setFilterCategory(e.target.value || null)}
          className="px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="">All Categories</option>
          {CATEGORIES.map(cat => (
            <option key={cat} value={cat}>{cat}</option>
          ))}
        </select>
      </div>

      {/* Accounts Table */}
      <div className="bg-white rounded-lg border shadow-sm overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <SortHeader field="status" label="Status" />
              <SortHeader field="username" label="Account" />
              <SortHeader field="category" label="Category" />
              <SortHeader field="tier" label="Tier" />
              <SortHeader field="tweets_collected" label="Total" />
              <SortHeader field="last_checked" label="Last Checked" />
              <SortHeader field="last_tweet" label="Latest Tweet" />
              <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {filteredAccounts.map((account) => (
              <tr key={account.id} className={!account.enabled ? 'bg-gray-50 opacity-60' : ''}>
                <td className="px-4 py-3">
                  <button
                    onClick={() => toggleAccount(account)}
                    className={`p-1 rounded ${account.enabled ? 'text-green-600' : 'text-gray-400'}`}
                    title={account.enabled ? 'Enabled - Click to disable' : 'Disabled - Click to enable'}
                  >
                    {account.enabled ? (
                      <ToggleRight className="w-6 h-6" />
                    ) : (
                      <ToggleLeft className="w-6 h-6" />
                    )}
                  </button>
                </td>
                <td className="px-4 py-3">
                  <div className="flex items-center gap-3">
                    {account.profile_image_url ? (
                      <img
                        src={account.profile_image_url}
                        alt={account.username}
                        className="w-10 h-10 rounded-full"
                      />
                    ) : (
                      <div className="w-10 h-10 rounded-full bg-gray-200 flex items-center justify-center">
                        <Users className="w-5 h-5 text-gray-500" />
                      </div>
                    )}
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-medium text-gray-900">@{account.username}</span>
                        {account.verified && (
                          <span className="text-blue-500" title="Verified">✓</span>
                        )}
                        <a
                          href={`https://x.com/${account.username}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-gray-400 hover:text-blue-500"
                        >
                          <ExternalLink className="w-4 h-4" />
                        </a>
                      </div>
                      <div className="text-sm text-gray-500">{account.display_name}</div>
                    </div>
                  </div>
                </td>
                <td className="px-4 py-3 text-sm text-gray-600">{account.category}</td>
                <td className="px-4 py-3">
                  <span className={`px-2 py-1 text-xs font-medium rounded-full ${TIER_COLORS[account.tier]}`}>
                    {TIER_LABELS[account.tier]}
                  </span>
                </td>
                <td className="px-4 py-3 text-sm text-gray-900 font-medium">
                  {account.tweets_collected.toLocaleString()}
                </td>
                <td className="px-4 py-3 text-sm">
                  {(() => {
                    const accountStats = stats?.accounts.find(a => a.id === account.id);
                    if (!accountStats) return <span className="text-gray-400">-</span>;

                    const { check_status, minutes_since_check, tweets_in_last_check, is_overdue, last_error: _last_error } = accountStats;

                    // Determine icon and color based on status
                    let StatusIcon = CircleDashed;
                    let statusColor = 'text-gray-400';

                    if (check_status === 'success') {
                      StatusIcon = CheckCircle;
                      statusColor = 'text-green-500';
                    } else if (check_status === 'no_new_tweets') {
                      StatusIcon = MinusCircle;
                      statusColor = is_overdue ? 'text-yellow-500' : 'text-blue-400';
                    } else if (check_status === 'error') {
                      StatusIcon = AlertCircle;
                      statusColor = 'text-red-500';
                    }

                    // Format time
                    let timeStr = 'Never';
                    if (minutes_since_check !== null) {
                      if (minutes_since_check < 60) {
                        timeStr = `${minutes_since_check}m ago`;
                      } else if (minutes_since_check < 1440) {
                        timeStr = `${Math.floor(minutes_since_check / 60)}h ago`;
                      } else {
                        timeStr = `${Math.floor(minutes_since_check / 1440)}d ago`;
                      }
                    }

                    return (
                      <div className="flex items-center gap-2">
                        <StatusIcon className={`w-4 h-4 ${statusColor}`} />
                        <div>
                          <div className={is_overdue ? 'text-yellow-600 font-medium' : 'text-gray-600'}>
                            {timeStr}
                          </div>
                          <div className="text-xs text-gray-400">
                            {tweets_in_last_check > 0 ? (
                              <span className="text-green-600">+{tweets_in_last_check} new</span>
                            ) : check_status === 'never_checked' ? (
                              'Not checked'
                            ) : (
                              '0 new'
                            )}
                          </div>
                        </div>
                      </div>
                    );
                  })()}
                </td>
                <td className="px-4 py-3 text-sm">
                  {(() => {
                    const accountStats = stats?.accounts.find(a => a.id === account.id);
                    if (!accountStats?.latest_tweet) return <span className="text-gray-400">No tweets</span>;

                    const daysAgo = accountStats.days_without_new_tweets;
                    let activityColor = 'text-gray-600';
                    let activityLabel = '';

                    if (daysAgo !== null) {
                      if (daysAgo === 0) {
                        activityColor = 'text-green-600';
                        activityLabel = 'Active';
                      } else if (daysAgo <= 7) {
                        activityColor = 'text-blue-600';
                        activityLabel = 'Recent';
                      } else {
                        activityColor = 'text-gray-500';
                        activityLabel = 'Quiet';
                      }
                    }

                    return (
                      <div>
                        <div className={activityColor}>
                          {formatDate(accountStats.latest_tweet)}
                        </div>
                        {activityLabel && (
                          <div className={`text-xs ${activityColor}`}>{activityLabel}</div>
                        )}
                      </div>
                    );
                  })()}
                </td>
                <td className="px-4 py-3">
                  <div className="flex items-center justify-end gap-1">
                    <button
                      onClick={() => collectTweets(account)}
                      disabled={collectingAccount === account.id || !account.enabled}
                      className={`p-1.5 rounded transition-colors ${
                        collectingAccount === account.id
                          ? 'bg-blue-100 text-blue-600'
                          : account.enabled
                          ? 'text-blue-500 hover:bg-blue-50 hover:text-blue-600'
                          : 'text-gray-300 cursor-not-allowed'
                      }`}
                      title={account.enabled ? "Collect tweets now" : "Enable account first"}
                    >
                      {collectingAccount === account.id ? (
                        <Loader2 className="w-4 h-4 animate-spin" />
                      ) : (
                        <Download className="w-4 h-4" />
                      )}
                    </button>
                    <button
                      onClick={() => refreshAccountInfo(account)}
                      className="p-1 text-gray-400 hover:text-blue-500 rounded"
                      title="Refresh from Twitter"
                    >
                      <RefreshCw className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => {
                        setEditingAccount(account);
                        setShowEditModal(true);
                      }}
                      className="p-1 text-gray-400 hover:text-blue-500 rounded"
                      title="Edit"
                    >
                      <Edit2 className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => deleteAccount(account)}
                      className="p-1 text-gray-400 hover:text-red-500 rounded"
                      title="Delete"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {filteredAccounts.length === 0 && (
          <div className="p-8 text-center text-gray-500">
            No accounts found matching your filters.
          </div>
        )}
      </div>
        </>
      )}

      {/* Add Account Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-md p-6">
            <h2 className="text-xl font-bold mb-4">Add Twitter Account</h2>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Username
                </label>
                <div className="flex gap-2">
                  <input
                    type="text"
                    placeholder="@username"
                    value={newAccountData.username}
                    onChange={(e) => setNewAccountData(d => ({ ...d, username: e.target.value }))}
                    className="flex-1 px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                  <button
                    onClick={lookupTwitterUser}
                    disabled={lookingUp || !newAccountData.username}
                    className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 disabled:opacity-50"
                  >
                    {lookingUp ? 'Looking up...' : 'Lookup'}
                  </button>
                </div>
              </div>

              {lookupResult && (
                <div className={`p-3 rounded-lg ${lookupResult.exists ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'}`}>
                  {lookupResult.exists && lookupResult.user ? (
                    <div className="flex items-center gap-3">
                      {lookupResult.user.profile_image_url && (
                        <img src={lookupResult.user.profile_image_url} alt="" className="w-12 h-12 rounded-full" />
                      )}
                      <div>
                        <div className="font-medium">@{lookupResult.user.username}</div>
                        <div className="text-sm text-gray-600">{lookupResult.user.name}</div>
                        <div className="text-xs text-gray-500">{lookupResult.user.followers_count?.toLocaleString()} followers</div>
                      </div>
                    </div>
                  ) : (
                    <div className="text-red-700">{lookupResult.error || 'User not found'}</div>
                  )}
                </div>
              )}

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Display Name (optional)
                </label>
                <input
                  type="text"
                  value={newAccountData.display_name}
                  onChange={(e) => setNewAccountData(d => ({ ...d, display_name: e.target.value }))}
                  placeholder="Will use Twitter name if empty"
                  className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Category
                </label>
                <select
                  value={newAccountData.category}
                  onChange={(e) => setNewAccountData(d => ({ ...d, category: e.target.value }))}
                  className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  {CATEGORIES.map(cat => (
                    <option key={cat} value={cat}>{cat}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Priority Tier
                </label>
                <select
                  value={newAccountData.tier}
                  onChange={(e) => setNewAccountData(d => ({ ...d, tier: Number(e.target.value) }))}
                  className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value={1}>Tier 1 - High Priority (check every 30 min)</option>
                  <option value={2}>Tier 2 - Medium Priority (check every 2 hours)</option>
                  <option value={3}>Tier 3 - Low Priority (check every 6 hours)</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Description (optional)
                </label>
                <textarea
                  value={newAccountData.description}
                  onChange={(e) => setNewAccountData(d => ({ ...d, description: e.target.value }))}
                  placeholder="Brief description of this account"
                  rows={2}
                  className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="enabled"
                  checked={newAccountData.enabled}
                  onChange={(e) => setNewAccountData(d => ({ ...d, enabled: e.target.checked }))}
                  className="w-4 h-4"
                />
                <label htmlFor="enabled" className="text-sm text-gray-700">
                  Enable collection for this account
                </label>
              </div>
            </div>

            <div className="flex justify-end gap-2 mt-6">
              <button
                onClick={() => {
                  setShowAddModal(false);
                  setLookupResult(null);
                  setNewAccountData({
                    username: '',
                    display_name: '',
                    category: 'Other',
                    description: '',
                    tier: 2,
                    enabled: true
                  });
                }}
                className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg"
              >
                Cancel
              </button>
              <button
                onClick={addAccount}
                disabled={submitting || !newAccountData.username}
                className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50"
              >
                {submitting ? 'Adding...' : 'Add Account'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Edit Account Modal */}
      {showEditModal && editingAccount && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-md p-6">
            <h2 className="text-xl font-bold mb-4">Edit @{editingAccount.username}</h2>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Display Name
                </label>
                <input
                  type="text"
                  value={editingAccount.display_name}
                  onChange={(e) => setEditingAccount(a => a ? { ...a, display_name: e.target.value } : null)}
                  className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Category
                </label>
                <select
                  value={editingAccount.category}
                  onChange={(e) => setEditingAccount(a => a ? { ...a, category: e.target.value } : null)}
                  className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  {CATEGORIES.map(cat => (
                    <option key={cat} value={cat}>{cat}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Priority Tier
                </label>
                <select
                  value={editingAccount.tier}
                  onChange={(e) => setEditingAccount(a => a ? { ...a, tier: Number(e.target.value) } : null)}
                  className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value={1}>Tier 1 - High Priority</option>
                  <option value={2}>Tier 2 - Medium Priority</option>
                  <option value={3}>Tier 3 - Low Priority</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Description
                </label>
                <textarea
                  value={editingAccount.description || ''}
                  onChange={(e) => setEditingAccount(a => a ? { ...a, description: e.target.value } : null)}
                  rows={2}
                  className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="edit-enabled"
                  checked={editingAccount.enabled}
                  onChange={(e) => setEditingAccount(a => a ? { ...a, enabled: e.target.checked } : null)}
                  className="w-4 h-4"
                />
                <label htmlFor="edit-enabled" className="text-sm text-gray-700">
                  Enable collection for this account
                </label>
              </div>
            </div>

            <div className="flex justify-end gap-2 mt-6">
              <button
                onClick={() => {
                  setShowEditModal(false);
                  setEditingAccount(null);
                }}
                className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg"
              >
                Cancel
              </button>
              <button
                onClick={updateAccount}
                disabled={submitting}
                className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50"
              >
                {submitting ? 'Saving...' : 'Save Changes'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
