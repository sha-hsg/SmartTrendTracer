"""
Concept-aware suggestion API for tweets (MongoDB version).
Generates suggestions with proper concept structure (display_name, slug).
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Optional
from pydantic import BaseModel
import json
import logging
from app.database.mongodb import get_database
from bson import ObjectId

from app.services.concept_only_tag_service import ConceptOnlyTagService
from app.services.llm_manager import get_llm_manager
from app.repositories import concepts_suggestions as repo

logger = logging.getLogger(__name__)
router = APIRouter()

# MongoDB connection
db = get_database()

# Initialize services
concept_service = ConceptOnlyTagService()
llm_manager = get_llm_manager()

class ConceptSuggestionRequest(BaseModel):
    """Request model for concept suggestions"""
    model: Optional[str] = None  # Allow specifying model from frontend

@router.post("/tweets/{tweet_id}/suggest")
async def suggest_concepts_for_tweet(tweet_id: str, request: ConceptSuggestionRequest = ConceptSuggestionRequest()):
    """
    Get AI-suggested concepts for a specific tweet.
    Returns proper concept structures with display_name and slug.
    """
    
    # Get the tweet from MongoDB
    tweet = db.tweets.find_one({"_id": tweet_id})
    if not tweet:
        raise HTTPException(status_code=404, detail="Tweet not found")
    
    # Get existing concepts on this tweet
    existing_concepts = concept_service.get_tags_for_content('tweet', tweet_id)
    existing_concept_ids = [c['concept_id'] for c in existing_concepts]
    existing_slugs = [c['slug'] for c in existing_concepts]
    
    # 1. Find similar existing concepts from the database
    similar_concepts = []
    all_concepts = concept_service.get_all_concepts_with_counts(content_type='tweet')
    
    # Simple text matching for now (could be enhanced with embeddings)
    tweet_text_lower = tweet['text'].lower()
    for concept in all_concepts[:50]:  # Check top 50 concepts
        if concept['concept_id'] not in existing_concept_ids:
            # Check if concept name appears in tweet
            if concept['slug'].replace('_', ' ') in tweet_text_lower or \
               concept['display_name'].lower() in tweet_text_lower:
                similar_concepts.append({
                    "concept_id": concept['concept_id'],
                    "display_name": concept['display_name'],
                    "slug": concept['slug'],
                    "entity_type": concept.get('entity_type', 'topic'),
                    "usage_count": concept.get('count', 0),
                    "type": "existing"
                })
    
    # 2. Generate new concept suggestions using LLM
    new_concepts = []
    actual_model = "unknown"  # Will be set to actual model used or "error" on exception
    try:
        # Prepare prompt for LLM
        prompt = f"""Analyze this tweet and suggest relevant concept tags.

Tweet: {tweet['text']}

Instructions:
1. Suggest 3-5 relevant concepts for this tweet
2. Focus on main topics, technologies, people, organizations mentioned
3. Use snake_case for slugs (e.g., machine_learning, sam_altman)
4. Use proper capitalization for display names (e.g., "Machine Learning", "Sam Altman")
5. Avoid concepts already tagged: {', '.join(existing_slugs)}

