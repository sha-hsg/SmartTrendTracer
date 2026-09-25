"""
DBLP API endpoints - MongoDB version
Provides DBLP bibliography search and metadata extraction without SQLite dependencies
"""

from fastapi import APIRouter, Query, HTTPException, Path
from typing import Dict, Any, Optional
import logging
from datetime import datetime, timezone
from bson import ObjectId
from app.services.dblp_service import DBLPService
from app.repositories import dblp_queries as queries

logger = logging.getLogger(__name__)


# Create two routers - one for /api/dblp and one for /api/papers/dblp
router = APIRouter(prefix="/api/dblp", tags=["dblp"])
papers_router = APIRouter(prefix="/api/papers/dblp", tags=["dblp"])

# Initialize DBLP service
dblp_service = DBLPService()

@router.get("/bibtex")
async def get_bibtex(
    dblp_key: Optional[str] = Query(None, description="DBLP key identifier"),
    dblp_url: Optional[str] = Query(None, description="Full DBLP URL")
) -> Dict[str, Any]:
    """
    Get BibTeX citation for a specific DBLP entry
    
    Provide either dblp_key or dblp_url
    """
    try:
        if not dblp_key and not dblp_url:
            raise HTTPException(
                status_code=400, 
                detail="Either dblp_key or dblp_url must be provided"
            )
        
        bibtex = None
        
        if dblp_key:
            bibtex = dblp_service.get_bibtex(dblp_key)
        elif dblp_url:
            bibtex = dblp_service.get_bibtex_from_url(dblp_url)
        
        if not bibtex:
            raise HTTPException(status_code=404, detail="BibTeX not found")
        
        return {
            "bibtex": bibtex,
            "dblp_key": dblp_key,
            "dblp_url": dblp_url
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching BibTeX: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching BibTeX: {str(e)}")

@router.get("/metadata/{dblp_key:path}")
async def get_metadata(dblp_key: str = Path(..., description="DBLP key identifier")) -> Dict[str, Any]:
    """
    Get complete metadata for a DBLP entry by its key
    """
    try:
        metadata = dblp_service.get_complete_metadata(dblp_key)
        
        if not metadata:
            raise HTTPException(status_code=404, detail="Metadata not found")
        
        # Generate BibTeX from metadata if not already present
        if 'bibtex' not in metadata:
            metadata['bibtex'] = dblp_service.generate_bibtex_from_metadata(metadata)
        
        return metadata
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching metadata: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching metadata: {str(e)}")

# Add the same endpoints to papers_router for /api/papers/dblp/...
@papers_router.get("/search")
async def search_dblp_papers(
    title: str = Query(..., description="Paper title to search for"),
    max_results: int = Query(20, ge=1, le=100, description="Maximum number of results")
) -> Dict[str, Any]:
    """
    Search DBLP bibliography database from papers context
    """
    try:
        results = dblp_service.search_papers(title, max_results=max_results)
        return {
            "query": title,
            "count": len(results),
            "results": results
        }
    except Exception as e:
        logger.error(f"Error searching DBLP: {e}")
        raise HTTPException(status_code=500, detail=f"Error searching DBLP: {str(e)}")
@router.post("/attach-metadata/{paper_id}")
async def attach_dblp_metadata(
    paper_id: str,
    dblp_key: str = Query(..., description="DBLP key identifier"),
    overwrite: bool = Query(False, description="Overwrite existing metadata"),
) -> Dict[str, Any]:
    """
    Attach DBLP metadata to an existing paper in MongoDB
    
    Updates the paper with:
    - Complete author information
    - Publication venue and date
    - DOI and other identifiers
    - Conference/journal information
    - BibTeX citation
    """
    try:
        # Try to find paper by ObjectId or old SQLite ID
        paper = None
        try:
            if len(paper_id) == 24:
                paper = queries.papers_find_one__attach_dblp_metadata(paper_id)
            else:
                paper = queries.papers_find_one__attach_dblp_metadata_2(paper_id)
        except Exception:
            pass
            
        if not paper:
            raise HTTPException(status_code=404, detail=f"Paper not found: {paper_id}")
        
        # Fetch DBLP metadata
        metadata = dblp_service.get_complete_metadata(dblp_key)
        if not metadata:
            raise HTTPException(status_code=404, detail="DBLP metadata not found")
        
        # Track what was updated
        updated_fields = []
        
        # Prepare update data
        update_data = {}
        
        # Update BibTeX - always update this if we have it
        if metadata.get('official_bibtex') or metadata.get('bibtex'):
            bibtex = metadata.get('official_bibtex') or metadata.get('bibtex')
            update_data['bibtex'] = bibtex
            updated_fields.append('bibtex')
        
        # Update authors if empty or overwriting
        if metadata.get('authors'):
            current_authors = paper.get('authors', [])
            if not current_authors or overwrite:
                # Canonical schema: 'authors' = comma-separated string,
                # 'authors_detailed' = array of author objects
                author_names = []
                for author in metadata['authors']:
                    name = author.get('name', '') if isinstance(author, dict) else str(author)
                    if name:
                        author_names.append(name)
                update_data['authors'] = ', '.join(author_names)
                update_data['authors_detailed'] = [
                    {'name': name, 'affiliation': '', 'email': ''}
                    for name in author_names
                ]
                updated_fields.extend(['authors', 'authors_detailed'])
        
        # Update venue (conference/journal)
        if metadata.get('venue'):
            venue = metadata['venue']
            if metadata.get('type') == 'article':
                if not paper.get('journal') or overwrite:
                    update_data['journal'] = venue
                    updated_fields.append('journal')
            else:
                if not paper.get('conference') or overwrite:
                    update_data['conference'] = venue
                    updated_fields.append('conference')
        
        # Update year if available
        if metadata.get('year'):
            if not paper.get('year') or overwrite:
                try:
                    update_data['year'] = int(metadata['year'])
                    updated_fields.append('year')
                except Exception:
                    pass
        
        # Update DOI
        if metadata.get('doi'):
            if not paper.get('doi') or overwrite:
                update_data['doi'] = metadata['doi']
                updated_fields.append('doi')
        
        # Store DBLP identifiers
        update_data['dblp_key'] = dblp_key
        update_data['dblp_url'] = metadata.get('dblp_url', f"https://dblp.org/rec/{dblp_key}")
        update_data['dblp_metadata'] = metadata
        update_data['dblp_attached_at'] = datetime.now(timezone.utc)
        
        # Update the paper in MongoDB
        if update_data:
            result = queries.papers_update_one__attach_dblp_metadata(update_data, paper)
            
            if result.modified_count > 0:
                logger.info(f"Successfully attached DBLP metadata to paper {paper_id}")
            else:
                logger.warning(f"No changes made to paper {paper_id}")
        
        return {
            "success": True,
            "message": f"DBLP metadata attached successfully. Updated fields: {', '.join(updated_fields) if updated_fields else 'None'}",
            "paper_id": str(paper['_id']),
            "dblp_key": dblp_key,
            "updated_fields": updated_fields
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error attaching metadata: {e}")
        raise HTTPException(status_code=500, detail=f"Error attaching metadata: {str(e)}")
