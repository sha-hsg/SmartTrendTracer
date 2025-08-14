# SmartTrendTracer

An AI-powered content intelligence platform that tracks trends across **Twitter/X** and **Substack**, with **Python (FastAPI) backend**, **React frontend**, and **LLM-powered analysis**.

## ✨ Key Features

### Twitter/X Integration
- **Automatic Tweet Collection** - Monitors 7 AI-focused Twitter accounts every 30 minutes
- **Interactive AI Tagging** - Click any tweet for LLM-powered tag suggestions (Claude, GPT-4)
- **Trend Analysis** - Identifies hot, emerging, and declining topics
- **Media Support** - Displays images, videos, and link preview cards

### Substack Integration (NEW!)
- **Gmail-based Collection** - Automatically collects newsletters from your Gmail
- **Full Article Storage** - Converts HTML to Markdown for readability
- **Snippet Highlighting** - Highlight and annotate specific passages
- **Article Summarization** - AI-powered summaries and key point extraction
- **Cross-platform Analysis** - Unified trend detection across Twitter and Substack

### Backend Features
- **Python FastAPI** - Robust data processing and analysis
- **SQLite Database** - Efficient local storage with full-text search
- **LLM Integration** - Claude, GPT-4, and Gemini support
- **Hierarchical Tagging** - Ontology-based tag organization

## 📁 Project Structure

```
SmartTrendTracer/
├── backend/                 # Python FastAPI backend
│   ├── app/
│   │   ├── api/            # API endpoints
│   │   ├── models/         # SQLAlchemy database models
│   │   ├── collectors/     # Twitter data collection
│   │   ├── analyzers/      # Trend analysis
│   │   └── main.py         # FastAPI application
│   ├── requirements.txt    # Python dependencies
│   └── run.py             # Server startup script
│
├── frontend/               # React frontend (simplified)
│   ├── src/
│   │   └── components/     # React components
│   └── package.json
│
├── data/
│   └── tweets.db          # SQLite database
└── backend/
    ├── accounts.json      # Twitter accounts to monitor
    ├── llm.json          # LLM configuration
    └── prompts.json      # AI prompt templates

```

## 🚀 Quick Start

### 1. Set up Python Backend

```bash
# Navigate to backend
cd backend

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env and add:
# - TWITTER_BEARER_TOKEN
# - OPENAI_API_KEY (for tag suggestions)

# Run the backend server
python run.py
```

The API will be available at: http://localhost:8000
API documentation at: http://localhost:8000/docs

### 2. Set up React Frontend

```bash
# In a new terminal, navigate to frontend
cd frontend

# Install dependencies
npm install

# Start the development server
npm run dev
```

The dashboard will be available at: http://localhost:3000

## 🔧 Configuration

### Environment Variables (.env)

```env
# Twitter API
TWITTER_BEARER_TOKEN=your_bearer_token_here

# Database (optional, defaults to SQLite)
DATABASE_URL=sqlite:///../data/tweets.db

# API Settings
API_HOST=0.0.0.0
API_PORT=8000

# Frontend URL (for CORS)
FRONTEND_URL=http://localhost:3000
```

## 📊 Data Collection

### Automatic Collection
The backend automatically collects tweets every 30 minutes when running!

### Manual Collection

```bash
# Run collection script
cd backend
python collect_tweets.py

# Or use API
curl -X POST http://localhost:8000/api/collection/collect

# Collect historical tweets (up to 7 days)
curl -X POST "http://localhost:8000/api/collection/collect/historical?days=7"

# Check collection status
python test_collection.py
```

### Analyze Trends

```python
# backend/analyze_trends.py
from app.analyzers.trend_analyzer import TrendAnalyzer

analyzer = TrendAnalyzer()
results = analyzer.analyze_trends(hours=24)
print(f"Top hashtags: {results['top_hashtags'][:5]}")
```

## 🤖 Interactive AI Tagging

### How to Use
1. Click on any tweet card in the dashboard
2. The AI suggestion modal opens automatically
3. Review AI-suggested tags (powered by o1-mini by default)
4. Accept/reject individual suggestions
5. Add custom tags if needed
6. Click "Apply Tags" to save

### Test AI Tagging
```bash
cd backend
python test_interactive_tagging.py
```

### Configure AI Models
Edit `backend/llm.json` to change models:
- `o1-mini` - High-quality reasoning (default)
- `gpt-4o-mini` - Faster, cheaper
- `gpt-3.5-turbo` - Most economical

## 🎨 API Endpoints

### Tweets
- `GET /api/tweets` - Get recent tweets
- `GET /api/tweets/{tweet_id}` - Get specific tweet
- `GET /api/tweets/stats/summary` - Get statistics

