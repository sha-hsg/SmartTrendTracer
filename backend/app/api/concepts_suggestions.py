"""
Concept-aware suggestion API for tweets.
Generates suggestions with proper concept structure (display_name, slug).
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Optional
import json
import logging

from app.services.concept_only_tag_service import ConceptOnlyTagService
from app.services.llm_service import get_llm_service

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize concept service
concept_service = ConceptOnlyTagService()

@router.post("/tweets/{tweet_id}/suggest")
    """
    Get AI-suggested concepts for a specific tweet.
    Returns proper concept structures with display_name and slug.
    """
    
    # Get the tweet
    tweet = db.query(Tweet).filter(Tweet.id == tweet_id).first()
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
    tweet_text_lower = tweet.text.lower()
    for concept in all_concepts[:50]:  # Check top 50 concepts
        if concept['concept_id'] not in existing_concept_ids:
            # Check if concept name appears in tweet
            if concept['slug'].replace('_', ' ') in tweet_text_lower or \
               concept['display_name'].lower() in tweet_text_lower:
                similar_concepts.append({
                    'concept_id': concept['concept_id'],
                    'slug': concept['slug'],
                    'display_name': concept['display_name'],
                    'usage_count': concept.get('count', 0),
                    'type': 'existing',
                    'auto_generated': concept.get('auto_generated', False)
                })
    
    # Limit to top 5 similar concepts
    similar_concepts = similar_concepts[:5]
    
    # 2. Generate new concept suggestions using LLM
    new_concept_suggestions = []
    model_used = "unknown"
    
    try:
        # Use enhanced prompt for concept generation
        llm_service = get_llm_service()
        
        # Custom prompt for concept generation
        concept_prompt = f"""
        Analyze this tweet and suggest 3-5 relevant concepts (tags) for categorization.
        
        Tweet: "{tweet.text}"
        Author: @{tweet.author_username}
        
        For each concept, provide:
        1. display_name: Proper capitalization (e.g., "Machine Learning", "OpenAI", "GPT-4")
        2. slug: snake_case version (e.g., "machine_learning", "openai", "gpt_4")
        
        Return as JSON array:
        [
            {{"display_name": "Machine Learning", "slug": "machine_learning"}},
            {{"display_name": "OpenAI", "slug": "openai"}}
        ]
        
        Focus on:
        - Key topics and themes
        - Technologies mentioned
        - Companies/organizations
        - Important concepts
        - Avoid generic tags
        
        Existing concepts to avoid: {', '.join(existing_slugs[:10])}
        """
        
        # Call LLM with the enhanced prompt
        response = llm_service.generate_text(concept_prompt)
        
        # Parse the response
        if response:
            try:
                # Extract JSON from response
                import re
                json_match = re.search(r'\[.*?\]', response, re.DOTALL)
                if json_match:
                    concept_list = json.loads(json_match.group())
                    for item in concept_list:
                        if 'display_name' in item and 'slug' in item:
                            # Check if not already suggested
                            if item['slug'] not in existing_slugs:
                                new_concept_suggestions.append({
                                    'display_name': item['display_name'],
                                    'slug': item['slug'],
                                    'type': 'new',
                                    'model': 'gpt-4'
                                })
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(f"Failed to parse LLM response: {e}")
                # Fallback: try to extract suggestions from plain text
                lines = response.split('\n')
                for line in lines:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        # Simple extraction from text
                        slug = line.lower().replace(' ', '_').replace('-', '_')
                        slug = ''.join(c for c in slug if c.isalnum() or c == '_')
                        if slug and slug not in existing_slugs:
                            display_name = line.title() if len(line.split()) > 1 else line
                            new_concept_suggestions.append({
                                'display_name': display_name,
                                'slug': slug,
                                'type': 'new',
                                'model': 'fallback'
                            })
        
        # Get model info
        with open('llm.json', 'r') as f:
            llm_config = json.load(f)
        model_used = llm_config.get('models', {}).get('tag_suggestion', {}).get('model', 'unknown')
        
    except Exception as e:
        logger.error(f"Error generating concept suggestions: {e}")
    
    # Limit new suggestions to 5
    new_concept_suggestions = new_concept_suggestions[:5]
    
    return {
        'tweet_id': tweet_id,
        'existing_concepts': similar_concepts,
        'new_concepts': new_concept_suggestions,
        'already_tagged': [
            {
                'concept_id': c['concept_id'],
                'display_name': c['display_name'],
                'slug': c['slug']
            }
            for c in existing_concepts
        ],
        'model_used': model_used,
        'total_suggestions': len(similar_concepts) + len(new_concept_suggestions)
    }

@router.post("/tweets/{tweet_id}/apply-concepts")
def apply_concepts_to_tweet(
    tweet_id: str,
    concepts: List[Dict[str, str]],  # List of {display_name, slug} objects
):
    """
    Apply concept suggestions to a tweet.
    Creates concepts if they don't exist.
    """
    
    # Verify tweet exists
    tweet = db.query(Tweet).filter(Tweet.id == tweet_id).first()
    if not tweet:
        raise HTTPException(status_code=404, detail="Tweet not found")
    
    applied = []
    failed = []
    
    for concept_data in concepts:
        try:
            # The concept service will create the concept if it doesn't exist
            # It will use the display_name to create a proper concept
            display_name = concept_data.get('display_name', '')
            slug = concept_data.get('slug', '')
            
            # If we have a slug but no display_name, generate it
            if slug and not display_name:
                display_name = slug.replace('_', ' ').title()
            
            # If we have display_name but no slug, generate it
            if display_name and not slug:
                slug = display_name.lower().replace(' ', '_').replace('-', '_')
                slug = ''.join(c for c in slug if c.isalnum() or c == '_')
            
            # Apply the concept (will create if needed)
            success, concept_id = concept_service.add_tag('tweet', tweet_id, display_name)
            
            if success:
                applied.append({
                    'concept_id': concept_id,
                    'display_name': display_name,
                    'slug': slug
                })
            else:
                failed.append(display_name)
                
        except Exception as e:
            logger.error(f"Failed to apply concept {concept_data}: {e}")
            failed.append(concept_data.get('display_name', 'unknown'))
    
    return {
        'tweet_id': tweet_id,
        'applied': applied,
        'failed': failed,
        'success_count': len(applied),
        'fail_count': len(failed)
    }