# SmartTrendTracer API Documentation

## Base URL
```
http://localhost:8000
```

## Authentication
Currently no authentication required for local development.

## Endpoints

### Tweets

#### GET /api/tweets
Retrieve tweets with optional filtering.

**Query Parameters:**
- `limit` (int, default: 50): Number of tweets to return
- `offset` (int, default: 0): Pagination offset
- `author` (string): Filter by author username
- `start_date` (string): Filter tweets after this date (ISO format)
- `end_date` (string): Filter tweets before this date (ISO format)
- `has_media` (boolean): Filter tweets with media attachments

**Response:**
```json
{
  "tweets": [
    {
      "id": "1234567890",
      "text": "Tweet content...",
      "author_username": "OpenAI",
      "created_at": "2025-01-08T10:30:00",
      "retweet_count": 100,
      "like_count": 500,
      "reply_count": 50,
      "tags": ["gpt", "ai", "llm"],
      "media": [
        {
          "type": "photo",
          "url": "https://pbs.twimg.com/...",
          "alt_text": "Image description"
        }
      ]
    }
  ],
  "total": 1500,
  "page": 1,
  "pages": 30
}
```

#### GET /api/tweets/{tweet_id}
Get a specific tweet by ID.

**Response:**
```json
{
  "id": "1234567890",
  "text": "Tweet content...",
  "author_username": "OpenAI",
  "created_at": "2025-01-08T10:30:00",
  "tags": ["gpt", "ai"],
  "media": []
}
```

### Tags

#### GET /api/tags
List all unique tags in the system.

**Query Parameters:**
- `limit` (int, default: 100): Number of tags to return
- `min_count` (int, default: 1): Minimum usage count

**Response:**
```json
{
  "tags": [
    {
      "name": "gpt",
      "count": 234,
      "first_seen": "2025-01-01T00:00:00",
      "last_seen": "2025-01-08T12:00:00"
    }
  ],
  "total": 450
}
```

#### POST /api/tags/suggest/{tweet_id}
Get AI-powered tag suggestions for a tweet.

**Response:**
```json
{
  "tweet_id": "1234567890",
  "suggested_tags": ["gpt-4", "multimodal", "ai-safety", "openai", "benchmark"],
  "model_used": "o1-mini",
  "confidence": 0.95
}
```

#### POST /api/tags/auto-tag/{tweet_id}
Automatically apply suggested tags to a tweet.

**Request Body:**
```json
{
  "max_tags": 5,
  "override_existing": false
}
```

**Response:**
```json
{
  "tweet_id": "1234567890",
  "tags_added": ["gpt-4", "multimodal", "ai-safety"],
  "tags_skipped": ["openai"],
  "total_tags": 4
}
```

#### POST /api/tags/suggest/batch
Get tag suggestions for multiple tweets.

**Request Body:**
```json
{
  "tweet_ids": ["123", "456", "789"],
  "max_tags_per_tweet": 5
}
```

**Response:**
```json
{
  "suggestions": {
    "123": ["ai", "llm", "gpt"],
    "456": ["research", "paper", "benchmark"],
    "789": ["safety", "alignment", "rlhf"]
  },
  "model_used": "o1-mini",
  "processed": 3,
  "failed": 0
}
```

#### POST /api/tweets/{tweet_id}/tags
Add tags to a tweet.

**Request Body:**
```json
{
  "tags": ["ai", "llm", "gpt-4"]
}
```

**Response:**
```json
{
  "tweet_id": "1234567890",
  "tags": ["ai", "llm", "gpt-4", "existing-tag"],
  "added": ["ai", "llm", "gpt-4"],
  "already_exists": ["existing-tag"]
}
```

#### DELETE /api/tweets/{tweet_id}/tags/{tag_name}
Remove a tag from a tweet.

**Response:**
```json
{
  "tweet_id": "1234567890",
  "removed": "ai",
  "remaining_tags": ["llm", "gpt-4"]
}
```

### Trends

#### GET /api/trends
Get current trend analysis.

**Query Parameters:**
- `window_hours` (int, default: 24): Time window for analysis
- `min_mentions` (int, default: 2): Minimum mentions to include

