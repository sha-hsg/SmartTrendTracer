"""
Data access for app.api.articles.content (extracted by the arch-audit refactor).

Content CRUD, concept/tag management, and snippet routes for articles.
"""
from app.repositories.errors import InvalidInputError, NotFoundError
from bson import ObjectId
from datetime import datetime
from datetime import timezone
from pymongo import DESCENDING
import re

from app.database.mongodb import get_database

db = get_database()




def add_concept_to_article(article_id, text, concept_service):
    """Add a concept to an article"""

    try:
        if len(article_id) == 24:
            article = db.articles.find_one({'_id': ObjectId(article_id)})
        else:
            article = db.articles.find_one({'old_sqlite_id': int(article_id)})
    except Exception:
        article = None

    if not article:
        raise NotFoundError("Article not found")

    # Add concept using the service
    success, concept_id = concept_service.add_tag('article', str(article['_id']), text)

    if not success:
        raise InvalidInputError("Failed to add concept")

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



def remove_concept_from_article(article_id, concept_id, concept_service):
    """Remove a concept from an article"""

    try:
        if len(article_id) == 24:
            article = db.articles.find_one({'_id': ObjectId(article_id)})
        else:
            article = db.articles.find_one({'old_sqlite_id': int(article_id)})
    except Exception:
        article = None

    if not article:
        raise NotFoundError("Article not found")

    # Remove from concept service
    success = concept_service.remove_tag('article', str(article['_id']), concept_id)

    if not success:
        raise NotFoundError("Concept not found on this article")

    # Update article's concept_ids in MongoDB
    db.articles.update_one(
        {'_id': article['_id']},
        {'$pull': {'concept_ids': concept_id}}
    )

    return {"message": "Concept removed successfully"}



def remove_tag_from_article(article_id, tag_name, concept_service):
    """Remove a tag from an article by tag name (display_name)"""

    try:
        if len(article_id) == 24:
            article = db.articles.find_one({'_id': ObjectId(article_id)})
        else:
            article = db.articles.find_one({'old_sqlite_id': int(article_id)})
    except Exception:
        article = None

    if not article:
        raise NotFoundError("Article not found")

    # Find the concept by display_name
    concept = db.tag_concepts_v2.find_one({
        '$or': [
            {'display_name': tag_name},
            {'display_name': {'$regex': f'^{re.escape(tag_name)}$', '$options': 'i'}},
            {'slug': tag_name.lower().replace(' ', '-')}
        ]
    })

    if not concept:
        raise NotFoundError(f"Concept '{tag_name}' not found")

    concept_id = str(concept['_id'])

    # Remove from concept service
    success = concept_service.remove_tag('article', str(article['_id']), concept_id)

    # Also try with old_sqlite_id if present
    if not success and article.get('old_sqlite_id'):
        success = concept_service.remove_tag('article', str(article['old_sqlite_id']), concept_id)

    if not success:
        raise NotFoundError("Tag not found on this article")

    # Update article's concept_ids in MongoDB
    db.articles.update_one(
        {'_id': article['_id']},
        {'$pull': {'concept_ids': concept_id}}
    )

    return {"message": "Tag removed successfully", "removed_tag": tag_name}



def add_snippet(article_id, snippet):
    """Add a snippet to an article"""

    try:
        if len(article_id) == 24:
            article = db.articles.find_one({'_id': ObjectId(article_id)})
        else:
            article = db.articles.find_one({'old_sqlite_id': int(article_id)})
    except Exception:
        article = None

    if not article:
        raise NotFoundError("Article not found")

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



def remove_snippet(article_id, snippet_id):
    """Remove a snippet from an article"""

    try:
        if len(article_id) == 24:
            article = db.articles.find_one({'_id': ObjectId(article_id)})
        else:
            article = db.articles.find_one({'old_sqlite_id': int(article_id)})
    except Exception:
        article = None

    if not article:
        raise NotFoundError("Article not found")

    # Remove snippet from article
    db.articles.update_one(
        {'_id': article['_id']},
        {'$pull': {'snippets': {'id': snippet_id}}}
    )

    return {"message": "Snippet removed successfully"}



def update_article(article_id, updates):
    """Update article fields (title, content, url, date, etc.)"""

    try:
        if len(article_id) == 24:
            article = db.articles.find_one({'_id': ObjectId(article_id)})
        else:
            article = db.articles.find_one({'old_sqlite_id': int(article_id)})
    except Exception:
        article = None

    if not article:
        raise NotFoundError("Article not found")

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



def get_articles_without_author(page, page_size):
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

