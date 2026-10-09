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



def store_grobid_result(paper, result, overwrite_authors: bool = True) -> dict:
    """Persist a GROBIDService.process_pdf() result on the paper (TEI, BibTeX,
    references, sections, citation contexts; authors only when allowed or
    missing — the automatic run must not replace good import metadata) and
    sync the references into the normalized references collection."""
    from datetime import datetime, timezone
    update = {'grobid_metadata': result, 'grobid_processed': True,
              'grobid_processed_at': datetime.now(timezone.utc)}
    tei = (result.get('full_document') or {}).get('tei_xml') if result.get('success') else None
    if tei:
        update['tei_xml'] = tei
    meta = result.get('metadata') or {}
    if meta.get('bibtex_raw'):
        update['bibtex'] = meta['bibtex_raw']
    authors = meta.get('authors')
    if isinstance(authors, list) and authors and (overwrite_authors or not paper.get('authors')):
        names, detailed = [], []
        for a in authors:
            if isinstance(a, dict) and a.get('name'):
                names.append(a['name'])
                detailed.append(a)
            elif isinstance(a, str) and a.strip():
                names.append(a.strip())
                detailed.append({'name': a.strip()})
        if names:
            update['authors'] = ', '.join(names)
            update['authors_detailed'] = detailed
    for key in ('references', 'citation_contexts'):
        if result.get(key):
            update[key] = result[key]
    if result.get('sections') and (overwrite_authors or not paper.get('sections')):
        update['sections'] = result['sections']
    db.papers.update_one({'_id': paper['_id']}, {'$set': update})
    synced = 0
    if result.get('references'):
        from app.repositories.references import sync_paper_references
        synced = sync_paper_references(paper['_id'], result['references'])
    return {'references': len(result.get('references') or []), 'synced': synced,
            'sections': len(result.get('sections') or []),
            'citations': len(result.get('citation_contexts') or [])}


def papers_needing_grobid(limit: int):
    """Processed research papers with a PDF that GROBID has not seen yet."""
    return list(db.papers.find({'processed': True, 'pdf_path': {'$nin': [None, '']},
                                'paper_type': {'$ne': 'review'}, 'grobid_processed': {'$ne': True},
                                'grobid_failed_at': {'$exists': False}},
                               {'pdf_path': 1, 'authors': 1, 'sections': 1}).sort('created_at', -1).limit(limit))


def mark_grobid_failed(paper_id, error: str) -> None:
    from datetime import datetime, timezone
    db.papers.update_one({'_id': paper_id}, {'$set': {'grobid_failed_at': datetime.now(timezone.utc),
                                                      'grobid_error': error[:300]}})
