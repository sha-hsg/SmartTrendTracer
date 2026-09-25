from typing import List, Optional, Dict
from datetime import datetime
import re
from bson import ObjectId
from pymongo import DESCENDING

from app.database.mongodb import get_database

db = get_database()
from app.repositories.concepts import ConceptOnlyTagService

concept_service = ConceptOnlyTagService()
import logging

logger = logging.getLogger(__name__)


def build_author_query_conditions(author_id: str) -> list:
    or_conditions = []

    # Try MongoDB ObjectId
    try:
        if len(author_id) == 24:
            or_conditions.append({'author_id': ObjectId(author_id)})
            # Also check if this is the author's MongoDB ID
            author = db.substack_authors.find_one({'_id': ObjectId(author_id)})
            if author:
                # Add all ways this author might be referenced
                if author.get('name'):
                    or_conditions.append({'author_name': author['name']})
                if author.get('old_sqlite_id'):
                    or_conditions.append({'author_id': author['old_sqlite_id']})
                    or_conditions.append({'author_sqlite_id': author['old_sqlite_id']})
    except Exception:
        pass

    # Try numeric ID
    try:
        numeric_id = int(author_id)
        or_conditions.append({'author_id': numeric_id})
        or_conditions.append({'author_sqlite_id': numeric_id})
    except Exception:
        pass

    return or_conditions


def build_faceted_author_query_conditions(authors: List[str]) -> list:
    author_docs = list(db.substack_authors.find({'name': {'$in': authors}}))

    or_conditions = []
    known_names = [a.get('name') for a in author_docs if a.get('name')]

    # Always match by the display name against every candidate field,
    # so facet labels that come from primary_author_name / author still filter correctly.
    if authors:
        or_conditions.append({'primary_author_name': {'$in': authors}})
        or_conditions.append({'author_name': {'$in': authors}})
        or_conditions.append({'author': {'$in': authors}})

    if author_docs:
        # Also match by any canonical name from the substack_authors collection
        if known_names:
            or_conditions.append({'primary_author_name': {'$in': known_names}})
            or_conditions.append({'author_name': {'$in': known_names}})
            or_conditions.append({'author': {'$in': known_names}})

        # Match by old SQLite IDs
        old_ids = [a['old_sqlite_id'] for a in author_docs if a.get('old_sqlite_id')]
        if old_ids:
            or_conditions.append({'author_id': {'$in': old_ids}})
            or_conditions.append({'author_sqlite_id': {'$in': old_ids}})

        # Match by MongoDB ObjectIds (for newer articles)
        mongo_ids = [a['_id'] for a in author_docs]
        or_conditions.append({'author_id': {'$in': mongo_ids}})
        # primary_author_id is stored as string in some records
        or_conditions.append({'primary_author_id': {'$in': [str(mid) for mid in mongo_ids]}})

    return or_conditions


def build_concept_id_filter(concept_ids: List[str]) -> Optional[list]:
    concept_object_ids = []
    for cid in concept_ids:
        try:
            if len(cid) == 24:
                concept_object_ids.append(ObjectId(cid))
            else:
                concept_object_ids.append(cid)
        except Exception:
            concept_object_ids.append(cid)

    # Find all article IDs that have any of these concepts in tag_instances
    tag_instances = list(db.tag_instances.find({
        'content_type': 'article',
        'concept_id': {'$in': concept_object_ids}
    }))
    article_ids_filter = list(set([ti['content_id'] for ti in tag_instances]))
    logger.info(f"Found {len(article_ids_filter)} articles with concepts {concept_ids}")

    if not article_ids_filter:
        return None

    or_conditions = []
    for aid in article_ids_filter:
        # Try as MongoDB ObjectId
        try:
            if len(aid) == 24:
                or_conditions.append({'_id': ObjectId(aid)})
        except Exception:
            pass

        # Try as old SQLite ID (convert string to int if numeric)
        try:
            if aid.isdigit():
                or_conditions.append({'old_sqlite_id': int(aid)})
            else:
                or_conditions.append({'old_sqlite_id': aid})
        except Exception:
            pass

        # Also try as string _id
        or_conditions.append({'_id': aid})

    return or_conditions


def build_year_conditions(years: List[int]) -> list:
    year_conditions = []
    for year in years:
        start_date = datetime(year, 1, 1)
        end_date = datetime(year + 1, 1, 1)
        year_conditions.append({
            'published_at': {
                '$gte': start_date,
                '$lt': end_date
            }
        })
    return year_conditions


