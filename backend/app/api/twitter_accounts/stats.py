from fastapi import APIRouter, Depends, Query
from datetime import datetime, timezone
from bson import ObjectId

from app.database.mongodb import get_database

router = APIRouter()

# Tier collection intervals (in minutes)
TIER_INTERVALS = {
    1: 30,    # High priority: every 30 minutes
    2: 120,   # Medium priority: every 2 hours
    3: 360,   # Low priority: every 6 hours
}


@router.get("/stats")
def get_account_stats(db=Depends(get_database)):
    """Get collection statistics per account."""
    from datetime import timedelta

    now = datetime.now(timezone.utc)

    # Tier intervals in minutes
    tier_intervals = {1: 30, 2: 120, 3: 360}

    # Get account info
    accounts = list(db.twitter_accounts.find())

    stats = []
    for account in accounts:
        username = account.get('username')
        tier = account.get('tier', 2)

        # Count tweets for this account
        tweet_count = db.tweets.count_documents({'author_username': username})

        # Get latest tweet
        latest_tweet = db.tweets.find_one(
            {'author_username': username},
            sort=[('created_at', -1)]
        )

        # Get oldest tweet
        oldest_tweet = db.tweets.find_one(
            {'author_username': username},
            sort=[('created_at', 1)]
        )

        # Get collection state for this account
        collection_state = db.collection_state.find_one({'key': f'twitter_{username}'})

        # Calculate check status and timing
        last_run = collection_state.get('last_run') if collection_state else None
        if last_run and last_run.tzinfo is None:
            last_run = last_run.replace(tzinfo=timezone.utc)

        tweets_in_check = collection_state.get('tweets_collected', 0) if collection_state else 0
        last_error = collection_state.get('last_error') if collection_state else None
        error_count = collection_state.get('error_count', 0) if collection_state else 0

        # Determine check status
        if not collection_state:
            check_status = 'never_checked'
        elif last_error:
            check_status = 'error'
        elif tweets_in_check > 0:
            check_status = 'success'
        else:
            check_status = 'no_new_tweets'

        # Calculate if overdue
        is_overdue = False
        minutes_since_check = None
        minutes_until_next = None
        if last_run:
            delta = now - last_run
            minutes_since_check = int(delta.total_seconds() / 60)
            interval = tier_intervals.get(tier, 120)
            minutes_until_next = interval - minutes_since_check
            is_overdue = minutes_until_next < 0

        # Calculate days without new tweets
        days_without_new_tweets = None
        if latest_tweet and latest_tweet.get('created_at'):
            tweet_time = latest_tweet['created_at']
            if tweet_time.tzinfo is None:
                tweet_time = tweet_time.replace(tzinfo=timezone.utc)
            days_without_new_tweets = (now - tweet_time).days

        stats.append({
            'id': str(account['_id']),
            'username': username,
            'display_name': account.get('display_name', username),
            'tier': tier,
            'enabled': account.get('enabled', True),
            'category': account.get('category', 'Other'),
            'tweets_collected': tweet_count,
            # Tweet timing (when tweets were POSTED on Twitter)
            'latest_tweet': latest_tweet['created_at'].isoformat() if latest_tweet and latest_tweet.get('created_at') else None,
            'oldest_tweet': oldest_tweet['created_at'].isoformat() if oldest_tweet and oldest_tweet.get('created_at') else None,
            'days_without_new_tweets': days_without_new_tweets,
            # Collection timing (when WE CHECKED this account)
            'last_checked_at': last_run.isoformat() if last_run else None,
            'minutes_since_check': minutes_since_check,
            'minutes_until_next': minutes_until_next,
            'is_overdue': is_overdue,
            # Check result
            'tweets_in_last_check': tweets_in_check,
            'check_status': check_status,  # 'success' | 'no_new_tweets' | 'error' | 'never_checked'
            'last_error': last_error,
            'error_count': error_count,
            # Legacy field for compatibility
            'last_collection_run': last_run.isoformat() if last_run else None,
            'tweets_in_last_collection': tweets_in_check,
        })

    # Sort by tweet count descending
    stats.sort(key=lambda x: x['tweets_collected'], reverse=True)

    # Calculate summary stats
    accounts_with_new_tweets = sum(1 for s in stats if s['tweets_in_last_check'] > 0)
    accounts_without_new_tweets = sum(1 for s in stats if s['check_status'] == 'no_new_tweets')
    accounts_with_errors = sum(1 for s in stats if s['check_status'] == 'error')
    accounts_never_checked = sum(1 for s in stats if s['check_status'] == 'never_checked')
    accounts_overdue = sum(1 for s in stats if s['is_overdue'] and s['enabled'])

    return {
        'accounts': stats,
        'total_accounts': len(stats),
        'enabled_accounts': sum(1 for s in stats if s['enabled']),
        'total_tweets': sum(s['tweets_collected'] for s in stats),
        # New summary fields
        'accounts_with_new_tweets': accounts_with_new_tweets,
        'accounts_without_new_tweets': accounts_without_new_tweets,
        'accounts_with_errors': accounts_with_errors,
        'accounts_never_checked': accounts_never_checked,
        'accounts_overdue': accounts_overdue,
    }


