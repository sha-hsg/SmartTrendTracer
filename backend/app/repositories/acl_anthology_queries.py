"""
MongoDB queries of app.api.acl_anthology, moved verbatim out of the router
(one function per former inline call site).
"""
from bson import ObjectId
from datetime import datetime
from datetime import timezone
from app.database.mongodb import get_database

db = get_database()


def papers_find_one__import_acl_anthology_paper(dup_conditions):
    """papers.find_one from acl_anthology.import_acl_anthology_paper()"""
    return db.papers.find_one({'$or': dup_conditions})


def papers_insert_one__import_acl_anthology_paper(paper_doc):
    """papers.insert_one from acl_anthology.import_acl_anthology_paper()"""
    return db.papers.insert_one(paper_doc)


def tag_instances_insert_many__import_acl_anthology_paper(tag_instances):
    """tag_instances.insert_many from acl_anthology.import_acl_anthology_paper()"""
    return db.tag_instances.insert_many(tag_instances)


def papers_find_one__process_pdf_background(paper_id):
    """papers.find_one from acl_anthology.process_pdf_background()"""
    return db.papers.find_one({'_id': ObjectId(paper_id)})


def papers_update_one__process_pdf_background(paper_id, result):
    """papers.update_one from acl_anthology.process_pdf_background()"""
    return db.papers.update_one(
        {'_id': ObjectId(paper_id)},
        {'$set': {
            'content': result.get('markdown', ''),
            'processed': True,
            'processor_used': result.get('method_used', 'unknown'),
            'processed_at': datetime.now(timezone.utc)
        }}
    )

