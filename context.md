# SmartTrendTracer Context

## Recent Backend Updates
- Book uploads are now processed through a MongoDB-backed queue (`book_processing_jobs`).
- `/api/books/{id}/process` enqueues a job; the new worker (`backend/book_processing_worker.py`) must run alongside the API to drain the queue.
- `BookProcessorService` performs potentially long conversions using external services (Marker, MinerU, EPUB parser) in background threads.
- Queue documents track status (`queued`, `processing`, `completed`, `failed`) and are referenced from the corresponding book via `processing_job_id`.

## Running the Worker
```bash
cd backend
source venv/bin/activate  # if not already active
python book_processing_worker.py
```
- Set `BOOK_WORKER_IDLE_SECONDS` to control the poll interval (default 5 seconds).
- The worker handles SIGINT/SIGTERM gracefully and will finish the current job before exiting.

## Frontend Updates
- The Modern dashboard home view now includes a “Book Library” card that navigates to the books dashboard.
- Books in the UI show a `queued` status badge in addition to `pending`, `processing`, `completed`, and `failed`.
- The book viewer’s download helper respects Axios’ configured base URL instead of hard-coding `http://localhost:8000`.

## Deployment Notes
- Ensure MongoDB is reachable from both API and worker (default `mongodb://localhost:27017/`).
- Marker/MinerU endpoints are read from `MARKER_SERVICE_URL` and `MINERU_SERVICE_URL` environment variables.
- EPUB parsing requires `langchain-community` inside the backend virtual environment.

## Useful Paths
- Backend API: `backend/app/api/books_mongodb.py`
- Worker: `backend/book_processing_worker.py`
- Book processing service: `backend/app/services/book_processor_service.py`
- Frontend books dashboard: `frontend/src/components/FacetedBooksDashboard.tsx`
- Frontend main app shell: `frontend/src/ModernApp.tsx`