@router.get("/dashboard")
def get_collection_dashboard(db=Depends(get_database)):
    """Get comprehensive collection dashboard statistics."""
    from datetime import timedelta

    now = datetime.now(timezone.utc)

    # Get all accounts
    accounts = list(db.twitter_accounts.find())
    total_accounts = len(accounts)
    enabled_accounts = sum(1 for a in accounts if a.get('enabled', True))

    # Get total tweets
    total_tweets = db.tweets.count_documents({})

    # Get tweets by time period
    tweets_24h = db.tweets.count_documents({
        'created_at': {'$gte': now - timedelta(hours=24)}
    })
    tweets_7d = db.tweets.count_documents({
        'created_at': {'$gte': now - timedelta(days=7)}
    })
    tweets_30d = db.tweets.count_documents({
        'created_at': {'$gte': now - timedelta(days=30)}
    })

    # Get collection state info
    collection_states = list(db.collection_state.find({'key': {'$regex': '^twitter_'}}))

    # Find most recent collection
    last_collection = None
    last_collection_account = None
    total_tweets_last_run = 0

    for state in collection_states:
        if state.get('last_run'):
            if not last_collection or state['last_run'] > last_collection:
                last_collection = state['last_run']
                last_collection_account = state['key'].replace('twitter_', '')
            total_tweets_last_run += state.get('tweets_collected', 0)

    # Get tweets per tier
    tier_stats = {}
    for tier in [1, 2, 3]:
        tier_accounts = [a.get('username') for a in accounts if a.get('tier') == tier]
        tier_tweets = db.tweets.count_documents({'author_username': {'$in': tier_accounts}}) if tier_accounts else 0
        tier_stats[tier] = {
            'accounts': len(tier_accounts),
            'tweets': tier_tweets
        }

    # Get tweets per category
    category_stats = {}
    for account in accounts:
        cat = account.get('category', 'Other')
        if cat not in category_stats:
            category_stats[cat] = {'accounts': 0, 'tweets': 0}
        category_stats[cat]['accounts'] += 1

    # Count tweets per category
    for cat in category_stats:
        cat_accounts = [a.get('username') for a in accounts if a.get('category') == cat]
        category_stats[cat]['tweets'] = db.tweets.count_documents({'author_username': {'$in': cat_accounts}}) if cat_accounts else 0

    # Get most active accounts (by total tweets)
    top_accounts = list(db.tweets.aggregate([
        {'$group': {'_id': '$author_username', 'count': {'$sum': 1}}},
        {'$sort': {'count': -1}},
        {'$limit': 10}
    ]))

    # Get recent collection activity (last 7 collection runs per account)
    recent_activity = []
    for state in sorted(collection_states, key=lambda x: x.get('last_run') or datetime.min.replace(tzinfo=timezone.utc), reverse=True)[:20]:
        if state.get('last_run'):
            recent_activity.append({
                'username': state['key'].replace('twitter_', ''),
                'last_run': state['last_run'].isoformat(),
                'tweets_collected': state.get('tweets_collected', 0),
                'last_tweet_id': state.get('last_tweet_id')
            })

    # Calculate average tweets per day over last 30 days
    avg_tweets_per_day = round(tweets_30d / 30, 1) if tweets_30d else 0

    # Calculate next collection times per tier
    next_collections = {}
    for tier in [1, 2, 3]:
        tier_accounts = [a for a in accounts if a.get('tier') == tier and a.get('enabled', True)]
        if not tier_accounts:
            next_collections[tier] = {'next_run': None, 'accounts': []}
            continue

        # Find the account(s) due for collection soonest
        tier_next = []
        for acc in tier_accounts:
            username = acc.get('username')
            state = db.collection_state.find_one({'key': f'twitter_{username}'})
            last_run = state.get('last_run') if state else None

            if last_run:
                # Make sure last_run is timezone-aware
                if last_run.tzinfo is None:
                    last_run = last_run.replace(tzinfo=timezone.utc)
                next_run = last_run + timedelta(minutes=TIER_INTERVALS[tier])
            else:
                next_run = now  # Never collected, due now

            tier_next.append({
                'username': username,
                'last_run': last_run.isoformat() if last_run else None,
                'next_run': next_run.isoformat(),
                'is_overdue': next_run <= now
            })

        # Sort by next_run
        tier_next.sort(key=lambda x: x['next_run'])
        soonest = tier_next[0] if tier_next else None

        next_collections[tier] = {
            'interval_minutes': TIER_INTERVALS[tier],
            'next_run': soonest['next_run'] if soonest else None,
            'is_overdue': soonest['is_overdue'] if soonest else False,
            'accounts_due': [a for a in tier_next if a['is_overdue']],
            'accounts': tier_next[:5]  # Show top 5 per tier
        }

    return {
        'overview': {
            'total_accounts': total_accounts,
            'enabled_accounts': enabled_accounts,
            'disabled_accounts': total_accounts - enabled_accounts,
            'total_tweets': total_tweets,
            'tweets_24h': tweets_24h,
            'tweets_7d': tweets_7d,
            'tweets_30d': tweets_30d,
            'avg_tweets_per_day': avg_tweets_per_day,
        },
        'last_collection': {
            'timestamp': last_collection.isoformat() if last_collection else None,
            'account': last_collection_account,
            'total_tweets_collected': total_tweets_last_run,
        },
        'next_collections': next_collections,
        'tier_stats': tier_stats,
        'category_stats': category_stats,
        'top_accounts': [
            {'username': a['_id'], 'tweets': a['count']}
            for a in top_accounts
        ],
        'recent_activity': recent_activity,
    }


