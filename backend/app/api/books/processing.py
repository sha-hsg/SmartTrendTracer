"""
Book processing endpoints: queue-based and direct processing.
"""

from fastapi import APIRouter

from .utils import HTTPException, ObjectId, datetime, timezone, logger, db, get_book_by_id
from app.repositories import books_processing as repo
from app.repositories import books_processing_queries as queries

router = APIRouter()


@router.post("/{book_id}/process")
async def trigger_book_processing(
    book_id: str,
    preferred_processor: str = "auto"
):
    """Enqueue book processing job for asynchronous worker"""
    return repo.trigger_book_processing(book_id=book_id, preferred_processor=preferred_processor)

@router.post("/{book_id}/process-direct")
async def process_book_direct(
    book_id: str,
    preferred_processor: str = "auto"  # "auto", "marker", "mineru", "epub_native"
):
    """
    Process book content directly (synchronous) - use for immediate processing
    WARNING: Can take 1-6 hours for large books, client timeout recommended
    """
    book = get_book_by_id(book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    if not book.get("file_path"):
        raise HTTPException(status_code=400, detail="Book file not found")

    if book.get('processing_status') == 'processing':
        raise HTTPException(status_code=400, detail="Book is already being processed")

    # Update status to processing
    queries.books_update_one__process_book_direct(book_id)

    try:
        # Import and use BookProcessorService
        from app.services.book_processor_service import BookProcessorService
        processor = BookProcessorService()

        # Determine file type from extension
        file_path = book["file_path"]
        file_type = "epub" if file_path.lower().endswith('.epub') else "pdf"

        logger.info(f"Direct processing book {book_id} ({file_type}) with {preferred_processor}")

        # Process the book
        result = await processor.process_book(
            book_id=book_id,
            file_path=file_path,
            file_type=file_type,
            preferred_processor=preferred_processor
        )

        if result["success"]:
            # Update book document with extracted content and metadata
            update_data = {
                "markdown_content": result["markdown"],
                "processing_metadata": result.get("metadata", {}),
                "processing_method": result["method_used"],
                "processing_time": result.get("processing_time"),
                "images_extracted": result.get("images_extracted", False),
                "page_count": result.get("page_count"),
                "processing_status": "completed",
                "processed_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
                "processing_job_id": None
            }

            # Extract book-specific metadata if available
            metadata = result.get("metadata", {})
            if "table_of_contents" in metadata:
                update_data["table_of_contents"] = metadata["table_of_contents"]

            if "glossary_terms" in metadata:
                update_data["glossary_terms"] = metadata["glossary_terms"]

            if "reading_difficulty" in metadata:
                update_data["reading_difficulty"] = metadata["reading_difficulty"]

            # Update the book document
            queries.books_update_one__process_book_direct_2(update_data, book_id)

            logger.info(f"Book {book_id} processed successfully with {result['method_used']}")

            return {
                "status": "completed",
                "message": f"Book processed successfully using {result['method_used']}",
                "book_id": book_id,
                "processor": result["method_used"],
                "markdown_length": len(result["markdown"]),
                "processing_time": result.get("processing_time"),
                "images_extracted": result.get("images_extracted", False),
                "has_toc": "table_of_contents" in metadata,
                "has_glossary": "glossary_terms" in metadata,
                "reading_difficulty": metadata.get("reading_difficulty")
            }
        else:
            # Update book with error status
            queries.books_update_one__process_book_direct_3(book_id, result)

            logger.error(f"Book {book_id} processing failed: {result.get('error')}")

            raise HTTPException(
                status_code=500,
                detail=f"Processing failed: {result.get('error', 'Unknown error')}"
            )

    except Exception as e:
        logger.error(f"Error processing book {book_id}: {e}")
        # Update book with error status
        queries.books_update_one__process_book_direct_4(book_id, e)
        raise HTTPException(status_code=500, detail=str(e))
