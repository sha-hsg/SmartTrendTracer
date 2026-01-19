"""
Paper Repository API endpoints
Handles paper analyses and repository management
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import logging
from sqlalchemy.orm import Session

from ..models import get_db
from ..models.papers import Paper, PaperAnalysis
from ..models.paper_analysis import AnalysisPrompt, PaperRepository
from ..services.paper_repository_service import get_repository_service
from ..services.arxiv_import_service import get_arxiv_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/papers/repository", tags=["paper-repository"])

class GenerateAnalysisRequest(BaseModel):
    """Request to generate an analysis"""
    paper_id: int
    analysis_types: List[str] = Field(..., description="List of analysis types to generate")
    regenerate: bool = Field(False, description="Regenerate existing analyses")

class CustomAnalysisRequest(BaseModel):
    """Request for custom analysis"""
    paper_id: int
    prompt: str = Field(..., min_length=10, description="Custom analysis prompt")
    name: str = Field("Custom Analysis", description="Name for this analysis")

class CompareAnalysisRequest(BaseModel):
    """Request to compare analyses across papers"""
    paper_ids: List[int] = Field(..., min_items=2, description="Papers to compare")
    analysis_type: str = Field(..., description="Type of analysis to compare")

class ImportWithAnalysisRequest(BaseModel):
    """Import paper from ArXiv with analyses"""
    arxiv_id: str
    generate_analyses: List[str] = Field(
        default=["summary", "key_contributions", "limitations"],
        description="Analyses to generate after import"
    )

@router.get("/prompts")
async def get_available_prompts(db: Session = Depends(get_db)):
    """Get all available analysis prompts"""
    try:
        prompts = db.query(AnalysisPrompt).filter(
            AnalysisPrompt.is_active == True
        ).order_by(AnalysisPrompt.display_order).all()
        
        return {
            'prompts': [
                {
                    'key': p.prompt_key,
                    'name': p.prompt_name,
                    'description': p.description,
                    'icon': p.icon,
                    'color': p.color,
                    'category': p.category,
                    'is_fixed': p.is_fixed
                }
                for p in prompts
            ]
        }
    except Exception as e:
        logger.error(f"Failed to get prompts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate-analyses")
async def generate_analyses(
    request: GenerateAnalysisRequest,
    background_tasks: BackgroundTasks
):
    """Generate multiple analyses for a paper"""
    repository_service = get_repository_service()
    
    results = []
    for analysis_type in request.analysis_types:
        try:
            # Check if analysis exists and skip if not regenerating
            if not request.regenerate:
                db = next(get_db())
                existing = db.query(PaperAnalysis).filter(
                    PaperAnalysis.paper_id == request.paper_id,
                    PaperAnalysis.analysis_type == analysis_type,
                    PaperAnalysis.is_latest == True
                ).first()
                db.close()
                
                if existing:
                    results.append({
                        'analysis_type': analysis_type,
                        'status': 'exists',
                        'analysis_id': existing.id
                    })
                    continue
            
            # Generate analysis
            analysis_id = repository_service.generate_analysis(
                paper_id=request.paper_id,
                analysis_type=analysis_type
            )
            
            if analysis_id:
                results.append({
                    'analysis_type': analysis_type,
                    'status': 'generated',
                    'analysis_id': analysis_id
                })
            else:
                results.append({
                    'analysis_type': analysis_type,
                    'status': 'failed',
                    'error': 'Generation failed'
                })
                
        except Exception as e:
            logger.error(f"Failed to generate {analysis_type}: {e}")
            results.append({
                'analysis_type': analysis_type,
                'status': 'error',
                'error': str(e)
            })
    
    return {
        'paper_id': request.paper_id,
        'results': results,
        'summary': {
            'requested': len(request.analysis_types),
            'generated': len([r for r in results if r['status'] == 'generated']),
            'existing': len([r for r in results if r['status'] == 'exists']),
            'failed': len([r for r in results if r['status'] in ['failed', 'error']])
        }
    }

@router.post("/custom-analysis")
async def generate_custom_analysis(request: CustomAnalysisRequest):
    """Generate a custom analysis with user-provided prompt"""
    repository_service = get_repository_service()
    
    try:
        analysis_id = repository_service.generate_analysis(
            paper_id=request.paper_id,
            analysis_type="custom",
            custom_prompt=request.prompt
        )
        
        if analysis_id:
            return {
                'success': True,
                'analysis_id': analysis_id,
                'message': 'Custom analysis generated successfully'
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to generate custom analysis")
            
    except Exception as e:
        logger.error(f"Failed to generate custom analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{paper_id}/analyses")
async def get_paper_analyses(paper_id: int):
    """Get all analyses for a paper"""
    repository_service = get_repository_service()
    
    try:
        analyses = repository_service.get_paper_analyses(paper_id)
        
        # Group analyses by type for better UI organization
        grouped = {}
        for analysis in analyses:
            analysis_type = analysis['type']
            if analysis_type not in grouped:
                grouped[analysis_type] = []
            grouped[analysis_type].append(analysis)
        
        return {
            'paper_id': paper_id,
            'analyses': analyses,
            'grouped': grouped,
            'total': len(analyses)
        }
        
    except Exception as e:
        logger.error(f"Failed to get analyses: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{paper_id}/analysis/{analysis_type}")
async def get_specific_analysis(
    paper_id: int,
    analysis_type: str,
    db: Session = Depends(get_db)
):
    """Get a specific analysis for a paper"""
    try:
        analysis = db.query(PaperAnalysis).filter(
            PaperAnalysis.paper_id == paper_id,
            PaperAnalysis.analysis_type == analysis_type,
            PaperAnalysis.is_latest == True
        ).first()
        
        if not analysis:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        return {
            'id': analysis.id,
            'paper_id': paper_id,
            'type': analysis.analysis_type,
            'name': analysis.analysis_name,
            'content': analysis.content,
            'model': analysis.model_used,
            'word_count': analysis.word_count,
            'created_at': analysis.created_at.isoformat() if analysis.created_at else None,
            'user_rating': analysis.user_rating,
            'user_notes': analysis.user_notes
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/compare")
async def compare_paper_analyses(request: CompareAnalysisRequest):
    """Compare analyses across multiple papers"""
    repository_service = get_repository_service()
    
    try:
        comparison = repository_service.compare_papers(
            paper_ids=request.paper_ids,
            analysis_type=request.analysis_type
        )
        
        if comparison:
            return {
                'success': True,
                'comparison': comparison
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to generate comparison")
            
    except Exception as e:
        logger.error(f"Failed to compare papers: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def _process_paper_in_background(
    paper_id: int,
    pdf_path: str,
    generate_analyses: List[str]
):
    """Background task to process PDF and generate analyses asynchronously"""
    from datetime import datetime
    from ..models import get_db
    from ..models.papers import Paper
    from ..models.paper_analysis import PaperRepository
    from ..services.async_pdf_processor import get_async_pdf_processor
    from ..services.paper_repository_service import get_repository_service
    
    logger.info(f"Background processing started for paper {paper_id}")
    
    try:
        # Use async PDF processor to avoid blocking
        async_processor = get_async_pdf_processor()
        
        # Process PDF asynchronously with paper_id for image extraction
        logger.info(f"Processing PDF asynchronously for paper {paper_id}...")
        result = await async_processor.process_pdf_async(pdf_path, paper_id=paper_id)
        
        if result["success"]:
            # Update repository with processed content
            db = next(get_db())
            
            # Update the paper's processed status
            paper = db.query(Paper).filter(Paper.id == paper_id).first()
            if paper:
                paper.content = result["markdown"]
                paper.processed = True
                paper.processor_used = result.get("method_used", "unknown")
                db.commit()
                logger.info(f"Updated paper {paper_id} with processed content")
            
            repo = db.query(PaperRepository).filter(
                PaperRepository.paper_id == paper_id
            ).first()
            
            if repo:
                # Save markdown content
                from pathlib import Path
                markdown_dir = Path("data/paper_repository/markdown")
                markdown_dir.mkdir(parents=True, exist_ok=True)
                
                markdown_path = markdown_dir / f"paper_{paper_id}.md"
                with open(markdown_path, 'w', encoding='utf-8') as f:
                    f.write(result["markdown"])
                
                # Update repository record
                repo.markdown_path = str(markdown_path)
                repo.pdf_processed = True
                repo.markdown_generated = True
                repo.processed_at = datetime.utcnow()
                repo.processor_used = result.get("method_used", "unknown")
                
                db.commit()
                logger.info(f"PDF processed successfully for paper {paper_id}")
            
            db.close()
            
            # Generate analyses if requested
            if generate_analyses:
                repository_service = get_repository_service()
                logger.info(f"Generating {len(generate_analyses)} analyses for paper {paper_id}...")
                
                for analysis_type in generate_analyses:
                    try:
                        # This can also be made async if needed
                        repository_service.generate_analysis(
                            paper_id=paper_id,
                            analysis_type=analysis_type
                        )
                        logger.info(f"Generated {analysis_type} for paper {paper_id}")
                    except Exception as e:
                        logger.error(f"Failed to generate {analysis_type} for paper {paper_id}: {e}")
        else:
            logger.error(f"PDF processing failed for paper {paper_id}: {result.get('error')}")
        
        logger.info(f"Background processing complete for paper {paper_id}")
        
    except Exception as e:
        logger.error(f"Background processing failed for paper {paper_id}: {e}")

@router.post("/import-with-analysis")
async def import_paper_with_analysis(
    request: ImportWithAnalysisRequest,
    background_tasks: BackgroundTasks
):
    """Import paper from ArXiv and process asynchronously"""
    arxiv_service = get_arxiv_service()
    repository_service = get_repository_service()
    
    try:
        # Create permanent directory for ArXiv PDFs
        from pathlib import Path
        arxiv_dir = Path("data/papers/arxiv")
        arxiv_dir.mkdir(parents=True, exist_ok=True)
        
        # Quick metadata fetch from ArXiv
        logger.info(f"Fetching metadata for ArXiv {request.arxiv_id}")
        import_result = arxiv_service.import_paper(request.arxiv_id, download_dir=str(arxiv_dir))
        
        if not import_result['success']:
            raise HTTPException(status_code=400, detail=import_result.get('error'))
        
        # Quick paper record creation (no PDF processing yet)
        from ..models import get_db
        from ..models.papers import Paper
        from ..models.paper_analysis import PaperRepository
        
        db = next(get_db())
        
        # Create paper record
        # Debug logging
        logger.info(f"Import result metadata: {import_result['metadata']}")
        
        # Handle categories - might be string or list
        categories = import_result['metadata'].get('categories', [])
        logger.info(f"Categories type: {type(categories)}, value: {categories}")
        
        if isinstance(categories, str):
            categories_str = categories
        elif isinstance(categories, list):
            categories_str = ', '.join(categories)
        else:
            categories_str = ''
            
        # Handle authors - might be string or list
        authors = import_result['metadata'].get('authors', [])
        logger.info(f"Authors type: {type(authors)}, value: {authors}")
        
        if isinstance(authors, str):
            authors_str = authors
        elif isinstance(authors, list):
            authors_str = ', '.join(authors)
        else:
            authors_str = ''
        
        logger.info(f"Final authors_str: {authors_str}, categories_str: {categories_str}")
        
        paper = Paper(
            title=import_result['metadata']['title'],
            authors=authors_str,
            abstract=import_result['metadata']['abstract'],
            arxiv_id=import_result['arxiv_id'],
            pdf_url=import_result['metadata']['pdf_url'],
            pdf_path=import_result['pdf_path'],  # SAVE THE PDF PATH IMMEDIATELY!
            published_date=import_result['metadata'].get('published'),
            categories=categories_str,
            processed=False  # Mark as not processed yet
        )
        db.add(paper)
        db.commit()
        db.refresh(paper)
        
        # Create repository entry (marked as not processed)
        repo = PaperRepository(
            paper_id=paper.id,
            pdf_original_path=import_result['pdf_path'],
            pdf_processed=False,
            markdown_generated=False
        )
        db.add(repo)
        db.commit()
        
        paper_id = paper.id
        db.close()
        
        # NO LONGER AUTO-PROCESSING - User must click "Process PDF" button
        # logger.info(f"Scheduling background processing for paper {paper_id}")
        # background_tasks.add_task(
        #     _process_paper_in_background,
        #     paper_id=paper_id,
        #     pdf_path=import_result['pdf_path'],
        #     generate_analyses=request.generate_analyses
        # )
        
        # Return immediately
        return {
            'success': True,
            'paper_id': paper_id,
            'arxiv_id': request.arxiv_id,
            'title': import_result['metadata']['title'],
            'analyses_requested': request.generate_analyses,
            'message': 'Paper imported! Use "Process PDF" button to extract content.',
            'processing_status': 'ready'  # Changed from 'started' to 'ready'
        }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to import paper: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{paper_id}/processing-status")
async def get_processing_status(
    paper_id: int,
    db: Session = Depends(get_db)
):
    """Get real-time processing status for a paper"""
    try:
        repo = db.query(PaperRepository).filter(
            PaperRepository.paper_id == paper_id
        ).first()
        
        if not repo:
            return {
                'status': 'not_found',
                'paper_id': paper_id
            }
        
        # Determine current status
        if repo.pdf_processed and repo.markdown_generated:
            status = 'completed'
        elif repo.pdf_processed:
            status = 'processing_analyses'
        else:
            status = 'processing_pdf'
        
        # Get analysis count
        analysis_count = db.query(PaperAnalysis).filter(
            PaperAnalysis.paper_id == paper_id,
            PaperAnalysis.is_latest == True
        ).count()
        
        return {
            'status': status,
            'paper_id': paper_id,
            'pdf_processed': repo.pdf_processed,
            'markdown_generated': repo.markdown_generated,
            'analyses_completed': analysis_count,
            'processing_started': repo.imported_at.isoformat() if repo.imported_at else None,
            'processing_completed': repo.processed_at.isoformat() if repo.processed_at else None
        }
        
    except Exception as e:
        logger.error(f"Failed to get processing status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{paper_id}/repository-info")
async def get_repository_info(
    paper_id: int,
    db: Session = Depends(get_db)
):
    """Get repository information for a paper"""
    try:
        repo = db.query(PaperRepository).filter(
            PaperRepository.paper_id == paper_id
        ).first()
        
        if not repo:
            return {
                'exists': False,
                'paper_id': paper_id
            }
        
        # Get analysis count
        analysis_count = db.query(PaperAnalysis).filter(
            PaperAnalysis.paper_id == paper_id,
            PaperAnalysis.is_latest == True
        ).count()
        
        return {
            'exists': True,
            'paper_id': paper_id,
            'pdf_path': repo.pdf_original_path,
            'markdown_path': repo.markdown_path,
            'pdf_processed': repo.pdf_processed,
            'markdown_generated': repo.markdown_generated,
            'analysis_count': analysis_count,
            'analyses_completed': repo.analyses_completed or [],
            'pdf_size': repo.pdf_size_bytes,
            'imported_at': repo.imported_at.isoformat() if repo.imported_at else None,
            'processed_at': repo.processed_at.isoformat() if repo.processed_at else None
        }
        
    except Exception as e:
        logger.error(f"Failed to get repository info: {e}")
        raise HTTPException(status_code=500, detail=str(e))

class RatingUpdate(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    notes: Optional[str] = None

@router.put("/{paper_id}/analysis/{analysis_id}/rating")
async def update_analysis_rating(
    paper_id: int,
    analysis_id: int,
    body: RatingUpdate,
    db: Session = Depends(get_db)
):
    """Update user rating and notes for an analysis"""
    try:
        analysis = db.query(PaperAnalysis).filter(
            PaperAnalysis.id == analysis_id,
            PaperAnalysis.paper_id == paper_id
        ).first()
        
        if not analysis:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        analysis.user_rating = body.rating
        if body.notes:
            analysis.user_notes = body.notes
        
        db.commit()
        
        return {
            'success': True,
            'analysis_id': analysis_id,
            'rating': body.rating,
            'notes': body.notes
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update rating: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))