"""
Papers API with full MongoDB concept support
Replaces the legacy papers.py that uses SQLite tags
"""

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
import json
import logging
import os
import hashlib
from pathlib import Path

from app.models import get_db
from app.models.papers import Paper, PaperAuthor, PaperSection, PaperReference, PaperSnippet, PaperAnalysis
from app.services.concept_only_tag_service import ConceptOnlyTagService
from app.services.pdf_processor_service import PDFProcessorService
from app.services.paper_analysis_service import PaperAnalysisService
from app.services.llm_service import LLMService

router = APIRouter(prefix="/api/papers", tags=["papers-concepts"])
logger = logging.getLogger(__name__)

# Initialize services
concept_service = ConceptOnlyTagService()
pdf_processor = PDFProcessorService()
analysis_service = PaperAnalysisService()
llm_service = LLMService()

# Constants
UPLOAD_DIR = Path("data/papers")
UPLOAD_DIR.mkdir(exist_ok=True, parents=True)

@router.get("/", response_model=List[Dict])
async def get_papers(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    concept: Optional[str] = None,
    search: Optional[str] = None,
    author: Optional[str] = None,
    year: Optional[int] = None,
    sort_by: str = Query("uploaded_at", regex="^(uploaded_at|title|year)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    db: Session = Depends(get_db)
):
    """Get papers with concept-based filtering"""
    try:
        # Start with base query
        query = db.query(Paper)
        
        # Apply concept filter if provided
        if concept:
            # Get all papers with this concept
            paper_ids = concept_service.get_content_ids_by_concept(
                concept_slug=concept,
                content_type='paper'
            )
            
            if not paper_ids:
                return []
            
            query = query.filter(Paper.id.in_(paper_ids))
        
        # Apply other filters
        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                (Paper.title.ilike(search_pattern)) |
                (Paper.abstract.ilike(search_pattern))
            )
        
        if author:
            query = query.join(PaperAuthor).filter(
                PaperAuthor.name.ilike(f"%{author}%")
            )
        
        if year:
            query = query.filter(Paper.year == year)
        
        # Apply sorting
        if sort_order == "desc":
            if sort_by == "uploaded_at":
                query = query.order_by(Paper.uploaded_at.desc())
            elif sort_by == "title":
                query = query.order_by(Paper.title.desc())
            elif sort_by == "year":
                query = query.order_by(Paper.year.desc())
        else:
            if sort_by == "uploaded_at":
                query = query.order_by(Paper.uploaded_at.asc())
            elif sort_by == "title":
                query = query.order_by(Paper.title.asc())
            elif sort_by == "year":
                query = query.order_by(Paper.year.asc())
        
        # Execute query
        papers = query.offset(skip).limit(limit).all()
        
        # Format response with concepts
        result = []
        for paper in papers:
            paper_dict = {
                "id": paper.id,
                "title": paper.title,
                "abstract": paper.abstract,
                "authors": [{"name": a.name, "affiliation": a.affiliation} for a in paper.authors],
                "year": paper.year,
                "pdf_path": paper.pdf_path,
                "uploaded_at": paper.uploaded_at.isoformat() if paper.uploaded_at else None,
                "processed": paper.processed,
                "concepts": concept_service.get_concepts_for_content(
                    content_id=str(paper.id),
                    content_type='paper'
                )
            }
            result.append(paper_dict)
        
        return result
        
    except Exception as e:
        logger.error(f"Error fetching papers: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/faceted-search")
