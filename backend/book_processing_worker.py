#!/usr/bin/env python3
"""Standalone worker that processes queued book conversion jobs."""

import asyncio
import logging
import os
import signal
from datetime import datetime, timezone

from pymongo import MongoClient, ReturnDocument

from app.services.book_processor_service import BookProcessorService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("book_worker")

MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017/")
POLL_INTERVAL_SECONDS = float(os.getenv("BOOK_WORKER_IDLE_SECONDS", "5"))


class BookProcessingWorker:
    def __init__(self):
        self.client = MongoClient(MONGODB_URL)
        self.db = self.client.smarttrendtracer
        self.queue = self.db.book_processing_jobs
        self.books = self.db.books
        self.processor = BookProcessorService()
        self._shutdown = asyncio.Event()

    def request_shutdown(self, *_):
        logger.info("Shutdown signal received; finishing current job.")
        self._shutdown.set()

    async def run(self):
        while not self._shutdown.is_set():
            job = self._claim_job()
            if not job:
                try:
                    await asyncio.wait_for(self._shutdown.wait(), timeout=POLL_INTERVAL_SECONDS)
                except asyncio.TimeoutError:
                    continue
                else:
                    continue

            try:
                await self._process_job(job)
            except Exception as exc:
                logger.exception("Unexpected error while processing job %s", job.get("_id"))
                self._mark_job_failed(job, f"Worker error: {exc}")
            finally:
                await asyncio.sleep(0)

        self.client.close()
        logger.info("Worker stopped.")

    def _claim_job(self):
        return self.queue.find_one_and_update(
            {'status': 'queued'},
            {
                '$set': {
                    'status': 'processing',
                    'started_at': datetime.now(timezone.utc)
                },
                '$inc': {'attempts': 1}
            },
            sort=[('created_at', 1)],
            return_document=ReturnDocument.AFTER
        )

    async def _process_job(self, job):
        job_id = job['_id']
        book_id = job['book_id']
        logger.info("Processing book job %s for book %s", job_id, book_id)

        book = self.books.find_one({'_id': book_id})
        if not book:
            self._mark_job_failed(job, "Book not found")
            return

        file_path = book.get('file_path')
        if not file_path:
            self._mark_job_failed(job, "Book file path missing")
            self._update_book_failure(book_id, "No file path found")
            return

        if not os.path.exists(file_path):
            self._mark_job_failed(job, "Book file not found on disk")
            self._update_book_failure(book_id, "Book file missing on disk")
            return

        file_type = 'epub' if file_path.lower().endswith('.epub') else 'pdf'

        self.books.update_one(
            {'_id': book_id},
            {'$set': {
                'processing_status': 'processing',
                'processing_error': None,
                'processing_job_id': job_id,
                'updated_at': datetime.now(timezone.utc)
            }}
        )

        result = await self.processor.process_book(
            book_id=str(book_id),
            file_path=file_path,
            file_type=file_type,
            preferred_processor=job.get('preferred_processor', 'auto')
        )

        if result.get('success'):
            self._handle_success(job, result)
        else:
            error_message = result.get('error', 'Processing failed')
            self._mark_job_failed(job, error_message)
            self._update_book_failure(book_id, error_message, method=result.get('method_used'))

    def _handle_success(self, job, result):
        book_id = job['book_id']
        metadata = result.get('metadata', {})
        update_data = {
            'markdown_content': result.get('markdown', ''),
            'processing_metadata': metadata,
            'processing_method': result.get('method_used'),
            'processing_time': result.get('processing_time'),
            'images_extracted': result.get('images_extracted', False),
            'page_count': result.get('page_count'),
            'processing_status': 'completed',
            'processed_at': datetime.now(timezone.utc),
            'updated_at': datetime.now(timezone.utc),
            'processing_job_id': job['_id']
        }

        if 'table_of_contents' in metadata:
            update_data['table_of_contents'] = metadata['table_of_contents']
        if 'glossary_terms' in metadata:
            update_data['glossary_terms'] = metadata['glossary_terms']
        if 'reading_difficulty' in metadata:
            update_data['reading_difficulty'] = metadata['reading_difficulty']

        self.books.update_one(
            {'_id': book_id},
            {'$set': update_data}
        )

        self.queue.update_one(
            {'_id': job['_id']},
            {'$set': {
                'status': 'completed',
                'completed_at': datetime.now(timezone.utc),
                'last_error': None
            }}
        )

        logger.info("Book %s processed successfully with %s", book_id, result.get('method_used'))

    def _mark_job_failed(self, job, error_message):
        self.queue.update_one(
            {'_id': job['_id']},
            {'$set': {
                'status': 'failed',
                'completed_at': datetime.now(timezone.utc),
                'last_error': error_message
            }}
        )
        logger.error("Job %s failed: %s", job.get('_id'), error_message)

    def _update_book_failure(self, book_id, error_message, method=None):
        update = {
            'processing_status': 'failed',
            'processing_error': error_message,
            'updated_at': datetime.now(timezone.utc)
        }
        if method:
            update['processing_method'] = method
        self.books.update_one(
            {'_id': book_id},
            {'$set': update}
        )


def main():
    worker = BookProcessingWorker()
    loop = asyncio.get_event_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, worker.request_shutdown)

    try:
        loop.run_until_complete(worker.run())
    finally:
        loop.close()


if __name__ == "__main__":
    main()
