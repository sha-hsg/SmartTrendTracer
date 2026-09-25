"""
MongoDB queries of app.api.papers.analysis, moved verbatim out of the router
(one function per former inline call site).
"""
from app.database.mongodb import get_database

db = get_database()


def papers_update_one__create_analysis(paper, analysis):
    """papers.update_one from papers.analysis.create_analysis()"""
    return db.papers.update_one(
        {'_id': paper['_id']},
        {'$push': {'analyses': analysis}}
    )


def papers_update_one__create_analysis_2(paper, analysis_type):
    """papers.update_one from papers.analysis.create_analysis()"""
    return db.papers.update_one(
        {'_id': paper['_id']},
        {'$pull': {'analyses': {'$or': [
            {'type': analysis_type},
            {'analysis_type': analysis_type}
        ]}}}
    )
