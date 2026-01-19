"""
Author Management API Endpoints

Provides comprehensive author management functionality including:
- List all authors with statistics
- Get author details
- Update author information
- Delete authors
- Find similar authors for merging
- Merge duplicate authors
- Author analytics
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime
from bson import ObjectId

from app.database.mongodb import get_database
from app.services.author_service import AuthorService

router = APIRouter()

# MongoDB connection
db = get_database()

# Initialize author service
author_service = AuthorService(db)


# Pydantic Models
class AuthorResponse(BaseModel):
    id: str
    name: str
    canonical_name: Optional[str] = None
    subdomain: Optional[str] = None
    email: Optional[str] = None
    article_count: int = 0
    last_article_date: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class AuthorUpdateRequest(BaseModel):
    name: Optional[str] = None
    canonical_name: Optional[str] = None
    subdomain: Optional[str] = None
    email: Optional[EmailStr] = None


class AuthorMergeRequest(BaseModel):
    source_id: str
    target_id: str


class FindSimilarRequest(BaseModel):
    name: str
    threshold: float = 0.85


@router.get("/", response_model=Dict[str, Any])
def list_authors(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    search: Optional[str] = None,
    sort_by: str = Query("article_count", regex="^(name|article_count|last_article_date|created_at)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$")
):
    """
    List all authors with pagination, search, and sorting
    """
    # Build query
    query = {}
    if search:
        query['$or'] = [
            {'name': {'$regex': search, '$options': 'i'}},
            {'canonical_name': {'$regex': search, '$options': 'i'}}
        ]

    # Build sort
    sort_direction = -1 if sort_order == "desc" else 1
    sort_spec = [(sort_by, sort_direction)]

    # Get total count
    total = db.substack_authors.count_documents(query)

    # Get paginated results
    skip = (page - 1) * page_size
    authors = list(db.substack_authors.find(query)
                   .sort(sort_spec)
                   .skip(skip)
                   .limit(page_size))

    # Format response
    author_list = []
    for author in authors:
        author_list.append({
            'id': str(author['_id']),
            'name': author.get('name'),
            'canonical_name': author.get('canonical_name'),
            'subdomain': author.get('subdomain'),
            'email': author.get('email'),
            'article_count': author.get('article_count', 0),
            'last_article_date': author.get('last_article_date').isoformat() if author.get('last_article_date') else None,
            'created_at': author.get('created_at').isoformat() if author.get('created_at') else None,
            'updated_at': author.get('updated_at').isoformat() if author.get('updated_at') else None
        })

    return {
        'authors': author_list,
        'total': total,
        'page': page,
        'page_size': page_size,
        'pages': (total + page_size - 1) // page_size
    }


@router.get("/{author_id}", response_model=Dict[str, Any])
def get_author(author_id: str):
    """
    Get detailed author information including articles
    """
    try:
        # Get author
        author = db.substack_authors.find_one({'_id': ObjectId(author_id)})
        if not author:
            raise HTTPException(status_code=404, detail="Author not found")

        # Get author's articles
        articles = list(db.articles.find(
            {'primary_author_id': ObjectId(author_id)},
            {'title': 1, 'url': 1, 'published_at': 1, 'word_count': 1, 'preview': 1}
        ).sort('published_at', -1).limit(20))

        # Calculate statistics
        total_words = sum(a.get('word_count', 0) for a in articles)
        avg_words = total_words // len(articles) if articles else 0

        # Get first and last article dates
        all_articles = list(db.articles.find(
            {'primary_author_id': ObjectId(author_id)},
            {'published_at': 1}
        ).sort('published_at', 1))

        first_article_date = all_articles[0].get('published_at') if all_articles else None
        last_article_date = all_articles[-1].get('published_at') if all_articles else None

        # Format response
        return {
            'author': {
                'id': str(author['_id']),
                'name': author.get('name'),
                'canonical_name': author.get('canonical_name'),
                'subdomain': author.get('subdomain'),
                'email': author.get('email'),
                'article_count': author.get('article_count', 0),
                'last_article_date': last_article_date.isoformat() if last_article_date else None,
                'created_at': author.get('created_at').isoformat() if author.get('created_at') else None,
                'updated_at': author.get('updated_at').isoformat() if author.get('updated_at') else None
            },
            'articles': [
                {
                    'id': str(a['_id']),
                    'title': a.get('title'),
                    'url': a.get('url'),
                    'published_at': a.get('published_at').isoformat() if a.get('published_at') else None,
                    'word_count': a.get('word_count', 0),
                    'preview': a.get('preview', '')[:200]
                }
                for a in articles
            ],
            'statistics': {
                'total_articles': len(all_articles),
                'total_words': total_words,
                'avg_words_per_article': avg_words,
                'first_article_date': first_article_date.isoformat() if first_article_date else None,
                'last_article_date': last_article_date.isoformat() if last_article_date else None
            }
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{author_id}")
def update_author(author_id: str, update_data: AuthorUpdateRequest):
    """
    Update author information
    """
    try:
        # Check if author exists
        author = db.substack_authors.find_one({'_id': ObjectId(author_id)})
        if not author:
            raise HTTPException(status_code=404, detail="Author not found")

        # Build update document
        update_doc = {'updated_at': datetime.utcnow()}

        if update_data.name is not None:
            update_doc['name'] = update_data.name
        if update_data.canonical_name is not None:
            update_doc['canonical_name'] = update_data.canonical_name
        if update_data.subdomain is not None:
            update_doc['subdomain'] = update_data.subdomain
        if update_data.email is not None:
            update_doc['email'] = update_data.email

        # Update author
        db.substack_authors.update_one(
            {'_id': ObjectId(author_id)},
            {'$set': update_doc}
        )

        # Get updated author
        updated_author = db.substack_authors.find_one({'_id': ObjectId(author_id)})

        return {
            'success': True,
            'author': {
                'id': str(updated_author['_id']),
                'name': updated_author.get('name'),
                'canonical_name': updated_author.get('canonical_name'),
                'subdomain': updated_author.get('subdomain'),
                'email': updated_author.get('email'),
                'article_count': updated_author.get('article_count', 0)
            }
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{author_id}")
def delete_author(author_id: str):
    """
    Delete author (only if article_count is 0)
    """
    try:
        # Check if author exists
        author = db.substack_authors.find_one({'_id': ObjectId(author_id)})
        if not author:
            raise HTTPException(status_code=404, detail="Author not found")

        # Check article count
        article_count = db.articles.count_documents({'primary_author_id': ObjectId(author_id)})
        if article_count > 0:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot delete author with {article_count} articles. Reassign or delete articles first."
            )

        # Delete author
        db.substack_authors.delete_one({'_id': ObjectId(author_id)})

        return {
            'success': True,
            'message': f"Author '{author.get('name')}' deleted successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/find-similar")
def find_similar_authors(request: FindSimilarRequest):
    """
    Find authors with similar names (for merge detection)
    """
    try:
        similar = author_service.find_similar_authors(
            request.name,
            threshold=request.threshold
        )

        # Get full author details for each similar author
        similar_authors = []
        for sim in similar:
            author = db.substack_authors.find_one({'_id': sim['_id']})
            if author:
                similar_authors.append({
                    'author': {
                        'id': str(author['_id']),
                        'name': author.get('name'),
                        'canonical_name': author.get('canonical_name'),
                        'subdomain': author.get('subdomain'),
                        'article_count': author.get('article_count', 0)
                    },
                    'similarity': sim['similarity']
                })

        return {
            'query': request.name,
            'threshold': request.threshold,
            'similar_authors': similar_authors,
            'count': len(similar_authors)
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/merge")
def merge_authors(request: AuthorMergeRequest):
    """
    Merge two author records (source → target)
    """
    try:
        # Validate IDs
        source_id = ObjectId(request.source_id)
        target_id = ObjectId(request.target_id)

        # Check if both authors exist
        source = db.substack_authors.find_one({'_id': source_id})
        target = db.substack_authors.find_one({'_id': target_id})

        if not source:
            raise HTTPException(status_code=404, detail="Source author not found")
        if not target:
            raise HTTPException(status_code=404, detail="Target author not found")

        # Perform merge
        success = author_service.merge_authors(source_id, target_id)

        if not success:
            raise HTTPException(status_code=500, detail="Merge failed")

        # Get updated target author
        merged_author = db.substack_authors.find_one({'_id': target_id})

        return {
            'success': True,
            'message': f"Successfully merged '{source.get('name')}' into '{target.get('name')}'",
            'merged_author': {
                'id': str(merged_author['_id']),
                'name': merged_author.get('name'),
                'canonical_name': merged_author.get('canonical_name'),
                'article_count': merged_author.get('article_count', 0)
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/analytics/overview")
def get_author_analytics():
    """
    Get analytics data for author dashboard
    """
    try:
        # Top authors by article count
        top_authors = list(db.substack_authors.find(
            {'article_count': {'$gt': 0}}
        ).sort('article_count', -1).limit(10))

        # Publishing frequency by month (last 12 months)
        from datetime import datetime, timedelta
        twelve_months_ago = datetime.utcnow() - timedelta(days=365)

        # Aggregate articles by month
        pipeline = [
            {'$match': {'published_at': {'$gte': twelve_months_ago}}},
            {'$group': {
                '_id': {
                    'year': {'$year': '$published_at'},
                    'month': {'$month': '$published_at'}
                },
                'count': {'$sum': 1}
            }},
            {'$sort': {'_id.year': 1, '_id.month': 1}}
        ]
        publishing_freq = list(db.articles.aggregate(pipeline))

        # Word count by author
        pipeline = [
            {'$match': {'primary_author_id': {'$exists': True}}},
            {'$group': {
                '_id': '$primary_author_id',
                'total_words': {'$sum': '$word_count'},
                'article_count': {'$sum': 1}
            }},
            {'$addFields': {
                'avg_words': {'$divide': ['$total_words', '$article_count']}
            }},
            {'$sort': {'article_count': -1}},
            {'$limit': 10}
        ]
        word_counts = list(db.articles.aggregate(pipeline))

        # Get author names for word counts
        word_count_data = []
        for wc in word_counts:
            author = db.substack_authors.find_one({'_id': wc['_id']})
            if author:
                word_count_data.append({
                    'author': author.get('name'),
                    'avg_words': int(wc['avg_words']),
                    'total_words': wc['total_words'],
                    'article_count': wc['article_count']
                })

        # Summary statistics
        total_authors = db.substack_authors.count_documents({})
        active_authors = db.substack_authors.count_documents({'article_count': {'$gt': 0}})
        total_articles = db.articles.count_documents({})
        avg_articles_per_author = total_articles / active_authors if active_authors > 0 else 0

        return {
            'top_authors': [
                {
                    'name': a.get('name'),
                    'article_count': a.get('article_count', 0),
                    'subdomain': a.get('subdomain')
                }
                for a in top_authors
            ],
            'publishing_frequency': [
                {
                    'month': f"{pf['_id']['year']}-{pf['_id']['month']:02d}",
                    'count': pf['count']
                }
                for pf in publishing_freq
            ],
            'word_count_by_author': word_count_data,
            'summary': {
                'total_authors': total_authors,
                'active_authors': active_authors,
                'total_articles': total_articles,
                'avg_articles_per_author': round(avg_articles_per_author, 1)
            }
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
