# Twitter Basic Account API Strategy

## Account Type: Basic (Pay-as-you-go)
- **Monthly Cost**: $100
- **Tweet Reading**: 10,000 tweets per month
- **API Version**: v2

## Rate Limits Overview

### Critical Limits for SmartTrendTracer
| Endpoint | Limit | Window | Impact |
|----------|-------|--------|--------|
| User Timeline (get_users_tweets) | **15 requests** | 15 min | Primary constraint |
| Tweet Lookup | 15 requests | 15 min | Secondary endpoint |
| User Lookup | 100 requests | 24 hours | User verification |
| Search Recent | 60 requests | 15 min | Alternative collection |

## Current Collection Setup
- **Accounts Monitored**: 15 AI influencers
- **Collection Interval**: 30 minutes (1800 seconds)
- **Batch Size**: 3 accounts per batch
- **Pages per Account**: Max 5 (100 tweets/page)

## The Problem
With 15 accounts and only 15 requests per 15-minute window for user timelines, we can only query **ONE account per minute** without hitting rate limits. This creates a fundamental mismatch with our 30-minute collection cycle.

## Optimized Collection Strategy

### 1. **Staggered Collection Cycles**
Instead of trying to collect all accounts every 30 minutes, implement account prioritization:

```python
# Priority tiers based on posting frequency
TIER_1_ACCOUNTS = [  # Check every 30 minutes (high activity)
    "OpenAI",        # Major announcements
    "AnthropicAI",   # Product updates
    "sama",          # CEO insights
    "emollick"       # Daily poster
]

TIER_2_ACCOUNTS = [  # Check every 2 hours (moderate activity)
    "huggingface",   # Regular updates
    "GoogleDeepMind",
    "stanfordnlp",
    "hwchase17",
    "kaggle"
]

TIER_3_ACCOUNTS = [  # Check every 6 hours (lower activity)
    "rasbt",
    "JayAlammar", 
    "Yoavgo",
    "Shayneredford",
    "Sebastienbubeck"
]
```

### 2. **Smart Request Distribution**
```
15-minute window = 15 requests available
- Use 12 requests for timeline fetching (buffer of 3)
- 1 request per account (most accounts need only 1 page)
- Process 12 accounts per 15-minute window maximum
```

### 3. **Collection Schedule**
```
Minute 0-15:   Collect Tier 1 (4 accounts) + 8 from Tier 2
Minute 15-30:  Wait (rate limit reset)
Minute 30-45:  Collect Tier 1 (4 accounts) + remaining Tier 2
Minute 45-60:  Wait (rate limit reset)
[Repeat, inserting Tier 3 every 6 hours]
```

### 4. **Optimizations for Basic Account**

#### A. Single Page Strategy
```python
# For caught-up collections, fetch only 1 page
MAX_PAGES_PER_ACCOUNT = 1  # Reduce from 5
PER_PAGE_MAX_RESULTS = 100  # Maximum allowed

# Only fetch multiple pages for first-time collections
if not since_id:
    MAX_PAGES_PER_ACCOUNT = 3  # Limited initial fetch
```

#### B. Early Termination
```python
# Stop immediately if no new tweets
if saved == 0 and pages_collected == 1:
    logger.info(f"✅ No new tweets for @{username}, stopping")
    break
```

#### C. Request Pooling
```python
# Track requests across all accounts
class RequestPool:
    def __init__(self):
        self.requests_used = 0
        self.window_start = time.time()
        self.max_requests = 12  # Leave buffer
    
    def can_make_request(self):
        if time.time() - self.window_start > 900:  # 15 min
            self.reset()
        return self.requests_used < self.max_requests
    
    def use_request(self):
        self.requests_used += 1
```

### 5. **Fallback Strategies**

#### A. Search API Alternative
When rate limited on timelines, use search API (60 requests/15min):
```python
# Search for tweets from specific user
query = f"from:{username} -is:retweet"
tweets = client.search_recent_tweets(
    query=query,
    max_results=100,
    since_id=since_id
)
```

#### B. Batch User Lookups
Verify account status in batches (100 requests/day is plenty):
```python
# Check if accounts are still active/valid
user_ids = [acc['id'] for acc in ACCOUNTS_TO_FOLLOW[:100]]
users = client.get_users(ids=user_ids)
```

### 6. **Configuration Updates**

#### Environment Variables
```bash
# Optimized for Basic Account
export COLLECTION_INTERVAL_SECONDS=900      # 15 minutes (match rate limit window)
export MAX_PAGES_PER_ACCOUNT=1             # Single page for regular collections
export BATCH_SIZE=12                       # Max accounts per 15-min window
export REQUESTS_PER_WINDOW=12              # Leave buffer of 3
export USE_SEARCH_FALLBACK=true            # Enable search API fallback
export PRIORITY_COLLECTION=true            # Enable tiered collection
```

