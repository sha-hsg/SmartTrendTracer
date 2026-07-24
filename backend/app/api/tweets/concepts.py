"""
Tweet concept/tag management endpoints.
Routes: POST /{tweet_id}/concepts, DELETE /{tweet_id}/concepts/{concept_id}
"""

from fastapi import APIRouter, HTTPException, Query

from .utils import logger, db, concept_service

router = APIRouter()


@router.post("/{tweet_id}/concepts")
def add_concept_to_tweet(
    tweet_id: str,
    text: str = Query(..., description="Text to create/find concept from")
):
    """Add a concept to a tweet (creates concept if needed)"""

    # Check if tweet exists
    tweet = db.tweets.find_one({'_id': tweet_id})
    if not tweet:
        raise HTTPException(status_code=404, detail="Tweet not found")

    # Add concept using the service
    success, concept_id = concept_service.add_tag('tweet', tweet_id, text)

    if not success:
        raise HTTPException(status_code=400, detail="Failed to add concept")

    # Update tweet's concept_ids in MongoDB
    db.tweets.update_one(
        {'_id': tweet_id},
        {'$addToSet': {'concept_ids': concept_id}}
    )

    # Get concept details
    concept = concept_service.get_concept_by_id(concept_id)

    return {
        "message": "Concept added successfully",
        "concept": {
            "concept_id": concept_id,
            "id": concept.get('id'),
            "slug": concept.get('slug'),
            "display_name": concept.get('display_name')
        }
    }

@router.delete("/{tweet_id}/concepts/{concept_id}")
def remove_concept_from_tweet(tweet_id: str, concept_id: str):
    """Remove a concept from a tweet"""

    # Remove from concept service
    success = concept_service.remove_tag('tweet', tweet_id, concept_id)

    if not success:
        raise HTTPException(status_code=404, detail="Concept not found on this tweet")

    # Update tweet's concept_ids in MongoDB
    db.tweets.update_one(
        {'_id': tweet_id},
        {'$pull': {'concept_ids': concept_id}}
    )

    return {"message": "Concept removed successfully"}
