"""
MongoDB document models for SmartTrendTracer
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum
from bson import ObjectId

class ConceptStatus(str, Enum):
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    SUGGESTED = "suggested"
    DRAFT = "draft"

class EntityType(str, Enum):
    PERSON = "person"
    ORGANISATION = "organisation"
    LOCATION = "location"
    EVENT = "event"
    MODEL = "model"
    METHOD = "method"
    DATASET = "dataset"
    BENCHMARK = "benchmark"
    METRIC = "metric"
    RESEARCH_TOPIC = "research-topic"
    PAPER = "paper"
    TOOL = "tool"
    CONCEPT = "concept"

class AliasType(str, Enum):
    SYNONYM = "synonym"
    VARIANT = "variant"
    MISSPELLING = "misspelling"
    ABBREVIATION = "abbreviation"
    PLURAL = "plural"
    DEPRECATED = "deprecated"
    LEGACY = "legacy"

class RelationType(str, Enum):
    CHILD_OF = "child_of"
    RELATED = "related"
    PRODUCES = "produces"
    EVALUATED_ON = "evaluated_on"
    PART_OF = "part_of"
    INSTANCE_OF = "instance_of"
    SAME_AS = "same_as"
    REPLACES = "replaces"

class TagConcept(BaseModel):
    """MongoDB document for tag concepts"""
    id: str = Field(..., description="Unique concept ID like c_0001")
    slug: str = Field(..., description="Snake_case normalized name")
    display_name: str = Field(..., description="Human-readable name")
    description: Optional[str] = Field(None, description="Concept description")
    
    # Status and metadata
    status: ConceptStatus = Field(ConceptStatus.ACTIVE)
    entity_type: Optional[EntityType] = None
    usage_count: int = Field(0, description="Total usage across all content")
    
    # Hierarchy (poly-hierarchy support)
    parents: List[str] = Field(default_factory=list, description="Parent concept IDs")
    children: List[str] = Field(default_factory=list, description="Child concept IDs")
    level: int = Field(0, description="Depth in hierarchy (0 for root)")
    
    # Visual properties
    icon: Optional[str] = Field(None, description="Emoji icon")
    color: Optional[str] = Field(None, description="Hex color code")
    
    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        use_enum_values = True
        schema_extra = {
            "example": {
                "id": "c_0001",
                "slug": "large_language_models",
                "display_name": "Large Language Models (LLMs)",
                "description": "Transformer-based models trained on large corpora",
                "status": "active",
                "entity_type": "model",
                "parents": ["c_models", "c_architectures"],
                "children": ["c_gpt_4", "c_claude", "c_llama"],
                "icon": "🤖",
                "color": "#3B82F6"
            }
        }

class TagAlias(BaseModel):
    """MongoDB document for tag aliases"""
    alias_text: str = Field(..., description="The alias text")
    concept_id: str = Field(..., description="Reference to TagConcept.id")
    alias_type: AliasType
    confidence: float = Field(1.0, ge=0.0, le=1.0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        use_enum_values = True

class TagRelation(BaseModel):
    """MongoDB document for concept relationships"""
    source_id: str = Field(..., description="Source concept ID")
    target_id: str = Field(..., description="Target concept ID")
    relation_type: RelationType
    confidence: float = Field(1.0, ge=0.0, le=1.0)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        use_enum_values = True

class TagInstance(BaseModel):
    """MongoDB document for actual tag usage in content"""
    content_type: str = Field(..., description="tweet, paper, article")
    content_id: str = Field(..., description="ID of the content")
    concept_id: Optional[str] = Field(None, description="Linked concept ID")
    original_text: str = Field(..., description="Original tag text as entered")
    display_name: str = Field(..., description="Display name for UI")
    tag_type: str = Field("manual", description="manual, ai, llm, etc.")
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        schema_extra = {
            "example": {
                "content_type": "tweet",
                "content_id": "1234567890",
                "concept_id": "c_0001",
                "original_text": "LLM",
                "display_name": "Large Language Models",
                "tag_type": "ai"
            }
        }

class ReorganizationProposal(BaseModel):
    """MongoDB document for tag reorganization proposals"""
    proposal_id: str = Field(..., description="Unique proposal ID")
    version: str
    model_used: str
    total_tags: int
    confidence_score: float
    reasoning: str
    
    # Core data
    concepts: List[Dict[str, Any]] = Field(default_factory=list)
    aliases: List[Dict[str, Any]] = Field(default_factory=list)
    relations: List[Dict[str, Any]] = Field(default_factory=list)
    root_categories: List[str] = Field(default_factory=list)
    merge_proposals: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Governance
    governance: Dict[str, Any] = Field(default_factory=dict)
    validation: Dict[str, Any] = Field(default_factory=dict)
    
    # Status
    status: str = Field("draft", description="draft, approved, applied, rejected")
    applied_at: Optional[datetime] = None
    applied_by: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        schema_extra = {
            "example": {
                "proposal_id": "prop_2024_01_01_123456",
                "version": "1.0",
                "model_used": "gpt-5-2025-08-07",
                "total_tags": 1553,
                "confidence_score": 0.85,
                "status": "draft"
            }
        }

# Reddit Models
class RedditComment(BaseModel):
    """Reddit comment model"""
    id: str = Field(..., description="Reddit comment ID")
    author: str = Field(..., description="Comment author username")
    body: str = Field(..., description="Comment text content")
    score: int = Field(default=0, description="Comment score")
    created_utc: datetime = Field(..., description="Comment creation time")
    permalink: str = Field(..., description="Permalink to comment")

class SubredditConfig(BaseModel):
    """Subreddit configuration model"""
    name: str = Field(..., description="Subreddit name (without r/)")
    display_name: str = Field(..., description="Display name (e.g., r/LLM)")
    category: str = Field(..., description="Category of subreddit")
    description: str = Field(..., description="Description of subreddit content")
    subscribers: str = Field(..., description="Approximate subscriber count")
    priority: int = Field(default=1, description="Collection priority")

class RedditPost(BaseModel):
    """MongoDB document for Reddit posts"""
    id: Optional[str] = Field(None, alias="_id")
    reddit_id: str = Field(..., description="Reddit post ID")
    title: str = Field(..., description="Post title")
    selftext: str = Field(default="", description="Post text content (for text posts)")
    author: str = Field(..., description="Post author username")
    subreddit: str = Field(..., description="Subreddit name")
    subreddit_config: SubredditConfig = Field(..., description="Subreddit configuration")
    
    # Scoring and engagement
    score: int = Field(default=0, description="Post score")
    upvote_ratio: float = Field(default=0.5, description="Upvote ratio")
    num_comments: int = Field(default=0, description="Number of comments")
    
    # Metadata
    created_utc: datetime = Field(..., description="Post creation time")
    permalink: str = Field(..., description="Reddit permalink")
    url: str = Field(..., description="Post URL")
    urls: List[str] = Field(default_factory=list, description="Extracted URLs from post")
    
    # Post properties
    is_self: bool = Field(default=False, description="Is self post (text post)")
    is_video: bool = Field(default=False, description="Contains video")
    over_18: bool = Field(default=False, description="NSFW content")
    spoiler: bool = Field(default=False, description="Spoiler tagged")
    stickied: bool = Field(default=False, description="Stickied post")
    distinguished: Optional[str] = Field(None, description="Distinguished status")
    gilded: int = Field(default=0, description="Number of gildings")
    
    # Comments
    comments: List[RedditComment] = Field(default_factory=list, description="Post comments")
    
    # SmartTrendTracer integration
    tags: List[str] = Field(default_factory=list, description="Applied tags")
    processed: bool = Field(default=False, description="Whether post has been processed")
    content_type: str = Field(default="reddit_post", description="Content type identifier")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Document creation time")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update time")
    
    class Config:
        allow_population_by_field_name = True
        schema_extra = {
            "example": {
                "reddit_id": "abc123",
                "title": "New breakthrough in transformer architecture",
                "selftext": "Researchers have discovered...",
                "author": "ml_researcher",
                "subreddit": "MachineLearning",
                "score": 156,
                "num_comments": 23,
                "tags": ["transformer", "architecture", "research"],
                "processed": False
            }
        }

class RedditCollectionStats(BaseModel):
    """Statistics for Reddit collection"""
    total_posts: int = Field(default=0, description="Total posts collected")
    posts_by_subreddit: List[Dict[str, Any]] = Field(default_factory=list, description="Posts grouped by subreddit")
    recent_posts_24h: int = Field(default=0, description="Posts collected in last 24 hours")
    subreddits_monitored: int = Field(default=0, description="Number of monitored subreddits")
    last_collection: Optional[datetime] = Field(None, description="Last collection time")
    last_collection_stats: Optional[Dict[str, Any]] = Field(None, description="Last collection statistics")