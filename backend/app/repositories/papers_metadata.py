"""
Data access for app.api.papers.metadata (extracted by the arch-audit refactor).

Paper metadata route handlers.

Covers: metadata update, flag toggle, star rating, and generic field patching.
"""
from app.repositories.errors import DataAccessError, NotFoundError
from app.repositories.papers import find_paper_by_id
from bson import ObjectId
from datetime import datetime
from datetime import timezone

from app.database.mongodb import get_database

db = get_database()




def update_paper_content(paper_id, data):
    """Update paper content/markdown content"""

    content = data.get('content', '')

    paper = find_paper_by_id(paper_id)
    if not paper:
        raise NotFoundError("Paper not found")

    filter_query = {'_id': paper['_id']}

    # Update both content and markdown_content fields
    update_data = {
        'content': content,
        'markdown_content': content,
        'updated_at': datetime.now(timezone.utc)  # BSON datetime, not ISO string
    }

    # Perform the update
    result = db.papers.update_one(
        filter_query,
        {'$set': update_data}
    )

    # matched_count (not modified_count): saving identical content is not an error
    if result.matched_count == 0:
        raise DataAccessError("Failed to update paper content")

    return {
        "success": True,
        "message": "Paper content updated successfully",
        "updated_at": update_data['updated_at']
    }



def update_paper_metadata(paper_id, metadata):
    """Update paper metadata"""
    paper = find_paper_by_id(paper_id)
    if not paper:
        raise NotFoundError("Paper not found")

    # Prepare update data
    update_data = {}

    # Update basic metadata fields
    if 'title' in metadata:
        update_data['title'] = metadata['title']
    if 'abstract' in metadata:
        update_data['abstract'] = metadata['abstract']
    if 'publication_date' in metadata:
        update_data['publication_date'] = metadata['publication_date']
    if 'published_date' in metadata:
        # Map published_date input to publication_date (canonical field)
        # Also keep published_date for backwards compatibility with existing queries
        update_data['publication_date'] = metadata['published_date']
        update_data['published_date'] = metadata['published_date']
    if 'conference' in metadata:
        update_data['conference'] = metadata['conference']
    if 'journal' in metadata:
        update_data['journal'] = metadata['journal']
    if 'arxiv_id' in metadata:
        update_data['arxiv_id'] = metadata['arxiv_id']
    if 'doi' in metadata:
        update_data['doi'] = metadata['doi']

    # Handle flagged status (bookmark/mark for later)
    # System convention is `is_flagged` (see crud.py / flag endpoint)
    if 'flagged' in metadata:
        update_data['is_flagged'] = bool(metadata['flagged'])

    # Handle star rating (1-5 stars, or null to clear)
    # System convention is `user_rating` (see crud.py / rating endpoint)
    if 'rating' in metadata:
        rating = metadata['rating']
        if rating is None:
            update_data['user_rating'] = None
        elif isinstance(rating, (int, float)) and 1 <= rating <= 5:
            update_data['user_rating'] = int(rating)

    # Handle notes/comments
    if 'notes' in metadata:
        update_data['notes'] = metadata['notes']

    # Handle review-specific fields
    if 'review_deadline' in metadata:
        update_data['review_deadline'] = metadata['review_deadline']
    if 'review_decision' in metadata:
        update_data['review_decision'] = metadata['review_decision']
    if 'review_notes' in metadata:
        update_data['review_notes'] = metadata['review_notes']
    if 'review_confidence' in metadata:
        review_confidence = metadata['review_confidence']
        if review_confidence is None:
            update_data['review_confidence'] = None
        elif isinstance(review_confidence, (int, float)) and 1 <= review_confidence <= 5:
            update_data['review_confidence'] = int(review_confidence)

    # Handle authors - update both authors string and authors_detailed
    if 'authors' in metadata:
        if isinstance(metadata['authors'], list):
            # Build authors_detailed array
            authors_detailed = []
            author_names = []
            for idx, author in enumerate(metadata['authors']):
                if isinstance(author, dict):
                    author_detail = {
                        'name': author.get('name', ''),
                        'affiliation': author.get('affiliation', ''),
                        'email': author.get('email', ''),
                        'position': idx,
                        'is_corresponding': False
                    }
                    authors_detailed.append(author_detail)
                    author_names.append(author.get('name', ''))
                elif isinstance(author, str):
                    # Simple string author name
                    author_names.append(author)

            # Update both fields
            if authors_detailed:
                update_data['authors_detailed'] = authors_detailed
            update_data['authors'] = ', '.join(author_names) if author_names else ''
        elif isinstance(metadata['authors'], str):
            # Simple authors string
            update_data['authors'] = metadata['authors']

    # Add updated timestamp
    update_data['updated_at'] = datetime.now(timezone.utc)

    # Update the paper
    db.papers.update_one(
        {'_id': paper['_id']},
        {'$set': update_data}
    )

    # Return updated paper
    updated_paper = db.papers.find_one({'_id': paper['_id']})

    # Format response (similar to get_paper)
    return {
        'id': str(updated_paper['_id']),
        'title': updated_paper.get('title'),
        'abstract': updated_paper.get('abstract'),
        'authors': updated_paper.get('authors', ''),
        'authors_detailed': updated_paper.get('authors_detailed', []),  # Include detailed author info
        'publication_date': updated_paper.get('publication_date'),
        'published_date': updated_paper.get('published_date'),
        'conference': updated_paper.get('conference'),
        'journal': updated_paper.get('journal'),
        'arxiv_id': updated_paper.get('arxiv_id'),
        'doi': updated_paper.get('doi'),
        'review_deadline': updated_paper.get('review_deadline'),
        'review_decision': updated_paper.get('review_decision'),
        'review_notes': updated_paper.get('review_notes'),
        'review_confidence': updated_paper.get('review_confidence'),
        'message': 'Metadata updated successfully'
    }



