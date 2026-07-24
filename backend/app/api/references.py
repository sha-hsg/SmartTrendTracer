"""
API endpoints for managing references in the normalized references collection
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from bson import ObjectId
from app.database.mongodb import get_database
from datetime import datetime, timezone
import logging
import re

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/references", tags=["references"])

# MongoDB connection
db = get_database()

@router.get("/")
async def get_all_references(
    search: Optional[str] = Query(None, description="Search in title, authors, venue"),
    year: Optional[int] = Query(None, description="Filter by year"),
    has_doi: Optional[bool] = Query(None, description="Filter by DOI availability"),
    in_system: Optional[bool] = Query(None, description="Filter by whether paper exists in system"),
    min_citations: Optional[int] = Query(None, description="Minimum citation count"),
    limit: int = Query(100, le=1000),
    offset: int = Query(0, ge=0)
):
    """Get all unique references across all papers with filtering and search"""
    
    # Build query
    query = {}
    
    if search:
        query['$or'] = [
            {'title': {'$regex': search, '$options': 'i'}},
            {'authors': {'$regex': search, '$options': 'i'}},
            {'venue': {'$regex': search, '$options': 'i'}}
        ]
    
    if year:
        query['year'] = year
    
    if has_doi is not None:
        if has_doi:
            query['doi'] = {'$ne': '', '$exists': True}
        else:
            no_doi_clause = {'$or': [{'doi': ''}, {'doi': {'$exists': False}}]}
            if '$or' in query:
                # Combine with the search $or via $and instead of overwriting it
                query['$and'] = [{'$or': query.pop('$or')}, no_doi_clause]
            else:
                query.update(no_doi_clause)
    
    if in_system is not None:
        query['is_in_system'] = in_system
    
    if min_citations:
        query['citation_count'] = {'$gte': min_citations}
    
    # Get total count
    total = db.references.count_documents(query)
    
    # Get references
    references = list(db.references.find(query)
        .sort('citation_count', -1)
        .skip(offset)
        .limit(limit))
    
    # Convert ObjectIds to strings
    for ref in references:
        ref['_id'] = str(ref['_id'])
        if ref.get('paper_id'):
            ref['paper_id'] = str(ref['paper_id'])
        ref['cited_by'] = [str(pid) for pid in ref.get('cited_by', [])]
    
    return {
        'total': total,
        'references': references,
        'offset': offset,
        'limit': limit
    }

@router.get("/top-cited")
async def get_top_cited_references(limit: int = Query(20, le=100)):
    """Get the most cited references across all papers"""
    
    references = list(db.references.find()
        .sort('citation_count', -1)
        .limit(limit))
    
    # Enhance with paper titles that cite them
    for ref in references:
        # Get first 3 citing papers
        citing_paper_ids = ref.get('cited_by', [])[:3]
        citing_papers = list(db.papers.find(
            {'_id': {'$in': citing_paper_ids}},
            {'title': 1}
        ))
        
        ref['citing_papers_sample'] = [
            {'id': str(p['_id']), 'title': p['title']} 
            for p in citing_papers
        ]
        
        # Convert IDs
        ref['_id'] = str(ref['_id'])
        if ref.get('paper_id'):
            ref['paper_id'] = str(ref['paper_id'])
        ref['cited_by'] = [str(pid) for pid in ref.get('cited_by', [])]
    
    return references

@router.get("/importable")
async def get_importable_references(limit: int = Query(50, le=200)):
    """Get references that can be imported as new papers (have DOI/ArXiv but not in system)"""
    
    query = {
        'is_in_system': False,
        '$or': [
            {'doi': {'$ne': '', '$exists': True}},
            {'arxiv_id': {'$ne': '', '$exists': True}}
        ]
    }
    
    references = list(db.references.find(query)
        .sort('citation_count', -1)
        .limit(limit))
    
    # Group by import source
    importable = {
        'arxiv': [],
        'doi': [],
        'total': len(references)
    }
    
    for ref in references:
        ref['_id'] = str(ref['_id'])
        ref['cited_by'] = [str(pid) for pid in ref.get('cited_by', [])]
        
        if ref.get('arxiv_id'):
            importable['arxiv'].append(ref)
        elif ref.get('doi'):
            importable['doi'].append(ref)
    
    return importable

@router.get("/statistics")
async def get_reference_statistics():
    """Get statistics about the references collection"""
    
    stats = {
        'total_references': db.references.count_documents({}),
        'unique_titles': db.references.count_documents({'title': {'$ne': '', '$exists': True}}),
        'references_with_doi': db.references.count_documents({'doi': {'$ne': '', '$exists': True}}),
        'references_with_arxiv': db.references.count_documents({'arxiv_id': {'$ne': '', '$exists': True}}),
        'references_in_system': db.references.count_documents({'is_in_system': True}),
        'importable_references': db.references.count_documents({
            'is_in_system': False,
            '$or': [
                {'doi': {'$ne': '', '$exists': True}},
                {'arxiv_id': {'$ne': '', '$exists': True}}
            ]
        })
    }
    
    # Get top cited references
    top_cited = list(db.references.find()
        .sort('citation_count', -1)
        .limit(5))
    
    stats['top_cited'] = [
        {
            'title': ref.get('title', 'Unknown'),
            'citation_count': ref.get('citation_count', 0),
            'year': ref.get('year')
        }
        for ref in top_cited
    ]
    
    # Get citation distribution
    pipeline = [
        {'$group': {
            '_id': '$citation_count',
            'count': {'$sum': 1}
        }},
        {'$sort': {'_id': 1}}
    ]
    
    distribution = list(db.references.aggregate(pipeline))
    stats['citation_distribution'] = {
        '1_citation': sum(d['count'] for d in distribution if d['_id'] == 1),
        '2-5_citations': sum(d['count'] for d in distribution if 2 <= d['_id'] <= 5),
        '6-10_citations': sum(d['count'] for d in distribution if 6 <= d['_id'] <= 10),
        'over_10_citations': sum(d['count'] for d in distribution if d['_id'] > 10)
    }
    
    return stats

@router.post("/{reference_id}/import")
async def import_reference_as_paper(reference_id: str):
    """Import a reference as a new paper using its DOI or ArXiv ID"""
    
    try:
        ref = db.references.find_one({'_id': ObjectId(reference_id)})
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid reference ID")
    
    if not ref:
        raise HTTPException(status_code=404, detail="Reference not found")
    
    if ref.get('is_in_system'):
        raise HTTPException(status_code=400, detail="Reference already exists as a paper")
    
    # Determine import method
    if ref.get('arxiv_id'):
        # Import from ArXiv
        from app.services.arxiv_import_service import ArxivImportService
        service = ArxivImportService()
        
        try:
            result = await service.import_paper(ref['arxiv_id'])
            
            if result.get('paper_id'):
                # Update reference to mark it as in system
                db.references.update_one(
                    {'_id': ref['_id']},
                    {
                        '$set': {
                            'is_in_system': True,
                            'paper_id': ObjectId(result['paper_id']),
                            'imported_at': datetime.now(timezone.utc)
                        }
                    }
                )
                
                # Create citation links
                for citing_paper_id in ref.get('cited_by', []):
                    db.paper_citations.insert_one({
                        'citing_paper': citing_paper_id,
                        'cited_paper': ObjectId(result['paper_id']),
                        'reference_id': ref['_id'],
                        'created_at': datetime.now(timezone.utc)
                    })
                
                return {
                    'success': True,
                    'paper_id': result['paper_id'],
                    'message': f"Successfully imported from ArXiv: {ref['arxiv_id']}"
                }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to import from ArXiv: {str(e)}")
    
    elif ref.get('doi'):
        # TODO: Implement DOI import (CrossRef, Unpaywall, etc.)
        raise HTTPException(status_code=501, detail="DOI import not yet implemented")
    
    else:
        raise HTTPException(status_code=400, detail="Reference has no DOI or ArXiv ID for import")

@router.post("/{reference_id}/generate-bibtex")
async def generate_bibtex(reference_id: str):
    """Generate BibTeX entry for a reference"""
    
    try:
        ref = db.references.find_one({'_id': ObjectId(reference_id)})
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid reference ID")
    
    if not ref:
        raise HTTPException(status_code=404, detail="Reference not found")
    
    # If BibTeX already exists, return it
    if ref.get('bibtex'):
        return {'bibtex': ref['bibtex']}
    
    # Generate BibTeX

    # Create citation key
    first_author = ""
    if ref.get('authors'):
        if isinstance(ref['authors'], list) and ref['authors']:
            first_author = ref['authors'][0].split()[-1]
        elif isinstance(ref['authors'], str):
            first_author = ref['authors'].split(',')[0].split()[-1]
    
    year = str(ref.get('year', ''))
    title_words = re.sub(r'[^\w\s]', '', ref.get('title', '')).split()[:2]
    
    citation_key = f"{first_author}{year}{''.join(title_words)}"
    citation_key = re.sub(r'[^a-zA-Z0-9]', '', citation_key) or 'unknown'
    
    # Build BibTeX entry
    bibtex = f"@article{{{citation_key},\n"
    
    if ref.get('title'):
        bibtex += f"  title = {{{ref['title']}}},\n"
    
    if ref.get('authors'):
        if isinstance(ref['authors'], list):
            authors_str = ' and '.join(ref['authors'])
        else:
            authors_str = ref['authors']
        bibtex += f"  author = {{{authors_str}}},\n"
    
    if ref.get('year'):
        bibtex += f"  year = {{{ref['year']}}},\n"
    
    if ref.get('venue'):
        bibtex += f"  journal = {{{ref['venue']}}},\n"
    
    if ref.get('pages'):
        bibtex += f"  pages = {{{ref['pages']}}},\n"
    
    if ref.get('doi'):
        bibtex += f"  doi = {{{ref['doi']}}},\n"
    
    if ref.get('arxiv_id'):
        bibtex += f"  eprint = {{{ref['arxiv_id']}}},\n"
        bibtex += f"  archivePrefix = {{arXiv}},\n"
    
    bibtex += "}\n"
    
    # Save generated BibTeX
    db.references.update_one(
        {'_id': ref['_id']},
        {'$set': {'bibtex': bibtex}}
    )
    
    return {'bibtex': bibtex}
