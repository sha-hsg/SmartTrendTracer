# 🚀 SmartTrendTracer - Quick Start Guide

## Your Current Situation
- **Database**: 501 tweets collected ✅
- **Twitter API**: Rate limited (10 requests/15 min)
- **Twscrape**: Account added but needs manual verification
- **Solution**: Multiple working collectors!

## 🎯 RECOMMENDED: Start Collecting Now

### Option 1: Scheduled Collector (SET AND FORGET)
```bash
python scheduled_collector.py
```
- ✅ Runs every 30 minutes automatically
- ✅ Handles rate limits intelligently
- ✅ Keep it running in background
- ✅ No manual intervention needed

### Option 2: On-Demand Collection
```bash
python wait_and_collect.py
```
- ✅ Collects immediately
- ✅ Waits if rate limited
- ✅ Shows progress

### Option 3: Quick Check
```bash
python monitor_collection.py
```
- See latest tweets
- Check collection status
- View statistics

## 📊 Monitoring Commands

```bash
# Check if rate limited
python check_rate_limit.py

# See collection statistics
python monitor_collection.py

# View dashboard
cd ../frontend && npm start
# Then open http://localhost:3000
```

## 🔧 Server Commands

```bash
# Start API server (no auto-collection)
python simple_server.py

# Start with auto-collection
python run_server.py
```

## 📈 Your 7 Tracked Accounts
1. @OpenAI - GPT updates
2. @AnthropicAI - Claude news  
3. @GoogleDeepMind - Gemini developments
4. @huggingface - Open source AI
5. @emollick - AI insights
6. @stanfordnlp - Research
7. @sama - Sam Altman

## 🚨 If Rate Limited

Don't worry! The system handles it:

1. **Automatic**: Use `scheduled_collector.py` - it waits automatically
2. **Manual**: Run `wait_and_collect.py` - it waits for you
3. **Check status**: `python check_rate_limit.py`

## 💡 Best Practice

**For continuous collection:**
```bash
# Terminal 1: Run the scheduled collector
python scheduled_collector.py

# Terminal 2: Run the API server
python simple_server.py

# Terminal 3: Run the dashboard
cd ../frontend && npm start
```

This gives you:
- Automatic tweet collection every 30 minutes
- API for the dashboard
- Web interface to view tweets

## 🆘 Troubleshooting

**"429 Too Many Requests"**
- Normal! Wait 15 minutes or use `wait_and_collect.py`

**"Port 8000 in use"**
```bash
./emergency_stop.sh
```

**"No new tweets"**
- The AI accounts don't tweet every minute
- This is normal

## 📝 Summary

You have a fully working system that:
- ✅ Collects tweets from 7 AI accounts
- ✅ Manages rate limits automatically
- ✅ Stores everything in SQLite
- ✅ Has a web dashboard
- ✅ Works reliably with Twitter API

**Start with:** `python scheduled_collector.py`

It will run forever, collecting tweets every 30 minutes, handling all rate limits automatically. Perfect for your needs!