"""
Data access for app.api.papers.affiliations (extracted by the arch-audit refactor).

Affiliation extraction and application endpoints.

Split from entities.py -- all route handlers copied verbatim.
"""
from app.repositories.errors import NotFoundError
from bson import ObjectId

from app.database.mongodb import get_database

db = get_database()




def apply_paper_affiliations(paper_id, affiliations_data):
    """Apply selected affiliations to paper authors"""
    try:
        # Try to convert to ObjectId if it's a valid format
        if len(paper_id) == 24:
            paper = db.papers.find_one({'_id': ObjectId(paper_id)})
        else:
            # Try old SQLite ID
            paper = db.papers.find_one({'old_sqlite_id': int(paper_id)})
    except Exception:
        paper = None

    if not paper:
        raise NotFoundError("Paper not found")

    # Get affiliations to apply
    affiliations_to_apply = affiliations_data.get('affiliations', [])

    # Work on authors_detailed (object array, system convention).
    # Fall back to deriving it from the legacy `authors` field if missing.
    authors_detailed = paper.get('authors_detailed') or []
    if not authors_detailed:
        authors_raw = paper.get('authors', [])
        if isinstance(authors_raw, str):
            authors_detailed = [{'name': name.strip()} for name in authors_raw.split(',') if name.strip()]
        elif isinstance(authors_raw, list):
            authors_detailed = [
                author if isinstance(author, dict) else {'name': str(author)}
                for author in authors_raw
            ]

    # Ensure every entry is a dict (defensive against legacy string entries)
    authors_detailed = [
        author if isinstance(author, dict) else {'name': str(author)}
        for author in authors_detailed
    ]

    updated_count = 0
    for affiliation in affiliations_to_apply:
        author_index = affiliation.get('author_index')
        new_affiliation = affiliation.get('affiliation')

        if author_index is not None and 0 <= author_index < len(authors_detailed):
            authors_detailed[author_index]['affiliation'] = new_affiliation
            updated_count += 1

    # Re-derive `authors` as comma-separated string (system convention);
    # NEVER write the dict list into `authors`.
    authors_string = ', '.join(
        author.get('name', '') for author in authors_detailed if author.get('name')
    )

    db.papers.update_one(
        {'_id': paper['_id']},
        {'$set': {
            'authors_detailed': authors_detailed,
            'authors': authors_string
        }}
    )

    return {
        'paper_id': paper_id,
        'updated_count': updated_count,
        'authors': authors_string,
        'authors_detailed': authors_detailed
    }

