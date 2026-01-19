"""
API endpoints for importing articles from URLs
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, HttpUrl
from typing import Optional

from app.services.url_article_importer import URLArticleImporter

router = APIRouter()

class URLImportRequest(BaseModel):
    url: HttpUrl
    
class URLImportResponse(BaseModel):
    success: bool
    article_id: Optional[int] = None
    title: Optional[str] = None
    author: Optional[str] = None
    word_count: Optional[int] = None
    error: Optional[str] = None

@router.post("/import-url", response_model=URLImportResponse)
def import_article_from_url(
    request: URLImportRequest,
):
    """
    Import an article from a URL
    
    Supports:
    - Substack articles
    - Medium articles
    - Blog posts
    - General web articles
    """
    
    importer = URLArticleImporter(db)
    result = importer.import_from_url(str(request.url))
    
    if not result['success']:
        # Return error but don't raise exception for better UX
        return URLImportResponse(
            success=False,
            error=result.get('error', 'Unknown error occurred'),
            article_id=result.get('article_id')  # Include ID if article exists
        )
    
    return URLImportResponse(
        success=True,
        article_id=result['article_id'],
        title=result['title'],
        author=result['author'],
        word_count=result['word_count']
    )

@router.post("/import-batch")
def import_multiple_urls(
    urls: list[str],
):
    """
    Import multiple articles from URLs
    """
    importer = URLArticleImporter(db)
    results = []
    
    for url in urls:
        try:
            result = importer.import_from_url(url)
            results.append({
                'url': url,
                **result
            })
        except Exception as e:
            results.append({
                'url': url,
                'success': False,
                'error': str(e)
            })
    
    # Summary statistics
    successful = sum(1 for r in results if r['success'])
    failed = len(results) - successful
    
    return {
        'total': len(results),
        'successful': successful,
        'failed': failed,
        'results': results
    }