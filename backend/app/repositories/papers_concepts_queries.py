"""
MongoDB queries of app.api.papers.concepts, moved verbatim out of the router
(one function per former inline call site).
"""
import re
from app.database.mongodb import get_database

db = get_database()


def tag_concepts_v2_find_one__remove_tag_from_paper(tag):
    """tag_concepts_v2.find_one from papers.concepts.remove_tag_from_paper()"""
    return db.tag_concepts_v2.find_one({
                'display_name': {'$regex': f'^{re.escape(tag)}$', '$options': 'i'}
            })
