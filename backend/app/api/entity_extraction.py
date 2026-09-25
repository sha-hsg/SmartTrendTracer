"""
API endpoints for entity extraction and annotation management - MongoDB version
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Optional, Any
from pydantic import BaseModel
from datetime import datetime, timezone
from bson import ObjectId

from app.services.entity_extraction_service import EntityExtractionService, EntityExtraction
from app.database.mongodb import get_database
from app.repositories import entity_extraction_queries as queries

router = APIRouter()

class ExtractEntitiesRequest(BaseModel):
    text: Optional[str] = None
    article_id: Optional[str] = None  # Changed to str for MongoDB ObjectId
    tweet_id: Optional[str] = None
    use_fast_model: bool = False
    model: Optional[str] = None  # Allow custom model selection from UI

class EntitySuggestion(BaseModel):
    id: str
    text: str
    type: str
    confidence: float
    context: str
    normalized: str
    metadata: Dict

class EntityReviewRequest(BaseModel):
    entity_id: str
    action: str  # "accept", "reject", "modify"
    new_type: Optional[str] = None
    new_text: Optional[str] = None
    article_id: Optional[str] = None  # Optional: also tag this article on accept

class BulkEntityActionRequest(BaseModel):
    entity_ids: List[str]
    action: str  # "accept_all", "reject_all"
    article_id: Optional[str] = None  # Changed to str for MongoDB ObjectId
    entities: Optional[List[Dict]] = None  # Full entity data for processing

class EntityExtractionResponse(BaseModel):
    entities: List[EntitySuggestion]
    stats: Dict[str, Any]
    source: str
    model: str


def _normalize_concept_id(concept_id):
    """Normalize a concept _id: convert 24-hex strings to ObjectId, keep
    custom string IDs (e.g. 'c_person_x') and ObjectIds as-is."""
    if isinstance(concept_id, ObjectId):
        return concept_id
    if isinstance(concept_id, str) and ObjectId.is_valid(concept_id):
        return ObjectId(concept_id)
    return concept_id


def _find_article(db, article_id: str):
    """Look up an article by ObjectId or legacy SQLite id."""
    try:
        if len(article_id) == 24:
            return queries.articles_find_one___find_article_2(article_id)
        return queries.articles_find_one___find_article(article_id)
    except Exception:
        return None

@router.post("/extract", response_model=EntityExtractionResponse)
def extract_entities(
    request: ExtractEntitiesRequest,
):
    """
    Extract entities from text, article, or tweet - MongoDB version
    """

    # Get text based on source
    text = request.text
    source = "direct"

    if request.article_id:
        # MongoDB query for article
        article = None
        try:
            if len(request.article_id) == 24:
                article = queries.articles_find_one__extract_entities(request)
            else:
                article = queries.articles_find_one__extract_entities_2(request)
        except Exception:
            pass

        if not article:
            raise HTTPException(status_code=404, detail="Article not found")

        content = article.get('content_markdown') or article.get('content', '')
        text = f"{article.get('title', '')}\n\n{content[:5000]}"  # Limit length
        source = f"article_{request.article_id}"

    elif request.tweet_id:
        # MongoDB query for tweet (tweets store the Twitter ID as _id)
        tweet = queries.tweets_find_one__extract_entities(request)
        if not tweet:
            raise HTTPException(status_code=404, detail="Tweet not found")
        text = tweet.get('text', '')
        source = f"tweet_{request.tweet_id}"

    if not text:
        raise HTTPException(status_code=400, detail="No text provided for extraction")

    # Initialize service with custom model if specified
    service = EntityExtractionService(
        use_fast_model=request.use_fast_model,
        custom_model=request.model  # Use model from UI selection
    )

    # Extract entities
    entities = service.extract_entities(
        text=text,
        article_id=request.article_id
    )

    # Convert to response format
    entity_suggestions = [
        EntitySuggestion(
            id=entity.id,
            text=entity.text,
            type=entity.entity_type,
            confidence=entity.confidence,
            context=entity.context,
            normalized=entity.normalized,
            metadata=entity.metadata
        )
        for entity in entities
    ]

    # Calculate statistics
    stats = {
        "total": len(entities),
        "by_type": {},
        "avg_confidence": sum(e.confidence for e in entities) / len(entities) if entities else 0
    }

    for entity in entities:
        if entity.entity_type not in stats["by_type"]:
            stats["by_type"][entity.entity_type] = 0
        stats["by_type"][entity.entity_type] += 1

    return EntityExtractionResponse(
        entities=entity_suggestions,
        stats=stats,
        source=source,
        model=service.model_name
    )

@router.post("/review")
def review_entity(
    request: EntityReviewRequest,
    user: str = Query(default="user")
):
    """
    Review and accept/reject/modify an entity suggestion - MongoDB version
    """
    db = get_database()

    if request.action not in ("accept", "reject", "modify"):
        raise HTTPException(status_code=400, detail=f"Invalid action: {request.action}")

    # Persist every review decision
    review_doc = {
        'entity_id': request.entity_id,
        'action': request.action,
        'entity_text': request.new_text,
        'entity_type': request.new_type,
        'article_id': request.article_id,
        'reviewed_by': user,
        'reviewed_at': datetime.now(timezone.utc)
    }

    if request.action == "accept":
        # Use the entity data sent by the frontend (EntityAnnotationReviewModern
        # always sends new_text/new_type on accept)
        if not request.new_text or not request.new_type:
            raise HTTPException(
                status_code=400,
                detail="new_text and new_type are required to accept an entity"
            )

        entity = EntityExtraction(
            text=request.new_text,
            entity_type=request.new_type,
            confidence=1.0,
            context="Accepted by user review"
        )

        service = EntityExtractionService()

        # Save entity to ontology (this returns a concept from MongoDB)
        concept = service.save_entity_to_ontology(db, entity, request.new_type, user)

        if not concept:
            review_doc['status'] = 'failed'
            queries.entity_reviews_insert_one__review_entity_3(review_doc)
            return {
                "status": "failed",
                "entity_id": request.entity_id,
                "message": "Failed to save entity to ontology"
            }

        concept_id = _normalize_concept_id(concept.get('_id'))
        review_doc['concept_id'] = concept_id

        # Optionally tag the article (same mechanism as bulk-action)
        if request.article_id:
            article = _find_article(db, request.article_id)
            if article:
                existing_instance = queries.tag_instances_find_one__review_entity(concept_id, article)
                if not existing_instance:
                    queries.tag_instances_insert_one__review_entity(concept_id, user, article, concept, request)

        review_doc['status'] = 'accepted'
        queries.entity_reviews_insert_one__review_entity_2(review_doc)
        return {
            "status": "accepted",
            "entity_id": request.entity_id,
            "concept_id": str(concept_id),
            "message": f"Entity saved to ontology under {request.new_type}"
        }

    # reject / modify: persist the decision only
    queries.entity_reviews_insert_one__review_entity(review_doc)

    if request.action == "reject":
        return {
            "status": "rejected",
            "entity_id": request.entity_id,
            "message": "Entity suggestion rejected"
        }

    return {
        "status": "modified",
        "entity_id": request.entity_id,
        "new_type": request.new_type,
        "new_text": request.new_text,
        "message": "Entity suggestion modified"
    }

@router.post("/bulk-action")
def bulk_entity_action(
    request: BulkEntityActionRequest,
    user: str = Query(default="user")
):
    """
    Apply bulk actions to multiple entity suggestions - MongoDB version
    """
    db = get_database()

    results = {
        "total": len(request.entity_ids),
        "processed": 0,
        "failed": 0,
        "action": request.action
    }

    if request.action == "accept_all":
        # Process each entity and save to ontology
        service = EntityExtractionService()
        processed_count = 0
        failed_count = 0

        # Use article_id from request if provided
        article_id = request.article_id
        article_object_id = None

        # Get article if ID provided
        if article_id:
            try:
                if len(article_id) == 24:
                    article_object_id = ObjectId(article_id)
                    article = queries.articles_find_one__bulk_entity_action(article_object_id)
                else:
                    article = queries.articles_find_one__bulk_entity_action_2(article_id)
                    if article:
                        article_object_id = article['_id']
            except Exception:
                article = None

            if not article:
                return {
                    **results,
                    "message": f"Article {article_id} not found"
                }

        # If entities data is provided, use it
        if request.entities:
            # Process full entity data
            for entity_data in request.entities:
                try:
                    # Extract entity details
                    entity_text = entity_data.get('text', '')
                    entity_type = entity_data.get('type', '')
                    confidence = entity_data.get('confidence', 0.9)
                    context = entity_data.get('context', '')

                    # Create entity object
                    entity = EntityExtraction(
                        text=entity_text,
                        entity_type=entity_type,
                        confidence=confidence,
                        context=context
                    )

                    # Save entity to ontology as a tag concept
                    concept = service.save_entity_to_ontology(db, entity, entity_type, user)
                    print(f"Created concept: {concept.get('display_name') if concept else 'None'} for entity: {entity_text}")

                    if concept and article_object_id:
                        # Add as tag to the article using tag_instances collection
                        concept_id = _normalize_concept_id(concept.get('_id'))
                        display_name = concept.get('display_name', entity_text)
                        slug = concept.get('slug', entity_text.lower().replace(' ', '-'))

                        # Check if tag instance already exists (case-insensitive)
                        # Use content_type/content_id to match faceted-search queries
                        existing_instance = queries.tag_instances_find_one__bulk_entity_action(concept_id, article_object_id)

                        if not existing_instance:
                            # Create new tag instance with correct field names
                            tag_instance = {
                                'concept_id': concept_id,
                                'content_type': 'article',  # Matches faceted-search query
                                'content_id': str(article_object_id),  # Matches faceted-search query
                                'tag_slug': slug,
                                'display_name': display_name,
                                'tag_type': 'entity',  # Mark as entity-extracted tag
                                'created_at': datetime.now(timezone.utc),
                                'created_by': user
                            }
                            queries.tag_instances_insert_one__bulk_entity_action(tag_instance)
                            print(f"Added tag '{display_name}' to article {article_id}")
                            processed_count += 1
                        else:
                            print(f"Tag '{display_name}' already exists on article {article_id}")
                            processed_count += 1  # Already exists, count as processed
                    else:
                        # Just save to ontology without article association
                        if concept:
                            processed_count += 1
                        else:
                            failed_count += 1
                except Exception as e:
                    print(f"Error processing entity: {str(e)}")
                    import traceback
                    traceback.print_exc()
                    failed_count += 1
        else:
            # Without full entity data we cannot create concepts/tags
            raise HTTPException(
                status_code=400,
                detail="entities data is required for accept_all"
            )

        results["processed"] = processed_count
        results["failed"] = failed_count
        results["message"] = f"Accepted {processed_count} entities, {failed_count} failed"

    elif request.action == "reject_all":
        results["processed"] = len(request.entity_ids)
        results["message"] = f"Rejected {len(request.entity_ids)} entities"

    else:
        raise HTTPException(status_code=400, detail=f"Invalid bulk action: {request.action}")

    return results

@router.get("/schema")
def get_entity_schema():
    """
    Get the current entity type schema from top_level.json
    """
    import json
    import os

    # Get the correct path to top_level.json
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    schema_path = os.path.join(base_dir, 'top_level.json')

    try:
        with open(schema_path, 'r') as f:
            schema = json.load(f)

        return {
            "version": schema.get("version"),
            "entity_types": schema.get("entity_types"),
            "extraction_config": schema.get("extraction_config")
        }
    except FileNotFoundError:
        return {
            "version": "1.0",
            "entity_types": [],
            "extraction_config": {}
        }
