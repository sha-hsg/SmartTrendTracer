"""Author management routes for articles."""

from fastapi import APIRouter, HTTPException, Query, Body
from typing import List, Dict, Any
from datetime import datetime, timezone
from bson import ObjectId

from .utils import db, logger

router = APIRouter()


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
        'created_at': datetime.now(timezone.utc)
    }

    result = db.substack_authors.insert_one(new_author)

    return {
        'id': str(result.inserted_id),
        'name': new_author['name'],
        'exists': False
    }

@router.put("/authors/{author_id}")
def update_author(author_id: str, author_data: Dict[str, str] = Body(...)):
    """Update an author's details"""

    try:
        author = db.substack_authors.find_one({'_id': ObjectId(author_id)})
    except Exception:
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
    except Exception:
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

@router.put("/{article_id}/author")
def update_article_author(article_id: str, author_data: Dict[str, Any] = Body(...)):
    """Update an article's author - can be existing ID or new author name"""

    try:
        if len(article_id) == 24:
            article = db.articles.find_one({'_id': ObjectId(article_id)})
        else:
            article = db.articles.find_one({'old_sqlite_id': int(article_id)})
    except Exception:
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
                    'created_at': datetime.now(timezone.utc)
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

@router.post("/authors/{author_id}/assign-articles")
def assign_articles_to_author(author_id: str, article_ids: List[str] = Body(...)):
    """Assign multiple articles to an author"""

    try:
        author = db.substack_authors.find_one({'_id': ObjectId(author_id)})
    except Exception:
        author = None

    if not author:
        raise HTTPException(status_code=404, detail="Author not found")

    # Convert article IDs to ObjectIds
    object_ids = []
    for aid in article_ids:
        try:
            if len(aid) == 24:
                object_ids.append(ObjectId(aid))
        except Exception:
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
