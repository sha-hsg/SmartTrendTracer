# Setup Instructions for Faceted Browsing Features

## Prerequisites

### 1. Install React Router in Frontend
```bash
cd frontend
npm install react-router-dom
```

### 2. Update App Component
You have two options:

#### Option A: Use the new AppWithRouting (Recommended)
Edit `frontend/src/main.tsx` or `frontend/src/index.tsx` and change:
```typescript
// Old
import App from './App'

// New
import AppWithRouting from './AppWithRouting'
```

Then update the render:
```typescript
// Old
<App />

// New
<AppWithRouting />
```

#### Option B: Update existing App.tsx
Replace the content of `frontend/src/App.tsx` with the content from `AppWithRouting.tsx`

## Starting the Application

### Terminal 1 - Backend API
```bash
cd backend
source venv/bin/activate  # If using virtual environment
python app/main_simple.py

# Alternative with uvicorn:
# uvicorn app.main_simple:app --reload --host 0.0.0.0 --port 8000
```

### Terminal 2 - Frontend
```bash
cd frontend
npm start
```

## Verify Installation

1. **Check Backend API**:
   - Open http://localhost:8000/docs
   - Look for `/api/v2/tweets/` endpoints
   - Look for `/api/v2/substack/` endpoints

2. **Check Frontend**:
   - Open http://localhost:3000
   - You should see navigation links at the top:
     - Tweets (Classic)
     - Tweets (Faceted)
     - Substack (Classic)
     - Substack (Faceted)

## Using the New Features

### Faceted Tweet Dashboard
Navigate to: http://localhost:3000/tweets-faceted

Features:
- **Author Filtering**: Click authors in the left sidebar
- **Tag Filtering**: Click tags in the left sidebar
- **Search**: Use the search bar for full-text search
- **Exclude Retweets**: Toggle the checkbox
- **Clear Filters**: Click "Clear All Filters" button

### Faceted Substack Dashboard
Navigate to: http://localhost:3000/substack-faceted

Features:
- **Author Filtering**: Click authors in the left sidebar
- **Tag Filtering**: Click tags in the left sidebar
- **Search**: Use the search bar for title/content search
- **Tag Suggestions**: Click "Suggest Tags" on any article
- **Add Tags**: Click suggested tags to add them
- **Remove Tags**: Click × next to any tag

## Troubleshooting

### "Module not found: react-router-dom"
Run: `cd frontend && npm install react-router-dom`

### Navigation not showing
Make sure you're using `AppWithRouting` instead of the basic `App` component

### API endpoints return 404
1. Check the server console for import errors
2. Restart the backend server
3. Verify the enhanced modules are imported in `main_simple.py`

### No facet counts showing
Check browser console for API errors - the database might need indexes:
```sql
CREATE INDEX IF NOT EXISTS idx_article_tags_tag ON article_tags(tag);
CREATE INDEX IF NOT EXISTS idx_article_tags_article_id ON article_tags(article_id);
CREATE INDEX IF NOT EXISTS idx_tags_tag ON tags(tag);
CREATE INDEX IF NOT EXISTS idx_tags_tweet_id ON tags(tweet_id);
```

## Files Created/Modified

### Backend
- `/backend/app/api/enhanced_tweets.py` - Faceted browsing API for tweets
- `/backend/app/api/enhanced_substack.py` - Faceted browsing and tag suggestions for Substack
- `/backend/app/main_simple.py` - Updated to include new routers
- `/backend/app/main.py` - Updated to include new routers

### Frontend
- `/frontend/src/AppWithRouting.tsx` - Main app with routing
- `/frontend/src/components/FacetedTweetsDashboard.tsx` - Faceted tweet browser
- `/frontend/src/components/FacetedTweetsDashboard.css` - Styles for tweet browser
- `/frontend/src/components/FacetedSubstackDashboard.tsx` - Faceted Substack browser
- `/frontend/src/components/FacetedSubstackDashboard.css` - Styles for Substack browser
- `/frontend/src/App.css` - Updated with navigation styles

## Quick Test

After starting both backend and frontend:

1. Test Substack tag suggestions:
```bash
curl -X POST http://localhost:8000/api/v2/substack/articles/1/suggest-tags
```

2. Test faceted search:
```bash
curl "http://localhost:8000/api/v2/tweets/tweets/faceted-search?page=1&page_size=5"
```

If these return data, the backend is working correctly!