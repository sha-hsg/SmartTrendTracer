"""
Complete MongoDB-based articles API.
All data operations use MongoDB - no SQLite dependencies.
"""

from fastapi import APIRouter, HTTPException, Query, Body
from fastapi.responses import FileResponse
from pymongo import ASCENDING, DESCENDING
from app.database.mongodb import get_database
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
from bson import ObjectId
import json
from pathlib import Path

from app.services.concept_only_tag_service import ConceptOnlyTagService
from app.services.author_service import AuthorService

logger = logging.getLogger(__name__)
router = APIRouter()

# MongoDB connection
db = get_database()

# Initialize services
concept_service = ConceptOnlyTagService()
author_service = AuthorService(db)

@router.get("/", response_model=List[Dict])
def get_articles(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    author_id: Optional[str] = None,
    concept_id: Optional[str] = None,
    search: Optional[str] = None
):
    """Get articles with filtering and pagination from MongoDB"""
    
    # Build query
    query = {}
    
    if author_id:
        # Handle MongoDB ObjectId, old SQLite ID, or author name
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
        except:
            pass
        
        # Try numeric ID
        try:
            numeric_id = int(author_id)
            or_conditions.append({'author_id': numeric_id})
            or_conditions.append({'author_sqlite_id': numeric_id})
        except:
            pass
        
        if or_conditions:
            query['$or'] = or_conditions
    
    if concept_id:
        query['concept_ids'] = concept_id
    
    if search:
        query['$text'] = {'$search': search}
    
    # Count total
    total = db.articles.count_documents(query)

    # Get articles with pagination
    # Use aggregation to sort by published_at when available, otherwise by created_at
    skip = (page - 1) * page_size

    pipeline = [
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

    articles = list(db.articles.aggregate(pipeline))
    
    # Format response
    result = []
    for article in articles:
        # Get author - handle both embedded author_name and separate author collection
        author = None
        if article.get('author_name'):
            # Use embedded author data
            author = {
                'name': article.get('author_name'),
                'email': article.get('author_email'),
                'subdomain': None
            }
        elif article.get('author_id'):
            # Try to find in authors collection
            try:
                author = db.substack_authors.find_one({'_id': article['author_id']})
                if not author:
                    author = db.substack_authors.find_one({'sqlite_id': article['author_id']})
            except:
                pass
        
        # Get concepts from tag_instances collection
        # Try both MongoDB _id and old SQLite ID
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

        result.append({
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
                'id': str(author['_id']) if author else None,
                'name': author.get('name') if author else None,
                'subdomain': author.get('subdomain') if author else None
            } if author else None,
            'published_at': article.get('published_at').isoformat() if article.get('published_at') else None,
            'metrics': article.get('metrics', {}),
            'summary': article.get('summary'),
            'has_summary': bool(article.get('summary')),
            'concepts': concepts,
            'tags': tags,  # Frontend-compatible format
            'processed': article.get('processed', False),
            'summarized': article.get('summarized', False),
            'snippet_count': len(article.get('snippets', [])),
            'content': article.get('content_markdown', '')  # Use standardized content_markdown field
        })
    
    return result