@router.get("/collection-history")
def get_collection_history(
    days: int = Query(7, ge=1, le=90, description="Number of days to look back"),
    db=Depends(get_database)
):
    """Get tweet collection history over time."""
    from datetime import timedelta

    now = datetime.now(timezone.utc)
    start_date = now - timedelta(days=days)

    # Aggregate tweets by collection day (collected_at, not tweet post date)
    pipeline = [
        {'$match': {'collected_at': {'$gte': start_date}}},
        {'$group': {
            '_id': {
                'year': {'$year': '$collected_at'},
                'month': {'$month': '$collected_at'},
                'day': {'$dayOfMonth': '$collected_at'}
            },
            'count': {'$sum': 1}
        }},
        {'$sort': {'_id.year': 1, '_id.month': 1, '_id.day': 1}}
    ]

    daily_counts = list(db.tweets.aggregate(pipeline))

    # Format results
    history = []
    for item in daily_counts:
        date_str = f"{item['_id']['year']}-{item['_id']['month']:02d}-{item['_id']['day']:02d}"
        history.append({
            'date': date_str,
            'tweets': item['count']
        })

    # Aggregate by account over the period (by collection date)
    account_pipeline = [
        {'$match': {'collected_at': {'$gte': start_date}}},
        {'$group': {
            '_id': '$author_username',
            'count': {'$sum': 1}
        }},
        {'$sort': {'count': -1}}
    ]

    account_counts = list(db.tweets.aggregate(account_pipeline))

    return {
        'period_days': days,
        'start_date': start_date.isoformat(),
        'end_date': now.isoformat(),
        'total_tweets': sum(h['tweets'] for h in history),
        'daily_history': history,
        'by_account': [
            {'username': a['_id'], 'tweets': a['count']}
            for a in account_counts
        ]
    }


