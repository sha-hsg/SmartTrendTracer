"""
Automatic concept tagging of tweets, articles and papers — the one path used
by the scheduler job tag_content, the tweet "Annotate all" batch, tweet
concept suggestions and article tag suggestions.

The LLM (task tag_suggestion, prompt concept_suggestion) proposes concepts
as {display_name, slug, entity_type}; applying them goes through
ConceptOnlyTagService.add_tag, which resolves aliases and the canonical slug
before creating anything new. Papers in the interactive viewer keep their
own deeper prompt (paper_tag_suggestion).
"""
from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, List, Optional, Tuple

from app.repositories import concept_tagging as repo

logger = logging.getLogger(__name__)

TEXT_LIMIT = {'tweet': 2000, 'article': 12000, 'paper': 8000, 'reddit': 4000}
COUNT = {'tweet': '3-5', 'article': '5-8', 'paper': '6-10', 'reddit': '3-5'}
KIND = {'tweet': 'tweet', 'article': 'newsletter article', 'paper': 'research paper', 'reddit': 'Reddit post'}


class SuggestionError(RuntimeError):
    """The LLM call failed — callers must not mark the item as tagged."""


def parse_concepts(raw: str) -> List[Dict[str, Any]]:
    """JSON array of {display_name, slug?, entity_type?} from an LLM answer
    (tolerates code fences and text around the array)."""
    if not raw:
        return []
    match = re.search(r'\[[\s\S]*\]', raw)
    if not match:
        return []
    try:
        items = json.loads(match.group())
    except json.JSONDecodeError:
        return []
    from app.repositories.concepts import concept_slug
    out = []
    for it in items if isinstance(items, list) else []:
        if isinstance(it, dict) and str(it.get('display_name', '')).strip():
            name, etype = str(it['display_name']).strip(), str(it.get('entity_type', 'topic'))
        elif isinstance(it, str) and it.strip():
            name, etype = it.strip(), 'topic'
        else:
            continue
        out.append({'display_name': name, 'slug': concept_slug(name), 'entity_type': etype})   # canonical slug
    return out


def _messages(content_type: str, item: Dict[str, Any], existing: List[str], llm) -> List[Dict[str, str]]:
    prompt = llm.get_prompt('concept_suggestion')
    user = prompt['user_template'].format(
        kind=KIND[content_type], count=COUNT[content_type], title=item.get('title') or '—',
        author=item.get('author') or '—', text=(item.get('text') or '')[:TEXT_LIMIT[content_type]],
        existing=', '.join(existing) or 'none')
    return [{'role': 'system', 'content': prompt['system']}, {'role': 'user', 'content': user}]


def suggest(content_type: str, item: Dict[str, Any], existing: List[str], model: Optional[str] = None,
            llm=None) -> Tuple[List[Dict[str, Any]], str]:
    """(suggestions, model used). Raises SuggestionError if the call fails."""
    if llm is None:
        from app.services.llm_manager import get_llm_manager
        llm = get_llm_manager()
    routed = llm.resolve_model_override(model)
    try:
        resp = llm.completion_sync('tag_suggestion', _messages(content_type, item, existing, llm),
                                   user_id='default', override_params={'model': routed} if routed else None)
    except Exception as e:
        raise SuggestionError(str(e)) from e
    content = resp.choices[0].message.content
    if isinstance(content, list):                     # Gemini part lists
        content = ''.join(p.get('text', '') if isinstance(p, dict) else str(p) for p in content)
    return parse_concepts(content or ''), getattr(resp, 'model', '') or ''


async def suggest_async(content_type: str, item: Dict[str, Any], existing: List[str],
                        model: Optional[str] = None, llm=None) -> Tuple[List[Dict[str, Any]], str]:
    if llm is None:
        from app.services.llm_manager import get_llm_manager
        llm = get_llm_manager()
    routed = llm.resolve_model_override(model)
    try:
        resp = await llm.completion('tag_suggestion', _messages(content_type, item, existing, llm),
                                    user_id='default', override_params={'model': routed} if routed else None)
    except Exception as e:
        raise SuggestionError(str(e)) from e
    content = resp.choices[0].message.content
    if isinstance(content, list):
        content = ''.join(p.get('text', '') if isinstance(p, dict) else str(p) for p in content)
    return parse_concepts(content or ''), getattr(resp, 'model', '') or ''


def tag_item(content_type: str, content_id: str, model: Optional[str] = None, concept_service=None,
             llm=None) -> Dict[str, Any]:
    """Suggest and apply concepts for one item. Returns {new, skipped, failed}
    or {error}. An item with no usable concepts is marked as tagged."""
    if concept_service is None:
        from app.repositories.concepts import ConceptOnlyTagService
        concept_service = ConceptOnlyTagService()
    from app.repositories.concepts import concept_slug
    item = repo.load_item(content_type, content_id)
    if not item:
        return {'error': 'not_found'}
    existing = concept_service.get_tags_for_content(content_type, content_id)
    existing_slugs = {c['slug'] for c in existing}
    try:
        suggestions, _ = suggest(content_type, item, sorted(existing_slugs), model=model, llm=llm)
    except SuggestionError as e:
        return {'error': f'llm_failed: {e}'}
    new, skipped, failed = [], 0, 0
    for s in suggestions:
        slug = concept_slug(s['display_name'])
        if not slug or slug in existing_slugs:
            skipped += 1
            continue
        ok, _cid = concept_service.add_tag(content_type, content_id, s['display_name'], preserve_display_name=True,
                                          entity_type=s.get('entity_type'))
        if ok:
            new.append(s['display_name'])
            existing_slugs.add(slug)
        else:
            failed += 1
    if not new and not existing and not failed:
        repo.mark_no_concepts(content_type, content_id)
    return {'new': new, 'skipped': skipped, 'failed': failed}


def untagged_ids(content_type: str, limit: Optional[int] = None) -> List[str]:
    return repo.untagged_ids(content_type, limit)


def tag_untagged(content_type: str, limit: Optional[int] = None, llm=None) -> Dict[str, Any]:
    """Tag every untagged item of one type (scheduler job tag_content)."""
    ids = repo.untagged_ids(content_type, limit)
    stats = {'items': len(ids), 'tagged': 0, 'new_tags': 0, 'errors': 0}
    for cid in ids:
        result = tag_item(content_type, cid, llm=llm)
        if 'error' in result:
            stats['errors'] += 1
            continue
        stats['tagged'] += 1
        stats['new_tags'] += len(result['new'])
    logger.info(f"Tagging {content_type}: {stats}")
    return stats