Return as JSON array with format:
[
  {{
    "display_name": "Proper Name",
    "slug": "snake_case_slug",
    "entity_type": "topic|person|organisation|location|event|product"
  }}
]
"""
        
        # Resolve deprecated model aliases centrally (MODEL_MIGRATION_MAP);
        # without an explicit model the tag_suggestion task route decides.
        selected_model = request.model
        actual_model = (
            llm_manager.MODEL_MIGRATION_MAP.get(selected_model, selected_model)
            if selected_model else None
        )

        logger.info(f"Concept suggestion using LLMManager with tag_suggestion task type and model: {actual_model}")

        # Convert to OpenAI message format
        messages = [
            {"role": "user", "content": prompt}
        ]

        # Call LLM Manager async with tag_suggestion task type and selected model
        llm_response = await llm_manager.completion(
            task_type='tag_suggestion',
            messages=messages,
            user_id='default',
            override_params={'model': actual_model} if actual_model else None
        )

        response = llm_response.choices[0].message.content

        # Get the actual model used from the response
        actual_model = llm_response.model

        # Parse JSON response
        if response:
            try:
                # Extract JSON from response (handle markdown code blocks)
                json_text = response.strip()
                if json_text.startswith("```json"):
                    json_text = json_text[7:]
                if json_text.startswith("```"):
                    json_text = json_text[3:]
                if json_text.endswith("```"):
                    json_text = json_text[:-3]

                suggested = json.loads(json_text.strip())

                # Filter out existing concepts and format
                for concept in suggested:
                    if concept['slug'] not in existing_slugs:
                        new_concepts.append({
                            "display_name": concept['display_name'],
                            "slug": concept['slug'],
                            "entity_type": concept.get('entity_type', 'topic'),
                            "type": "new"
                        })
            except (json.JSONDecodeError, KeyError) as e:
                logger.error(f"Error parsing LLM response: {e}")
                logger.debug(f"Raw response: {response}")
    except Exception as e:
        logger.error(f"Error generating concept suggestions: {e}")
        actual_model = "error"

    return {
        "tweet_id": tweet_id,
        "existing_suggestions": similar_concepts[:5],  # Limit to 5
        "new_suggestions": new_concepts[:5],  # Limit to 5
        "already_tagged": existing_concepts,
        "total_suggestions": len(similar_concepts) + len(new_concepts),
        "model_used": actual_model
    }

@router.post("/tweets/{tweet_id}/apply-concepts")
async def apply_concepts_to_tweet(tweet_id: str, concepts: List[Dict[str, str]]):
    """
    Apply selected concepts to a tweet.
    Expects array of objects with display_name and slug.
    """
    return repo.apply_concepts_to_tweet(tweet_id=tweet_id, concepts=concepts)

@router.post("/reddit/{post_id}/suggest")
async def suggest_concepts_for_reddit(post_id: str, request: ConceptSuggestionRequest = ConceptSuggestionRequest()):
    """
    Get AI-suggested concepts for a specific Reddit post.
    Returns proper concept structures with display_name and slug.
    """
    # Get the Reddit post from MongoDB
    try:
        post = db.reddit_posts.find_one({"_id": ObjectId(post_id)})
    except Exception:
        post = db.reddit_posts.find_one({"_id": post_id})

    if not post:
        raise HTTPException(status_code=404, detail="Reddit post not found")

    # Get existing concepts on this post
    existing_concepts = concept_service.get_tags_for_content('reddit', str(post['_id']))
    existing_concept_ids = [c['concept_id'] for c in existing_concepts]
    existing_slugs = [c['slug'] for c in existing_concepts]

    # 1. Find similar existing concepts from the database
    similar_concepts = []
    all_concepts = concept_service.get_all_concepts_with_counts(content_type='reddit')

    post_text = f"{post.get('title', '')} {post.get('selftext', '')}".lower()
    for concept in all_concepts[:50]:
        if concept['concept_id'] not in existing_concept_ids:
            if concept['slug'].replace('_', ' ') in post_text or \
               concept['display_name'].lower() in post_text:
                similar_concepts.append({
                    "concept_id": concept['concept_id'],
                    "display_name": concept['display_name'],
                    "slug": concept['slug'],
                    "entity_type": concept.get('entity_type', 'topic'),
                    "usage_count": concept.get('count', 0),
                    "type": "existing"
                })

    # 2. Generate new concept suggestions using LLM
    new_concepts = []
    actual_model = "unknown"
    try:
        content_text = post.get('title', '')
        if post.get('selftext'):
            content_text += f"\n\n{post['selftext']}"

        prompt = f"""Analyze this Reddit post and suggest relevant concept tags.

Reddit Post (r/{post.get('subreddit', 'unknown')}): {content_text}

