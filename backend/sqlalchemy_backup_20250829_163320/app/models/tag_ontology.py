"""
Tag Ontology Models for hierarchical and semantic tag relationships
Using materialized path pattern for efficient hierarchical queries
"""
from sqlalchemy import Column, String, Integer, ForeignKey, Text, Index, DateTime, Boolean, JSON
from sqlalchemy.orm import relationship, Session
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from typing import List, Set, Optional, Dict
import json

from app.models.database import Base

class TagConcept(Base):
    """
    Main tag concept with hierarchical support using materialized path
    The path stores the full hierarchy like: /ai-tools/llm/gpt-5/
    """
    __tablename__ = 'tag_concepts'
    
    id = Column(Integer, primary_key=True)
    tag = Column(String(100), unique=True, nullable=False, index=True)
    display_name = Column(String(100), nullable=False)
    description = Column(Text)
    
    # Materialized path for hierarchy - stores full path like /1/5/12/
    path = Column(String(500), nullable=False, index=True)
    parent_id = Column(Integer, ForeignKey('tag_concepts.id'), nullable=True)
    level = Column(Integer, default=0)  # Depth in hierarchy
    
    # Precomputed data for performance
    child_count = Column(Integer, default=0)
    descendant_count = Column(Integer, default=0)  # Total descendants
    descendant_tags = Column(JSON)  # Cached list of all descendant tag names
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    parent = relationship("TagConcept", remote_side=[id], backref="children")
    synonyms = relationship("TagSynonym", back_populates="concept", cascade="all, delete-orphan")
    
    # Indexes for efficient queries
    __table_args__ = (
        Index('idx_tag_path', 'path'),
        Index('idx_tag_parent', 'parent_id'),
        Index('idx_tag_level', 'level'),
    )
    
    def get_ancestors(self, db: Session) -> List['TagConcept']:
        """Get all ancestors of this tag"""
        if not self.parent_id:
            return []
        
        # Parse path to get ancestor IDs
        path_ids = [int(id) for id in self.path.strip('/').split('/') if id and id != str(self.id)]
        if not path_ids:
            return []
            
        return db.query(TagConcept).filter(TagConcept.id.in_(path_ids)).order_by(TagConcept.level).all()
    
    def get_descendants(self, db: Session) -> List['TagConcept']:
        """Get all descendants efficiently using path"""
        return db.query(TagConcept).filter(
            TagConcept.path.like(f"{self.path}{self.id}/%")
        ).all()
    
    def get_siblings(self, db: Session) -> List['TagConcept']:
        """Get sibling tags (same parent)"""
        if not self.parent_id:
            # Root level siblings
            return db.query(TagConcept).filter(
                TagConcept.parent_id.is_(None),
                TagConcept.id != self.id
            ).all()
        return db.query(TagConcept).filter(
            TagConcept.parent_id == self.parent_id,
            TagConcept.id != self.id
        ).all()
    
    def update_path(self, db: Session):
        """Update materialized path when hierarchy changes"""
        if self.parent_id:
            parent = db.query(TagConcept).filter(TagConcept.id == self.parent_id).first()
            self.path = f"{parent.path}{parent.id}/"
            self.level = parent.level + 1
        else:
            self.path = "/"
            self.level = 0
    
    def update_descendant_cache(self, db: Session):
        """Update cached descendant information"""
        descendants = self.get_descendants(db)
        self.descendant_count = len(descendants)
        self.descendant_tags = [d.tag for d in descendants]
        
        # Update child count
        self.child_count = db.query(TagConcept).filter(
            TagConcept.parent_id == self.id
        ).count()
    
    def get_all_related_tags(self, db: Session) -> Set[str]:
        """Get all tags that should match when this tag is selected"""
        tags = {self.tag}
        
        # Add all synonyms
        for synonym in self.synonyms:
            tags.add(synonym.synonym_tag)
        
        # Add all descendant tags
        if self.descendant_tags:
            tags.update(self.descendant_tags)
        
        # Add synonyms of descendants
        if self.descendant_tags:
            descendant_synonyms = db.query(TagSynonym.synonym_tag).join(
                TagConcept
            ).filter(
                TagConcept.tag.in_(self.descendant_tags)
            ).all()
            tags.update([s[0] for s in descendant_synonyms])
        
        return tags


