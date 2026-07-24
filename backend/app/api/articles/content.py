"""Content CRUD, concept/tag management, and snippet routes for articles."""

from fastapi import APIRouter, HTTPException, Query, Body
from pymongo import DESCENDING
from typing import Dict, Any
from datetime import datetime, timezone
import re
from bson import ObjectId

from .utils import db, logger, concept_service

router = APIRouter()


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
    except Exception:
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
        "success": True,
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
    except Exception:
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
    except Exception:
        article = None

    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    # Find the concept by display_name
    concept = db.tag_concepts_v2.find_one({
        '$or': [
            {'display_name': tag_name},
            {'display_name': {'$regex': f'^{re.escape(tag_name)}$', '$options': 'i'}},
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


@router.post("/{article_id}/snippets")
def add_snippet(article_id: str, snippet: Dict[str, Any] = Body(...)):
    """Add a snippet to an article"""

    try:
        if len(article_id) == 24:
            article = db.articles.find_one({'_id': ObjectId(article_id)})
        else:
            article = db.articles.find_one({'old_sqlite_id': int(article_id)})
    except Exception:
        article = None

    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    # Create snippet document
    new_snippet = {
        'id': str(ObjectId()),
        'text': snippet.get('text', ''),
        'annotation': snippet.get('annotation', ''),
        'created_at': datetime.now(timezone.utc).isoformat()
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
    except Exception:
        article = None

    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    # Remove snippet from article
    db.articles.update_one(
        {'_id': article['_id']},
        {'$pull': {'snippets': {'id': snippet_id}}}
    )

    return {"message": "Snippet removed successfully"}

@router.patch("/{article_id}")
def update_article(article_id: str, updates: Dict[str, Any] = Body(...)):
    """Update article fields (title, content, url, date, etc.)"""

    try:
        if len(article_id) == 24:
            article = db.articles.find_one({'_id': ObjectId(article_id)})
        else:
            article = db.articles.find_one({'old_sqlite_id': int(article_id)})
    except Exception:
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
        update_doc['updated_at'] = datetime.now(timezone.utc)

        # Update the article
        db.articles.update_one(
            {'_id': article['_id']},
            {'$set': update_doc}
        )

        return {"message": "Article updated successfully", "updated_fields": list(update_doc.keys())}
    else:
        return {"message": "No fields to update"}


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
