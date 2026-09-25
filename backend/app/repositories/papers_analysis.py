"""
Data access for app.api.papers.analysis (extracted by the arch-audit refactor).

Paper analysis routes: generate, retrieve, update, and delete LLM-powered analyses.

Includes structured (prompt-config-driven) analysis endpoints.
"""
from app.repositories.errors import NotFoundError
from bson import ObjectId

from app.database.mongodb import get_database

db = get_database()




def get_saved_analyses(paper_id):
    """Get saved analyses for a paper from MongoDB"""

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

    # Get analyses from the paper document
    analyses = paper.get('analyses', [])

    # Convert array to object keyed by analysis type (frontend expects this format)
    analyses_dict = {}
    for analysis in analyses:
        # Get the analysis type (handle both field names)
        analysis_type = analysis.get('type') or analysis.get('analysis_type')
        if not analysis_type:
            continue

        # Format the analysis for frontend
        analyses_dict[analysis_type] = {
            "success": True,
            "content": analysis.get('content', ''),
            "model": analysis.get('model_used') or analysis.get('model', 'gpt-4o-mini'),
            "created_at": analysis.get('created_at') or analysis.get('generated_at'),
            "metadata": {
                "word_count": analysis.get('word_count'),
                "confidence_score": analysis.get('confidence_score'),
                "version": analysis.get('version')
            }
        }

    return {"analyses": analyses_dict}

