"""
Paper processing routes: Marker, MinerU, PDF extraction,
progress callbacks, and processing status/health endpoints.
"""

from app.services import pdf_service_client
from datetime import datetime, timezone
from typing import Any, Dict

from bson import ObjectId
from fastapi import APIRouter, BackgroundTasks, HTTPException, Request

from .utils import (
    db,
    logger,
    find_paper_by_id,
)
from .processing_helpers import (
    process_with_marker_background,
    process_with_mineru_background,
)

router = APIRouter()


# ---------------------------------------------------------------------------
# GET /{paper_id}/content
# ---------------------------------------------------------------------------

@router.get("/{paper_id}/content")
def get_paper_content(paper_id: str) -> Dict[str, Any]:
    """Get paper content (sections, references, etc.) from MongoDB"""
    paper = find_paper_by_id(paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    # Return content-specific fields
    return {
        'id': str(paper['_id']),
        'title': paper.get('title'),
        'content': paper.get('content', ''),
        'sections': paper.get('sections', []),
        'references': paper.get('references', []),
        'abstract': paper.get('abstract'),
        'pdf_path': paper.get('pdf_path')
    }


# ---------------------------------------------------------------------------
# POST /{paper_id}/process-with-marker
# ---------------------------------------------------------------------------

@router.post("/{paper_id}/process-with-marker")
async def process_paper_with_marker(paper_id: str, background_tasks: BackgroundTasks) -> Dict[str, Any]:
    """Start async processing of paper's PDF using Marker service"""

    logger.info(f"=== PROCESS WITH MARKER ENDPOINT CALLED ===")
    logger.info(f"Paper ID: {paper_id}")

    try:
        # Try to convert to ObjectId if it's a valid format
        if len(paper_id) == 24:
            paper = db.papers.find_one({'_id': ObjectId(paper_id)})
            logger.info(f"Found paper by ObjectId")
        else:
            # Try old SQLite ID
            paper = db.papers.find_one({'old_sqlite_id': int(paper_id)})
            logger.info(f"Found paper by old SQLite ID")
    except Exception as e:
        logger.error(f"Error finding paper: {e}")
        paper = None

    if not paper:
        logger.error(f"Paper not found: {paper_id}")
        raise HTTPException(status_code=404, detail="Paper not found")

    logger.info(f"Paper title: {paper.get('title', 'Unknown')}")

    pdf_path = paper.get('pdf_path')
    if not pdf_path:
        logger.error(f"No PDF path for paper {paper_id}")
        raise HTTPException(status_code=400, detail="No PDF path found for this paper")

    logger.info(f"PDF path: {pdf_path}")

    # Check if already processing
    current_status = paper.get('processing_status')
    logger.info(f"Current processing status: {current_status}")

    if current_status == 'processing_with_marker':
        logger.warning(f"Paper already being processed")
        return {
            'success': False,
            'message': 'Paper is already being processed with Marker',
            'status': 'processing'
        }

    # Check if file exists
    from pathlib import Path
    pdf_file = Path(pdf_path)
    if not pdf_file.exists():
        # Try relative to backend directory
        pdf_file = Path(__file__).resolve().parents[3] / pdf_path
        logger.info(f"Trying relative path: {pdf_file}")
        if not pdf_file.exists():
            logger.error(f"PDF file not found at: {pdf_file}")
            raise HTTPException(status_code=404, detail=f"PDF file not found: {pdf_path}")

    logger.info(f"PDF file found: {pdf_file}")
    logger.info(f"PDF file size: {pdf_file.stat().st_size} bytes")

    # Start background processing
    logger.info(f"=== ADDING BACKGROUND TASK ===")
    background_tasks.add_task(
        process_with_marker_background,
        str(paper['_id']),
        str(pdf_file)
    )
    logger.info(f"Background task added successfully")

    return {
        'success': True,
        'message': 'PDF processing with Marker has been started in the background',
        'status': 'processing',
        'paper_id': str(paper['_id']),
        'expected_time': 'Processing may take 10-15 minutes for complex papers'
    }


# ---------------------------------------------------------------------------
# POST /{paper_id}/cancel-processing
# ---------------------------------------------------------------------------

@router.post("/{paper_id}/cancel-processing")
async def cancel_processing(paper_id: str) -> Dict[str, Any]:
    """Cancel ongoing Marker/MinerU processing"""
    paper = find_paper_by_id(paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    current_status = paper.get('processing_status')
    if current_status not in ('processing_with_marker', 'processing_with_mineru'):
        return {
            'success': False,
            'message': 'Paper is not being processed',
            'status': current_status or 'not_started'
        }

    # Update status to cancelled (background tasks check this before their
    # final DB write and will not overwrite it)
    db.papers.update_one(
        {'_id': paper['_id']},
        {'$set': {
            'processing_status': 'cancelled',
            'processing_cancelled_at': datetime.now(timezone.utc)
        }}
    )

    # Kill the orphaned marker_single subprocess (same pattern as the
    # timeout handling in processing_helpers.py)
    if current_status == 'processing_with_marker':
        await pdf_service_client.kill_marker_job_async()

    return {
        'success': True,
        'message': 'Processing has been cancelled',
        'paper_id': str(paper['_id'])
    }


# ---------------------------------------------------------------------------
# GET /{paper_id}/processing-status
# ---------------------------------------------------------------------------

@router.get("/{paper_id}/processing-status")
async def get_processing_status(paper_id: str) -> Dict[str, Any]:
    """Check the processing status of a paper"""
    paper = find_paper_by_id(paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    status = paper.get('processing_status', 'not_started')
    response = {
        'paper_id': str(paper['_id']),
        'status': status,
        'processed': paper.get('processed', False),
        'processor_used': paper.get('processor_used'),
        'processed_at': paper.get('processed_at').isoformat() if paper.get('processed_at') else None
    }

    if status == 'processing_with_marker':
        started_at = paper.get('processing_started_at')
        if started_at:
            if isinstance(started_at, str):
                started_at = datetime.fromisoformat(started_at.replace('Z', '+00:00'))
            elif started_at.tzinfo is None:
                started_at = started_at.replace(tzinfo=timezone.utc)
            elapsed = (datetime.now(timezone.utc) - started_at).total_seconds()
            response['elapsed_seconds'] = elapsed
            response['elapsed_minutes'] = round(elapsed / 60, 1)

        # Include detailed progress information
        progress_data = paper.get('processing_progress')
        if progress_data:
            response['progress'] = progress_data
            # Extract current stage and progress percentage for easy access
            response['current_stage'] = progress_data.get('stage', 'processing')
            response['progress_message'] = progress_data.get('message', 'Processing...')
            response['progress_percentage'] = progress_data.get('progress', 0)

    if status == 'failed':
        response['error'] = paper.get('processing_error')

    if status == 'completed' and paper.get('marker_metadata'):
        response['marker_metadata'] = paper['marker_metadata']

    return response


# ---------------------------------------------------------------------------
# GET /{paper_id}/process-health
# ---------------------------------------------------------------------------

@router.get("/{paper_id}/process-health")
async def get_process_health(paper_id: str) -> Dict[str, Any]:
    """Get detailed process health information for currently running Marker process"""
    paper = find_paper_by_id(paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    status = paper.get('processing_status', 'not_started')

    # Only return health info if actively processing
    if status not in ['processing_with_marker', 'processing_with_mineru', 'processing_pdf']:
        return {
            'paper_id': str(paper['_id']),
            'status': status,
            'is_processing': False,
            'message': 'No active processing'
        }

    # Get process health data from MongoDB
    health_data = paper.get('marker_process_health', {})

    response = {
        'paper_id': str(paper['_id']),
        'status': status,
        'is_processing': True,
        'processor': paper.get('processor_used', 'marker'),
        'health': {
            'pid': health_data.get('pid'),
            'cpu_time': health_data.get('cpu_time', 0),
            'memory_mb': health_data.get('memory_mb', 0),
            'cpu_percent': health_data.get('cpu_percent', 0),
            'last_updated': health_data.get('last_updated').isoformat() if health_data.get('last_updated') else None,
            'output_files': health_data.get('output_files', {
                'markdown_exists': False,
                'image_count': 0
            })
        }
    }

    # Add elapsed time
    started_at = paper.get('processing_started_at')
    if started_at:
        if isinstance(started_at, str):
            started_at = datetime.fromisoformat(started_at.replace('Z', '+00:00'))
        elif started_at.tzinfo is None:
            started_at = started_at.replace(tzinfo=timezone.utc)
        elapsed = (datetime.now(timezone.utc) - started_at).total_seconds()
        response['elapsed_seconds'] = elapsed
        response['elapsed_minutes'] = round(elapsed / 60, 1)

    return response


# ---------------------------------------------------------------------------
# POST /{paper_id}/process
# ---------------------------------------------------------------------------

@router.post("/{paper_id}/process")
async def process_paper_pdf(paper_id: str, background_tasks: BackgroundTasks) -> Dict[str, Any]:
    """Process a paper's PDF to extract content"""
    paper = find_paper_by_id(paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    pdf_path = paper.get('pdf_path')
    if not pdf_path:
        raise HTTPException(status_code=400, detail="No PDF path found for this paper")

    # Check if file exists
    from pathlib import Path
    pdf_file = Path(pdf_path)
    if not pdf_file.exists():
        # Try relative to backend directory
        pdf_file = Path(__file__).resolve().parents[3] / pdf_path
        if not pdf_file.exists():
            raise HTTPException(status_code=404, detail=f"PDF file not found: {pdf_path}")

    # Process the PDF
    from ...services.pdf_processor_service import get_pdf_processor_service
    pdf_service = get_pdf_processor_service()

    logger.info(f"Processing PDF for paper {paper_id}: {pdf_path}")
    result = pdf_service.process_pdf(str(pdf_file), paper_id=str(paper['_id']))

    if result['success']:
        # Update paper with processed content
        # Note: pdf_processor_service returns 'markdown' not 'content'
        content = result.get('markdown', '') or result.get('content', '')
        update_data = {
            'content': content,
            'markdown_content': content,  # Store in both fields for compatibility
            'processed': True,
            'processor_used': result.get('method_used', 'unknown'),
            'processed_at': datetime.now(timezone.utc)
        }

        # Add metadata if available
        if result.get('metadata'):
            update_data['processing_metadata'] = result['metadata']
            # Store image count if extracted
            if result['metadata'].get('images_extracted'):
                update_data['images_extracted'] = result['metadata']['images_extracted']

        db.papers.update_one(
            {'_id': paper['_id']},
            {'$set': update_data}
        )

        return {
            'success': True,
            'message': f"Successfully processed PDF with {result.get('method_used', 'unknown')}",
            'content_length': len(content),
            'method_used': result.get('method_used', 'unknown'),
            'images_extracted': result.get('metadata', {}).get('images_extracted', 0)
        }
    else:
        raise HTTPException(status_code=500, detail=result.get('error', 'Failed to process PDF'))


# ---------------------------------------------------------------------------
# POST /{paper_id}/progress-callback
# ---------------------------------------------------------------------------

@router.post("/{paper_id}/progress-callback")
async def receive_marker_progress(
    paper_id: str,
    request: Request
) -> Dict[str, Any]:
    """Receive progress updates from Marker service during processing"""
    try:
        progress_data = await request.json()
        logger.info(f"Progress update for paper {paper_id}: {progress_data}")

        # Update paper with progress information
        paper = db.papers.find_one({'_id': ObjectId(paper_id) if len(paper_id) == 24 else paper_id})

        if not paper:
            raise HTTPException(status_code=404, detail="Paper not found")

        # Store progress in database
        progress_update = {
            'processing_progress': progress_data,
            'last_progress_update': datetime.now(timezone.utc)
        }

        # If health data is included in the progress update, store it separately
        if 'health' in progress_data:
            health_data = progress_data['health']
            health_data['last_updated'] = datetime.now(timezone.utc)
            progress_update['marker_process_health'] = health_data
            logger.info(f"Stored process health data: PID={health_data.get('pid')}, CPU={health_data.get('cpu_percent')}%, RAM={health_data.get('memory_mb')}MB")

        db.papers.update_one(
            {'_id': ObjectId(paper_id) if len(paper_id) == 24 else paper_id},
            {'$set': progress_update}
        )

        return {'success': True, 'message': 'Progress updated'}

    except Exception as e:
        logger.error(f"Failed to update progress for paper {paper_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update progress")


# ---------------------------------------------------------------------------
# POST /{paper_id}/process-with-mineru
# ---------------------------------------------------------------------------

@router.post("/{paper_id}/process-with-mineru")
async def process_paper_with_mineru(paper_id: str, background_tasks: BackgroundTasks) -> Dict[str, Any]:
    """Start async processing of paper's PDF using MinerU service"""

    try:
        # Try to convert to ObjectId if it's a valid format
        if len(paper_id) == 24:
            paper = db.papers.find_one({'_id': ObjectId(paper_id)})
        else:
            # Try old SQLite ID
            paper = db.papers.find_one({'old_sqlite_id': int(paper_id)})
    except Exception:
        paper = None

    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    # Check if already processing
    current_status = paper.get('processing_status')
    if current_status in ['processing_with_marker', 'processing_with_mineru', 'processing_pdf']:
        logger.warning(f"Paper already being processed")
        return {
            'success': False,
            'message': 'Paper is already being processed',
            'status': 'processing'
        }

    pdf_path = paper.get('pdf_path')
    if not pdf_path:
        raise HTTPException(status_code=400, detail="No PDF path found for this paper")

    # Check if file exists
    from pathlib import Path
    pdf_file = Path(pdf_path)
    if not pdf_file.exists():
        # Try relative to backend directory
        pdf_file = Path(__file__).resolve().parents[3] / pdf_path
        if not pdf_file.exists():
            raise HTTPException(status_code=404, detail=f"PDF file not found: {pdf_path}")

    logger.info(f"Starting MinerU processing for paper {paper_id}")

    # Set initial processing status
    db.papers.update_one(
        {'_id': paper['_id']},
        {'$set': {
            'processing_status': 'processing_with_mineru',
            'processing_started_at': datetime.now(timezone.utc)
        }}
    )

    # Add background task for MinerU processing
    background_tasks.add_task(process_with_mineru_background, paper_id, str(pdf_file))

    return {
        'success': True,
        'message': 'PDF processing with MinerU has been started in the background',
        'status': 'processing',
        'paper_id': paper_id,
        'expected_time': 'Processing may take 5-10 minutes depending on paper complexity'
    }
