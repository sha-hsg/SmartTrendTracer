"""
Database models for research papers
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Date, Boolean, ForeignKey, Float, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base

class Paper(Base):
    __tablename__ = "papers"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(Text, nullable=False, index=True)
    authors = Column(Text)  # Comma-separated list of authors
    abstract = Column(Text)
    content = Column(Text)  # Full extracted text/markdown
    pdf_path = Column(Text)  # Path to stored PDF file
    pdf_url = Column(Text)  # Original PDF URL (e.g., ArXiv PDF URL)
    arxiv_id = Column(String(50), index=True, unique=True)
    doi = Column(String(100), index=True)
    published_date = Column(Text)  # ArXiv published date
    publication_date = Column(Date)  # Parsed date
    categories = Column(Text)  # ArXiv categories (comma-separated)
    conference = Column(String(200))
    journal = Column(String(200))
    citation_count = Column(Integer, default=0)
    page_count = Column(Integer)
    word_count = Column(Integer)  # Word count of the paper content
    language = Column(String(10), default='en')
    
    # Processing metadata
    processor_used = Column(String(20))  # 'docling', 'marker', 'pypdfium2', etc.
    processing_error = Column(Text)  # Error message if processing failed
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    processed = Column(Boolean, default=False)  # Whether full processing is complete
    
    # Flagging system
    is_flagged = Column(Boolean, default=False, index=True)
    flag_notes = Column(Text)
    
    # DBLP integration
    dblp_key = Column(String(200), index=True)  # e.g., 'conf/emnlp/LiKHdBN22'
    dblp_url = Column(Text)  # Full DBLP URL
    bibtex = Column(Text)  # Stored BibTeX citation
    
    # Relationships
    author_details = relationship("PaperAuthor", back_populates="paper", cascade="all, delete-orphan")
    sections = relationship("PaperSection", back_populates="paper", cascade="all, delete-orphan")
    references = relationship("PaperReference", back_populates="paper", cascade="all, delete-orphan")
    tags = relationship("PaperTag", back_populates="paper", cascade="all, delete-orphan")
    snippets = relationship("PaperSnippet", back_populates="paper", cascade="all, delete-orphan")
    analyses = relationship("PaperAnalysis", back_populates="paper", cascade="all, delete-orphan")
    repository = relationship("PaperRepository", back_populates="paper", uselist=False, cascade="all, delete-orphan")


class PaperAuthor(Base):
    __tablename__ = "paper_authors"
    
    id = Column(Integer, primary_key=True, index=True)
    paper_id = Column(Integer, ForeignKey("papers.id", ondelete="CASCADE"))
    name = Column(Text, nullable=False, index=True)
    email = Column(Text)
    affiliation = Column(Text)
    position = Column(Integer)  # Author order in the paper
    is_corresponding = Column(Boolean, default=False)
    
    # Relationships
    paper = relationship("Paper", back_populates="author_details")


class PaperSection(Base):
    __tablename__ = "paper_sections"
    
    id = Column(Integer, primary_key=True, index=True)
    paper_id = Column(Integer, ForeignKey("papers.id", ondelete="CASCADE"))
    section_type = Column(String(50))  # intro, methods, results, discussion, conclusion
    title = Column(Text)
    content = Column(Text)
    position = Column(Integer)  # Order in the paper
    page_start = Column(Integer)
    page_end = Column(Integer)
    
    # Relationships
    paper = relationship("Paper", back_populates="sections")


class PaperReference(Base):
    __tablename__ = "paper_references"
    
    id = Column(Integer, primary_key=True, index=True)
    paper_id = Column(Integer, ForeignKey("papers.id", ondelete="CASCADE"))
    cited_paper_id = Column(Integer, nullable=True)  # If we have the cited paper (simplified for now)
    raw_citation = Column(Text)
    title = Column(Text)
    authors = Column(Text)
    year = Column(Integer)
    venue = Column(Text)
    doi = Column(String(100))
    
    # Relationships (simplified)
    paper = relationship("Paper", back_populates="references")


class PaperTag(Base):
    __tablename__ = "paper_tags"
    
    id = Column(Integer, primary_key=True, index=True)
    paper_id = Column(Integer, ForeignKey("papers.id", ondelete="CASCADE"))
    tag = Column(Text, nullable=False, index=True)  # Store tag text directly
    tag_type = Column(String(20), default="manual")  # manual, auto, llm
    confidence = Column(Float, default=1.0)  # For AI-suggested tags
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    paper = relationship("Paper", back_populates="tags")


class PaperAnalysis(Base):
    __tablename__ = "paper_analyses"
    
    id = Column(Integer, primary_key=True, index=True)
    paper_id = Column(Integer, ForeignKey("papers.id", ondelete="CASCADE"))
    analysis_type = Column(String(50), nullable=False)  # 'switt_analysis', 'layman_summary', etc.
    content = Column(Text, nullable=False)  # The markdown content
    model_used = Column(String(100))  # Which LLM model was used
    generated_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    paper = relationship("Paper", back_populates="analyses")
    
    # Unique constraint to prevent duplicate analyses of the same type
    __table_args__ = (
        Index('idx_paper_analysis_type', 'paper_id', 'analysis_type', unique=True),
    )


class PaperSnippet(Base):
    __tablename__ = "paper_snippets"
    
    id = Column(Integer, primary_key=True, index=True)
    paper_id = Column(Integer, ForeignKey("papers.id", ondelete="CASCADE"))
    content = Column(Text, nullable=False)
    page_number = Column(Integer)
    section_id = Column(Integer, ForeignKey("paper_sections.id", ondelete="SET NULL"), nullable=True)
    annotation = Column(Text)
    category = Column(String(50))  # finding, method, dataset, limitation, etc.
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    paper = relationship("Paper", back_populates="snippets")
    section = relationship("PaperSection")