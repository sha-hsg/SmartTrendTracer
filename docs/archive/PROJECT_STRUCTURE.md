# SmartTrendTracer - Project Structure

## Current Architecture: Python + React

```
SmartTrendTracer/
├── backend/                    # Python FastAPI Backend
│   ├── app/
│   │   ├── api/               # API endpoints
│   │   │   ├── tweets.py      # Tweet endpoints
│   │   │   ├── tags.py        # Tag management + LLM suggestions
│   │   │   ├── media.py       # Media endpoints
│   │   │   └── trends.py      # Trend analysis
│   │   ├── models/            # SQLAlchemy models
│   │   │   ├── database.py    # Database connection
│   │   │   └── tweet.py       # Data models
│   │   ├── services/          # Business logic
│   │   │   └── llm_service.py # LLM integration for tag suggestions
│   │   ├── collectors/        # Data collection
│   │   │   └── twitter_collector.py
│   │   ├── analyzers/         # Analysis tools
│   │   │   └── trend_analyzer.py
│   │   └── main.py            # FastAPI app
│   ├── llm.json              # LLM model configuration
│   ├── prompts.json          # LLM prompts
│   ├── requirements.txt      # Python dependencies
│   ├── run.py                # Server startup
│   ├── test_tag_suggestions.py # Test LLM features
│   └── .env                  # API keys and config
│
├── frontend/                  # React Frontend (minimal)
│   ├── src/
│   │   ├── components/       # React components
│   │   │   ├── Dashboard.tsx
│   │   │   ├── TweetCard.tsx
│   │   │   ├── TagCloud.tsx
│   │   │   └── TrendAnalysis.tsx
│   │   └── App.tsx
│   ├── package.json
│   └── vite.config.ts        # Vite bundler config
│
├── data/
│   ├── tweets.db             # SQLite database
│   └── media/                # Downloaded media files
│
└── setup_python.sh           # Setup script
```

## Key Features

### Backend (Python/FastAPI)
- **LLM-Powered Tag Suggestions** using OpenAI (o1-mini, GPT-4, etc.)
- **Twitter Data Collection** via Tweepy
- **Trend Analysis** with velocity calculations
- **RESTful API** with automatic documentation
- **SQLAlchemy ORM** for database operations

### Frontend (React)
- **Minimal UI** for displaying data
- **Tag Management** interface
- **Trend Visualization**
- **No complex state management** - just displays Python backend data

### LLM Integration
- **Configurable Models** via `llm.json`
- **Customizable Prompts** via `prompts.json`
- **Reasoning Model Support** (o1-mini, o1-preview)
- **Automatic Fallback** for API failures

## Quick Start

```bash
# Backend
cd backend
source venv/bin/activate
python run.py

# Frontend (new terminal)
cd frontend
npm run dev
```

## API Documentation
- Backend API: http://localhost:8000/docs
- Frontend: http://localhost:3000

## Configuration Files
- `backend/llm.json` - LLM model settings
- `backend/prompts.json` - AI prompts
- `backend/.env` - API keys and secrets
- `accounts.json` - Twitter accounts to monitor