"""
Entity extraction endpoints for papers.

Split from papers_mongodb.py.
Tag suggestion endpoints moved to tag_suggestions.py.
Legacy duplicates of the /api/entities routes (schema, text extract, review)
and the superseded /{paper_id}/extract-entities endpoint were removed.
"""

from fastapi import APIRouter, HTTPException
from typing import Optional, Dict, Any
from bson import ObjectId

from .utils import db, logger

router = APIRouter()


@router.post("/{paper_id}/entities/extract")
def extract_paper_entities(paper_id: str, use_fast_model: bool = False, model_choice: Optional[str] = None) -> Dict[str, Any]:
    """Extract entities from paper content using AI"""
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
        raise HTTPException(status_code=404, detail="Paper not found")

    # Get content from paper - try content field first, then sections
    content_text = paper.get('content', '')

    # If no content, try to extract from sections
    if not content_text and paper.get('sections'):
        sections_content = []
        for section in paper['sections']:
            if section.get('content'):
                sections_content.append(f"## {section.get('title', 'Section')}\n{section['content']}")
        content_text = '\n\n'.join(sections_content)

    if not content_text:
        raise HTTPException(status_code=400, detail="Paper has no content to analyze")

    import logging
    logger = logging.getLogger(__name__)

    try:
        from app.services.entity_extraction_service import EntityExtractionService

        # Initialize service with model choice (default to 'auto' if not specified)
        service = EntityExtractionService(use_fast_model=use_fast_model, model_choice=model_choice or 'auto')

        # Prepare full paper content for analysis
        paper_text = f"""
Title: {paper.get('title', 'Unknown')}

Abstract: {paper.get('abstract', 'No abstract available')}

Authors: {paper.get('authors', 'Unknown')}

Full Paper Content:
{content_text}
"""

        logger.info(f"Extracting entities from paper {paper_id} with {len(paper_text)} characters")

        # Extract entities using full paper content
        entities = service.extract_entities(text=paper_text, article_id=None)

        # Convert to response format
        entity_suggestions = [
            {
                "id": entity.id,
                "text": entity.text,
                "type": entity.entity_type,
                "confidence": entity.confidence,
                "context": entity.context,
                "normalized": entity.normalized,
                "metadata": entity.metadata
            }
            for entity in entities
        ]

        # Calculate statistics
        stats = {
            "total_entities": len(entities),
            "entity_types": {},
            "confidence_distribution": {
                "high": 0,
                "medium": 0,
                "low": 0
            }
        }

        for entity in entities:
            # Count by type
            if entity.entity_type not in stats["entity_types"]:
                stats["entity_types"][entity.entity_type] = 0
            stats["entity_types"][entity.entity_type] += 1

            # Count by confidence level
            if entity.confidence >= 0.8:
                stats["confidence_distribution"]["high"] += 1
            elif entity.confidence >= 0.6:
                stats["confidence_distribution"]["medium"] += 1
            else:
                stats["confidence_distribution"]["low"] += 1

        return {
            "entities": entity_suggestions,
            "stats": stats,
            "model": service.model_name,
            "paper_title": paper.get('title', f'Paper {paper_id}'),
            "paper_id": paper_id
        }

    except Exception as e:
        logger.error(f"Error extracting entities from paper {paper_id}: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))
