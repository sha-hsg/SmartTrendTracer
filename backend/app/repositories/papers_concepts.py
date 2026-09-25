"""
Data access for app.api.papers.concepts (extracted by the arch-audit refactor).

Paper concept and tag route handlers.

Covers: add/remove concepts, add/remove tags (legacy endpoints).
"""
from app.repositories.concepts import ConceptOnlyTagService
from app.repositories.errors import InvalidInputError, NotFoundError
from app.repositories.papers import find_paper_by_id
import logging

concept_service = ConceptOnlyTagService()

from app.database.mongodb import get_database

db = get_database()

logger = logging.getLogger(__name__)




def apply_concepts_to_paper(paper_id, concepts):
    """Batch-apply selected concepts to a paper.
    Expects array of objects with display_name and slug."""
    paper = find_paper_by_id(paper_id)
    if not paper:
        raise NotFoundError("Paper not found")

    success_count = 0
    fail_count = 0

    for concept_data in concepts:
        try:
            text = concept_data.get('display_name', concept_data.get('tag', ''))
            if not text:
                fail_count += 1
                continue
            success, concept_id = concept_service.add_tag(
                content_type='paper',
                content_id=str(paper['_id']),
                text=text,
                preserve_display_name=True
            )
            if success:
                success_count += 1
                db.papers.update_one(
                    {'_id': paper['_id']},
                    {'$addToSet': {'concept_ids': concept_id}}
                )
            else:
                fail_count += 1
        except Exception as e:
            logger.error(f"Error applying concept {concept_data}: {e}")
            fail_count += 1

    return {
        "success_count": success_count,
        "fail_count": fail_count,
        "total_applied": success_count,
        "message": f"Applied {success_count} concepts to paper"
    }



def add_concept_to_paper(paper_id, text):
    """Add a concept to a paper"""
    paper = find_paper_by_id(paper_id)
    if not paper:
        raise NotFoundError("Paper not found")

    # Add concept using the service
    success, concept_id = concept_service.add_tag('paper', str(paper['_id']), text)

    if not success:
        raise InvalidInputError("Failed to add concept")

    # Update paper's concept_ids in MongoDB
    db.papers.update_one(
        {'_id': paper['_id']},
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



def remove_concept_from_paper(paper_id, concept_id):
    """Remove a concept from a paper"""
    paper = find_paper_by_id(paper_id)
    if not paper:
        raise NotFoundError("Paper not found")

    # Remove from concept service
    success = concept_service.remove_tag('paper', str(paper['_id']), concept_id)

    if not success:
        raise NotFoundError("Concept not found on this paper")

    # Update paper's concept_ids in MongoDB
    db.papers.update_one(
        {'_id': paper['_id']},
        {'$pull': {'concept_ids': concept_id}}
    )

    return {"message": "Concept removed successfully"}

