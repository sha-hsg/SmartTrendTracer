# Tweet Collector Service

## Default Mode: Basic Account ($100/month)
The collector now **defaults to Basic Account Mode**, optimized for Twitter's $100/month API plan.

## Quick Start

```bash
# Just run the collector - Basic Mode is default
python tweet_collector_service.py

# Or use the launcher for options
./start_basic_collector.sh
```

## Configuration

### Basic Account Mode (DEFAULT)
- **Enabled by default** - no configuration needed
- Max 1 page per account (100 tweets)
- 15-minute collection intervals
- 12 requests per 15-minute window
- Monthly limit: 10,000 tweets
- Daily budget: 333 tweets
- Tiered priority system enabled

### To Use Pro/Enterprise Mode
If you have a higher tier Twitter API plan:

```bash
# Disable Basic Account Mode
export BASIC_ACCOUNT_MODE=false
python tweet_collector_service.py
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `BASIC_ACCOUNT_MODE` | **true** | Enable Basic Account optimizations |
| `MAX_PAGES_PER_ACCOUNT` | 1 (Basic) / 5 (Pro) | Pages to fetch per account |
| `COLLECTION_INTERVAL_SECONDS` | 900 (Basic) / 1800 (Pro) | Time between collection cycles |
| `USE_TIERED_PRIORITY` | true (Basic) / false (Pro) | Enable account prioritization |
| `USE_SEARCH_FALLBACK` | true (Basic) / false (Pro) | Use search API when rate limited |

## Account Tiers (Basic Mode)

### Tier 1 (Every 30 min)
- OpenAI
- AnthropicAI  
- sama
- emollick

### Tier 2 (Every 2 hours)
- huggingface
- GoogleDeepMind
- stanfordnlp
- hwchase17
- kaggle

### Tier 3 (Every 6 hours)
- rasbt
- JayAlammar
- Yoavgo
- Shayneredford
- Sebastienbubeck

## Monitoring Usage

```bash
# Real-time usage dashboard
python monitor_usage.py

# Check current stats
python test_refactored_collector.py
```

## Current Status
- Monthly usage: ~83% (8,378/10,000 tweets)
- Daily usage: Varies
- Recommendation: Monitor closely as approaching monthly limit

## Troubleshooting

### "Rate limit exceeded"
- Normal for Basic account - collector will wait automatically
- Uses exponential backoff up to 15 minutes

### "Monthly/Daily budget exceeded"
- Collector will automatically reduce frequency
- Consider waiting until next month/day

### To force Pro mode
```bash
export BASIC_ACCOUNT_MODE=false
export MAX_PAGES_PER_ACCOUNT=5
python tweet_collector_service.py
```