"""
MongoDB queries of app.api.analytics_trends.network_correlation, moved verbatim out of the router
(one function per former inline call site).
"""
from app.database.mongodb import concept_id_query_variants
from app.database.mongodb import get_database

db = get_database()


def tag_concepts_v2_find_one__get_concept_network(concept_id):
    """tag_concepts_v2.find_one from analytics_trends.network_correlation.get_concept_network()"""
    return db.tag_concepts_v2.find_one(
                {'_id': {'$in': concept_id_query_variants(concept_id)}})
