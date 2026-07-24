import { Search, Users, ToggleLeft, ToggleRight, Trash2, Edit2, ChevronDown, ChevronUp, ExternalLink, RefreshCw, Download, Loader2, MinusCircle, AlertCircle, CheckCircle, CircleDashed } from 'lucide-react';
import type { TwitterAccount, AccountStats } from './types';

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

type SortField = 'username' | 'tier' | 'tweets_collected' | 'category' | 'status' | 'last_checked' | 'last_tweet';

interface AccountListTableProps {
  accounts: TwitterAccount[];
  stats: AccountStats | null;
  filteredAccounts: TwitterAccount[];
  searchTerm: string;
  onSearchTermChange: (value: string) => void;
  filterTier: number | null;
  onFilterTierChange: (value: number | null) => void;
  filterCategory: string | null;
  onFilterCategoryChange: (value: string | null) => void;
  sortField: SortField;
  sortDirection: 'asc' | 'desc';
  onSortChange: (field: SortField) => void;
  collectingAccount: string | null;
  onToggleAccount: (account: TwitterAccount) => void;
  onCollectTweets: (account: TwitterAccount) => void;
  onRefreshAccountInfo: (account: TwitterAccount) => void;
  onEditAccount: (account: TwitterAccount) => void;
  onDeleteAccount: (account: TwitterAccount) => void;
  formatDate: (dateStr: string | null) => string;
}

export function AccountListTable({
  accounts,
  stats,
  filteredAccounts,
  searchTerm,
  onSearchTermChange,
  filterTier,
  onFilterTierChange,
  filterCategory,
  onFilterCategoryChange,
  sortField,
  sortDirection,
  onSortChange,
  collectingAccount,
  onToggleAccount,
  onCollectTweets,
  onRefreshAccountInfo,
  onEditAccount,
  onDeleteAccount,
  formatDate,
}: AccountListTableProps) {
  const SortHeader = ({ field, label }: { field: SortField; label: string }) => (
    <th
      className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
      onClick={() => onSortChange(field)}
    >
      <div className="flex items-center gap-1">
        {label}
        {sortField === field && (
          sortDirection === 'asc' ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />
        )}
      </div>
    </th>
  );

  return (
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
            onChange={(e) => onSearchTermChange(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <select
          value={filterTier ?? ''}
          onChange={(e) => onFilterTierChange(e.target.value ? Number(e.target.value) : null)}
          className="px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="">All Tiers</option>
          <option value="1">Tier 1 - High Priority</option>
          <option value="2">Tier 2 - Medium Priority</option>
          <option value="3">Tier 3 - Low Priority</option>
        </select>
        <select
          value={filterCategory ?? ''}
          onChange={(e) => onFilterCategoryChange(e.target.value || null)}
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
                    onClick={() => onToggleAccount(account)}
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
                      onClick={() => onCollectTweets(account)}
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
                      onClick={() => onRefreshAccountInfo(account)}
                      className="p-1 text-gray-400 hover:text-blue-500 rounded"
                      title="Refresh from Twitter"
                    >
                      <RefreshCw className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => onEditAccount(account)}
                      className="p-1 text-gray-400 hover:text-blue-500 rounded"
                      title="Edit"
                    >
                      <Edit2 className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => onDeleteAccount(account)}
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
  );
}
