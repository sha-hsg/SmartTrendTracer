# Batch Tweet Annotation

## Overview

Batch annotation allows users to automatically generate and apply AI-powered concept tags to multiple tweets at once. Users filter tweets using existing facets (search, author, year, annotation status), select an LLM model, and trigger batch processing. The system processes tweets in the background, showing real-time progress.

## User Flow

1. **Filter Tweets**: Use existing facets to narrow down the tweet list
   - Search by text
   - Filter by author (@OpenAI, @AnthropicAI, etc.)
   - Filter by year
   - Filter by annotation status ("Not Annotated" for new tweets)

2. **Select Model**: Choose an AI model from the dropdown
   - Claude models (Sonnet, Opus, Haiku)
   - GPT models (GPT-4o, GPT-4o-mini)
   - Gemini models (2.5 Pro, 2.5 Flash)

3. **Start Batch**: Click "Batch Annotate (N tweets)"

4. **Monitor Progress**: Watch the progress bar update in real-time

5. **View Results**: See summary of new tags added, skipped, and errors

## Architecture

### Backend Components

#### API Endpoints

**File**: `backend/app/api/tweets_mongodb.py`

```
POST /api/tweets/batch-annotate
```
Starts batch annotation for a list of tweet IDs.

**Request Body:**
```json
{
  "tweet_ids": ["tweet_id_1", "tweet_id_2", ...],
  "model": "claude-3.5-sonnet"  // Optional, uses default if not specified
}
```

**Response:**
```json
{
  "task_id": "uuid-string",
  "status": "started",
  "total": 50,
  "message": "Batch annotation started for 50 tweets"
}
```

---

```
GET /api/tweets/batch-annotate/{task_id}/status
```
Polls the status of a running batch annotation task.

**Response:**
```json
{
  "task_id": "uuid-string",
  "status": "running",        // "running" | "completed"
  "progress": 45,             // 0-100 percentage
  "total": 50,
  "processed": 23,
  "new_tags_count": 87,
  "skipped_count": 12,
  "error_count": 0,
  "started_at": "2025-01-25T10:30:00Z",
  "completed_at": null        // Set when completed
}
```

#### Background Processing

The `run_batch_annotation()` function processes tweets sequentially in a FastAPI BackgroundTask:

1. **Get Tweet Content**: Fetch tweet text from MongoDB
2. **Check Existing Tags**: Get current concepts to avoid duplicates
3. **Generate Suggestions**: Call LLM with tag suggestion prompt
4. **Apply New Concepts**: Add only concepts not already present
5. **Update Progress**: Track processed count and percentage

#### Tag Suggestion Prompt

```
Analyze this tweet and suggest relevant concept tags.

Tweet: {tweet_text}

Instructions:
1. Suggest 3-5 relevant concepts for this tweet
2. Focus on main topics, technologies, people, organizations mentioned
3. Use snake_case for slugs (e.g., machine_learning, sam_altman)
4. Use proper capitalization for display names (e.g., "Machine Learning", "Sam Altman")

Return as JSON array with format:
[
  {
    "display_name": "Proper Name",
    "slug": "snake_case_slug",
    "entity_type": "topic|person|organisation|location|event|product"
  }
]
```

### Frontend Components

**File**: `frontend/src/components/FacetedTweetsDashboardModern.tsx`

#### State Variables

```typescript
const [batchAnnotating, setBatchAnnotating] = useState(false)
const [batchProgress, setBatchProgress] = useState(0)
const [batchModel, setBatchModel] = useState<string>('')
const [batchResult, setBatchResult] = useState<{
  status: 'idle' | 'running' | 'completed' | 'error'
  newTagsCount?: number
  skippedCount?: number
  errorCount?: number
  message?: string
}>({ status: 'idle' })
```

#### UI Components

