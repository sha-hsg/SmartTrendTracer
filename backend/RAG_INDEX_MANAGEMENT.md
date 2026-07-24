# RAG Index Management Guide

## Overview
The RAG (Retrieval-Augmented Generation) index powers the semantic search functionality in SmartTrendTracer. It uses either Google Gemini or OpenAI embeddings to create vector representations of tweets, articles, and snippets.

## How to Update the Index

### Method 1: Via API (Server Must Be Running)
```bash
# Force rebuild
curl -X POST http://localhost:8088/api/rag/rebuild
```

### Method 2: Direct Script (Server not required)
```bash
# Run the rebuild script directly (blocks until the index is written)
cd backend
python rebuild_rag_index.py
```

## When to Update the Index

The index should be updated when:
1. **New tweets collected** - After running tweet collection
2. **New articles added** - After Substack newsletter collection
3. **New snippets created** - After annotating articles
4. **Tags modified** - After bulk tagging or reorganization
5. **More than 24 hours old** - For freshness

## Index Storage

The index files are stored in:
```
backend/data/rag_index_concepts/
├── faiss.index            # Vector index (FAISS)
├── metadata.pkl           # Document metadata
├── doc_map.pkl            # Document text map
├── embeddings_cache.pkl   # Cached embeddings
└── index_info.json        # Index status/statistics
```

## Troubleshooting

### Index not updating?
1. Check server is running: `ps aux | grep uvicorn`
2. Verify API key is set: `echo $GOOGLE_API_KEY`
3. Check server logs: `tail -f server.log`
4. Try direct rebuild: `python rebuild_rag_index.py`

### Wrong embedding model?
- With Google API key: Uses Gemini (768 dimensions)
- With OpenAI API key: Uses OpenAI (1536 dimensions)
- Priority: Google > OpenAI

### Build taking too long?
- First build caches embeddings (~5-10 minutes)
- Subsequent builds use cache (much faster)
- Check progress in server logs

## API Endpoints

- `GET /api/rag/stats` - Current index status
- `POST /api/rag/rebuild` - Force complete rebuild
- `POST /api/rag/ask` - Ask a question against the index
- `GET /api/rag/health` - RAG service health check

## Monitoring

Check index health:
```bash
# Detailed API stats
curl http://localhost:8088/api/rag/stats | python -m json.tool
```
