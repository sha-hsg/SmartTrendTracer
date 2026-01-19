"""
Tag Reorganization Service using Gemini 2.5 Pro via LangChain
Leverages configuration files for prompts and models
"""
import json
import os
import logging
import time
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict
from collections import defaultdict

from sqlalchemy.orm import Session
from sqlalchemy import func, distinct

from app.models import Tag, Tweet, get_db
from app.models.tag_ontology import TagConcept, TagSynonym, TagOntologyService, TagMapping
from app.services.langchain_llm_service import get_langchain_llm_service

# Configure logger for detailed debugging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


@dataclass
class TagNode:
    """Represents a node in the tag taxonomy tree - new structure with ID and slug"""
    id: str  # Unique ID like "c_0001"
    slug: str  # Normalized name like "large_language_models"
    display_name: str  # Human-readable name like "Large Language Models (LLMs)"
    description: Optional[str] = None
    status: str = "active"  # active, deprecated, etc.
    parents: List[str] = None  # Now plural, supports poly-hierarchy
    children: List[str] = None  # Child concept IDs
    usage_count: int = 0
    icon: Optional[str] = None  # Emoji icon
    color: Optional[str] = None  # Color code for UI
    
    # Legacy fields for backwards compatibility
    name: Optional[str] = None  # Will be set to slug for compatibility
    parent: Optional[str] = None  # Single parent for backwards compatibility
    level: Optional[int] = 0  # Hierarchy level
    synonyms: Optional[List[str]] = None  # Now handled via aliases
    examples: Optional[List[str]] = None  # Sample usage contexts
    
    def __post_init__(self):
        if self.parents is None:
            self.parents = []
        if self.children is None:
            self.children = []
        if self.synonyms is None:
            self.synonyms = []
        if self.examples is None:
            self.examples = []
        
        # Set legacy fields for backwards compatibility
        if not self.name:
            self.name = self.slug
        if not self.parent and self.parents:
            self.parent = self.parents[0] if self.parents else None


@dataclass
class TaxonomyReorganization:
    """Complete taxonomy reorganization proposal"""
    version: str
    created_at: str
    model_used: str
    total_tags: int
    hierarchy: Dict[str, TagNode]
    root_categories: List[str]
    deprecated_tags: List[str]
    merge_proposals: List[Dict[str, Any]]
    new_tags_suggested: List[TagNode]
    confidence_score: float
    reasoning: str
    statistics: Dict[str, Any]


