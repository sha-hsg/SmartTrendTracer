import {
  Zap,
  XCircle,
  RefreshCw,
  Loader2,
  Clock,
  CheckCircle,
  MinusCircle,
  AlertCircle,
  AlertTriangle,
} from 'lucide-react'

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

interface LiveProgress {
  status: 'collecting' | 'sleeping' | 'rate_limited' | 'error' | 'stopped' | 'unknown';
  current_account: string | null;
  accounts_processed: number;
  total_accounts: number;
  progress_percent: number;
  tweets_this_cycle: number;
  current_batch: number;
  total_batches: number;
  seconds_until_next_cycle: number | null;
  is_stale: boolean;
}

interface CollectorStatusCardProps {
  collectorStatus: CollectorStatus;
  liveProgress: LiveProgress | null;
  onRefresh: () => void;
}

export function CollectorStatusCard({ collectorStatus, liveProgress, onRefresh }: CollectorStatusCardProps) {
  return (
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
            onClick={onRefresh}
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
          </div>
        </div>
      )}
    </div>
  )
}