#### Modified Collection Logic
```python
def collect_with_basic_limits():
    """Collection optimized for Basic account constraints"""
    
    # Initialize request pool
    request_pool = RequestPool()
    
    # Get priority accounts for this cycle
    current_minute = datetime.now().minute
    if current_minute < 15 or (current_minute >= 30 and current_minute < 45):
        accounts = TIER_1_ACCOUNTS + TIER_2_ACCOUNTS[:8]
    else:
        # Use search API during wait periods for missed tweets
        use_search_fallback_for_active_accounts()
        return
    
    for account in accounts:
        if not request_pool.can_make_request():
            logger.warning("Request limit reached, waiting for reset")
            break
            
        # Fetch only new tweets (single page)
        tweets = fetch_single_page(account)
        request_pool.use_request()
        
        # Process and save
        save_tweets_to_mongodb(tweets)
```

### 7. **Monthly Budget Management**

With 10,000 tweets/month limit:
- **Daily Budget**: ~333 tweets
- **Per Account Daily**: ~22 tweets (for 15 accounts)
- **Collection Frequency**: Adjust based on usage

```python
def check_monthly_usage():
    """Monitor monthly tweet consumption"""
    current_month = datetime.now().month
    tweet_count = db.tweets.count_documents({
        "collected_at": {
            "$gte": datetime(datetime.now().year, current_month, 1)
        }
    })
    
    daily_rate = tweet_count / datetime.now().day
    projected_monthly = daily_rate * 30
    
    if projected_monthly > 9000:  # 90% of limit
        logger.warning(f"⚠️ High usage: {projected_monthly}/10000 projected")
        # Reduce collection frequency
        return "reduce_frequency"
    return "normal"
```

### 8. **Error Handling for Basic Limits**

```python
ERROR_STRATEGIES = {
    "429": {  # Rate limit
        "action": "wait",
        "duration": 900,  # Full 15-minute window
        "fallback": "use_search_api"
    },
    "403": {  # Forbidden (possibly hit monthly limit)
        "action": "check_usage",
        "fallback": "pause_collection"
    }
}
```

## Implementation Checklist

- [ ] Implement tiered account priority system
- [ ] Add request pooling to track API usage
- [ ] Create search API fallback mechanism  
- [ ] Add monthly usage monitoring
- [ ] Implement single-page fetching for regular collections
- [ ] Add smart scheduling based on account activity patterns
- [ ] Create usage dashboard to monitor API consumption
- [ ] Set up alerts for approaching limits

## Expected Performance

### Before Optimization
- 15 accounts × 5 pages = 75 requests per cycle
- Hit rate limit after 3 accounts
- Collection time: 2+ hours with delays

### After Optimization  
- 15 accounts × 1 page = 15 requests per cycle
- All accounts in 30 minutes (2 windows)
- Smart prioritization ensures important accounts checked frequently
- Search API fallback provides redundancy

## Monitoring Commands

```bash
# Check current rate limit status
curl -X GET "https://api.twitter.com/2/tweets/1" \
  -H "Authorization: Bearer $TWITTER_BEARER_TOKEN" \
  -I  # Headers only to see rate limit

# Monitor collection efficiency
python -c "
from pymongo import MongoClient
db = MongoClient().smarttrendtracer
pipeline = [
    {'\$group': {
        '_id': {
            'hour': {'\$hour': '\$collected_at'},
            'day': {'\$dayOfMonth': '\$collected_at'}
        },
        'count': {'\$sum': 1}
    }},
    {'\$sort': {'_id.day': -1, '_id.hour': -1}},
    {'\$limit': 24}
]
for stat in db.tweets.aggregate(pipeline):
    print(f\"Day {stat['_id']['day']} Hour {stat['_id']['hour']:02d}: {stat['count']} tweets\")
"
```

## Cost-Benefit Analysis

### Current Setup ($100/month)
- ✅ 10,000 tweets/month sufficient for 15 accounts
- ✅ Core operators adequate for our needs
- ⚠️ Tight rate limits require careful management
- ❌ No streaming access (miss real-time tweets)

### Recommended Adjustments
1. **Focus on Quality**: Prioritize high-value accounts
2. **Time-based Collection**: Collect during peak posting hours
3. **Deduplication**: Ensure no duplicate API calls
4. **Caching**: Store user metadata to reduce lookups

### Upgrade Trigger Points
Consider Pro tier ($5,000/month) if:
- Need to monitor 50+ accounts
- Require real-time streaming
- Need full archive search
- Want higher rate limits (300 requests/15min)

## Conclusion

The Basic account is workable for SmartTrendTracer with proper optimization. The key is respecting the 15 requests/15-minute rate limit for timeline fetching and using smart scheduling to maximize coverage within these constraints.