### Tags
- `GET /api/tags` - Get all tags with counts
- `GET /api/tags/tweet/{tweet_id}` - Get tags for a tweet
- `POST /api/tags/tweet/{tweet_id}` - Add tag to tweet
- `DELETE /api/tags/tweet/{tweet_id}/{tag}` - Remove tag
- `POST /api/tags/suggest/{tweet_id}` - Get AI tag suggestions
- `POST /api/tags/auto-tag/{tweet_id}` - Auto-apply AI tags

### Collection
- `GET /api/collection/status` - Collection statistics
- `POST /api/collection/collect` - Trigger manual collection
- `POST /api/collection/collect/historical` - Collect past tweets
- `GET /api/collection/gaps` - Find collection gaps

### Trends
- `GET /api/trends` - Get trending topics
- `GET /api/trends/analysis` - Get comprehensive analysis
- `GET /api/trends/topics` - Get all topics

### Media
- `GET /api/media` - Get media items
- `GET /api/media/stats` - Get media statistics

## 🐍 Python Usage Examples

### Working with the Database

```python
from app.models import Tweet, Tag, get_db
from sqlalchemy.orm import Session

# Get database session
db: Session = next(get_db())

# Query tweets
recent_tweets = db.query(Tweet).order_by(Tweet.created_at.desc()).limit(10).all()

# Add a tag
new_tag = Tag(tweet_id="123", tag="python", tag_type="manual")
db.add(new_tag)
db.commit()

# Find tweets with specific tag
tagged_tweets = db.query(Tweet).join(Tag).filter(Tag.tag == "AI").all()
```

### Custom Analysis

```python
import pandas as pd
from app.models import Tweet, get_db

# Load tweets into DataFrame
db = next(get_db())
tweets = db.query(Tweet).all()

df = pd.DataFrame([{
    'id': t.id,
    'text': t.text,
    'author': t.author_username,
    'created_at': t.created_at,
    'likes': t.like_count
} for t in tweets])

# Analyze engagement
top_engaged = df.nlargest(10, 'likes')
print("Most liked tweets:", top_engaged[['text', 'likes']])

# Time series analysis
df['created_at'] = pd.to_datetime(df['created_at'])
daily_tweets = df.resample('D', on='created_at').size()
print("Daily tweet counts:", daily_tweets)
```

## 🔍 Debugging

### Check Backend Status
```bash
# Check if API is running
curl http://localhost:8000/health

# View API docs
open http://localhost:8000/docs
```

### Database Queries
```bash
# Check tweet count
sqlite3 data/tweets.db "SELECT COUNT(*) FROM tweets;"

# View recent tweets
sqlite3 data/tweets.db "SELECT created_at, author_username, text FROM tweets ORDER BY created_at DESC LIMIT 5;"
```

### Python Debugging
```python
# Enable detailed logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Interactive debugging
import pdb; pdb.set_trace()
```

## 📦 Adding New Features

### Add a New API Endpoint

1. Create endpoint in `backend/app/api/your_feature.py`:
```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.models import get_db

router = APIRouter()

@router.get("/")
def your_endpoint(db: Session = Depends(get_db)):
    # Your logic here
    return {"message": "Success"}
```

2. Register in `backend/app/main.py`:
```python
from app.api import your_feature
app.include_router(your_feature.router, prefix="/api/your-feature")
```

### Add a New Collector

```python
# backend/app/collectors/custom_collector.py
class CustomCollector:
    def collect_data(self):
        # Your collection logic
        pass
```

## 🚢 Deployment

### Using Docker

```dockerfile
# backend/Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "run.py"]
```

### Using systemd (Linux)

```ini
# /etc/systemd/system/smarttrendtracer.service
[Unit]
Description=SmartTrendTracer API
After=network.target

[Service]
Type=simple
User=youruser
WorkingDirectory=/path/to/backend
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/python run.py
Restart=always

[Install]
WantedBy=multi-user.target
```

## 📝 Key Differences from JavaScript Version

1. **Database Access**: Using SQLAlchemy ORM instead of raw SQL
2. **Type Safety**: Python type hints + Pydantic for validation
3. **API Framework**: FastAPI instead of Next.js API routes
4. **Data Processing**: Pandas/NumPy for analysis instead of JavaScript array methods
5. **Async Support**: Native Python async/await with proper database session management

## 🛠️ Troubleshooting

### Common Issues

1. **ModuleNotFoundError**: Make sure virtual environment is activated
2. **Database locked**: Close other connections to SQLite
3. **CORS errors**: Check FRONTEND_URL in .env matches your React app
4. **Rate limiting**: Twitter API allows 10 requests/15 min

### Support

For issues or questions about the Python implementation, check:
- FastAPI docs: https://fastapi.tiangolo.com
- SQLAlchemy docs: https://www.sqlalchemy.org
- Tweepy docs: https://docs.tweepy.org

## 🎯 Next Steps

1. Add automated testing with pytest
2. Implement Redis caching for better performance
3. Add Celery for background task processing
4. Deploy to cloud (AWS/GCP/Azure)
5. Add machine learning models for better trend prediction

---

Built with ❤️ using Python and React