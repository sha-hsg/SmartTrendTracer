from app.repositories.papers import paper_filter as _paper_filter
from app.services import pdf_service_client
import os
import re
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from bson import ObjectId

from .utils import (
    db,
    logger,
    marker_semaphore,
    parse_marker_error,
    readability_service,
)
from app.repositories import papers_processing_helpers_queries as queries




def _processing_cancelled(paper_id: str) -> bool:
    """Check whether the user cancelled processing for this paper.

    Background tasks must call this before their final DB write so that a
    'cancelled' status set via POST /{paper_id}/cancel-processing is not
    overwritten with 'completed' or 'failed'.
    """
    doc = queries.papers_find_one___processing_cancelled(paper_id)
    return bool(doc and doc.get('processing_status') == 'cancelled')


async def process_with_marker_background(paper_id: str, pdf_path: str) -> None:
    """Background task to process PDF with Marker service"""
    import httpx
    from pathlib import Path
    import traceback

    logger.info(f"=== MARKER BACKGROUND TASK STARTED ===")
    logger.info(f"Paper ID: {paper_id}")
    logger.info(f"PDF Path: {pdf_path}")

    # Update status to processing
    queries.papers_update_one__process_with_marker_background(paper_id)
    logger.info(f"Updated paper status to 'processing_with_marker'")

    pdf_file = Path(pdf_path)
    if not pdf_file.exists():
        # Try relative to backend directory
        pdf_file = Path(__file__).parent.parent.parent / pdf_path
        logger.info(f"Using relative path: {pdf_file}")

    if not pdf_file.exists():
        error_msg = f"PDF file not found: {pdf_file}"
        logger.error(error_msg)
        queries.papers_update_one__process_with_marker_background_2(paper_id, error_msg)
        return

    logger.info(f"PDF file exists: {pdf_file} (size: {pdf_file.stat().st_size} bytes)")

    marker_url = pdf_service_client.marker_url("convert")
    logger.info(f"Marker URL: {marker_url}")

    try:
        # Test if Marker service is reachable
        logger.info("Testing Marker service connectivity...")
        async with httpx.AsyncClient(timeout=5.0) as test_client:
            try:
                health_response = await test_client.get(pdf_service_client.marker_url())
                logger.info(f"Marker service health check: {health_response.status_code}")
            except Exception as e:
                logger.error(f"Marker service not reachable: {e}")

        # Use semaphore to limit concurrent Marker processing
        logger.info("Acquiring Marker semaphore...")
        async with marker_semaphore:
            logger.info("Marker semaphore acquired. Starting processing...")
            # Use a very long timeout for Marker (3 hours to handle complex PDFs)
            logger.info("Opening PDF file for upload...")
            async with httpx.AsyncClient(timeout=10800.0) as client:
                with open(pdf_file, 'rb') as f:
                    file_content = f.read()
                    logger.info(f"Read PDF file: {len(file_content)} bytes")

                    files = {'file': (pdf_file.name, file_content, 'application/pdf')}

                # Add callback URL for progress updates
                callback_url = pdf_service_client.progress_callback_url(paper_id)

                # CRITICAL: Must send paper_id for Marker to save images!
                # Check if this paper already has an old_sqlite_id (shouldn't happen for new processing)
                # For new papers, we need to generate a stable integer ID
                # We'll use the MongoDB ObjectId to generate a unique integer
                if len(paper_id) == 24:
                    # MongoDB ObjectId - convert to a stable integer
                    # Use last 8 hex chars converted to int for uniqueness
                    paper_id_int = int(paper_id[-8:], 16)
                else:
                    # Already an integer ID
                    paper_id_int = int(paper_id)

                data = {
                    'output_format': 'markdown',
                    'extract_images': 'true',
                    'debug': 'true',  # Enable debug for more info
                    'rewrite_to_files': 'false',
                    'paper_id': paper_id_int,  # CRITICAL: Must include paper_id for image saving!
                    'callback_url': callback_url  # Progress callback URL
                }

                logger.info(f"=== SENDING REQUEST TO MARKER ===")
                logger.info(f"File name: {pdf_file.name}")
                logger.info(f"File size: {len(file_content)} bytes")
                logger.info(f"Data params: {data}")

                response = await client.post(marker_url, files=files, data=data)
                logger.info(f"Marker response status: {response.status_code}")

                if response.status_code == 200:
                    logger.info(f"=== MARKER SUCCESS RESPONSE ===")
                    result = response.json()
                    logger.info(f"Response keys: {result.keys() if isinstance(result, dict) else 'not a dict'}")
                    logger.info(f"Content length: {len(result.get('content', ''))} chars")
                    logger.info(f"Image count: {result.get('image_count', 0)}")
                    logger.info(f"Processing time: {result.get('elapsed', 0)} seconds")

                    # Update paper with processed content
                    # Extract the kept_dir from debug info to know where images are stored
                    debug_info = result.get('_debug', {})
                    kept_dir = debug_info.get('kept_dir', '')

                    # Extract just the session ID from the full path
                    # e.g., from "/path/to/marker_service/debug_runs/marker_cli_oyismanp/arxiv_2505.15105"
                    # we want "marker_cli_oyismanp"
                    marker_session_id = None
                    if kept_dir:
                        import re
                        match = re.search(r'(marker_cli_[^/]+)', kept_dir)
                        if match:
                            marker_session_id = match.group(1)

                    # Calculate readability metrics for the processed content
                    readability_metrics = {}
                    content = result.get('content', '')
                    if content:
                        try:
                            readability_metrics = readability_service.get_readability_metrics(content)
                            logger.info(f"Calculated readability: {readability_metrics.get('difficulty', 'Unknown')}")
                        except Exception as e:
                            logger.warning(f"Could not calculate readability: {e}")

                    update_data = {
                        'content': content,  # Fixed: Marker returns 'content', not 'markdown'
                        'processed': True,
                        'processor_used': 'marker_service',
                        'processed_at': datetime.now(timezone.utc),
                        'processing_status': 'completed',
                        'readability': readability_metrics,  # Store readability scores
                        'marker_metadata': {
                            'method': result.get('method', 'marker'),
                            'image_count': result.get('image_count', 0),
                            'processing_time': result.get('elapsed', 0),
                            'images': result.get('images', []),
                            'kept_dir': kept_dir,
                            'session_id': marker_session_id
                        }
                    }

                    if _processing_cancelled(paper_id):
                        logger.info(f"Processing was cancelled for paper {paper_id}; skipping final update")
                        return

                    queries.papers_update_one__process_with_marker_background_6(paper_id, update_data)
                    logger.info(f"=== SUCCESSFULLY UPDATED PAPER {paper_id} ===")
                else:
                    error_text = response.text
                    logger.error(f"=== MARKER ERROR RESPONSE ===")
                    logger.error(f"Status code: {response.status_code}")
                    logger.error(f"Error text (first 500 chars): {error_text[:500]}")

                    # Parse error to get user-friendly message
                    user_error = parse_marker_error(error_text)

                    if _processing_cancelled(paper_id):
                        logger.info(f"Processing was cancelled for paper {paper_id}; keeping 'cancelled' status")
                        return

                    queries.papers_update_one__process_with_marker_background_7(paper_id, user_error)
    except httpx.TimeoutException as e:
        error_msg = f"Marker service timeout after 3 hours"
        logger.error(f"=== MARKER TIMEOUT ===")
        logger.error(error_msg)
        if not _processing_cancelled(paper_id):
            queries.papers_update_one__process_with_marker_background_3(paper_id, error_msg)
        # Kill orphaned marker_single subprocess
        pdf_service_client.kill_marker_job()
    except httpx.RequestError as e:
        error_msg = f"Marker service connection error: {str(e)}"
        logger.error(f"=== MARKER CONNECTION ERROR ===")
        logger.error(error_msg)
        if not _processing_cancelled(paper_id):
            queries.papers_update_one__process_with_marker_background_4(paper_id, error_msg)
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        logger.error(f"=== MARKER UNEXPECTED ERROR ===")
        logger.error(error_msg)
        logger.error(f"Traceback: {traceback.format_exc()}")
        if not _processing_cancelled(paper_id):
            queries.papers_update_one__process_with_marker_background_5(paper_id, error_msg)


