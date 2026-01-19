"""
Orphan Tag Assigner Service
Automatically assigns orphaned tags to existing taxonomy categories using Gemini 2.5 Pro
"""
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime

from app.models import TagConcept, TagSynonym, get_db
from app.models.tag_instance import TagInstance, ContentType
from app.services.llm_service import LLMService

logger = logging.getLogger(__name__)


class OrphanTagAssigner:
    """Service for automatically assigning orphaned tags to taxonomy"""
    
    def __init__(self, db: Session):
        self.db = db
        self.llm_service = LLMService()
    
    def get_orphan_tags(self, min_usage: int = 1) -> List[Dict[str, Any]]:
        """
        Get all orphaned tags (tags without parent categories)
        NOTE: Distinguishes between true root categories (with children) and orphan tags
        
        Args:
            min_usage: Minimum usage count to consider
            
        Returns:
            List of orphan tag dictionaries with usage stats
        """
        # Get all root-level tags that are NOT established categories
        # Orphan tags are those with:
        # - No parent (parent_id is NULL)
        # - No children (child_count = 0 or NULL) 
        # - OR have usage but no proper categorization
        orphan_concepts = self.db.query(TagConcept).filter(
            TagConcept.parent_id == None,
            (TagConcept.child_count == 0) | (TagConcept.child_count == None)
        ).all()
        
        orphan_tags = []
        
        # Known root categories that should be excluded (these are intentional roots)
        known_root_categories = [
            'ai-tools', 'ai-research', 'industry-news', 'technical-topics',
            'platforms-companies', 'community-education', 'ethics-policy',
            'applications'  # Add other known root categories here
        ]
        
        for concept in orphan_concepts:
            # Skip if this is a known root category
            if concept.tag in known_root_categories:
                continue
            
            # Get usage count
            usage_count = self.db.query(func.count(TagInstance.id)).filter(
                TagInstance.concept_id == concept.id,
                TagInstance.deleted == False
            ).scalar() or 0
            
            # Skip if below minimum usage
            if usage_count < min_usage:
                continue
            
            # Get sample content using this tag
            sample_instances = self.db.query(TagInstance).filter(
                TagInstance.concept_id == concept.id,
                TagInstance.deleted == False
            ).limit(3).all()
            
            sample_contexts = []
            for instance in sample_instances:
                context = {
                    'type': instance.content_type.value,
                    'content_id': instance.content_id
                }
                # Could fetch actual content here if needed
                sample_contexts.append(context)
            
            orphan_tags.append({
                'id': concept.id,
                'tag': concept.tag,
                'display_name': concept.display_name,
                'description': concept.description,
                'usage_count': usage_count,
                'sample_contexts': sample_contexts,
                'is_orphan': True  # Mark as true orphan
            })
        
        # Sort by usage count (most used first)
        orphan_tags.sort(key=lambda x: x['usage_count'], reverse=True)
        
        return orphan_tags
    
    def get_taxonomy_structure(self) -> Dict[str, Any]:
        """
        Get the existing taxonomy structure for context
        
        Returns:
            Dictionary representing the taxonomy hierarchy
        """
        # Get all non-orphan concepts (have parents or are established root categories)
        root_categories = self.db.query(TagConcept).filter(
            TagConcept.parent_id == None,
            TagConcept.child_count > 0  # Has children, so it's a category
        ).all()
        
        taxonomy = {}
        
        def build_branch(concept: TagConcept, depth: int = 0) -> Dict[str, Any]:
            """Recursively build taxonomy branch"""
            if depth > 5:  # Prevent infinite recursion
                return None
                
            branch = {
                'tag': concept.tag,
                'display_name': concept.display_name,
                'description': concept.description,
                'level': concept.level,
                'children': []
            }
            
            # Get children
            children = self.db.query(TagConcept).filter(
                TagConcept.parent_id == concept.id
            ).all()
            
            for child in children:
                child_branch = build_branch(child, depth + 1)
                if child_branch:
                    branch['children'].append(child_branch)
            
            # Get synonyms
            synonyms = self.db.query(TagSynonym).filter(
                TagSynonym.concept_id == concept.id
            ).all()
            
            if synonyms:
                branch['synonyms'] = [s.synonym_tag for s in synonyms]
            
            return branch
        
        for root in root_categories:
            taxonomy[root.tag] = build_branch(root)
        
        return taxonomy
    
    async def assign_orphan_tags(
        self,
        orphan_tags: Optional[List[Dict]] = None,
        min_usage: int = 2,
        batch_size: int = 20,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        Assign orphan tags to taxonomy categories using Gemini 2.5 Pro
        
        Args:
            orphan_tags: Optional list of orphan tags to process
            min_usage: Minimum usage count for automatic processing
            batch_size: Number of tags to process at once
            dry_run: If True, don't actually make changes
            
        Returns:
            Results dictionary with assignments and statistics
        """
        try:
            # Get orphan tags if not provided
            if orphan_tags is None:
                orphan_tags = self.get_orphan_tags(min_usage)
            
            if not orphan_tags:
                return {
                    'success': True,
                    'message': 'No orphan tags found to process',
                    'summary': {'total_processed': 0}
                }
            
            # Get existing taxonomy
            taxonomy = self.get_taxonomy_structure()
            
            if not taxonomy:
                return {
                    'success': False,
                    'error': 'No existing taxonomy structure found',
                    'summary': {'total_processed': 0}
                }
            
            all_results = {
                'assignments': [],
                'new_intermediate_categories': [],
                'unassignable': [],
                'errors': []
            }
            
            # Process in batches
            for i in range(0, len(orphan_tags), batch_size):
                batch = orphan_tags[i:i + batch_size]
                
                logger.info(f"Processing batch {i//batch_size + 1}: {len(batch)} tags")
                
                # Load top_level.json for entity type schema
                top_level_schema = {}
                try:
                    import os
                    from pathlib import Path
                    backend_dir = Path(__file__).parent.parent.parent
                    top_level_path = backend_dir / "top_level.json"
                    if top_level_path.exists():
                        with open(top_level_path, 'r') as f:
                            top_level_schema = json.load(f)
                except Exception as e:
                    logger.warning(f"Could not load top_level.json: {e}")
                
                # Call LLM (will use GPT-5 based on llm.json config)
                try:
                    result = await self.llm_service.generate_with_model(
                        model_key='orphan_tag_assignment',
                        prompt_key='assign_orphan_tags',
                        top_level_json=json.dumps(top_level_schema, indent=2),
                        taxonomy_json=json.dumps(taxonomy, indent=2),
                        orphan_tags_json=json.dumps(batch, indent=2)
                    )
                    
                    if result and 'assignments' in result:
                        all_results['assignments'].extend(result.get('assignments', []))
                        all_results['new_intermediate_categories'].extend(
                            result.get('new_intermediate_categories', [])
                        )
                        all_results['unassignable'].extend(result.get('unassignable', []))
                    else:
                        logger.error(f"Invalid response from LLM for batch {i//batch_size + 1}")
                        all_results['errors'].append({
                            'batch': i//batch_size + 1,
                            'error': 'Invalid LLM response'
                        })
                        
                except Exception as e:
                    logger.error(f"Error processing batch {i//batch_size + 1}: {e}")
                    all_results['errors'].append({
                        'batch': i//batch_size + 1,
                        'error': str(e)
                    })
            
            # Apply assignments if not dry run
            if not dry_run:
                applied_count = self._apply_assignments(all_results)
                all_results['applied_count'] = applied_count
            
            # Calculate summary
            summary = {
                'total_processed': len(orphan_tags),
                'assigned': len(all_results['assignments']),
                'new_categories_suggested': len(all_results['new_intermediate_categories']),
                'unassignable': len(all_results['unassignable']),
                'errors': len(all_results['errors']),
                'dry_run': dry_run
            }
            
            return {
                'success': True,
                'results': all_results,
                'summary': summary
            }
            
        except Exception as e:
            logger.error(f"Failed to assign orphan tags: {e}")
            return {
                'success': False,
                'error': str(e),
                'summary': {'total_processed': 0}
            }
    
    def _apply_assignments(self, results: Dict[str, Any]) -> int:
        """
        Apply the assignment results to the database
        
        Args:
            results: Assignment results from LLM
            
        Returns:
            Number of successful assignments
        """
        applied = 0
        
        # First, create any new intermediate categories
        new_category_map = {}
        for new_cat in results.get('new_intermediate_categories', []):
            try:
                # Find parent
                parent = self.db.query(TagConcept).filter(
                    TagConcept.tag == new_cat['parent']
                ).first()
                
                if not parent:
                    logger.warning(f"Parent not found for new category: {new_cat['tag']}")
                    continue
                
                # Create new category
                new_concept = TagConcept(
                    tag=new_cat['tag'],
                    display_name=new_cat['display_name'],
                    description=new_cat.get('description', ''),
                    parent_id=parent.id,
                    path=f"{parent.path}{parent.id}/",
                    level=parent.level + 1,
                    descendant_tags=[]
                )
                
                self.db.add(new_concept)
                self.db.flush()
                
                new_category_map[new_cat['tag']] = new_concept.id
                logger.info(f"Created new category: {new_cat['display_name']}")
                
            except Exception as e:
                logger.error(f"Failed to create category {new_cat['tag']}: {e}")
        
        # Apply assignments
        for assignment in results.get('assignments', []):
            try:
                # Find the orphan tag
                orphan = self.db.query(TagConcept).filter(
                    TagConcept.tag == assignment['tag']
                ).first()
                
                if not orphan:
                    logger.warning(f"Orphan tag not found: {assignment['tag']}")
                    continue
                
                if assignment['action'] == 'assign':
                    # Find parent (could be existing or newly created)
                    parent_tag = assignment['parent']
                    
                    if parent_tag in new_category_map:
                        parent_id = new_category_map[parent_tag]
                    else:
                        parent = self.db.query(TagConcept).filter(
                            TagConcept.tag == parent_tag
                        ).first()
                        
                        if not parent:
                            logger.warning(f"Parent not found: {parent_tag}")
                            continue
                        
                        parent_id = parent.id
                    
                    # Update orphan's parent
                    orphan.parent_id = parent_id
                    
                    # Update path and level
                    parent_concept = self.db.query(TagConcept).filter(
                        TagConcept.id == parent_id
                    ).first()
                    
                    orphan.path = f"{parent_concept.path}{parent_concept.id}/"
                    orphan.level = parent_concept.level + 1
                    
                    # Update parent's child count
                    parent_concept.child_count = (parent_concept.child_count or 0) + 1
                    
                    applied += 1
                    logger.info(f"Assigned {orphan.tag} to {parent_tag}")
                    
                elif assignment['action'] == 'synonym':
                    # Find the target concept
                    target = self.db.query(TagConcept).filter(
                        TagConcept.tag == assignment['synonym_of']
                    ).first()
                    
                    if not target:
                        logger.warning(f"Synonym target not found: {assignment['synonym_of']}")
                        continue
                    
                    # Create synonym relationship
                    synonym = TagSynonym(
                        concept_id=target.id,
                        synonym_tag=orphan.tag,
                        created_at=datetime.utcnow()
                    )
                    
                    self.db.add(synonym)
                    
                    # Optionally, merge the orphan concept into target
                    # Update all tag instances to point to target
                    self.db.query(TagInstance).filter(
                        TagInstance.concept_id == orphan.id
                    ).update({'concept_id': target.id})
                    
                    # Delete the orphan concept
                    self.db.delete(orphan)
                    
                    applied += 1
                    logger.info(f"Created synonym: {orphan.tag} -> {target.tag}")
                    
            except Exception as e:
                logger.error(f"Failed to apply assignment for {assignment['tag']}: {e}")
        
        # Commit changes
        try:
            self.db.commit()
            logger.info(f"Successfully applied {applied} assignments")
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to commit assignments: {e}")
            return 0
        
        return applied
    
    def get_assignment_preview(
        self,
        limit: int = 10,
        min_usage: int = 2
    ) -> Dict[str, Any]:
        """
        Get a preview of orphan tags that would be processed
        
        Args:
            limit: Maximum number of tags to preview
            min_usage: Minimum usage count
            
        Returns:
            Preview information
        """
        orphan_tags = self.get_orphan_tags(min_usage)[:limit]
        
        # Get taxonomy stats
        total_categories = self.db.query(func.count(TagConcept.id)).filter(
            TagConcept.child_count > 0
        ).scalar() or 0
        
        total_orphans = self.db.query(func.count(TagConcept.id)).filter(
            TagConcept.parent_id == None,
            TagConcept.child_count == 0
        ).scalar() or 0
        
        return {
            'orphan_tags_preview': orphan_tags,
            'total_orphans': total_orphans,
            'total_categories': total_categories,
            'preview_count': len(orphan_tags)
        }