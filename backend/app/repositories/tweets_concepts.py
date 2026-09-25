"""
Data access for app.api.tweets.concepts (extracted by the arch-audit refactor).

Tweet concept/tag management endpoints.
Routes: POST /{tweet_id}/concepts, DELETE /{tweet_id}/concepts/{concept_id}
"""
from app.repositories.concepts import ConceptOnlyTagService
from app.repositories.errors import InvalidInputError, NotFoundError

concept_service = ConceptOnlyTagService()

from app.database.mongodb import get_database

db = get_database()




def add_concept_to_tweet(tweet_id, text):
    """Add a concept to a tweet (creates concept if needed)"""

    # Check if tweet exists
    tweet = db.tweets.find_one({'_id': tweet_id})
    if not tweet:
        raise NotFoundError("Tweet not found")

    # Add concept using the service
    success, concept_id = concept_service.add_tag('tweet', tweet_id, text)

    if not success:
        raise InvalidInputError("Failed to add concept")

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



def remove_concept_from_tweet(tweet_id, concept_id):
    """Remove a concept from a tweet"""

    # Remove from concept service
    success = concept_service.remove_tag('tweet', tweet_id, concept_id)

    if not success:
        raise NotFoundError("Concept not found on this tweet")

    # Update tweet's concept_ids in MongoDB
    db.tweets.update_one(
        {'_id': tweet_id},
        {'$pull': {'concept_ids': concept_id}}
    )

    return {"message": "Concept removed successfully"}

