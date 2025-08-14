# LLM Configuration Guide

## Configuration Files

### llm.json
Contains model configurations and API settings.

#### Model Configuration Parameters:

- **`model`**: The model identifier (e.g., "o1-mini", "gpt-4o-mini", "gpt-3.5-turbo")
- **`is_reasoning`**: Boolean flag for reasoning models (true for o1-mini, o1-preview)
- **`temperature`**: Creativity parameter (0.0-1.0) - only for non-reasoning models
- **`max_tokens`**: Maximum response length
- **`description`**: Human-readable description of the model's purpose

### Key Differences: Reasoning vs Standard Models

#### Reasoning Models (is_reasoning: true)
- Examples: o1-mini, o1-preview
- **No temperature parameter**
- **No system messages** - system prompt is combined with user prompt
- Better for complex reasoning tasks
- More expensive but higher quality

#### Standard Models (is_reasoning: false)
- Examples: gpt-4o-mini, gpt-3.5-turbo, claude-3
- **Uses temperature** for creativity control
- **Supports system messages** for better role definition
- Faster and cheaper
- Good for straightforward tasks

## Available Models

### For Tag Suggestions (default: o1-mini)
```json
"tag_suggestion": {
  "model": "o1-mini",
  "is_reasoning": true,
  "max_tokens": 500
}
```

Alternative options:
- `"gpt-4o-mini"` - Faster, cheaper, still good quality
- `"gpt-3.5-turbo"` - Most economical
- `"o1-preview"` - Best quality reasoning (more expensive)

### For Trend Analysis (default: gpt-4o-mini)
```json
"trend_analysis": {
  "model": "gpt-4o-mini",
  "is_reasoning": false,
  "temperature": 0.3,
  "max_tokens": 1000
}
```

## Switching Models

To switch from o1-mini to a cheaper model for tag suggestions:

```json
"tag_suggestion": {
  "model": "gpt-4o-mini",
  "is_reasoning": false,
  "temperature": 0.2,
  "max_tokens": 500
}
```

To use the most powerful reasoning model:

```json
"tag_suggestion": {
  "model": "o1-preview",
  "is_reasoning": true,
  "max_tokens": 1000
}
```

## Cost Comparison (Approximate)

| Model | Input Cost | Output Cost | Quality | Speed |
|-------|------------|-------------|---------|-------|
| o1-preview | $15/1M | $60/1M | ⭐⭐⭐⭐⭐ | Slow |
| o1-mini | $3/1M | $12/1M | ⭐⭐⭐⭐ | Medium |
| gpt-4o-mini | $0.15/1M | $0.60/1M | ⭐⭐⭐ | Fast |
| gpt-3.5-turbo | $0.50/1M | $1.50/1M | ⭐⭐ | Very Fast |

## Testing Different Models

1. Edit `llm.json` to change the model
2. Update `is_reasoning` flag accordingly
3. Run the test script:
   ```bash
   python test_tag_suggestions.py
   ```

## Environment Variables

Set in your `.env` file or environment:
```bash
OPENAI_API_KEY=your-api-key-here
OPENAI_ORG_ID=your-org-id-optional
```

## Prompts Configuration (prompts.json)

Customize the prompts for different tasks:
- `tag_suggestion`: How tags are generated
- `trend_classification`: How trends are analyzed
- `topic_extraction`: How topics are identified
- `sentiment_analysis`: How sentiment is determined

## Fallback Behavior

If the LLM API fails, the system will:
1. Use cached responses if available
2. Fall back to keyword extraction
3. Extract hashtags from tweets
4. Use predefined AI-related keywords

## Rate Limiting

The configuration includes:
- `rate_limit_per_minute`: 20 (adjustable)
- `cache_ttl_seconds`: 3600 (1 hour cache)
- `max_retries`: 3 attempts before fallback