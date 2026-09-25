"""
MongoDB queries of app.api.entity_extraction, moved verbatim out of the router
(one function per former inline call site).
"""
from bson import ObjectId
from datetime import datetime
from datetime import timezone
from app.database.mongodb import get_database

db = get_database()


def entity_reviews_insert_one__review_entity(review_doc):
    """entity_reviews.insert_one from entity_extraction.review_entity()"""
    return db.entity_reviews.insert_one(review_doc)


def articles_find_one___find_article(article_id):
    """articles.find_one from entity_extraction._find_article()"""
    return db.articles.find_one({'old_sqlite_id': int(article_id)})


def entity_reviews_insert_one__review_entity_2(review_doc):
    """entity_reviews.insert_one from entity_extraction.review_entity()"""
    return db.entity_reviews.insert_one(review_doc)


def articles_find_one___find_article_2(article_id):
    """articles.find_one from entity_extraction._find_article()"""
    return db.articles.find_one({'_id': ObjectId(article_id)})


def tweets_find_one__extract_entities(request):
    """tweets.find_one from entity_extraction.extract_entities()"""
    return db.tweets.find_one({'_id': request.tweet_id})


def entity_reviews_insert_one__review_entity_3(review_doc):
    """entity_reviews.insert_one from entity_extraction.review_entity()"""
    return db.entity_reviews.insert_one(review_doc)


def articles_find_one__extract_entities(request):
    """articles.find_one from entity_extraction.extract_entities()"""
    return db.articles.find_one({'_id': ObjectId(request.article_id)})


def articles_find_one__extract_entities_2(request):
    """articles.find_one from entity_extraction.extract_entities()"""
    return db.articles.find_one({'old_sqlite_id': int(request.article_id)})


def tag_instances_find_one__review_entity(concept_id, article):
    """tag_instances.find_one from entity_extraction.review_entity()"""
    return db.tag_instances.find_one({
                        'content_type': 'article',
                        'content_id': str(article['_id']),
                        'concept_id': concept_id
                    })


def tag_instances_insert_one__review_entity(concept_id, user, article, concept, request):
    """tag_instances.insert_one from entity_extraction.review_entity()"""
    return db.tag_instances.insert_one({
        'concept_id': concept_id,
        'content_type': 'article',
        'content_id': str(article['_id']),
        'tag_slug': concept.get('slug', request.new_text.lower().replace(' ', '-')),
        'display_name': concept.get('display_name', request.new_text),
        'tag_type': 'entity',
        'created_at': datetime.now(timezone.utc),
        'created_by': user
    })


def articles_find_one__bulk_entity_action(article_object_id):
    """articles.find_one from entity_extraction.bulk_entity_action()"""
    return db.articles.find_one({'_id': article_object_id})


def articles_find_one__bulk_entity_action_2(article_id):
    """articles.find_one from entity_extraction.bulk_entity_action()"""
    return db.articles.find_one({'old_sqlite_id': int(article_id)})


def tag_instances_find_one__bulk_entity_action(concept_id, article_object_id):
    """tag_instances.find_one from entity_extraction.bulk_entity_action()"""
    return db.tag_instances.find_one({
                                'content_type': 'article',
                                'content_id': str(article_object_id),
                                'concept_id': concept_id
                            })


def tag_instances_insert_one__bulk_entity_action(tag_instance):
    """tag_instances.insert_one from entity_extraction.bulk_entity_action()"""
    return db.tag_instances.insert_one(tag_instance)
