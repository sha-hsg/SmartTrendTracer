"""Content processing, summarization, tag suggestion, and recollection routes for articles."""

from fastapi import APIRouter, HTTPException, Query, Body
from typing import Dict, Any, List
from datetime import datetime, timezone
from bson import ObjectId
import json
import re

from .utils import db, logger, concept_service

router = APIRouter()


@router.post("/{article_id}/extract-metadata")
def extract_metadata_from_content(article_id: str, model: str | None = Query(None)):
    """Extract author and published date from article content using LLM"""

    try:
        if len(article_id) == 24:
            article = db.articles.find_one({'_id': ObjectId(article_id)})
        else:
            article = db.articles.find_one({'old_sqlite_id': int(article_id)})
    except Exception:
        article = None

    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    # Get article content (use standardized content_markdown field)
    content = article.get('content_markdown', '')

    if not content:
        raise HTTPException(status_code=400, detail="Article has no content to analyze")

    # Take first 2000 characters (enough for header with author/date info)
    content_snippet = content[:2000]

    # Use LLM to extract metadata via LLMManager
    from app.services.llm_manager import get_llm_manager
    llm_manager = get_llm_manager()

    prompt = f"""Extract the author name and publication date from this article content.
Return ONLY a JSON object with 'author' and 'date' fields.
If you cannot find the information, use null.

For the date, convert it to ISO format (YYYY-MM-DD).

Example output:
{{"author": "John Doe", "date": "2025-01-15"}}

Article content:
{content_snippet}

JSON output:"""

    try:
        # Use entity extraction task type for metadata extraction
        messages = [{"role": "user", "content": prompt}]
        llm_response = llm_manager.completion_sync(
            task_type='entity_extraction',
            messages=messages,
            user_id='default',
            override_params={'model': model} if model else None,
        )
        response = llm_response.choices[0].message.content

        # Parse the JSON response
        # Extract JSON from response (in case there's extra text)
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            metadata = json.loads(json_match.group())
        else:
            metadata = json.loads(response)

        # Update article in database
        update_fields = {}

        if metadata.get('author'):
            update_fields['author_name'] = metadata['author']
            logger.info(f"Extracted author: {metadata['author']}")

        if metadata.get('date'):
            from datetime import datetime, timezone
            # Parse the date
            try:
                pub_date = datetime.fromisoformat(metadata['date'])
                update_fields['published_at'] = pub_date
                logger.info(f"Extracted date: {metadata['date']}")
            except Exception:
                logger.warning(f"Could not parse date: {metadata['date']}")

        if update_fields:
            db.articles.update_one(
                {'_id': article['_id']},
                {'$set': update_fields}
            )

        return {
            "success": True,
            "extracted": metadata,
            "updated_fields": list(update_fields.keys())
        }

    except Exception as e:
        logger.error(f"Failed to extract metadata: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to extract metadata: {str(e)}")

