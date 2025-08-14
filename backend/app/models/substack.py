"""
Substack Article and Snippet Models
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, Float, JSON, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from app.models import Base

class SubstackAuthor(Base):
    """Substack author/publication information"""
    __tablename__ = 'substack_authors'
    
    id = Column(Integer, primary_key=True)
    subdomain = Column(String(100), unique=True, nullable=False, index=True)  # e.g., 'astralcodexten'
    name = Column(String(255), nullable=False)
    description = Column(Text)
    url = Column(String(500))
    email = Column(String(255))  # Email address where newsletters arrive
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    articles = relationship("SubstackArticle", back_populates="author", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<SubstackAuthor {self.subdomain}: {self.name}>"

class SubstackArticle(Base):
    """Substack article with full content"""
    __tablename__ = 'substack_articles'
    
    id = Column(Integer, primary_key=True)
    substack_id = Column(String(255), unique=True, index=True)  # Unique ID from Substack
    title = Column(String(500), nullable=False)
    subtitle = Column(Text)
    slug = Column(String(255))  # URL slug
    url = Column(String(500))
    
    # Content
    content_html = Column(Text)  # Original HTML
    content_markdown = Column(Text)  # Converted to Markdown
    preview = Column(Text)  # First 500 chars for dashboard display
    word_count = Column(Integer)
    reading_time_minutes = Column(Integer)
    
    # Metadata
    author_id = Column(Integer, ForeignKey('substack_authors.id'), nullable=False)
    published_at = Column(DateTime, index=True)
    collected_at = Column(DateTime, default=datetime.utcnow)
    
    # Engagement metrics (if available)
    likes = Column(Integer, default=0)
    comments = Column(Integer, default=0)
    
    # Processing flags
    processed = Column(Boolean, default=False)
    summarized = Column(Boolean, default=False)
    deleted = Column(Boolean, default=False)  # Soft delete flag
    
    # AI-generated fields
    summary = Column(Text)  # LLM-generated summary
    key_points = Column(JSON)  # List of key points
    topics = Column(JSON)  # Detected topics
    sentiment = Column(Float)  # Sentiment score
    
    # Relationships
    author = relationship("SubstackAuthor", back_populates="articles")
    snippets = relationship("ArticleSnippet", back_populates="article", cascade="all, delete-orphan")
    tags = relationship("ArticleTag", back_populates="article", cascade="all, delete-orphan")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_article_author_date', 'author_id', 'published_at'),
        Index('idx_article_processed', 'processed', 'summarized'),
    )
    
    def __repr__(self):
        return f"<SubstackArticle {self.title[:50]}...>"

class ArticleSnippet(Base):
    """Highlighted/annotated snippets from articles"""
    __tablename__ = 'article_snippets'
    
    id = Column(Integer, primary_key=True)
    article_id = Column(Integer, ForeignKey('substack_articles.id'), nullable=False)
    
    # Snippet content and location
    text = Column(Text, nullable=False)  # The highlighted text
    start_offset = Column(Integer)  # Character offset in markdown
    end_offset = Column(Integer)
    paragraph_index = Column(Integer)  # Which paragraph it's from
    
    # User annotations
    annotation = Column(Text)  # User's note about this snippet
    category = Column(String(50))  # e.g., 'insight', 'question', 'critique', 'todo'
    importance = Column(Integer, default=3)  # 1-5 scale
    
    # AI analysis
    summary = Column(Text)  # AI summary of this snippet
    entities = Column(JSON)  # Extracted entities
    sentiment = Column(Float)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(100), default='user')  # Track who created it
    
    # Relationships
    article = relationship("SubstackArticle", back_populates="snippets")
    snippet_tags = relationship("SnippetTag", back_populates="snippet", cascade="all, delete-orphan")
    
    # Index for fast retrieval
    __table_args__ = (
        Index('idx_snippet_article', 'article_id'),
        Index('idx_snippet_category', 'category'),
    )
    
    def __repr__(self):
        return f"<Snippet {self.text[:50]}...>"

class ArticleTag(Base):
    """Tags for articles"""
    __tablename__ = 'article_tags'
    
    id = Column(Integer, primary_key=True)
    article_id = Column(Integer, ForeignKey('substack_articles.id'), nullable=False)
    tag = Column(String(100), nullable=False, index=True)
    tag_type = Column(String(20), default='manual')  # manual, llm, auto
    confidence = Column(Float, default=1.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    article = relationship("SubstackArticle", back_populates="tags")
    
    # Unique constraint to prevent duplicate tags
    __table_args__ = (
        Index('idx_article_tag_unique', 'article_id', 'tag', unique=True),
    )

class SnippetTag(Base):
    """Tags for snippets"""
    __tablename__ = 'snippet_tags'
    
    id = Column(Integer, primary_key=True)
    snippet_id = Column(Integer, ForeignKey('article_snippets.id'), nullable=False)
    tag = Column(String(100), nullable=False, index=True)
    tag_type = Column(String(20), default='manual')
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    snippet = relationship("ArticleSnippet", back_populates="snippet_tags")
    
    # Unique constraint
    __table_args__ = (
        Index('idx_snippet_tag_unique', 'snippet_id', 'tag', unique=True),
    )

class SubstackCollection(Base):
    """Track collection runs and email processing"""
    __tablename__ = 'substack_collections'
    
    id = Column(Integer, primary_key=True)
    source = Column(String(50))  # 'email', 'rss', 'web_scrape'
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    articles_collected = Column(Integer, default=0)
    status = Column(String(20))  # 'running', 'completed', 'failed'
    error_message = Column(Text)
    collection_metadata = Column(JSON)  # Store any additional info
    
    def __repr__(self):
        return f"<Collection {self.source} at {self.started_at}>"