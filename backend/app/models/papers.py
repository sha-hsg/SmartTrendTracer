"""
Database models for research papers
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Date, Boolean, ForeignKey, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base

class Paper(Base):
    __tablename__ = "papers"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(Text, nullable=False, index=True)
    abstract = Column(Text)
    content = Column(Text)  # Full extracted text
    pdf_path = Column(Text)  # Path to stored PDF file
    arxiv_id = Column(String(50), index=True)
    doi = Column(String(100), index=True)
    publication_date = Column(Date)
    conference = Column(String(200))
    journal = Column(String(200))
    citation_count = Column(Integer, default=0)
    page_count = Column(Integer)
    language = Column(String(10), default='en')
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    processed = Column(Boolean, default=False)  # Whether full processing is complete
    
    # Relationships
    authors = relationship("PaperAuthor", back_populates="paper", cascade="all, delete-orphan")
    sections = relationship("PaperSection", back_populates="paper", cascade="all, delete-orphan")
    references = relationship("PaperReference", back_populates="paper", cascade="all, delete-orphan")
    tags = relationship("PaperTag", back_populates="paper", cascade="all, delete-orphan")
    snippets = relationship("PaperSnippet", back_populates="paper", cascade="all, delete-orphan")


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
    paper = relationship("Paper", back_populates="authors")


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