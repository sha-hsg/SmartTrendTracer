"""
MongoDB queries of app.api.article_import.conversion, moved verbatim out of the router
(one function per former inline call site).
"""
from app.database.mongodb import get_database

db = get_database()


def articles_find_one__service_import_url_playwright(url):
    """articles.find_one from article_import.conversion.service_import_url_playwright()"""
    return db.articles.find_one({'url': url})


def articles_insert_one__service_import_url_playwright(doc):
    """articles.insert_one from article_import.conversion.service_import_url_playwright()"""
    return db.articles.insert_one(doc)
