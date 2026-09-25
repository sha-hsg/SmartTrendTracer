"""
MongoDB queries of app.api.papers.analysis_management, moved verbatim out of the router
(one function per former inline call site).
"""
from app.database.mongodb import get_database

db = get_database()


def papers_update_one__create_free_analysis(paper, analysis):
    """papers.update_one from papers.analysis_management.create_free_analysis()"""
    return db.papers.update_one(
        {'_id': paper['_id']},
        {'$push': {'free_analyses': analysis}}
    )


def papers_update_one__create_free_analysis_2(paper, prompt):
    """papers.update_one from papers.analysis_management.create_free_analysis()"""
    return db.papers.update_one(
        {'_id': paper['_id']},
        {'$pull': {'free_analyses': {'prompt': prompt}}}
    )
