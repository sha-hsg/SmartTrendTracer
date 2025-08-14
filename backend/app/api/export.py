"""
Export API endpoints for articles and annotations
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import Response, FileResponse
from typing import List, Optional
from sqlalchemy.orm import Session
import tempfile
import os

from app.models import get_db
from app.services.export_service import ExportService

router = APIRouter()

@router.get("/articles/json")
def export_articles_json(
    article_ids: Optional[List[int]] = Query(None),
    db: Session = Depends(get_db)
):
    """Export articles as JSON"""
    try:
        export_service = ExportService(db)
        json_data = export_service.export_articles_json(article_ids)
        
        return Response(
            content=json_data,
            media_type="application/json",
            headers={
                "Content-Disposition": "attachment; filename=substack_articles.json"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/articles/markdown")
def export_articles_markdown(
    article_ids: Optional[List[int]] = Query(None),
    db: Session = Depends(get_db)
):
    """Export articles as Markdown"""
    try:
        export_service = ExportService(db)
        markdown_data = export_service.export_articles_markdown(article_ids)
        
        return Response(
            content=markdown_data,
            media_type="text/markdown",
            headers={
                "Content-Disposition": "attachment; filename=substack_articles.md"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/articles/html")
def export_articles_html(
    article_ids: Optional[List[int]] = Query(None),
    db: Session = Depends(get_db)
):
    """Export articles as HTML"""
    try:
        export_service = ExportService(db)
        html_data = export_service.export_articles_html(article_ids)
        
        return Response(
            content=html_data,
            media_type="text/html",
            headers={
                "Content-Disposition": "attachment; filename=substack_articles.html"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/snippets/csv")
def export_snippets_csv(
    article_ids: Optional[List[int]] = Query(None),
    db: Session = Depends(get_db)
):
    """Export all snippets/highlights as CSV"""
    try:
        export_service = ExportService(db)
        csv_data = export_service.export_snippets_csv(article_ids)
        
        return Response(
            content=csv_data,
            media_type="text/csv",
            headers={
                "Content-Disposition": "attachment; filename=substack_highlights.csv"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/reading-list")
def export_reading_list(
    article_ids: Optional[List[int]] = Query(None),
    db: Session = Depends(get_db)
):
    """Export a simple reading list"""
    try:
        export_service = ExportService(db)
        reading_list = export_service.export_reading_list(article_ids)
        
        return Response(
            content=reading_list,
            media_type="text/markdown",
            headers={
                "Content-Disposition": "attachment; filename=reading_list.md"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/bundle")
def create_export_bundle(
    article_ids: Optional[List[int]] = Query(None),
    formats: List[str] = Query(["json", "markdown"]),
    db: Session = Depends(get_db)
):
    """Create a bundle with multiple export formats"""
    try:
        export_service = ExportService(db)
        
        # Create temporary directory for bundle
        with tempfile.TemporaryDirectory() as temp_dir:
            files_created = []
            
            # Generate requested formats
            if "json" in formats:
                json_data = export_service.export_articles_json(article_ids)
                json_path = os.path.join(temp_dir, "articles.json")
                with open(json_path, "w", encoding="utf-8") as f:
                    f.write(json_data)
                files_created.append("articles.json")
            
            if "markdown" in formats:
                md_data = export_service.export_articles_markdown(article_ids)
                md_path = os.path.join(temp_dir, "articles.md")
                with open(md_path, "w", encoding="utf-8") as f:
                    f.write(md_data)
                files_created.append("articles.md")
            
            if "html" in formats:
                html_data = export_service.export_articles_html(article_ids)
                html_path = os.path.join(temp_dir, "articles.html")
                with open(html_path, "w", encoding="utf-8") as f:
                    f.write(html_data)
                files_created.append("articles.html")
            
            if "csv" in formats:
                csv_data = export_service.export_snippets_csv(article_ids)
                csv_path = os.path.join(temp_dir, "highlights.csv")
                with open(csv_path, "w", encoding="utf-8") as f:
                    f.write(csv_data)
                files_created.append("highlights.csv")
            
            if "reading-list" in formats:
                reading_data = export_service.export_reading_list(article_ids)
                reading_path = os.path.join(temp_dir, "reading_list.md")
                with open(reading_path, "w", encoding="utf-8") as f:
                    f.write(reading_data)
                files_created.append("reading_list.md")
            
            # Create ZIP archive
            import zipfile
            zip_path = os.path.join(temp_dir, "export_bundle.zip")
            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                for file_name in files_created:
                    file_path = os.path.join(temp_dir, file_name)
                    zipf.write(file_path, file_name)
            
            # Read zip file
            with open(zip_path, "rb") as f:
                zip_data = f.read()
            
            return Response(
                content=zip_data,
                media_type="application/zip",
                headers={
                    "Content-Disposition": "attachment; filename=substack_export.zip"
                }
            )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))