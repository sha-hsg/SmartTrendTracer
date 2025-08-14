# SmartTrendTracer Collection Guide

## 🆕 NEW: Twscrape Support (No Rate Limits!)

We now support **twscrape** as an alternative to the Twitter API:
- ✅ **NO RATE LIMITS** - Collect as much as you want
- ✅ **Search support** - Search for any tweets
- ✅ **Historical data** - Get older tweets
- ⚠️ **Less reliable** - May break when Twitter changes
- ⚠️ **ToS violation** - Use at your own risk

### Quick Start with Twscrape:
```bash
python setup_twscrape_guest.py   # One-time setup
python collect_twscrape.py       # Collect without limits!
```

## Twitter API Rate Limits (Original Method)
- **Basic Tier**: 10 requests per 15 minutes
- **We track 7 accounts** = minimum 7 requests per full collection
- **Strategy**: Collect conservatively to avoid 429 errors

## Collection Tools Comparison

| Method | Rate Limits | Speed | Reliability | Best For |
|--------|------------|-------|-------------|----------|
| **Twitter API** | 10 req/15min | Slow | Very High | Production |
| **Twscrape** | None! | Fast | Medium | Personal/Research |
| **Smart Hybrid** | Best of both | Fast | High | All scenarios |

## Collection Tools

### 🆕 0. Smart Hybrid Collector (RECOMMENDED)
```bash
python smart_collect.py
```
- Uses Twitter API when available
- Falls back to twscrape when rate limited
- Best of both worlds!

### 1. Simple Server (No Auto-Collection)
```bash
python simple_server.py
```
- Starts API server WITHOUT automatic collection
- Use this when you want manual control
- Responds to Ctrl+C immediately

### 2. Main Server (With Auto-Collection)
```bash
python run_server.py
```
- Starts API server WITH automatic startup collection
- Fills gaps since last run
- May wait for rate limits on startup

### 3. Manual Collection
```bash
python collect_tweets.py
```
- Simple manual collection
- Collects tweets since last run
- Exits if rate limited

### 4. Wait and Collect (Recommended)
```bash
python wait_and_collect.py
```
- **Smart collection that waits for rate limits**
- Shows progress and statistics
- Collects from all 7 accounts efficiently
- Best for scheduled/regular collection

### 5. Force Collection
```bash
python force_collect.py
```
- Forces collection from last 3 hours
- Only collects from 3 accounts (to avoid rate limits)
- Use when you need urgent updates

### 6. Monitor Collection Status
```bash
python monitor_collection.py
```
- Shows comprehensive collection statistics
- Displays rate limit status
- Shows tweet distribution by time and account
- Provides recommendations

### 7. Check Rate Limit
```bash
python check_rate_limit.py
```
- Shows current rate limit status
- Displays remaining requests
- Shows when rate limit will reset

### 8. Reset Collection State
```bash
python reset_collection_state.py
```
- Resets last collection timestamp
- Forces next collection to gather recent tweets
- Use if collection state is corrupted

## Emergency Tools

### Emergency Stop
```bash
./emergency_stop.sh
```
- Force kills all server processes
- Use when server won't respond to Ctrl+C
- Cleans up port 8000

### Clean Start
```bash
./clean_start.sh
```
- Kills existing processes on port 8000
- Starts fresh server instance

## Recommended Workflow

### Daily Operation
1. Start server: `python simple_server.py`
2. Check status: `python monitor_collection.py`
3. Collect tweets: `python wait_and_collect.py`
4. View dashboard: http://localhost:3000

### Automated Collection (Cron)
Add to crontab for hourly collection:
```bash
0 * * * * cd /path/to/backend && source venv/bin/activate && python wait_and_collect.py
```

### Dealing with Rate Limits

#### Check Current Status
```bash
python check_rate_limit.py
```

#### If Rate Limited
1. **Option A**: Wait for automatic reset (15 minutes)
2. **Option B**: Use `wait_and_collect.py` (waits automatically)
3. **Option C**: Check specific time with `monitor_collection.py`

#### If Getting 429 Errors
1. Stop current collection (Ctrl+C or `emergency_stop.sh`)
2. Check rate limit: `python check_rate_limit.py`
3. Wait for reset or use `wait_and_collect.py`

## Tips

1. **Best Collection Times**: Every 2-4 hours is sufficient
2. **Rate Limit Management**: The system tracks requests automatically
3. **Backoff Strategy**: After 429 errors, system waits 5 minutes minimum
4. **Partial Collection**: If rate limited, partial collection is saved
5. **Gap Filling**: System automatically fills gaps on next run

## Database Info

- **Database**: `data/tweets.db`
- **Tables**: tweets, tweet_media, tags, collection_state
- **Total Capacity**: Unlimited (SQLite)

## Troubleshooting

### "Port 8000 already in use"
```bash
./emergency_stop.sh
# or
lsof -i :8000 | grep LISTEN | awk '{print $2}' | xargs kill -9
```

### "Rate limited (429)"
```bash
python check_rate_limit.py  # Check status
python wait_and_collect.py  # Will wait automatically
```

### "No new tweets collected"
- This is normal if accounts haven't posted recently
- Check `monitor_collection.py` for last tweet times
- Some accounts post infrequently

### "Server won't stop"
```bash
./emergency_stop.sh
```

## Performance Stats

- **Collection Time**: ~10 seconds for all 7 accounts
- **Rate Limit Window**: 15 minutes
- **Max Requests**: 10 per window
- **Optimal Frequency**: Every 2-4 hours
- **Database Size**: ~5MB per 1000 tweets

---
Last Updated: August 8, 2025