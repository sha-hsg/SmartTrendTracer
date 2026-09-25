"""
Data access for app.api.papers.analysis_management (extracted by the arch-audit refactor).

Paper analysis management routes: free-form analyses, updates, and deletions.

Handles CRUD for free-form (custom-prompt) analyses, content updates for
generated analyses, and deletion of individual or all analyses.
"""
from app.repositories.errors import InvalidInputError, NotFoundError
from app.repositories.papers import find_paper_by_id
from bson import ObjectId
from datetime import datetime
from datetime import timezone

from app.database.mongodb import get_database

db = get_database()


def _find_paper(paper_id: str):
    """Look up a paper by ObjectId or legacy SQLite id."""
    try:
        if len(paper_id) == 24:
            paper = db.papers.find_one({'_id': ObjectId(paper_id)})
        else:
            paper = db.papers.find_one({'old_sqlite_id': int(paper_id)})
    except Exception:
        paper = None
    return paper


def update_free_analysis(paper_id, analysis_id, content):
    """Update the content of a free-form analysis"""

    paper = _find_paper(paper_id)
    if not paper:
        raise NotFoundError("Paper not found")

    # Find and update the analysis
    free_analyses = paper.get('free_analyses', [])
    updated = False

    for analysis in free_analyses:
        if analysis.get('id') == analysis_id:
            analysis['content'] = content
            analysis['updated_at'] = datetime.now(timezone.utc).isoformat()
            updated = True
            break

    if not updated:
        raise NotFoundError("Analysis not found")

    # Save to database
    db.papers.update_one(
        {'_id': paper['_id']},
        {'$set': {'free_analyses': free_analyses}}
    )

    return {"success": True, "message": "Analysis updated"}



def delete_free_analysis(paper_id, analysis_id):
    """Delete a free-form analysis"""

    paper = _find_paper(paper_id)
    if not paper:
        raise NotFoundError("Paper not found")

    # Filter out the analysis to delete
    free_analyses = paper.get('free_analyses', [])
    filtered_analyses = [a for a in free_analyses if a.get('id') != analysis_id]

    if len(filtered_analyses) == len(free_analyses):
        raise NotFoundError("Analysis not found")

    # Save to database
    db.papers.update_one(
        {'_id': paper['_id']},
        {'$set': {'free_analyses': filtered_analyses}}
    )

    return {"success": True, "message": "Analysis deleted"}



def update_generated_analysis(paper_id, analysis_type, data):
    """Update the content of a generated analysis (like mollick_summary)"""

    content = data.get('content', '')

    paper = _find_paper(paper_id)
    if not paper:
        raise NotFoundError("Paper not found")

    # Get existing analyses - handle both dict and list formats
    analyses = paper.get('analyses', {})
    updated = False

    if isinstance(analyses, dict):
        # Dict format - used by the generation endpoint
        if analysis_type not in analyses:
            raise NotFoundError(f"Analysis type '{analysis_type}' not found")

        # Update the content while preserving other fields
        analyses[analysis_type]['content'] = content
        analyses[analysis_type]['updated_at'] = datetime.now(timezone.utc).isoformat()
        updated = True

    elif isinstance(analyses, list):
        # List format - handle legacy format
        for analysis in analyses:
            # Check both 'type' and 'analysis_type' fields
            if (analysis.get('type') == analysis_type or
                analysis.get('analysis_type') == analysis_type):
                analysis['content'] = content
                analysis['updated_at'] = datetime.now(timezone.utc).isoformat()
                updated = True
                break

        if not updated:
            raise NotFoundError(f"Analysis type '{analysis_type}' not found")
    else:
        raise InvalidInputError("Invalid analyses format")

    # Save to database
    db.papers.update_one(
        {'_id': paper['_id']},
        {'$set': {'analyses': analyses}}
    )

    return {"success": True, "message": f"Analysis '{analysis_type}' updated"}



def delete_all_analyses(paper_id):
    """Delete all saved analyses for a paper"""
    paper = find_paper_by_id(paper_id)
    if not paper:
        raise NotFoundError("Paper not found")

    count = len(paper.get('analyses', []))
    db.papers.update_one(
        {'_id': paper['_id']},
        {'$set': {'analyses': []}}
    )

    return {"message": f"Deleted {count} analyses", "deleted_count": count}



def delete_analysis(paper_id, analysis_type):
    """Delete a saved analysis"""

    paper = _find_paper(paper_id)
    if not paper:
        raise NotFoundError("Paper not found")

    # Remove analysis from paper atomically - check both type and analysis_type fields
    db.papers.update_one(
        {'_id': paper['_id']},
        {'$pull': {'analyses': {'$or': [
            {'type': analysis_type},
            {'analysis_type': analysis_type}
        ]}}}
    )

    return {"message": "Analysis deleted successfully"}

