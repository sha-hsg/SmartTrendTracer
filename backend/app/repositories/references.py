"""
Data access for app.api.references (extracted by the arch-audit refactor).

API endpoints for managing references in the normalized references collection
"""
from app.repositories.errors import InvalidInputError, NotFoundError
from bson import ObjectId
from datetime import datetime, timezone
import re

from app.database.mongodb import get_database

db = get_database()




def get_all_references(search, year, has_doi, in_system, min_citations, limit, offset):
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



def get_top_cited_references(limit):
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



def get_importable_references(limit):
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



def get_reference_statistics():
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



def generate_bibtex(reference_id):
    """Generate BibTeX entry for a reference"""
    
    try:
        ref = db.references.find_one({'_id': ObjectId(reference_id)})
    except Exception:
        raise InvalidInputError("Invalid reference ID")
    
    if not ref:
        raise NotFoundError("Reference not found")
    
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



def find_reference(reference_id):
    """Reference by id; raises InvalidInputError for malformed ids (None if absent)."""
    try:
        return db.references.find_one({'_id': ObjectId(reference_id)})
    except Exception:
        raise InvalidInputError("Invalid reference ID")


def mark_reference_imported(ref, paper_id):
    """Flag a reference as imported and link every citing paper to the new paper."""
    db.references.update_one(
        {'_id': ref['_id']},
        {
            '$set': {
                'is_in_system': True,
                'paper_id': ObjectId(paper_id),
                'imported_at': datetime.now(timezone.utc)
            }
        }
    )
    for citing_paper_id in ref.get('cited_by', []):
        db.paper_citations.insert_one({
            'citing_paper': citing_paper_id,
            'cited_paper': ObjectId(paper_id),
            'reference_id': ref['_id'],
            'created_at': datetime.now(timezone.utc)
        })


def _normalize_title(title: str) -> str:
    return ' '.join(re.sub(r'[^\w\s]', '', (title or '').lower()).split())


def reference_hash(ref: dict) -> str:
    """Dedup key: DOI, else arXiv id, else title(+year) — as in the original migration."""
    import hashlib
    if (ref.get('doi') or '').strip():
        return f"doi:{ref['doi'].strip().lower()}"
    if (ref.get('arxiv_id') or '').strip():
        return f"arxiv:{ref['arxiv_id'].strip().lower()}"
    title, year = _normalize_title(ref.get('title', '')), str(ref.get('year') or '').strip()
    if title:
        return 'title:' + hashlib.md5((f'{title}:{year}' if year else title).encode()).hexdigest()
    return 'raw:' + hashlib.md5(str(sorted(ref.items())).encode()).hexdigest()


def sync_paper_references(paper_id, refs) -> int:
    """Upsert a paper's extracted references into the references collection
    (cited_by gets the paper) and link them on the paper. The collection was
    built once by a migration (2025-09) and never updated afterwards."""
    ids = []
    now = datetime.now(timezone.utc)
    for ref in refs or []:
        if not isinstance(ref, dict):
            continue
        h = reference_hash(ref)
        existing = db.references.find_one({'reference_hash': h}, {'_id': 1, 'cited_by': 1})
        if existing:
            if paper_id not in (existing.get('cited_by') or []):
                db.references.update_one({'_id': existing['_id']},
                                         {'$addToSet': {'cited_by': paper_id}, '$inc': {'citation_count': 1},
                                          '$set': {'updated_at': now}})
            ids.append(existing['_id'])
            continue
        authors = ref.get('authors') or []
        if isinstance(authors, str):
            authors = [a.strip() for a in authors.split(',') if a.strip()]
        ids.append(db.references.insert_one({
            'reference_hash': h, 'title': ref.get('title', ''), 'normalized_title': _normalize_title(ref.get('title', '')),
            'authors': authors, 'year': ref.get('year'), 'venue': ref.get('venue', ''), 'doi': ref.get('doi', ''),
            'arxiv_id': ref.get('arxiv_id', ''), 'pages': ref.get('pages', ''), 'url': ref.get('url', ''),
            'bibtex': ref.get('bibtex', ''), 'raw_citation': ref.get('raw_citation', ''), 'cited_by': [paper_id],
            'citation_count': 1, 'is_in_system': False, 'created_at': now, 'updated_at': now,
            'source': 'grobid', 'grobid_id': ref.get('id', '')}).inserted_id)
    db.papers.update_one({'_id': paper_id}, {'$set': {'reference_ids': ids, 'references_migrated': True}})
    return len(ids)
