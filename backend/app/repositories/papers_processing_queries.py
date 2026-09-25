"""
MongoDB queries of app.api.papers.processing, moved verbatim out of the router
(one function per former inline call site).
"""
from bson import ObjectId
from datetime import datetime
from datetime import timezone
from app.database.mongodb import get_database

db = get_database()


def papers_update_one__cancel_processing(paper):
    """papers.update_one from papers.processing.cancel_processing()"""
    return db.papers.update_one(
        {'_id': paper['_id']},
        {'$set': {
            'processing_status': 'cancelled',
            'processing_cancelled_at': datetime.now(timezone.utc)
        }}
    )


def papers_update_one__process_paper_with_mineru(paper):
    """papers.update_one from papers.processing.process_paper_with_mineru()"""
    return db.papers.update_one(
        {'_id': paper['_id']},
        {'$set': {
            'processing_status': 'processing_with_mineru',
            'processing_started_at': datetime.now(timezone.utc)
        }}
    )


def papers_update_one__process_paper_pdf(update_data, paper):
    """papers.update_one from papers.processing.process_paper_pdf()"""
    return db.papers.update_one(
        {'_id': paper['_id']},
        {'$set': update_data}
    )


def papers_find_one__receive_marker_progress(paper_id):
    """papers.find_one from papers.processing.receive_marker_progress()"""
    return db.papers.find_one({'_id': ObjectId(paper_id) if len(paper_id) == 24 else paper_id})


def papers_update_one__receive_marker_progress(progress_update, paper_id):
    """papers.update_one from papers.processing.receive_marker_progress()"""
    return db.papers.update_one(
        {'_id': ObjectId(paper_id) if len(paper_id) == 24 else paper_id},
        {'$set': progress_update}
    )


def papers_find_one__process_paper_with_marker(paper_id):
    """papers.find_one from papers.processing.process_paper_with_marker()"""
    return db.papers.find_one({'_id': ObjectId(paper_id)})


def papers_find_one__process_paper_with_marker_2(paper_id):
    """papers.find_one from papers.processing.process_paper_with_marker()"""
    return db.papers.find_one({'old_sqlite_id': int(paper_id)})


def papers_find_one__process_paper_with_mineru(paper_id):
    """papers.find_one from papers.processing.process_paper_with_mineru()"""
    return db.papers.find_one({'_id': ObjectId(paper_id)})


def papers_find_one__process_paper_with_mineru_2(paper_id):
    """papers.find_one from papers.processing.process_paper_with_mineru()"""
    return db.papers.find_one({'old_sqlite_id': int(paper_id)})