@router.post("/{article_id}/tags/suggest")
async def suggest_tags_for_article(article_id: str, request: dict = Body({})):
    """
    Get AI-powered concept suggestions for an article.
    Returns existing matching concepts and new LLM-generated suggestions.
    """
    model = request.get('model', None)
    logger.info(f"Tag suggestion requested for article {article_id} with model: {model}")

    # Get article
    try:
        if len(article_id) == 24:
            article = db.articles.find_one({'_id': ObjectId(article_id)})
        else:
            article = db.articles.find_one({'old_sqlite_id': int(article_id)})
    except Exception:
        article = None

    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    # Get existing concepts on this article
    article_id_str = str(article['_id'])
    sqlite_id_str = str(article.get('old_sqlite_id', ''))

    existing_tags = list(db.tag_instances.find({
        'content_type': 'article',
        '$or': [
            {'content_id': article_id_str},
            {'content_id': sqlite_id_str}
        ]
    }))

    existing_concept_ids = [ti['concept_id'] for ti in existing_tags if ti.get('concept_id')]

    # Get concept display names for already tagged (PERF: batch query)
    already_tagged = []
    if existing_concept_ids:
        concepts_lookup = concept_service.get_concepts_by_ids(existing_concept_ids)
        for cid in existing_concept_ids:
            concept = concepts_lookup.get(str(cid))
            if concept:
                already_tagged.append({
                    'concept_id': str(cid),
                    'display_name': concept.get('display_name', ''),
                    'slug': concept.get('slug', '')
                })

    # Find similar existing concepts based on title/content
    existing_suggestions = []
    all_concepts = concept_service.get_all_concepts_with_counts(content_type='article')

    # Simple text matching for suggestions
    article_text = f"{article.get('title', '')} {article.get('content_markdown', '')[:2000]}".lower()

    for concept in all_concepts[:30]:  # Check top 30 concepts
        if concept['id'] not in existing_concept_ids:
            if concept['display_name'].lower() in article_text or \
               any(alias.lower() in article_text for alias in concept.get('aliases', [])):
                existing_suggestions.append({
                    'concept_id': concept['id'],
                    'display_name': concept['display_name'],
                    'slug': concept['slug'],
                    'entity_type': concept.get('entity_type', 'topic'),
                    'usage_count': concept.get('usage_count', 0),
                    'type': 'existing'
                })
                if len(existing_suggestions) >= 5:
                    break

    # Generate new suggestions using LLM
    new_suggestions = []
    model_used = model if model else 'default'
    try:
        from app.services.llm_manager import get_llm_manager
        llm_manager = get_llm_manager()

        # Prepare article text for LLM
        article_text_for_llm = f"Title: {article.get('title', '')}\n"
        article_text_for_llm += f"Author: {article.get('author_name', 'Unknown')}\n\n"

        content = article.get('content_markdown', '') or article.get('content', '') or ''
        if content:
            article_text_for_llm += f"Article Content:\n{content[:12000]}"
            logger.info(f"Sending article content to LLM: {min(len(content), 12000)} characters")
        else:
            logger.warning(f"Article {article_id} has no content, using title only")

        existing_slugs = [t['slug'] for t in already_tagged]

        prompt = f"""Analyze this article and suggest relevant concept tags.

{article_text_for_llm}

Instructions:
1. Suggest 5-8 relevant concepts for this article
2. Focus on main topics, technologies, people, organizations mentioned
3. Use snake_case for slugs (e.g., machine_learning, sam_altman)
4. Use proper capitalization for display names (e.g., "Machine Learning", "Sam Altman")
5. Avoid concepts already tagged: {', '.join(existing_slugs)}

Return as JSON array with format:
[
  {{"display_name": "Proper Name", "slug": "snake_case_slug", "entity_type": "topic|person|organisation|location|event|product"}}
]
"""

        # Model mapping (same as tweets)
        model_mapping = {
            "gpt-5": "gpt-5-2025-08-07",
            "gpt-5.1": "gpt-5.1",
            "gpt-5-mini": "gpt-5-mini",
            "gpt-5-nano": "gpt-5-nano",
            "gpt-4o": "gpt-4o",
            "gpt-4o-mini": "gpt-4o-mini",
            "claude-sonnet-4.5": "claude-sonnet-4-5-20250929",
            "claude-opus-4.1": "claude-opus-5-5",
            "claude-haiku-4.5": "claude-haiku-4-5-20251001",
            "claude-3.5-sonnet": "claude-sonnet-5",
            "gemini-3.1-pro-preview": "gemini-3.1-pro-preview",
            "gemini-3.5-flash": "gemini-3.5-flash",
            "gemini-3.1-flash-lite": "gemini-3.1-flash-lite",
            "gemini-2.5-pro": "gemini-2.5-pro",
            "gemini-2.5-flash": "gemini-2.5-flash",
            "gemini-2.5-flash-lite": "gemini-2.5-flash-lite",
        }

        selected_model = model if model else "claude-3.5-sonnet"
        actual_model = model_mapping.get(selected_model, selected_model)

        logger.info(f"Article concept suggestion using model: {actual_model}")

        messages = [{"role": "user", "content": prompt}]

        llm_response = await llm_manager.completion(
            task_type='tag_suggestion',
            messages=messages,
            user_id='default',
            model=actual_model
        )

        response = llm_response.choices[0].message.content
        model_used = llm_response.model

        logger.info(f"LLM response from {model_used}: {len(response)} chars")

        # Parse JSON response (handle markdown code blocks)
        if response:
            json_text = response.strip()
            if json_text.startswith("```json"):
                json_text = json_text[7:]
            if json_text.startswith("```"):
                json_text = json_text[3:]
            if json_text.endswith("```"):
                json_text = json_text[:-3]

            try:
                suggested = json.loads(json_text.strip())
                if not isinstance(suggested, list):
                    logger.error(f"LLM returned non-list response: {type(suggested)}")
                    suggested = []
            except json.JSONDecodeError:
                # Try to extract JSON array from response
                json_match = re.search(r'\[[\s\S]*\]', response)
                if json_match:
                    try:
                        suggested = json.loads(json_match.group())
                    except json.JSONDecodeError:
                        logger.error(f"Failed to parse extracted JSON: {response[:200]}")
                        suggested = []
                else:
                    logger.error(f"No JSON array found in response: {response[:200]}")
                    suggested = []

            # Filter out already tagged and existing suggestions
            already_tagged_slugs = {t['slug'] for t in already_tagged}
            existing_suggestion_slugs = {s['slug'] for s in existing_suggestions}

            for concept in suggested:
                slug = concept.get('slug', '')
                if slug not in already_tagged_slugs and slug not in existing_suggestion_slugs:
                    new_suggestions.append({
                        'display_name': concept.get('display_name', slug),
                        'slug': slug,
                        'entity_type': concept.get('entity_type', 'topic'),
                        'type': 'new'
                    })

        logger.info(f"Generated {len(new_suggestions)} new tag suggestions for article {article_id}")

    except Exception as e:
        logger.error(f"Failed to generate LLM tag suggestions: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")

    return {
        "existing_suggestions": existing_suggestions[:5],
        "new_suggestions": new_suggestions[:8],
        "already_tagged": already_tagged,
        "model_used": model_used
    }