async def process_with_mineru_background(paper_id: str, pdf_path: str) -> None:
    """Background task to process PDF with MinerU service"""
    logger.info(f"=== MINERU BACKGROUND TASK STARTED ===")
    logger.info(f"Paper ID: {paper_id}")
    logger.info(f"PDF Path: {pdf_path}")

    try:
        # Update paper with current timestamp
        queries.papers_update_one__process_with_mineru_background(paper_id)
        logger.info("Updated paper status to 'processing_with_mineru'")

        # Convert MongoDB ObjectId to integer for MinerU image saving
        mongo_id = paper_id  # Keep the original MongoDB ID for URLs
        if len(paper_id) == 24:
            # MongoDB ObjectId - convert to a stable integer
            # Use last 8 hex chars converted to int for uniqueness
            paper_id_int = int(paper_id[-8:], 16)
            logger.info(f"Converted MongoDB ID {paper_id} to integer {paper_id_int} for MinerU")
        else:
            # Already an integer ID
            paper_id_int = int(paper_id)

        # Use the PDF processor service with MinerU preference
        from ...services.pdf_processor_service import get_pdf_processor_service
        pdf_service = get_pdf_processor_service()

        # Pass both the integer ID for file storage and MongoDB ID for callback URL
        logger.info(f"Processing PDF with MinerU service, paper_id_int={paper_id_int}, mongo_id={mongo_id}")
        result = pdf_service.process_pdf(
            pdf_path,
            prefer_method='mineru',
            paper_id=paper_id_int,
            mongo_paper_id=mongo_id  # Pass MongoDB ID for callback URL
        )

        if result['success'] and result.get('markdown'):
            logger.info(f"=== MINERU SUCCESS ===")
            logger.info(f"Content length: {len(result['markdown'])} chars")

            # Fix image URLs in markdown to use MongoDB ID instead of converted integer
            content = result['markdown']
            if len(paper_id) == 24:
                # Replace image URLs that use the converted integer with the MongoDB ID
                content = content.replace(f'/api/papers/{paper_id_int}/images/', f'/api/papers/{mongo_id}/images/')
                logger.info(f"Fixed image URLs: {paper_id_int} -> {mongo_id}")

            # Calculate readability metrics for the processed content
            readability_metrics = {}
            try:
                readability_metrics = readability_service.get_readability_metrics(content)
                logger.info(f"Calculated readability: {readability_metrics.get('difficulty', 'Unknown')}")
            except Exception as e:
                logger.warning(f"Could not calculate readability: {e}")

            # Update paper with processed content
            update_data = {
                'content': content,  # Fixed: use 'content' field
                'processed': True,
                'processor_used': 'mineru_service',
                'processed_at': datetime.now(timezone.utc),
                'processing_status': 'completed',
                'readability': readability_metrics  # Store readability scores
            }

            # Store metadata if available
            if result.get('metadata'):
                update_data['mineru_metadata'] = result['metadata']
                logger.info(f"MinerU metadata: {result['metadata']}")

            if _processing_cancelled(paper_id):
                logger.info(f"Processing was cancelled for paper {paper_id}; skipping final update")
                return

            queries.papers_update_one__process_with_mineru_background_2(paper_id, update_data)
            logger.info(f"=== SUCCESSFULLY UPDATED PAPER {paper_id} ===")
        else:
            error_msg = result.get('error', 'MinerU processing failed')
            logger.error(f"=== MINERU ERROR ===")
            logger.error(error_msg)

            if _processing_cancelled(paper_id):
                logger.info(f"Processing was cancelled for paper {paper_id}; keeping 'cancelled' status")
                return

            queries.papers_update_one__process_with_mineru_background_3(paper_id, error_msg)
    except Exception as e:
        error_msg = f"MinerU service error: {str(e)}"
        logger.error(f"=== MINERU EXCEPTION ===")
        logger.error(error_msg)
        if not _processing_cancelled(paper_id):
            queries.papers_update_one__process_with_mineru_background_4(paper_id, error_msg)
