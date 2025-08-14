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
        
        # Format user prompt
        user_prompt = user_template.format(text=text[:5000])  # Limit text length
        
        messages = [
            SystemMessage(content=system_prompt),
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
        """Check if entity type is valid according to schema"""
        for category in self.ontology_schema['entity_types'].values():
            if entity_type == category.get('tag'):
                return True
            for child in category.get('children', {}).values():
                if entity_type == child.get('tag'):
                    return True
        return False
    
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
                               parent_type: str, user: str = "system") -> Optional[TagConcept]:
        """
        Save an extracted entity to the tag ontology
        
        Args:
            db: Database session
            entity: EntityExtraction object
            parent_type: Parent entity type from schema (e.g., 'person', 'organisation')
            user: User who triggered the extraction
            
        Returns:
            Created or existing TagConcept
        """
        # Check if entity already exists (case-insensitive)
        from sqlalchemy import func
        existing = db.query(TagConcept).filter(
            func.lower(TagConcept.tag) == func.lower(entity.normalized)
        ).first()
        
        if existing:
            # Update metadata if needed
            if not existing.description:
                existing.description = f"{entity.entity_type}: {entity.context}"
            return existing
        
        # Find the appropriate parent concept based on entity type
        # Entity types from top_level.json are organized under parent categories
        parent = None
        parent_category = None
        
        # Map entity types to their parent categories from top_level.json
        for category_key, category_data in self.ontology_schema.get('entity_types', {}).items():
            if parent_type == category_data.get('tag'):
                # Direct parent category match
                parent = db.query(TagConcept).filter(
                    TagConcept.tag == parent_type
                ).first()
                parent_category = category_key
                break
            
            # Check if parent_type is a child of this category
            children = category_data.get('children', {})
            for child_key, child_data in children.items():
                if parent_type == child_data.get('tag'):
                    # This is a child entity type, use it as parent
                    parent = db.query(TagConcept).filter(
                        TagConcept.tag == parent_type
                    ).first()
                    
                    # If the specific entity type doesn't exist as a concept,
                    # fall back to the parent category
                    if not parent:
                        parent = db.query(TagConcept).filter(
                            TagConcept.tag == category_data.get('tag')
                        ).first()
                    parent_category = category_key
                    break
            
            if parent:
                break
        
        if not parent:
            print(f"Parent type {parent_type} not found in ontology, checking for fallback...")
            # Try to find any existing top-level category as fallback
            # Prefer "named-entities" as a general fallback
            parent = db.query(TagConcept).filter(
                TagConcept.tag == 'named-entities'
            ).first()
            
            if not parent:
                # Last resort: create at root level (no parent)
                print(f"No suitable parent found, creating at root level")
                parent_id = None
                level = 0
            else:
                parent_id = parent.id
                level = parent.level + 1
        else:
            parent_id = parent.id
            level = parent.level + 1
        
        # Create new concept
        concept = TagConcept(
            tag=entity.normalized,
            display_name=entity.text,
            description=f"{entity.entity_type}: {entity.context[:200] if entity.context else ''}",
            parent_id=parent_id,
            level=level,
            path="/"  # Will be updated
        )
        
        db.add(concept)
        db.flush()
        
        # Update path
        concept.update_path(db)
        
        # Add metadata as JSON in description (could be extended with proper metadata table)
        metadata = {
            "created_by": user,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "source": "llm",
            "confidence": entity.confidence,
            "llm_model": self.model_name,
            "context": entity.context[:500] if entity.context else "",  # Limit context size
            "validated": False,
            "entity_type": entity.entity_type
        }
        
        # Store metadata in a more structured way
        concept.description = f"Auto-extracted {entity.entity_type}: {entity.text}"
        
        db.commit()
        return concept
    
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
        """Get the parent type for an entity type from schema"""
        for category in self.ontology_schema['entity_types'].values():
            for child_key, child in category.get('children', {}).items():
                if child.get('tag') == entity_type:
                    return entity_type  # The entity type itself is the parent for instances
        return None