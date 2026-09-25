"""
Data access for app.api.papers.content (extracted by the arch-audit refactor).

Paper content route handlers.

Covers: snippets, sections, references, TEI XML, PDF serving,
and LLM-based section extraction.

Image serving is in content_media.py.
"""
from app.repositories.errors import NotFoundError
from bson import ObjectId
from datetime import datetime
from datetime import timezone

from app.database.mongodb import get_database

db = get_database()




def get_paper_snippets(paper_id):
    """Get paper snippets from MongoDB"""

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

    # Return snippets (if stored in MongoDB) with ObjectId conversion for safety
    snippets = paper.get('snippets', [])

    # Convert any ObjectIds to strings in snippets
    for snippet in snippets:
        if isinstance(snippet, dict):
            for key, value in snippet.items():
                if isinstance(value, ObjectId):
                    snippet[key] = str(value)

    return snippets



def add_paper_snippet(paper_id, snippet):
    """Add a snippet to a paper (analog to the article snippet endpoint)"""

    try:
        if len(paper_id) == 24:
            paper = db.papers.find_one({'_id': ObjectId(paper_id)})
        else:
            paper = db.papers.find_one({'old_sqlite_id': int(paper_id)})
    except Exception:
        paper = None

    if not paper:
        raise NotFoundError("Paper not found")

    # Create snippet document matching the structure the GET endpoint returns
    # and the frontend expects (usePaperActions.ts: content/annotation/category/page_number)
    new_snippet = {
        'id': str(ObjectId()),
        'content': snippet.get('content', ''),
        'annotation': snippet.get('annotation', ''),
        'category': snippet.get('category', ''),
        'page_number': snippet.get('page_number'),
        'created_at': datetime.now(timezone.utc).isoformat()
    }

    db.papers.update_one(
        {'_id': paper['_id']},
        {'$push': {'snippets': new_snippet}}
    )

    # Frontend appends the response body directly to its snippet list
    return new_snippet



def remove_paper_snippet(paper_id, snippet_id):
    """Remove a snippet from a paper"""

    try:
        if len(paper_id) == 24:
            paper = db.papers.find_one({'_id': ObjectId(paper_id)})
        else:
            paper = db.papers.find_one({'old_sqlite_id': int(paper_id)})
    except Exception:
        paper = None

    if not paper:
        raise NotFoundError("Paper not found")

    db.papers.update_one(
        {'_id': paper['_id']},
        {'$pull': {'snippets': {'id': snippet_id}}}
    )

    return {"message": "Snippet removed successfully"}



def get_paper_sections(paper_id):
    """Get paper sections from MongoDB"""

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

    # Return sections with ObjectId conversion for safety
    sections = paper.get('sections', [])

    # Convert any ObjectIds to strings in sections
    for section in sections:
        if isinstance(section, dict):
            for key, value in section.items():
                if isinstance(value, ObjectId):
                    section[key] = str(value)

    return sections



def update_paper_section(paper_id, section_id, request):
    """Update a paper section's title or content"""

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

    sections = paper.get('sections', [])
    section_found = False

    # Update the specific section
    for i, section in enumerate(sections):
        if section.get('id') == section_id:
            if 'title' in request:
                # Clean up the title - remove leading numbers
                import re
                clean_title = re.sub(r'^\d+\.?\s*', '', request['title'])
                sections[i]['title'] = clean_title
            if 'content' in request:
                sections[i]['content'] = request['content']
            section_found = True
            break

    if not section_found:
        raise NotFoundError("Section not found")

    # Update the paper with the modified sections
    db.papers.update_one(
        {'_id': paper['_id']},
        {'$set': {'sections': sections}}
    )

    return {"success": True, "message": "Section updated successfully"}



def get_paper_references(paper_id):
    """Get extracted references for a paper from MongoDB"""

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

    references = paper.get('references', [])

    # Convert any ObjectIds to strings in references for safety
    for ref in references:
        if isinstance(ref, dict):
            for key, value in ref.items():
                if isinstance(value, ObjectId):
                    ref[key] = str(value)

    return {
        'paper_id': paper_id,
        'paper_title': paper.get('title', ''),
        'total_references': len(references),
        'references': references
    }

