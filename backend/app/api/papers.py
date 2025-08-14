"""
API endpoints for research papers
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from typing import List, Optional
from datetime import datetime, date
import logging

from app.models import get_db
from app.models.papers import Paper, PaperAuthor, PaperSection, PaperTag, PaperSnippet
from app.services.paper_service import PaperService
from app.services.paper_rag_service import PaperRAGService
from app.services.paper_tag_service import PaperTagService
from app.services.unified_tag_service import UnifiedTagService
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/papers", tags=["papers"])

# Initialize services
paper_service = PaperService()
rag_service = PaperRAGService()
tag_service = PaperTagService()

# Pydantic models
class PaperResponse(BaseModel):
    id: int
    title: str
    abstract: Optional[str]
    authors: List[dict]
    publication_date: Optional[date]
    conference: Optional[str]
    journal: Optional[str]
    arxiv_id: Optional[str]
    doi: Optional[str]
    page_count: int
    tags: List[str]
    created_at: datetime
    processed: bool
    
    class Config:
        from_attributes = True

class PaperUploadResponse(BaseModel):
    id: int
    title: str
    message: str
    extracted_sections: int
    extracted_authors: int

class PaperListResponse(BaseModel):
    papers: List[PaperResponse]
    total: int
    page: int
    page_size: int

class TagRequest(BaseModel):
    tag: str
    tag_type: str = "manual"

class SnippetRequest(BaseModel):
    content: str
    page_number: Optional[int]
    annotation: Optional[str]
    category: Optional[str]

@router.post("/upload", response_model=PaperUploadResponse)
async def upload_paper(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload and process a PDF research paper"""
    
    # Validate file type
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    # Check file size (limit to 50MB)
    contents = await file.read()
    if len(contents) > 50 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File size exceeds 50MB limit")
    
    try:
        # Save the PDF file
        pdf_path = paper_service.save_pdf_file(contents, file.filename)
        
        # Extract text and metadata
        extracted_data = paper_service.extract_text_from_pdf(pdf_path)
        
        # Extract additional metadata from filename
        filename_metadata = paper_service.extract_metadata_from_filename(file.filename)
        
        # Create paper record
        paper = Paper(
            title=extracted_data.get("title") or file.filename,
            abstract=extracted_data.get("abstract"),
            content=extracted_data.get("content"),
            pdf_path=pdf_path,
            page_count=extracted_data.get("page_count", 0),
            arxiv_id=filename_metadata.get("arxiv_id"),
            conference=filename_metadata.get("conference"),
            processed=False
        )
        
        # Set publication date if year is found
        if filename_metadata.get("year"):
            paper.publication_date = date(filename_metadata["year"], 1, 1)
        
        db.add(paper)
        db.flush()  # Get the paper ID
        
        # Extract and save authors
        authors = paper_service.extract_authors_from_content(extracted_data.get("content", ""))
        for author_data in authors:
            author = PaperAuthor(
                paper_id=paper.id,
                name=author_data["name"],
                email=author_data.get("email"),
                position=author_data.get("position", 0)
            )
            db.add(author)
        
        # Save sections
        for section_data in extracted_data.get("sections", []):
            section = PaperSection(
                paper_id=paper.id,
                section_type=section_data["type"],
                title=section_data["title"],
                content=section_data["content"][:10000],  # Limit content length
                position=section_data["position"]
            )
            db.add(section)
        
        # Mark as processed
        paper.processed = True
        
        db.commit()
        
        # Add to RAG index
        try:
            rag_service.add_paper_to_index(db, paper.id)
            logger.info(f"Added paper {paper.id} to RAG index")
        except Exception as e:
            logger.error(f"Failed to add paper to RAG index: {e}")
            # Don't fail the upload if RAG indexing fails
        
        return PaperUploadResponse(
            id=paper.id,
            title=paper.title,
            message="Paper uploaded and processed successfully",
            extracted_sections=len(extracted_data.get("sections", [])),
            extracted_authors=len(authors)
        )
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error processing paper: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing paper: {str(e)}")

