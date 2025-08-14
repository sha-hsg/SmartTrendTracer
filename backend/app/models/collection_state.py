"""
Model for tracking collection state and last run time
"""
from sqlalchemy import Column, String, DateTime, Integer
from app.models.database import Base
from datetime import datetime, timezone

class CollectionState(Base):
    __tablename__ = "collection_state"
    
    id = Column(Integer, primary_key=True)
    key = Column(String, unique=True, nullable=False)
    last_run = Column(DateTime, nullable=False)
    last_tweet_id = Column(String, nullable=True)
    tweets_collected = Column(Integer, default=0)
    
    @classmethod
    def get_last_run(cls, db):
        """Get the last run timestamp"""
        state = db.query(cls).filter(cls.key == "main").first()
        if state:
            return state.last_run
        return None
    
    @classmethod
    def update_last_run(cls, db, tweet_count=0, last_tweet_id=None):
        """Update the last run timestamp"""
        state = db.query(cls).filter(cls.key == "main").first()
        if not state:
            state = cls(key="main")
            db.add(state)
        
        state.last_run = datetime.now(timezone.utc)
        state.tweets_collected = tweet_count
        if last_tweet_id:
            state.last_tweet_id = last_tweet_id
        
        db.commit()
        return state