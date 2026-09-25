"""
MongoDB queries of app.api.papers.processing_helpers, moved verbatim out of the router
(one function per former inline call site).
"""
from app.repositories.papers import paper_filter as _paper_filter
from bson import ObjectId
from datetime import datetime
from datetime import timezone
from app.database.mongodb import get_database

db = get_database()


def papers_find_one___processing_cancelled(paper_id):
    """papers.find_one from papers.processing_helpers._processing_cancelled()"""
    return db.papers.find_one(_paper_filter(paper_id), {'processing_status': 1})


def papers_update_one__process_with_marker_background(paper_id):
    """papers.update_one from papers.processing_helpers.process_with_marker_background()"""
    return db.papers.update_one(
        {'_id': ObjectId(paper_id) if len(paper_id) == 24 else paper_id},
        {'$set': {
            'processing_status': 'processing_with_marker',
            'processing_started_at': datetime.now(timezone.utc)
        }}
    )


def papers_update_one__process_with_marker_background_2(paper_id, error_msg):
    """papers.update_one from papers.processing_helpers.process_with_marker_background()"""
    return db.papers.update_one(
        {'_id': ObjectId(paper_id) if len(paper_id) == 24 else paper_id},
        {'$set': {
            'processing_status': 'failed',
            'processing_error': error_msg
        }}
    )


def papers_update_one__process_with_mineru_background(paper_id):
    """papers.update_one from papers.processing_helpers.process_with_mineru_background()"""
    return db.papers.update_one(
        {'_id': ObjectId(paper_id) if len(paper_id) == 24 else paper_id},
        {'$set': {
            'processing_status': 'processing_with_mineru',
            'processing_started_at': datetime.now(timezone.utc)
        }}
    )


def papers_update_one__process_with_mineru_background_2(paper_id, update_data):
    """papers.update_one from papers.processing_helpers.process_with_mineru_background()"""
    return db.papers.update_one(
        _paper_filter(paper_id),
        {'$set': update_data}
    )


def papers_update_one__process_with_mineru_background_3(paper_id, error_msg):
    """papers.update_one from papers.processing_helpers.process_with_mineru_background()"""
    return db.papers.update_one(
        _paper_filter(paper_id),
        {'$set': {
            'processing_status': 'failed',
            'processing_error': f"MinerU processing error: {error_msg}"
        }}
    )


def papers_update_one__process_with_marker_background_3(paper_id, error_msg):
    """papers.update_one from papers.processing_helpers.process_with_marker_background()"""
    return db.papers.update_one(
        _paper_filter(paper_id),
        {'$set': {
            'processing_status': 'failed',
            'processing_error': error_msg
        }}
    )


def papers_update_one__process_with_marker_background_4(paper_id, error_msg):
    """papers.update_one from papers.processing_helpers.process_with_marker_background()"""
    return db.papers.update_one(
        _paper_filter(paper_id),
        {'$set': {
            'processing_status': 'failed',
            'processing_error': error_msg
        }}
    )


def papers_update_one__process_with_marker_background_5(paper_id, error_msg):
    """papers.update_one from papers.processing_helpers.process_with_marker_background()"""
    return db.papers.update_one(
        _paper_filter(paper_id),
        {'$set': {
            'processing_status': 'failed',
            'processing_error': error_msg
        }}
    )


def papers_update_one__process_with_mineru_background_4(paper_id, error_msg):
    """papers.update_one from papers.processing_helpers.process_with_mineru_background()"""
    return db.papers.update_one(
        _paper_filter(paper_id),
        {'$set': {
            'processing_status': 'failed',
            'processing_error': error_msg
        }}
    )


def papers_update_one__process_with_marker_background_6(paper_id, update_data):
    """papers.update_one from papers.processing_helpers.process_with_marker_background()"""
    return db.papers.update_one(
        _paper_filter(paper_id),
        {'$set': update_data}
    )


def papers_update_one__process_with_marker_background_7(paper_id, user_error):
    """papers.update_one from papers.processing_helpers.process_with_marker_background()"""
    return db.papers.update_one(
        _paper_filter(paper_id),
        {'$set': {
            'processing_status': 'failed',
            'processing_error': user_error
        }}
    )
