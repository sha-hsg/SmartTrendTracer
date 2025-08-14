# Faceted Browsing & Enhanced Features Guide

## Overview
This guide documents the new faceted browsing and tag suggestion features added to SmartTrendTracer for both Twitter/X tweets and Substack articles.

## New Features

### 1. Tag Suggestions for Substack Articles
Similar to the existing tweet tag suggestions, Substack articles now have AI-powered tag suggestions that combine:
- **Existing tags** from the vector store (semantic similarity search)
- **New AI-generated tags** using GPT-4o-mini

### 2. Faceted Browsing for Tweets
Enhanced tweet browsing with multi-faceted filtering:
- Filter by multiple authors simultaneously
- Filter by multiple tags (AND/OR logic)
- Exclude retweets option
- Full-text search
- Real-time facet counts

### 3. Faceted Browsing for Substack Articles
Advanced article browsing with:
- Filter by multiple authors
- Filter by multiple tags
- Full-text search across title, subtitle, and preview
- Tag suggestion integration
- Real-time facet counts

## API Endpoints

### Enhanced Substack API (`/api/v2/substack/`)

#### Tag Suggestions
```http
POST /api/v2/substack/articles/{article_id}/suggest-tags
```
Returns both existing similar tags and new AI-generated suggestions.

#### Add Tag to Article
```http
POST /api/v2/substack/articles/{article_id}/tags
Body: {
  "tag": "string",
  "tag_type": "manual",
  "confidence": 1.0
}
```

#### Remove Tag from Article
```http
DELETE /api/v2/substack/articles/{article_id}/tags/{tag}
```

#### Faceted Search
```http
GET /api/v2/substack/articles/faceted-search
Query Parameters:
- page: int (default: 1)
- page_size: int (default: 20, max: 100)
- author_ids: List[int] (optional)
- tags: List[str] (optional)
- search: str (optional)
```

### Enhanced Tweets API (`/api/v2/tweets/`)

#### Faceted Search
```http
GET /api/v2/tweets/tweets/faceted-search
Query Parameters:
- page: int (default: 1)
- page_size: int (default: 50, max: 200)
- authors: List[str] (optional, usernames)
- tags: List[str] (optional)
- search: str (optional)
- exclude_retweets: bool (default: false)
```

#### Get Tweets by Author
```http
GET /api/v2/tweets/tweets/by-author/{author_username}
Query Parameters:
- page: int
- page_size: int
- tags: List[str] (optional)
- exclude_retweets: bool
```

#### Get Tweets by Tags
```http
GET /api/v2/tweets/tweets/by-tags
Query Parameters:
- tags: List[str] (required)
- mode: str ('all' or 'any')
- page: int
- page_size: int
- authors: List[str] (optional)
- exclude_retweets: bool
```

## Frontend Components

### FacetedSubstackDashboard
Location: `frontend/src/components/FacetedSubstackDashboard.tsx`

Features:
- Multi-author filtering
- Multi-tag filtering
- Search functionality
- Tag suggestion modal
- Add/remove tags inline
- Pagination
- Real-time facet counts

### FacetedTweetsDashboard
Location: `frontend/src/components/FacetedTweetsDashboard.tsx`

Features:
- Multi-author filtering with username and display name
- Multi-tag filtering
- Search functionality
- Exclude retweets toggle
- Pagination
- Real-time facet counts

## Usage Instructions

### Starting the Application

1. **Start the Backend API**:
```bash
cd backend
python app/main.py
```

2. **Start the Frontend**:
```bash
cd frontend
npm start
```

3. **Access the Application**:
- Classic Tweet Dashboard: http://localhost:3000/
- Faceted Tweet Dashboard: http://localhost:3000/tweets-faceted
- Classic Substack Dashboard: http://localhost:3000/substack
- Faceted Substack Dashboard: http://localhost:3000/substack-faceted

### Using Faceted Browsing

#### For Tweets:
1. Navigate to the Faceted Tweets Dashboard
2. Use the left sidebar to:
   - Select one or more authors to filter
   - Select one or more tags to filter
   - Toggle "Exclude Retweets" if desired
3. Use the search bar for full-text search
4. Active filters appear as tags below the search bar
5. Click "Clear All Filters" to reset

#### For Substack Articles:
1. Navigate to the Faceted Substack Dashboard
2. Use the left sidebar to:
   - Select one or more authors to filter
   - Select one or more tags to filter
3. Use the search bar to search titles and content
4. Click "Suggest Tags" on any article to get AI suggestions
5. Click on suggested tags to add them
6. Remove tags with the × button

### Tag Management

#### Adding Tags to Substack Articles:
1. Click "Suggest Tags" button on an article
2. Review suggestions:
   - Green tags: Existing tags from other articles (with similarity scores)
   - Purple tags: New AI-generated suggestions
3. Click any suggestion to add it to the article
4. Tags are immediately saved to the database

#### Removing Tags:
- Click the × button next to any tag to remove it

## Database Schema

### New/Modified Tables

#### article_tags
Stores tags for Substack articles:
- `id`: Primary key
- `article_id`: Foreign key to substack_articles
- `tag`: Tag text
- `tag_type`: 'manual', 'ai_suggested', etc.
- `confidence`: Confidence score (0-1)
- `created_at`: Timestamp

## Implementation Details

### Vector Store Integration
Both tweet and article tag suggestions use the same FAISS vector store with OpenAI embeddings for finding semantically similar existing tags.

### Faceted Search Performance
- Server-side filtering for optimal performance
- Efficient SQL queries with proper indexing
- Pagination to handle large datasets
- Real-time facet counts updated with each filter change

### Tag Filtering Logic
- **Tweets**: When multiple tags selected, tweets must have ALL tags (AND logic)
- **Articles**: When multiple tags selected, articles must have ALL tags (AND logic)
- **Authors**: When multiple authors selected, content from ANY author is shown (OR logic)

## Troubleshooting

### API Not Found (404 errors)
- Ensure the server has been restarted after adding new endpoints
- Check that enhanced_tweets and enhanced_substack routers are imported in main.py

### Tag Suggestions Not Working
- Verify OpenAI API key is set in environment variables
- Check that the vector store exists in `data/vector_store/`
- Rebuild vector store if needed: `python build_vector_store.py`

### Facets Not Updating
- Check browser console for errors
- Verify API responses include facet data
- Ensure database has proper indexes on tag and author fields

## Future Enhancements

1. **Advanced Tag Management**:
   - Bulk tag operations
   - Tag hierarchies and relationships
   - Auto-tagging on collection

2. **Enhanced Filtering**:
   - Date range filters
   - Sentiment filters
   - Media type filters for tweets

3. **Export Functionality**:
   - Export filtered results to CSV/JSON
   - Generate reports from faceted views

4. **Saved Searches**:
   - Save filter combinations
   - Create custom dashboards
   - Alert on new matching content

## Dependencies

### Backend:
- FastAPI
- SQLAlchemy
- OpenAI API (for tag suggestions)
- FAISS (for vector similarity)

### Frontend:
- React
- TypeScript
- Axios
- React Router DOM

---

Last updated: August 10, 2025