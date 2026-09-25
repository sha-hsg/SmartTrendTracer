"""
Tweet concept/tag management endpoints.
Routes: POST /{tweet_id}/concepts, DELETE /{tweet_id}/concepts/{concept_id}
"""

from fastapi import APIRouter, Query

from app.repositories import tweets_concepts as repo

router = APIRouter()


@router.post("/{tweet_id}/concepts")
def add_concept_to_tweet(
    tweet_id: str,
    text: str = Query(..., description="Text to create/find concept from")
):
    """Add a concept to a tweet (creates concept if needed)"""
    return repo.add_concept_to_tweet(tweet_id=tweet_id, text=text)

@router.delete("/{tweet_id}/concepts/{concept_id}")
def remove_concept_from_tweet(tweet_id: str, concept_id: str):
    """Remove a concept from a tweet"""
    return repo.remove_concept_from_tweet(tweet_id=tweet_id, concept_id=concept_id)
