"""
Domain models for YouTube Research module.

Represents core entities for computational social science research with
provenance tracking, historical observations, and research-grade data quality.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class CollectionStatus(str, Enum):
    """Status of a collection operation."""
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"
    NOT_ATTEMPTED = "not_attempted"


class Observation(BaseModel):
    """Historical observation of a metric at a specific time."""
    observed_at: datetime = Field(..., description="When this observation was made")
    value: float = Field(..., description="The observed value")
    source: str = Field(..., description="Source of this observation (raw/derived)")
    collection_run_id: str = Field(..., description="ID of the collection run")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Channel(BaseModel):
    """YouTube channel with metadata for research."""
    channel_id: str = Field(..., description="Stable YouTube channel ID")
    title: str = Field(..., description="Channel title")
    description: str = Field(..., description="Channel description")
    custom_url: Optional[str] = Field(None, description="Custom URL")
    subscriber_count: int = Field(0, description="Subscriber count")
    video_count: int = Field(0, description="Total video count")
    playlist_id: str = Field(..., description="Channel's uploads playlist ID")
    url: str = Field(..., description="Canonical URL")
    thumbnail_url: Optional[str] = Field(None, description="Channel thumbnail")
    created_at: Optional[datetime] = Field(None, description="When channel was created")
    
    # Collection metadata
    collection_status: CollectionStatus = Field(CollectionStatus.SUCCESS)
    collection_errors: List[str] = Field(default_factory=list)
    collection_run_id: str = Field(..., description="ID of the collection run")
    collected_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Historical observations
    subscriber_count_observations: List[Observation] = Field(default_factory=list)


class Video(BaseModel):
    """YouTube video with metadata and statistics for research."""
    video_id: str = Field(..., description="Stable YouTube video ID")
    channel_id: str = Field(..., description="ID of the channel this video belongs to")
    channel_title: str = Field(..., description="Title of the channel")
    title: str = Field(..., description="Video title")
    description: str = Field(..., description="Video description")
    published_at: datetime = Field(..., description="When the video was published")
    duration: int = Field(..., description="Video duration in seconds")
    category: Optional[str] = Field(None, description="Video category")
    tags: List[str] = Field(default_factory=list)
    language: Optional[str] = Field(None, description="Video language")
    
    # Statistics
    view_count: int = Field(0, description="Number of views")
    like_count: int = Field(0, description="Number of likes")
    comment_count: int = Field(0, description="Number of comments")
    
    # URLs
    url: str = Field(..., description="Canonical URL")
    thumbnail_url: Optional[str] = Field(None, description="Video thumbnail")
    
    # Collection metadata
    collection_status: CollectionStatus = Field(CollectionStatus.SUCCESS)
    collection_errors: List[str] = Field(default_factory=list)
    collection_run_id: str = Field(..., description="ID of the collection run")
    collected_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Historical observations
    view_count_observations: List[Observation] = Field(default_factory=list)
    like_count_observations: List[Observation] = Field(default_factory=list)
    comment_count_observations: List[Observation] = Field(default_factory=list)
    
    # Derived metrics
    engagement_rate: Optional[float] = Field(None, description="(likes + comments) / views")
    like_rate: Optional[float] = Field(None, description="likes / views")
    comment_rate: Optional[float] = Field(None, description="comments / views")


class Comment(BaseModel):
    """YouTube comment with metadata for research."""
    comment_id: str = Field(..., description="Stable YouTube comment ID")
    video_id: str = Field(..., description="ID of the video this comment belongs to")
    channel_id: str = Field(..., description="ID of the channel this video belongs to")
    author_id: Optional[str] = Field(None, description="ID of the comment author")
    author_name: Optional[str] = Field(None, description="Name of the comment author")
    author_thumbnail: Optional[str] = Field(None, description="Author thumbnail URL")
    text: str = Field(..., description="Comment text content")
    published_at: datetime = Field(..., description="When the comment was published")
    like_count: int = Field(0, description="Number of likes on this comment")
    reply_count: int = Field(0, description="Number of replies to this comment")
    parent_id: Optional[str] = Field(None, description="ID of parent comment if this is a reply")
    is_reply: bool = Field(False, description="Whether this comment is a reply")
    
    # Collection metadata
    collection_status: CollectionStatus = Field(CollectionStatus.SUCCESS)
    collection_errors: List[str] = Field(default_factory=list)
    collection_run_id: str = Field(..., description="ID of the collection run")
    collected_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Historical observations
    like_count_observations: List[Observation] = Field(default_factory=list)


class CollectionRun(BaseModel):
    """Metadata about a data collection run for provenance."""
    collection_run_id: str = Field(..., description="Unique identifier for this run")
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = Field(None)
    status: CollectionStatus = Field(CollectionStatus.NOT_ATTEMPTED)
    
    # Source info
    source_type: str = Field(..., description="Type of source (channel/video/recommendation)")
    source_id: str = Field(..., description="ID of the source entity")
    source_url: str = Field(..., description="URL of the source entity")
    
    # Collection statistics
    videos_discovered: int = Field(0, description="Number of videos discovered")
    videos_collected: int = Field(0, description="Number of videos successfully collected")
    videos_failed: int = Field(0, description="Number of videos that failed to collect")
    
    comments_discovered: int = Field(0, description="Number of comments discovered")
    comments_collected: int = Field(0, description="Number of comments successfully collected")
    comments_failed: int = Field(0, description="Number of comments that failed to collect")
    
    recommendations_discovered: int = Field(0, description="Number of recommendations discovered")
    recommendations_collected: int = Field(0, description="Number of recommendations successfully collected")
    recommendations_failed: int = Field(0, description="Number of recommendations that failed to collect")
    
    errors: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)