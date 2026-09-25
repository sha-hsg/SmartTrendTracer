"""
API endpoints for PDF export functionality - MongoDB version
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from bson import ObjectId

from app.services.pdf_export_service import PDFExportService
from app.database.mongodb import get_database
from app.repositories import articles as articles_repo

router = APIRouter()

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
        article = articles_repo.find_article_by_any_id(article_id)

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
