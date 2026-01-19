"""
Database models for paper analyses and repository
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float, JSON, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base
import enum

class AnalysisType(enum.Enum):
    """Types of paper analyses"""
    # Fixed prompt-based analyses (9 types)
    SUMMARY = "summary"                    # Executive summary
    KEY_CONTRIBUTIONS = "key_contributions" # Main contributions
    METHODOLOGY = "methodology"             # Research methodology
    LIMITATIONS = "limitations"             # Limitations and critiques
    FUTURE_WORK = "future_work"            # Future research directions
    PRACTICAL_APPLICATIONS = "practical_applications"  # Real-world applications
    RELATED_WORK = "related_work"          # Comparison with related work
    TECHNICAL_DEPTH = "technical_depth"    # Technical details analysis
    IMPACT_ASSESSMENT = "impact_assessment" # Potential impact and significance
    
    # Additional custom analyses
    CUSTOM = "custom"                      # User-defined prompt

# PaperAnalysis class moved to papers.py to avoid duplication
# The model in papers.py is the authoritative version

class AnalysisPrompt(Base):
    """Store and manage analysis prompts"""
    __tablename__ = "analysis_prompts"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Prompt identification
    prompt_key = Column(String(50), unique=True, nullable=False, index=True)  # e.g., "summary", "methodology"
    prompt_name = Column(String(200), nullable=False)  # Display name
    category = Column(String(50))  # Grouping prompts
    
    # Prompt content
    system_prompt = Column(Text)  # System message for the LLM
    user_prompt_template = Column(Text, nullable=False)  # Template with placeholders
    
    # Configuration
    default_model = Column(String(100), default="gpt-4")
    default_parameters = Column(JSON)  # Default temperature, max_tokens, etc.
    
    # UI configuration
    display_order = Column(Integer, default=0)
    icon = Column(String(50))  # Icon name for UI
    color = Column(String(20))  # Color for UI
    description = Column(Text)  # Description for users
    
    # Control
    is_active = Column(Boolean, default=True)
    is_fixed = Column(Boolean, default=True)  # True for the 9 fixed prompts
    requires_review = Column(Boolean, default=False)  # Flag for sensitive analyses
    
    # Usage tracking
    usage_count = Column(Integer, default=0)
    last_used = Column(DateTime(timezone=True))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class PaperRepository(Base):
    """Extended paper repository metadata"""
    __tablename__ = "paper_repository"
    
    id = Column(Integer, primary_key=True, index=True)
    paper_id = Column(Integer, ForeignKey("papers.id", ondelete="CASCADE"), unique=True, nullable=False)
    
    # Storage paths
    pdf_original_path = Column(Text)  # Original PDF location
    pdf_archived_path = Column(Text)  # Archived/backup PDF
    markdown_path = Column(Text)  # Processed markdown
    images_folder = Column(Text)  # Extracted images folder
    
    # Processing status
    pdf_processed = Column(Boolean, default=False)
    markdown_generated = Column(Boolean, default=False)
    analyses_completed = Column(JSON)  # List of completed analysis types
    
    # Quality metrics
    extraction_quality = Column(Float)  # 0-1 score for extraction quality
    has_math_formulas = Column(Boolean, default=False)
    has_tables = Column(Boolean, default=False)
    has_figures = Column(Boolean, default=False)
    
    # File metadata
    pdf_size_bytes = Column(Integer)
    pdf_hash = Column(String(64))  # SHA256 hash for deduplication
    markdown_size_bytes = Column(Integer)
    image_count = Column(Integer, default=0)
    
    # Access tracking
    view_count = Column(Integer, default=0)
    download_count = Column(Integer, default=0)
    last_accessed = Column(DateTime(timezone=True))
    
    # Tags and categorization
    custom_tags = Column(JSON)  # User-defined tags
    auto_categories = Column(JSON)  # Auto-detected categories
    
    # Timestamps
    imported_at = Column(DateTime(timezone=True), server_default=func.now())
    processed_at = Column(DateTime(timezone=True))
    
    # Relationships
    paper = relationship("Paper", back_populates="repository", uselist=False)

class AnalysisComparison(Base):
    """Compare analyses across papers"""
    __tablename__ = "analysis_comparisons"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Papers being compared
    paper_ids = Column(JSON, nullable=False)  # List of paper IDs
    analysis_type = Column(String(50), nullable=False)
    
    # Comparison content
    comparison_content = Column(Text)
    similarity_scores = Column(JSON)  # Pairwise similarity scores
    key_differences = Column(JSON)  # Structured differences
    key_similarities = Column(JSON)  # Structured similarities
    
    # Metadata
    model_used = Column(String(100))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

# Add relationships to Paper model
# This should be added to the existing Paper model in papers.py:
# analyses = relationship("PaperAnalysis", back_populates="paper", cascade="all, delete-orphan")
# repository = relationship("PaperRepository", back_populates="paper", uselist=False, cascade="all, delete-orphan")