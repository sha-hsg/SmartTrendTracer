"""
MongoDB queries of app.api.pdf_export, moved verbatim out of the router
(one function per former inline call site).
"""
from bson import ObjectId
from app.database.mongodb import get_database

db = get_database()


def articles_find_one__export_article_pdf(article_id):
    """articles.find_one from pdf_export.export_article_pdf()"""
    return db.articles.find_one({'_id': ObjectId(article_id)})


def articles_find_one__export_article_pdf_2(article_id):
    """articles.find_one from pdf_export.export_article_pdf()"""
    return db.articles.find_one({'old_sqlite_id': int(article_id)})
