"""
MongoDB queries of app.api.acl_anthology, moved verbatim out of the router
(one function per former inline call site).
"""
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
