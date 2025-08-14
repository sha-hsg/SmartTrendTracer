from sqlalchemy import Column, String, Integer, DateTime, Boolean, Float, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from .database import Base

class Tweet(Base):
    __tablename__ = "tweets"
    
    id = Column(String, primary_key=True)
    text = Column(Text, nullable=False)
    author_id = Column(String, nullable=False)
    author_username = Column(String, nullable=False)
    author_name = Column(String)
    created_at = Column(DateTime, nullable=False)
    collected_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    processed = Column(Boolean, default=False)
    retweet_count = Column(Integer, default=0)
    like_count = Column(Integer, default=0)
    reply_count = Column(Integer, default=0)
    quote_count = Column(Integer, default=0)
    hashtags = Column(Text)  # JSON string
    mentions = Column(Text)  # JSON string
    urls = Column(Text)  # JSON string
    referenced_tweets = Column(Text)  # JSON string
    media_count = Column(Integer, default=0)
    
    # Relationships
    media = relationship("TweetMedia", back_populates="tweet", cascade="all, delete-orphan")
    tags = relationship("Tag", back_populates="tweet", cascade="all, delete-orphan")
    topics = relationship("TweetTopic", back_populates="tweet", cascade="all, delete-orphan")


class TweetMedia(Base):
    __tablename__ = "tweet_media"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    tweet_id = Column(String, ForeignKey("tweets.id"), nullable=False)
    media_key = Column(String, nullable=False)
    type = Column(String, nullable=False)  # photo, video, animated_gif
    url = Column(String)
    preview_image_url = Column(String)
    alt_text = Column(String)
    width = Column(Integer)
    height = Column(Integer)
    duration_ms = Column(Integer)
    local_path = Column(String)
    downloaded = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Relationship
    tweet = relationship("Tweet", back_populates="media")


class Tag(Base):
    __tablename__ = "tags"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    tweet_id = Column(String, ForeignKey("tweets.id"), nullable=False)
    tag = Column(String, nullable=False)
    tag_type = Column(String, default="manual")  # manual, auto, llm
    confidence = Column(Float, default=1.0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Relationship
    tweet = relationship("Tweet", back_populates="tags")


class Topic(Base):
    __tablename__ = "topics"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False, unique=True)
    category = Column(String, default="general")
    first_seen = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow)
    mention_count = Column(Integer, default=1)
    
    # Relationship
    tweets = relationship("TweetTopic", back_populates="topic")


class TweetTopic(Base):
    __tablename__ = "tweet_topics"
    
    tweet_id = Column(String, ForeignKey("tweets.id"), primary_key=True)
    topic_id = Column(Integer, ForeignKey("topics.id"), primary_key=True)
    relevance_score = Column(Float, default=1.0)
    
    # Relationships
    tweet = relationship("Tweet", back_populates="topics")
    topic = relationship("Topic", back_populates="tweets")