Instructions:
1. Suggest 3-5 relevant concepts for this post
2. Focus on main topics, technologies, people, organizations mentioned
3. Use snake_case for slugs (e.g., machine_learning, sam_altman)
4. Use proper capitalization for display names (e.g., "Machine Learning", "Sam Altman")
5. Avoid concepts already tagged: {', '.join(existing_slugs)}

Return as JSON array with format:
[
  {{
    "display_name": "Proper Name",
    "slug": "snake_case_slug",
    "entity_type": "topic|person|organisation|location|event|product"
  }}
]
"""
        # Resolve deprecated model aliases centrally (MODEL_MIGRATION_MAP);
        # without an explicit model the tag_suggestion task route decides.
        selected_model = request.model
        actual_model = (
            llm_manager.MODEL_MIGRATION_MAP.get(selected_model, selected_model)
            if selected_model else None
        )

        logger.info(f"Reddit concept suggestion using LLMManager with model: {actual_model}")

        messages = [{"role": "user", "content": prompt}]
        llm_response = await llm_manager.completion(
            task_type='tag_suggestion',
            messages=messages,
            user_id='default',
            override_params={'model': actual_model} if actual_model else None
        )

        response = llm_response.choices[0].message.content
        actual_model = llm_response.model

        if response:
            try:
                json_text = response.strip()
                if json_text.startswith("```json"):
                    json_text = json_text[7:]
                if json_text.startswith("```"):
                    json_text = json_text[3:]
                if json_text.endswith("```"):
                    json_text = json_text[:-3]

                suggested = json.loads(json_text.strip())
                for concept in suggested:
                    if concept['slug'] not in existing_slugs:
                        new_concepts.append({
                            "display_name": concept['display_name'],
                            "slug": concept['slug'],
                            "entity_type": concept.get('entity_type', 'topic'),
                            "type": "new"
                        })
            except (json.JSONDecodeError, KeyError) as e:
                logger.error(f"Error parsing LLM response for Reddit: {e}")
    except Exception as e:
        logger.error(f"Error generating Reddit concept suggestions: {e}")
        actual_model = "error"

    return {
        "tweet_id": str(post['_id']),  # Keep field name for frontend compatibility
        "existing_suggestions": similar_concepts[:5],
        "new_suggestions": new_concepts[:5],
        "already_tagged": existing_concepts,
        "total_suggestions": len(similar_concepts) + len(new_concepts),
        "model_used": actual_model
    }


@router.post("/reddit/{post_id}/apply-concepts")
async def apply_concepts_to_reddit(post_id: str, concepts: List[Dict[str, str]]):
    """
    Apply selected concepts to a Reddit post.
    Expects array of objects with display_name and slug.
    """
    return repo.apply_concepts_to_reddit(post_id=post_id, concepts=concepts)


def _score_concept_text(query_lower: str, query_words: List[str],
                        display_name: str, slug: str, description: str,
                        aliases: List[str]) -> float:
    """Pure text-match score in [0, 100]; 0 means no textual match at all.

    Exact display-name/slug match ranks above exact alias match, which ranks
    above substring matches, which rank above per-word matches. The usage
    boost is applied by the caller and must never rescue a zero text score.
    """
    if not query_lower:
        return 0

    display_name_lower = display_name.lower()
    slug_lower = slug.lower()
    description_lower = (description or '').lower()
    aliases_lower = [a.lower() for a in aliases]

    if query_lower == display_name_lower or query_lower == slug_lower:
        return 100
    if any(query_lower == a for a in aliases_lower):
        return 95
    if query_lower in display_name_lower or query_lower in slug_lower:
        return 80
    if any(query_lower in a for a in aliases_lower):
        return 75

    haystacks = [display_name_lower, slug_lower, description_lower] + aliases_lower
    word_matches = sum(1 for word in query_words if any(word in h for h in haystacks))
    return (word_matches / len(query_words)) * 60 if query_words else 0


@router.get("/search-concepts")
async def search_concepts_semantic(
    query: str,
    content_types: Optional[List[str]] = Query(None),
    limit: int = Query(20, ge=1, le=100)
):
    """
    Universal concept text search that can filter by content types.
    Matches the query against concept display names, slugs and descriptions
    (simple string/word matching, no embeddings).
    Can be used across different browsing contexts (tweets, articles, papers).
    """
    try:
        # Default to all content types if none specified
        if content_types is None:
            content_types = ['tweet', 'article', 'paper']
        
        # Get all concepts with counts for specified content types
        all_concepts = []
        for content_type in content_types:
            concepts = concept_service.get_all_concepts_with_counts(content_type=content_type)
            # Add content type to each concept for filtering
            for concept in concepts:
                concept['available_in'] = content_type
                all_concepts.append(concept)
        
        # Deduplicate concepts (same concept may appear in multiple content types)
        concept_map = {}
        for concept in all_concepts:
            concept_id = concept['concept_id']
            if concept_id not in concept_map:
                concept_map[concept_id] = {
                    'concept_id': concept_id,
                    'display_name': concept['display_name'],
                    'slug': concept['slug'],
                    'entity_type': concept.get('entity_type', 'topic'),
                    'icon': concept.get('icon'),
                    'description': concept.get('description'),
                    'total_usage': 0,
                    'content_types': [],
                    'usage_by_type': {}
                }
            
            # Aggregate usage counts
            concept_map[concept_id]['total_usage'] += concept.get('count', 0)
            content_type = concept['available_in']
            if content_type not in concept_map[concept_id]['content_types']:
                concept_map[concept_id]['content_types'].append(content_type)
            concept_map[concept_id]['usage_by_type'][content_type] = concept.get('count', 0)
        
        # Aliases: map concept_id (string form) -> [alias_text, ...] so that
        # e.g. "LLM" finds "Large Language Model"
        alias_map: dict = {}
        try:
            for alias_doc in db.tag_aliases_v2.find({}, {'alias_text': 1, 'concept_id': 1}):
                if alias_doc.get('alias_text') and alias_doc.get('concept_id') is not None:
                    alias_map.setdefault(str(alias_doc['concept_id']), []).append(alias_doc['alias_text'])
        except Exception as alias_err:
            logger.warning(f"Could not load concept aliases for search: {alias_err}")

        # Text matching (word/substring based; see _score_concept_text)
        query_lower = query.lower()
        query_words = query_lower.split()
        
        results = []
        for concept_data in concept_map.values():
            text_score = _score_concept_text(
                query_lower, query_words,
                concept_data['display_name'], concept_data['slug'],
                concept_data.get('description') or '',
                alias_map.get(str(concept_data['concept_id']), [])
            )

            # Usage boost only refines ranking among textual matches — it must
            # not surface popular concepts for unrelated queries
            if text_score > 10:
                usage_boost = min(concept_data['total_usage'] / 10, 20)  # Max 20 point boost
                score = text_score + usage_boost
                results.append({
                    'concept_id': concept_data['concept_id'],
                    'display_name': concept_data['display_name'],
                    'slug': concept_data['slug'],
                    'entity_type': concept_data['entity_type'],
                    'icon': concept_data.get('icon'),
                    'description': concept_data.get('description'),
                    'total_usage': concept_data['total_usage'],
                    'content_types': concept_data['content_types'],
                    'usage_by_type': concept_data['usage_by_type'],
                    'text_score': text_score,
                    'similarity_score': round(score, 2)
                })
        
        # Sort by text relevance first, usage second — an exact match on a
        # rarely-used concept must outrank a popular substring match
        results.sort(key=lambda x: (x['text_score'], x['total_usage']), reverse=True)
        for r in results:
            r.pop('text_score', None)

        page = results[:limit]
        return {
            'query': query,
            'content_types_searched': content_types,
            'total_results': len(page),
            'total_matches': len(results),
            'results': page
        }
        
    except Exception as e:
        logger.error(f"Error searching concepts: {e}")
        raise HTTPException(status_code=500, detail=str(e))