- **UnifiedModelSelector**: Dropdown for selecting LLM model
- **Batch Annotate Button**: Triggers annotation, shows progress when running
- **Progress Bar**: Visual progress indicator (0-100%)
- **Result Badge**: Shows success/error message after completion

#### Polling Mechanism

Frontend polls the status endpoint every 2 seconds while batch is running:

```typescript
const pollBatchStatus = (taskId: string) => {
  const interval = setInterval(async () => {
    const response = await axios.get(`/api/tweets/batch-annotate/${taskId}/status`)
    setBatchProgress(response.data.progress)

    if (response.data.status === 'completed') {
      clearInterval(interval)
      setBatchAnnotating(false)
      fetchTweets()  // Refresh to show new tags
    }
  }, 2000)
}
```

## Duplicate Prevention

The system prevents duplicate tags at multiple levels:

1. **Pre-check Existing Concepts**: Before generating suggestions, the system retrieves all existing concept slugs for each tweet

2. **Slug Comparison**: New suggestions are compared by slug (case-insensitive) against existing concepts

3. **Batch-level Tracking**: Slugs added during the current batch are tracked to prevent duplicates within the same run

4. **Service-level Check**: `ConceptOnlyTagService.add_tag()` has its own internal duplicate prevention

## Model Support

The batch annotation supports all models configured in `litellm_config.yaml`:

| Frontend Name | Actual Model |
|---------------|--------------|
| claude-3.5-sonnet | claude-sonnet-4-20250514 |
| claude-sonnet-4.5 | claude-sonnet-4-5-20250929 |
| claude-opus-4.1 | claude-opus-4-1-20250805 |
| gpt-4o | gpt-4o |
| gpt-4o-mini | gpt-4o-mini |
| gemini-2.5-pro | gemini-2.5-pro |
| gemini-2.5-flash | gemini-2.5-flash |

## Performance Considerations

- **Sequential Processing**: Tweets are processed one at a time to respect LLM rate limits
- **Background Task**: Processing runs in FastAPI BackgroundTasks, non-blocking to the API
- **In-Memory State**: Task progress is stored in-memory (`batch_annotation_tasks` dict)
- **Progress Updates**: Updated after each tweet, polled by frontend every 2 seconds

## Limitations

1. **In-Memory State**: Task state is lost if server restarts during processing
2. **Single Server**: Not designed for distributed deployment (state not shared)
3. **Rate Limits**: Large batches may hit LLM API rate limits
4. **Page-Based**: Only annotates tweets currently loaded in the view (max 50 per page)

## Future Improvements

- Persist task state to MongoDB for crash recovery
- Add rate limiting/throttling for LLM calls
- Support annotating all matching tweets (not just current page)
- Add cancel/pause functionality
- Batch multiple tweets per LLM call for efficiency

## Usage Example

```bash
# 1. Start backend server
cd backend
python -m uvicorn app.main:app --reload --port 8000

# 2. Start frontend
cd frontend
npm run dev

# 3. Navigate to Twitter/X Feed
# 4. Filter to "Not Annotated" tweets
# 5. Select a model (e.g., "claude-3.5-sonnet")
# 6. Click "Batch Annotate"
# 7. Watch progress and results
```

## Related Files

| File | Purpose |
|------|---------|
| `backend/app/api/tweets_mongodb.py` | API endpoints and background processing |
| `backend/app/services/llm_manager.py` | LLM integration via LiteLLM |
| `backend/app/services/concept_only_tag_service.py` | Tag/concept management |
| `frontend/src/components/FacetedTweetsDashboardModern.tsx` | UI implementation |
| `frontend/src/components/UnifiedModelSelector.tsx` | Model selection component |

## Verification Checklist

- [ ] Filter tweets by author (e.g., @OpenAI)
- [ ] Select a model from dropdown
- [ ] Click "Batch Annotate"
- [ ] Progress bar advances to 100%
- [ ] Success message shows new tags count
- [ ] Tweets display newly added concepts
- [ ] Re-running on same tweets doesn't duplicate tags
