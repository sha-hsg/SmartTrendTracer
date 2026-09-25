"""
Data access for app.api.concepts_suggestions_mongodb (extracted by the arch-audit refactor).

Concept-aware suggestion API for tweets (MongoDB version).
Generates suggestions with proper concept structure (display_name, slug).
"""
from app.repositories.concepts import ConceptOnlyTagService
from app.repositories.errors import NotFoundError
from bson import ObjectId
import logging

concept_service = ConceptOnlyTagService()

from app.database.mongodb import get_database

db = get_database()

logger = logging.getLogger(__name__)




def apply_concepts_to_tweet(tweet_id, concepts):
    """
    Apply selected concepts to a tweet.
    Expects array of objects with display_name and slug.
    """
    # Verify tweet exists
    tweet = db.tweets.find_one({"_id": tweet_id})
    if not tweet:
        raise NotFoundError("Tweet not found")
    
    success_count = 0
    fail_count = 0
    
    for concept_data in concepts:
        try:
            # Add tag using the concept service
            # The service will find or create the concept as needed
            success, concept_id = concept_service.add_tag(
                content_type='tweet',
                content_id=tweet_id,
                text=concept_data['display_name'],
                preserve_display_name=True  # Preserve exact display name
            )
            
            if success:
                success_count += 1
            else:
                fail_count += 1
                
        except Exception as e:
            logger.error(f"Error applying concept {concept_data}: {e}")
            fail_count += 1
    
    return {
        "success_count": success_count,
        "fail_count": fail_count,
        "total_applied": success_count,
        "message": f"Applied {success_count} concepts to tweet"
    }



def apply_concepts_to_reddit(post_id, concepts):
    """
    Apply selected concepts to a Reddit post.
    Expects array of objects with display_name and slug.
    """
    try:
        post = db.reddit_posts.find_one({"_id": ObjectId(post_id)})
    except Exception:
        post = db.reddit_posts.find_one({"_id": post_id})

    if not post:
        raise NotFoundError("Reddit post not found")

    success_count = 0
    fail_count = 0

    for concept_data in concepts:
        try:
            success, concept_id = concept_service.add_tag(
                content_type='reddit',
                content_id=str(post['_id']),
                text=concept_data['display_name'],
                preserve_display_name=True
            )
            if success:
                success_count += 1
            else:
                fail_count += 1
        except Exception as e:
            logger.error(f"Error applying concept {concept_data} to Reddit post: {e}")
            fail_count += 1

    return {
        "success_count": success_count,
        "fail_count": fail_count,
        "total_applied": success_count,
        "message": f"Applied {success_count} concepts to Reddit post"
    }

