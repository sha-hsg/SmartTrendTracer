"""
Affiliation extraction and application endpoints.

Split from entities.py -- all route handlers copied verbatim.
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from bson import ObjectId
import logging

from .utils import db

router = APIRouter()

logger = logging.getLogger(__name__)


@router.post("/{paper_id}/extract-affiliations")
def extract_paper_affiliations(paper_id: str) -> Dict[str, Any]:
    """Extract author affiliations from paper header using LLM"""
    try:
        # Try to convert to ObjectId if it's a valid format
        if len(paper_id) == 24:
            paper = db.papers.find_one({'_id': ObjectId(paper_id)})
        else:
            # Try old SQLite ID
            paper = db.papers.find_one({'old_sqlite_id': int(paper_id)})
    except Exception:
        paper = None

    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    # Get existing authors - handle both string and array formats
    authors_raw = paper.get('authors', [])
    if not authors_raw:
        raise HTTPException(status_code=400, detail="Paper has no authors to extract affiliations for")

    # Parse authors if they're a string
    if isinstance(authors_raw, str):
        # Split by comma and clean up
        authors = [{'name': name.strip()} for name in authors_raw.split(',') if name.strip()]
    elif isinstance(authors_raw, list):
        # Already in list format
        authors = authors_raw
    else:
        authors = []

    # Get paper header text (title to abstract)
    title = paper.get('title', '')
    abstract = paper.get('abstract', '')

    # Try to get the beginning of the content if available
    header_text = f"Title: {title}\n\n"

    # Look for the first section or content before abstract
    if paper.get('sections'):
        # Get content from the first few sections (likely contains author info)
        for section in paper['sections'][:3]:  # Check first 3 sections
            section_content = section.get('content', '')
            if section_content:
                header_text += f"{section.get('title', '')}\n{section_content[:2000]}\n\n"
                break
    elif paper.get('content'):
        # Get first 2000 characters of content
        header_text += paper['content'][:2000] + "\n\n"

    header_text += f"Abstract: {abstract}"

    # Prepare authors list for the prompt
    authors_list = []
    for i, author in enumerate(authors):
        if isinstance(author, dict):
            name = author.get('name', f'Author {i+1}')
            current_affiliation = author.get('affiliation', 'Not specified')
            authors_list.append(f"{i+1}. {name} (Current affiliation: {current_affiliation})")
        else:
            authors_list.append(f"{i+1}. {author} (Current affiliation: Not specified)")

    authors_text = '\n'.join(authors_list)

    try:
        from app.services.llm_manager import get_llm_manager
        import json
        import logging

        logger = logging.getLogger(__name__)
        llm = get_llm_manager()

        # Prompt from prompts_config.json, model/params from the task route
        prompt_config = llm.get_prompt('paper_affiliation_extraction')
        user_prompt = prompt_config.get('user_template', '').format(
            authors_list=authors_text,
            header_text=header_text
        )
        prompt_response = llm.complete_text(
            'paper_affiliation_extraction',
            user_prompt,
            system_prompt=prompt_config.get('system') or None,
        )

        logger.info(f"LLM response for affiliation extraction: {prompt_response}")

        # Parse the JSON response
        try:
            affiliations_data = json.loads(prompt_response)
        except json.JSONDecodeError:
            # Try to extract JSON from the response if it's wrapped in text
            import re
            json_match = re.search(r'\{.*\}', prompt_response, re.DOTALL)
            if json_match:
                affiliations_data = json.loads(json_match.group())
            else:
                raise ValueError("Could not parse LLM response as JSON")

        # Format the response for the UI
        suggestions = []
        for affiliation in affiliations_data.get('affiliations', []):
            author_index = affiliation.get('author_index', 0) - 1  # Convert to 0-based index
            if 0 <= author_index < len(authors):
                author_name = authors[author_index].get('name', authors[author_index]) if isinstance(authors[author_index], dict) else authors[author_index]
                suggestions.append({
                    'author_index': author_index,
                    'author_name': author_name,
                    'suggested_affiliation': affiliation.get('affiliation', ''),
                    'confidence': affiliation.get('confidence', 'medium'),
                    'current_affiliation': authors[author_index].get('affiliation', '') if isinstance(authors[author_index], dict) else ''
                })

        return {
            'paper_id': paper_id,
            'paper_title': title,
            'suggestions': suggestions,
            'model_used': model_config.get('model')  # Model name string, not the config dict
        }

    except Exception as e:
        logger.error(f"Error extracting affiliations for paper {paper_id}: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{paper_id}/apply-affiliations")
def apply_paper_affiliations(paper_id: str, affiliations_data: Dict[str, Any]) -> Dict[str, Any]:
    """Apply selected affiliations to paper authors"""
    try:
        # Try to convert to ObjectId if it's a valid format
        if len(paper_id) == 24:
            paper = db.papers.find_one({'_id': ObjectId(paper_id)})
        else:
            # Try old SQLite ID
            paper = db.papers.find_one({'old_sqlite_id': int(paper_id)})
    except Exception:
        paper = None

    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    # Get affiliations to apply
    affiliations_to_apply = affiliations_data.get('affiliations', [])

    # Work on authors_detailed (object array, system convention).
    # Fall back to deriving it from the legacy `authors` field if missing.
    authors_detailed = paper.get('authors_detailed') or []
    if not authors_detailed:
        authors_raw = paper.get('authors', [])
        if isinstance(authors_raw, str):
            authors_detailed = [{'name': name.strip()} for name in authors_raw.split(',') if name.strip()]
        elif isinstance(authors_raw, list):
            authors_detailed = [
                author if isinstance(author, dict) else {'name': str(author)}
                for author in authors_raw
            ]

    # Ensure every entry is a dict (defensive against legacy string entries)
    authors_detailed = [
        author if isinstance(author, dict) else {'name': str(author)}
        for author in authors_detailed
    ]

    updated_count = 0
    for affiliation in affiliations_to_apply:
        author_index = affiliation.get('author_index')
        new_affiliation = affiliation.get('affiliation')

        if author_index is not None and 0 <= author_index < len(authors_detailed):
            authors_detailed[author_index]['affiliation'] = new_affiliation
            updated_count += 1

    # Re-derive `authors` as comma-separated string (system convention);
    # NEVER write the dict list into `authors`.
    authors_string = ', '.join(
        author.get('name', '') for author in authors_detailed if author.get('name')
    )

    db.papers.update_one(
        {'_id': paper['_id']},
        {'$set': {
            'authors_detailed': authors_detailed,
            'authors': authors_string
        }}
    )

    return {
        'paper_id': paper_id,
        'updated_count': updated_count,
        'authors': authors_string,
        'authors_detailed': authors_detailed
    }