**Response:**
```json
{
  "hot_topics": [
    {
      "topic": "GPT-4",
      "score": 0.95,
      "velocity": 0.8,
      "acceleration": 0.3,
      "mention_count_24h": 45,
      "mention_count_7d": 200,
      "classification": "hot",
      "sample_tweets": ["tweet1", "tweet2"]
    }
  ],
  "emerging_topics": [
    {
      "topic": "Claude-3",
      "score": 0.7,
      "velocity": 0.9,
      "first_seen": "2025-01-07T10:00:00"
    }
  ],
  "declining_topics": [
    {
      "topic": "GPT-3",
      "score": 0.2,
      "velocity": -0.5,
      "last_peak": "2025-01-05T12:00:00"
    }
  ],
  "statistics": {
    "total_tweets_analyzed": 1500,
    "time_range": "2025-01-01 to 2025-01-08",
    "unique_topics": 234,
    "analysis_timestamp": "2025-01-08T14:30:00"
  }
}
```

#### GET /api/trends/history/{topic}
Get historical trend data for a specific topic.

**Response:**
```json
{
  "topic": "GPT-4",
  "history": [
    {
      "date": "2025-01-01",
      "mentions": 10,
      "engagement": 500
    },
    {
      "date": "2025-01-02",
      "mentions": 15,
      "engagement": 750
    }
  ],
  "peak_date": "2025-01-05",
  "total_mentions": 234
}
```

### Media

#### GET /api/media/{tweet_id}
Get media attachments for a tweet.

**Response:**
```json
{
  "tweet_id": "1234567890",
  "media": [
    {
      "type": "photo",
      "url": "https://pbs.twimg.com/media/...",
      "alt_text": "Description of image",
      "width": 1200,
      "height": 800
    },
    {
      "type": "video",
      "url": "https://video.twimg.com/...",
      "duration_ms": 30000,
      "thumbnail_url": "https://pbs.twimg.com/..."
    }
  ]
}
```

### Collection

#### POST /api/collect/gaps
Fill gaps in tweet collection since last run.

**Response:**
```json
{
  "tweets_collected": 45,
  "time_range": "2025-01-07T14:00:00 to 2025-01-08T14:00:00",
  "accounts_checked": 7,
  "errors": []
}
```

#### POST /api/collect/history
Collect historical tweets (up to 7 days).

**Request Body:**
```json
{
  "days_back": 7,
  "max_tweets_per_account": 100
}
```

**Response:**
```json
{
  "tweets_collected": 650,
  "accounts_processed": 7,
  "oldest_tweet": "2025-01-01T00:00:00",
  "newest_tweet": "2025-01-08T14:00:00"
}
```

### System

#### GET /api/health
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "database": "connected",
  "tweets_count": 1500,
  "tags_count": 234,
  "uptime_seconds": 3600
}
```

#### GET /api/stats
System statistics.

**Response:**
```json
{
  "database": {
    "tweets": 1500,
    "tags": 234,
    "media_items": 450,
    "unique_authors": 7
  },
  "collection": {
    "last_run": "2025-01-08T12:00:00",
    "tweets_per_day_avg": 50
  },
  "llm": {
    "total_calls": 234,
    "cache_hit_rate": 0.45,
    "avg_response_time_ms": 1200
  }
}
```

## Error Responses

All endpoints use standard HTTP status codes and return errors in this format:

```json
{
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "Tweet with ID 1234567890 not found",
    "details": {
      "tweet_id": "1234567890"
    }
  }
}
```

### Common Error Codes

- `400 Bad Request`: Invalid parameters
- `404 Not Found`: Resource not found
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error
- `503 Service Unavailable`: External service (Twitter/OpenAI) unavailable

## Rate Limiting

- Twitter API: 10 requests per 15 minutes (handled automatically)
- OpenAI API: Based on your tier (typically 60 requests/minute)
- Local endpoints: No rate limiting

## WebSocket Support (Future)

WebSocket support for real-time updates is planned at:
```
ws://localhost:8000/ws
```

## CORS

CORS is enabled for local development. In production, configure allowed origins in `backend/app/main.py`.