@router.post("/{article_id}/apply-concepts")
async def apply_concepts_to_article(article_id: str, concepts: List[Dict[str, str]]):
    """
    Batch-apply selected concepts to an article.
    Expects array of objects with display_name and slug.
    """
    try:
        if len(article_id) == 24:
            article = db.articles.find_one({'_id': ObjectId(article_id)})
        else:
            article = db.articles.find_one({'old_sqlite_id': int(article_id)})
    except Exception:
        article = None

    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    success_count = 0
    fail_count = 0

    for concept_data in concepts:
        try:
            success, concept_id = concept_service.add_tag(
                content_type='article',
                content_id=str(article['_id']),
                text=concept_data['display_name'],
                preserve_display_name=True
            )
            if success:
                # Keep articles.concept_ids in sync (parity with
                # POST /{article_id}/concepts in content.py) so the
                # concept_id filter in GET / finds tagged articles.
                db.articles.update_one(
                    {'_id': article['_id']},
                    {'$addToSet': {'concept_ids': concept_id}}
                )
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
        "message": f"Applied {success_count} concepts to article"
    }


@router.post("/{article_id}/summarize")
def summarize_article(article_id: str, model: str | None = Query(None)):
    """Generate a summary for an article"""

    try:
        if len(article_id) == 24:
            article = db.articles.find_one({'_id': ObjectId(article_id)})
        else:
            article = db.articles.find_one({'old_sqlite_id': int(article_id)})
    except Exception:
        article = None

    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    # Check if already summarized
    if article.get('summary'):
        return {
            "summary": article['summary'],
            "key_points": article.get('key_points', []),
            "model_used": article.get('summary_model', 'unknown'),
            "cached": True
        }

    # Get the content for summarization (use standardized content_markdown field)
    content = article.get('content_markdown', '') or article.get('preview', '')

    if not content:
        raise HTTPException(status_code=400, detail="No content available to summarize")

    # Validate content length (minimum 50 characters)
    if len(content.strip()) < 50:
        raise HTTPException(
            status_code=400,
            detail=f"Article content too short ({len(content.strip())} chars). Minimum 50 characters required."
        )

    # Import the summarization service (uses centralized LLM Manager)
    from app.services.article_summarizer import ArticleSummarizer

    try:
        summarizer = ArticleSummarizer()
    except Exception as e:
        logger.error(f"Failed to initialize ArticleSummarizer: {e}")
        raise HTTPException(status_code=500, detail=f"LLM service initialization failed: {str(e)}")

    # Get author name - check embedded field first, then lookup
    author_name = article.get('author_name', 'Unknown')
    if not author_name or author_name == 'Unknown':
        if article.get('author_id'):
            try:
                author_doc = db.substack_authors.find_one({'_id': article['author_id']})
                if not author_doc:
                    author_doc = db.substack_authors.find_one({'sqlite_id': article['author_id']})
                if author_doc:
                    author_name = author_doc.get('name', 'Unknown')
            except Exception:
                pass

    # Generate summary with timeout handling
    try:
        summary_result = summarizer.summarize_article_content(
            content=content,
            title=article.get('title', 'Untitled'),
            author=author_name,
            model=model,
        )
    except TimeoutError:
        raise HTTPException(status_code=504, detail="Summary generation timed out. The article might be too long.")
    except Exception as e:
        logger.error(f"Summary generation failed: {e}")
        if "API key" in str(e).lower():
            raise HTTPException(status_code=500, detail="LLM API key is invalid or missing.")
        elif "rate limit" in str(e).lower():
            raise HTTPException(status_code=429, detail="Rate limit exceeded. Please try again later.")
        else:
            raise HTTPException(status_code=500, detail=f"Summary generation failed: {str(e)}")

    if summary_result and summary_result.get('summary'):
        # Extract the summary text and key points
        summary_text = summary_result['summary']
        key_points = summary_result.get('key_points', [])
        model_used = summary_result.get('model_used', 'unknown')

        # Save the summary to the database
        db.articles.update_one(
            {'_id': article['_id']},
            {
                '$set': {
                    'summary': summary_text,
                    'key_points': key_points,
                    'summarized': True,
                    'summarized_at': datetime.now(timezone.utc),
                    'summary_model': model_used
                }
            }
        )

        return {
            "summary": summary_text,
            "key_points": key_points,
            "model_used": model_used,
            "cached": False
        }
    else:
        raise HTTPException(status_code=500, detail="Summary generation returned empty result")