@router.get("", response_model=PaperListResponse)
def get_papers(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    author: Optional[str] = None,
    tag: Optional[str] = None,
    conference: Optional[str] = None,
    year: Optional[int] = None,
    use_ontology: bool = Query(True, description="Use tag ontology for hierarchical filtering"),
    db: Session = Depends(get_db)
):
    """Get list of papers with filtering and pagination"""
    
    query = db.query(Paper)
    
    # Apply filters
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (Paper.title.ilike(search_term)) |
            (Paper.abstract.ilike(search_term))
        )
    
    if author:
        query = query.join(PaperAuthor).filter(
            PaperAuthor.name.ilike(f"%{author}%")
        )
    
    if tag:
        # Use unified tag service for consistent filtering
        unified_service = UnifiedTagService(db)
        query = unified_service.filter_papers_by_tag(query, tag, use_hierarchy=use_ontology)
        logger.info(f"Filtering papers by tag: '{tag}' (hierarchy={'enabled' if use_ontology else 'disabled'})")
    
    if conference:
        query = query.filter(Paper.conference.ilike(f"%{conference}%"))
    
    if year:
        query = query.filter(
            func.extract('year', Paper.publication_date) == year
        )
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    offset = (page - 1) * page_size
    papers = query.order_by(desc(Paper.created_at)).offset(offset).limit(page_size).all()
    
    # Format response
    paper_responses = []
    for paper in papers:
        paper_dict = {
            "id": paper.id,
            "title": paper.title,
            "abstract": paper.abstract,
            "authors": [
                {"name": a.name, "email": a.email}
                for a in paper.authors
            ],
            "publication_date": paper.publication_date,
            "conference": paper.conference,
            "journal": paper.journal,
            "arxiv_id": paper.arxiv_id,
            "doi": paper.doi,
            "page_count": paper.page_count,
            "tags": [t.tag for t in paper.tags],
            "created_at": paper.created_at,
            "processed": paper.processed
        }
        paper_responses.append(PaperResponse(**paper_dict))
    
    return PaperListResponse(
        papers=paper_responses,
        total=total,
        page=page,
        page_size=page_size
    )

@router.post("/reindex")
def reindex_papers(db: Session = Depends(get_db)):
    """Reindex all papers in the RAG system"""
    try:
        results = rag_service.update_all_papers(db)
        return {
            "message": "Papers reindexed successfully",
            "results": results
        }
    except Exception as e:
        logger.error(f"Error reindexing papers: {e}")
        raise HTTPException(status_code=500, detail=f"Error reindexing papers: {str(e)}")