@router.get("/collector-status")
def get_collector_status(db=Depends(get_database)):
    """Get the current status of the tweet collector service."""
    import subprocess
    from datetime import timedelta

    now = datetime.now(timezone.utc)

    # Check if collector process is running
    try:
        result = subprocess.run(
            ['pgrep', '-f', 'tweet_collector'],
            capture_output=True,
            text=True,
            timeout=5
        )
        is_running = result.returncode == 0
        pid = result.stdout.strip().split('\n')[0] if is_running else None
    except Exception:
        is_running = False
        pid = None

    # Get collection state summary
    collection_states = list(db.collection_state.find({'key': {'$regex': '^twitter_'}}))

    # Calculate overdue accounts per tier
    accounts = list(db.twitter_accounts.find({'enabled': True}))
    overdue_by_tier = {1: [], 2: [], 3: []}

    for acc in accounts:
        tier = acc.get('tier', 2)
        username = acc.get('username')
        state = db.collection_state.find_one({'key': f'twitter_{username}'})
        last_run = state.get('last_run') if state else None

        if last_run:
            if last_run.tzinfo is None:
                last_run = last_run.replace(tzinfo=timezone.utc)
            next_run = last_run + timedelta(minutes=TIER_INTERVALS[tier])
            if next_run <= now:
                minutes_overdue = int((now - next_run).total_seconds() / 60)
                overdue_by_tier[tier].append({
                    'username': username,
                    'minutes_overdue': minutes_overdue
                })
        else:
            overdue_by_tier[tier].append({
                'username': username,
                'minutes_overdue': None  # Never collected
            })

    # Find most recent collection
    last_collection = None
    last_account = None
    for state in collection_states:
        if state.get('last_run'):
            if not last_collection or state['last_run'] > last_collection:
                last_collection = state['last_run']
                last_account = state['key'].replace('twitter_', '')

    # Calculate time since last collection
    time_since_last = None
    if last_collection:
        if last_collection.tzinfo is None:
            last_collection = last_collection.replace(tzinfo=timezone.utc)
        delta = now - last_collection
        time_since_last = {
            'minutes': int(delta.total_seconds() / 60),
            'hours': round(delta.total_seconds() / 3600, 1)
        }

    # Calculate accounts with/without new tweets in last check
    accounts_with_new_tweets = 0
    accounts_without_new_tweets = 0
    accounts_never_checked = 0
    accounts_with_errors = 0
    total_tweets_last_cycle = 0

    for acc in accounts:
        username = acc.get('username')
        state = db.collection_state.find_one({'key': f'twitter_{username}'})

        if not state or not state.get('last_run'):
            accounts_never_checked += 1
        elif state.get('last_error'):
            accounts_with_errors += 1
        else:
            tweets_in_check = state.get('tweets_collected', 0)
            if tweets_in_check > 0:
                accounts_with_new_tweets += 1
                total_tweets_last_cycle += tweets_in_check
            else:
                accounts_without_new_tweets += 1

    return {
        'collector_running': is_running,
        'collector_pid': pid,
        'last_collection': {
            'timestamp': last_collection.isoformat() if last_collection else None,
            'account': last_account,
            'time_ago': time_since_last
        },
        'cycle_summary': {
            'accounts_checked': len(accounts),
            'accounts_with_new_tweets': accounts_with_new_tweets,
            'accounts_without_new_tweets': accounts_without_new_tweets,
            'accounts_never_checked': accounts_never_checked,
            'accounts_with_errors': accounts_with_errors,
            'total_tweets_collected': total_tweets_last_cycle
        },
        'overdue_accounts': {
            'tier_1': overdue_by_tier[1],
            'tier_2': overdue_by_tier[2],
            'tier_3': overdue_by_tier[3],
            'total': len(overdue_by_tier[1]) + len(overdue_by_tier[2]) + len(overdue_by_tier[3])
        },
        'schedule': {
            'tier_1_interval': '30 minutes',
            'tier_2_interval': '2 hours',
            'tier_3_interval': '6 hours'
        }
    }


