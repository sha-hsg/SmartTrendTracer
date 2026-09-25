"""
MongoDB queries of app.api.article_import.url_import, moved verbatim out of the router
(one function per former inline call site).
"""
from datetime import datetime
from datetime import timezone
from app.database.mongodb import get_database

db = get_database()


def articles_find_one__import_article_from_url(url):
    """articles.find_one from article_import.url_import.import_article_from_url()"""
    return db.articles.find_one({'url': url})


def articles_find_one__import_article_enhanced(url):
    """articles.find_one from article_import.url_import.import_article_enhanced()"""
    return db.articles.find_one({'url': url})


def articles_update_one__import_article_from_url(existing, markdown_content, word_count):
    """articles.update_one from article_import.url_import.import_article_from_url()"""
    return db.articles.update_one(
        {'_id': existing['_id']},
        {'$set': {
            'content_markdown': markdown_content,
            'word_count': word_count,
            'updated_at': datetime.now(timezone.utc)
        }}
    )


def articles_insert_one__import_article_from_url(article_doc):
    """articles.insert_one from article_import.url_import.import_article_from_url()"""
    return db.articles.insert_one(article_doc)


def articles_update_one__import_article_enhanced(existing, markdown_content, word_count, cookies):
    """articles.update_one from article_import.url_import.import_article_enhanced()"""
    return db.articles.update_one(
        {'_id': existing['_id']},
        {'$set': {
            'content_markdown': markdown_content,
            'word_count': word_count,
            'updated_at': datetime.now(timezone.utc),
            'authenticated': bool(cookies)
        }}
    )


def articles_insert_one__import_article_enhanced(article_doc):
    """articles.insert_one from article_import.url_import.import_article_enhanced()"""
    return db.articles.insert_one(article_doc)
