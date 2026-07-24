import { useState, useEffect, useCallback } from 'react';
import { Plus, RefreshCw, Users, BarChart3, CheckCircle, XCircle } from 'lucide-react';
import axios from 'axios';
import { AccountFormModal } from '../TwitterAccountManager/AccountFormModal';
import { CollectionDashboard } from './CollectionDashboard';
import { AccountListTable } from './AccountListTable';
import type {
  TwitterAccount,
  AccountStats,
  DashboardData,
  CollectionHistory,
  CollectorStatus,
  UsageStats,
  LiveProgress,
  AddAccountData,
  TwitterUserLookup,
} from './types';

// Re-export types for backward compatibility
export type {
  TwitterAccount,
  AccountStats,
  DashboardData,
  CollectionHistory,
  CollectorStatus,
  UsageStats,
  LiveProgress,
} from './types';


const API_BASE = `/api/twitter-accounts`;

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

  const fetchCollectorStatus = useCallback(async () => {
    try {
      const res = await axios.get<CollectorStatus>(`${API_BASE}/collector-status`);
      setCollectorStatus(res.data);
    } catch (err) {
      console.error('Failed to fetch collector status:', err);
    }
  }, []);

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

  useEffect(() => {
    if (activeTab !== 'dashboard') return;

    const interval = setInterval(fetchCollectorStatus, 10000);
    return () => clearInterval(interval);
  }, [activeTab, fetchCollectorStatus]);

  useEffect(() => {
    if (activeTab !== 'dashboard') return;
    if (!collectorStatus?.collector_running) return;

    fetchLiveProgress();

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

  const getAccountStats = (accountId: string) => stats?.accounts.find(s => s.id === accountId);

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
        const statusOrder = { 'success': 0, 'no_new_tweets': 1, 'error': 2, 'never_checked': 3 };
        const statusA = statsA?.check_status || 'never_checked';
        const statusB = statsB?.check_status || 'never_checked';
        comparison = statusOrder[statusA] - statusOrder[statusB];
      } else if (sortField === 'last_checked') {
        const minsA = statsA?.minutes_since_check ?? 999999;
        const minsB = statsB?.minutes_since_check ?? 999999;
        comparison = minsA - minsB;
      } else if (sortField === 'last_tweet') {
        const dateA = statsA?.latest_tweet ? new Date(statsA.latest_tweet).getTime() : 0;
        const dateB = statsB?.latest_tweet ? new Date(statsB.latest_tweet).getTime() : 0;
        comparison = dateB - dateA;
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

  const handleSortChange = (field: typeof sortField) => {
    if (sortField === field) {
      setSortDirection(d => d === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('asc');
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="w-8 h-8 animate-spin text-blue-500" />
      </div>
    );
  }

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
        <CollectionDashboard
          dashboard={dashboard}
          history={history}
          collectorStatus={collectorStatus}
          usageStats={usageStats}
          liveProgress={liveProgress}
          onRefreshCollectorStatus={fetchCollectorStatus}
          formatDate={formatDate}
        />
      )}

      {/* Accounts Tab */}
      {activeTab === 'accounts' && (
        <AccountListTable
          accounts={accounts}
          stats={stats}
          filteredAccounts={filteredAccounts}
          searchTerm={searchTerm}
          onSearchTermChange={setSearchTerm}
          filterTier={filterTier}
          onFilterTierChange={setFilterTier}
          filterCategory={filterCategory}
          onFilterCategoryChange={setFilterCategory}
          sortField={sortField}
          sortDirection={sortDirection}
          onSortChange={handleSortChange}
          collectingAccount={collectingAccount}
          onToggleAccount={toggleAccount}
          onCollectTweets={collectTweets}
          onRefreshAccountInfo={refreshAccountInfo}
          onEditAccount={(account) => {
            setEditingAccount(account);
            setShowEditModal(true);
          }}
          onDeleteAccount={deleteAccount}
          formatDate={formatDate}
        />
      )}

      {/* Add Account Modal */}
      {showAddModal && (
        <AccountFormModal
          mode="add"
          data={newAccountData}
          onChange={(updater) => setNewAccountData(updater)}
          onSubmit={addAccount}
          onCancel={() => {
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
          submitting={submitting}
          onLookup={lookupTwitterUser}
          lookingUp={lookingUp}
          lookupResult={lookupResult}
        />
      )}

      {/* Edit Account Modal */}
      {showEditModal && editingAccount && (
        <AccountFormModal
          mode="edit"
          editUsername={editingAccount.username}
          data={{
            username: editingAccount.username,
            display_name: editingAccount.display_name,
            category: editingAccount.category,
            description: editingAccount.description || '',
            tier: editingAccount.tier,
            enabled: editingAccount.enabled,
          }}
          onChange={(updater) => {
            setEditingAccount(a => {
              if (!a) return null;
              const formData = {
                username: a.username,
                display_name: a.display_name,
                category: a.category,
                description: a.description || '',
                tier: a.tier,
                enabled: a.enabled,
              };
              const updated = updater(formData);
              return { ...a, ...updated };
            });
          }}
          onSubmit={updateAccount}
          onCancel={() => {
            setShowEditModal(false);
            setEditingAccount(null);
          }}
          submitting={submitting}
        />
      )}
    </div>
  );
}
