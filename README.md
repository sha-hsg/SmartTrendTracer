# SmartTrendTracer

SmartTrendTracer is an AI-first content intelligence platform that unifies trends from Twitter/X, Substack newsletters, research papers, and long-form books. The system pairs a MongoDB-backed FastAPI service with a modern React frontend and dedicated document processing workers (Marker, MinerU, EPUB parsing) to keep pace with rapidly evolving AI conversations.

## Platform Highlights
- **Multi-source ingestion** – Twitter collector with tiered rate limiting, Gmail+forwarder Substack importers, research paper pipeline, and the new book library for PDF/EPUB content.
- **Unified knowledge graph** – Concept-only tagging system backed by MongoDB collections (`tag_concepts_v2`, `tag_instances`, `tag_aliases_v2`) powers filtering, analytics, and ontology views.
- **Document intelligence** – Marker/MinerU processors plus native EPUB extraction provide table of contents, glossary detection, reading difficulty, and chunked rendering for large artifacts.
- **Trend analytics** – Unified trends, article clustering, RAG endpoints, and media galleries surface what is emerging, peaking, or fading across sources.

## Architecture Overview
```
SmartTrendTracer/
├── backend/
│   ├── app/
│   │   ├── api/                # FastAPI routers (tweets_mongodb, books_mongodb, trends, etc.)
│   │   ├── services/           # Processing services (book_processor_service, async_pdf_processor, etc.)
│   │   ├── utils/, jobs/, ...  # Supporting logic
│   │   └── main.py             # FastAPI application (MongoDB-only)
│   ├── collect_*.py            # Twitter/Substack/Gmail collectors and utilities
│   ├── migrations/, logs/, ...
│   └── venv/ (optional virtualenv)
│
├── frontend/
│   ├── src/components/         # React components (ModernNavigation, FacetedBooksDashboard, viewers)
│   ├── src/lib/                # API helpers, state stores
│   └── package.json            # Vite-based toolchain
│
├── data/
│   └── book_repository/, paper_repository/   # Extracted artifacts and originals
└── documentation/*.md           # Deep dive feature docs, setup guides, system analyses
```

## Prerequisites
- **Python 3.11+** with virtualenv support.
- **MongoDB 6+** running locally on `mongodb://localhost:27017/` (default) or configure `MONGODB_URL`.
- **Node.js 18+ / npm** for the React frontend.
- **Optional external services**: Marker (`MARKER_SERVICE_URL`), MinerU (`MINERU_SERVICE_URL`), Gmail API credentials, LangChain community package for EPUB parsing.

## Quick Start
1. **Backend**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt

   cp .env.example .env
   # Edit .env: Mongo connection, Twitter keys, Gmail settings, service URLs, OpenAI/Claude keys, etc.

   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```
   API docs: http://localhost:8000/docs • Health check: http://localhost:8000/health

2. **Book Processing Worker**
   ```bash
   cd backend
   # Assuming the backend virtualenv is active
   python book_processing_worker.py
   ```
   The worker polls the `book_processing_jobs` queue and executes conversions via Marker/MinerU/EPUB processing. Keep it running alongside the API when books are being uploaded.

3. **Frontend**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```
   UI served at http://localhost:3000 (Modern Navigation exposes Books, Papers, Tweets, Substack, Analytics).

## Configuration Notes
- **MongoDB** – Collections are created automatically on startup. Ensure indexes from `app/main.py` can be applied to your instance.
- **Book processing** – Configure `MARKER_SERVICE_URL`, `MINERU_SERVICE_URL`, and (optionally) install `langchain-community` in the backend venv for EPUB support. Uploads land in `data/book_repository/{book_id}` with sanitized filenames.
- **Book worker** – Conversion requests are enqueued in `book_processing_jobs` and executed by `backend/book_processing_worker.py`. Run at least one worker alongside the API to drain the queue (scale horizontally for throughput).
- **Frontend API base** – Axios is configured to hit `/api/...` during dev; Vite proxy rules forward to the backend. When deploying, align `VITE_API_BASE_URL` (if defined) with your API gateway.

## Key Workflows
- **Books** – Upload via “Book Library → Upload Book”, then trigger `Process` to convert to markdown. Faceted dashboard supports filtering by author, publisher, concept, genre, difficulty, processor, etc. Large documents stream via virtualized viewer.
- **Tweets** – `backend/tweet_collector_service.py` schedules tiered pulls with MongoDB persistence. Use `collect_all_with_retweets.py` or `collect_twscrape.py` for specialty imports.
- **Substack** – Gmail/forwarded pipelines normalize newsletters into MongoDB; see `SUBSTACK_SETUP.md` and `ENHANCED_IMPORT_GUIDE.md` for OAuth + filtering steps.
- **Concepts** – Concept-only tagging ensures consistent ontology usage. Utilities in `backend/analyze_*` and `tag_reorganization_*` help curate hierarchies.

## Additional Documentation
Extensive deep-dive notes live alongside the codebase:
- `CLAUDE.md` – running change log and feature index (large file).
- `API_DOCUMENTATION.md` – endpoint reference.
- `FACETED_BROWSING_GUIDE.md`, `PDF_PAPERS_IMPLEMENTATION_PLAN.md`, `TAG_SYSTEM_V2_DOCUMENTATION.md`, etc. for feature-specific guidance.

## Contributing Tips
- Prefer enhancing existing services instead of creating parallel stacks.
- Keep filenames ASCII; sanitize any user input before writing to disk.
- For long-running jobs, lean on the built-in book processing queue/worker pattern before introducing new infrastructure.
- Run targeted scripts/tests in `backend/test_*.py` when adjusting collectors or processors.

---

Happy trend tracing! EOF