class TagReorganizationService:
    """Service for comprehensive tag reorganization using Gemini via LangChain"""
    
    def __init__(self, db: Session):
        self.db = db
        self.llm_service = get_langchain_llm_service()
    
    def get_all_tags_with_context(self) -> Dict[str, Any]:
        """Get all tags with their usage context and statistics from all sources"""
        
        # Import necessary models
        from app.models.papers import PaperTag
        from app.models.substack import ArticleTag
        
        # Get tags from all sources with usage counts
        # 1. Tweet tags
        tweet_tags = self.db.query(
            Tag.tag,
            func.count(Tag.id).label('usage_count')
        ).group_by(Tag.tag).all()
        
        # 2. Paper tags
        paper_tags = self.db.query(
            PaperTag.tag,
            func.count(PaperTag.id).label('usage_count')
        ).group_by(PaperTag.tag).all()
        
        # 3. Article tags  
        article_tags = self.db.query(
            ArticleTag.tag,
            func.count(ArticleTag.id).label('usage_count')
        ).group_by(ArticleTag.tag).all()
        
        # Combine all tags into a single dictionary
        combined_tags = defaultdict(lambda: {'usage_count': 0, 'sources': []})
        
        for tag_name, count in tweet_tags:
            combined_tags[tag_name]['usage_count'] += count
            combined_tags[tag_name]['sources'].append('tweets')
            
        for tag_name, count in paper_tags:
            combined_tags[tag_name]['usage_count'] += count
            combined_tags[tag_name]['sources'].append('papers')
            
        for tag_name, count in article_tags:
            combined_tags[tag_name]['usage_count'] += count
            combined_tags[tag_name]['sources'].append('articles')
        
        tags_data = {}
        
        # Import necessary models for getting sample content
        from app.models.papers import Paper, PaperTag
        from app.models.substack import SubstackArticle, ArticleTag
        
        for tag_name, tag_info in combined_tags.items():
            usage_count = tag_info['usage_count']
            sources = tag_info['sources']
            
            sample_contexts = []
            
            # Get sample content from each source
            if 'tweets' in sources:
                sample_tweets = self.db.query(Tweet.text).join(Tag).filter(
                    Tag.tag == tag_name
                ).limit(2).all()
                sample_contexts.extend([f"[Tweet] {tweet[0][:100]}" for tweet in sample_tweets])
            
            if 'papers' in sources:
                sample_papers = self.db.query(Paper.title).join(PaperTag).filter(
                    PaperTag.tag == tag_name
                ).limit(1).all()
                sample_contexts.extend([f"[Paper] {paper[0][:100]}" for paper in sample_papers])
            
            if 'articles' in sources:
                sample_articles = self.db.query(SubstackArticle.title).join(ArticleTag).filter(
                    ArticleTag.tag == tag_name
                ).limit(1).all()
                sample_contexts.extend([f"[Article] {article[0][:100]}" for article in sample_articles])
            
            # Get co-occurring tags from tweets (most common source)
            co_tags = []
            if 'tweets' in sources:
                co_tags = self.db.query(
                    Tag.tag,
                    func.count(Tag.tag).label('co_count')
                ).join(Tweet, Tag.tweet_id == Tweet.id).filter(
                    Tweet.id.in_(
                        self.db.query(Tweet.id).join(Tag).filter(Tag.tag == tag_name)
                    ),
                    Tag.tag != tag_name
                ).group_by(Tag.tag).order_by(func.count(Tag.tag).desc()).limit(5).all()
            
            # Limit context data for large datasets
            tags_data[tag_name] = {
                'name': tag_name,
                'usage_count': usage_count,
                'sources': sources,
                # Only include sample contexts for frequently used tags
                'sample_contexts': sample_contexts[:3] if usage_count > 3 else [],
                # Only top 3 co-occurring tags
                'co_occurring_tags': [{'tag': tag, 'count': count} for tag, count in co_tags[:3]],
                'existing_synonyms': []  # Will be populated from new ontology
            }
        
        # Get overall statistics
        total_tags = len(tags_data)
        total_taggings = sum(t['usage_count'] for t in tags_data.values())
        avg_usage = total_taggings / total_tags if total_tags > 0 else 0
        
        # Identify low-usage tags
        low_usage_threshold = max(3, avg_usage * 0.1)
        low_usage_tags = [name for name, data in tags_data.items() 
                         if data['usage_count'] < low_usage_threshold]
        
        # Get counts for each source
        unique_tweets = self.db.query(distinct(Tag.tweet_id)).count()
        unique_papers = self.db.query(distinct(PaperTag.paper_id)).count()
        unique_articles = self.db.query(distinct(ArticleTag.article_id)).count()
        
        # Count tags by source
        tags_by_source = {
            'tweets_only': len([t for t, d in tags_data.items() if d['sources'] == ['tweets']]),
            'papers_only': len([t for t, d in tags_data.items() if d['sources'] == ['papers']]),
            'articles_only': len([t for t, d in tags_data.items() if d['sources'] == ['articles']]),
            'multi_source': len([t for t, d in tags_data.items() if len(d['sources']) > 1])
        }
        
        return {
            'tags': tags_data,
            'statistics': {
                'total_tags': total_tags,
                'total_taggings': total_taggings,
                'average_usage': avg_usage,
                'low_usage_tags': low_usage_tags,
                'unique_tweets_tagged': unique_tweets,
                'unique_papers_tagged': unique_papers,
                'unique_articles_tagged': unique_articles,
                'tags_by_source': tags_by_source
            }
        }
    
    def generate_reorganization_proposal(self) -> TaxonomyReorganization:
        """Generate a complete reorganization proposal using Gemini via LangChain"""
        
        start_time = time.time()
        logger.info("=== Starting Tag Reorganization Proposal Generation ===")
        
        # Get all tags with context
        logger.debug("Step 1: Getting all tags with context...")
        tags_context = self.get_all_tags_with_context()
        logger.info(f"Retrieved {tags_context['statistics']['total_tags']} tags for analysis")
        
        # Get the model that will be used from config
        model_config = self.llm_service.llm_config.get("models", {}).get("tag_reorganization_full", {})
        model_name = model_config.get("model", "gpt-5-2025-08-07")
        
        # Send ALL tags to LLM for complete reorganization
        logger.info(f"Sending ALL {tags_context['statistics']['total_tags']} tags to {model_name} for complete reorganization")
        
        # Use all tags, but simplify context for very low usage tags
        llm_tags = {}
        for name, data in tags_context['tags'].items():
            if data['usage_count'] >= 3:
                # Include full context for frequently used tags
                llm_tags[name] = data
            else:
                # Simplify context for rarely used tags to save tokens
                llm_tags[name] = {
                    'name': name,
                    'usage_count': data['usage_count'],
                    'sources': data['sources'],
                    'sample_contexts': [],  # Skip samples for low-usage tags
                    'co_occurring_tags': []  # Skip co-occurrence for low-usage tags
                }
        
        llm_context = {
            'tags': llm_tags,
            'statistics': tags_context['statistics']
        }
        logger.debug(f"Statistics: Total tags: {tags_context['statistics']['total_tags']}, "
                    f"Total taggings: {tags_context['statistics']['total_taggings']}, "
                    f"Average usage: {tags_context['statistics']['average_usage']:.2f}")
        
        # Use LangChain service for reorganization
        try:
            # Call the specialized tag reorganization method
            # Model will be selected from llm.json configuration
            logger.info("Step 2: Calling LangChain service for tag reorganization...")
            logger.debug(f"Sending {len(llm_context['tags'])} tags to LLM service")
            
            llm_start = time.time()
            reorganization_data = self.llm_service.generate_tag_reorganization(
                tags_context=llm_context
            )
            llm_duration = time.time() - llm_start
            
            logger.info(f"Step 3: Received response from LLM (took {llm_duration:.2f} seconds)")
            logger.debug(f"Response contains {len(reorganization_data.get('hierarchy', {}))} hierarchy items")
            
            # Convert to TagNode objects
            logger.info("Step 4: Building taxonomy hierarchy...")
            hierarchy = {}
            hierarchy_count = 0
            
            # Check if response uses new format (concepts) or old format (hierarchy)
            if 'concepts' in reorganization_data:
                # New format with concepts and aliases
                logger.debug("Using new concept-based format")
                for concept in reorganization_data.get('concepts', []):
                    concept_id = concept.get('id')
                    hierarchy[concept_id] = TagNode(
                        id=concept_id,
                        slug=concept.get('slug', concept_id),
                        display_name=concept.get('display_name', concept.get('slug', '')),
                        description=concept.get('description'),
                        status=concept.get('status', 'active'),
                        parents=concept.get('parents', []),
                        children=concept.get('children', []),
                        usage_count=concept.get('usage_count', 0),
                        icon=concept.get('icon'),
                        color=concept.get('color'),
                        # Set legacy fields
                        name=concept.get('slug', concept_id),
                        parent=concept.get('parents', [None])[0] if concept.get('parents') else None,
                        level=concept.get('level', 0),
                        synonyms=[]  # Aliases are handled separately
                    )
                    hierarchy_count += 1
                    
                    # Log progress every 50 items
                    if hierarchy_count % 50 == 0:
                        logger.debug(f"Processed {hierarchy_count} concepts...")
                
                # Store aliases separately if needed
                self.aliases = reorganization_data.get('aliases', [])
                self.relations = reorganization_data.get('relations', [])
                
            else:
                # Old format with hierarchy dictionary
                logger.debug("Using legacy hierarchy format")
                for tag_name, tag_data in reorganization_data.get('hierarchy', {}).items():
                    # Generate a concept ID for legacy format
                    concept_id = f"c_{tag_name.lower().replace('-', '_').replace(' ', '_')}"
                    hierarchy[concept_id] = TagNode(
                        id=concept_id,
                        slug=tag_name.lower().replace('-', '_').replace(' ', '_'),
                        display_name=tag_data.get('display_name', tag_name),
                        description=tag_data.get('description'),
                        status='active',
                        parents=[tag_data.get('parent')] if tag_data.get('parent') else [],
                        children=tag_data.get('children', []),
                        usage_count=tags_context['tags'].get(tag_name, {}).get('usage_count', 0),
                        icon=tag_data.get('icon'),
                        color=tag_data.get('color'),
                        # Set legacy fields
                        name=tag_name,
                        parent=tag_data.get('parent'),
                        level=tag_data.get('level', 0),
                        synonyms=tag_data.get('synonyms', [])
                    )
                    hierarchy_count += 1
                    
                    # Log progress every 50 items
                    if hierarchy_count % 50 == 0:
                        logger.debug(f"Processed {hierarchy_count} hierarchy nodes...")
            
            logger.info(f"Created hierarchy with {len(hierarchy)} nodes")
            
            # Get model used from config
            model_config = self.llm_service.llm_config.get("models", {}).get("tag_reorganization_full", {})
            model_used = model_config.get("model", "gemini-2.5-pro")
            logger.info(f"Model used: {model_used}")
            
            # Extract metrics
            root_count = len(reorganization_data.get('root_categories', []))
            deprecated_count = len(reorganization_data.get('deprecated_tags', []))
            merge_count = len(reorganization_data.get('merge_proposals', []))
            new_categories_count = len(reorganization_data.get('new_categories_suggested', []))
            
            logger.info(f"Step 5: Reorganization metrics:")
            logger.info(f"  - Root categories: {root_count}")
            logger.info(f"  - Deprecated tags: {deprecated_count}")
            logger.info(f"  - Merge proposals: {merge_count}")
            logger.info(f"  - New categories suggested: {new_categories_count}")
            
            # Create the reorganization proposal
            proposal = TaxonomyReorganization(
                version="1.0",
                created_at=datetime.now().isoformat(),
                model_used=model_used,
                total_tags=tags_context['statistics']['total_tags'],
                hierarchy=hierarchy,
                root_categories=reorganization_data.get('root_categories', []),
                deprecated_tags=reorganization_data.get('deprecated_tags', []),
                merge_proposals=reorganization_data.get('merge_proposals', []),
                new_tags_suggested=[
                    TagNode(
                        id=f"c_new_{i:04d}",
                        slug=cat.get('name', '').lower().replace('-', '_').replace(' ', '_'),
                        display_name=cat.get('display_name', cat['name']),
                        description=cat.get('description'),
                        status='suggested',
                        parents=[],
                        children=[],
                        usage_count=0,
                        icon=cat.get('icon', '📁'),
                        color=cat.get('color'),
                        # Legacy fields
                        name=cat['name'],
                        parent=None,
                        level=0
                    ) for i, cat in enumerate(reorganization_data.get('new_categories_suggested', []), 1)
                ],
                confidence_score=reorganization_data.get('confidence_score', 0.8),
                reasoning=reorganization_data.get('reasoning', ''),
                statistics={
                    'original_tags': tags_context['statistics']['total_tags'],
                    'reorganized_tags': len(hierarchy),
                    'deprecated_count': deprecated_count,
                    'merge_count': merge_count,
                    'new_categories': new_categories_count
                }
            )
            
            total_duration = time.time() - start_time
            logger.info(f"=== Reorganization proposal generated successfully in {total_duration:.2f} seconds ===")
            
            return proposal
            
        except Exception as e:
            error_duration = time.time() - start_time
            logger.error(f"=== ERROR: Reorganization failed after {error_duration:.2f} seconds ===")
            logger.error(f"Error type: {type(e).__name__}")
            logger.error(f"Error message: {str(e)}")
            
            import traceback
            logger.debug(f"Full traceback:\n{traceback.format_exc()}")
            
            raise
    
    def apply_reorganization(self, proposal: TaxonomyReorganization, 
                            approved_changes: Optional[Dict[str, bool]] = None) -> Dict[str, Any]:
        """Apply the approved reorganization changes to the database"""
        
        start_time = time.time()
        logger.info("=== Starting Tag Reorganization Application ===")
        
        if approved_changes is None:
            # Apply all changes by default
            approved_changes = {tag: True for tag in proposal.hierarchy.keys()}
            logger.info(f"No specific approvals provided, applying all {len(approved_changes)} changes")
        else:
            approved_count = sum(1 for approved in approved_changes.values() if approved)
            logger.info(f"Applying {approved_count} approved changes out of {len(approved_changes)} total")
        
        results = {
            'concepts_created': 0,
            'concepts_updated': 0,
            'tags_merged': 0,
            'synonyms_created': 0,
            'errors': [],
            'details': []
        }
        
        try:
            logger.debug("Step 1: Initializing ontology service...")
            ontology_service = TagOntologyService(self.db)
            
            # First pass: Create/update TagConcepts for approved tags
            concept_map = {}  # tag_name -> TagConcept
            
            logger.info("Step 2: Processing tag concepts...")
            concept_count = 0
            
            for tag_name, node in proposal.hierarchy.items():
                # Skip if not approved
                if not approved_changes.get(tag_name, False):
                    logger.debug(f"Skipping unapproved tag: {tag_name}")
                    continue
                
                concept_count += 1
                logger.debug(f"Processing concept {concept_count}: {tag_name}")
                
                # Check if concept already exists
                existing_concept = self.db.query(TagConcept).filter(
                    TagConcept.tag == tag_name
                ).first()
                
                if existing_concept:
                    # Update existing concept
                    logger.debug(f"Updating existing concept: {tag_name}")
                    existing_concept.display_name = node.display_name
                    existing_concept.description = node.description
                    # Only set icon if the field exists in the model
                    if node.icon and hasattr(existing_concept, 'icon'):
                        existing_concept.icon = node.icon
                    # Note: color field is not supported in TagConcept model
                    concept_map[tag_name] = existing_concept
                    results['concepts_updated'] += 1
                    results['details'].append(f"Updated concept: {tag_name}")
                else:
                    # Create new concept
                    logger.debug(f"Creating new concept: {tag_name} as '{node.display_name}'")
                    # Create concept without color field (not supported in model)
                    new_concept = TagConcept(
                        tag=tag_name,
                        display_name=node.display_name,
                        description=node.description,
                        path="/"  # Initialize with root path, will be updated later
                    )
                    # Set icon if provided (check if field exists)
                    if node.icon and hasattr(new_concept, 'icon'):
                        new_concept.icon = node.icon
                    self.db.add(new_concept)
                    self.db.flush()  # Get the ID
                    concept_map[tag_name] = new_concept
                    results['concepts_created'] += 1
                    results['details'].append(f"Created concept: {tag_name} ({node.display_name})")
                
                # Log progress every 20 concepts
                if concept_count % 20 == 0:
                    logger.info(f"Processed {concept_count} concepts...")
            
            # Second pass: Set up parent-child relationships
            logger.info("Step 3: Setting up parent-child relationships...")
            relationship_count = 0
            
            for tag_name, node in proposal.hierarchy.items():
                if not approved_changes.get(tag_name, False):
                    continue
                
                if node.parent and node.parent in concept_map:
                    relationship_count += 1
                    logger.debug(f"Setting {tag_name} as child of {node.parent}")
                    child_concept = concept_map[tag_name]
                    parent_concept = concept_map[node.parent]
                    child_concept.parent_id = parent_concept.id
                    child_concept.update_path(self.db)  # Update materialized path
            
            logger.info(f"Established {relationship_count} parent-child relationships")
            
            # Third pass: Handle synonyms and merges
            logger.info("Step 4: Processing synonyms and tag merges...")
            merge_count = 0
            synonym_count = 0
            
            for tag_name, node in proposal.hierarchy.items():
                if not approved_changes.get(tag_name, False):
                    continue
                
                concept = concept_map.get(tag_name)
                if not concept:
                    logger.warning(f"Concept not found in map for tag: {tag_name}")
                    continue
                
                # Process synonyms
                logger.debug(f"Processing {len(node.synonyms)} synonyms for {tag_name}")
                for synonym in node.synonyms:
                    # Check if synonym exists as a tag in the database
                    existing_tags = self.db.query(Tag).filter(Tag.tag == synonym).all()
                    
                    if existing_tags:
                        # This is a merge operation - change all occurrences to the main tag
                        for tag_entry in existing_tags:
                            # Check if main tag already exists for this tweet
                            existing_main = self.db.query(Tag).filter(
                                Tag.tweet_id == tag_entry.tweet_id,
                                Tag.tag == tag_name
                            ).first()
                            
                            if not existing_main:
                                # Change the synonym tag to the main tag
                                tag_entry.tag = tag_name
                            else:
                                # Delete duplicate
                                self.db.delete(tag_entry)
                        
                        results['tags_merged'] += 1
                        results['details'].append(f"Merged '{synonym}' into '{tag_name}'")
                    
                    # Create synonym relationship
                    # First check if this synonym already exists for ANY concept
                    existing_global_synonym = self.db.query(TagSynonym).filter(
                        TagSynonym.synonym_tag == synonym
                    ).first()
                    
                    if existing_global_synonym:
                        # Synonym already exists for another concept, skip it
                        logger.debug(f"Synonym '{synonym}' already exists for concept {existing_global_synonym.concept_id}, skipping")
                        continue
                    
                    # Now check if it exists for this specific concept (redundant but safe)
                    existing_synonym = self.db.query(TagSynonym).filter(
                        TagSynonym.concept_id == concept.id,
                        TagSynonym.synonym_tag == synonym
                    ).first()
                    
                    if not existing_synonym:
                        new_synonym = TagSynonym(
                            concept_id=concept.id,
                            synonym_tag=synonym
                        )
                        self.db.add(new_synonym)
                        results['synonyms_created'] += 1
            
            # Handle deprecated tags
            for deprecated_tag in proposal.deprecated_tags:
                # Find replacement tag if specified in merge proposals
                replacement = None
                for merge in proposal.merge_proposals:
                    if deprecated_tag in merge.get('from_tags', []):
                        replacement = merge.get('to_tag')
                        break
                
                if replacement and replacement in concept_map:
                    # Merge deprecated tag into replacement
                    deprecated_entries = self.db.query(Tag).filter(Tag.tag == deprecated_tag).all()
                    for tag_entry in deprecated_entries:
                        existing = self.db.query(Tag).filter(
                            Tag.tweet_id == tag_entry.tweet_id,
                            Tag.tag == replacement
                        ).first()
                        if not existing:
                            tag_entry.tag = replacement
                        else:
                            self.db.delete(tag_entry)
                    results['tags_merged'] += 1
                    results['details'].append(f"Deprecated '{deprecated_tag}' merged into '{replacement}'")
            
            # Rebuild tag mappings for efficient filtering
            logger.info("Step 6: Rebuilding tag mappings for efficient filtering...")
            rebuild_start = time.time()
            TagMapping.rebuild_mappings(self.db)
            rebuild_duration = time.time() - rebuild_start
            logger.debug(f"Tag mappings rebuilt in {rebuild_duration:.2f} seconds")
            
            # Commit all changes
            logger.info("Step 7: Committing all changes to database...")
            self.db.commit()
            
            total_duration = time.time() - start_time
            
            results['success'] = True
            results['message'] = (f"Successfully applied reorganization: "
                                 f"{results['concepts_created']} concepts created, "
                                 f"{results['concepts_updated']} updated, "
                                 f"{results['tags_merged']} tags merged, "
                                 f"{results['synonyms_created']} synonyms created")
            
            logger.info(f"=== Tag Reorganization Applied Successfully ===")
            logger.info(f"Total duration: {total_duration:.2f} seconds")
            logger.info(f"Results: {results['message']}")
            
        except Exception as e:
            error_duration = time.time() - start_time
            logger.error(f"=== ERROR: Apply reorganization failed after {error_duration:.2f} seconds ===")
            logger.error(f"Error type: {type(e).__name__}")
            logger.error(f"Error message: {str(e)}")
            
            self.db.rollback()
            logger.info("Database rolled back")
            
            results['errors'].append(str(e))
            results['success'] = False
            results['message'] = f"Failed to apply reorganization: {str(e)}"
            
            import traceback
            logger.debug(f"Full traceback:\n{traceback.format_exc()}")
        
        return results
    
    def export_taxonomy(self, proposal: TaxonomyReorganization, format: str = "json") -> str:
        """Export the taxonomy in various formats"""
        
        if format == "json":
            return json.dumps(asdict(proposal), indent=2)
        
        elif format == "markdown":
            md = f"# Tag Taxonomy Reorganization\n\n"
            md += f"**Generated**: {proposal.created_at}\n"
            md += f"**Model**: {proposal.model_used}\n"
            md += f"**Total Tags**: {proposal.total_tags}\n"
            md += f"**Confidence**: {proposal.confidence_score:.1%}\n\n"
            
            md += "## Root Categories\n\n"
            for root in proposal.root_categories:
                if root in proposal.hierarchy:
                    node = proposal.hierarchy[root]
                    md += f"- **{node.display_name}** ({root})\n"
                    if node.description:
                        md += f"  - {node.description}\n"
            
            return md
        
        elif format == "csv":
            import csv
            import io
            
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(['Tag', 'Display Name', 'Parent', 'Level', 'Description'])
            
            for tag_name, node in proposal.hierarchy.items():
                writer.writerow([
                    tag_name,
                    node.display_name,
                    node.parent or '',
                    node.level,
                    node.description or ''
                ])
            
            return output.getvalue()
        
        else:
            raise ValueError(f"Unsupported format: {format}")


class TagOntologyService:
    """Compatibility class for existing code"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_hierarchy_tree(self):
        """Get hierarchy tree - stub for compatibility"""
        return []