@router.get("/search")
def search_papers_rag(
    q: str = Query(..., description="Search query"),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """Search papers using RAG (semantic search)"""
    try:
        results = rag_service.search_papers(q, k=limit)
        
        # Filter to only paper results
        paper_results = [r for r in results if r.get("type") == "paper"]
        
        return {
            "query": q,
            "results": paper_results,
            "total": len(paper_results)
        }
    except Exception as e:
        logger.error(f"Error searching papers: {e}")
        raise HTTPException(status_code=500, detail=f"Error searching papers: {str(e)}")

@router.get("/{paper_id}/pdf")
def get_paper_pdf(paper_id: int, db: Session = Depends(get_db)):
    """Get the PDF file for a paper"""
    
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    if not paper.pdf_path:
        raise HTTPException(status_code=404, detail="PDF file not found")
    
    import os
    if not os.path.exists(paper.pdf_path):
        raise HTTPException(status_code=404, detail="PDF file not found on disk")
    
    return FileResponse(
        path=paper.pdf_path,
        media_type="application/pdf",
        filename=os.path.basename(paper.pdf_path)
    )

@router.get("/{paper_id}", response_model=PaperResponse)
def get_paper(paper_id: int, db: Session = Depends(get_db)):
    """Get detailed information about a specific paper"""
    
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    return PaperResponse(
        id=paper.id,
        title=paper.title,
        abstract=paper.abstract,
        authors=[
            {"name": a.name, "email": a.email}
            for a in paper.authors
        ],
        publication_date=paper.publication_date,
        conference=paper.conference,
        journal=paper.journal,
        arxiv_id=paper.arxiv_id,
        doi=paper.doi,
        page_count=paper.page_count,
        tags=[t.tag for t in paper.tags],
        created_at=paper.created_at,
        processed=paper.processed
    )

@router.get("/{paper_id}/content")
def get_paper_content(paper_id: int, db: Session = Depends(get_db)):
    """Get the full text content of a paper"""
    
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    return {
        "id": paper.id,
        "title": paper.title,
        "content": paper.content,
        "sections": [
            {
                "id": s.id,
                "type": s.section_type,
                "title": s.title,
                "content": s.content,
                "position": s.position
            }
            for s in paper.sections
        ]
    }

@router.get("/{paper_id}/tags/suggestions")
def get_tag_suggestions(
    paper_id: int,
    db: Session = Depends(get_db)
):
    """Get AI-powered tag suggestions for a paper"""
    
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    suggestions = tag_service.suggest_tags_from_paper(db, paper_id)
    
    # Get existing tags
    existing_tags = db.query(PaperTag.tag).filter(
        PaperTag.paper_id == paper_id
    ).all()
    
    return {
        "paper_id": paper_id,
        "suggestions": suggestions,
        "existing_tags": [tag[0] for tag in existing_tags]
    }

@router.post("/{paper_id}/tags")
def add_paper_tag(
    paper_id: int,
    tag_request: TagRequest,
    db: Session = Depends(get_db)
):
    """Add a tag to a paper"""
    
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    # Normalize tag using unified service
    unified_service = UnifiedTagService(db)
    normalized_tag = unified_service.normalize_tag_for_storage(
        tag_request.tag, 
        preserve_case=(tag_request.tag_type == 'manual')
    )
    
    # Check if tag already exists (check both original and normalized)
    existing_tag = db.query(PaperTag).filter(
        PaperTag.paper_id == paper_id,
        func.lower(PaperTag.tag) == func.lower(normalized_tag)
    ).first()
    
    if existing_tag:
        return {"message": "Tag already exists", "tag": existing_tag.tag}
    
    # Add new tag with normalized form
    new_tag = PaperTag(
        paper_id=paper_id,
        tag=normalized_tag,
        tag_type=tag_request.tag_type
    )
    db.add(new_tag)
    db.commit()
    
    logger.info(f"Added tag '{normalized_tag}' to paper {paper_id} (original: '{tag_request.tag}')")
    
    return {"message": "Tag added successfully", "tag": normalized_tag}

@router.delete("/{paper_id}/tags/{tag}")
def remove_paper_tag(
    paper_id: int,
    tag: str,
    db: Session = Depends(get_db)
):
    """Remove a tag from a paper"""
    
    tag_entry = db.query(PaperTag).filter(
        PaperTag.paper_id == paper_id,
        PaperTag.tag == tag
    ).first()
    
    if not tag_entry:
        raise HTTPException(status_code=404, detail="Tag not found")
    
    db.delete(tag_entry)
    db.commit()
    
    return {"message": "Tag removed successfully"}

@router.post("/{paper_id}/snippets")
def create_paper_snippet(
    paper_id: int,
    snippet_request: SnippetRequest,
    db: Session = Depends(get_db)
):
    """Create a snippet from a paper"""
    
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    snippet = PaperSnippet(
        paper_id=paper_id,
        content=snippet_request.content,
        page_number=snippet_request.page_number,
        annotation=snippet_request.annotation,
        category=snippet_request.category
    )
    
    db.add(snippet)
    db.commit()
    db.refresh(snippet)
    
    return {
        "id": snippet.id,
        "content": snippet.content,
        "annotation": snippet.annotation,
        "category": snippet.category,
        "created_at": snippet.created_at
    }

@router.get("/{paper_id}/snippets")
def get_paper_snippets(paper_id: int, db: Session = Depends(get_db)):
    """Get all snippets for a paper"""
    
    snippets = db.query(PaperSnippet).filter(
        PaperSnippet.paper_id == paper_id
    ).order_by(desc(PaperSnippet.created_at)).all()
    
    return [
        {
            "id": s.id,
            "content": s.content,
            "page_number": s.page_number,
            "annotation": s.annotation,
            "category": s.category,
            "created_at": s.created_at
        }
        for s in snippets
    ]

@router.get("/{paper_id}/snippets/export")
def export_paper_snippets(
    paper_id: int,
    format: str = Query("markdown", enum=["markdown", "json", "text"]),
    db: Session = Depends(get_db)
):
    """Export snippets in various formats"""
    
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    snippets = db.query(PaperSnippet).filter(
        PaperSnippet.paper_id == paper_id
    ).order_by(PaperSnippet.created_at).all()
    
    if format == "markdown":
        # Generate markdown format
        content = f"# Snippets from: {paper.title}\n\n"
        content += f"**Authors:** {', '.join([a.name for a in paper.authors])}\n\n"
        
        # Group by category
        categories = {}
        uncategorized = []
        
        for snippet in snippets:
            if snippet.category:
                if snippet.category not in categories:
                    categories[snippet.category] = []
                categories[snippet.category].append(snippet)
            else:
                uncategorized.append(snippet)
        
        # Write categorized snippets
        for category, cat_snippets in categories.items():
            content += f"## {category.title()}\n\n"
            for s in cat_snippets:
                content += f"### Snippet {s.id}\n"
                if s.page_number:
                    content += f"*Page {s.page_number}*\n\n"
                content += f"> {s.content}\n\n"
                if s.annotation:
                    content += f"**Note:** {s.annotation}\n\n"
                content += "---\n\n"
        
        # Write uncategorized snippets
        if uncategorized:
            content += "## Uncategorized\n\n"
            for s in uncategorized:
                content += f"### Snippet {s.id}\n"
                if s.page_number:
                    content += f"*Page {s.page_number}*\n\n"
                content += f"> {s.content}\n\n"
                if s.annotation:
                    content += f"**Note:** {s.annotation}\n\n"
                content += "---\n\n"
        
        from fastapi.responses import Response
        return Response(
            content=content,
            media_type="text/markdown",
            headers={
                "Content-Disposition": f"attachment; filename=snippets_{paper_id}.md"
            }
        )
    
    elif format == "json":
        # Return JSON format
        import json
        data = {
            "paper": {
                "id": paper.id,
                "title": paper.title,
                "authors": [a.name for a in paper.authors]
            },
            "snippets": [
                {
                    "id": s.id,
                    "content": s.content,
                    "page_number": s.page_number,
                    "annotation": s.annotation,
                    "category": s.category,
                    "created_at": s.created_at.isoformat() if s.created_at else None
                }
                for s in snippets
            ]
        }
        
        from fastapi.responses import Response
        return Response(
            content=json.dumps(data, indent=2),
            media_type="application/json",
            headers={
                "Content-Disposition": f"attachment; filename=snippets_{paper_id}.json"
            }
        )
    
    else:  # text format
        # Simple text format
        content = f"Snippets from: {paper.title}\n"
        content += "=" * 50 + "\n\n"
        
        for i, s in enumerate(snippets, 1):
            content += f"Snippet {i}"
            if s.page_number:
                content += f" (Page {s.page_number})"
            content += "\n" + "-" * 30 + "\n"
            content += s.content + "\n"
            if s.annotation:
                content += f"\nNote: {s.annotation}\n"
            content += "\n"
        
        from fastapi.responses import Response
        return Response(
            content=content,
            media_type="text/plain",
            headers={
                "Content-Disposition": f"attachment; filename=snippets_{paper_id}.txt"
            }
        )


@router.get("/{paper_id}/related")
def get_related_content(
    paper_id: int,
    db: Session = Depends(get_db)
):
    """Find tweets and articles related to this paper"""
    
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    # Use semantic search to find related content
    from app.services.rag_service import RAGService
    rag_service = RAGService(db)
    
    # Create a search query from paper title and abstract
    query = f"{paper.title}"
    if paper.abstract:
        query += f" {paper.abstract[:200]}"
    
    # Search for related content
    search_results = rag_service.search(query, k=20)
    
    related_tweets = []
    related_articles = []
    
    for result in search_results:
        if result.source_type == 'tweet':
            related_tweets.append({
                'tweet_id': result.source_id,
                'content': result.content[:280],
                'author': result.metadata.get('author'),
                'score': result.score
            })
        elif result.source_type == 'article':
            related_articles.append({
                'article_id': result.source_id,
                'title': result.metadata.get('title'),
                'author': result.metadata.get('author'),
                'content_preview': result.content[:200],
                'score': result.score
            })
    
    # Also check for direct keyword matches in tags
    paper_tags = [tag.tag for tag in paper.tags]
    
    if paper_tags:
        from app.models import Tag, Tweet, SubstackArticle
        
        # Find tweets with matching tags
        tag_matched_tweets = db.query(Tweet).join(Tag).filter(
            Tag.tag.in_(paper_tags)
        ).limit(10).all()
        
        for tweet in tag_matched_tweets:
            if not any(t['tweet_id'] == str(tweet.id) for t in related_tweets):
                related_tweets.append({
                    'tweet_id': str(tweet.id),
                    'content': tweet.text[:280],
                    'author': tweet.author_username,
                    'score': 0.5  # Lower score for tag matches
                })
    
    # Sort by score
    related_tweets.sort(key=lambda x: x['score'], reverse=True)
    related_articles.sort(key=lambda x: x['score'], reverse=True)
    
    return {
        'paper_id': paper_id,
        'paper_title': paper.title,
        'related_tweets': related_tweets[:10],
        'related_articles': related_articles[:10]
    }

@router.get("/stats/overview")
def get_papers_stats(db: Session = Depends(get_db)):
    """Get overview statistics for papers"""
    
    total_papers = db.query(func.count(Paper.id)).scalar()
    total_authors = db.query(func.count(func.distinct(PaperAuthor.name))).scalar()
    total_tags = db.query(func.count(func.distinct(PaperTag.tag))).scalar()
    total_snippets = db.query(func.count(PaperSnippet.id)).scalar()
    
    # Get recent papers
    recent_papers = db.query(Paper).order_by(
        desc(Paper.created_at)
    ).limit(5).all()
    
    # Get top tags
    top_tags = db.query(
        PaperTag.tag,
        func.count(PaperTag.id).label('count')
    ).group_by(PaperTag.tag).order_by(
        desc('count')
    ).limit(10).all()
    
    return {
        "total_papers": total_papers,
        "total_authors": total_authors,
        "total_tags": total_tags,
        "total_snippets": total_snippets,
        "recent_papers": [
            {"id": p.id, "title": p.title, "created_at": p.created_at}
            for p in recent_papers
        ],
        "top_tags": [
            {"tag": tag, "count": count}
            for tag, count in top_tags
        ]
    }