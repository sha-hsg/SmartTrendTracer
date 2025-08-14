# Article Tag Suggestion Enhancements

## Overview
Enhanced the tag suggestion system for Substack articles to handle longer content and provide more comprehensive tagging compared to tweets.

## Key Improvements

### 1. Content Analysis
**Articles now use significantly more content for tag generation:**
- **Primary content**: Up to 5,000 characters (vs 500 for tweets)
- **Middle section**: Additional 1,000 chars from middle for long articles
- **Conclusion**: Last 1,000 chars to capture summary points
- **Total analysis**: Up to 7,000 characters for comprehensive understanding

### 2. Tag Quantity
**Articles receive more tags due to their richer content:**
- **LLM-generated tags**: Up to 10 tags (vs 5 for tweets)
- **Similar existing tags**: Up to 10 tags (vs 5 for tweets)
- **Total potential**: 20 tags per article

### 3. Similarity Thresholds
**Adjusted for longer, more diverse content:**
- **Similarity threshold**: 0.40 for articles (vs 0.45-0.50 for tweets)
- **Candidate pool**: Search 15 similar tags (vs 8 for tweets)

## Implementation Details

### New LLM Method: `suggest_article_tags()`
Located in `/app/services/llm_service.py`

```python
def suggest_article_tags(
    article_text: str, 
    author: str, 
    max_tags: int = 10
) -> List[str]
```

**Features:**
- Optimized prompt for long-form content
- Handles up to 8,000 chars for LLM processing
- Generates specific, descriptive tags
- Captures main topics, concepts, arguments, and content type

### Enhanced API Endpoint
Located in `/app/api/enhanced_substack.py`

**Endpoint**: `POST /api/v2/substack/articles/{article_id}/suggest-tags`

**Response includes:**
- `existing_suggestions`: Up to 10 semantically similar existing tags
- `new_suggestions`: Up to 10 AI-generated new tags
- `already_tagged`: Tags already applied to the article
- `model_used`: LLM model used (GPT-4o-mini by default)

## Usage Examples

### API Request
```bash
POST /api/v2/substack/articles/123/suggest-tags
```

### Response
```json
{
  "article_id": 123,
  "existing_suggestions": [
    {"tag": "machine-learning", "score": 0.72, "usage_count": 45, "type": "existing"},
    {"tag": "neural-networks", "score": 0.68, "usage_count": 32, "type": "existing"},
    // ... up to 10 tags
  ],
  "new_suggestions": [
    {"tag": "transformer-architecture", "type": "new", "model": "gpt-4o-mini"},
    {"tag": "technical-tutorial", "type": "new", "model": "gpt-4o-mini"},
    // ... up to 10 tags
  ],
  "already_tagged": ["ai", "deep-learning"],
  "model_used": "gpt-4o-mini",
  "total_suggestions": 20
}
```

## Benefits

1. **Better Coverage**: Articles get more comprehensive tagging reflecting their depth
2. **Content-Aware**: Uses beginning, middle, and end sections for full understanding
3. **Scalable**: Handles articles of any length efficiently
4. **Normalized**: All tags are automatically normalized for consistency

## Testing

Run the test script to verify the enhancements:
```bash
python test_article_tags.py
```

This will test:
- Old vs new tag generation methods
- Different max_tags values (5, 7, 10, 15)
- Vector similarity search with various k values
- Content preparation strategies