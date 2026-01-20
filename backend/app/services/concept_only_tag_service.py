"""
Concept-only tag service for MongoDB.
All tags are now concepts with IDs. No more orphan tags or text-based tags.
"""

from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime
from pymongo import ASCENDING, DESCENDING
from bson import ObjectId
import logging
import re

logger = logging.getLogger(__name__)

class ConceptOnlyTagService:
    """Service for managing tags as concepts in MongoDB"""
    
    _instance = None
    _client = None
    _db = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            from app.database.mongodb import get_client, get_database

            cls._client = get_client()
            cls._db = get_database()
        return cls._instance

    # ------------------------------
    # Helpers
    # ------------------------------
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

    def _concept_instance_exists(self, content_type: str, content_id: str, concept_ref) -> bool:
        """Check whether a tag instance already exists for content/concept."""
        query = {
            'content_type': content_type,
            'content_id': str(content_id)
        }

        if isinstance(concept_ref, ObjectId):
            if self.tag_instances.find_one({**query, 'concept_id': concept_ref}):
                return True
            # Also check string representation for legacy records
            if self.tag_instances.find_one({**query, 'concept_id': str(concept_ref)}):
                return True
        else:
            if self.tag_instances.find_one({**query, 'concept_id': concept_ref}):
                return True

        return False

    def _insert_tag_instance(self, content_type: str, content_id: str, concept_ref) -> bool:
        """Insert tag instance, handling duplicates gracefully."""
        tag_instance = {
            'content_type': content_type,
            'content_id': str(content_id),
            'concept_id': concept_ref,
            'created_at': datetime.now().isoformat(),
            'source': 'api',
            'tag_type': 'concept',
            'confidence': 1.0
        }

        try:
            result = self.tag_instances.insert_one(tag_instance)
            return bool(result.inserted_id)
        except Exception as exc:
            # Duplicate assignments are acceptable; surface other errors
            message = str(exc).lower()
            if 'duplicate key' in message or 'e11000' in message:
                logger.info(
                    "Concept %s already attached to %s %s",
                    concept_ref,
                    content_type,
                    content_id
                )
                return True
            logger.error(
                "Failed to insert tag instance for %s %s and concept %s: %s",
                content_type,
                content_id,
                concept_ref,
                exc
            )
            return False

    @property
    def db(self):
        """Get database instance"""
        return self._db
    
    @property
    def tag_instances(self):
        """Get tag_instances collection"""
        return self.db.tag_instances
    
    @property
    def tag_concepts(self):
        """Get tag_concepts_v2 collection"""
        return self.db.tag_concepts_v2
    
    @property
    def tag_aliases(self):
        """Get tag_aliases_v2 collection"""
        return self.db.tag_aliases_v2
    
    def _generate_concept_id(self) -> str:
        """Generate a unique concept ID in format c_XXXX"""
        last_concept = self.tag_concepts.find_one(
            {"id": {"$regex": "^c_\\d+$"}},
            sort=[("id", -1)]
        )
        
        if last_concept and 'id' in last_concept:
            last_num = int(last_concept['id'].split('_')[1])
            new_num = last_num + 1
        else:
            new_num = 1000
        
        while True:
            new_id = f"c_{new_num:04d}"
            if not self.tag_concepts.find_one({"id": new_id}):
                return new_id
            new_num += 1
    
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
            "created_at": datetime.now().isoformat(),
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
        except:
            return None
    
    def get_tags_for_content(self, content_type: str, content_id: str) -> List[Dict]:
        """
        Get all tags (as concepts) for a specific content item.
        Returns list of concept dictionaries.
        """
        try:
            # Get tag instances
            instances = list(self.tag_instances.find({
                'content_type': content_type,
                'content_id': str(content_id)
            }))
            
            # Get unique concept IDs
            concept_ids = list(set(inst['concept_id'] for inst in instances if inst.get('concept_id')))
            
            # Fetch all concepts at once
            concepts = []
            if concept_ids:
                # Convert to ObjectIds
                object_ids = []
                for cid in concept_ids:
                    try:
                        if len(cid) == 24:
                            object_ids.append(ObjectId(cid))
                    except:
                        pass
                
                if object_ids:
                    concept_docs = self.tag_concepts.find({"_id": {"$in": object_ids}})
                    for doc in concept_docs:
                        # Convert any ObjectIds to strings
                        parents = doc.get('parents', [])
                        if parents:
                            parents = [str(p) if hasattr(p, '__str__') else p for p in parents]
                        
                        concepts.append({
                            "concept_id": str(doc['_id']),
                            "id": doc.get('id', f"c_{str(doc['_id'])[:4]}"),
                            "slug": doc.get('slug', ''),
                            "display_name": doc.get('display_name', doc.get('name', '')),
                            "entity_type": doc.get('entity_type', 'topic'),
                            "description": doc.get('description', ''),
                            "parents": parents
                        })
            
            return concepts
            
        except Exception as e:
            logger.error(f"Error getting tags for {content_type} {content_id}: {e}")
            return []
    
    def add_tag(self, content_type: str, content_id: str, text: str, preserve_display_name: bool = True) -> Tuple[bool, str]:
        """
        Add a tag to content. Creates concept if needed.
        Returns (success, concept_id)
        
        Args:
            preserve_display_name: If True, preserve exact text as display_name (for user input)
        """
        try:
            # First check if concept exists (don't create yet)
            slug = self._normalize_to_slug(text)
            
            # Check if concept exists with this slug
            existing_concept = self.tag_concepts.find_one({"slug": slug})
            if existing_concept:
                concept_id = str(existing_concept['_id'])
                concept_existed = True
            else:
                # Check aliases
                alias = self.tag_aliases.find_one({"alias": slug})
                if alias:
                    concept_id = alias['concept_id']
                    concept_existed = True
                else:
                    concept_id = None
                    concept_existed = False
            
            # If concept doesn't exist, we'll create it only after ensuring we can create the tag_instance
            if not concept_existed:
                # Prepare the new concept but don't insert yet
                if preserve_display_name:
                    display_name = text.strip()
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
                    "created_at": datetime.now().isoformat(),
                    "created_by": "concept_service",
                    "auto_generated": True
                }
                
                # Create concept first
                try:
                    result = self.tag_concepts.insert_one(new_concept)
                    concept_id = str(result.inserted_id)
                    logger.info(f"Created concept: {display_name} (id: {new_concept['id']})")
                except Exception as e:
                    logger.error(f"Failed to create concept: {e}")
                    return False, None
            
            # Check if already tagged
            existing_tag = self.tag_instances.find_one({
                'content_type': content_type,
                'content_id': str(content_id),
                'concept_id': ObjectId(concept_id) if len(concept_id) == 24 else concept_id
            })
            
            if existing_tag:
                logger.info(f"Content already has this concept: {concept_id}")
                return True, concept_id
            
            # Create tag instance
            tag_instance = {
                'content_type': content_type,
                'content_id': str(content_id),
                'concept_id': ObjectId(concept_id) if len(concept_id) == 24 else concept_id,
                'created_at': datetime.now().isoformat(),
                'source': 'api',
                'tag_type': 'concept',
                'confidence': 1.0
            }
            
            try:
                result = self.tag_instances.insert_one(tag_instance)
                
                if result.inserted_id:
                    logger.info(f"Added concept {concept_id} to {content_type} {content_id}")
                    return True, concept_id
                else:
                    # If we created a new concept but failed to create tag_instance, delete the concept
                    if not concept_existed:
                        self.tag_concepts.delete_one({"_id": ObjectId(concept_id)})
                        logger.warning(f"Rolled back concept creation due to tag_instance failure")
                    return False, None
                    
            except Exception as e:
                # Check if it's a duplicate key error (E11000)
                if 'E11000' in str(e) or 'duplicate key' in str(e).lower():
                    logger.info(f"Concept {concept_id} already attached to {content_type} {content_id} (caught duplicate key error)")
                    # This is actually fine - the concept is already attached
                    return True, concept_id
                else:
                    logger.error(f"Failed to create tag_instance: {e}")
                    # Rollback concept creation if it was new
                    if not concept_existed:
                        try:
                            self.tag_concepts.delete_one({"_id": ObjectId(concept_id)})
                            logger.warning(f"Rolled back concept creation due to tag_instance error: {e}")
                        except:
                            logger.error(f"Failed to rollback concept creation")
                    return False, None
            
        except Exception as e:
            logger.error(f"Error adding tag: {e}")
            return False, None

    def add_concept_to_content(
        self,
        *,
        content_type: str,
        content_id: str,
        concept_name: Optional[str] = None,
        concept_slug: Optional[str] = None,
        concept_id: Optional[str] = None,
        context: Optional[str] = None,
        preserve_display_name: bool = True
    ) -> Tuple[bool, Optional[str]]:
        """Attach a concept to content, creating it if needed."""

        # context is currently unused but accepted for API compatibility
        _ = context

        try:
            # Create or reuse concept based on provided identifiers
            if concept_name:
                return self.add_tag(
                    content_type=content_type,
                    content_id=content_id,
                    text=concept_name,
                    preserve_display_name=preserve_display_name
                )

            concept_doc = None

            if concept_id:
                concept_doc = self.get_concept_by_id(concept_id)
            elif concept_slug:
                concept_doc = self._find_concept_by_slug_or_alias(concept_slug)

            if not concept_doc:
                logger.error(
                    "Unable to resolve concept for %s %s (concept_id=%s, concept_slug=%s)",
                    content_type,
                    content_id,
                    concept_id,
                    concept_slug
                )
                return False, None

            concept_ref = self._normalize_concept_identifier(concept_doc.get('_id'))
            concept_id_str = str(concept_ref) if isinstance(concept_ref, ObjectId) else str(concept_ref)

            if self._concept_instance_exists(content_type, content_id, concept_ref):
                return True, concept_id_str

            inserted = self._insert_tag_instance(content_type, content_id, concept_ref)

            # If storing as ObjectId failed (e.g., legacy data), retry with string representation
            if not inserted and isinstance(concept_ref, ObjectId):
                inserted = self._insert_tag_instance(content_type, content_id, concept_id_str)

            return inserted, concept_id_str if inserted else None

        except Exception as exc:
            logger.error(
                "Error attaching concept to %s %s: %s",
                content_type,
                content_id,
                exc
            )
            return False, None

    def remove_tag(self, content_type: str, content_id: str, concept_id: str) -> bool:
        """
        Remove a tag (concept) from content.
        """
        try:
            # Convert concept_id to ObjectId if it's a valid ObjectId string
            concept_id_obj = concept_id
            if isinstance(concept_id, str) and len(concept_id) == 24:
                try:
                    concept_id_obj = ObjectId(concept_id)
                except:
                    concept_id_obj = concept_id
            
            result = self.tag_instances.delete_one({
                'content_type': content_type,
                'content_id': str(content_id),
                'concept_id': concept_id_obj
            })
            
            if result.deleted_count > 0:
                logger.info(f"Removed concept {concept_id} from {content_type} {content_id}")
                return True
            
            # If not found with ObjectId, try with string
            if isinstance(concept_id_obj, ObjectId):
                result = self.tag_instances.delete_one({
                    'content_type': content_type,
                    'content_id': str(content_id),
                    'concept_id': str(concept_id)
                })
                
                if result.deleted_count > 0:
                    logger.info(f"Removed concept {concept_id} (as string) from {content_type} {content_id}")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error removing tag: {e}")
            return False

    def remove_concept_from_content(
        self,
        *,
        content_type: str,
        content_id: str,
        concept_id: Optional[str] = None,
        concept_slug: Optional[str] = None,
        concept_name: Optional[str] = None
    ) -> bool:
        """Detach a concept from the specified content."""

        target_id = concept_id

        if not target_id and concept_slug:
            concept = self._find_concept_by_slug_or_alias(concept_slug)
            if concept:
                target_id = str(concept.get('_id'))

        if not target_id and concept_name:
            concept = self._find_concept_by_slug_or_alias(concept_name)
            if concept:
                target_id = str(concept.get('_id'))

        if not target_id:
            logger.warning(
                "Unable to resolve concept to remove for %s %s",
                content_type,
                content_id
            )
            return False

        return self.remove_tag(content_type, content_id, target_id)

    def remove_all_concepts_from_content(self, content_id: str, content_type: str) -> int:
        """Remove all concept assignments from the specified content."""

        try:
            result = self.tag_instances.delete_many({
                'content_type': content_type,
                'content_id': str(content_id)
            })
            removed = result.deleted_count if result else 0
            logger.info(
                "Removed %s concept assignments from %s %s",
                removed,
                content_type,
                content_id
            )
            return removed
        except Exception as exc:
            logger.error(
                "Failed to remove concepts from %s %s: %s",
                content_type,
                content_id,
                exc
            )
            return 0

    def get_concepts_for_content(self, content_id: str, content_type: str) -> List[Dict]:
        """Compatibility helper – alias to get_tags_for_content."""
        return self.get_tags_for_content(content_type, content_id)

    def get_all_concepts_with_counts(self, content_type: Optional[str] = None, include_unused: bool = False) -> List[Dict]:
        """
        Get all concepts with their usage counts.
        
        Args:
            content_type: Filter by content type (tweet, paper, article)
            include_unused: If True, include concepts with no annotations (important for reorganization!)
        """
        try:
            if include_unused and not content_type:
                # Get ALL concepts from tag_concepts_v2, including those without annotations
                # This is critical for Tag Reorganizer to see the full hierarchy
                all_concepts = list(self.tag_concepts.find())
                results = []
                
                for concept in all_concepts:
                    concept_id = concept['_id']  # Keep as ObjectId
                    concept_id_str = str(concept_id)
                    
                    # Count annotations for this concept (use ObjectId, not string)
                    count = self.tag_instances.count_documents({'concept_id': concept_id})
                    
                    # Get content types if there are annotations
                    content_types = []
                    if count > 0:
                        content_types = self.tag_instances.distinct('content_type', {'concept_id': concept_id})
                    
                    # Convert ObjectIds in parents and children to strings
                    parents = concept.get('parents', [])
                    if parents:
                        parents = [str(p) if hasattr(p, '__str__') else p for p in parents]
                    
                    children = concept.get('children', [])
                    if children:
                        children = [str(c) if hasattr(c, '__str__') else c for c in children]
                    
                    results.append({
                        '_id': str(concept['_id']),
                        'concept_id': concept_id_str,
                        'id': concept.get('id', f"c_{concept_id_str[:4]}"),
                        'slug': concept.get('slug', ''),
                        'display_name': concept.get('display_name', concept.get('name', '')),
                        'count': count,
                        'content_types': content_types,
                        'entity_type': concept.get('entity_type', 'concept'),
                        'parents': parents,
                        'children': children,
                        'is_parent': len(children) > 0,
                        'is_root': len(parents) == 0
                    })
                
                # Sort by count (used concepts first) then by name
                results.sort(key=lambda x: (-x['count'], x['display_name']))
                return results
            
            # Original behavior - only return concepts with annotations
            # Build aggregation pipeline
            pipeline = []
            
            if content_type:
                pipeline.append({'$match': {'content_type': content_type}})
            
            pipeline.extend([
                {'$group': {
                    '_id': '$concept_id',
                    'count': {'$sum': 1},
                    'content_types': {'$addToSet': '$content_type'}
                }},
                {'$sort': {'count': -1}}
            ])
            
            # Get counts
            counts = list(self.tag_instances.aggregate(pipeline))
            
            # Get concept details
            # Handle both ObjectId and string-based concept IDs
            object_ids = []
            string_ids = []
            
            for c in counts:
                if c['_id']:
                    # Check if it's already an ObjectId
                    if isinstance(c['_id'], ObjectId):
                        object_ids.append(c['_id'])
                    else:
                        # Convert to string to check if it could be an ObjectId
                        id_str = str(c['_id'])
                        if len(id_str) == 24:
                            # Try to convert to ObjectId
                            try:
                                object_ids.append(ObjectId(id_str))
                            except:
                                # If it fails to convert, treat as string ID
                                string_ids.append(c['_id'])
                        else:
                            # It's a string-based ID like 'c_org_deepmind'
                            string_ids.append(c['_id'])
            
            concepts_map = {}
            
            # Query for ObjectId-based concepts
            if object_ids:
                for concept in self.tag_concepts.find({'_id': {'$in': object_ids}}):
                    concepts_map[str(concept['_id'])] = concept
            
            # Query for string ID-based concepts
            if string_ids:
                for concept in self.tag_concepts.find({'id': {'$in': string_ids}}):
                    # Use the 'id' field as the key for string-based IDs
                    # BUT also check if this concept is already in the map by its ObjectId
                    obj_id_str = str(concept['_id'])
                    if obj_id_str not in concepts_map:
                        # Only add if not already present via ObjectId lookup
                        concepts_map[concept['id']] = concept
            
            # Combine results
            results = []
            seen_concepts = set()  # Track which concepts we've already added
            
            for count_doc in counts:
                concept_id = count_doc['_id']
                # Convert ObjectId to string for lookup in concepts_map
                lookup_key = str(concept_id) if isinstance(concept_id, ObjectId) else concept_id
                if lookup_key in concepts_map:
                    concept = concepts_map[lookup_key]
                    # Use the concept's ObjectId as the unique key
                    unique_key = str(concept['_id'])
                    
                    # Only add if we haven't seen this concept yet
                    if unique_key not in seen_concepts:
                        seen_concepts.add(unique_key)
                        results.append({
                            'concept_id': unique_key,  # Use the actual ObjectId as string
                            'id': concept.get('id', f"c_{unique_key[:4]}"),
                            'slug': concept.get('slug', ''),
                            'display_name': concept.get('display_name', concept.get('name', '')),
                            'count': count_doc['count'],
                            'content_types': count_doc['content_types']
                        })
            
            return results
            
        except Exception as e:
            logger.error(f"Error getting concept counts: {e}")
            return []
    
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
