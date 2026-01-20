"""
AI-powered entity extraction service for automatic annotation
Migrated to use LLM Manager with LiteLLM
"""
import json
import os
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime, timezone
from dotenv import load_dotenv
import hashlib

from app.services.llm_manager import get_llm_manager

load_dotenv()

class EntityExtraction:
    """Represents an extracted entity"""
    def __init__(self, text: str, entity_type: str, confidence: float,
                 context: str = "", normalized: str = "", metadata: Dict = None):
        self.text = text
        self.entity_type = entity_type
        self.confidence = confidence
        self.context = context
        self.normalized = normalized or self._normalize_text(text)
        self.metadata = metadata or {}
        self.id = self._generate_id()

    def _normalize_text(self, text: str) -> str:
        """Normalize entity text for matching - preserve capitalization for proper nouns"""
        return text.strip().replace(" ", "-").replace("_", "-")

    def _generate_id(self) -> str:
        """Generate unique ID for the entity"""
        content = f"{self.text}:{self.entity_type}:{self.normalized}"
        return hashlib.md5(content.encode()).hexdigest()[:12]

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "text": self.text,
            "type": self.entity_type,
            "confidence": self.confidence,
            "context": self.context,
            "normalized": self.normalized,
            "metadata": self.metadata
        }

class EntityExtractionService:
    """Service for extracting entities from text using LLM Manager"""

    def __init__(self, use_fast_model: bool = False, model_choice: str = None, custom_model: str = None, user_id: str = "default"):
        """Initialize with LLM Manager

        Args:
            use_fast_model: Use fast model (deprecated, kept for backward compatibility)
            model_choice: Specific model to use ('gpt5', 'gemini', 'claude', 'fast')
            custom_model: Direct model name from UI (e.g., 'gemini-2.5-flash-lite', 'claude-opus-4-1-20250805')
            user_id: User ID for preference lookup
        """
        self.use_fast_model = use_fast_model
        self.model_choice = model_choice
        self.custom_model = custom_model  # Store custom model selection
        self.user_id = user_id

        # Initialize LLM Manager
        self.llm_manager = get_llm_manager()

        # Load configurations
        with open('llm.json', 'r') as f:
            self.llm_config = json.load(f)

        with open('prompts_config.json', 'r') as f:
            self.prompts = json.load(f)

        with open('top_level.json', 'r') as f:
            self.ontology_schema = json.load(f)

        # Determine task type based on model choice
        if model_choice == 'gpt5':
            self.task_type = 'entity_extraction_gpt5'
        elif model_choice == 'gemini':
            self.task_type = 'entity_extraction_gemini'
        elif model_choice == 'claude':
            self.task_type = 'entity_extraction'
        elif model_choice == 'fast':
            self.task_type = 'entity_extraction_fast'
        elif use_fast_model:
            self.task_type = 'entity_extraction_fast'
        else:
            self.task_type = 'entity_extraction'

        # Get model info for attribution (will be overridden if custom_model is set)
        task_info = self.llm_manager.get_task_info(self.task_type)
        self.model_name = custom_model if custom_model else (task_info['model'] if task_info else 'unknown')

        self.extraction_config = self.ontology_schema.get('extraction_config', {})

        # Cache valid entity types from MongoDB
        self._cache_valid_entity_types()

    def _cache_valid_entity_types(self):
        """Cache valid entity types from MongoDB concept hierarchy"""
        from app.database.mongodb import get_database

        db = get_database()
        concepts_col = db.tag_concepts_v2

        self.valid_entity_types = {}
        self.entity_parent_map = {}

        # Get all distinct entity types
        distinct_entity_types = concepts_col.distinct("entity_type", {
            "entity_type": {
                "$exists": True,
                "$nin": ["concept", "category"]
            }
        })

        # Determine parent category mapping
        category_mapping = {
            'person': 'named-entities',
            'organisation': 'named-entities',
            'organization': 'named-entities',
            'location': 'named-entities',
            'event': 'named-entities',
            'product': 'named-entities',
            'hardware': 'named-entities',
            'method': 'research-entities',
            'model': 'research-entities',
            'technology': 'research-entities',
            'technique': 'research-entities',
            'algorithm': 'research-entities',
            'framework': 'research-entities',
            'tool': 'research-entities',
            'dataset': 'research-entities',
            'topic': 'research-entities',
            'paper': 'content-types',
            'article': 'content-types',
            'book': 'content-types',
            'document': 'content-types'
        }

        # Cache information for each entity type
        for entity_type in distinct_entity_types:
            if not entity_type:
                continue

            sample_concept = concepts_col.find_one({"entity_type": entity_type})
            parent_category = category_mapping.get(entity_type, 'research-entities')

            self.valid_entity_types[entity_type] = {
                'entity_type': entity_type,
                'parent_category': parent_category,
                'icon': sample_concept.get('icon', '🏷️') if sample_concept else '🏷️',
                'color': sample_concept.get('color', '#6B7280') if sample_concept else '#6B7280',
                'sample_concept': sample_concept.get('display_name', '') if sample_concept else '',
                'validation_rules': {},
                'extraction_hints': []
            }
            self.entity_parent_map[entity_type] = entity_type

        print(f"Cached {len(self.valid_entity_types)} valid entity types from MongoDB")

    def get_entity_hierarchy_for_prompt(self) -> str:
        """Get entity hierarchy as string for LLM prompt"""
        hierarchy = []

        # Group by parent category
        categories = {}
        for entity_type, info in self.valid_entity_types.items():
            parent = info['parent_category']
            if parent not in categories:
                categories[parent] = []
            sample_name = info.get('sample_concept', entity_type)
            categories[parent].append(f"- {entity_type}: {sample_name}")

        # Format for prompt
        for category, types in categories.items():
            hierarchy.append(f"\n{category.replace('-', ' ').title()}:")
            hierarchy.extend(types)

        return '\n'.join(hierarchy)

    def extract_entities(self, text: str, article_id: Optional[int] = None) -> List[EntityExtraction]:
        """
        Extract entities from text using LLM Manager

        Args:
            text: Text to extract entities from
            article_id: Optional article ID for context

        Returns:
            List of EntityExtraction objects
        """
        import logging
        logger = logging.getLogger(__name__)

        if not text or len(text.strip()) < 10:
            logger.warning(f"🚨 Entity extraction skipped: Text too short ({len(text)} chars)")
            return []

        logger.info(f"🔍 Starting entity extraction with:")
        logger.info(f"  📄 Text length: {len(text)} characters")
        logger.info(f"  🤖 Model: {self.model_name}")
        logger.info(f"  ⚡ Task type: {self.task_type}")
        logger.info(f"  🆔 Article ID: {article_id}")

        # Get extraction prompt
        prompt_config = self.prompts.get('entity_extraction', {})
        system_prompt = prompt_config.get('system', '')
        user_template = prompt_config.get('user_template', '')

        # Add dynamic entity hierarchy to system prompt
        entity_hierarchy = self.get_entity_hierarchy_for_prompt()
        enhanced_system_prompt = system_prompt.replace(
            "The system has these EXISTING entity type parent concepts in MongoDB:",
            f"The system has these EXISTING entity type parent concepts in MongoDB:\n{entity_hierarchy}\n\nEach extracted entity should use one of these types:"
        )

        # Format user prompt
        text_to_send = text[:5000]  # Limit text length
        user_prompt = user_template.format(text=text_to_send)

        logger.info(f"📝 Prepared prompts (system: {len(enhanced_system_prompt)} chars, user: {len(user_prompt)} chars)")

        # Convert to OpenAI message format
        messages = [
            {"role": "system", "content": enhanced_system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        try:
            logger.info(f"🚀 Calling LLM Manager for entity extraction...")

            # Call LLM Manager with custom model if specified
            if self.custom_model:
                logger.info(f"🎯 Using custom model from UI: {self.custom_model}")
                response = self.llm_manager.completion_sync(
                    task_type=self.task_type,
                    messages=messages,
                    user_id=self.user_id,
                    override_params={'model': self.custom_model}  # Override with UI-selected model
                )
            else:
                response = self.llm_manager.completion_sync(
                    task_type=self.task_type,
                    messages=messages,
                    user_id=self.user_id
                )

            logger.info(f"✅ LLM response received")

            # Extract content
            content = response.choices[0].message.content
            logger.info(f"📤 Response length: {len(content)} chars")

            # Clean JSON if needed
            if '```json' in content:
                content = content.split('```json')[1].split('```')[0]
                logger.info(f"🧹 Cleaned JSON from code blocks")
            elif '```' in content:
                content = content.split('```')[1].split('```')[0]
                logger.info(f"🧹 Cleaned content from generic code blocks")
            content = content.strip()

            # Parse JSON response
            try:
                result = json.loads(content)
                logger.info(f"✅ JSON parsing successful")

                entities_data = result.get('entities', [])
                logger.info(f"📊 Found {len(entities_data)} raw entities in response")

            except json.JSONDecodeError as json_error:
                logger.error(f"🚨 JSON parsing failed: {json_error}")
                logger.error(f"  Content that failed: {content[:1000]}...")
                return []

            # Convert to EntityExtraction objects
            entities = []
            skipped_entities = []

            for i, entity_data in enumerate(entities_data):
                # Validate entity type
                entity_type = entity_data.get('type', '')
                if not self._is_valid_entity_type(entity_type):
                    skipped_entities.append(f"Invalid type '{entity_type}' for '{entity_data.get('text', '')}'")
                    continue

                # Check confidence threshold
                confidence = entity_data.get('confidence', 0.5)
                min_confidence = self.extraction_config.get('confidence_threshold', 0.6)
                if confidence < min_confidence:
                    skipped_entities.append(f"Low confidence {confidence} < {min_confidence} for '{entity_data.get('text', '')}'")
                    continue

                # Create entity
                entity = EntityExtraction(
                    text=entity_data.get('text', ''),
                    entity_type=entity_type,
                    confidence=confidence,
                    context=entity_data.get('context', ''),
                    normalized=entity_data.get('normalized', ''),
                    metadata={
                        'source': 'llm',
                        'model': self.model_name,
                        'article_id': article_id,
                        'extracted_at': datetime.now(timezone.utc).isoformat()
                    }
                )
                entities.append(entity)

            logger.info(f"✅ Successfully processed {len(entities)} entities")
            if skipped_entities:
                logger.info(f"⏭️ Skipped {len(skipped_entities)} entities:")
                for reason in skipped_entities[:5]:
                    logger.info(f"    {reason}")

            # Apply deduplication and limiting
            entities = self._deduplicate_entities(entities)
            entities = self._limit_entities_per_type(entities)

            logger.info(f"🎯 Final result: {len(entities)} entities extracted")
            for entity in entities[:5]:
                logger.info(f"    📌 {entity.text} ({entity.entity_type}, confidence: {entity.confidence:.2f})")

            return entities

        except Exception as e:
            logger.error(f"🚨 ERROR in entity extraction: {e}", exc_info=True)
            return []

    def _is_valid_entity_type(self, entity_type: str) -> bool:
        """Check if entity type is valid"""
        return entity_type in self.valid_entity_types

    def _deduplicate_entities(self, entities: List[EntityExtraction]) -> List[EntityExtraction]:
        """Remove duplicate entities, keeping highest confidence"""
        seen = {}
        for entity in entities:
            key = entity.normalized
            if key not in seen or seen[key].confidence < entity.confidence:
                seen[key] = entity
        return list(seen.values())

    def _limit_entities_per_type(self, entities: List[EntityExtraction]) -> List[EntityExtraction]:
        """Limit number of entities per type"""
        max_per_type = self.extraction_config.get('max_entities_per_type', 20)

        by_type = {}
        for entity in entities:
            if entity.entity_type not in by_type:
                by_type[entity.entity_type] = []
            by_type[entity.entity_type].append(entity)

        limited = []
        for entity_type, type_entities in by_type.items():
            sorted_entities = sorted(type_entities, key=lambda e: e.confidence, reverse=True)
            limited.extend(sorted_entities[:max_per_type])

        return limited

    def validate_entity(self, entity: EntityExtraction, context: str = "") -> Tuple[bool, Optional[str], str]:
        """
        Validate an extracted entity using LLM Manager

        Returns:
            (is_valid, suggested_type, reasoning)
        """
        prompt_config = self.prompts.get('entity_validation', {})
        system_prompt = prompt_config.get('system', '')
        user_template = prompt_config.get('user_template', '')

        user_prompt = user_template.format(
            text=entity.text,
            type=entity.entity_type,
            context=context or entity.context
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        try:
            # Use custom model if specified
            if self.custom_model:
                response = self.llm_manager.completion_sync(
                    task_type=self.task_type,
                    messages=messages,
                    user_id=self.user_id,
                    override_params={'model': self.custom_model}  # Override with UI-selected model
                )
            else:
                response = self.llm_manager.completion_sync(
                    task_type=self.task_type,
                    messages=messages,
                    user_id=self.user_id
                )

            content = response.choices[0].message.content

            # Parse JSON
            if '```json' in content:
                content = content.split('```json')[1].split('```')[0]
            result = json.loads(content.strip())

            return (
                result.get('valid', True),
                result.get('suggested_type'),
                result.get('reasoning', '')
            )
        except Exception as e:
            print(f"Error validating entity: {e}")
            return True, None, ""

    def save_entity_to_ontology(self, db: Any, entity: EntityExtraction,
                               parent_type: str, user: str = "system") -> Optional[Dict]:
        """
        Save an extracted entity to the MongoDB tag ontology

        Args:
            db: Database session (not used for MongoDB, kept for compatibility)
            entity: EntityExtraction object
            parent_type: Parent entity type
            user: User who triggered the extraction

        Returns:
            Created or existing concept as dict
        """
        from datetime import datetime
        import re
        from app.database.mongodb import get_database

        db_mongo = get_database()
        concepts_col = db_mongo.tag_concepts_v2

        # Generate slug
        slug = entity.normalized.lower().replace(" ", "_").replace("-", "_")
        slug = re.sub(r'[^a-z0-9_]', '', slug)

        # Check if exists
        existing = concepts_col.find_one({
            "$or": [
                {"slug": slug},
                {"display_name": {"$regex": f"^{re.escape(entity.text)}$", "$options": "i"}}
            ]
        })

        if existing:
            if not existing.get("description"):
                concepts_col.update_one(
                    {"_id": existing["_id"]},
                    {"$set": {"description": f"{entity.entity_type}: {entity.context[:200] if entity.context else ''}"}}
                )
            return existing

        # Get parent concept
        parent_concept_id = self.entity_parent_map.get(parent_type)
        if not parent_concept_id:
            parent_concept_id = f"c_et_{parent_type}"
            parent = concepts_col.find_one({"_id": parent_concept_id})
            if not parent:
                parent = concepts_col.find_one({"slug": "named-entities"})
                parent_concept_id = parent["_id"] if parent else None

        parent = concepts_col.find_one({"_id": parent_concept_id}) if parent_concept_id else None

        # Generate unique ID
        concept_id = f"c_{parent_type}_{slug}"
        counter = 1
        while concepts_col.find_one({"id": concept_id}):
            concept_id = f"c_{parent_type}_{slug}_{counter}"
            counter += 1

        # Get entity info
        entity_info = {}
        for category in self.ontology_schema.get('entity_types', {}).values():
            for child_key, child_data in category.get('children', {}).items():
                if parent_type == child_data.get('tag'):
                    entity_info = child_data
                    break
            if entity_info:
                break

        # Create concept
        concept = {
            "id": concept_id,
            "_id": concept_id,
            "slug": slug,
            "display_name": entity.text,
            "description": f"{entity.entity_type}: {entity.context[:200] if entity.context else ''}",
            "entity_type": parent_type,
            "parents": [parent_concept_id] if parent_concept_id else [],
            "children": [],
            "level": parent["level"] + 1 if parent else 0,
            "icon": entity_info.get("icon", "🏷️"),
            "color": entity_info.get("color", "#6B7280"),
            "usage_count": 0,
            "status": "active",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "metadata": {
                "created_by": user,
                "source": "entity_extraction",
                "confidence": entity.confidence,
                "llm_model": self.model_name,
                "context": entity.context[:500] if entity.context else "",
                "validated": False,
                "original_text": entity.text
            }
        }

        concepts_col.insert_one(concept)

        # Update parent
        if parent_concept_id:
            concepts_col.update_one(
                {"id": parent_concept_id},
                {"$addToSet": {"children": concept_id}}
            )

        return {
            "id": concept_id,
            "_id": concept_id,  # Include _id for compatibility with tag_instances
            "tag": slug,
            "slug": slug,
            "display_name": entity.text,
            "description": concept["description"]
        }

    def batch_save_entities(self, db: Any, entities: List[EntityExtraction],
                           user: str = "system") -> Dict[str, Any]:
        """Save multiple entities to the ontology"""
        stats = {
            "total": len(entities),
            "saved": 0,
            "existing": 0,
            "failed": 0,
            "by_type": {}
        }

        for entity in entities:
            parent_type = self._get_parent_type_for_entity(entity.entity_type)
            if not parent_type:
                stats["failed"] += 1
                continue

            try:
                concept = self.save_entity_to_ontology(db, entity, parent_type, user)
                if concept:
                    if concept.get("id"):
                        stats["saved"] += 1
                    else:
                        stats["existing"] += 1

                    if entity.entity_type not in stats["by_type"]:
                        stats["by_type"][entity.entity_type] = 0
                    stats["by_type"][entity.entity_type] += 1
                else:
                    stats["failed"] += 1
            except Exception as e:
                print(f"Error saving entity {entity.text}: {e}")
                stats["failed"] += 1

        return stats

    def _get_parent_type_for_entity(self, entity_type: str) -> Optional[str]:
        """Get the parent type for an entity type"""
        if entity_type in self.valid_entity_types:
            return entity_type

        for valid_type in self.valid_entity_types:
            if valid_type.lower() == entity_type.lower():
                return valid_type

        return None
