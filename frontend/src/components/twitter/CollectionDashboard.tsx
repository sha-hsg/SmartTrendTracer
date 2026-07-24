import { Users, Activity, Clock, TrendingUp, BarChart3, Calendar } from 'lucide-react';
import { CollectorStatusCard } from '../TwitterAccountManager/CollectorStatusCard';
import type { DashboardData, CollectionHistory, CollectorStatus, UsageStats, LiveProgress } from './types';

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

interface CollectionDashboardProps {
  dashboard: DashboardData;
  history: CollectionHistory | null;
  collectorStatus: CollectorStatus | null;
  usageStats: UsageStats | null;
  liveProgress: LiveProgress | null;
  onRefreshCollectorStatus: () => void;
  formatDate: (dateStr: string | null) => string;
}

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

export function CollectionDashboard({
  dashboard,
  history,
  collectorStatus,
  usageStats,
  liveProgress,
  onRefreshCollectorStatus,
  formatDate,
}: CollectionDashboardProps) {
  return (
    <div className="space-y-6">
      {/* Live Collector Status */}
      {collectorStatus && (
        <CollectorStatusCard
          collectorStatus={collectorStatus}
          liveProgress={liveProgress}
          onRefresh={onRefreshCollectorStatus}
        />
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
  );
}