def build_search_condition(search: str, search_mode: str) -> dict:
    escaped = re.escape(search)
    if search_mode == "content":
        return {'content_markdown': {'$regex': escaped, '$options': 'i'}}
    elif search_mode == "all":
        return {'$or': [
            {'title': {'$regex': escaped, '$options': 'i'}},
            {'content_markdown': {'$regex': escaped, '$options': 'i'}}
        ]}
    else:  # "title" (default)
        return {'title': {'$regex': escaped, '$options': 'i'}}


def merge_condition_into_query(query: dict, condition: dict) -> dict:
    if '$or' in condition:
        if '$and' in query:
            query['$and'].append(condition)
        elif query:
            query = {'$and': [query, condition]}
        else:
            query = condition
    else:
        query.update(condition)
    return query


def build_sort_pipeline(query: dict, skip: int, page_size: int) -> list:
    return [
        {'$match': query},
        {'$addFields': {
            'sort_date': {
                '$ifNull': ['$published_at', '$created_at']
            }
        }},
        {'$sort': {'sort_date': DESCENDING}},
        {'$skip': skip},
        {'$limit': page_size}
    ]


def resolve_author_for_article(article: dict) -> Optional[dict]:
    if article.get('author_name'):
        return {
            'name': article.get('author_name'),
            'email': article.get('author_email'),
            'subdomain': None
        }
    elif article.get('author_id'):
        try:
            author = db.substack_authors.find_one({'_id': article['author_id']})
            if not author:
                author = db.substack_authors.find_one({'sqlite_id': article['author_id']})
            return author
        except Exception:
            pass
    return None


def resolve_author_for_single_article(article: dict) -> Optional[dict]:
    if article.get('author_name'):
        return {
            'name': article.get('author_name'),
            'email': article.get('author_email'),
            'subdomain': None
        }
    elif article.get('author'):
        return {
            'name': article.get('author'),
            'email': None,
            'subdomain': None
        }
    elif article.get('author_id'):
        try:
            author = db.substack_authors.find_one({'_id': article['author_id']})
            if not author:
                author = db.substack_authors.find_one({'sqlite_id': article['author_id']})
            if author:
                return {
                    'id': str(author['_id']),
                    'name': author.get('name'),
                    'subdomain': author.get('subdomain'),
                    'description': author.get('description')
                }
        except Exception:
            pass
    return None


def get_article_concepts_and_tags(article: dict) -> tuple:
    article_id = str(article['_id'])
    sqlite_id = str(article.get('old_sqlite_id', ''))

    tag_instances = list(db.tag_instances.find({
        'content_type': 'article',
        '$or': [
            {'content_id': article_id},
            {'content_id': sqlite_id}
        ]
    }))

    # Deduplicate concept_ids to avoid React key warnings
    concept_ids = list(set(ti['concept_id'] for ti in tag_instances))

    # Get concept details in batch (PERF: Quick Win - avoids N+1 queries)
    concepts = []
    tags = []  # Frontend-compatible format
    if concept_ids:
        concepts_lookup = concept_service.get_concepts_by_ids(concept_ids)
        for cid in concept_ids:
            concept = concepts_lookup.get(str(cid))
            if concept:
                concepts.append({
                    'concept_id': str(cid),
                    'display_name': concept.get('display_name'),
                    'slug': concept.get('slug')
                })
                tags.append({
                    'id': str(cid),
                    'tag': concept.get('display_name'),
                    'type': 'concept'
                })

    return concepts, tags


def format_article_for_list(article: dict, author: Optional[dict], concepts: list, tags: list) -> dict:
    return {
        'id': str(article['_id']),
        'substack_id': article.get('substack_id'),
        'title': article.get('title'),
        'subtitle': article.get('subtitle'),
        'slug': article.get('slug'),
        'url': article.get('url'),
        'preview': article.get('preview'),
        'word_count': article.get('word_count', 0),
        'reading_time_minutes': article.get('reading_time_minutes', 0),
        'author': {
            # author may come from resolve_author_for_article's author_name
            # fallback, which has no '_id' key - use .get() to avoid KeyError
            'id': str(author['_id']) if author.get('_id') else None,
            'name': author.get('name'),
            'subdomain': author.get('subdomain')
        } if author else None,
        'published_at': article.get('published_at').isoformat() if article.get('published_at') else None,
        'metrics': article.get('metrics', {}),
        'summary': article.get('summary'),
        'has_summary': bool(article.get('summary')),
        'concepts': concepts,
        'tags': tags,
        'processed': article.get('processed', False),
        'summarized': article.get('summarized', False),
        'snippet_count': len(article.get('snippets', [])),
        'content': article.get('content_markdown', '')
    }


