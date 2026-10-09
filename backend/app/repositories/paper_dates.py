"""
One storage form for papers.publication_date: an ISO string "YYYY-MM-DD"
("YYYY-MM" / "YYYY" when only that much is known). Importers write BSON
dates, ISO timestamps, "" or a separate published_date / year field; the
year facet then fell back to the import year (papers from 2010 listed under
2026). normalize_all() is idempotent and run daily (scheduler job
paper_hygiene); published_date / year are folded into publication_date.
"""
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from dateutil import parser as date_parser

from app.database.mongodb import get_database

db = get_database()


def canonical_date(value: Any) -> Optional[str]:
    """ISO date string of a publication date value, or None."""
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, int) and 1900 <= value <= 2100:
        return str(value)
    if not isinstance(value, str):
        return None
    v = value.strip()
    if not v:
        return None
    if len(v) == 4 and v.isdigit():
        return v
    if len(v) == 7 and v[4] == '-' and v[:4].isdigit() and v[5:].isdigit():
        return v
    try:
        parsed = date_parser.parse(v, default=datetime(2000, 1, 1))
    except (ValueError, OverflowError):
        return None
    numeric_date = re.match(r'^\d{4}-\d{2}-\d{2}', v)
    day_token = re.search(r'(?<!\d)\d{1,2}(?!\d)', re.sub(r'\d{4}', '', v))   # a 1-2 digit number besides the year
    if numeric_date or (any(ch.isalpha() for ch in v) and day_token):
        return parsed.date().isoformat()
    if any(ch.isalpha() for ch in v) or re.match(r'^\d{4}[-/]\d{1,2}$', v):
        return parsed.strftime('%Y-%m')                # month known, day not
    return parsed.date().isoformat()


def normalize_all(dry_run: bool = False) -> Dict[str, Any]:
    changed, unparsable = 0, []
    for p in db.papers.find({}, {'publication_date': 1, 'published_date': 1, 'year': 1}):
        current = p.get('publication_date')
        best = canonical_date(current) or canonical_date(p.get('published_date')) or canonical_date(p.get('year'))
        if current not in (None, '') and canonical_date(current) is None:
            unparsable.append(str(p['_id']))
        update: Dict[str, Any] = {}
        if best != current:
            update['$set'] = {'publication_date': best}
        if 'published_date' in p:
            update.setdefault('$unset', {})['published_date'] = ''
        if update:
            changed += 1
            if not dry_run:
                db.papers.update_one({'_id': p['_id']}, update)
    missing = db.papers.count_documents({'publication_date': {'$in': [None, '']}}) + \
        db.papers.count_documents({'publication_date': {'$exists': False}})
    return {'changed': changed, 'unparsable': unparsable[:20], 'missing_after': missing}


def papers_missing_date(limit: int = 200) -> List[Dict[str, Any]]:
    return list(db.papers.find(
        {'$or': [{'publication_date': {'$exists': False}}, {'publication_date': {'$in': [None, '']}}],
         '$and': [{'$or': [{'arxiv_id': {'$nin': [None, '']}}, {'doi': {'$nin': [None, '']}}]}]},
        {'arxiv_id': 1, 'doi': 1, 'title': 1}).limit(limit))


def set_publication_date(paper_id, date: str) -> None:
    db.papers.update_one({'_id': paper_id}, {'$set': {'publication_date': date}})


# --- further paper hygiene (run with the dates by services.paper_hygiene) -------

PLACEHOLDER_ABSTRACT = 'PDF uploaded'


def normalize_arxiv_ids() -> int:
    """Store arXiv ids without prefix/version so duplicate checks match."""
    from app.repositories.papers import arxiv_key
    changed = 0
    for p in db.papers.find({'arxiv_id': {'$regex': r'(^arxiv:)|(v\d+$)', '$options': 'i'}}, {'arxiv_id': 1}):
        db.papers.update_one({'_id': p['_id']}, {'$set': {'arxiv_id': arxiv_key(p['arxiv_id'])}})
        changed += 1
    return changed


def papers_with_placeholder_abstract() -> List[Dict[str, Any]]:
    """Upload placeholder, or no abstract although the text is processed."""
    return list(db.papers.find({'$or': [
        {'abstract': {'$regex': f'^{PLACEHOLDER_ABSTRACT}'}},
        {'abstract': {'$in': [None, '']}, 'content': {'$nin': [None, '']}, 'abstract_checked': {'$ne': True}},
    ]}, {'content': 1}))


def set_abstract(paper_id, abstract: str, checked: bool) -> None:
    # abstract_checked: the processed text has no findable abstract — do not re-scan daily
    db.papers.update_one({'_id': paper_id}, {'$set': {'abstract': abstract, 'abstract_checked': checked}})


def papers_without_md5() -> List[Dict[str, Any]]:
    return list(db.papers.find({'file_md5': {'$exists': False}, 'pdf_path': {'$nin': [None, '']}}, {'pdf_path': 1}))


def set_file_md5(paper_id, md5: str) -> None:
    db.papers.update_one({'_id': paper_id}, {'$set': {'file_md5': md5}})
