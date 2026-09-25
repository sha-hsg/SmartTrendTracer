"""
GROBID processing and metadata route handlers.

Covers: process_with_grobid (run GROBID on a paper PDF),
get_grobid_metadata (retrieve stored GROBID results),
and update_paper_metadata_grobid (update paper metadata fields).
"""

from .utils import (
    # Standard library re-exports used by the handlers
    datetime,
    timezone,
    # typing
    Any,
    Dict,
    # Third-party
    ObjectId,
    APIRouter,
    HTTPException,
    # Shared application state
    db,
    logger,
)
from app.repositories import papers_grobid as repo
from app.repositories import papers_grobid_queries as queries

router = APIRouter()


@router.post("/{paper_id}/grobid/process")
async def process_with_grobid(paper_id: str) -> Dict[str, Any]:
    """Process paper with GROBID service"""
    try:
        # Get paper from MongoDB
        if len(paper_id) == 24:
            paper = queries.papers_find_one__process_with_grobid(paper_id)
        else:
            paper = queries.papers_find_one__process_with_grobid_2(paper_id)
    except Exception:
        paper = None

    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    # Check if PDF exists
    pdf_path = paper.get('pdf_path')
    if not pdf_path:
        raise HTTPException(status_code=400, detail="Paper has no PDF file")

    # Import GROBID service
    from app.services.grobid_service import GROBIDService
    grobid_service = GROBIDService()

    try:
        # Process with GROBID (not async)
        result = grobid_service.process_pdf(pdf_path)

        # Extract TEI XML from the result
        tei_xml = None
        if result.get('success') and result.get('full_document', {}).get('tei_xml'):
            tei_xml = result['full_document']['tei_xml']

        # Store GROBID data in paper
        update_data = {
            'grobid_metadata': result,
            'grobid_processed': True,
            'grobid_processed_at': datetime.now(timezone.utc)
        }

        # Store TEI XML if available
        if tei_xml:
            update_data['tei_xml'] = tei_xml

        # Store BibTeX if available
        if result.get('metadata', {}).get('bibtex_raw'):
            update_data['bibtex'] = result['metadata']['bibtex_raw']

        # Store extracted authors if available
        if result.get('metadata', {}).get('authors'):
            authors = result['metadata']['authors']
            if isinstance(authors, list) and authors:
                # GROBID may return authors as plain strings or as objects.
                # Normalize authors_detailed to {'name': ...} objects — it must
                # never become a list of strings.
                author_names = []
                authors_detailed = []
                for author in authors:
                    if isinstance(author, dict) and 'name' in author:
                        author_names.append(author['name'])
                        authors_detailed.append(author)
                    elif isinstance(author, str) and author.strip():
                        author_names.append(author.strip())
                        authors_detailed.append({'name': author.strip()})

                if author_names:  # Only update if we have valid author names
                    update_data['authors'] = ', '.join(author_names)  # Store as comma-separated string for compatibility
                    update_data['authors_detailed'] = authors_detailed  # Normalized object array

        # Store extracted references in dedicated field
        if result.get('references'):
            update_data['references'] = result['references']

        # Store extracted sections in dedicated field
        if result.get('sections'):
            update_data['sections'] = result['sections']

        # Store citation contexts in dedicated field
        if result.get('citation_contexts'):
            update_data['citation_contexts'] = result['citation_contexts']

        queries.papers_update_one__process_with_grobid(update_data, paper)

        # Format response for frontend
        response = {
            "success": True,
            "metadata": result,
            "metadata_extracted": bool(result.get('metadata')),
            "references_extracted": len(result.get('references', [])),
            "sections_extracted": len(result.get('sections', [])),
            "citations_extracted": len(result.get('citation_contexts', []))
        }

        return response
    except Exception as e:
        logger.error(f"GROBID processing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{paper_id}/grobid/metadata")
def get_grobid_metadata(paper_id: str) -> Dict[str, Any]:
    """Get GROBID metadata for a paper"""
    return repo.get_grobid_metadata(paper_id=paper_id)



# Note: PUT /{paper_id}/metadata is handled in crud.py (update_paper_metadata)
# The GROBID metadata panel in the frontend uses the same endpoint.
