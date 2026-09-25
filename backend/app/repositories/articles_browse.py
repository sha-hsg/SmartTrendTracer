"""
Data access for app.api.articles.browse (extracted by the arch-audit refactor).


"""
from app.repositories.article_browse import build_author_facets
from app.repositories.article_browse import build_author_query_conditions
from app.repositories.article_browse import build_concept_facets
from app.repositories.article_browse import build_concept_id_filter
from app.repositories.article_browse import build_faceted_author_query_conditions
from app.repositories.article_browse import build_search_condition
from app.repositories.article_browse import build_sort_pipeline
from app.repositories.article_browse import build_year_conditions
from app.repositories.article_browse import build_year_facets
from app.repositories.article_browse import format_article_for_faceted
from app.repositories.article_browse import format_article_for_list
from app.repositories.article_browse import get_article_concepts_and_tags
from app.repositories.article_browse import merge_condition_into_query
from app.repositories.article_browse import resolve_author_for_article
from app.repositories.article_browse import resolve_author_for_single_article
from app.repositories.errors import NotFoundError
from bson import ObjectId

from app.database.mongodb import get_database

db = get_database()




def get_articles(page, page_size, author_id, concept_id, search, search_mode):
    query = {}

    if author_id:
        or_conditions = build_author_query_conditions(author_id)
        if or_conditions:
            query['$or'] = or_conditions

    if concept_id:
        query['concept_ids'] = concept_id

    if search:
        search_cond = build_search_condition(search, search_mode)
        if '$or' in search_cond:
            if '$and' in query:
                query['$and'].append(search_cond)
            elif query:
                query = {'$and': [query, search_cond]}
            else:
                query = search_cond
        else:
            query.update(search_cond)

    # Count total
    total = db.articles.count_documents(query)

    # Get articles with pagination
    skip = (page - 1) * page_size
    pipeline = build_sort_pipeline(query, skip, page_size)
    articles = list(db.articles.aggregate(pipeline))

    # Format response
    result = []
    for article in articles:
        author = resolve_author_for_article(article)
        concepts, tags = get_article_concepts_and_tags(article)
        result.append(format_article_for_list(article, author, concepts, tags))

    return result



def faceted_search(page, page_size, authors, concept_ids, years, search, search_mode):
    query = {}

    if authors:
        or_conditions = build_faceted_author_query_conditions(authors)
        if or_conditions:
            query['$or'] = or_conditions

    if concept_ids:
        or_conditions = build_concept_id_filter(concept_ids)

        if or_conditions is None:
            # No articles with these concepts, return empty result
            return {
                "articles": [],
                "total": 0,
                "page": page,
                "page_size": page_size,
                "facets": {
                    "authors": [],
                    "concepts": [],
                    "years": []
                }
            }

        if or_conditions:
            # Need to combine with existing query conditions
            if query:
                # Wrap existing conditions and new OR conditions in an AND
                new_query = {'$and': [query, {'$or': or_conditions}]}
                query = new_query
            else:
                query['$or'] = or_conditions

    if years:
        year_conditions = build_year_conditions(years)

        if year_conditions:
            if query:
                # Combine with existing query
                if '$and' in query:
                    query['$and'].append({'$or': year_conditions})
                else:
                    query = {'$and': [query, {'$or': year_conditions}]}
            else:
                query['$or'] = year_conditions

    if search:
        search_cond = build_search_condition(search, search_mode)
        query = merge_condition_into_query(query, search_cond)

    # Get total count
    total = db.articles.count_documents(query)

    # Get articles with pagination
    skip = (page - 1) * page_size
    pipeline = build_sort_pipeline(query, skip, page_size)
    articles = list(db.articles.aggregate(pipeline))

    # Build facets
    author_facets = build_author_facets(query)
    concept_facets = build_concept_facets()
    year_facets = build_year_facets(query)

    # Format articles
    result_articles = []
    for article in articles:
        author = resolve_author_for_article(article)
        concepts, tags = get_article_concepts_and_tags(article)
        result_articles.append(format_article_for_faceted(article, author, concepts, tags))

    return {
        'articles': result_articles,
        'facets': {
            'authors': author_facets,
            'concepts': concept_facets,
            'years': year_facets
        },
        'total': total,
        'page': page,
        'page_size': page_size
    }



def delete_article(article_id):
    try:
        if len(article_id) == 24:
            article = db.articles.find_one({'_id': ObjectId(article_id)})
        else:
            article = db.articles.find_one({'old_sqlite_id': int(article_id)})
    except Exception:
        article = None

    if not article:
        raise NotFoundError("Article not found")

    db.articles.delete_one({'_id': article['_id']})

    # Delete associated tag instances for both id variants
    article_id_str = str(article['_id'])
    sqlite_id_str = str(article.get('old_sqlite_id', ''))
    db.tag_instances.delete_many({
        'content_type': 'article',
        '$or': [
            {'content_id': article_id_str},
            {'content_id': sqlite_id_str}
        ]
    })

    return {"message": "Article deleted successfully"}



def get_article(article_id):
    try:
        if len(article_id) == 24:
            article = db.articles.find_one({'_id': ObjectId(article_id)})
        else:
            article = db.articles.find_one({'old_sqlite_id': int(article_id)})
    except Exception:
        article = None

    if not article:
        raise NotFoundError("Article not found")

    # Get author
    author_data = resolve_author_for_single_article(article)

    # Get concepts
    concepts, tags = get_article_concepts_and_tags(article)

    # Format response
    return {
        'id': str(article['_id']),
        'substack_id': article.get('substack_id'),
        'title': article.get('title'),
        'subtitle': article.get('subtitle'),
        'slug': article.get('slug'),
        'url': article.get('url'),
        'content_html': article.get('content_html'),
        'content_markdown': article.get('content_markdown', ''),
        'content': article.get('content_markdown', ''),
        'preview': article.get('preview'),
        'word_count': article.get('word_count', 0),
        'reading_time_minutes': article.get('reading_time_minutes', 0),
        'author': author_data,
        'published_at': article.get('published_at').isoformat() if article.get('published_at') else None,
        'collected_at': article.get('collected_at').isoformat() if article.get('collected_at') else None,
        'metrics': article.get('metrics', {}),
        'summary': article.get('summary'),
        'key_points': article.get('key_points', []),
        'topics': article.get('topics', []),
        'sentiment': article.get('sentiment'),
        'snippets': article.get('snippets', []),
        'concepts': concepts,
        'tags': tags,
        'processed': article.get('processed', False),
        'summarized': article.get('summarized', False)
    }

