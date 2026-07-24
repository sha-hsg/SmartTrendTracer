from typing import List, Dict, Optional
from datetime import datetime, timezone
from bson import ObjectId
import logging
import re

logger = logging.getLogger(__name__)


class ConceptLookupMixin:

    def _normalize_concept_identifier(self, concept_id):
        """Return concept identifier using ObjectId when possible."""
        if isinstance(concept_id, ObjectId):
            return concept_id
        if isinstance(concept_id, str) and len(concept_id) == 24:
            try:
                return ObjectId(concept_id)
            except Exception:
                return concept_id
        return concept_id

    def _find_concept_by_slug_or_alias(self, slug: str) -> Optional[Dict]:
        """Resolve a concept document by slug or alias text."""
        if not slug:
            return None

        normalized_slug = self._normalize_to_slug(slug)

        concept = self.tag_concepts.find_one({"slug": normalized_slug})
        if concept:
            return concept

        alias = self.tag_aliases.find_one({"alias": normalized_slug})
        if not alias:
            alias = self.tag_aliases.find_one({"alias_text": normalized_slug})

        if alias:
            return self.get_concept_by_id(alias.get('concept_id'))

        return None

    def _generate_concept_id(self) -> str:
        """Generate a unique concept ID in format c_XXXXX.
        Caches the counter in memory to avoid repeated regex scans."""
        if not hasattr(self, '_concept_id_counter'):
            last_concept = self.tag_concepts.find_one(
                {"id": {"$regex": "^c_\\d+$"}},
                sort=[("id", -1)]
            )
            if last_concept and 'id' in last_concept:
                self._concept_id_counter = int(last_concept['id'].split('_')[1])
            else:
                self._concept_id_counter = 999

        self._concept_id_counter += 1
        return f"c_{self._concept_id_counter:05d}"

    def _normalize_to_slug(self, text: str) -> str:
        """Convert text to snake_case slug"""
        # Convert to lowercase
        text = text.lower().strip()
        # Replace spaces and hyphens with underscores
        text = re.sub(r'[\s\-]+', '_', text)
        # Remove non-alphanumeric characters except underscores
        text = re.sub(r'[^\w_]', '', text)
        # Remove duplicate underscores
        text = re.sub(r'_+', '_', text)
        # Strip underscores from ends
        return text.strip('_')

    def _generate_display_name(self, slug: str) -> str:
        """Generate a proper display name from a slug"""
        special_cases = {
            'ai': 'AI', 'ml': 'ML', 'llm': 'LLM', 'llms': 'LLMs',
            'nlp': 'NLP', 'rag': 'RAG', 'api': 'API', 'apis': 'APIs',
            'gpt': 'GPT', 'bert': 'BERT', 'lstm': 'LSTM', 'rnn': 'RNN',
            'cnn': 'CNN', 'gan': 'GAN', 'gans': 'GANs', 'vae': 'VAE',
            'rl': 'RL', 'dl': 'DL', 'gpu': 'GPU', 'cpu': 'CPU',
            'openai': 'OpenAI', 'deepmind': 'DeepMind',
            'huggingface': 'HuggingFace', 'anthropic': 'Anthropic',
            'usa': 'USA', 'uk': 'UK', 'eu': 'EU', 'nyc': 'NYC',
            'mit': 'MIT', 'ceo': 'CEO', 'cto': 'CTO', 'vp': 'VP',
        }

        parts = slug.split('_')
        result_parts = []

        for part in parts:
            lower_part = part.lower()
            if lower_part in special_cases:
                result_parts.append(special_cases[lower_part])
            elif part.isdigit():
                result_parts.append(part)
            elif lower_part.startswith('gpt') and len(part) > 3:
                result_parts.append(f"GPT-{part[3:]}")
            elif lower_part.startswith('v') and part[1:].isdigit():
                result_parts.append(part.upper())
            else:
                result_parts.append(part.capitalize())

        return ' '.join(result_parts)

    def find_or_create_concept(self, text: str, preserve_display_name: bool = True) -> str:
        """
        Find existing concept or create new one.
        Always returns a concept_id.

        Args:
            text: The text to create a concept from
            preserve_display_name: If True, use the exact text as display_name (for user selections)
        """
        # Normalize to slug
        slug = self._normalize_to_slug(text)

        # Check if concept exists with this slug
        existing = self.tag_concepts.find_one({"slug": slug})
        if existing:
            return str(existing['_id'])

        # Check aliases
        alias = self.tag_aliases.find_one({"alias": slug})
        if alias:
            return alias['concept_id']

        # Create new concept
        # Use exact text as display_name if preserve_display_name is True (e.g., from context menu)
        # Otherwise generate display_name from slug (e.g., for auto-generated concepts)
        if preserve_display_name:
            display_name = text.strip()  # Use exact text, just strip whitespace
        else:
            display_name = self._generate_display_name(slug)

        new_concept = {
            "id": self._generate_concept_id(),
            "slug": slug,
            "name": display_name,
            "display_name": display_name,
            "description": f"Auto-generated concept for '{display_name}'",
            "parents": [],
            "entity_type": "topic",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "created_by": "concept_service",
            "auto_generated": True
        }

        result = self.tag_concepts.insert_one(new_concept)
        logger.info(f"Created concept: {display_name} (id: {new_concept['id']})")

        return str(result.inserted_id)

    def get_concept_by_id(self, concept_id) -> Optional[Dict]:
        """Get concept details by ID (accepts ObjectId or string)"""
        # Return None for null/empty concept_ids (orphan tags)
        if concept_id is None or concept_id == '' or concept_id == 'None':
            return None

        try:
            # If it's already an ObjectId, use it directly
            if isinstance(concept_id, ObjectId):
                return self.tag_concepts.find_one({"_id": concept_id})
            # If it's a string that looks like an ObjectId
            elif isinstance(concept_id, str) and len(concept_id) == 24:
                return self.tag_concepts.find_one({"_id": ObjectId(concept_id)})
            # Otherwise treat as custom ID
            else:
                return self.tag_concepts.find_one({"id": concept_id})
        except Exception:
            return None

    def get_concepts_by_ids(self, concept_ids: List) -> Dict[str, Dict]:
        """
        Batch fetch multiple concepts by their IDs.
        Returns a dict mapping concept_id (as string) to concept document.
        This avoids N+1 query patterns.
        """
        if not concept_ids:
            return {}

        # Convert to ObjectIds where applicable
        object_ids = []
        for cid in concept_ids:
            if cid is None or cid == '' or cid == 'None':
                continue
            try:
                if isinstance(cid, ObjectId):
                    object_ids.append(cid)
                elif isinstance(cid, str) and len(cid) == 24:
                    object_ids.append(ObjectId(cid))
            except Exception:
                pass

        if not object_ids:
            return {}

        # Single batch query
        concepts = list(self.tag_concepts.find({"_id": {"$in": object_ids}}))

        # Build lookup dict
        return {str(c['_id']): c for c in concepts}

    def search_concepts(self, query: str, limit: int = 10) -> List[Dict]:
        """
        Search for concepts by text.
        """
        try:
            # Create search regex
            search_pattern = {'$regex': query, '$options': 'i'}

            # Search in multiple fields
            concepts = self.tag_concepts.find({
                '$or': [
                    {'slug': search_pattern},
                    {'name': search_pattern},
                    {'display_name': search_pattern},
                    {'description': search_pattern}
                ]
            }).limit(limit)

            results = []
            for concept in concepts:
                results.append({
                    'concept_id': str(concept['_id']),
                    'id': concept.get('id', f"c_{str(concept['_id'])[:4]}"),
                    'slug': concept.get('slug', ''),
                    'display_name': concept.get('display_name', concept.get('name', '')),
                    'entity_type': concept.get('entity_type', 'topic')
                })

            return results

        except Exception as e:
            logger.error(f"Error searching concepts: {e}")
            return []