def toggle_paper_flag(paper_id, flag_data):
    """Toggle the flag status of a paper"""
    paper = find_paper_by_id(paper_id)
    if not paper:
        raise NotFoundError("Paper not found")

    # Get the flag status from request
    is_flagged = flag_data.get('is_flagged', False)
    flag_notes = flag_data.get('flag_notes', '')

    # Update the paper
    update_data = {
        'is_flagged': is_flagged,
        'flag_notes': flag_notes if is_flagged else '',
        'updated_at': datetime.now(timezone.utc)
    }

    db.papers.update_one(
        {'_id': paper['_id']},
        {'$set': update_data}
    )

    return {
        'id': str(paper['_id']),
        'is_flagged': is_flagged,
        'flag_notes': flag_notes if is_flagged else '',
        'message': f"Paper {'flagged' if is_flagged else 'unflagged'} successfully"
    }



def set_paper_rating(paper_id, rating):
    """Set user rating for a paper (1-5 stars, 0 to clear rating)"""
    paper = find_paper_by_id(paper_id)
    if not paper:
        raise NotFoundError("Paper not found")

    if rating == 0:
        # Clear rating
        db.papers.update_one(
            {'_id': paper['_id']},
            {'$unset': {'user_rating': ''}, '$set': {'updated_at': datetime.now(timezone.utc)}}
        )
        return {
            'id': str(paper['_id']),
            'user_rating': None,
            'message': 'Rating cleared successfully'
        }
    else:
        # Set rating
        db.papers.update_one(
            {'_id': paper['_id']},
            {'$set': {'user_rating': rating, 'updated_at': datetime.now(timezone.utc)}}
        )
        return {
            'id': str(paper['_id']),
            'user_rating': rating,
            'message': f'Rating set to {rating} stars'
        }



def patch_paper_fields(paper_id, updates):
    """
    Patch specific paper fields including import_url and import_source
    """
    try:
        # Try to convert to ObjectId if it's a valid format
        if len(paper_id) == 24:
            paper = db.papers.find_one({'_id': ObjectId(paper_id)})
        else:
            # Try old SQLite ID
            paper = db.papers.find_one({'old_sqlite_id': int(paper_id)})
    except Exception:
        paper = None

    if not paper:
        raise NotFoundError("Paper not found")

    # Prepare update data - only update fields that are provided
    update_data = {}

    # Handle import-related fields
    if 'import_url' in updates:
        update_data['import_url'] = updates['import_url']

    if 'import_source' in updates:
        update_data['import_source'] = updates['import_source']

    # Add timestamp for tracking
    update_data['updated_at'] = datetime.now(timezone.utc)

    # Update the paper
    if update_data:
        db.papers.update_one(
            {'_id': paper['_id']},
            {'$set': update_data}
        )

        return {
            "success": True,
            "message": "Paper updated successfully",
            "updated_fields": list(update_data.keys())
        }

    return {
        "success": False,
        "message": "No fields to update"
    }