@router.get("/live-progress")
def get_live_collection_progress(db=Depends(get_database)):
    """
    Get real-time collection progress from the collector service.
    Returns current status, which account is being processed, and progress metrics.
    """
    from datetime import timezone

    now = datetime.now(timezone.utc)

    # Get live progress document
    progress = db.collector_live_status.find_one({'_id': 'current'})

    if not progress:
        return {
            'status': 'unknown',
            'message': 'No progress data available. Collector may not have run yet.',
            'is_stale': True
        }

    # Check if data is stale (more than 2 minutes old)
    updated_at = progress.get('updated_at')
    is_stale = False
    seconds_since_update = None

    if updated_at:
        if updated_at.tzinfo is None:
            updated_at = updated_at.replace(tzinfo=timezone.utc)
        seconds_since_update = int((now - updated_at).total_seconds())
        is_stale = seconds_since_update > 120  # Stale if not updated in 2 minutes

    # Recalculate seconds until next cycle
    next_cycle_at = progress.get('next_cycle_at')
    seconds_until_next = None
    if next_cycle_at and progress.get('status') == 'sleeping':
        if next_cycle_at.tzinfo is None:
            next_cycle_at = next_cycle_at.replace(tzinfo=timezone.utc)
        seconds_until_next = max(0, int((next_cycle_at - now).total_seconds()))

    return {
        'status': progress.get('status', 'unknown'),
        'current_account': progress.get('current_account'),
        'accounts_processed': progress.get('accounts_processed', 0),
        'total_accounts': progress.get('total_accounts', 0),
        'progress_percent': progress.get('progress_percent', 0),
        'tweets_this_cycle': progress.get('tweets_this_cycle', 0),
        'current_batch': progress.get('current_batch', 0),
        'total_batches': progress.get('total_batches', 0),
        'cycle_start_time': progress.get('cycle_start_time').isoformat() if progress.get('cycle_start_time') else None,
        'next_cycle_at': next_cycle_at.isoformat() if next_cycle_at else None,
        'seconds_until_next_cycle': seconds_until_next,
        'error_message': progress.get('error_message'),
        'updated_at': updated_at.isoformat() if updated_at else None,
        'seconds_since_update': seconds_since_update,
        'is_stale': is_stale,
        'pid': progress.get('pid')
    }


@router.get("/usage")
def get_usage_stats(db=Depends(get_database)):
    """Get Twitter API usage statistics for the current month."""
    from datetime import timedelta

    now = datetime.now(timezone.utc)

    # Monthly stats
    month_start = datetime(now.year, now.month, 1, tzinfo=timezone.utc)
    monthly_count = db.tweets.count_documents({'collected_at': {'$gte': month_start}})

    # Days in month
    if now.month == 12:
        next_month = datetime(now.year + 1, 1, 1, tzinfo=timezone.utc)
    else:
        next_month = datetime(now.year, now.month + 1, 1, tzinfo=timezone.utc)
    days_in_month = (next_month - month_start).days
    days_elapsed = now.day
    days_remaining = days_in_month - days_elapsed

    # Basic account limit
    monthly_limit = 10000
    remaining = monthly_limit - monthly_count
    usage_percentage = (monthly_count / monthly_limit) * 100

    # Daily stats
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    daily_count = db.tweets.count_documents({'collected_at': {'$gte': today_start}})

    # Suggested daily budget
    suggested_daily = remaining // max(days_remaining, 1) if remaining > 0 else 0

    # Weekly stats
    week_start = now - timedelta(days=7)
    weekly_count = db.tweets.count_documents({'collected_at': {'$gte': week_start}})
    avg_daily = weekly_count / 7

    return {
        'monthly': {
            'collected': monthly_count,
            'limit': monthly_limit,
            'remaining': remaining,
            'usage_percentage': round(usage_percentage, 1),
            'days_elapsed': days_elapsed,
            'days_remaining': days_remaining,
        },
        'daily': {
            'collected': daily_count,
            'suggested_budget': suggested_daily,
            'avg_last_7_days': round(avg_daily, 1),
        },
        'status': 'ok' if usage_percentage < 80 else 'warning' if usage_percentage < 95 else 'critical'
    }
