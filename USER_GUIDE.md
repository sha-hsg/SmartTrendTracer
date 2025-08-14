# SmartTrendTracer User Guide

## Getting Started

SmartTrendTracer helps you track AI trends on Twitter/X by monitoring key accounts and using AI to analyze patterns and suggest relevant tags.

## Starting the Application

### Quick Start

1. **Start the backend server** (Terminal 1):
```bash
cd backend
source venv/bin/activate
python run.py
```

2. **Start the frontend** (Terminal 2):
```bash
cd frontend
npm run dev
```

3. **Open your browser**:
Navigate to http://localhost:3000

## Dashboard Overview

### Main Interface

The dashboard displays:
- **Recent Tweets**: Latest tweets from monitored accounts
- **Tag Cloud**: Visual representation of trending tags
- **Trend Analysis**: Hot, emerging, and declining topics
- **Media Gallery**: Images and videos from tweets

### Navigation

- **Home**: Main dashboard with tweet feed
- **Trends**: Detailed trend analysis
- **Tags**: Manage and browse tags
- **Media**: Browse all media attachments
- **Settings**: Configure preferences

## Core Features

### 1. Viewing Tweets

Each tweet card shows:
- Author name and profile picture
- Tweet content with clickable links
- Engagement metrics (likes, retweets, replies)
- Timestamp
- Associated tags
- Media attachments (if any)

**Actions you can take:**
- Click the tweet to view on Twitter/X
- Click tags to filter by that tag
- Click media to view full size
- Add or remove tags

### 2. Tag Management

#### Adding Tags Manually

1. Click the tag icon on any tweet
2. Type the tag name
3. Press Enter or click "Add"

#### AI-Powered Tag Suggestions

1. Click "Suggest Tags" button on a tweet
2. Wait for AI analysis (1-2 seconds)
3. Review suggested tags
4. Click tags to add them
5. Remove unwanted suggestions

#### Auto-Tagging

1. Select multiple tweets (checkbox)
2. Click "Auto-Tag Selected"
3. AI will analyze and apply relevant tags

### 3. Trend Analysis

The trends page shows:

#### Hot Topics
- Topics with high activity in the last 6 hours
- Sorted by engagement and velocity
- Color-coded by intensity (red = very hot)

#### Emerging Topics
- New topics gaining traction
- Less than 24 hours old
- Positive velocity (growing)

#### Declining Topics
- Previously popular topics losing momentum
- Negative velocity or no recent activity

#### Statistics
- Total tweets analyzed
- Time range of analysis
- Number of unique topics
- Average engagement rates

### 4. Media Browser

Browse all media from tweets:
- **Filter by type**: Photos, Videos, GIFs
- **Search**: Find media by associated tweet content
- **Download**: Save media locally
- **View details**: See alt text and tweet context

## Data Collection

### Automatic Collection

The system automatically:
- Checks for new tweets every hour
- Fills gaps when restarted
- Maintains 7-day history minimum

### Manual Collection

#### Collect Recent Tweets
```bash
cd backend
python -m app.collectors.twitter_collector
```

#### Collect Historical Data (up to 7 days)
```bash
python -m app.collectors.smart_collector --days 7
```

#### Fill Gaps
```bash
python -m app.collectors.gap_filler
```

## AI Features

### Tag Suggestion Models

The system uses different AI models for different tasks:

#### For Tag Suggestions (Default: o1-mini)
- High-quality reasoning model
- Understands context deeply
- Suggests 3-5 relevant tags

#### Alternative Models
- **gpt-4o-mini**: Faster, cheaper, good quality
- **gpt-3.5-turbo**: Most economical option

### Changing AI Models

Edit `backend/llm.json`:
```json
{
  "models": {
    "tag_suggestion": {
      "model": "gpt-4o-mini",  // Change model here
      "temperature": 0.3,
      "max_tokens": 500
    }
  }
}
```

### Custom Prompts

Modify AI behavior by editing `backend/prompts.json`:
- Adjust tag suggestion criteria
- Change trend classification rules
- Customize topic extraction

## Search and Filtering

### Quick Filters

- **By Author**: Click author name
- **By Tag**: Click any tag
- **By Date**: Use date picker
- **With Media**: Toggle media-only view

### Advanced Search

Use the search bar with operators:
- `author:OpenAI` - Tweets from OpenAI
- `tag:gpt` - Tweets tagged with "gpt"
- `has:media` - Tweets with media
- `after:2025-01-01` - Tweets after date

### Combining Filters

You can combine multiple filters:
```
author:OpenAI tag:gpt has:media after:2025-01-01
```

## Keyboard Shortcuts

