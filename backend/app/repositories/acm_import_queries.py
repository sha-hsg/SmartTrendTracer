"""
MongoDB queries of app.api.acm_import, moved verbatim out of the router
(one function per former inline call site).
"""
from bson import ObjectId
from datetime import datetime
from datetime import timezone
from app.database.mongodb import get_database

db = get_database()


def papers_update_one__process_pdf_background(paper_id, result):
    """papers.update_one from acm_import.process_pdf_background()"""
    return db.papers.update_one(
        {'_id': ObjectId(paper_id)},
        {'$set': {
            'content': result.get('markdown', ''),
            'word_count': len((result.get('markdown', '') or '').split()),
            'markdown_content': result.get('markdown', ''),
            'processed': True,
            'processor_used': result.get('method_used', 'unknown'),
            'processed_at': datetime.now(timezone.utc)
        }}
    )
