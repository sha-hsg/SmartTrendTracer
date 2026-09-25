"""
MongoDB queries of app.api.arxiv, moved verbatim out of the router
(one function per former inline call site).
"""
from bson import ObjectId
from datetime import datetime
from datetime import timezone
from app.database.mongodb import get_database

db = get_database()




def papers_update_one__import_arxiv_paper(paper_id, process_result):
    """papers.update_one from arxiv.import_arxiv_paper()"""
    return db.papers.update_one(
                                {'_id': ObjectId(paper_id)},
                                {'$set': {
                                    'content': process_result['markdown'],
                                    'processed': True,
                                    'processor_used': process_result.get('method_used', 'unknown'),
                                    'processed_at': datetime.now(timezone.utc)
                                }}
                            )
