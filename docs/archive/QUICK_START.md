# SmartTrendTracer - Quick Start Guide

## 🚀 Starting the System

### 1. Start Backend Server
```bash
cd backend
source venv/bin/activate
python -m uvicorn app.main:app --reload --port 8000
```

### 2. Start Frontend (in new terminal)
```bash
cd frontend
npm start
```

### 3. Access the Application
Open your browser and go to: **http://localhost:3000**

## ✅ System Health Check

Run the health check to verify everything is working:
```bash
cd backend
python system_check.py
```

This will show:
- ✓ Service status (Backend & Frontend)
- ✓ Database connectivity
- ✓ API endpoints
- ✓ Configuration files
- ✓ Recent activity

## 📊 Main Features

### 1. Twitter Dashboard
**URL:** http://localhost:3000/
- View latest tweets from monitored AI accounts
- Tag tweets with AI topics
- Search and filter by tags
- View media attachments

### 2. Substack Articles
**URL:** http://localhost:3000/substack
- Browse collected newsletters
- Read full articles
- Create snippets and annotations
- Generate AI summaries

### 3. Tag Management
**URL:** http://localhost:3000/tags
- View tag cloud
- Manage tag hierarchy
- Use Gemini 2.5 Pro for tag reorganization
- Create synonyms and relationships

### 4. Trends Analysis
**URL:** http://localhost:3000/trends
- View trending topics
- Analyze hot/declining trends
- Cross-platform insights (Twitter + Substack)

## 📥 Collecting New Content

### Collect Today's Articles Only
```bash
cd backend
python todays_articles.py

# Or only forwarded articles
python todays_articles.py --forwarded-only
```

### Collect New Tweets (if not rate-limited)
```bash
cd backend
python collect_tweets.py
```

## 🔍 Common Tasks

### Check System Status
```bash
python system_check.py
```

### View Database Statistics
```bash
sqlite3 data/tweets.db "SELECT 'Tweets:', COUNT(*) FROM tweets UNION SELECT 'Articles:', COUNT(*) FROM substack_articles UNION SELECT 'Tags:', COUNT(*) FROM tags;"
```

### Restart Servers
```bash
# Kill existing servers
pkill -f uvicorn
pkill -f "npm start"

# Start fresh
cd backend && source venv/bin/activate && python -m uvicorn app.main:app --reload &
cd frontend && npm start &
```

## ⚠️ Troubleshooting

### Backend Not Responding
1. Check if port 8000 is free: `lsof -i :8000`
2. Kill any process using it: `kill -9 <PID>`
3. Restart backend server

### Frontend Not Loading
1. Check if port 3000 is free: `lsof -i :3000`
2. Clear browser cache
3. Check console for errors (F12)

### Database Issues
1. Check database exists: `ls -la backend/data/tweets.db`
2. Check permissions: `chmod 644 backend/data/tweets.db`
3. Verify with: `sqlite3 backend/data/tweets.db ".tables"`

### Rate Limiting (Twitter)
- System is rate-limited for 15-minute windows
- Check status: `python system_check.py`
- Wait for automatic retry or use `python wait_and_collect.py`

## 📝 Configuration Files

- **backend/llm.json** - LLM model configurations
- **backend/prompts_config.json** - System prompts
- **backend/forwarded_authors.json** - Forwarded newsletter authors
- **backend/.env** - API keys and environment variables

## 🎯 Current System Status

As of your last check:
- ✅ **Backend**: Running on port 8000
- ✅ **Frontend**: Running on port 3000
- ✅ **Database**: 578 tweets, 39 articles, 1448 tags
- ⚠️ **Twitter Collection**: Rate-limited (automatic retry enabled)
- ✅ **Today's Activity**: 13 tweets, 3 articles collected

## 💡 Tips

1. **Use the system check** regularly to verify health
2. **Collect articles daily** with `python todays_articles.py`
3. **Tag tweets** to build your knowledge graph
4. **Use Gemini reorganization** to organize tags efficiently
5. **Create snippets** from articles for key insights

---
**Need help?** Run `python system_check.py` to diagnose issues!