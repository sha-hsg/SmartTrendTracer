"""
Bulk operations endpoints for paper entities.

Split from entities.py.
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from datetime import datetime, timezone

from .utils import db, concept_service, logger, find_paper_by_id
from app.repositories import papers_bulk_ops_queries as queries

router = APIRouter()


@router.post("/{paper_id}/entities/bulk-action")
def bulk_action_entities(paper_id: str, action_data: Dict[str, Any]) -> Dict[str, Any]:
    """Perform bulk actions on entities (accept_all or reject_all)"""
    try:
        entity_ids = action_data.get('entity_ids', [])
        action = action_data.get('action', 'accept_all')
        entities = action_data.get('entities', [])

        if not entity_ids:
            raise HTTPException(status_code=400, detail="No entity IDs provided")

        paper = find_paper_by_id(paper_id)
        if not paper:
            raise HTTPException(status_code=404, detail="Paper not found")

        processed_entities = []

        if action == 'accept_all':
            # Save accepted entities to the concept hierarchy AND tag the paper.
            # Parent resolution is delegated to EntityExtractionService, which
            # maps entity types to existing parent concepts and falls back to
            # the 'named-entities' concept. (The previously used hardcoded
            # 'c_et_*' parent IDs do not exist in tag_concepts_v2 — verified
            # against the live database.)
            from app.services.entity_extraction_service import (
                EntityExtraction,
                EntityExtractionService,
            )
            entity_service = EntityExtractionService(use_fast_model=True)

            for entity in entities:
                entity_name = entity.get('text', '')
                entity_type = entity.get('type', '')

                if not entity_name or not entity_type:
                    continue

                try:
                    concept_id = None

                    # Save to ontology under the proper entity-type parent
                    parent_type = entity_service._get_parent_type_for_entity(entity_type)
                    if parent_type:
                        extraction = EntityExtraction(
                            text=entity_name,
                            entity_type=entity_type,
                            confidence=float(entity.get('confidence', 0.8) or 0.8),
                            context=entity.get('context', '') or '',
                        )
                        concept = entity_service.save_entity_to_ontology(
                            None, extraction, parent_type, user="system"
                        )
                        if concept:
                            concept_id = str(concept.get('_id') or concept.get('id'))

                    # Actually tag the paper (creates/finds concept as needed)
                    success, tagged_concept_id = concept_service.add_tag(
                        content_type='paper',
                        content_id=str(paper['_id']),
                        text=entity_name,
                        preserve_display_name=True
                    )
                    if success and tagged_concept_id:
                        concept_id = str(tagged_concept_id)
                        queries.papers_update_one__bulk_action_entities_2(paper, tagged_concept_id)

                    processed_entities.append({
                        'entity_name': entity_name,
                        'entity_type': entity_type,
                        'concept_id': concept_id,
                        'tagged': bool(success),
                        'status': 'accepted'
                    })

                except Exception as e:
                    processed_entities.append({
                        'entity_name': entity_name,
                        'entity_type': entity_type,
                        'error': str(e),
                        'status': 'failed'
                    })

        elif action == 'reject_all':
            # Persist rejected entities on the paper so rejections survive
            # (used for review bookkeeping / future extraction improvement).
            rejected_items = []
            if entities:
                for entity in entities:
                    rejected_items.append({
                        'entity_id': entity.get('id', ''),
                        'text': entity.get('text', ''),
                        'type': entity.get('type', '')
                    })
                    processed_entities.append({
                        'entity_name': entity.get('text', ''),
                        'entity_type': entity.get('type', ''),
                        'status': 'rejected'
                    })
            else:
                # Frontend bulkReject sends only entity_ids
                for entity_id in entity_ids:
                    rejected_items.append({'entity_id': entity_id})
                    processed_entities.append({
                        'entity_id': entity_id,
                        'status': 'rejected'
                    })

            queries.papers_update_one__bulk_action_entities(paper, rejected_items)

        return {
            "message": f"Bulk {action} completed",
            "processed_count": len(processed_entities),
            "successful": len([e for e in processed_entities if e.get('status') in ['accepted', 'rejected']]),
            "failed": len([e for e in processed_entities if e.get('status') == 'failed']),
            "entities": processed_entities
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error performing bulk action on entities for paper {paper_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
