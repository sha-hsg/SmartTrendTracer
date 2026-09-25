"""
Data access for app.api.papers.grobid (extracted by the arch-audit refactor).

GROBID processing and metadata route handlers.

Covers: process_with_grobid (run GROBID on a paper PDF),
get_grobid_metadata (retrieve stored GROBID results),
and update_paper_metadata_grobid (update paper metadata fields).
"""
from app.repositories.errors import NotFoundError
from bson import ObjectId

from app.database.mongodb import get_database

db = get_database()




def get_grobid_metadata(paper_id):
    """Get GROBID metadata for a paper"""
    try:
        # Get paper from MongoDB
        if len(paper_id) == 24:
            paper = db.papers.find_one({'_id': ObjectId(paper_id)})
        else:
            paper = db.papers.find_one({'old_sqlite_id': int(paper_id)})
    except Exception:
        paper = None

    if not paper:
        raise NotFoundError("Paper not found")

    grobid_metadata = paper.get('grobid_metadata')
    if not grobid_metadata:
        return {"success": False, "message": "No GROBID metadata available"}

    return {
        "success": True,
        "grobid_metadata": grobid_metadata,
        "metadata": grobid_metadata,
        "metadata_extracted": bool(grobid_metadata.get('metadata')),
        "references_extracted": len(grobid_metadata.get('references', [])),
        "sections_extracted": len(grobid_metadata.get('sections', [])),
        "citations_extracted": len(grobid_metadata.get('citation_contexts', [])),
        "processed_at": paper.get('grobid_processed_at')
    }

