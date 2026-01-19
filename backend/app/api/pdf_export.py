"""
API endpoints for PDF export functionality - MongoDB version
"""
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response
from typing import List, Optional
from pydantic import BaseModel
from bson import ObjectId
from datetime import datetime, timedelta

from app.services.pdf_export_service import PDFExportService
from app.database.mongodb import get_database

router = APIRouter()

class BulkExportRequest(BaseModel):
    """Request model for bulk PDF export"""
    article_ids: List[str]  # Changed to str to support MongoDB ObjectIds
    title: Optional[str] = "Article Collection"
    include_toc: bool = True

@router.get("/article/{article_id}")
def export_article_pdf(
    article_id: str,  # Changed to str to support MongoDB ObjectIds
):
    """
    Export a single article to PDF
    """
    try:
        db = get_database()
        pdf_service = PDFExportService(db)
        pdf_bytes = pdf_service.export_article_to_pdf(article_id)

        # Get article for filename
        article = None
        try:
            if len(article_id) == 24:
                article = db.articles.find_one({'_id': ObjectId(article_id)})
            else:
                article = db.articles.find_one({'old_sqlite_id': int(article_id)})
        except:
            pass

        if article and article.get('title'):
            # Create safe filename
            safe_title = "".join(c for c in article['title'] if c.isalnum() or c in (' ', '-', '_'))[:50]
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
):
    """
    Export multiple articles to a single PDF
    """
    try:
        if not request.article_ids:
            raise ValueError("No article IDs provided")

        db = get_database()
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
    author_id: str,  # Changed to str to support MongoDB ObjectIds
):
    """
    Export all articles from a specific author to PDF
    """
    try:
        db = get_database()
        pdf_service = PDFExportService(db)
        pdf_bytes = pdf_service.export_author_articles_to_pdf(author_id)

        # Get author for filename
        author = None
        try:
            if len(author_id) == 24:
                author = db.substack_authors.find_one({'_id': ObjectId(author_id)})
            else:
                author = db.substack_authors.find_one({'sqlite_id': int(author_id)})
        except:
            pass

        if author and author.get('name'):
            safe_name = "".join(c for c in author['name'] if c.isalnum() or c in (' ', '-', '_'))[:30]
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
):
    """
    Export recent articles to PDF
    """
    try:
        db = get_database()

        # Get recent articles
        cutoff_date = datetime.now() - timedelta(days=days)

        articles = list(db.articles.find({
            'published_at': {'$gte': cutoff_date}
        }).sort('published_at', -1).limit(limit))

        if not articles:
            raise ValueError(f"No articles found in the last {days} days")

        article_ids = [str(article['_id']) for article in articles]
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
):
    """
    Export articles with a specific tag to PDF
    """
    try:
        db = get_database()

        # Get articles with this tag
        # Find tag instances with this concept slug
        tag_instances = list(db.tag_instances.find({
            'source_type': 'article',
            'tag_slug': tag
        }))

        if not tag_instances:
            raise ValueError(f"No articles found with tag '{tag}'")

        article_ids = [str(ti['source_id']) for ti in tag_instances]
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
