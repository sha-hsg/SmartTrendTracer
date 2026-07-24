export interface TwitterAccount {
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

export interface AccountStats {
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

export interface DashboardData {
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

export interface CollectionHistory {
  period_days: number;
  start_date: string;
  end_date: string;
  total_tweets: number;
  daily_history: Array<{ date: string; tweets: number }>;
  by_account: Array<{ username: string; tweets: number }>;
}

export interface CollectorStatus {
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

export interface UsageStats {
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

export interface LiveProgress {
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

export interface AddAccountData {
  username: string;
  display_name: string;
  category: string;
  description: string;
  tier: number;
  enabled: boolean;
}

export interface TwitterUserLookup {
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