class TagSynonym(Base):
    """
    Synonym relationships (sameAs) between tags
    Maps alternative names to canonical tag concepts
    """
    __tablename__ = 'tag_synonyms'
    
    id = Column(Integer, primary_key=True)
    concept_id = Column(Integer, ForeignKey('tag_concepts.id'), nullable=False)
    synonym_tag = Column(String(100), unique=True, nullable=False, index=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(50))  # Track who created the synonym
    
    # Relationship
    concept = relationship("TagConcept", back_populates="synonyms")
    
    __table_args__ = (
        Index('idx_synonym_concept', 'concept_id'),
    )


class TagMapping(Base):
    """
    Cached mapping table for ultra-fast filtering
    Pre-computes all tag relationships for efficient queries
    """
    __tablename__ = 'tag_mappings'
    
    id = Column(Integer, primary_key=True)
    source_tag = Column(String(100), nullable=False, index=True)  # The tag selected in UI
    mapped_tag = Column(String(100), nullable=False, index=True)  # Tag to include in search
    relationship_type = Column(String(20))  # 'self', 'synonym', 'child', 'descendant'
    distance = Column(Integer, default=0)  # How many levels down in hierarchy
    
    __table_args__ = (
        Index('idx_mapping_source', 'source_tag'),
        Index('idx_mapping_mapped', 'mapped_tag'),
        Index('idx_mapping_both', 'source_tag', 'mapped_tag'),
    )
    
    @classmethod
    def rebuild_mappings(cls, db: Session):
        """Rebuild all tag mappings for efficient queries"""
        # Clear existing mappings
        db.query(cls).delete()
        db.commit()  # Commit the deletion to avoid conflicts
        
        # Get all tag concepts
        concepts = db.query(TagConcept).all()
        
        # Use a set to track unique mappings and avoid duplicates
        added_mappings = set()
        
        for concept in concepts:
            # Map to self
            mapping_key = (concept.tag, concept.tag)
            if mapping_key not in added_mappings:
                db.add(cls(
                    source_tag=concept.tag,
                    mapped_tag=concept.tag,
                    relationship_type='self',
                    distance=0
                ))
                added_mappings.add(mapping_key)
            
            # Map synonyms
            for synonym in concept.synonyms:
                # Synonym maps to concept
                mapping_key = (synonym.synonym_tag, concept.tag)
                if mapping_key not in added_mappings:
                    db.add(cls(
                        source_tag=synonym.synonym_tag,
                        mapped_tag=concept.tag,
                        relationship_type='synonym',
                        distance=0
                    ))
                    added_mappings.add(mapping_key)
                    
                # Concept maps to synonym
                mapping_key = (concept.tag, synonym.synonym_tag)
                if mapping_key not in added_mappings:
                    db.add(cls(
                        source_tag=concept.tag,
                        mapped_tag=synonym.synonym_tag,
                        relationship_type='synonym',
                        distance=0
                    ))
                    added_mappings.add(mapping_key)
            
            # Map descendants
            descendants = concept.get_descendants(db)
            for desc in descendants:
                distance = desc.level - concept.level
                relationship = 'child' if distance == 1 else 'descendant'
                
                mapping_key = (concept.tag, desc.tag)
                if mapping_key not in added_mappings:
                    db.add(cls(
                        source_tag=concept.tag,
                        mapped_tag=desc.tag,
                        relationship_type=relationship,
                        distance=distance
                    ))
                    added_mappings.add(mapping_key)
                
                # Also map descendant's synonyms
                for syn in desc.synonyms:
                    mapping_key = (concept.tag, syn.synonym_tag)
                    if mapping_key not in added_mappings:
                        db.add(cls(
                            source_tag=concept.tag,
                            mapped_tag=syn.synonym_tag,
                            relationship_type='descendant_synonym',
                            distance=distance
                        ))
                        added_mappings.add(mapping_key)
        
        db.commit()
    
    @classmethod
    def get_mapped_tags(cls, db: Session, source_tag: str) -> List[str]:
        """Get all tags that should be included when filtering by source_tag"""
        mappings = db.query(cls.mapped_tag).filter(
            cls.source_tag == source_tag
        ).all()
        return [m[0] for m in mappings]