def format_article_for_faceted(article: dict, author: Optional[dict], concepts: list, tags: list) -> dict:
    content = article.get('content_markdown', '')
    summary = article.get('summary')
    has_summary = bool(summary and len(summary) > 0)

    return {
        'id': str(article['_id']),
        'title': article.get('title'),
        'subtitle': article.get('subtitle'),
        'url': article.get('url'),
        'preview': article.get('preview'),
        'content': content,
        'content_length': len(content) if content else 0,
        'author': {
            'name': author.get('name') if author else None,
            'subdomain': author.get('subdomain') if author else None
        } if author else None,
        'published_at': article.get('published_at').isoformat() if article.get('published_at') else None,
        'concepts': concepts,
        'tags': tags,
        'metrics': article.get('metrics', {}),
        'summarized': article.get('summarized', False),
        'summary': summary,
        'has_summary': has_summary,
        'reading_time_minutes': article.get('reading_time_minutes', 0),
        'word_count': article.get('word_count', 0),
        'snippet_count': len(article.get('snippets', []))
    }


def build_author_facets(query: dict) -> list:
    # Prefer primary_author_name (clean, single-author reference) over author_name
    # (raw display string that may contain a compound list like "A, B, C and others"
    # or a suffix like ", PhD" / " (LLM Watch)"). Fall back to author / author_id.
    author_pipeline = [
        {'$match': query if query else {}},
        {'$project': {
            'author_info': {
                '$ifNull': [
                    '$primary_author_name',
                    {'$ifNull': [
                        '$author_name',
                        {'$ifNull': ['$author', '$author_id']}
                    ]}
                ]
            }
        }},
        {'$group': {
            '_id': '$author_info',
            'count': {'$sum': 1}
        }},
        {'$sort': {'count': -1}}
        # Removed $limit: 20 to show ALL authors
    ]
    author_counts = list(db.articles.aggregate(author_pipeline))

    # Get author names
    author_facets = []
    for ac in author_counts:
        if ac['_id']:
            # First check if _id is already a name string
            if isinstance(ac['_id'], str) and not ac['_id'].isdigit():
                author_facets.append({
                    'name': ac['_id'],
                    'subdomain': None,
                    'count': ac['count']
                })
            else:
                # Try to find in authors collection by various ID fields
                author = db.substack_authors.find_one({'_id': ac['_id']}) or \
                         db.substack_authors.find_one({'old_sqlite_id': ac['_id']}) or \
                         db.substack_authors.find_one({'sqlite_id': ac['_id']})
                if author:
                    # Always include author even if subdomain is missing
                    author_facets.append({
                        'name': author.get('name'),
                        'subdomain': author.get('subdomain'),  # Can be None
                        'count': ac['count']
                    })
                else:
                    # If not found, use the ID as name (shouldn't happen often)
                    author_facets.append({
                        'name': f"Author {str(ac['_id'])}",
                        'subdomain': None,
                        'count': ac['count']
                    })

    return author_facets


def build_concept_facets() -> list:
    concept_facets = []
    all_concepts = concept_service.get_all_concepts_with_counts(content_type='article')
    # Convert ObjectIds to strings in concept facets
    for concept in all_concepts[:100]:
        concept_facet = {
            'concept_id': str(concept.get('concept_id')) if concept.get('concept_id') else None,
            'slug': concept.get('slug'),
            'display_name': concept.get('display_name'),
            'count': concept.get('count', 0)
        }
        concept_facets.append(concept_facet)
    return concept_facets


def build_year_facets(query: dict) -> list:
    year_pipeline = [
        {'$match': query if query else {}},
        {'$project': {
            'year': {'$year': '$published_at'}
        }},
        {'$match': {'year': {'$ne': None}}},
        {'$group': {
            '_id': '$year',
            'count': {'$sum': 1}
        }},
        {'$sort': {'_id': -1}},
        {'$limit': 10}
    ]
    year_counts = list(db.articles.aggregate(year_pipeline))
    return [{'year': yc['_id'], 'count': yc['count']} for yc in year_counts if yc['_id']]
