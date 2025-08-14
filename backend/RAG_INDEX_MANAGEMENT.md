# RAG Index Management Guide

## Overview
The RAG (Retrieval-Augmented Generation) index powers the semantic search functionality in SmartTrendTracer. It uses either Google Gemini or OpenAI embeddings to create vector representations of tweets, articles, and snippets.

## Current Status
- **Embedding Model**: Gemini (text-embedding-004) ✅
- **Documents Indexed**: 1,148
- **Index Ready**: Yes

## How to Update the Index

### Method 1: Quick Update Script (Recommended)
```bash
# Check current index status
python update_rag_index.py --status

# Update the index (tries API first, falls back to direct build)
python update_rag_index.py

# Force complete rebuild
python update_rag_index.py --force
```

### Method 2: Via API (Server Must Be Running)
```bash
# Incremental update
curl -X POST http://localhost:8000/api/rag/build

# Force rebuild
curl -X POST http://localhost:8000/api/rag/rebuild
```

### Method 3: Direct Script
```bash
# Run the build script directly
python build_rag_index.py
```

## When to Update the Index

The index should be updated when:
1. **New tweets collected** - After running tweet collection
2. **New articles added** - After Substack newsletter collection
3. **New snippets created** - After annotating articles
4. **Tags modified** - After bulk tagging or reorganization
5. **More than 24 hours old** - For freshness

## Automatic Updates

The system automatically attempts to update the index:
- On server startup (if index is missing or outdated)
- When accessing RAG search and index is not ready

## Index Storage

The index files are stored in:
```
backend/data/rag_index/
├── faiss_index.bin       # Vector index (FAISS)
├── metadata.pkl          # Document metadata
└── embeddings_cache.pkl  # Cached embeddings
```

## Troubleshooting

### Index not updating?
1. Check server is running: `ps aux | grep uvicorn`
2. Verify API key is set: `echo $GOOGLE_API_KEY`
3. Check server logs: `tail -f server.log`
4. Try direct build: `python build_rag_index.py`

### Wrong embedding model?
- With Google API key: Uses Gemini (768 dimensions)
- With OpenAI API key: Uses OpenAI (1536 dimensions)
- Priority: Google > OpenAI

### Build taking too long?
- First build caches embeddings (~5-10 minutes)
- Subsequent builds use cache (much faster)
- Check progress in server logs

## Performance Tips

1. **Use Gemini embeddings** (current setup) - Faster and cheaper
2. **Keep index updated** - Better search results
3. **Monitor index size** - Large indexes may need optimization
4. **Use incremental updates** - Faster than full rebuilds

## API Endpoints

- `GET /api/rag/stats` - Current index status
- `POST /api/rag/build` - Trigger index update
- `POST /api/rag/rebuild` - Force complete rebuild
- `POST /api/rag/search` - Search the index

## Example Search Query

```bash
curl -X POST http://localhost:8000/api/rag/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the latest AI trends?",
    "limit": 5
  }'
```

## Monitoring

Check index health:
```bash
# Quick status check
python update_rag_index.py --status

# Detailed API stats
curl http://localhost:8000/api/rag/stats | python -m json.tool

# Search test
curl -X POST http://localhost:8000/api/rag/search \
  -H "Content-Type: application/json" \
  -d '{"query": "test", "limit": 1}'
```