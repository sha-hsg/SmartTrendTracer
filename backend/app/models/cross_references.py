"""
Cross-reference models for linking papers with tweets and articles
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime

from app.models import Base

class PaperTweetReference(Base):
    __tablename__ = 'paper_tweet_references'
    
    id = Column(Integer, primary_key=True)
    paper_id = Column(Integer, ForeignKey('papers.id'), nullable=False)
    tweet_id = Column(String, nullable=False)  # Tweet IDs are strings
    relevance_score = Column(Integer, default=0)  # 0-100 relevance score
    reference_type = Column(String, default='mention')  # mention, citation, discussion
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    paper = relationship("Paper", back_populates="tweet_references")

class PaperArticleReference(Base):
    __tablename__ = 'paper_article_references'
    
    id = Column(Integer, primary_key=True)
    paper_id = Column(Integer, ForeignKey('papers.id'), nullable=False)
    article_id = Column(Integer, ForeignKey('substack_articles.id'), nullable=False)
    relevance_score = Column(Integer, default=0)
    reference_type = Column(String, default='mention')
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    paper = relationship("Paper", back_populates="article_references")
    article = relationship("SubstackArticle", back_populates="paper_references")