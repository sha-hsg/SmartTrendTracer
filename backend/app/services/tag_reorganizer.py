"""
Unified Tag Reorganization Service
Merges rule-based (ComprehensiveStrategy) and LLM-powered (LLMStrategy)
approaches into a single service with strategy pattern.
"""

from app.paths import DATA_ROOT
import re
import json
import logging
import os
import time
from typing import Dict, List, Set, Optional, Any, Callable
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from abc import ABC, abstractmethod

from app.services.tag_reorganizer_helpers import (
    AliasType, ConceptStatus, Concept, Alias, Relation,
    canonicalize_slug, generate_display_name,
    ROOT_CATEGORIES, CATEGORY_KEYWORDS,
    is_misspelling, is_abbreviation, is_plural,
    categorize_tag,
    extract_json_from_markdown, extract_json_from_text,
)

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────
# Strategy interface
# ──────────────────────────────────────────────────

class ReorganizationStrategy(ABC):
    @abstractmethod
    def reorganize_tags(self, tags_data: List[Dict[str, Any]], progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        ...

    def reorganize_tags_with_debug(self, tags_data: List[Dict[str, Any]], progress_callback: Optional[Callable] = None) -> tuple:
        """Default: returns (result, empty_debug). LLM strategy overrides this."""
        result = self.reorganize_tags(tags_data, progress_callback)
        return result, {"prompt": "Rule-based reorganization - no LLM prompt", "system_prompt": ""}


# ──────────────────────────────────────────────────
# ComprehensiveStrategy (rule-based, deterministic)
# ──────────────────────────────────────────────────

class ComprehensiveStrategy(ReorganizationStrategy):
    """Rule-based tag reorganization with canonicalization, aliasing, and hierarchy."""

    def __init__(self):
        self.concepts: Dict[str, Concept] = {}
        self.aliases: Dict[str, Alias] = {}
        self.relations: List[Relation] = []
        self.merge_proposals: List[Dict] = []

    # -- public helpers exposed for validation in LLM strategy --
    canonicalize_slug = staticmethod(canonicalize_slug)
    generate_display_name = staticmethod(generate_display_name)

    def reorganize_tags(self, tags_data: List[Dict[str, Any]], progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        logger.info(f"Starting rule-based reorganization of {len(tags_data)} tags")

        self._initialize_root_categories()

        tag_to_concept = {}
        for tag_info in tags_data:
            original_tag = tag_info.get('tag', '')
            usage_count = tag_info.get('count', 0)
            if not original_tag:
                continue
            slug = canonicalize_slug(original_tag)
            if not slug:
                continue

            if slug in self.concepts:
                if original_tag != slug:
                    self._add_alias(original_tag, slug)
                self.concepts[slug].usage_count += usage_count
            else:
                display = generate_display_name(slug)
                concept = Concept(id=slug, slug=slug, display_name=display, usage_count=usage_count)
                category = categorize_tag(slug, display)
                concept.parents = [category]
                self.concepts[slug] = concept
                if category in self.concepts:
                    self.concepts[category].children.add(slug)
                if original_tag != slug:
                    self._add_alias(original_tag, slug)

            tag_to_concept[original_tag] = slug

        self._detect_and_merge_duplicates()
        self._cleanup_hierarchy()
        validation = self._validate(tags_data)

        result = {
            "summary": {
                "total_original_tags": len(tags_data),
                "total_concepts": len(self.concepts),
                "total_aliases": len(self.aliases),
                "root_categories": len([c for c in self.concepts.values() if not c.parents]),
                "validation_passed": validation["all_tags_mapped"],
            },
            "concepts": [self._concept_to_dict(c) for c in self.concepts.values()],
            "aliases": [self._alias_to_dict(a) for a in self.aliases.values()],
            "relations": [{"source": r.source, "target": r.target, "relation_type": r.relation_type, "metadata": r.metadata} for r in self.relations],
            "mapping_report": tag_to_concept,
            "validation_report": validation,
            "merge_proposals": self.merge_proposals,
            "hierarchy": self._generate_hierarchy(),
        }
        logger.info(f"Rule-based reorganization complete: {len(self.concepts)} concepts, {len(self.aliases)} aliases")
        return result

    def export_to_database_format(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return {"concepts": result["concepts"], "aliases": result["aliases"], "timestamp": datetime.now(timezone.utc).isoformat(), "version": "2.0", "backwards_compatible": True}

    # ── internals ──

    def _initialize_root_categories(self):
        for slug, info in ROOT_CATEGORIES.items():
            self.concepts[slug] = Concept(id=slug, slug=slug, display_name=info["display_name"], description=info["description"], parents=[], status=ConceptStatus.ACTIVE)

    def _add_alias(self, alias_text: str, canonical_slug: str):
        if alias_text in self.aliases:
            if self.aliases[alias_text].canonical_slug != canonical_slug:
                logger.warning(f"Alias conflict: '{alias_text}' maps to both '{self.aliases[alias_text].canonical_slug}' and '{canonical_slug}'")
            return
        alias_type = self._detect_alias_type(alias_text, canonical_slug)
        self.aliases[alias_text] = Alias(alias_text=alias_text, canonical_slug=canonical_slug, alias_type=alias_type)

    def _detect_alias_type(self, original: str, canonical: str) -> AliasType:
        orig_l, canon_l = original.lower(), canonical.lower()
        if is_misspelling(orig_l, canon_l):
            return AliasType.MISSPELLING
        if is_abbreviation(original, canonical):
            return AliasType.ABBREVIATION
        if is_plural(orig_l, canon_l):
            return AliasType.PLURAL
        if canonicalize_slug(original) == canonicalize_slug(canonical):
            return AliasType.VARIANT
        if any(w in orig_l for w in ['old', 'legacy', 'deprecated', 'v1', 'beta']):
            return AliasType.DEPRECATED
        return AliasType.SYNONYM

    def _detect_and_merge_duplicates(self):
        groups = defaultdict(list)
        for c in self.concepts.values():
            if not c.parents:
                continue
            key = re.sub(r'[^a-z0-9]', '', c.slug.lower())
            groups[key].append(c)
        for group in groups.values():
            if len(group) > 1:
                group.sort(key=lambda x: x.usage_count, reverse=True)
                for dup in group[1:]:
                    self._merge_concepts(dup, group[0])

    def _merge_concepts(self, src: Concept, tgt: Concept):
        self._add_alias(src.slug, tgt.slug)
        if src.display_name != tgt.display_name:
            self._add_alias(src.display_name, tgt.slug)
        tgt.usage_count += src.usage_count
        for child in src.children:
            tgt.children.add(child)
            if child in self.concepts:
                self.concepts[child].parents = [p if p != src.slug else tgt.slug for p in self.concepts[child].parents]
        for p in src.parents:
            if p in self.concepts:
                self.concepts[p].children.discard(src.slug)
                self.concepts[p].children.add(tgt.slug)
        src.status = ConceptStatus.MERGED
        src.metadata["merged_into"] = tgt.slug
        self.merge_proposals.append({"source": src.slug, "target": tgt.slug, "reason": "Duplicate concept detected", "source_usage": src.usage_count, "target_usage": tgt.usage_count})
        del self.concepts[src.slug]

    def _cleanup_hierarchy(self):
        for c in self.concepts.values():
            c.children = set(c.children)
            c.children.discard(c.slug)
            if c.slug in c.parents:
                c.parents.remove(c.slug)
            valid = set()
            for ch in c.children:
                if ch in self.concepts:
                    valid.add(ch)
                elif ch in self.aliases:
                    canon = self.aliases[ch].canonical_slug
                    if canon in self.concepts:
                        valid.add(canon)
            c.children = valid

    def _validate(self, original_tags: List[Dict]) -> Dict[str, Any]:
        report = {"all_tags_mapped": True, "unmapped_tags": [], "alias_conflicts": [], "orphan_concepts": [], "circular_dependencies": [], "statistics": {}}
        for info in original_tags:
            tag = info.get('tag', '')
            if not tag:
                continue
            slug = canonicalize_slug(tag)
            if slug in self.concepts or tag in self.aliases:
                continue
            report["all_tags_mapped"] = False
            report["unmapped_tags"].append(tag)
        for c in self.concepts.values():
            if not c.parents and c.slug not in ROOT_CATEGORIES:
                report["orphan_concepts"].append(c.slug)
        for c in self.concepts.values():
            if self._has_cycle(c.slug, set()):
                report["circular_dependencies"].append(c.slug)
        report["statistics"] = {"total_tags": len(original_tags), "mapped_tags": len(original_tags) - len(report["unmapped_tags"]), "concepts": len(self.concepts), "aliases": len(self.aliases), "orphans": len(report["orphan_concepts"]), "circular": len(report["circular_dependencies"])}
        return report

    def _has_cycle(self, slug: str, visited: Set[str]) -> bool:
        if slug in visited:
            return True
        if slug not in self.concepts:
            return False
        visited.add(slug)
        return any(self._has_cycle(p, visited.copy()) for p in self.concepts[slug].parents)

    def _generate_hierarchy(self) -> Dict[str, Any]:
        h = {}
        for slug in ROOT_CATEGORIES:
            if slug in self.concepts:
                h[slug] = self._hierarchy_node(self.concepts[slug])
        return h

    def _hierarchy_node(self, concept: Concept, depth: int = 0) -> Optional[Dict]:
        if depth > 5:
            return None
        node = {"slug": concept.slug, "display_name": concept.display_name, "usage_count": concept.usage_count, "children": {}}
        for ch in sorted(concept.children):
            if ch in self.concepts:
                child_node = self._hierarchy_node(self.concepts[ch], depth + 1)
                if child_node:
                    node["children"][ch] = child_node
        return node

    def _concept_to_dict(self, c: Concept) -> Dict:
        return {"id": c.id, "slug": c.slug, "display_name": c.display_name, "description": c.description, "parents": c.parents, "children": list(c.children), "status": c.status.value, "usage_count": c.usage_count, "metadata": c.metadata}

    def _alias_to_dict(self, a: Alias) -> Dict:
        return {"alias_text": a.alias_text, "canonical_slug": a.canonical_slug, "alias_type": a.alias_type.value, "confidence": a.confidence, "metadata": a.metadata}


# ──────────────────────────────────────────────────
# LLMStrategy (GPT-5 / Gemini powered)
# ──────────────────────────────────────────────────

# Directory for storing LLM responses
RESPONSE_LOG_DIR = DATA_ROOT / 'gpt5_responses'
RESPONSE_LOG_DIR.mkdir(parents=True, exist_ok=True)


class LLMStrategy(ReorganizationStrategy):
    """LLM-powered tag reorganization with GPT-5 primary, Gemini fallback, rule-based last resort."""

    def __init__(self, model_override: Optional[str] = None):
        from app.services.llm_manager import get_llm_manager
        self.llm = get_llm_manager()
        self.model_override = model_override

        self.prompts = self.llm.get_prompt('tag_reorganization')

        # 'gpt5' is the legacy UI switch for "OpenAI flagship" -> the
        # tag_reorganization_openai route; otherwise the dedicated reorganization
        # route. Models, fallbacks and params come from litellm_config.yaml.
        self.task_type = 'tag_reorganization_openai' if model_override == 'gpt5' else 'tag_reorganization_comprehensive'
        self.model_config = {'model': self.llm._resolve_actual_model(self.task_type)}

        self.top_level_json = self._load_top_level_json()
        logger.info(f"Initialized LLM reorganizer with model: {self.model_config.get('model')}")

    @staticmethod
    def _load_top_level_json() -> str:
        for path in ['top_level.json', '../top_level.json']:
            if os.path.exists(path):
                try:
                    with open(path, 'r') as f:
                        return json.dumps(json.load(f), indent=2)
                except Exception:
                    pass
        return "{}"

    def reorganize_tags(self, tags_data: List[Dict[str, Any]], progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        debug_info: Dict[str, Any] = {}
        return self._reorganize_internal(tags_data, progress_callback, debug_info)

    def reorganize_tags_with_debug(self, tags_data: List[Dict[str, Any]], progress_callback: Optional[Callable] = None) -> tuple:
        debug_info: Dict[str, Any] = {}
        result = self._reorganize_internal(tags_data, progress_callback, debug_info)
        return result, debug_info

    def _reorganize_internal(self, tags_data: List[Dict[str, Any]], progress_callback: Optional[Callable], debug_info: Dict[str, Any]) -> Dict[str, Any]:
        try:
            logger.info(f"Starting LLM reorganization of {len(tags_data)} tags using {self.model_config.get('model', 'unknown')}")

            debug_info['input_stats'] = {
                'total_concepts': len(tags_data),
                'organized': sum(1 for t in tags_data if t.get('current_parents')),
                'unorganized': sum(1 for t in tags_data if not t.get('current_parents')),
                'auto_generated': sum(1 for t in tags_data if t.get('auto_generated')),
                'manual': sum(1 for t in tags_data if not t.get('auto_generated')),
            }

            # Compact format to save tokens
            compact_tags = []
            for tag in tags_data:
                ct = {'id': tag['id'], 't': tag['tag'], 'd': tag['display_name'], 'c': tag['count']}
                if tag.get('entity_type'):
                    ct['e'] = tag['entity_type']
                if tag.get('current_parents'):
                    ct['p'] = tag['current_parents']
                compact_tags.append(ct)
            tags_json = json.dumps(compact_tags, separators=(',', ':'))

            estimated_tokens = len(tags_json) // 4
            total_taggings = sum(t.get('count', 0) for t in tags_data)
            average_usage = total_taggings / len(tags_data) if tags_data else 0

            system_prompt = self.prompts.get('system', '')
            user_prompt = self.prompts.get('user_template', '')
            user_prompt = user_prompt.replace('{total_tags}', str(len(tags_data)))
            user_prompt = user_prompt.replace('{tags_json}', tags_json)
            user_prompt = user_prompt.replace('{top_level_json}', self.top_level_json)
            user_prompt = user_prompt.replace('{total_taggings}', str(total_taggings))
            user_prompt = user_prompt.replace('{average_usage}', f"{average_usage:.1f}")

            debug_info.update({'system_prompt': system_prompt, 'prompt': user_prompt, 'prompt_size': len(user_prompt), 'system_prompt_size': len(system_prompt), 'estimated_tokens': estimated_tokens})

            result_text = self._call_llm(system_prompt, user_prompt, progress_callback, len(tags_data))
            if not result_text:
                return self._fallback(tags_data)

            try:
                json_result = extract_json_from_markdown(result_text)
                result = json_result if json_result else json.loads(re.sub(r'/\*.*?\*/', '', result_text, flags=re.DOTALL))

                debug_info['output_stats'] = {'concepts_returned': len(result.get('concepts', [])), 'aliases_returned': len(result.get('aliases', [])), 'merge_proposals': len(result.get('merge_proposals', [])), 'response_size': len(result_text)}

                result['validation'] = self._validate_result(result, tags_data)
                debug_info['validation'] = result['validation']
                result['metadata'] = {'model': self.model_config.get('model'), 'timestamp': datetime.now(timezone.utc).isoformat(), 'input_tags': len(tags_data), 'estimated_tokens': estimated_tokens, 'debug_info': debug_info}
                return result

            except json.JSONDecodeError:
                extracted = extract_json_from_text(result_text)
                if extracted:
                    return extracted
                return self._fallback(tags_data)

        except Exception as e:
            import traceback
            logger.error(f"Error in LLM reorganization: {e}\n{traceback.format_exc()}")
            return self._fallback(tags_data)

    def _call_llm(self, system_prompt: str, user_prompt: str, progress_callback: Optional[Callable], tags_count: int) -> Optional[str]:
        """Single routed call; retries and provider fallbacks are handled by
        the LiteLLM router (num_retries, fallbacks in litellm_config.yaml)."""
        if progress_callback:
            progress_callback(f"Processing {tags_count} concepts with {self.model_config.get('model', 'LLM')} (may take 5-15 minutes)...")
        try:
            result_text = self.llm.complete_text(self.task_type, user_prompt, system_prompt=system_prompt)
            self._save_response(result_text, 'success')
            return result_text
        except Exception as e:
            logger.error(f"LLM reorganization call failed: {e}")
            self._save_response(str(e), 'error')
            if progress_callback:
                progress_callback("LLM unavailable, using rule-based fallback")
            return None

    def _fallback(self, tags_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        logger.info("Falling back to rule-based reorganization")
        result = ComprehensiveStrategy().reorganize_tags(tags_data)
        result['metadata'] = {'model': 'fallback_rule_based', 'timestamp': datetime.now(timezone.utc).isoformat(), 'reason': 'LLM unavailable or failed'}
        return result

    def _validate_result(self, result: Dict[str, Any], original_tags: List[Dict]) -> Dict[str, Any]:
        validation = {'all_tags_mapped': True, 'unmapped_tags': [], 'unmapped_ids': [], 'duplicate_aliases': [], 'orphan_concepts': [], 'statistics': {}}
        original_texts = set(t.get('tag', t.get('slug', '')) for t in original_tags if t.get('tag') or t.get('slug'))
        original_ids = set(t.get('id') for t in original_tags if t.get('id'))

        concepts = {c.get('slug', c.get('tag', '')): c for c in result.get('concepts', []) if c.get('slug') or c.get('tag')}
        concept_ids = set(c.get('id') for c in result.get('concepts', []) if c.get('id'))
        aliases = result.get('aliases', [])

        mapped = set()
        for c in concepts.values():
            cid = c.get('slug') or c.get('tag', '')
            if cid:
                mapped.add(cid)
            if 'display_name' in c:
                mapped.add(c['display_name'])
        for a in aliases:
            at = a.get('alias_text') or a.get('from_tag', '')
            if at:
                mapped.add(at)

        for tag in original_texts:
            if tag not in mapped:
                canonical = canonicalize_slug(tag)
                if canonical not in concepts:
                    validation['all_tags_mapped'] = False
                    validation['unmapped_tags'].append(tag)

        alias_texts = [a.get('alias_text') or a.get('alias_tag', '') for a in aliases]
        dupes = [t for t in alias_texts if alias_texts.count(t) > 1]
        if dupes:
            validation['duplicate_aliases'] = list(set(dupes))

        root_cats = set(result.get('root_categories', []))
        for c in concepts.values():
            cid = c.get('slug') or c.get('tag', '')
            if not c.get('parents') and cid and cid not in root_cats:
                validation['orphan_concepts'].append(cid)

        if original_ids:
            for tid in original_ids:
                if tid not in concept_ids:
                    if not any(a.get('id') == tid or a.get('alias_of') == tid for a in aliases):
                        validation['unmapped_ids'].append(tid)

        validation['statistics'] = {'total_input_tags': len(original_tags), 'mapped_tags': len(original_texts) - len(validation['unmapped_tags']), 'mapped_ids': len(original_ids) - len(validation['unmapped_ids']) if original_ids else 0, 'concepts_created': len(concepts), 'aliases_created': len(aliases), 'root_categories': len(root_cats), 'orphan_concepts': len(validation['orphan_concepts']), 'duplicate_aliases': len(validation['duplicate_aliases']), 'ids_provided': len(original_ids) if original_ids else 0}
        return validation

    def analyze_tags(self, tags_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        try:
            system_prompt = "You are an expert at analyzing tag taxonomies. Analyze the provided tags and identify: 1. Duplicate concepts with different spellings 2. Inconsistent naming conventions 3. Missing hierarchy relationships 4. Suggested root categories 5. Quality issues and recommendations"
            user_prompt = f"Analyze these tags and provide insights:\n\nTotal tags: {len(tags_data)}\nSample tags: {json.dumps(tags_data[:100], indent=2)}\n\nProvide analysis as JSON."
            result_text = self._call_llm(system_prompt, user_prompt, None, len(tags_data))
            if result_text:
                try:
                    return json.loads(result_text)
                except Exception:
                    return {'error': 'Failed to parse analysis', 'raw': result_text}
            return {'error': 'No analysis generated'}
        except Exception as e:
            return {'error': str(e)}

    def _save_response(self, content: str, response_type: str) -> str:
        ts = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
        filepath = RESPONSE_LOG_DIR / f"gpt5_{response_type}_{ts}.txt"
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"Timestamp: {datetime.now(timezone.utc).isoformat()}\nType: {response_type}\nModel: {self.model_config.get('model', 'unknown')}\n{'-'*80}\n{content}")
            return str(filepath)
        except Exception:
            return ""


# ──────────────────────────────────────────────────
# TagReorganizer — public facade (factory)
# ──────────────────────────────────────────────────

class TagReorganizer:
    """
    Unified entry point for tag reorganization.

    Usage:
        reorganizer = TagReorganizer(strategy="gpt5", model_override="gpt5")
        result = reorganizer.reorganize_tags(tags_data)

        # or with debug info:
        result, debug = reorganizer.reorganize_tags_with_debug(tags_data, callback)
    """

    def __init__(self, strategy: str = "gpt5", model_override: Optional[str] = None):
        if strategy == "comprehensive":
            self._strategy = ComprehensiveStrategy()
        else:
            self._strategy = LLMStrategy(model_override=model_override)

    def reorganize_tags(self, tags_data: List[Dict[str, Any]], progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        return self._strategy.reorganize_tags(tags_data, progress_callback)

    def reorganize_tags_with_debug(self, tags_data: List[Dict[str, Any]], progress_callback: Optional[Callable] = None) -> tuple:
        return self._strategy.reorganize_tags_with_debug(tags_data, progress_callback)

    def analyze_tags(self, tags_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        if isinstance(self._strategy, LLMStrategy):
            return self._strategy.analyze_tags(tags_data)
        return {"error": "Tag analysis requires LLM strategy"}


# ──────────────────────────────────────────────────
# Backwards-compatible aliases
# ──────────────────────────────────────────────────
ComprehensiveTagReorganizer = ComprehensiveStrategy
GPT5TagReorganizer = LLMStrategy
