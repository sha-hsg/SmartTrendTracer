"""
JAIR (Journal of Artificial Intelligence Research) import API endpoints.
"""
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, HttpUrl

from app.database.mongodb import get_database
from app.services.jair_service import jair_service

db = get_database()
logger = logging.getLogger(__name__)
router = APIRouter()


class JAIRParseRequest(BaseModel):
    url: HttpUrl


class JAIRImportRequest(BaseModel):
    url: HttpUrl
    add_tags: Optional[list[str]] = None


def _parse_publication_date(date_raw: str) -> Optional[datetime]:
    """Parse JAIR citation_date strings (e.g. '2024/01/15') into a datetime."""
    if not date_raw:
        return None
    for fmt in ('%Y/%m/%d', '%Y-%m-%d', '%Y/%m', '%Y-%m', '%Y'):
        try:
            return datetime.strptime(date_raw.strip(), fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    logger.warning(f"Could not parse JAIR publication date: {date_raw!r}")
    return None


@router.post("/parse")
async def parse_jair_url(request: JAIRParseRequest) -> Dict[str, Any]:
    """Parse a JAIR URL to preview metadata before importing."""
    try:
        url = str(request.url)
        if 'jair.org' not in url:
            raise HTTPException(status_code=400, detail="URL must be from jair.org")

        metadata = jair_service.parse_jair_url(url)
        if not metadata:
            raise HTTPException(status_code=404, detail="Could not extract metadata from JAIR page")

        return {
            "success": True,
            "metadata": metadata,
            "pdf_url": metadata.get('pdf_url'),
            "message": f"Successfully parsed paper: {metadata.get('title', 'Unknown')}",
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error parsing JAIR URL: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/import")
async def import_jair_paper(request: JAIRImportRequest) -> Dict[str, Any]:
    """Import a paper from JAIR: parse metadata, download PDF, create DB record."""
    try:
        url = str(request.url)
        if 'jair.org' not in url:
            raise HTTPException(status_code=400, detail="URL must be from jair.org")

        # Parse metadata first to get DOI for duplicate check
        metadata = jair_service.parse_jair_url(url)
        doi = metadata.get('doi', '')

        # Check for duplicates
        dup_query = {'$or': [{'import_url': url}]}
        if doi:
            dup_query['$or'].append({'doi': doi})
        existing = db.papers.find_one(dup_query)

        if existing:
            return {
                "success": False,
                "message": "Paper already exists in database",
                "paper_id": str(existing['_id']),
                "existing": True,
            }

        # Download PDF
        save_dir = Path("data/papers")
        save_dir.mkdir(parents=True, exist_ok=True)

        if not metadata.get('pdf_url'):
            raise HTTPException(status_code=404, detail="Could not find PDF URL on JAIR page")

        pdf_path = jair_service.download_pdf(
            metadata['pdf_url'], save_dir, metadata.get('title', '')
        )

        # Build paper document
        paper_doc = {
            'title': metadata.get('title', ''),
            'authors': metadata.get('authors', ''),
            'authors_detailed': metadata.get('authors_detailed', []),
            'abstract': metadata.get('abstract', ''),
            'pdf_path': pdf_path,
            'pdf_url': metadata.get('pdf_url', ''),
            'doi': doi,
            'journal': metadata.get('journal', 'Journal of Artificial Intelligence Research'),
            'volume': metadata.get('volume', ''),
            'year': metadata.get('year'),
            'publication_date': _parse_publication_date(metadata.get('date_raw', '')),
            'published_date_raw': metadata.get('date_raw', ''),
            'keywords': metadata.get('keywords', []),
            'source': 'jair',
            'import_source': 'jair',
            'import_url': url,
            'jair_article_id': metadata.get('jair_article_id'),
            'created_at': datetime.now(timezone.utc),
            'processed': False,
            'paper_type': 'research',
        }

        result = db.papers.insert_one(paper_doc)
        paper_id = str(result.inserted_id)

        logger.info(f"Imported JAIR paper '{metadata.get('title')}' with ID {paper_id}")

        return {
            "success": True,
            "paper_id": paper_id,
            "title": metadata.get('title', ''),
            "message": f"Successfully imported: {metadata.get('title', '')}",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error importing JAIR paper: {e}")
        raise HTTPException(status_code=500, detail=str(e))
