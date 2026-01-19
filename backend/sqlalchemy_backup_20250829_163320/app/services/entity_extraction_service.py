"""
AI-powered entity extraction service for automatic annotation
"""
import json
import os
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from dotenv import load_dotenv
import hashlib

from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from app.models import TagConcept, TagSynonym, get_db
from app.models.tag_ontology import TagMapping

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
        # Just replace spaces with hyphens, preserve capitalization
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
    """Service for extracting entities from text using LLMs"""
    
    def __init__(self, use_fast_model: bool = False):
        """Initialize with LLM configuration"""
        # Load configurations
        with open('llm.json', 'r') as f:
            self.llm_config = json.load(f)
        
        with open('prompts_config.json', 'r') as f:
            self.prompts = json.load(f)
        
        with open('top_level.json', 'r') as f:
            self.ontology_schema = json.load(f)
        
        # Select model configuration
        model_key = 'entity_extraction_fast' if use_fast_model else 'entity_extraction'
        model_config = self.llm_config['models'][model_key]
        
        # Initialize LLM based on provider
        if model_config['provider'] == 'anthropic':
            api_key = os.getenv('ANTHROPIC_API_KEY')
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY not found")
            
            self.llm = ChatAnthropic(
                model=model_config['model'],
                anthropic_api_key=api_key,
                temperature=model_config.get('temperature', 0.1),
                max_tokens=model_config.get('max_tokens', 2000)
            )
        elif model_config['provider'] == 'openai':
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                raise ValueError("OPENAI_API_KEY not found")
            
            self.llm = ChatOpenAI(
                model=model_config['model'],
                openai_api_key=api_key,
                temperature=model_config.get('temperature', 0.1),
                max_tokens=model_config.get('max_tokens', 1000)
            )
        else:
            raise ValueError(f"Unsupported provider: {model_config['provider']}")
        
        self.model_name = model_config['model']
        self.extraction_config = self.ontology_schema.get('extraction_config', {})
        
        # Cache valid entity types from MongoDB
        self._cache_valid_entity_types()
    
    def _cache_valid_entity_types(self):
        """Cache valid entity types from MongoDB concept hierarchy"""
        from pymongo import MongoClient
        
        # Connect to MongoDB
        client = MongoClient("mongodb://localhost:27017/")
        db = client.smarttrendtracer
        concepts_col = db.tag_concepts_v2
        
        # Get all entity type concepts (children of named-entities and research-entities)
        self.valid_entity_types = {}
        self.entity_parent_map = {}
        
        # Find the main entity categories
        entity_categories = concepts_col.find({
            "slug": {"$in": ["named-entities", "research-entities", "content-types"]}
        })
        
        for category in entity_categories:
            # Get all children of this category
            for child_id in category.get('children', []):
                child = concepts_col.find_one({"_id": child_id})
                if child:
                    entity_type = child.get('entity_type', child['slug'])
                    self.valid_entity_types[entity_type] = {
                        'id': child['_id'],
                        'slug': child['slug'],
                        'display_name': child['display_name'],
                        'parent_category': category['slug'],
                        'icon': child.get('icon', '🏷️'),
                        'color': child.get('color', '#6B7280'),
                        'validation_rules': child.get('metadata', {}).get('validation_rules', {}),
                        'extraction_hints': child.get('metadata', {}).get('extraction_hints', [])
                    }
                    self.entity_parent_map[entity_type] = child['_id']
        
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
            categories[parent].append(f"- {entity_type}: {info['display_name']}")
        
        # Format for prompt
        for category, types in categories.items():
            hierarchy.append(f"\n{category.replace('-', ' ').title()}:")
            hierarchy.extend(types)
        
        return '\n'.join(hierarchy)
    
    def extract_entities(self, text: str, article_id: Optional[int] = None) -> List[EntityExtraction]:
        """
        Extract entities from text using LLM
        
        Args:
            text: Text to extract entities from
            article_id: Optional article ID for context
            
        Returns:
            List of EntityExtraction objects
        """
        if not text or len(text.strip()) < 10:
            return []
        
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
        user_prompt = user_template.format(text=text[:5000])  # Limit text length
        
        messages = [
            SystemMessage(content=enhanced_system_prompt),
            HumanMessage(content=user_prompt)
        ]
        
        try:
            # Call LLM
            response = self.llm.invoke(messages)
            
            # Parse response
            if hasattr(response, 'content'):
                content = response.content
            else:
                content = str(response)
            
            # Clean JSON if needed
            if isinstance(content, str):
                if '```json' in content:
                    content = content.split('```json')[1].split('```')[0]
                elif '```' in content:
                    content = content.split('```')[1].split('```')[0]
                content = content.strip()
            
            # Parse JSON response
            result = json.loads(content)
            entities_data = result.get('entities', [])
            
            # Convert to EntityExtraction objects
            entities = []
            for entity_data in entities_data:
                # Validate entity type
                entity_type = entity_data.get('type', '')
                if not self._is_valid_entity_type(entity_type):
                    continue
                
                # Check confidence threshold
                confidence = entity_data.get('confidence', 0.5)
                min_confidence = self.extraction_config.get('confidence_threshold', 0.6)
                if confidence < min_confidence:
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
            
            # Apply deduplication
            entities = self._deduplicate_entities(entities)
            
            # Limit number of entities per type
            entities = self._limit_entities_per_type(entities)
            
            return entities
            
        except Exception as e:
            print(f"Error extracting entities: {e}")
            return []
    
    def _is_valid_entity_type(self, entity_type: str) -> bool:
        """Check if entity type is valid according to MongoDB concept hierarchy"""
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
        
        # Group by type
        by_type = {}
        for entity in entities:
            if entity.entity_type not in by_type:
                by_type[entity.entity_type] = []
            by_type[entity.entity_type].append(entity)
        
        # Sort by confidence and limit
        limited = []
        for entity_type, type_entities in by_type.items():
            sorted_entities = sorted(type_entities, key=lambda e: e.confidence, reverse=True)
            limited.extend(sorted_entities[:max_per_type])
        
        return limited
    
    def validate_entity(self, entity: EntityExtraction, context: str = "") -> Tuple[bool, Optional[str], str]:
        """
        Validate an extracted entity using LLM
        
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
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
        
        try:
            response = self.llm.invoke(messages)
            content = response.content if hasattr(response, 'content') else str(response)
            
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
            return True, None, ""  # Default to valid if validation fails
    
    def save_entity_to_ontology(self, db: Session, entity: EntityExtraction, 
                               parent_type: str, user: str = "system") -> Optional[Dict]:
        """
        Save an extracted entity to the MongoDB tag ontology
        
        Args:
            db: Database session (not used for MongoDB, kept for compatibility)
            entity: EntityExtraction object
            parent_type: Parent entity type from schema (e.g., 'person', 'organisation')
            user: User who triggered the extraction
            
        Returns:
            Created or existing concept as dict
        """
        from pymongo import MongoClient
        from datetime import datetime
        import re
        
        # Connect to MongoDB
        client = MongoClient("mongodb://localhost:27017/")
        db_mongo = client.smarttrendtracer
        concepts_col = db_mongo.tag_concepts_v2
        
        # Generate a proper slug for the entity
        slug = entity.normalized.lower().replace(" ", "_").replace("-", "_")
        slug = re.sub(r'[^a-z0-9_]', '', slug)
        
        # Check if entity already exists (case-insensitive)
        existing = concepts_col.find_one({
            "$or": [
                {"slug": slug},
                {"display_name": {"$regex": f"^{re.escape(entity.text)}$", "$options": "i"}}
            ]
        })
        
        if existing:
            # Update metadata if needed
            if not existing.get("description"):
                concepts_col.update_one(
                    {"_id": existing["_id"]},
                    {"$set": {"description": f"{entity.entity_type}: {entity.context[:200] if entity.context else ''}"}}
                )
            return existing
        
        # Get parent concept ID from cached map
        parent_concept_id = self.entity_parent_map.get(parent_type)
        
        if not parent_concept_id:
            # If not in map, try to find it with c_et_ prefix
            parent_concept_id = f"c_et_{parent_type}"
            parent = concepts_col.find_one({"_id": parent_concept_id})
            
            if not parent:
                # Fallback to named-entities if no specific parent found
                print(f"Parent type {parent_type} not found in cache, using named-entities as fallback")
                parent = concepts_col.find_one({"slug": "named-entities"})
                if parent:
                    parent_concept_id = parent["_id"]
                else:
                    print(f"No suitable parent found, creating at root level")
                    parent_concept_id = None
        
        # Get parent document for level calculation
        parent = concepts_col.find_one({"_id": parent_concept_id}) if parent_concept_id else None
        
        # Generate unique ID for the new concept
        # Use a combination of entity type and slug
        concept_id = f"c_{parent_type}_{slug}"
        
        # Ensure ID is unique
        counter = 1
        while concepts_col.find_one({"id": concept_id}):
            concept_id = f"c_{parent_type}_{slug}_{counter}"
            counter += 1
        
        # Get entity type info from schema
        entity_info = {}
        for category in self.ontology_schema.get('entity_types', {}).values():
            for child_key, child_data in category.get('children', {}).items():
                if parent_type == child_data.get('tag'):
                    entity_info = child_data
                    break
            if entity_info:
                break
        
        # Create new concept
        concept = {
            "id": concept_id,
            "_id": concept_id,  # Use same ID for MongoDB _id
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
        
        # Insert the new concept
        concepts_col.insert_one(concept)
        
        # Update parent's children list if parent exists
        if parent_concept_id:
            concepts_col.update_one(
                {"id": parent_concept_id},
                {"$addToSet": {"children": concept_id}}
            )
        
        # Return as dict for compatibility
        return {
            "id": concept_id,
            "tag": slug,
            "display_name": entity.text,
            "description": concept["description"]
        }
    
    def batch_save_entities(self, db: Session, entities: List[EntityExtraction], 
                           user: str = "system") -> Dict[str, Any]:
        """
        Save multiple entities to the ontology
        
        Returns:
            Statistics about the save operation
        """
        stats = {
            "total": len(entities),
            "saved": 0,
            "existing": 0,
            "failed": 0,
            "by_type": {}
        }
        
        for entity in entities:
            # Determine parent type
            parent_type = self._get_parent_type_for_entity(entity.entity_type)
            if not parent_type:
                stats["failed"] += 1
                continue
            
            try:
                concept = self.save_entity_to_ontology(db, entity, parent_type, user)
                if concept:
                    if concept.id:
                        stats["saved"] += 1
                    else:
                        stats["existing"] += 1
                    
                    # Track by type
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
        """Get the parent type for an entity type from cached MongoDB data"""
        # The entity type itself is valid if it's in our valid types
        if entity_type in self.valid_entity_types:
            return entity_type
        
        # Try to find a matching entity type (case-insensitive)
        for valid_type in self.valid_entity_types:
            if valid_type.lower() == entity_type.lower():
                return valid_type
        
        return None