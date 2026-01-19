"""
Async paper upload endpoint
"""
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, BackgroundTasks
from app.services.paper_service import PaperService
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/papers", tags=["papers-async"])

paper_service = PaperService()

def process_pdf_in_background(paper_id: int, pdf_path: str):
    """Background task to process PDF - runs in thread pool"""
    from ..services.pdf_processor_service import get_pdf_processor_service
    
    logger.info(f"Starting background processing for paper {paper_id}")
    
    try:
        # Use the regular PDF processor (it will use Marker service if available)
        pdf_processor = get_pdf_processor_service()
        result = pdf_processor.process_pdf(pdf_path)
        
        if result["success"]:
            # Update paper with processed content
            paper = db.query(Paper).filter(Paper.id == paper_id).first()
            if paper:
                paper.content = result["markdown"]
                paper.processed = True
                paper.processor_used = result.get("method_used", "unknown")
                # Extract better title/abstract if available
                if "metadata" in result:
                    metadata = result["metadata"]
                    if metadata.get("title"):
                        paper.title = metadata["title"]
                    if metadata.get("abstract"):
                        paper.abstract = metadata["abstract"]
                    if metadata.get("page_count"):
                        paper.page_count = metadata["page_count"]
                db.commit()
                logger.info(f"Successfully processed paper {paper_id} using {result.get('method_used')}")
            db.close()
        else:
            logger.error(f"Failed to process paper {paper_id}: {result.get('error')}")
            # Mark paper as failed
            paper = db.query(Paper).filter(Paper.id == paper_id).first()
            if paper:
                paper.processed = False
                paper.abstract = f"Processing failed: {result.get('error', 'Unknown error')}"
                db.commit()
            db.close()
    except Exception as e:
        logger.error(f"Error processing paper {paper_id}: {e}")
        # Mark paper as failed
        try:
            paper = db.query(Paper).filter(Paper.id == paper_id).first()
            if paper:
                paper.processed = False
                paper.abstract = f"Processing error: {str(e)}"
                db.commit()
            db.close()
        except:
            pass

@router.post("/upload-async")
async def upload_paper_async(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None,
):
    """Upload paper with true async processing"""
    
    # Validate file type
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    # Read and validate size
    contents = await file.read()
    if len(contents) > 50 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File size exceeds 50MB limit")
    
    try:
        # Save PDF file
        pdf_path = paper_service.save_pdf_file(contents, file.filename)
        
        # Create paper record with minimal info (instant response)
        paper = Paper(
            title=file.filename.replace('.pdf', ''),
            authors='Processing...',
            abstract='PDF is being processed in the background. This may take 1-2 minutes.',
            content='',
            pdf_path=pdf_path
        )
        db.add(paper)
        db.commit()
        db.refresh(paper)
        
        # Schedule background processing
        background_tasks.add_task(
            process_pdf_in_background,
            paper.id,
            pdf_path
        )
        
        # Return immediately
        return {
            "success": True,
            "paper_id": paper.id,
            "message": "Paper uploaded! Processing in background...",
            "filename": file.filename,
            "status": "processing"
        }
        
    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))