"""
API endpoints for advanced paper features - Phase 5
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from pydantic import BaseModel

from ..models import get_db
from ..services.paper_advanced_service import PaperAdvancedService

router = APIRouter(prefix="/api/papers/advanced", tags=["paper-advanced"])
advanced_service = PaperAdvancedService()


class ArxivImportRequest(BaseModel):
    arxiv_id: str


class SummarizeRequest(BaseModel):
    paper_id: int
    include_insights: bool = True


@router.get("/recommendations/{paper_id}")
def get_paper_recommendations(
    paper_id: int,
    limit: int = Query(5, le=20),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get recommendations for similar papers"""
    try:
        recommendations = advanced_service.get_paper_recommendations(
            db, paper_id, limit
        )
        return {
            "paper_id": paper_id,
            "recommendations": recommendations,
            "count": len(recommendations)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/summarize")
def generate_paper_summary(
    request: SummarizeRequest,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Generate AI-powered summary of a paper"""
    try:
        summary = advanced_service.generate_paper_summary(
            db, request.paper_id
        )
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/knowledge-graph")
def get_knowledge_graph(
    paper_id: Optional[int] = Query(None, description="Center paper ID"),
    depth: int = Query(2, le=3),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Build knowledge graph of paper relationships"""
    try:
        graph = advanced_service.build_knowledge_graph(
            db, paper_id, depth
        )
        return graph
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/import-arxiv")
def import_from_arxiv(
    request: ArxivImportRequest,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Import a paper from ArXiv by ID"""
    try:
        result = advanced_service.import_from_arxiv(
            db, request.arxiv_id
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/github-links/{paper_id}")
def extract_github_links(
    paper_id: int,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Extract GitHub repository links from paper"""
    try:
        links = advanced_service.extract_github_links(db, paper_id)
        return {
            "paper_id": paper_id,
            "github_links": links,
            "count": len(links)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/author-network")
def get_author_collaboration_network(
    min_papers: int = Query(2, description="Minimum papers per author"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get author collaboration network"""
    try:
        network = advanced_service.get_author_collaboration_network(
            db, min_papers
        )
        return network
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/semantic-scholar/{paper_id}")
def get_semantic_scholar_data(
    paper_id: int,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get additional data from Semantic Scholar"""
    # This would integrate with Semantic Scholar API
    # For now, return mock data structure
    from ..models import Paper
    
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    # In production, this would call Semantic Scholar API
    # using paper.doi or paper.arxiv_id
    return {
        "paper_id": paper_id,
        "semantic_scholar_data": {
            "citation_velocity": 0,
            "influential_citation_count": 0,
            "tldr": "This would be fetched from Semantic Scholar API",
            "fields_of_study": ["Artificial Intelligence", "Machine Learning"],
            "s2_paper_id": None
        },
        "message": "Semantic Scholar integration not yet implemented"
    }