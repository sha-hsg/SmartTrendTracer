"""
API endpoints for PDF export functionality
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from app.models import get_db, SubstackArticle
from app.services.pdf_export_service import PDFExportService


router = APIRouter()


class BulkExportRequest(BaseModel):
    """Request model for bulk PDF export"""
    article_ids: List[int]
    title: Optional[str] = "Article Collection"
    include_toc: bool = True


@router.get("/article/{article_id}")
def export_article_pdf(
    article_id: int,
    db: Session = Depends(get_db)
):
    """
    Export a single article to PDF
    """
    try:
        pdf_service = PDFExportService(db)
        pdf_bytes = pdf_service.export_article_to_pdf(article_id)
        
        # Get article for filename
        article = db.query(SubstackArticle).filter(
            SubstackArticle.id == article_id
        ).first()
        
        if article:
            # Create safe filename
            safe_title = "".join(c for c in article.title if c.isalnum() or c in (' ', '-', '_'))[:50]
            filename = f"{safe_title}.pdf"
        else:
            filename = f"article_{article_id}.pdf"
        
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to export PDF: {str(e)}")


@router.post("/articles/bulk")
def export_multiple_articles_pdf(
    request: BulkExportRequest,
    db: Session = Depends(get_db)
):
    """
    Export multiple articles to a single PDF
    """
    try:
        if not request.article_ids:
            raise ValueError("No article IDs provided")
        
        pdf_service = PDFExportService(db)
        pdf_bytes = pdf_service.export_multiple_articles_to_pdf(
            article_ids=request.article_ids,
            title=request.title,
            include_toc=request.include_toc
        )
        
        # Create filename based on number of articles
        filename = f"articles_collection_{len(request.article_ids)}.pdf"
        
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to export PDF: {str(e)}")


@router.get("/author/{author_id}")
def export_author_articles_pdf(
    author_id: int,
    db: Session = Depends(get_db)
):
    """
    Export all articles from a specific author to PDF
    """
    try:
        pdf_service = PDFExportService(db)
        pdf_bytes = pdf_service.export_author_articles_to_pdf(author_id)
        
        # Get author for filename
        from app.models import SubstackAuthor
        author = db.query(SubstackAuthor).filter(
            SubstackAuthor.id == author_id
        ).first()
        
        if author:
            safe_name = "".join(c for c in author.name if c.isalnum() or c in (' ', '-', '_'))[:30]
            filename = f"{safe_name}_articles.pdf"
        else:
            filename = f"author_{author_id}_articles.pdf"
        
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to export PDF: {str(e)}")


@router.get("/recent")
def export_recent_articles_pdf(
    days: int = Query(7, description="Number of days to look back"),
    limit: int = Query(10, description="Maximum number of articles"),
    db: Session = Depends(get_db)
):
    """
    Export recent articles to PDF
    """
    try:
        from datetime import datetime, timedelta
        
        # Get recent articles
        cutoff_date = datetime.now() - timedelta(days=days)
        
        articles = db.query(SubstackArticle).filter(
            SubstackArticle.published_at >= cutoff_date
        ).order_by(
            SubstackArticle.published_at.desc()
        ).limit(limit).all()
        
        if not articles:
            raise ValueError(f"No articles found in the last {days} days")
        
        article_ids = [article.id for article in articles]
        title = f"Recent Articles (Last {days} Days)"
        
        pdf_service = PDFExportService(db)
        pdf_bytes = pdf_service.export_multiple_articles_to_pdf(
            article_ids=article_ids,
            title=title,
            include_toc=True
        )
        
        filename = f"recent_articles_{days}days.pdf"
        
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to export PDF: {str(e)}")


@router.get("/tagged/{tag}")
def export_tagged_articles_pdf(
    tag: str,
    db: Session = Depends(get_db)
):
    """
    Export articles with a specific tag to PDF
    """
    try:
        # Get articles with this tag
        from app.models import ArticleTag
        
        article_ids = db.query(ArticleTag.article_id).filter(
            ArticleTag.tag == tag
        ).distinct().all()
        
        if not article_ids:
            raise ValueError(f"No articles found with tag '{tag}'")
        
        article_ids = [id[0] for id in article_ids]
        title = f"Articles Tagged: {tag}"
        
        pdf_service = PDFExportService(db)
        pdf_bytes = pdf_service.export_multiple_articles_to_pdf(
            article_ids=article_ids,
            title=title,
            include_toc=True
        )
        
        safe_tag = "".join(c for c in tag if c.isalnum() or c in ('-', '_'))[:30]
        filename = f"articles_{safe_tag}.pdf"
        
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to export PDF: {str(e)}")