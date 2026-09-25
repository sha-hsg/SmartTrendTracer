"""
MongoDB queries of app.api.analytics_trends.analysis, moved verbatim out of the router
(one function per former inline call site).
"""
from app.database.mongodb import get_database

db = get_database()


def tweets_count_documents__generate_summary(tweet_filter):
    """tweets.count_documents from analytics_trends.analysis.generate_summary()"""
    return db.tweets.count_documents(tweet_filter)


def articles_count_documents__generate_summary(article_filter):
    """articles.count_documents from analytics_trends.analysis.generate_summary()"""
    return db.articles.count_documents(article_filter)


def papers_count_documents__generate_summary(paper_filter):
    """papers.count_documents from analytics_trends.analysis.generate_summary()"""
    return db.papers.count_documents(paper_filter)


def tag_instances_aggregate__get_trends_at_a_glance(pipeline):
    """tag_instances.aggregate from analytics_trends.analysis.get_trends_at_a_glance()"""
    return db.tag_instances.aggregate(pipeline)


def tweets_count_documents__generate_summary_2(any_tweet_filter):
    """tweets.count_documents from analytics_trends.analysis.generate_summary()"""
    return db.tweets.count_documents(any_tweet_filter)


def articles_count_documents__generate_summary_2(any_article_filter):
    """articles.count_documents from analytics_trends.analysis.generate_summary()"""
    return db.articles.count_documents(any_article_filter)


def papers_count_documents__generate_summary_2(any_paper_filter):
    """papers.count_documents from analytics_trends.analysis.generate_summary()"""
    return db.papers.count_documents(any_paper_filter)


def tweets_find__generate_summary(any_tweet_filter):
    """tweets.find from analytics_trends.analysis.generate_summary()"""
    return db.tweets.find(any_tweet_filter, {'created_at': 1})


def articles_find__generate_summary(any_article_filter):
    """articles.find from analytics_trends.analysis.generate_summary()"""
    return db.articles.find(any_article_filter, {'published_at': 1})
