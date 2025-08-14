from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

class MediaItem(BaseModel):
    media_key: str
    type: str
    url: Optional[str]
    preview_image_url: Optional[str]
    alt_text: Optional[str]
    width: Optional[int]
    height: Optional[int]

class TagItem(BaseModel):
    tag: str
    type: str = "manual"

class TweetMetrics(BaseModel):
    likes: int
    retweets: int
    replies: int
    quotes: int

class TweetResponse(BaseModel):
    id: str
    text: str
    author_id: str
    author_username: str
    created_at: datetime
    metrics: TweetMetrics
    
    class Config:
        from_attributes = True

class TweetWithMedia(TweetResponse):
    media: List[MediaItem] = []
    tags: List[TagItem] = []