async def faceted_search(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    concepts: Optional[str] = Query(None, description="Comma-separated concept slugs"),
    authors: Optional[str] = Query(None, description="Comma-separated author names"),
    years: Optional[str] = Query(None, description="Comma-separated years"),
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Faceted search for papers with concept support"""
    try:
        # Parse filters
        concept_list = concepts.split(',') if concepts else []
        author_list = authors.split(',') if authors else []
        year_list = [int(y) for y in years.split(',')] if years else []
        
        # Start with base query
        query = db.query(Paper)
        
        # Apply concept filters
        if concept_list:
            # Get papers that have ALL specified concepts
            paper_id_sets = []
            for concept_slug in concept_list:
                ids = concept_service.get_content_ids_by_concept(
                    concept_slug=concept_slug,
                    content_type='paper'
                )
                if ids:
                    paper_id_sets.append(set(ids))
            
            if paper_id_sets:
                # Intersection of all sets to get papers with ALL concepts
                common_ids = set.intersection(*paper_id_sets) if paper_id_sets else set()
                if common_ids:
                    query = query.filter(Paper.id.in_(list(common_ids)))
                else:
                    return {"papers": [], "facets": {}, "total": 0}
        
        # Apply author filters
        if author_list:
            query = query.join(PaperAuthor).filter(
                PaperAuthor.name.in_(author_list)
            )
        
        # Apply year filters
        if year_list:
            query = query.filter(Paper.year.in_(year_list))
        
        # Apply search
        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                (Paper.title.ilike(search_pattern)) |
                (Paper.abstract.ilike(search_pattern))
            )
        
        # Get total count
        total = query.count()
        
        # Get papers
        papers = query.offset(skip).limit(limit).all()
        
        # Build facets
        all_paper_ids = [p.id for p in db.query(Paper).all()]
        
        # Concept facets
        concept_facets = []
        all_concepts = concept_service.get_all_concepts_with_counts(content_type='paper')
        for concept in all_concepts[:50]:  # Top 50 concepts
            concept_facets.append({
                "value": concept['slug'],
                "label": concept.get('display_name', concept['slug']),
                "count": concept['count']
            })
        
        # Author facets
        author_counts = {}
        for author in db.query(PaperAuthor).all():
            author_counts[author.name] = author_counts.get(author.name, 0) + 1
        
        author_facets = [
            {"value": name, "label": name, "count": count}
            for name, count in sorted(author_counts.items(), key=lambda x: x[1], reverse=True)[:20]
        ]
        
        # Year facets
        year_counts = {}
        for paper in db.query(Paper).all():
            if paper.year:
                year_counts[paper.year] = year_counts.get(paper.year, 0) + 1
        
        year_facets = [
            {"value": str(year), "label": str(year), "count": count}
            for year, count in sorted(year_counts.items(), reverse=True)
        ]
        
        # Format papers with concepts
        formatted_papers = []
        for paper in papers:
            formatted_papers.append({
                "id": paper.id,
                "title": paper.title,
                "abstract": paper.abstract,
                "authors": [{"name": a.name, "affiliation": a.affiliation} for a in paper.authors],
                "year": paper.year,
                "pdf_path": paper.pdf_path,
                "uploaded_at": paper.uploaded_at.isoformat() if paper.uploaded_at else None,
                "concepts": concept_service.get_concepts_for_content(
                    content_id=str(paper.id),
                    content_type='paper'
                )
            })
        
        return {
            "papers": formatted_papers,
            "facets": {
                "concepts": concept_facets,
                "authors": author_facets,
                "years": year_facets
            },
            "total": total
        }
        
    except Exception as e:
        logger.error(f"Error in faceted search: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{paper_id}")
async def get_paper(paper_id: int, db: Session = Depends(get_db)):
    """Get a single paper with all details and concepts"""
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    # Get concepts for this paper
    concepts = concept_service.get_concepts_for_content(
        content_id=str(paper_id),
        content_type='paper'
    )
    
    # Get analyses if available
    analyses = db.query(PaperAnalysis).filter(PaperAnalysis.paper_id == paper_id).all()
    
    return {
        "id": paper.id,
        "title": paper.title,
        "abstract": paper.abstract,
        "authors": [
            {"name": a.name, "affiliation": a.affiliation}
            for a in paper.authors
        ],
        "year": paper.year,
        "pdf_path": paper.pdf_path,
        "pdf_url": paper.pdf_url,
        "uploaded_at": paper.uploaded_at.isoformat() if paper.uploaded_at else None,
        "processed": paper.processed,
        "processor": paper.processor,
        "sections": [
            {
                "id": s.id,
                "title": s.title,
                "content": s.content,
                "section_number": s.section_number
            }
            for s in paper.sections
        ],
        "references": [
            {
                "id": r.id,
                "title": r.title,
                "authors": r.authors,
                "year": r.year,
                "venue": r.venue
            }
            for r in paper.references
        ],
        "concepts": concepts,
        "analyses": [
            {
                "id": a.id,
                "analysis_type": a.analysis_type,
                "content": a.content,
                "created_at": a.created_at.isoformat() if a.created_at else None
            }
            for a in analyses
        ],
        "snippets": [
            {
                "id": s.id,
                "content": s.content,
                "annotation": s.annotation,
                "created_at": s.created_at.isoformat() if s.created_at else None
            }
            for s in paper.snippets
        ]
    }

@router.post("/{paper_id}/concepts")
async def add_paper_concept(
    paper_id: int,
    concept_slug: str = Form(...),
    db: Session = Depends(get_db)
):
    """Add a concept to a paper"""
    # Verify paper exists
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    try:
        # Add concept using the service
        concept_service.add_concept_to_content(
            content_id=str(paper_id),
            content_type='paper',
            concept_slug=concept_slug
        )
        
        return {
            "message": "Concept added successfully",
            "concepts": concept_service.get_concepts_for_content(
                content_id=str(paper_id),
                content_type='paper'
            )
        }
    except Exception as e:
        logger.error(f"Error adding concept to paper: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{paper_id}/concepts/{concept_slug}")
async def remove_paper_concept(
    paper_id: int,
    concept_slug: str,
    db: Session = Depends(get_db)
):
    """Remove a concept from a paper"""
    # Verify paper exists
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    try:
        # Remove concept using the service
        concept_service.remove_concept_from_content(
            content_id=str(paper_id),
            content_type='paper',
            concept_slug=concept_slug
        )
        
        return {
            "message": "Concept removed successfully",
            "concepts": concept_service.get_concepts_for_content(
                content_id=str(paper_id),
                content_type='paper'
            )
        }
    except Exception as e:
        logger.error(f"Error removing concept from paper: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{paper_id}/concepts/suggest")
async def suggest_paper_concepts(
    paper_id: int,
    db: Session = Depends(get_db)
):
    """Suggest concepts for a paper using AI"""
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    try:
        # Prepare paper text for analysis
        paper_text = f"Title: {paper.title}\n\nAbstract: {paper.abstract}\n\n"
        
        # Add section content if available
        for section in paper.sections[:5]:  # First 5 sections
            paper_text += f"\n{section.title}:\n{section.content[:1000]}\n"
        
        # Get AI suggestions
        prompt = f"""Suggest relevant concepts/tags for this research paper:

{paper_text}

Provide 10-15 specific concepts that capture:
- Main topics and domains
- Methods and techniques used
- Datasets or benchmarks mentioned
- Key technologies or models
- Application areas

Return as JSON array of strings."""

        suggestions = llm_service.complete(prompt)
        
        # Parse suggestions
        import json
        try:
            suggested_concepts = json.loads(suggestions)
        except:
            suggested_concepts = []
        
        # Get existing concepts
        existing = concept_service.get_concepts_for_content(
            content_id=str(paper_id),
            content_type='paper'
        )
        existing_slugs = [c['slug'] for c in existing]
        
        # Filter out existing ones
        new_suggestions = [s for s in suggested_concepts if s not in existing_slugs]
        
        return {
            "existing_concepts": existing,
            "suggested_concepts": new_suggestions[:15]
        }
        
    except Exception as e:
        logger.error(f"Error suggesting concepts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/upload")
async def upload_paper(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    year: Optional[int] = Form(None),
    db: Session = Depends(get_db)
):
    """Upload a new paper PDF and process it"""
    try:
        # Validate file type
        if not file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are supported")
        
        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_hash = hashlib.md5(file.filename.encode()).hexdigest()[:8]
        safe_filename = f"{timestamp}_{file_hash}_{file.filename}"
        file_path = UPLOAD_DIR / safe_filename
        
        # Save file
        content = await file.read()
        with open(file_path, 'wb') as f:
            f.write(content)
        
        # Process PDF
        extracted_data = pdf_processor.process_pdf(str(file_path))
        
        # Create paper record
        paper = Paper(
            title=title or extracted_data.get('title', file.filename),
            abstract=extracted_data.get('abstract', ''),
            year=year or extracted_data.get('year'),
            pdf_path=str(file_path),
            processed=True,
            processor=extracted_data.get('processor', 'unknown'),
            uploaded_at=datetime.utcnow()
        )
        
        db.add(paper)
        db.commit()
        db.refresh(paper)
        
        # Add authors
        for author_data in extracted_data.get('authors', []):
            author = PaperAuthor(
                paper_id=paper.id,
                name=author_data.get('name', ''),
                affiliation=author_data.get('affiliation')
            )
            db.add(author)
        
        # Add sections
        for idx, section_data in enumerate(extracted_data.get('sections', [])):
            section = PaperSection(
                paper_id=paper.id,
                title=section_data.get('title', ''),
                content=section_data.get('content', ''),
                section_number=idx
            )
            db.add(section)
        
        db.commit()
        
        # Auto-suggest concepts
        paper_text = f"{paper.title} {paper.abstract}"
        suggested_tags = llm_service.suggest_tags(paper_text)
        
        # Add suggested concepts
        for tag in suggested_tags[:10]:  # Add top 10
            try:
                concept_service.add_concept_to_content(
                    content_id=str(paper.id),
                    content_type='paper',
                    concept_slug=tag
                )
            except:
                pass  # Ignore if concept doesn't exist
        
        return {
            "id": paper.id,
            "title": paper.title,
            "message": "Paper uploaded and processed successfully",
            "concepts": concept_service.get_concepts_for_content(
                content_id=str(paper.id),
                content_type='paper'
            )
        }
        
    except Exception as e:
        logger.error(f"Error uploading paper: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats/concepts")
async def get_paper_concept_stats():
    """Get statistics about concepts used in papers"""
    try:
        stats = concept_service.get_concept_statistics(content_type='paper')
        
        return {
            "total_concepts": stats.get('total_concepts', 0),
            "total_assignments": stats.get('total_instances', 0),
            "top_concepts": stats.get('top_concepts', []),
            "recent_concepts": stats.get('recent_additions', [])
        }
    except Exception as e:
        logger.error(f"Error getting concept stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/concepts/hierarchy")
async def get_paper_concepts_hierarchy():
    """Get hierarchical view of concepts used in papers"""
    try:
        # Get all concepts used in papers
        paper_concepts = concept_service.get_all_concepts_with_counts(content_type='paper')
        
        # Build hierarchy
        hierarchy = concept_service.build_concept_hierarchy(paper_concepts)
        
        return hierarchy
    except Exception as e:
        logger.error(f"Error building concept hierarchy: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/migrate-tags")
async def migrate_paper_tags_to_concepts(db: Session = Depends(get_db)):
    """One-time migration of old paper_tags to concepts"""
    try:
        from app.models.papers import PaperTag
        
        # Get all old paper tags
        old_tags = db.query(PaperTag).all()
        
        migrated = 0
        errors = []
        
        for old_tag in old_tags:
            try:
                # Add as concept
                concept_service.add_concept_to_content(
                    content_id=str(old_tag.paper_id),
                    content_type='paper',
                    concept_slug=old_tag.tag
                )
                migrated += 1
            except Exception as e:
                errors.append(f"Paper {old_tag.paper_id}, Tag {old_tag.tag}: {str(e)}")
        
        return {
            "message": "Migration completed",
            "migrated": migrated,
            "errors": errors[:10] if errors else []
        }
    except Exception as e:
        logger.error(f"Error migrating tags: {e}")
        raise HTTPException(status_code=500, detail=str(e))