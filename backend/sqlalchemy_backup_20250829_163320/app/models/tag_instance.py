"""
Unified Tag Instance Model - Core of the new tag architecture
This replaces the separate tag tables with a unified system
"""
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, ForeignKey, 
    Index, UniqueConstraint, Enum, Boolean, Text
)
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from .database import Base


class ContentType(enum.Enum):
    """Enum for different content types that can be tagged"""
    TWEET = "tweet"
    ARTICLE = "article"
    PAPER = "paper"
    SNIPPET = "snippet"


class TagType(enum.Enum):
    """Enum for different tag types"""
    MANUAL = "manual"
    AI_SUGGESTED = "ai_suggested"
    AUTO = "auto"
    SYSTEM = "system"


class TagInstance(Base):
    """
    Unified tag instance table that links all content to concepts.
    This is the central table for all tagging operations.
    """
    __tablename__ = "tag_instances"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Content reference (polymorphic)
    content_type = Column(Enum(ContentType), nullable=False)
    content_id = Column(String(255), nullable=False)  # Can be tweet_id, article_id, paper_id
    
    # Link to concept (the core improvement)
    concept_id = Column(Integer, ForeignKey("tag_concepts.id", ondelete="CASCADE"), nullable=False)
    
    # Store the original tag as entered (for display/history)
    raw_tag = Column(String(255), nullable=False)
    
    # Tag metadata
    tag_type = Column(Enum(TagType), default=TagType.MANUAL)
    confidence = Column(Float, default=1.0)  # For AI-suggested tags
    
    # User tracking (if needed)
    created_by = Column(String(100))  # Username or system
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Soft delete
    deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime)
    
    # Relationships - removed back_populates to avoid circular dependency
    concept = relationship("TagConcept", foreign_keys=[concept_id])
    
    # Indexes for performance
    __table_args__ = (
        Index("idx_content", "content_type", "content_id"),
        Index("idx_concept", "concept_id"),
        Index("idx_raw_tag", "raw_tag"),
        Index("idx_created_at", "created_at"),
        Index("idx_deleted", "deleted"),
        # Ensure unique tag per content item (when not deleted)
        UniqueConstraint(
            "content_type", "content_id", "concept_id",
            name="uq_content_concept",
            # This would need to be a partial index in PostgreSQL
            # For SQLite, we'll handle in application logic
        ),
    )
    
    def __repr__(self):
        return f"<TagInstance({self.content_type.value}:{self.content_id} -> {self.raw_tag})>"
    
    @property
    def display_tag(self):
        """Get the display version of the tag"""
        if self.concept:
            return self.concept.display_name
        return self.raw_tag
    
    @property
    def normalized_tag(self):
        """Get the normalized version of the tag"""
        if self.concept:
            return self.concept.tag
        return self.raw_tag.lower().replace(' ', '-')


class TagConceptExtended(Base):
    """
    Extended attributes for TagConcept to support the new architecture.
    This extends the existing tag_concepts table.
    """
    __tablename__ = "tag_concept_extended"
    
    id = Column(Integer, primary_key=True)
    concept_id = Column(Integer, ForeignKey("tag_concepts.id", ondelete="CASCADE"), unique=True, nullable=False)
    
    # Usage tracking
    usage_count = Column(Integer, default=0)
    last_used_at = Column(DateTime)
    
    # Quality metrics
    quality_score = Column(Float, default=1.0)  # Based on consistency, usage patterns
    
    # Metadata
    auto_created = Column(Boolean, default=False)  # Was this created automatically?
    verified = Column(Boolean, default=False)  # Has a human verified this concept?
    
    # Configuration
    allow_auto_tagging = Column(Boolean, default=True)  # Can this be auto-applied?
    min_confidence = Column(Float, default=0.5)  # Minimum confidence for auto-tagging
    
    # Rich description (for UI tooltips, documentation)
    description = Column(Text)
    external_url = Column(String(500))  # Link to Wikipedia, documentation, etc.
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship - removed back_populates to avoid circular dependency
    concept = relationship("TagConcept")


class TagMigrationLog(Base):
    """
    Track the migration of tags from old system to new system.
    This helps with rollback and debugging.
    """
    __tablename__ = "tag_migration_log"
    
    id = Column(Integer, primary_key=True)
    
    # What was migrated
    source_table = Column(String(50), nullable=False)  # 'tags', 'article_tags', 'paper_tags'
    source_id = Column(Integer)  # Original record ID
    
    # Original data
    original_tag = Column(String(255), nullable=False)
    original_content_id = Column(String(255), nullable=False)
    
    # New data
    tag_instance_id = Column(Integer, ForeignKey("tag_instances.id"))
    concept_id = Column(Integer, ForeignKey("tag_concepts.id"))
    
    # Migration metadata
    migration_status = Column(String(20))  # 'success', 'failed', 'skipped'
    migration_notes = Column(Text)
    
    # Timestamps
    migrated_at = Column(DateTime, default=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index("idx_source", "source_table", "source_id"),
        Index("idx_status", "migration_status"),
    )


# Note: Relationships to TagConcept should be added in the TagConcept model file itself
# or handled through proper SQLAlchemy configuration