- `Space` - Pause/resume auto-refresh
- `R` - Refresh data
- `T` - Toggle tag panel
- `M` - Toggle media view
- `S` - Focus search
- `Esc` - Close modals
- `1-9` - Quick filter by top tags

## Tips and Best Practices

### For Better Tag Suggestions

1. **Keep tweets focused**: AI works better with clear, single-topic tweets
2. **Review suggestions**: AI suggestions improve with feedback
3. **Maintain consistency**: Use similar tags for related content

### For Trend Analysis

1. **Check daily**: Trends are most accurate with regular data
2. **Look at velocity**: Not just volume, but rate of change
3. **Compare periods**: Use time windows to spot patterns

### For Performance

1. **Limit date ranges**: Smaller ranges load faster
2. **Use pagination**: Don't load all tweets at once
3. **Cache results**: Recently viewed data loads instantly

## Troubleshooting

### Common Issues

#### "No tweets found"
- Check if backend is running
- Verify data collection has run
- Check date filters

#### "AI suggestions failed"
- Verify OpenAI API key is set
- Check API quota/credits
- Try alternative model

#### "Media not loading"
- Check internet connection
- Twitter media URLs may expire
- Try refreshing the page

### Getting Help

1. **Check logs**: 
```bash
# Backend logs
tail -f backend/logs/app.log

# Check database
sqlite3 data/tweets.db "SELECT COUNT(*) FROM tweets;"
```

2. **Test connections**:
```bash
# Test API
curl http://localhost:8000/api/health

# Test AI
cd backend
python test_tag_suggestions.py
```

## Data Export

### Export Tweets to CSV
```python
import pandas as pd
import sqlite3

conn = sqlite3.connect('data/tweets.db')
df = pd.read_sql_query("SELECT * FROM tweets", conn)
df.to_csv('tweets_export.csv', index=False)
```

### Export Tags
```sql
sqlite3 data/tweets.db <<EOF
.headers on
.mode csv
.output tags_export.csv
SELECT t.name, COUNT(tt.tweet_id) as usage_count
FROM tags t
LEFT JOIN tweet_tags tt ON t.id = tt.tag_id
GROUP BY t.id
ORDER BY usage_count DESC;
.quit
EOF
```

## Customization

### Monitored Accounts

Edit `accounts.json` to change which accounts to track:
```json
[
  {
    "username": "NewAccount",
    "twitter_id": "1234567890",
    "category": "AI Research"
  }
]
```

### Update Frequency

Edit collection schedule in backend:
```python
# In backend/app/scheduler.py
scheduler.add_job(
    collect_tweets,
    trigger=IntervalTrigger(minutes=30),  # Change interval
    id='collect_tweets'
)
```

### UI Theme

Modify frontend colors in `frontend/src/styles/theme.css`:
```css
:root {
  --primary-color: #1da1f2;  /* Twitter blue */
  --background: #15202b;      /* Dark mode */
  --text-color: #ffffff;
}
```

## Best Practices

### Daily Workflow

1. **Morning**: Check overnight trends
2. **Midday**: Review hot topics
3. **Evening**: Analyze daily patterns

### Weekly Tasks

1. Review tag usage and clean up duplicates
2. Check trend accuracy
3. Export data for reports
4. Update AI model if needed

### Data Management

1. **Regular backups**: Daily automatic backups
2. **Clean old data**: Remove tweets older than 30 days if needed
3. **Optimize database**: Weekly VACUUM command

## Privacy and Ethics

- All data is collected from public Twitter accounts
- No personal data is stored beyond public tweets
- AI suggestions are for organizational purposes only
- Respect Twitter's Terms of Service

## Advanced Usage

### API Integration

Access data programmatically:
```python
import requests

# Get recent tweets
response = requests.get('http://localhost:8000/api/tweets')
tweets = response.json()

# Get tag suggestions
response = requests.post(
    'http://localhost:8000/api/tags/suggest/1234567890'
)
tags = response.json()
```

### Custom Analysis

Run custom trend analysis:
```python
from backend.app.analyzers.trend_analyzer import TrendAnalyzer

analyzer = TrendAnalyzer()
trends = analyzer.analyze_custom(
    start_date='2025-01-01',
    end_date='2025-01-08',
    min_mentions=5
)
```

## Updates and Maintenance

### Checking for Updates
```bash
git pull origin main
pip install -r backend/requirements.txt
npm install --legacy-peer-deps
```

### Database Maintenance
```bash
# Backup
sqlite3 data/tweets.db ".backup data/backup.db"

# Optimize
sqlite3 data/tweets.db "VACUUM; ANALYZE;"
```

## Support

For issues or questions:
1. Check this user guide
2. Review API documentation
3. Check system logs
4. Contact support with error details