@router.get("/faceted-search")
def faceted_search(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    authors: Optional[List[str]] = Query(None),
    concept_ids: Optional[List[str]] = Query(None),
    years: Optional[List[int]] = Query(None),
    search: Optional[str] = None
):
    """Faceted search for articles using MongoDB"""
    
    # Build query
    query = {}
    
    if authors:
        # Get author documents from names
        author_docs = list(db.substack_authors.find({'name': {'$in': authors}}))
        
        if author_docs:
            # Build complex query to match articles by various author fields
            or_conditions = []
            
            # Match by author name (most reliable)
            or_conditions.append({'author_name': {'$in': [a.get('name') for a in author_docs if a.get('name')]}})
            
            # Match by old SQLite IDs
            old_ids = [a['old_sqlite_id'] for a in author_docs if a.get('old_sqlite_id')]
            if old_ids:
                or_conditions.append({'author_id': {'$in': old_ids}})
                or_conditions.append({'author_sqlite_id': {'$in': old_ids}})
            
            # Match by MongoDB ObjectIds (for newer articles)
            mongo_ids = [a['_id'] for a in author_docs]
            or_conditions.append({'author_id': {'$in': mongo_ids}})
            
            query['$or'] = or_conditions
    
    if concept_ids:
        # Convert concept_ids to ObjectId if they're valid hex strings
        concept_object_ids = []
        for cid in concept_ids:
            try:
                if len(cid) == 24:
                    concept_object_ids.append(ObjectId(cid))
                else:
                    concept_object_ids.append(cid)  # Keep as is if not valid ObjectId format
            except:
                concept_object_ids.append(cid)  # Keep as is if conversion fails
        
        # Find all article IDs that have any of these concepts in tag_instances
        tag_instances = list(db.tag_instances.find({
            'content_type': 'article',
            'concept_id': {'$in': concept_object_ids}
        }))
        article_ids_filter = list(set([ti['content_id'] for ti in tag_instances]))
        logger.info(f"Found {len(article_ids_filter)} articles with concepts {concept_ids}")
        
        if article_ids_filter:
            # Build complex query to handle different ID formats
            or_conditions = []
            for aid in article_ids_filter:
                # Try as MongoDB ObjectId
                try:
                    if len(aid) == 24:
                        or_conditions.append({'_id': ObjectId(aid)})
                except:
                    pass
                
                # Try as old SQLite ID (convert string to int if numeric)
                try:
                    if aid.isdigit():
                        or_conditions.append({'old_sqlite_id': int(aid)})
                    else:
                        or_conditions.append({'old_sqlite_id': aid})
                except:
                    pass
                
                # Also try as string _id
                or_conditions.append({'_id': aid})
            
            if or_conditions:
                # Need to combine with existing query conditions
                if query:
                    # Wrap existing conditions and new OR conditions in an AND
                    new_query = {'$and': [query, {'$or': or_conditions}]}
                    query = new_query
                else:
                    query['$or'] = or_conditions
            else:
                query['_id'] = {'$in': article_ids_filter}
        else:
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
    
    if years:
        # Filter by year
        from datetime import datetime
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
        query['$text'] = {'$search': search}
    
    # Get total count
    total = db.articles.count_documents(query)

    # Get articles with pagination
    # Use aggregation to sort by published_at when available, otherwise by created_at
    skip = (page - 1) * page_size

    pipeline = [
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

    articles = list(db.articles.aggregate(pipeline))
    
    # Build facets
    
    # Author facets - handle both embedded author_name and separate author collection
    author_pipeline = [
        {'$match': query if query else {}},
        {'$project': {
            'author_info': {
                '$cond': [
                    # First: Check if author_name exists and is not None
                    {'$ne': ['$author_name', None]},
                    '$author_name',
                    {
                        '$cond': [
                            # Second: Check if author exists and is not None
                            {'$ne': ['$author', None]},
                            '$author',
                            # Third: Fall back to author_id
                            '$author_id'
                        ]
                    }
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
    
    # Concept facets
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
    
    # Format articles
    result_articles = []
    for article in articles:
        # Get author - handle both embedded author_name and separate author collection
        author = None
        if article.get('author_name'):
            # Use embedded author data
            author = {
                'name': article.get('author_name'),
                'email': article.get('author_email'),
                'subdomain': None  # Could extract from email if needed
            }
        elif article.get('author_id'):
            # Try to find in authors collection (handle both ObjectId and numeric IDs)
            try:
                author = db.substack_authors.find_one({'_id': article['author_id']})
                if not author:
                    # Try with old SQLite ID
                    author = db.substack_authors.find_one({'sqlite_id': article['author_id']})
            except:
                pass
        
        # Get concepts from tag_instances collection
        # Try both MongoDB _id and old SQLite ID
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

        # Get content safely (use standardized content_markdown field)
        content = article.get('content_markdown', '')

        summary = article.get('summary')
        has_summary = bool(summary and len(summary) > 0)

        result_articles.append({
            'id': str(article['_id']),
            'title': article.get('title'),
            'subtitle': article.get('subtitle'),
            'url': article.get('url'),
            'preview': article.get('preview'),
            'content': content,  # Article full content
            'content_length': len(content) if content else 0,
            'author': {
                'name': author.get('name') if author else None,
                'subdomain': author.get('subdomain') if author else None
            } if author else None,
            'published_at': article.get('published_at').isoformat() if article.get('published_at') else None,
            'concepts': concepts,
            'tags': tags,  # Frontend-compatible format
            'metrics': article.get('metrics', {}),
            'summarized': article.get('summarized', False),
            'summary': summary,
            'has_summary': has_summary,
            'reading_time_minutes': article.get('reading_time_minutes', 0),
            'word_count': article.get('word_count', 0),
            'snippet_count': len(article.get('snippets', []))
        })
    
    # Year facets
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
    year_facets = [{'year': yc['_id'], 'count': yc['count']} for yc in year_counts if yc['_id']]
    
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

@router.get("/{article_id}/images/{filename}")
def get_article_image(article_id: str, filename: str):
    """Serve a local article image"""
    
    # Construct the image path
    image_path = Path(f"data/article_images/{filename}")
    
    # Security check: ensure the filename contains the article_id
    if not filename.startswith(f"{article_id}_"):
        raise HTTPException(status_code=403, detail="Invalid image request")
    
    if not image_path.exists():
        raise HTTPException(status_code=404, detail="Image not found")
    
    # Determine content type based on file extension
    ext = image_path.suffix.lower()
    content_types = {
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.gif': 'image/gif',
        '.webp': 'image/webp',
        '.svg': 'image/svg+xml'
    }
    
    media_type = content_types.get(ext, 'application/octet-stream')
    
    return FileResponse(image_path, media_type=media_type)

@router.delete("/{article_id}")
def delete_article(article_id: str):
    """Delete an article by ID"""
    
    try:
        if len(article_id) == 24:
            result = db.articles.delete_one({'_id': ObjectId(article_id)})
        else:
            result = db.articles.delete_one({'old_sqlite_id': int(article_id)})
    except:
        result = None
    
    if not result or result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Article not found")
    
    # Also delete associated tag instances
    db.tag_instances.delete_many({
        'content_type': 'article',
        'content_id': article_id
    })
    
    return {"message": "Article deleted successfully"}

@router.get("/{article_id}")
def get_article(article_id: str):
    """Get a specific article by ID from MongoDB"""
    
    try:
        if len(article_id) == 24:
            article = db.articles.find_one({'_id': ObjectId(article_id)})
        else:
            article = db.articles.find_one({'old_sqlite_id': int(article_id)})
    except:
        article = None
    
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    # Get author - handle both embedded author_name and separate author collection
    author = None
    author_data = None
    if article.get('author_name'):
        # Use embedded author data
        author_data = {
            'name': article.get('author_name'),
            'email': article.get('author_email'),
            'subdomain': None
        }
    elif article.get('author'):
        # Handle simple author string field
        author_data = {
            'name': article.get('author'),
            'email': None,
            'subdomain': None
        }
    elif article.get('author_id'):
        # Try to find in authors collection
        try:
            author = db.substack_authors.find_one({'_id': article['author_id']})
            if not author:
                author = db.substack_authors.find_one({'sqlite_id': article['author_id']})
            if author:
                # Convert to plain dict with string IDs
                author_data = {
                    'id': str(author['_id']),
                    'name': author.get('name'),
                    'subdomain': author.get('subdomain'),
                    'description': author.get('description')
                }
        except:
            pass
    
    # Get concepts from tag_instances collection
    # Try both MongoDB _id and old SQLite ID
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
                    'concept_id': str(cid),  # Convert ObjectId to string
                    'display_name': concept.get('display_name'),
                    'slug': concept.get('slug')
                })
                # Also add to tags array for frontend compatibility
                tags.append({
                    'id': str(cid),
                    'tag': concept.get('display_name'),
                    'type': 'concept'
                })

    # Format response
    return {
        'id': str(article['_id']),
        'substack_id': article.get('substack_id'),
        'title': article.get('title'),
        'subtitle': article.get('subtitle'),
        'slug': article.get('slug'),
        'url': article.get('url'),
        'content_html': article.get('content_html'),
        'content_markdown': article.get('content_markdown', ''),  # Use standardized content_markdown field
        'content': article.get('content_markdown', ''),  # Return as 'content' for frontend compatibility
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
        'tags': tags,  # Frontend-compatible format
        'processed': article.get('processed', False),
        'summarized': article.get('summarized', False)
    }

@router.post("/{article_id}/extract-metadata")
def extract_metadata_from_content(article_id: str):
    """Extract author and published date from article content using LLM"""

    try:
        if len(article_id) == 24:
            article = db.articles.find_one({'_id': ObjectId(article_id)})
        else:
            article = db.articles.find_one({'old_sqlite_id': int(article_id)})
    except:
        article = None

    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    # Get article content (use standardized content_markdown field)
    content = article.get('content_markdown', '')

    if not content:
        raise HTTPException(status_code=400, detail="Article has no content to analyze")

    # Take first 2000 characters (enough for header with author/date info)
    content_snippet = content[:2000]

    # Use LLM to extract metadata via LLMManager
    from app.services.llm_manager import get_llm_manager
    llm_manager = get_llm_manager()

    prompt = f"""Extract the author name and publication date from this article content.
Return ONLY a JSON object with 'author' and 'date' fields.
If you cannot find the information, use null.

For the date, convert it to ISO format (YYYY-MM-DD).

Example output:
{{"author": "John Doe", "date": "2025-01-15"}}

Article content:
{content_snippet}

JSON output:"""

    try:
        # Use entity extraction task type for metadata extraction
        messages = [{"role": "user", "content": prompt}]
        llm_response = llm_manager.completion_sync(
            task_type='entity_extraction',
            messages=messages,
            user_id='default'
        )
        response = llm_response.choices[0].message.content

        # Parse the JSON response
        import re
        # Extract JSON from response (in case there's extra text)
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            metadata = json.loads(json_match.group())
        else:
            metadata = json.loads(response)

        # Update article in database
        update_fields = {}

        if metadata.get('author'):
            update_fields['author_name'] = metadata['author']
            logger.info(f"Extracted author: {metadata['author']}")

        if metadata.get('date'):
            from datetime import datetime
            # Parse the date
            try:
                pub_date = datetime.fromisoformat(metadata['date'])
                update_fields['published_at'] = pub_date
                logger.info(f"Extracted date: {metadata['date']}")
            except:
                logger.warning(f"Could not parse date: {metadata['date']}")

        if update_fields:
            db.articles.update_one(
                {'_id': article['_id']},
                {'$set': update_fields}
            )

        return {
            "success": True,
            "extracted": metadata,
            "updated_fields": list(update_fields.keys())
        }

    except Exception as e:
        logger.error(f"Failed to extract metadata: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to extract metadata: {str(e)}")

@router.post("/{article_id}/concepts")
def add_concept_to_article(
    article_id: str,
    text: str = Query(..., description="Text to create/find concept from")
):
    """Add a concept to an article"""
    
    try:
        if len(article_id) == 24:
            article = db.articles.find_one({'_id': ObjectId(article_id)})
        else:
            article = db.articles.find_one({'old_sqlite_id': int(article_id)})
    except:
        article = None
    
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    # Add concept using the service
    success, concept_id = concept_service.add_tag('article', str(article['_id']), text)
    
    if not success:
        raise HTTPException(status_code=400, detail="Failed to add concept")
    
    # Update article's concept_ids in MongoDB
    db.articles.update_one(
        {'_id': article['_id']},
        {'$addToSet': {'concept_ids': concept_id}}
    )
    
    # Get concept details
    concept = concept_service.get_concept_by_id(concept_id)

    return {
        "message": "Concept added successfully",
        "concept": {
            "concept_id": concept_id,
            "slug": concept.get('slug', ''),
            "display_name": concept.get('display_name', '')
        }
    }

@router.delete("/{article_id}/concepts/{concept_id}")
def remove_concept_from_article(article_id: str, concept_id: str):
    """Remove a concept from an article"""
    
    try:
        if len(article_id) == 24:
            article = db.articles.find_one({'_id': ObjectId(article_id)})
        else:
            article = db.articles.find_one({'old_sqlite_id': int(article_id)})
    except:
        article = None
    
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    # Remove from concept service
    success = concept_service.remove_tag('article', str(article['_id']), concept_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Concept not found on this article")
    
    # Update article's concept_ids in MongoDB
    db.articles.update_one(
        {'_id': article['_id']},
        {'$pull': {'concept_ids': concept_id}}
    )
    
    return {"message": "Concept removed successfully"}


@router.delete("/{article_id}/tags/{tag_name}")
def remove_tag_from_article(article_id: str, tag_name: str):
    """Remove a tag from an article by tag name (display_name)"""

    try:
        if len(article_id) == 24:
            article = db.articles.find_one({'_id': ObjectId(article_id)})
        else:
            article = db.articles.find_one({'old_sqlite_id': int(article_id)})
    except:
        article = None

    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    # Find the concept by display_name
    concept = db.tag_concepts_v2.find_one({
        '$or': [
            {'display_name': tag_name},
            {'display_name': {'$regex': f'^{tag_name}$', '$options': 'i'}},
            {'slug': tag_name.lower().replace(' ', '-')}
        ]
    })

    if not concept:
        raise HTTPException(status_code=404, detail=f"Concept '{tag_name}' not found")

    concept_id = str(concept['_id'])

    # Remove from concept service
    success = concept_service.remove_tag('article', str(article['_id']), concept_id)

    # Also try with old_sqlite_id if present
    if not success and article.get('old_sqlite_id'):
        success = concept_service.remove_tag('article', str(article['old_sqlite_id']), concept_id)

    if not success:
        raise HTTPException(status_code=404, detail="Tag not found on this article")

    # Update article's concept_ids in MongoDB
    db.articles.update_one(
        {'_id': article['_id']},
        {'$pull': {'concept_ids': concept_id}}
    )

    return {"message": "Tag removed successfully", "removed_tag": tag_name}


@router.post("/{article_id}/tags/suggest")
async def suggest_tags_for_article(article_id: str, request: dict = Body({})):
    """
    Get AI-powered concept suggestions for an article.
    Returns existing matching concepts and new LLM-generated suggestions.
    """
    model = request.get('model', None)
    logger.info(f"Tag suggestion requested for article {article_id} with model: {model}")

    # Get article
    try:
        if len(article_id) == 24:
            article = db.articles.find_one({'_id': ObjectId(article_id)})
        else:
            article = db.articles.find_one({'old_sqlite_id': int(article_id)})
    except:
        article = None

    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    # Get existing concepts on this article
    article_id_str = str(article['_id'])
    sqlite_id_str = str(article.get('old_sqlite_id', ''))

    existing_tags = list(db.tag_instances.find({
        'content_type': 'article',
        '$or': [
            {'content_id': article_id_str},
            {'content_id': sqlite_id_str}
        ]
    }))

    existing_concept_ids = [ti['concept_id'] for ti in existing_tags if ti.get('concept_id')]

    # Get concept display names for already tagged (PERF: batch query)
    already_tagged = []
    if existing_concept_ids:
        concepts_lookup = concept_service.get_concepts_by_ids(existing_concept_ids)
        for cid in existing_concept_ids:
            concept = concepts_lookup.get(str(cid))
            if concept:
                already_tagged.append(concept.get('display_name', ''))

    # Find similar existing concepts based on title/content
    existing_suggestions = []
    all_concepts = concept_service.get_all_concepts_with_counts(content_type='article')

    # Simple text matching for suggestions
    article_text = f"{article.get('title', '')} {article.get('content_markdown', '')[:2000]}".lower()

    for concept in all_concepts[:30]:  # Check top 30 concepts
        if concept['id'] not in existing_concept_ids:
            if concept['display_name'].lower() in article_text or \
               any(alias.lower() in article_text for alias in concept.get('aliases', [])):
                existing_suggestions.append({
                    'concept_id': concept['id'],
                    'display_name': concept['display_name'],
                    'slug': concept['slug'],
                    'usage_count': concept.get('usage_count', 0)
                })
                if len(existing_suggestions) >= 5:
                    break

    # Generate new suggestions using LLM
    new_suggestions = []
    try:
        from app.services.llm_manager import get_llm_manager
        llm_manager = get_llm_manager()

        # Prepare article text for LLM - use title and content
        article_text_for_llm = f"Title: {article.get('title', '')}\n\n"
        article_text_for_llm += f"Author: {article.get('author_name', '')}\n\n"

        # Add content - limit to 8000 chars for reasonable processing time
        content = article.get('content_markdown', '') or article.get('content', '') or ''
        if content:
            article_text_for_llm += f"Article Content:\n{content[:8000]}"
            logger.info(f"Sending article content to LLM: {min(len(content), 8000)} characters")
        else:
            logger.warning(f"Article {article_id} has no content, using title only")

        # Load prompts configuration
        import os
        backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        with open(os.path.join(backend_dir, 'prompts_config.json'), 'r') as f:
            prompts_config = json.load(f)

        # Use paper tag suggestion prompt (similar enough for articles)
        tag_config = prompts_config.get('paper_tag_suggestion', {})
        system_prompt = tag_config.get('system', '')
        user_template = tag_config.get('user_template', '')
        max_tags = tag_config.get('max_tags', 20)

        # Replace placeholders
        author = article.get('author_name', 'Unknown')
        user_prompt = user_template.replace('{author}', author).replace('{text}', article_text_for_llm).replace('{max_tags}', str(max_tags))

        # Build messages
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_prompt})

        # Model mapping (same as papers)
        model_mapping = {
            "gpt-5": "gpt-5-2025-08-07",
            "gpt-5.1": "gpt-5.1",
            "gpt-5-mini": "gpt-5-mini",
            "gpt-5-nano": "gpt-5-nano",
            "gpt-4o": "gpt-4o",
            "gpt-4o-mini": "gpt-4o-mini",
            "claude-sonnet-4.5": "claude-sonnet-4-5-20250929",
            "claude-opus-4.1": "claude-opus-4-1-20250805",
            "claude-haiku-4.5": "claude-haiku-4-5-20251001",
            "claude-3.5-sonnet": "claude-sonnet-4-20250514",
            "gemini-3-flash-preview": "gemini-3-flash-preview",
            "gemini/gemini-3-flash-preview": "gemini-3-flash-preview",
            "gemini-3-pro-preview": "gemini-3-pro-preview",
            "gemini/gemini-3-pro-preview": "gemini-3-pro-preview",
            "gemini-2.5-pro": "gemini-2.5-pro",
            "gemini/gemini-2.5-pro": "gemini-2.5-pro",
            "gemini-2.5-flash": "gemini-2.5-flash",
            "gemini/gemini-2.5-flash": "gemini-2.5-flash",
        }

        # Prepare override parameters if user selected a model
        override_params = None
        if model and model in model_mapping:
            litellm_model = model_mapping[model]
            override_params = {'model': litellm_model}
            logger.info(f"Using user-selected model: {model} → {litellm_model}")
        elif model:
            logger.warning(f"Model '{model}' not found in model_mapping, falling back to default")

        # Call LLM
        task_type = 'paper_tag_suggestion_gpt5' if not model else 'paper_tag_suggestion_deep'
        llm_response = await llm_manager.completion(
            task_type=task_type,
            messages=messages,
            user_id='default',
            override_params=override_params
        )

        result = llm_response.choices[0].message.content
        model_used = llm_response.model

        logger.info(f"LLM response from {model_used}: {len(result)} chars")

        # Parse JSON response
        import re
        try:
            llm_tags = json.loads(result)
            if not isinstance(llm_tags, list):
                logger.error(f"LLM returned non-list response: {type(llm_tags)}")
                llm_tags = []
        except json.JSONDecodeError as je:
            # Try to extract JSON array from response text
            logger.warning(f"Direct JSON parse failed, attempting extraction: {je}")
            json_match = re.search(r'\[[\s\S]*\]', result)
            if json_match:
                try:
                    llm_tags = json.loads(json_match.group())
                    logger.info(f"Successfully extracted JSON array from response")
                except json.JSONDecodeError:
                    logger.error(f"Failed to parse extracted JSON: {result[:200]}")
                    llm_tags = []
            else:
                logger.error(f"No JSON array found in response: {result[:200]}")
                llm_tags = []

        # Filter out tags that already exist or are already tagged
        already_tagged_names = {t.lower() for t in already_tagged}
        existing_suggestion_names = {s['display_name'].lower() for s in existing_suggestions}

        for tag in llm_tags:
            tag_lower = tag.lower()
            if tag_lower not in already_tagged_names and tag_lower not in existing_suggestion_names:
                new_suggestions.append({
                    'display_name': tag,
                    'slug': tag.lower().replace(' ', '-'),
                    'is_new': True
                })

        logger.info(f"Generated {len(new_suggestions)} new tag suggestions for article {article_id}")

    except Exception as e:
        logger.error(f"Failed to generate LLM tag suggestions: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")

    return {
        "existing_suggestions": existing_suggestions,
        "new_suggestions": new_suggestions,
        "already_tagged": already_tagged,
        "model_used": model if model else "default"
    }


@router.post("/{article_id}/summarize")
def summarize_article(article_id: str):
    """Generate a summary for an article"""
    
    try:
        if len(article_id) == 24:
            article = db.articles.find_one({'_id': ObjectId(article_id)})
        else:
            article = db.articles.find_one({'old_sqlite_id': int(article_id)})
    except:
        article = None
    
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    # Check if already summarized
    if article.get('summary'):
        return {
            "summary": article['summary'], 
            "key_points": article.get('key_points', []),
            "model_used": article.get('summary_model', 'unknown'),
            "cached": True
        }
    
    # Get the content for summarization (use standardized content_markdown field)
    content = article.get('content_markdown', '') or article.get('preview', '')

    if not content:
        raise HTTPException(status_code=400, detail="No content available to summarize")

    # Validate content length (minimum 50 characters)
    if len(content.strip()) < 50:
        raise HTTPException(
            status_code=400,
            detail=f"Article content too short ({len(content.strip())} chars). Minimum 50 characters required."
        )

    # Import the summarization service (uses centralized LLM Manager)
    from app.services.article_summarizer import ArticleSummarizer

    try:
        summarizer = ArticleSummarizer()
    except Exception as e:
        logger.error(f"Failed to initialize ArticleSummarizer: {e}")
        raise HTTPException(status_code=500, detail=f"LLM service initialization failed: {str(e)}")
    
    # Get author name - check embedded field first, then lookup
    author_name = article.get('author_name', 'Unknown')
    if not author_name or author_name == 'Unknown':
        if article.get('author_id'):
            try:
                author_doc = db.substack_authors.find_one({'_id': article['author_id']})
                if not author_doc:
                    author_doc = db.substack_authors.find_one({'sqlite_id': article['author_id']})
                if author_doc:
                    author_name = author_doc.get('name', 'Unknown')
            except:
                pass
    
    # Generate summary with timeout handling
    try:
        summary_result = summarizer.summarize_article_content(
            content=content,
            title=article.get('title', 'Untitled'),
            author=author_name
        )
    except TimeoutError:
        raise HTTPException(status_code=504, detail="Summary generation timed out. The article might be too long.")
    except Exception as e:
        logger.error(f"Summary generation failed: {e}")
        if "API key" in str(e).lower():
            raise HTTPException(status_code=500, detail="LLM API key is invalid or missing.")
        elif "rate limit" in str(e).lower():
            raise HTTPException(status_code=429, detail="Rate limit exceeded. Please try again later.")
        else:
            raise HTTPException(status_code=500, detail=f"Summary generation failed: {str(e)}")

    if summary_result and summary_result.get('summary'):
        # Extract the summary text and key points
        summary_text = summary_result['summary']
        key_points = summary_result.get('key_points', [])
        model_used = summary_result.get('model_used', 'unknown')

        # Save the summary to the database
        db.articles.update_one(
            {'_id': article['_id']},
            {
                '$set': {
                    'summary': summary_text,
                    'key_points': key_points,
                    'summarized': True,
                    'summarized_at': datetime.utcnow(),
                    'summary_model': model_used
                }
            }
        )

        return {
            "summary": summary_text,
            "key_points": key_points,
            "model_used": model_used,
            "cached": False
        }
    else:
        raise HTTPException(status_code=500, detail="Summary generation returned empty result")

@router.post("/{article_id}/snippets")
def add_snippet(article_id: str, snippet: Dict[str, Any] = Body(...)):
    """Add a snippet to an article"""
    
    try:
        if len(article_id) == 24:
            article = db.articles.find_one({'_id': ObjectId(article_id)})
        else:
            article = db.articles.find_one({'old_sqlite_id': int(article_id)})
    except:
        article = None
    
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    # Create snippet document
    new_snippet = {
        'id': str(ObjectId()),
        'text': snippet.get('text', ''),
        'annotation': snippet.get('annotation', ''),
        'created_at': datetime.utcnow().isoformat()
    }
    
    # Add snippet to article
    db.articles.update_one(
        {'_id': article['_id']},
        {'$push': {'snippets': new_snippet}}
    )
    
    return {"message": "Snippet added successfully", "snippet": new_snippet}

@router.delete("/{article_id}/snippets/{snippet_id}")
def remove_snippet(article_id: str, snippet_id: str):
    """Remove a snippet from an article"""
    
    try:
        if len(article_id) == 24:
            article = db.articles.find_one({'_id': ObjectId(article_id)})
        else:
            article = db.articles.find_one({'old_sqlite_id': int(article_id)})
    except:
        article = None
    
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    # Remove snippet from article
    db.articles.update_one(
        {'_id': article['_id']},
        {'$pull': {'snippets': {'id': snippet_id}}}
    )
    
    return {"message": "Snippet removed successfully"}

@router.put("/authors/{author_id}")
def update_author(author_id: str, author_data: Dict[str, str] = Body(...)):
    """Update an author's details"""
    
    try:
        author = db.substack_authors.find_one({'_id': ObjectId(author_id)})
    except:
        author = None
    
    if not author:
        raise HTTPException(status_code=404, detail="Author not found")
    
    # Update author details
    update_doc = {}
    if 'name' in author_data:
        update_doc['name'] = author_data['name']
    if 'email' in author_data:
        update_doc['email'] = author_data['email']
    if 'subdomain' in author_data:
        update_doc['subdomain'] = author_data['subdomain']
    if 'description' in author_data:
        update_doc['description'] = author_data['description']
    
    if update_doc:
        db.substack_authors.update_one(
            {'_id': author['_id']},
            {'$set': update_doc}
        )
        
        # Also update author_name in all articles if name changed
        if 'name' in update_doc:
            # Build query to find all articles by this author
            or_conditions = []
            
            # Match by old name
            if author.get('name'):
                or_conditions.append({'author_name': author['name']})
            
            # Match by SQLite ID
            if author.get('old_sqlite_id'):
                or_conditions.append({'author_id': author['old_sqlite_id']})
                or_conditions.append({'author_sqlite_id': author['old_sqlite_id']})
            
            # Match by MongoDB ObjectId (for newer articles)
            or_conditions.append({'author_id': author['_id']})
            
            if or_conditions:
                db.articles.update_many(
                    {'$or': or_conditions},
                    {'$set': {'author_name': update_doc['name']}}
                )
    
    return {"message": "Author updated successfully"}

@router.delete("/authors/{author_id}")
def delete_author(author_id: str, delete_articles: bool = Query(False)):
    """Delete an author and optionally their articles"""
    
    try:
        author = db.substack_authors.find_one({'_id': ObjectId(author_id)})
    except:
        author = None
    
    if not author:
        raise HTTPException(status_code=404, detail="Author not found")
    
    # Count articles by this author
    article_count = db.articles.count_documents({'author_id': author['_id']})
    
    if delete_articles:
        # Delete all articles by this author
        db.articles.delete_many({'author_id': author['_id']})
    else:
        # Clear author from articles
        db.articles.update_many(
            {'author_id': author['_id']},
            {'$set': {'author_id': None, 'author_name': None}}
        )
    
    # Delete the author
    db.substack_authors.delete_one({'_id': author['_id']})
    
    return {
        "message": "Author deleted successfully",
        "articles_deleted": article_count if delete_articles else 0,
        "articles_unlinked": article_count if not delete_articles else 0
    }

@router.post("/authors/{author_id}/assign-articles")
def assign_articles_to_author(author_id: str, article_ids: List[str] = Body(...)):
    """Assign multiple articles to an author"""
    
    try:
        author = db.substack_authors.find_one({'_id': ObjectId(author_id)})
    except:
        author = None
    
    if not author:
        raise HTTPException(status_code=404, detail="Author not found")
    
    # Convert article IDs to ObjectIds
    object_ids = []
    for aid in article_ids:
        try:
            if len(aid) == 24:
                object_ids.append(ObjectId(aid))
        except:
            pass
    
    if object_ids:
        # Update all specified articles
        result = db.articles.update_many(
            {'_id': {'$in': object_ids}},
            {'$set': {
                'author_id': author['_id'],
                'author_name': author.get('name'),
                'author_email': author.get('email')
            }}
        )
        
        return {
            "message": f"Assigned {result.modified_count} articles to {author.get('name')}",
            "modified_count": result.modified_count
        }
    
    return {"message": "No valid article IDs provided", "modified_count": 0}

@router.get("/without-author")
def get_articles_without_author(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200)
):
    """Get articles that don't have an author assigned"""
    
    query = {
        '$or': [
            {'author_id': None},
            {'author_id': {'$exists': False}},
            {'author_name': None},
            {'author_name': ''}
        ]
    }
    
    total = db.articles.count_documents(query)
    skip = (page - 1) * page_size
    
    articles = list(db.articles.find(query)
        .sort('published_at', DESCENDING)
        .skip(skip)
        .limit(page_size))
    
    result = []
    for article in articles:
        result.append({
            'id': str(article['_id']),
            'title': article.get('title'),
            'url': article.get('url'),
            'published_at': article.get('published_at').isoformat() if article.get('published_at') else None,
            'preview': article.get('preview', '')[:200]
        })
    
    return {
        'articles': result,
        'total': total,
        'page': page,
        'page_size': page_size
    }

@router.get("/authors/all")
def get_all_authors():
    """Get all Substack authors from MongoDB"""
    
    authors = list(db.substack_authors.find())
    
    result = []
    for author in authors:
        # Count articles - check multiple fields since IDs are mixed
        article_count = 0
        
        # Check by author name (most reliable)
        article_count += db.articles.count_documents({'author_name': author.get('name')})
        
        # Check by old SQLite ID if it exists
        if author.get('old_sqlite_id'):
            article_count += db.articles.count_documents({'author_id': author['old_sqlite_id']})
            article_count += db.articles.count_documents({'author_sqlite_id': author['old_sqlite_id']})
        
        # Check by MongoDB ObjectId (for newer articles)
        article_count += db.articles.count_documents({'author_id': author['_id']})
        
        result.append({
            'id': str(author['_id']),
            'name': author.get('name'),
            'subdomain': author.get('subdomain'),
            'description': author.get('description'),
            'url': author.get('url'),
            'email': author.get('email'),
            'article_count': article_count
        })
    
    return result

@router.get("/authors")
def get_all_authors():
    """Get all authors with article counts"""
    
    authors = list(db.substack_authors.find())
    result = []
    
    for author in authors:
        # Count articles for this author - check multiple fields since IDs are mixed
        article_count = 0
        
        # Check by author name (most reliable)
        article_count += db.articles.count_documents({'author_name': author.get('name')})
        
        # Check by old SQLite ID if it exists
        if author.get('old_sqlite_id'):
            article_count += db.articles.count_documents({'author_id': author['old_sqlite_id']})
            article_count += db.articles.count_documents({'author_sqlite_id': author['old_sqlite_id']})
        
        # Check by MongoDB ObjectId (for newer articles)
        article_count += db.articles.count_documents({'author_id': author['_id']})
        
        result.append({
            'id': str(author['_id']),
            'name': author.get('name'),
            'email': author.get('email'),
            'subdomain': author.get('subdomain'),
            'description': author.get('description'),
            'url': author.get('url'),
            'article_count': article_count
        })
    
    # Sort by name
    result.sort(key=lambda x: x['name'].lower() if x['name'] else '')
    
    return result

# Duplicate endpoint removed - see line 821 for the paginated version

@router.post("/authors")
def create_author(author_data: Dict[str, str] = Body(...)):
    """Create a new author"""
    
    # Check if author with same name already exists
    existing = db.substack_authors.find_one({'name': author_data.get('name')})
    if existing:
        return {
            'id': str(existing['_id']),
            'name': existing.get('name'),
            'exists': True
        }
    
    # Create new author
    new_author = {
        'name': author_data.get('name'),
        'email': author_data.get('email'),
        'subdomain': author_data.get('subdomain'),
        'description': author_data.get('description'),
        'url': author_data.get('url'),
        'created_at': datetime.utcnow()
    }
    
    result = db.substack_authors.insert_one(new_author)
    
    return {
        'id': str(result.inserted_id),
        'name': new_author['name'],
        'exists': False
    }

@router.put("/{article_id}/author")
def update_article_author(article_id: str, author_data: Dict[str, Any] = Body(...)):
    """Update an article's author - can be existing ID or new author name"""
    
    try:
        if len(article_id) == 24:
            article = db.articles.find_one({'_id': ObjectId(article_id)})
        else:
            article = db.articles.find_one({'old_sqlite_id': int(article_id)})
    except:
        article = None
    
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    # Check if we have an author_id or a new author name
    if 'author_id' in author_data:
        # Using existing author
        author_id = author_data['author_id']
        if author_id:
            # Verify author exists
            author = db.substack_authors.find_one({'_id': ObjectId(author_id)})
            if author:
                # Update article with author info
                db.articles.update_one(
                    {'_id': article['_id']},
                    {'$set': {
                        'author_id': author['_id'],
                        'author_name': author.get('name'),
                        'author_email': author.get('email')
                    }}
                )
            else:
                raise HTTPException(status_code=404, detail="Author not found")
        else:
            # Clear author
            db.articles.update_one(
                {'_id': article['_id']},
                {'$set': {
                    'author_id': None,
                    'author_name': None,
                    'author_email': None
                }}
            )
    elif 'author_name' in author_data:
        # Creating or finding author by name
        author_name = author_data['author_name']
        
        if not author_name:
            # Clear author
            db.articles.update_one(
                {'_id': article['_id']},
                {'$set': {
                    'author_id': None,
                    'author_name': None,
                    'author_email': None
                }}
            )
        else:
            # Check if author exists
            existing_author = db.substack_authors.find_one({'name': author_name})
            
            if existing_author:
                # Use existing author
                db.articles.update_one(
                    {'_id': article['_id']},
                    {'$set': {
                        'author_id': existing_author['_id'],
                        'author_name': existing_author.get('name'),
                        'author_email': existing_author.get('email')
                    }}
                )
            else:
                # Create new author
                new_author = {
                    'name': author_name,
                    'email': author_data.get('author_email'),
                    'created_at': datetime.utcnow()
                }
                result = db.substack_authors.insert_one(new_author)
                
                # Update article with new author
                db.articles.update_one(
                    {'_id': article['_id']},
                    {'$set': {
                        'author_id': result.inserted_id,
                        'author_name': author_name,
                        'author_email': author_data.get('author_email')
                    }}
                )
    
    return {"message": "Author updated successfully"}

@router.patch("/{article_id}")
def update_article(article_id: str, updates: Dict[str, Any] = Body(...)):
    """Update article fields (title, content, url, date, etc.)"""
    
    try:
        if len(article_id) == 24:
            article = db.articles.find_one({'_id': ObjectId(article_id)})
        else:
            article = db.articles.find_one({'old_sqlite_id': int(article_id)})
    except:
        article = None
    
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    # Build update document - only include fields that are provided
    update_doc = {}
    
    if 'title' in updates:
        update_doc['title'] = updates['title']
    
    if 'content_markdown' in updates:
        update_doc['content_markdown'] = updates['content_markdown']
        # Also update content field for compatibility
        update_doc['content'] = updates['content_markdown']
    
    if 'content' in updates:
        update_doc['content'] = updates['content']
        # If content_markdown not provided, also update it
        if 'content_markdown' not in updates:
            update_doc['content_markdown'] = updates['content']
    
    if 'url' in updates:
        update_doc['url'] = updates['url']
    
    if 'published_at' in updates:
        if updates['published_at']:
            update_doc['published_at'] = datetime.fromisoformat(updates['published_at'].replace('Z', '+00:00'))
        else:
            update_doc['published_at'] = None
    
    if 'author_id' in updates:
        update_doc['author_id'] = updates['author_id']
    
    if update_doc:
        # Add updated timestamp
        update_doc['updated_at'] = datetime.utcnow()

        # Update the article
        db.articles.update_one(
            {'_id': article['_id']},
            {'$set': update_doc}
        )

        return {"message": "Article updated successfully", "updated_fields": list(update_doc.keys())}
    else:
        return {"message": "No fields to update"}


@router.post("/{article_id}/recollect")
async def recollect_article(article_id: str):
    """
    Re-collect an article using Playwright to get fresh/complete content.

    Useful when an article was initially imported incompletely or
    when you want to refresh the content.
    """
    # Find the article
    try:
        if len(article_id) == 24:
            article = db.articles.find_one({'_id': ObjectId(article_id)})
        else:
            article = db.articles.find_one({'old_sqlite_id': int(article_id)})
    except:
        article = None

    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    # Get the URL
    url = article.get('url')
    if not url:
        raise HTTPException(status_code=400, detail="Article has no URL to recollect from")

    try:
        from app.collectors.playwright_collector import PlaywrightCollector

        collector = PlaywrightCollector()
        try:
            result = await collector.fetch_article(url)

            if not result.get('success'):
                return {
                    'success': False,
                    'error': result.get('error', 'Failed to fetch article'),
                    'requires_auth': result.get('requires_auth', False),
                    'site': result.get('site'),
                    'auth_url': result.get('auth_url')
                }

            # Update the article with new content
            update_doc = {
                'content_html': result.get('content_html'),
                'content_markdown': result.get('content_markdown'),
                'preview': result.get('preview'),
                'word_count': result.get('word_count', 0),
                'reading_time_minutes': result.get('reading_time_minutes', 0),
                'recollected_at': datetime.utcnow(),
            }

            # Update title if we got a better one (not just a number)
            new_title = result.get('title')
            if new_title and not new_title.isdigit() and new_title != article.get('title'):
                update_doc['title'] = new_title

            # Update author if we got one and didn't have one before
            if result.get('author') and not article.get('author_name'):
                update_doc['author_name'] = result.get('author')

            db.articles.update_one(
                {'_id': article['_id']},
                {'$set': update_doc}
            )

            return {
                'success': True,
                'article_id': str(article['_id']),
                'title': update_doc.get('title', article.get('title')),
                'word_count': result.get('word_count', 0),
                'reading_time_minutes': result.get('reading_time_minutes', 0),
                'updated_fields': list(update_doc.keys())
            }

        finally:
            await collector.close()

    except ImportError:
        raise HTTPException(
            status_code=503,
            detail="Playwright not installed. Run: pip install playwright && playwright install chromium"
        )
    except Exception as e:
        logger.error(f"Failed to recollect article: {e}")
        raise HTTPException(status_code=500, detail=str(e))
