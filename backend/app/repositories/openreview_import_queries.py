"""
MongoDB queries of app.api.openreview_import, moved verbatim out of the router
(one function per former inline call site).
"""
from bson import ObjectId
from datetime import datetime
from datetime import timezone
from app.database.mongodb import get_database

db = get_database()


def papers_find_one__import_openreview_paper(forum_id):
    """papers.find_one from openreview_import.import_openreview_paper()"""
    return db.papers.find_one({"openreview_id": forum_id})


def papers_insert_one__import_openreview_paper(paper_doc):
    """papers.insert_one from openreview_import.import_openreview_paper()"""
    return db.papers.insert_one(paper_doc)


def papers_update_one__process_pdf_background(update_data, paper_id):
    """papers.update_one from openreview_import.process_pdf_background()"""
    return db.papers.update_one(
        {"_id": ObjectId(paper_id)},
        {"$set": update_data}
    )


def tag_instances_insert_one__import_openreview_paper(tag, paper_id):
    """tag_instances.insert_one from openreview_import.import_openreview_paper()"""
    return db.tag_instances.insert_one({
        "tag": tag,
        "content_type": "paper",
        "content_id": paper_id,
        "created_at": datetime.now(timezone.utc)
    })
