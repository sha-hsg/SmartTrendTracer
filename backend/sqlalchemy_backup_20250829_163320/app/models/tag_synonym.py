"""
SQLAlchemy model for tag synonyms (sameAs relationships)
"""
from sqlalchemy import Column, Integer, String, DateTime, UniqueConstraint
from sqlalchemy.sql import func
from app.models import Base

class TagSynonym(Base):
    __tablename__ = 'tag_synonyms'
    __table_args__ = (
        UniqueConstraint('primary_tag', 'synonym_tag', name='_primary_synonym_uc'),
        {'extend_existing': True}
    )
    
    id = Column(Integer, primary_key=True)
    primary_tag = Column(String, nullable=False)
    synonym_tag = Column(String, nullable=False)
    created_at = Column(DateTime, default=func.now())
    
    def __repr__(self):
        return f"<TagSynonym(primary='{self.primary_tag}', synonym='{self.synonym_tag}')>"