@router.post("/{article_id}/recollect")
async def recollect_article(article_id: str):
    """
    Re-collect an article using Playwright to get fresh/complete content.

    Useful when an article was initially imported incompletely or
    when you want to refresh the content.
    """
    # Find the article
    try:
        if len(article_id) == 24:
            article = db.articles.find_one({'_id': ObjectId(article_id)})
        else:
            article = db.articles.find_one({'old_sqlite_id': int(article_id)})
    except Exception:
        article = None

    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    # Get the URL
    url = article.get('url')
    if not url:
        raise HTTPException(status_code=400, detail="Article has no URL to recollect from")

    try:
        from app.collectors.playwright_collector import PlaywrightCollector

        collector = PlaywrightCollector()
        try:
            result = await collector.fetch_article(url)

            if not result.get('success'):
                return {
                    'success': False,
                    'error': result.get('error', 'Failed to fetch article'),
                    'requires_auth': result.get('requires_auth', False),
                    'site': result.get('site'),
                    'auth_url': result.get('auth_url')
                }

            # Update the article with new content
            update_doc = {
                'content_html': result.get('content_html'),
                'content_markdown': result.get('content_markdown'),
                'preview': result.get('preview'),
                'word_count': result.get('word_count', 0),
                'reading_time_minutes': result.get('reading_time_minutes', 0),
                'recollected_at': datetime.now(timezone.utc),
            }

            # Update title if we got a better one (not just a number)
            new_title = result.get('title')
            if new_title and not new_title.isdigit() and new_title != article.get('title'):
                update_doc['title'] = new_title

            # Update author if we got one and didn't have one before
            if result.get('author') and not article.get('author_name'):
                update_doc['author_name'] = result.get('author')

            db.articles.update_one(
                {'_id': article['_id']},
                {'$set': update_doc}
            )

            return {
                'success': True,
                'article_id': str(article['_id']),
                'title': update_doc.get('title', article.get('title')),
                'word_count': result.get('word_count', 0),
                'reading_time_minutes': result.get('reading_time_minutes', 0),
                'updated_fields': list(update_doc.keys())
            }

        finally:
            await collector.close()

    except ImportError:
        raise HTTPException(
            status_code=503,
            detail="Playwright not installed. Run: pip install playwright && playwright install chromium"
        )
    except Exception as e:
        logger.error(f"Failed to recollect article: {e}")
        raise HTTPException(status_code=500, detail=str(e))
