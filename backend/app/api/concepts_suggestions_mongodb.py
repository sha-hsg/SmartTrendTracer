"""
Concept-aware suggestion API for tweets (MongoDB version).
Generates suggestions with proper concept structure (display_name, slug).
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Optional
from pydantic import BaseModel
import json
import logging
from app.database.mongodb import get_database
from bson import ObjectId

from app.services.concept_only_tag_service import ConceptOnlyTagService
from app.services.llm_manager import get_llm_manager

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
        
        # Get LLM response
        # Map frontend model names to actual model names
        model_mapping = {
            # Working GPT models
            "gpt-5": "gpt-5-2025-08-07",  # Reasoning model (temperature=1 only)
            "gpt-5.1": "gpt-5.1",  # Reasoning model (temperature=1 only)
            "gpt-5-mini": "gpt-5-mini",  # Reasoning model (temperature=1 only)
            "gpt-5-nano": "gpt-5-nano",  # Reasoning model (temperature=1 only)
            "gpt-4o": "gpt-4o",
            "gpt-4o-mini": "gpt-4o-mini",

            # Working Claude models
            "claude-sonnet-4.5": "claude-sonnet-4-5-20250929",
            "claude-opus-4.1": "claude-opus-4-1-20250805",
            "claude-haiku-4.5": "claude-haiku-4-5-20251001",
            "claude-3.5-sonnet": "claude-sonnet-4-20250514",

            # Working Gemini models
            "gemini-3-pro": "gemini-3.0-pro",  # Preview model
            "gemini-2.5-pro": "gemini-2.5-pro",  # Uses gemini-pro-latest
            "gemini-2.5-flash": "gemini-2.5-flash",  # Uses gemini-flash-latest
            "gemini-2.5-flash-lite": "gemini-2.5-flash-lite"
        }

        # Extract model from request or use default
        selected_model = request.model if request.model else "claude-3.5-sonnet"
        actual_model = model_mapping.get(selected_model, selected_model)

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
            model=actual_model  # Pass the selected model
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
    # Verify tweet exists
    tweet = db.tweets.find_one({"_id": tweet_id})
    if not tweet:
        raise HTTPException(status_code=404, detail="Tweet not found")
    
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

@router.post("/papers/{paper_id}/suggest")
async def suggest_concepts_for_paper(paper_id: str):
    """
    Get AI-suggested concepts for a specific paper.
    """
    # Get the paper from MongoDB
    try:
        paper = db.papers.find_one({"_id": ObjectId(paper_id)})
    except:
        paper = db.papers.find_one({"id": int(paper_id) if paper_id.isdigit() else paper_id})
    
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    # Get existing concepts on this paper
    existing_concepts = concept_service.get_tags_for_content('paper', str(paper.get('_id', paper.get('id'))))
    existing_concept_ids = [c['concept_id'] for c in existing_concepts]
    existing_slugs = [c['slug'] for c in existing_concepts]
    
    # Similar logic as tweets but using paper title and abstract
    paper_text = f"{paper.get('title', '')} {paper.get('abstract', '')}".lower()
    
    similar_concepts = []
    all_concepts = concept_service.get_all_concepts_with_counts(content_type='paper')
    
    for concept in all_concepts[:50]:
        if concept['concept_id'] not in existing_concept_ids:
            if concept['slug'].replace('_', ' ') in paper_text or \
               concept['display_name'].lower() in paper_text:
                similar_concepts.append({
                    "concept_id": concept['concept_id'],
                    "display_name": concept['display_name'],
                    "slug": concept['slug'],
                    "entity_type": concept.get('entity_type', 'topic'),
                    "usage_count": concept.get('count', 0),
                    "type": "existing"
                })
    
    return {
        "paper_id": paper_id,
        "existing_suggestions": similar_concepts[:10],
        "new_suggestions": [],  # Could add LLM suggestions for papers too
        "already_tagged": existing_concepts,
        "total_suggestions": len(similar_concepts)
    }

@router.get("/search-concepts")
async def search_concepts_semantic(
    query: str,
    content_types: Optional[List[str]] = None,
    limit: int = 20
):
    """
    Universal semantic concept search that can filter by content types.
    Returns concepts similar to the search query.
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
        
        # Perform semantic search (for now, simple text matching - can be enhanced with embeddings)
        query_lower = query.lower()
        query_words = query_lower.split()
        
        results = []
        for concept_data in concept_map.values():
            # Calculate similarity score
            score = 0
            display_name_lower = concept_data['display_name'].lower()
            slug_lower = concept_data['slug'].lower()
            description_lower = (concept_data.get('description') or '').lower()
            
            # Exact match gets highest score
            if query_lower == display_name_lower or query_lower == slug_lower:
                score = 100
            # Contains query gets high score
            elif query_lower in display_name_lower or query_lower in slug_lower:
                score = 80
            # Word matches get medium score
            else:
                word_matches = 0
                for word in query_words:
                    if word in display_name_lower or word in slug_lower or word in description_lower:
                        word_matches += 1
                score = (word_matches / len(query_words)) * 60
            
            # Boost score based on usage (popular concepts rank higher)
            usage_boost = min(concept_data['total_usage'] / 10, 20)  # Max 20 point boost
            score += usage_boost
            
            if score > 10:  # Only include concepts with reasonable similarity
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
                    'similarity_score': round(score, 2)
                })
        
        # Sort by similarity score (highest first)
        results.sort(key=lambda x: x['similarity_score'], reverse=True)
        
        return {
            'query': query,
            'content_types_searched': content_types,
            'total_results': len(results),
            'results': results[:limit]
        }
        
    except Exception as e:
        logger.error(f"Error searching concepts: {e}")
        raise HTTPException(status_code=500, detail=str(e))
