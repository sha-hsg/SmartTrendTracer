from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime, timezone
from bson import ObjectId
import logging

logger = logging.getLogger(__name__)


class ConceptTaggingMixin:

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
            'created_at': datetime.now(timezone.utc),
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

            # Get unique concept IDs (filter out sentinel entries where concept_id is None)
            concept_ids = list(set(inst['concept_id'] for inst in instances if inst.get('concept_id') is not None))

            # Fetch all concepts at once via the central resolver (handles
            # ObjectId, stringified-ObjectId and legacy slug _ids alike — the
            # previous len(cid)==24 check raised TypeError on ObjectIds and
            # silently returned [] for ~98% of tagged content)
            concepts = []
            if concept_ids:
                docs_by_id = self.get_concepts_by_ids(concept_ids)
                seen = set()
                for doc in docs_by_id.values():
                    if str(doc['_id']) in seen:
                        continue
                    seen.add(str(doc['_id']))
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
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "created_by": "concept_service",
                    "auto_generated": True
                }

                # Create concept first. Under concurrency two workers can race
                # on the same new slug (unique index) — on duplicate, adopt the
                # winner's concept instead of dropping the tag.
                try:
                    result = self.tag_concepts.insert_one(new_concept)
                    concept_id = str(result.inserted_id)
                    logger.info(f"Created concept: {display_name} (id: {new_concept['id']})")
                except Exception as e:
                    winner = self.tag_concepts.find_one({"slug": slug})
                    if winner is not None:
                        concept_id = str(winner['_id'])
                        logger.info(f"Concept '{slug}' created concurrently; reusing {concept_id}")
                    else:
                        logger.error(f"Failed to create concept: {e}")
                        return False, None

            # Check if already tagged
            from app.database.mongodb import safe_object_id, concept_id_query_variants
            native_concept_id = safe_object_id(concept_id) or concept_id
            existing_tag = self.tag_instances.find_one({
                'content_type': content_type,
                'content_id': str(content_id),
                'concept_id': {'$in': concept_id_query_variants(concept_id)}
            })

            if existing_tag:
                logger.info(f"Content already has this concept: {concept_id}")
                return True, concept_id

            # Create tag instance
            tag_instance = {
                'content_type': content_type,
                'content_id': str(content_id),
                'concept_id': native_concept_id,
                'created_at': datetime.now(timezone.utc),
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
                        except Exception:
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
                except Exception:
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

    def get_instances_by_concept_id(
        self,
        concept_id,
        content_type: Optional[str] = None,
        limit: int = 0,
    ) -> List[Dict]:
        """Get tag instances for a given concept.

        Args:
            concept_id: Concept ObjectId or string
            content_type: Optional filter ('tweet', 'article', 'paper')
            limit: Max results (0 = unlimited)

        Returns:
            List of tag instance documents
        """
        oid = self._normalize_concept_identifier(concept_id)
        query: Dict[str, Any] = {"concept_id": oid}
        if content_type:
            query["content_type"] = content_type
        cursor = self.tag_instances.find(query)
        if limit:
            cursor = cursor.limit(limit)
        return list(cursor)

    def get_tagged_content_ids(
        self,
        concept_ids: List,
        content_type: str,
    ) -> List[str]:
        """Get content IDs tagged with any of the given concepts.

        Args:
            concept_ids: List of concept ObjectIds or strings
            content_type: 'tweet', 'article', or 'paper'

        Returns:
            List of content ID strings
        """
        if not concept_ids:
            return []
        oids = [self._normalize_concept_identifier(c) for c in concept_ids]
        oids = [o for o in oids if o is not None]
        if not oids:
            return []
        instances = self.tag_instances.find({
            "content_type": content_type,
            "concept_id": {"$in": oids},
        })
        return [inst["content_id"] for inst in instances]

    def get_concepts_for_content(self, content_id: str, content_type: str) -> List[Dict]:
        """Compatibility helper -- alias to get_tags_for_content."""
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
                            except Exception:
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