class TagOntologyService:
    """Service class for managing tag ontology operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_concept(self, tag: str, display_name: str, 
                       description: str = None, parent_id: int = None) -> TagConcept:
        """Create a new tag concept"""
        concept = TagConcept(
            tag=tag.lower().replace(' ', '-'),
            display_name=display_name,
            description=description,
            parent_id=parent_id
        )
        
        # Set path based on parent
        concept.update_path(self.db)
        
        self.db.add(concept)
        self.db.commit()
        
        # Update parent's counts if exists
        if parent_id:
            parent = self.db.query(TagConcept).filter(TagConcept.id == parent_id).first()
            if parent:
                parent.update_descendant_cache(self.db)
                self.db.commit()
        
        # Rebuild mappings
        TagMapping.rebuild_mappings(self.db)
        
        return concept
    
    def add_synonym(self, concept_id: int, synonym: str) -> TagSynonym:
        """Add a synonym to a concept"""
        syn = TagSynonym(
            concept_id=concept_id,
            synonym_tag=synonym.lower().replace(' ', '-')
        )
        self.db.add(syn)
        self.db.commit()
        
        # Rebuild mappings
        TagMapping.rebuild_mappings(self.db)
        
        return syn
    
    def move_concept(self, concept_id: int, new_parent_id: Optional[int]):
        """Move a concept to a new parent"""
        concept = self.db.query(TagConcept).filter(TagConcept.id == concept_id).first()
        if not concept:
            raise ValueError(f"Concept {concept_id} not found")
        
        old_parent_id = concept.parent_id
        concept.parent_id = new_parent_id
        concept.update_path(self.db)
        
        # Update all descendants' paths
        descendants = concept.get_descendants(self.db)
        for desc in descendants:
            desc.update_path(self.db)
        
        self.db.commit()
        
        # Update caches
        if old_parent_id:
            old_parent = self.db.query(TagConcept).filter(TagConcept.id == old_parent_id).first()
            if old_parent:
                old_parent.update_descendant_cache(self.db)
        
        if new_parent_id:
            new_parent = self.db.query(TagConcept).filter(TagConcept.id == new_parent_id).first()
            if new_parent:
                new_parent.update_descendant_cache(self.db)
        
        concept.update_descendant_cache(self.db)
        self.db.commit()
        
        # Rebuild mappings
        TagMapping.rebuild_mappings(self.db)
    
    def get_tags_for_filtering(self, tag: str) -> List[str]:
        """Get all tags to include when filtering by a specific tag"""
        # First try with the original tag as-is
        mapped_tags = TagMapping.get_mapped_tags(self.db, tag)
        
        # If no results, try with slugified version for backward compatibility
        if not mapped_tags:
            slugified = tag.lower().replace(' ', '-')
            mapped_tags = TagMapping.get_mapped_tags(self.db, slugified)
        
        # If still no results, just return the original tag
        if not mapped_tags:
            return [tag]
            
        return mapped_tags
    
    def get_hierarchy_tree(self) -> List[Dict]:
        """Get the full tag hierarchy as a tree structure"""
        def build_tree(parent_id=None):
            concepts = self.db.query(TagConcept).filter(
                TagConcept.parent_id == parent_id
            ).order_by(TagConcept.display_name).all()
            
            tree = []
            for concept in concepts:
                node = {
                    'id': concept.id,
                    'tag': concept.tag,
                    'display_name': concept.display_name,
                    'description': concept.description,
                    'child_count': concept.child_count,
                    'descendant_count': concept.descendant_count,
                    'synonyms': [s.synonym_tag for s in concept.synonyms],
                    'children': build_tree(concept.id)
                }
                tree.append(node)
            return tree
        
        return build_tree()